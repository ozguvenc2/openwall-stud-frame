"""Synth-compatible OpenMask3D CLIP stage for stage0 posed RGB-D.

Uses class-agnostic masks already produced by the OpenMask3D mask module, the
synthetic posed RGB-D folder from ``synth_posed_rgbd``, and OpenAI CLIP text
queries to pick a stud instance. Skips the upstream SAM multi-round crop
refiner so the stage0 cloud can finish without a ScanNet capture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.sam2_mask import full_stud_cameras, project_points
from openwall_stud.synthetic import Scene


STUD_QUERIES = (
    "a wooden stud",
    "a vertical wooden framing stud",
    "a wood 2x4 stud beam",
)
NEG_QUERIES = (
    "clutter",
    "empty background",
    "floor",
)


def _load_masks(mask_path: Path) -> np.ndarray:
    import torch

    blob = torch.load(mask_path, map_location="cpu", weights_only=False)
    if hasattr(blob, "detach"):
        arr = blob.detach().cpu().numpy()
    else:
        arr = np.asarray(blob)
    if arr.ndim != 2:
        raise ValueError(f"expected [N,M] masks, got {arr.shape}")
    return arr.astype(np.float64)


def _clip_encode_images(model, preprocess, device, crops: list) -> np.ndarray:
    import torch

    if not crops:
        return np.zeros((0, 512), dtype=np.float32)
    batch = torch.stack([preprocess(img) for img in crops]).to(device)
    with torch.no_grad():
        feats = model.encode_image(batch).float()
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.detach().cpu().numpy()


def _clip_encode_texts(model, device, texts: tuple[str, ...]) -> np.ndarray:
    import clip
    import torch

    tokens = clip.tokenize(list(texts)).to(device)
    with torch.no_grad():
        feats = model.encode_text(tokens).float()
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.detach().cpu().numpy()


def score_masks_with_clip(
    scene: Scene,
    mask_path: Path,
    posed_dir: Path,
    *,
    top_masks: int = 24,
    min_mask_points: int = 200,
    clip_model_name: str = "ViT-B/32",
) -> dict[str, Any]:
    """Return best stud mask index + per-mask CLIP scores for stage0."""
    import clip
    import torch
    from PIL import Image

    arr = _load_masks(mask_path)
    if arr.shape[0] != scene.n_points:
        raise ValueError(f"mask rows {arr.shape[0]} != cloud {scene.n_points}")
    cameras = full_stud_cameras()
    color_dir = Path(posed_dir) / "color"
    images = []
    for i in range(len(cameras)):
        path = color_dir / f"{i}.jpg"
        if not path.is_file():
            raise FileNotFoundError(f"missing posed color {path}")
        images.append(Image.open(path).convert("RGB"))

    point_counts = (arr > 0.0).sum(axis=0)
    order = np.argsort(-point_counts)
    candidates = [int(i) for i in order if point_counts[i] >= min_mask_points][:top_masks]
    if not candidates:
        candidates = [int(order[0])]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load(clip_model_name, device=device)
    stud_txt = _clip_encode_texts(model, device, STUD_QUERIES).mean(axis=0)
    stud_txt = stud_txt / np.linalg.norm(stud_txt)
    neg_txt = _clip_encode_texts(model, device, NEG_QUERIES).mean(axis=0)
    neg_txt = neg_txt / np.linalg.norm(neg_txt)

    projections = [project_points(scene.points_m, cam) for cam in cameras]
    per_mask: list[dict[str, Any]] = []
    max_points = float(max(int(point_counts[i]) for i in candidates) or 1)

    for mask_i in candidates:
        mask = arr[:, mask_i] > 0.0
        crops = []
        for view_i, camera in enumerate(cameras):
            proj = projections[view_i]
            u = proj["u"]
            v = proj["v"]
            valid = proj["valid"]
            ui = np.rint(u).astype(np.int32)
            vi = np.rint(v).astype(np.int32)
            inside = (
                mask
                & valid
                & (ui >= 0)
                & (ui < camera.width)
                & (vi >= 0)
                & (vi < camera.height)
            )
            if not np.any(inside):
                continue
            xs = ui[inside]
            ys = vi[inside]
            pad = 8
            x0 = max(int(xs.min()) - pad, 0)
            x1 = min(int(xs.max()) + pad + 1, camera.width)
            y0 = max(int(ys.min()) - pad, 0)
            y1 = min(int(ys.max()) + pad + 1, camera.height)
            if x1 <= x0 + 2 or y1 <= y0 + 2:
                continue
            crops.append(images[view_i].crop((x0, y0, x1, y1)))
        n_pts = int(point_counts[mask_i])
        size_prior = n_pts / max_points
        if not crops:
            clip_score = -1e9
            stud_sim = float("nan")
            neg_sim = float("nan")
            score = -1e9
        else:
            feats = _clip_encode_images(model, preprocess, device, crops)
            feat = feats.mean(axis=0)
            feat = feat / max(float(np.linalg.norm(feat)), 1e-8)
            stud_sim = float(feat @ stud_txt)
            neg_sim = float(feat @ neg_txt)
            # Synth wood silhouettes are nearly CLIP-tied; break ties with mask size
            # so the largest stud-like instance wins on the one-beam scene.
            clip_score = stud_sim - neg_sim
            score = clip_score + 0.05 * size_prior
        per_mask.append(
            {
                "mask_index": mask_i,
                "n_points": n_pts,
                "n_crops": len(crops),
                "stud_sim": stud_sim,
                "neg_sim": neg_sim,
                "clip_score": clip_score,
                "size_prior": size_prior,
                "score": score,
            }
        )

    per_mask.sort(key=lambda row: float(row["score"]), reverse=True)
    best = per_mask[0]
    return {
        "best_mask_index": int(best["mask_index"]),
        "best_score": float(best["score"]),
        "n_candidates": len(candidates),
        "clip_model": clip_model_name,
        "device": device,
        "stud_queries": list(STUD_QUERIES),
        "neg_queries": list(NEG_QUERIES),
        "size_prior_weight": 0.05,
        "per_mask": per_mask,
        "path": "synth_posed_rgbd_clip_bbox_crops",
        "note": (
            "CLIP on synthetic posed RGB-D bbox crops of OpenMask3D mask-module "
            "instances. Score = (stud−neg) CLIP margin + 0.05×size prior. "
            "SAM multi-round crop refiner not run."
        ),
    }
