"""Stage0 stud-bar writers for the four promptable foundation tools.

Does not train foundation backbones. Point-SAM / Segment3D / OpenMask3D want
the WSL mlenv interpreter. SAM3D (Yang et al. ViT-H lift) runs on the Windows
ranks45 torch 2.7 env that already has segment-anything.

    # WSL
    /home/pegassy/mlenv/bin/python scripts/phase_neg1_stage0_foundation.py --tool pointsam
    /home/pegassy/mlenv/bin/python scripts/phase_neg1_stage0_foundation.py --tool openmask3d
    /home/pegassy/mlenv/bin/python scripts/phase_neg1_stage0_foundation.py --tool segment3d

    # Windows ranks45 .venv
    ...\\python.exe scripts/phase_neg1_stage0_foundation.py --tool sam3d
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if not ROOT.exists():
    ROOT = Path("/mnt/c/Repos/openwall-stud-frame")
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.foundation_stage0 import (  # noqa: E402
    blocked_row,
    labels_from_mask,
    summary_row,
    write_foundation_card,
)
from openwall_stud.synthetic import stage0_single_stud  # noqa: E402

SCENE_NAME = "stage0_2x4_lean0.000"
OUT = ROOT / "artifacts" / "scorecards"
PHASE = ROOT / "artifacts" / "phase_neg1"


def scene():
    cloud = stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)
    if cloud.name != SCENE_NAME:
        raise SystemExit(f"scene name {cloud.name} != {SCENE_NAME}")
    return cloud


def _cuda_event_time(fn):
    import torch

    if not torch.cuda.is_available():
        started = time.perf_counter()
        result = fn()
        return result, time.perf_counter() - started, None
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    torch.cuda.synchronize()
    wall0 = time.perf_counter()
    start.record()
    result = fn()
    end.record()
    torch.cuda.synchronize()
    wall = time.perf_counter() - wall0
    gpu_ms = float(start.elapsed_time(end))
    return result, wall, gpu_ms


def run_pointsam() -> dict:
    import torch
    from hydra import compose, initialize_config_dir
    from hydra.utils import instantiate
    from safetensors.torch import load_model

    cloud = scene()
    point_sam = ROOT / "artifacts" / "third_party" / "Point-SAM"
    sys.path.insert(0, str(point_sam))
    points = np.asarray(cloud.points_m, dtype=np.float32)
    coords = torch.from_numpy(points).float().cuda().unsqueeze(0)
    coords = coords - coords.mean(dim=1, keepdim=True)
    coords = coords / coords.norm(dim=2, keepdim=True).max()
    features = torch.zeros(coords.shape, device=coords.device, dtype=coords.dtype)
    os.chdir(point_sam)
    with initialize_config_dir(config_dir=str(point_sam / "configs"), version_base=None):
        cfg = compose(config_name="large")
    model = instantiate(cfg.model)
    weight = ROOT / "data" / "cache" / "phase_neg1" / "pointsam" / "model.safetensors"
    load_model(model, str(weight), strict=False)
    model.cuda().eval()
    prompt = coords[:, :1, :]
    prompt_labels = torch.ones((1, 1), device=coords.device, dtype=torch.int64)

    def _forward():
        with torch.no_grad():
            return model.predict_masks(coords, features, prompt, prompt_labels)

    (masks, iou_preds), wall_s, gpu_ms = _cuda_event_time(_forward)
    # Best of three masks by predicted IoU.
    best = int(torch.argmax(iou_preds.reshape(-1)).item())
    mask = masks[0, best].detach().float().cpu().numpy() > 0.0
    labels = labels_from_mask(mask, cloud.n_points)
    dest = OUT / f"pointsam_stage0_{cloud.name}.json"
    card = write_foundation_card(
        cloud,
        labels,
        algorithm_id="F1",
        algorithm="Point-SAM promptable mask (zero-shot, point prompt)",
        rank=8,
        runtime_s=wall_s,
        dest=dest,
        license_name="Point-SAM code + HF weights (see upstream); not a stud-trained head",
        hardware=f"cuda; torch {torch.__version__}; {torch.cuda.get_device_name(0)}",
        failure_modes=[
            "Zero-shot foundation mask, not a stud-class train.",
            "Single point prompt at the normalized cloud origin.",
        ],
        implementation={
            "weight": str(weight),
            "mask_index": best,
            "iou_pred": float(iou_preds.reshape(-1)[best].detach().float().cpu()),
            "gpu_ms": gpu_ms,
            "prompt": "first-point after mean-center/normalize",
        },
        implementation_short="Point-SAM large, one positive point prompt, best IoU mask → stud labels.",
        day_algorithm="pointsam",
    )
    row = summary_row("pointsam", card)
    row["gpu_ms"] = gpu_ms
    row["reason"] = "zero-shot point prompt; not a stud-trained head"
    return row


def run_sam3d() -> dict:
    """Yang et al. SAM3D path: ViT-H on full-stud pinholes, union lift to points.

    The old scaffold ``default_stud_camera`` FOV-crops the 8 ft stud to ~1.0 m and
    fails the stage0 length bar. Stage0 uses ``full_stud_cameras`` (front+back).
    """
    import torch
    from segment_anything import SamPredictor, sam_model_registry

    from openwall_stud.contenders.sam2_mask import (
        _prompt_on_stud_pixels,
        _rgb_from_occupied,
        full_stud_cameras,
        lift_mask_winners,
        raster_nearest,
    )

    cloud = scene()
    cameras = full_stud_cameras()
    weight = ROOT / "data" / "cache" / "phase_neg1" / "sam" / "sam_vit_h_4b8939.pth"
    sam = sam_model_registry["vit_h"](checkpoint=str(weight))
    sam.to(device="cuda")
    predictor = SamPredictor(sam)

    union = np.zeros(cloud.n_points, dtype=bool)
    view_records: list[dict] = []
    wall_acc = 0.0
    gpu_acc = 0.0

    for view_i, camera in enumerate(cameras):
        raster = raster_nearest(cloud.points_m, cloud.part, camera)
        rgb, _ = _rgb_from_occupied(raster["part_image"])
        prompt = _prompt_on_stud_pixels(raster["part_image"])
        if prompt is None:
            view_records.append({"view": view_i, "status": "no_stud_pixels"})
            continue
        predictor.set_image(rgb)
        x_px, y_px = prompt

        def _forward(predictor=predictor, x_px=x_px, y_px=y_px):
            return predictor.predict(
                point_coords=np.array([[x_px, y_px]], dtype=np.float32),
                point_labels=np.array([1], dtype=np.int32),
                multimask_output=True,
            )

        (masks, scores, _logits), wall_s, gpu_ms = _cuda_event_time(_forward)
        wall_acc += float(wall_s)
        if gpu_ms is not None:
            gpu_acc += float(gpu_ms)
        best = int(np.argmax(scores))
        indices = lift_mask_winners(raster, masks[best].astype(bool))
        if indices.size:
            union[indices] = True
        view_records.append(
            {
                "view": view_i,
                "eye_m": list(camera.eye_m),
                "prompt_px": [float(x_px), float(y_px)],
                "best_score": float(scores[best]),
                "n_lifted": int(indices.size),
            }
        )

    if not union.any():
        return blocked_row("sam3d", "no points lifted from full-stud pinholes")

    labels = labels_from_mask(union, cloud.n_points)
    dest = OUT / f"sam3d_stage0_{cloud.name}.json"
    card = write_foundation_card(
        cloud,
        labels,
        algorithm_id="F2",
        algorithm="SAM3D (Yang et al.) ViT-H full-stud multi-view lift",
        rank=9,
        runtime_s=wall_acc,
        dest=dest,
        license_name="segment-anything Apache-2.0; SAM3D upstream; not a stud-trained head",
        hardware=f"cuda; torch {torch.__version__}; {torch.cuda.get_device_name(0)}",
        failure_modes=[
            "ScanNet multi-frame SAM3D path not used; two synthetic full-stud pinholes.",
            "Occluded points behind each pinhole are not lifted (union of winners only).",
            "Zero-shot image mask, not a stud-class train.",
        ],
        implementation={
            "identity": "Pointcept/SegmentAnything3D yang2023sam3d",
            "weight": str(weight),
            "cameras": "full_stud_cameras front+back",
            "views": view_records,
            "n_lifted": int(union.sum()),
            "gpu_ms": gpu_acc if gpu_acc else None,
            "note": (
                "2D SAM ViT-H on full-stud pinholes + z-buffer lift union. "
                "Replaces FOV-cropped default_stud_camera that truncated length to ~1 m."
            ),
        },
        implementation_short=(
            "SAM ViT-H on full-stud front+back pinholes, mask union lifted → stud labels."
        ),
        day_algorithm="sam3d",
    )
    row = summary_row("sam3d", card)
    row["gpu_ms"] = gpu_acc if gpu_acc else None
    fails = card.get("stage0_bar_failures") or []
    row["reason"] = (
        "ViT-H full-stud multi-view lift; ScanNet multi-frame path not run"
        + (f"; bars: {'; '.join(fails)}" if fails else "")
    )
    return row


def run_openmask3d() -> dict:
    """Mask module + synth posed RGB-D CLIP text query → stud labels."""
    import torch

    from openwall_stud.openmask3d_clip_stage0 import score_masks_with_clip
    from openwall_stud.synth_posed_rgbd import write_posed_rgbd_scene

    cloud = scene()
    mask_path = PHASE / "openmask3d_masks" / "stage0_2x4_lean0_masks.pt"
    if not mask_path.is_file():
        return blocked_row(
            "openmask3d",
            "mask module output missing; run scripts/phase_neg1_openmask3d_smoke.sh first",
        )
    posed_dir = PHASE / "stage0_posed_rgbd"
    meta_path = posed_dir / "synth_posed_rgbd.json"
    if not meta_path.is_file() or not (posed_dir / "color" / "0.jpg").is_file():
        write_posed_rgbd_scene(cloud, posed_dir)

    started = time.perf_counter()
    try:
        clip_info = score_masks_with_clip(cloud, mask_path, posed_dir)
    except Exception as exc:  # noqa: BLE001
        return blocked_row("openmask3d", f"CLIP/posed-RGB-D stage failed: {type(exc).__name__}: {exc}")
    masks = torch.load(mask_path, map_location="cpu", weights_only=False)
    if torch.is_tensor(masks):
        arr = masks.detach().cpu().numpy()
    else:
        arr = np.asarray(masks)
    if arr.shape[0] != cloud.n_points:
        return blocked_row(
            "openmask3d",
            f"mask rows {arr.shape[0]} != cloud {cloud.n_points}",
        )
    best = int(clip_info["best_mask_index"])
    mask = arr[:, best] > 0.0
    wall_s = time.perf_counter() - started
    labels = labels_from_mask(mask, cloud.n_points)
    dest = OUT / f"openmask3d_stage0_{cloud.name}.json"
    card = write_foundation_card(
        cloud,
        labels,
        algorithm_id="F3",
        algorithm="OpenMask3D mask module + synth posed RGB-D CLIP",
        rank=10,
        runtime_s=wall_s,
        dest=dest,
        license_name="OpenMask3D upstream; openai-clip; not a stud-trained head",
        hardware=f"clip device {clip_info.get('device')}; prior CUDA mask-module forward",
        failure_modes=[
            "Posed RGB-D is synthetic (full-stud pinholes), not a real capture.",
            "CLIP uses bbox crops of projected mask points; upstream SAM multi-round crop refiner not run.",
            "Zero-shot foundation mask + open-vocab text, not a stud-class train.",
        ],
        implementation={
            "mask_path": str(mask_path),
            "mask_shape": list(arr.shape),
            "mask_index": best,
            "mask_sum": float(arr[:, best].sum()),
            "posed_rgbd": str(posed_dir),
            "clip_stage": "ran_synth_posed_rgbd",
            "clip": clip_info,
        },
        implementation_short=(
            "OpenMask3D masks + synth posed RGB-D CLIP text query → stud labels."
        ),
        day_algorithm="openmask3d",
    )
    row = summary_row("openmask3d", card)
    fails = card.get("stage0_bar_failures") or []
    row["reason"] = (
        "mask-module + synth posed RGB-D CLIP open-vocab"
        + (f"; bars: {'; '.join(fails)}" if fails else "")
    )
    return row


def run_segment3d() -> dict:
    import os as _os
    import types

    import open3d as o3d
    import torch
    from omegaconf import OmegaConf

    _os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
    exp = types.ModuleType("hydra.experimental")

    def _unused(*_a, **_k):
        raise RuntimeError("unused shim")

    exp.initialize = _unused
    exp.compose = _unused
    sys.modules["hydra.experimental"] = exp

    repo = ROOT / "artifacts" / "third_party" / "Segment3D"
    sys.path.insert(0, str(repo))
    _os.chdir(repo)
    import hydra
    from demo_utils import prepare_data

    cloud = scene()
    ckpt = ROOT / "data" / "cache" / "phase_neg1" / "segment3d" / "segment3d.ckpt"
    model_cfg = OmegaConf.load(repo / "conf/model/mask3d_no_aux.yaml")
    parent = OmegaConf.create(
        {
            "general": {"train_on_segments": False},
            "data": {
                "voxel_size": 0.02,
                "in_channels": 3,
                "num_labels": 20,
                "add_raw_coordinates": True,
            },
            "model": model_cfg,
        }
    )
    OmegaConf.resolve(parent)
    OmegaConf.set_struct(parent.model, False)
    parent.model._recursive_ = False
    net = hydra.utils.instantiate(parent.model)
    blob = torch.load(str(ckpt), map_location="cpu")
    state = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
    own = net.state_dict()
    stripped = {}
    for key, value in state.items():
        name = key[6:] if key.startswith("model.") else key
        if name in own and own[name].shape == value.shape:
            stripped[name] = value
    net.load_state_dict(stripped, strict=False)
    net.eval()
    device = torch.device("cuda")
    net.to(device)
    pts = np.asarray(cloud.points_m, dtype=np.float64)
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(pts)
    colors = np.tile(np.array([[0.7, 0.7, 0.7]], dtype=np.float64), (pts.shape[0], 1))
    mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
    data, point2segment, _full, raw_coordinates, inverse_map = prepare_data(
        parent, mesh, None, device
    )

    def _forward():
        with torch.no_grad():
            return net(data, point2segment=point2segment, raw_coordinates=raw_coordinates)

    outputs, wall_s, gpu_ms = _cuda_event_time(_forward)
    if not isinstance(outputs, dict) or "pred_logits" not in outputs or "pred_masks" not in outputs:
        return blocked_row("segment3d", f"unexpected outputs keys={list(outputs) if isinstance(outputs, dict) else type(outputs)}")
    logits = outputs["pred_logits"][0]  # [Q, C]
    raw_masks = outputs["pred_masks"]
    # Mask3D returns a list of length batch; each entry is [N_vox, Q].
    pred_masks = raw_masks[0] if isinstance(raw_masks, list) else raw_masks[0]
    # Objectness: max over classes excluding void if present; else max over all.
    scores = logits.softmax(-1)[..., 1:].max(-1).values if logits.shape[-1] > 1 else logits.softmax(-1).max(-1).values
    best = int(torch.argmax(scores).item())
    vox_mask = pred_masks[:, best].detach().float().cpu().numpy() > 0.0
    inv = np.asarray(inverse_map).reshape(-1)
    # prepare_data inverse_map is point → voxel index (length = n_points).
    if inv.shape[0] == cloud.n_points and inv.max() < vox_mask.shape[0]:
        point_mask = vox_mask[inv].astype(bool)
    elif inv.shape[0] == vox_mask.shape[0]:
        point_mask = np.zeros(cloud.n_points, dtype=bool)
        chosen = inv[vox_mask]
        chosen = chosen[(chosen >= 0) & (chosen < cloud.n_points)]
        point_mask[chosen] = True
    elif vox_mask.shape[0] == cloud.n_points:
        point_mask = vox_mask.astype(bool)
    else:
        return blocked_row(
            "segment3d",
            f"cannot map pred_masks {tuple(pred_masks.shape)} via inverse_map {inv.shape}",
        )
    labels = labels_from_mask(point_mask, cloud.n_points)
    dest = OUT / f"segment3d_stage0_{cloud.name}.json"
    card = write_foundation_card(
        cloud,
        labels,
        algorithm_id="F4",
        algorithm="Segment3D Mask3D zero-shot (no cuML postprocess)",
        rank=11,
        runtime_s=wall_s,
        dest=dest,
        license_name="Segment3D upstream; segment3d.ckpt; not a stud-trained head",
        hardware=f"cuda; torch {torch.__version__}; {torch.cuda.get_device_name(0)}",
        failure_modes=[
            "cuML DBSCAN demo postprocess not run.",
            "Zero-shot instance query, not a stud-class train.",
            "Constant gray RGB on the synth stud.",
        ],
        implementation={
            "weight": str(ckpt),
            "loaded_tensors": len(stripped),
            "query_index": best,
            "query_score": float(scores[best].detach().cpu()),
            "pred_logits": list(outputs["pred_logits"].shape),
            "pred_masks": list(pred_masks.shape),
            "gpu_ms": gpu_ms,
            "n_stud_points": int(point_mask.sum()),
        },
        implementation_short="Segment3D Mask3D best query mask → stud labels. No cuML.",
        day_algorithm="segment3d",
    )
    row = summary_row("segment3d", card)
    row["gpu_ms"] = gpu_ms
    row["reason"] = "zero-shot Mask3D forward; cuML postprocess not run"
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Foundation stud-bar writers on stage0.")
    parser.add_argument(
        "--tool",
        choices=("pointsam", "sam3d", "openmask3d", "segment3d"),
        required=True,
    )
    args = parser.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    PHASE.mkdir(parents=True, exist_ok=True)
    runners = {
        "pointsam": run_pointsam,
        "sam3d": run_sam3d,
        "openmask3d": run_openmask3d,
        "segment3d": run_segment3d,
    }
    try:
        row = runners[args.tool]()
    except Exception as exc:  # noqa: BLE001 — surface as blocked for the all-nine table
        row = blocked_row(args.tool, f"{type(exc).__name__}: {exc}")
    dest = PHASE / f"stage0_round_{args.tool}.json"
    dest.write_text(json.dumps([row], indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, indent=2))
    return 0 if row.get("pass_fail") not in (None,) else 0


if __name__ == "__main__":
    raise SystemExit(main())
