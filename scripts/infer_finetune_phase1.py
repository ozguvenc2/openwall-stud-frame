"""Score the fine-tuned stud class on the 25 phase-1 S1 clouds.

RandLA-Net:

    .venv-o3dml\\Scripts\\python.exe scripts/infer_finetune_phase1.py --stack randlanet

Pointcept:

    .venv\\Scripts\\python.exe scripts/infer_finetune_phase1.py --stack pointcept

Scorecards land in artifacts/scorecards/phase1_s1_finetune/ so the control
histograms in phase1_s1/ stay put.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.finetune_score import score_stud_labels  # noqa: E402
from openwall_stud.finetune_synth import (  # noqa: E402
    ensure_cloud,
    estimate_normals,
    load_manifest,
    materialize,
)
from openwall_stud.scorecard import write_scorecard  # noqa: E402
from openwall_stud.synthetic import LEAN_AXES, phase1_s1_single_stud  # noqa: E402

SCORE_DIR = ROOT / "artifacts" / "scorecards" / "phase1_s1_finetune"
MAGNITUDES = (0.0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0)


def phase1_scenes():
    yield phase1_s1_single_stud(lean_deg=0.0, axis="none", seed=2, spacing_m=0.005, noise_std_m=0.001)
    for magnitude in MAGNITUDES:
        if magnitude == 0.0:
            continue
        for axis in LEAN_AXES:
            yield phase1_s1_single_stud(
                lean_deg=magnitude,
                axis=axis,
                seed=2,
                spacing_m=0.005,
                noise_std_m=0.001,
            )


def _write(stack: str, rank: int, key: str, scene, labels, runtime_s, **kwargs) -> dict:
    card, _detections = score_stud_labels(
        scene,
        labels,
        runtime_s=runtime_s,
        rank=rank,
        **kwargs,
    )
    dest = SCORE_DIR / f"r{rank}_{key}__{scene.name}.json"
    write_scorecard(dest, card)
    angle = card["angle"]
    return {
        "scene": scene.name,
        "kind": "phase1" if scene.name.startswith("s1_") else "heldout",
        "n_stud_points": card["finetune"]["n_stud_points"],
        "stud_box": bool(card["finetune"]["stud_box"]),
        "lean_measured_deg": None if not angle["per_stud"] else angle["per_stud"][0]["measured_deg"],
        "lean_true_deg": None if not angle["per_stud"] else angle["per_stud"][0]["true_deg"],
        "abs_error_deg": None if not angle["per_stud"] else angle["per_stud"][0]["abs_error_deg"],
        "runtime_s": card["cost"]["runtime_s"],
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
    }


def run_randlanet() -> dict:
    import torch

    from openwall_stud.finetune_randlanet import build_model, load_checkpoint, predict_labels, weight_path

    if not weight_path().is_file():
        raise SystemExit(f"missing weights {weight_path()}")
    model = build_model("cuda")
    meta = load_checkpoint(model, weight_path())
    common = dict(
        algorithm_id="A5",
        algorithm="Open3D-ML RandLA-Net fine-tuned stud/clutter (synthetic)",
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware=f"cuda; torch {torch.__version__}",
        failure_modes=[
            "Trained on synthetic dressed studs and a floor slab only.",
            "RGB features are zeros.",
            "A real scan was not used.",
        ],
        implementation={
            "module": "openwall_stud.finetune_randlanet",
            "weight": str(weight_path().relative_to(ROOT)).replace("\\", "/"),
            "meta": meta,
        },
        implementation_short="RandLA-Net S3DIS encoder, 2-class head, minimal OBB on stud points.",
    )
    rows = []
    # Warm the pipeline, then time one held-in generator cloud that is not a phase-1 card.
    warm = materialize(
        {
            "kind": "stud",
            "lean_deg": 0.2,
            "axis": "+Y",
            "seed": 777,
            "noise_std_m": 0.001,
            "spacing_m": 0.005,
            "id": "time_one",
        }
    )
    predict_labels(model, warm.points_m)
    timed_pred, timed_s = predict_labels(model, warm.points_m)
    rows.append(
        _write("randlanet", 5, "open3d_ml", warm, timed_pred, timed_s, **common)
    )
    for scene in phase1_scenes():
        pred, runtime_s = predict_labels(model, scene.points_m)
        rows.append(_write("randlanet", 5, "open3d_ml", scene, pred, runtime_s, **common))
    manifest = load_manifest()
    held = [spec for spec in manifest["val"] if spec["kind"] == "stud"][:2]
    held += [spec for spec in manifest["val"] if spec["kind"] == "stud_floor"][:2]
    for spec in held:
        cloud = ensure_cloud(spec)
        scene = materialize(spec)
        scene.name = spec["id"] + "_" + scene.name
        pred, runtime_s = predict_labels(model, cloud["points"])
        # Score the generator scene. Labels came from the same spec, so the
        # cloud matches aside from normal estimation, which RandLA-Net ignores.
        if pred.shape[0] != scene.n_points:
            pred = np.asarray(pred).reshape(-1)[: scene.n_points]
        rows.append(_write("randlanet", 5, "open3d_ml", scene, pred, runtime_s, **common))
    return {"stack": "randlanet", "one_stud_s": timed_s, "rows": rows}


def run_pointcept() -> dict:
    import torch

    from openwall_stud.finetune_pointcept import (
        build_model,
        load_bimstruct_backbone,
        load_finetuned,
        predict_full,
        weight_path,
    )

    if not weight_path().is_file():
        raise SystemExit(f"missing weights {weight_path()}")
    model = build_model("cuda")
    load_bimstruct_backbone(model)
    meta = load_finetuned(model, weight_path())
    common = dict(
        algorithm_id="A4",
        algorithm="Pointcept PTv3 fine-tuned stud/clutter (synthetic)",
        license_name="MIT code; BIMStruct3D weights CC BY-NC-SA 4.0, not committed",
        hardware=f"cuda; torch {torch.__version__}",
        failure_modes=[
            "Trained on synthetic dressed studs and a floor slab only.",
            "Color features are zeros. Normals are estimated.",
            "A real scan was not used.",
            "CC BY-NC-SA base weights are not a commercial stud model.",
        ],
        implementation={
            "module": "openwall_stud.finetune_pointcept",
            "weight": str(weight_path().relative_to(ROOT)).replace("\\", "/"),
            "meta": meta,
        },
        implementation_short="PTv3 backbone plus a 2-class head, minimal OBB on stud points.",
    )
    rows = []
    warm = materialize(
        {
            "kind": "stud",
            "lean_deg": 0.2,
            "axis": "+Y",
            "seed": 777,
            "noise_std_m": 0.001,
            "spacing_m": 0.005,
            "id": "time_one",
        }
    )
    warm_normals = estimate_normals(warm.points_m)
    predict_full(model, warm.points_m, warm_normals)
    started = time.perf_counter()
    timed_pred = predict_full(model, warm.points_m, warm_normals)
    timed_s = time.perf_counter() - started
    rows.append(_write("pointcept", 4, "pointcept", warm, timed_pred, timed_s, **common))
    for scene in phase1_scenes():
        normals = estimate_normals(scene.points_m)
        started = time.perf_counter()
        pred = predict_full(model, scene.points_m, normals)
        runtime_s = time.perf_counter() - started
        rows.append(_write("pointcept", 4, "pointcept", scene, pred, runtime_s, **common))
    manifest = load_manifest()
    held = [spec for spec in manifest["val"] if spec["kind"] == "stud"][:2]
    held += [spec for spec in manifest["val"] if spec["kind"] == "stud_floor"][:2]
    for spec in held:
        cloud = ensure_cloud(spec)
        scene = materialize(spec)
        scene.name = spec["id"] + "_" + scene.name
        started = time.perf_counter()
        pred = predict_full(model, cloud["points"], cloud["normals"])
        runtime_s = time.perf_counter() - started
        rows.append(_write("pointcept", 4, "pointcept", scene, pred, runtime_s, **common))
    return {"stack": "pointcept", "one_stud_s": timed_s, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Infer fine-tuned stud labels on phase 1 S1.")
    parser.add_argument("--stack", choices=("randlanet", "pointcept"), required=True)
    args = parser.parse_args(argv)
    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    if args.stack == "randlanet":
        summary = run_randlanet()
    else:
        summary = run_pointcept()
    phase1 = [row for row in summary["rows"] if row["kind"] == "phase1"]
    boxes = sum(1 for row in phase1 if row["stud_box"])
    summary["phase1_scenes"] = len(phase1)
    summary["phase1_stud_box"] = boxes
    summary["phase1_clutter_only"] = len(phase1) - boxes
    dest = SCORE_DIR / f"summary_{args.stack}.json"
    dest.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"{args.stack}: phase1 stud boxes {boxes}/{len(phase1)}; "
        f"one-stud inference {summary['one_stud_s']:.3f}s; wrote {dest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
