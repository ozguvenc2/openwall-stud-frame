"""Phase -1 smoke for the nine-tool stud-seg bake-off.

This does not write scorecards and does not start a ranking trial.
It loads stage0_2x4_lean0.000 (seed 1, 5 mm spacing, 1 mm noise) and
checks that each installed tool can touch that cloud.

Geometry and the two supervised nets run in the interpreters named below.
Foundation-model smokes are separate commands; this file records the
geometry and supervised rows when those interpreters are the ones running.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCENE_NAME = "stage0_2x4_lean0.000"
POINTCEPT_PY = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe")
O3DML_PY = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml\Scripts\python.exe")
MAIN_PY = ROOT / ".venv" / "Scripts" / "python.exe"


def scene():
    from openwall_stud.synthetic import stage0_single_stud

    cloud = stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)
    if cloud.name != SCENE_NAME:
        raise RuntimeError(f"scene name {cloud.name} != {SCENE_NAME}")
    return cloud


def _normals(points):
    import numpy as np
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    cloud.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamKNN(knn=30)
    )
    return np.asarray(cloud.normals, dtype=np.float32)


def smoke_open3d(cloud) -> dict:
    import open3d as o3d
    from openwall_stud.open3d_baseline import run_baseline

    result = run_baseline(cloud)
    return {
        "tool": "Open3D",
        "installed": True,
        "version": o3d.__version__,
        "smoke": "yes",
        "detail": (
            f"n_points={cloud.n_points} clusters={len(result.detections)} "
            f"kept={int(result.keep_mask.sum())} runtime_s={result.runtime_s}"
        ),
    }


def smoke_pyransac(cloud) -> dict:
    import importlib.metadata
    from openwall_stud.contenders.pyransac3d_cuboid import sequential_cuboids

    fitted = sequential_cuboids(cloud.points_m, seed=cloud.seed, has_floor=False)
    n_in = 0
    clusters = fitted.get("clusters") or []
    if clusters:
        n_in = int(len(clusters[0]))
    return {
        "tool": "pyRANSAC-3D",
        "installed": True,
        "version": importlib.metadata.version("pyransac3d"),
        "smoke": "yes",
        "detail": f"n_points={cloud.n_points} first_inliers={n_in} attempts={len(fitted.get('attempts') or [])}",
    }


def smoke_pointcept(cloud) -> dict:
    import numpy as np
    import torch
    from openwall_stud.contenders.pointcept_ptv3 import _ensure_bimstruct, _cache_root, _forward
    from openwall_stud.finetune_pointcept import (
        build_model,
        collate_cloud,
        load_bimstruct_backbone,
        load_finetuned,
        train_step,
        weight_path,
    )

    cache = _cache_root()
    err = _ensure_bimstruct(cache)
    if err:
        return {
            "tool": "Pointcept",
            "installed": True,
            "version": f"torch {torch.__version__}",
            "smoke": "no",
            "error": err,
        }
    control = _forward(cloud, cache, "cuda")
    hist = control.get("class_histogram") or control.get("histogram") or []
    top = ""
    if isinstance(hist, list) and hist:
        ranked = sorted(hist, key=lambda row: int(row.get("count", 0)), reverse=True)
        top = f" top={ranked[0].get('name')}:{ranked[0].get('count')}"
    normals = _normals(cloud.points_m)
    labels = np.ones((cloud.n_points,), dtype=np.int64)
    model = build_model("cuda")
    loaded = load_bimstruct_backbone(model)
    if weight_path().is_file():
        load_finetuned(model, weight_path())
        head = "existing_2class_head_loaded"
    else:
        head = "no_saved_head"
    batch = collate_cloud(cloud.points_m, labels, normals)
    head_params = [p for n, p in model.named_parameters() if p.requires_grad and n.startswith("seg_head")]
    other = [p for n, p in model.named_parameters() if p.requires_grad and not n.startswith("seg_head")]
    groups = [{"params": head_params, "lr": 1e-3}]
    if other:
        groups.append({"params": other, "lr": 1e-4})
    optimizer = torch.optim.AdamW(groups, weight_decay=1e-4)
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
    loss = train_step(model, optimizer, batch, class_weight, grad_backbone=False)
    # Do not save. The published finetune file stays as it was.
    return {
        "tool": "Pointcept",
        "installed": True,
        "version": f"torch {torch.__version__} cuda {torch.version.cuda}",
        "smoke": "yes",
        "detail": (
            f"device={torch.cuda.get_device_name(0)} control_keys={sorted(control)[:8]}{top} "
            f"backbone_copied={loaded.get('copied')} {head} one_step_loss={loss:.4f} "
            f"official_weight_untouched={weight_path()}"
        ),
    }


def smoke_o3dml(cloud) -> dict:
    import numpy as np
    import torch
    from openwall_stud.contenders.open3d_ml_s3dis import _ensure_weight, _forward, _probe_ml, _weight_path
    from openwall_stud.finetune_randlanet import (
        build_model,
        load_checkpoint,
        load_s3dis_encoder,
        predict_labels,
        train_step,
        weight_path,
    )

    probe_text = _probe_ml()
    err = _ensure_weight(_weight_path())
    if err:
        return {
            "tool": "Open3D-ML",
            "installed": probe_text.startswith("open3d.ml.torch"),
            "version": f"torch {torch.__version__}",
            "smoke": "no",
            "error": err,
        }
    control = _forward(
        cloud,
        _weight_path(),
        {
            "torch_version": torch.__version__,
            "torch_device": torch.cuda.get_device_name(0),
        },
    )
    hist = control.get("class_histogram") or control.get("histogram") or []
    top = ""
    if isinstance(hist, list) and hist:
        ranked = sorted(hist, key=lambda row: int(row.get("count", 0)), reverse=True)
        top = f" top={ranked[0].get('name')}:{ranked[0].get('count')}"
    model = build_model("cuda")
    loaded = load_s3dis_encoder(model)
    if weight_path().is_file():
        load_checkpoint(model, weight_path())
        head = "existing_2class_head_loaded"
    else:
        head = "no_saved_head"
    pred, runtime_s = predict_labels(model, cloud.points_m)
    labels = np.ones((cloud.n_points,), dtype=np.int64)
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
    head_params = [p for n, p in model.named_parameters() if n.startswith("fc1")]
    rest = [p for n, p in model.named_parameters() if not n.startswith("fc1")]
    optimizer = torch.optim.AdamW(
        [{"params": rest, "lr": 1e-4}, {"params": head_params, "lr": 1e-3}],
        weight_decay=1e-4,
    )
    loss = train_step(model, optimizer, cloud.points_m, labels, class_weight)
    return {
        "tool": "Open3D-ML",
        "installed": True,
        "version": f"torch {torch.__version__} cuda {torch.version.cuda} open3d.ml.torch",
        "smoke": "yes",
        "detail": (
            f"device={torch.cuda.get_device_name(0)} s3dis_probe={probe_text}{top} "
            f"encoder_copied={loaded.get('copied')} {head} "
            f"dry_pred_n={int(pred.shape[0])} runtime_s={runtime_s} one_step_loss={loss:.4f}"
        ),
    }


def _run(fn, cloud) -> dict:
    try:
        row = fn(cloud)
        row.setdefault("error", "")
        row.setdefault("needs_user_at_keyboard", "no")
        return row
    except Exception as exc:
        return {
            "tool": fn.__name__,
            "installed": False,
            "version": "",
            "smoke": "no",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-2000:],
            "needs_user_at_keyboard": "no",
        }


def which() -> str:
    if os.environ.get("PHASE_NEG1_ROLE"):
        return os.environ["PHASE_NEG1_ROLE"]
    ver = ""
    try:
        import torch

        ver = torch.__version__
    except Exception:
        ver = ""
    if ver.startswith("2.7"):
        return "pointcept"
    if ver.startswith("2.13"):
        return "o3dml"
    return "geometry"


def main() -> int:
    role = which()
    cloud = scene()
    print(f"scene {cloud.name} n={cloud.n_points} seed={cloud.seed}", flush=True)
    out = ROOT / "artifacts" / "phase_neg1"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    if role == "geometry":
        rows.append(_run(smoke_open3d, cloud))
        rows.append(_run(smoke_pyransac, cloud))
    elif role == "pointcept":
        rows.append(_run(smoke_pointcept, cloud))
    elif role == "o3dml":
        rows.append(_run(smoke_o3dml, cloud))
    else:
        raise SystemExit(f"unknown role {role}")
    dest = out / f"smoke_{role}.json"
    dest.write_text(json.dumps({"scene": cloud.name, "n_points": cloud.n_points, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(dest)
    for row in rows:
        print(json.dumps({k: row[k] for k in row if k != "traceback"}))
    return 0 if all(row.get("smoke") == "yes" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
