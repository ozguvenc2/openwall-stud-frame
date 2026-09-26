"""Phase 1 smoke: full-room heads load, geometry tools still run.

Roles use the interpreter that already owns that stack on Oz_PC.

    .venv\\Scripts\\python.exe scripts/smoke_fullroom_phase1.py --role geometry
    C:\\Repos\\openwall-stud-frame-ranks45\\.venv\\Scripts\\python.exe scripts/smoke_fullroom_phase1.py --role pointcept
    C:\\Repos\\openwall-stud-frame-ranks45\\.venv-o3dml\\Scripts\\python.exe scripts/smoke_fullroom_phase1.py --role randlanet

Does not write a catch table and does not rewrite Experiment 1 weights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.finetune_fullroom import (  # noqa: E402
    EXPERIMENT1_WEIGHTS,
    WEIGHT_DIR,
    ensure_cloud,
    load_manifest,
    materialize,
)

OUT = ROOT / "artifacts" / "fullroom" / "phase1_smoke.json"


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _experiment1_hashes() -> dict[str, str | None]:
    return {str(path.relative_to(ROOT)): _sha256(path) for path in EXPERIMENT1_WEIGHTS}


def _val_spec() -> dict:
    manifest = load_manifest()
    return manifest["val"][0]


def smoke_geometry() -> dict:
    from openwall_stud.contenders.pyransac3d_cuboid import _fit_once
    from openwall_stud.open3d_baseline import run_baseline
    from openwall_stud.region_grow import grow_labels

    spec = _val_spec()
    scene = materialize(spec)
    started = time.perf_counter()
    run = run_baseline(scene)
    open3d_s = round(time.perf_counter() - started, 3)
    slot0 = scene.stud_slot == 0
    stud_points = scene.points_m[slot0]
    started = time.perf_counter()
    fit = _fit_once(stud_points, scene.seed)
    pyransac_s = round(time.perf_counter() - started, 3)
    n_inliers = int(len(np.asarray(fit.inliers)))
    work = ROOT / "artifacts" / "fullroom" / "pcl_smoke"
    started = time.perf_counter()
    _labels, provenance = grow_labels(scene.points_m, work)
    pcl_s = round(time.perf_counter() - started, 3)
    return {
        "role": "geometry",
        "scene_id": spec["id"],
        "seed": spec["seed"],
        "n_studs": len(scene.studs),
        "n_points": scene.n_points,
        "open3d": {
            "runnable": True,
            "runtime_s": open3d_s,
            "n_detections": len(run.detections),
        },
        "pyransac3d": {
            "runnable": True,
            "runtime_s": pyransac_s,
            "scope": "first stud points only, existing Cuboid.fit thresholds",
            "n_inliers": n_inliers,
            "n_stud_points": int(slot0.sum()),
        },
        "pcl": {
            "runnable": True,
            "runtime_s": pcl_s,
            "native_pcl_region_growing": bool(provenance.get("native_pcl_region_growing")),
            "provenance_keys": sorted(provenance.keys()),
        },
    }


def smoke_pointcept() -> dict:
    import torch

    from openwall_stud.finetune_pointcept import build_model, load_bimstruct_backbone, load_finetuned, predict_full

    path = WEIGHT_DIR / "pointcept_stud_2class_fullroom.pth"
    if not path.is_file():
        raise SystemExit(f"missing full-room Pointcept head {path}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    spec = _val_spec()
    cloud = ensure_cloud(spec)
    model = build_model("cuda")
    load_bimstruct_backbone(model)
    load_finetuned(model, path)
    started = time.perf_counter()
    pred = predict_full(model, cloud["points"], cloud["normals"])
    runtime_s = round(time.perf_counter() - started, 3)
    classes = sorted(int(value) for value in set(pred.tolist()))
    if classes != [0, 1]:
        raise SystemExit(f"Pointcept prediction classes {classes}, want both clutter and stud")
    return {
        "role": "pointcept",
        "weight": str(path.relative_to(ROOT)),
        "scene_id": spec["id"],
        "runtime_s": runtime_s,
        "classes": classes,
        "n_points": int(pred.shape[0]),
        "n_stud_pred": int((pred == 1).sum()),
        "n_clutter_pred": int((pred == 0).sum()),
    }


def smoke_randlanet() -> dict:
    import torch

    from openwall_stud.finetune_randlanet import build_model, load_checkpoint, predict_labels

    path = WEIGHT_DIR / "randlanet_stud_2class_fullroom.pth"
    if not path.is_file():
        raise SystemExit(f"missing full-room RandLA-Net head {path}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    spec = _val_spec()
    cloud = ensure_cloud(spec)
    model = build_model("cuda")
    load_checkpoint(model, path)
    started = time.perf_counter()
    pred, runtime_s = predict_labels(model, cloud["points"])
    classes = sorted(int(value) for value in set(pred.tolist()))
    if classes != [0, 1]:
        raise SystemExit(f"RandLA-Net prediction classes {classes}, want both clutter and stud")
    return {
        "role": "randlanet",
        "weight": str(path.relative_to(ROOT)),
        "scene_id": spec["id"],
        "runtime_s": round(runtime_s, 3),
        "load_to_predict_s": round(time.perf_counter() - started, 3),
        "classes": classes,
        "n_points": int(pred.shape[0]),
        "n_stud_pred": int((pred == 1).sum()),
        "n_clutter_pred": int((pred == 0).sum()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke full-room heads and geometry tools.")
    parser.add_argument("--role", choices=("geometry", "pointcept", "randlanet"), required=True)
    args = parser.parse_args(argv)
    before = _experiment1_hashes()
    if args.role == "geometry":
        row = smoke_geometry()
    elif args.role == "pointcept":
        row = smoke_pointcept()
    else:
        row = smoke_randlanet()
    after = _experiment1_hashes()
    if before != after:
        raise SystemExit("Experiment 1 checkpoint bytes changed during the smoke")
    row["experiment1_sha256_unchanged"] = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if OUT.is_file():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
    existing[args.role] = row
    OUT.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, indent=2), flush=True)
    print(f"wrote {OUT.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
