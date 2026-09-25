"""Run rank 4 (Pointcept) and rank 5 (Open3D-ML) on the synthetic wall corner.

Control weights are the phase-1 paths (BIMStruct3D PTv3, S3DIS RandLA-Net).
``stud_finetune`` reloads the phase-1 stud/clutter heads. Those heads have
no wall class. A stud label is not a face detection.

    .venv\\Scripts\\python.exe scripts/infer_neural_corner.py --stack pointcept --weights control
    .venv-o3dml\\Scripts\\python.exe scripts/infer_neural_corner.py --stack randlanet --weights control

Scorecards land in artifacts/scorecards/phase2_neural_corner/.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.wall_corner import (  # noqa: E402
    histogram,
    load_manifest,
    read_ply,
    recover_faces,
    repo_root,
)

OUT_DIR = repo_root() / "artifacts" / "scorecards" / "phase2_neural_corner"
MIN_FREE_BYTES = 5 * 1024**3


def _free_cuda_bytes() -> int:
    import torch

    if not torch.cuda.is_available():
        return 0
    free, _total = torch.cuda.mem_get_info()
    return int(free)


def _wait_for_headroom() -> int:
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available in this interpreter")
    for attempt in range(8):
        free = _free_cuda_bytes()
        print(f"cuda free {free / 1024**3:.2f} GiB")
        if free >= MIN_FREE_BYTES:
            return free
        print(f"waiting for GPU headroom ({attempt + 1}/8)")
        time.sleep(15)
    raise SystemExit(f"GPU free memory stayed under {MIN_FREE_BYTES / 1024**3:.1f} GiB")


def _scene_arrays(scene: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    path = repo_root() / scene["ply"]
    if not path.is_file():
        raise SystemExit(f"Missing {path}. Run scripts/gen_wall_corner.py first.")
    return read_ply(path)


def _write(card: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{card['file_stem']}.json"
    path = OUT_DIR / name
    path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    return path


def _refresh_summary() -> None:
    rows = []
    for path in sorted(OUT_DIR.glob("r*_*.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    summary = {
        "what": "phase-2 neural corner, ranks 4 and 5",
        "not_studs": True,
        "not_field_cloud": True,
        "n_cards": len(rows),
        "both_faces_detected": [
            {
                "stack": row.get("stack"),
                "weights": row.get("weights"),
                "scene": row.get("scene"),
                "both_faces_detected": (row.get("faces_score") or {}).get("both_faces_detected"),
                "runtime_s": row.get("runtime_s"),
            }
            for row in rows
        ],
        "cards": [row.get("file_stem") for row in rows],
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def _card(
    *,
    stack: str,
    rank: int,
    weights: str,
    scene: dict[str, Any],
    names: list[str],
    pred: np.ndarray,
    runtime_s: float,
    extra: dict[str, Any],
) -> dict[str, Any]:
    points, labels = _scene_arrays(scene)
    score = recover_faces(
        points,
        pred,
        names,
        labels,
        np.asarray(scene["gt_normal_a"], dtype=float),
        np.asarray(scene["gt_normal_b"], dtype=float),
        seed=int(scene["seed"]),
        gt_lean_a=float(scene["gt_face_a_lean_deg"]),
        gt_lean_b=float(scene["gt_face_b_lean_deg"]),
        wall_names=set(extra["wall_names"]) if "wall_names" in extra else {"wall"},
    )
    stem = f"r{rank}_{stack}_{weights}__{scene['name']}"
    return {
        "file_stem": stem,
        "rank": rank,
        "stack": stack,
        "weights": weights,
        "scene": scene["name"],
        "claim": "wall planes and corner lean. Not a stud detection.",
        "gt_face_a_lean_deg": scene["gt_face_a_lean_deg"],
        "gt_face_b_lean_deg": scene["gt_face_b_lean_deg"],
        "n_points": int(points.shape[0]),
        "runtime_s": round(float(runtime_s), 4),
        "histogram": histogram(pred, names),
        "faces_score": score,
        **{key: value for key, value in extra.items() if key != "wall_names"},
    }


def run_pointcept(weights: str) -> None:
    _wait_for_headroom()
    from openwall_stud.contenders import pointcept_ptv3
    from openwall_stud.finetune_pointcept import (
        build_model,
        load_bimstruct_backbone,
        load_finetuned,
        predict_full,
        weight_path,
    )

    manifest = load_manifest()
    cache = pointcept_ptv3._cache_root()
    fetch_error = pointcept_ptv3._ensure_bimstruct(cache)
    if fetch_error:
        raise SystemExit(fetch_error)
    if str(cache) not in sys.path:
        sys.path.insert(0, str(cache))
    import segment_scan

    if weights == "control":
        for scene in manifest["scenes"]:
            points, _labels = _scene_arrays(scene)
            namespace = SimpleNamespace(points_m=points, seed=int(scene["seed"]))
            started = time.perf_counter()
            forward = pointcept_ptv3._forward(namespace, cache, "cuda")
            runtime_s = time.perf_counter() - started
            card = _card(
                stack="pointcept",
                rank=4,
                weights="control",
                scene=scene,
                names=forward["names"],
                pred=forward["labels"],
                runtime_s=runtime_s,
                extra={
                    "wall_names": ["wall"],
                    "path": "openwall_stud.contenders.pointcept_ptv3._forward",
                    "weight": "data/cache/bimstruct3d/weights/model_best.pth",
                    "license": "BIMStruct3D weights CC BY-NC-SA 4.0, not committed",
                    "tta": forward.get("tta"),
                    "vote_mass": forward.get("vote_mass"),
                    "n_uncovered": forward.get("n_uncovered"),
                },
            )
            print(card["file_stem"], "both", card["faces_score"]["both_faces_detected"], "s", card["runtime_s"])
            _write(card)
            _refresh_summary()
        return

    if weights != "stud_finetune":
        raise SystemExit(f"unknown pointcept weights {weights}")
    model = build_model("cuda")
    backbone = load_bimstruct_backbone(model)
    meta = load_finetuned(model, weight_path())
    for scene in manifest["scenes"]:
        points, _labels = _scene_arrays(scene)
        normals = segment_scan.estimate_normals(np.asarray(points, dtype=np.float64))
        started = time.perf_counter()
        pred = predict_full(model, points, normals)
        runtime_s = time.perf_counter() - started
        card = _card(
            stack="pointcept",
            rank=4,
            weights="stud_finetune",
            scene=scene,
            names=["clutter", "stud"],
            pred=pred,
            runtime_s=runtime_s,
            extra={
                "wall_names": [],
                "path": "openwall_stud.finetune_pointcept.predict_full",
                "weight": str(weight_path()),
                "head_meta": meta,
                "backbone_copied": backbone.get("copied"),
                "note": "Stud/clutter head. A stud label is not a wall face. Face planes are not scored from the stud class.",
            },
        )
        print(card["file_stem"], "both", card["faces_score"]["both_faces_detected"], "s", card["runtime_s"])
        _write(card)
        _refresh_summary()


def run_randlanet(weights: str) -> None:
    _wait_for_headroom()
    from openwall_stud.contenders import open3d_ml_s3dis
    from openwall_stud.finetune_randlanet import (
        build_model,
        load_checkpoint,
        predict_labels,
        weight_path,
    )

    manifest = load_manifest()
    if weights == "control":
        weight = open3d_ml_s3dis._weight_path()
        fetch_error = open3d_ml_s3dis._ensure_weight(weight)
        if fetch_error:
            raise SystemExit(fetch_error)
        probe = {"torch_version": None, "torch_device": "cuda"}
        import torch

        probe["torch_version"] = torch.__version__
        for scene in manifest["scenes"]:
            points, _labels = _scene_arrays(scene)
            namespace = SimpleNamespace(points_m=points.astype(np.float32), seed=int(scene["seed"]))
            started = time.perf_counter()
            forward = open3d_ml_s3dis._forward(namespace, weight, probe)
            runtime_s = time.perf_counter() - started
            card = _card(
                stack="open3d_ml",
                rank=5,
                weights="control",
                scene=scene,
                names=forward["names"],
                pred=forward["labels"],
                runtime_s=runtime_s,
                extra={
                    "wall_names": ["wall"],
                    "path": "openwall_stud.contenders.open3d_ml_s3dis._forward",
                    "weight": str(weight),
                    "config": forward.get("config"),
                    "note": "S3DIS office classes. Wall is a semantic class, not a stud.",
                },
            )
            print(card["file_stem"], "both", card["faces_score"]["both_faces_detected"], "s", card["runtime_s"])
            _write(card)
            _refresh_summary()
        return

    if weights != "stud_finetune":
        raise SystemExit(f"unknown randlanet weights {weights}")
    model = build_model("cuda")
    meta = load_checkpoint(model, weight_path())
    # Warm the pipeline once so the timed pass is the cloud, not the first import.
    first_points, _ = _scene_arrays(manifest["scenes"][0])
    predict_labels(model, first_points.astype(np.float32))
    for scene in manifest["scenes"]:
        points, _labels = _scene_arrays(scene)
        pred, runtime_s = predict_labels(model, points.astype(np.float32))
        card = _card(
            stack="open3d_ml",
            rank=5,
            weights="stud_finetune",
            scene=scene,
            names=["clutter", "stud"],
            pred=pred,
            runtime_s=runtime_s,
            extra={
                "wall_names": [],
                "path": "openwall_stud.finetune_randlanet.predict_labels",
                "weight": str(weight_path()),
                "head_meta_epoch": (meta or {}).get("epoch"),
                "note": "Stud/clutter head. predict_labels uses per-cloud batch-norm stats. A stud label is not a wall face.",
            },
        )
        print(card["file_stem"], "both", card["faces_score"]["both_faces_detected"], "s", card["runtime_s"])
        _write(card)
        _refresh_summary()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", choices=("pointcept", "randlanet"), required=True)
    parser.add_argument("--weights", choices=("control", "stud_finetune"), required=True)
    args = parser.parse_args()
    if args.stack == "pointcept":
        run_pointcept(args.weights)
    else:
        run_randlanet(args.weights)


if __name__ == "__main__":
    main()
