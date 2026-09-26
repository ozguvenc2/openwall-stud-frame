"""First-round score of stage0_2x4_lean0.000 only.

Uses the existing stud-bar scorecard and the existing control-forward card.
Does not walk the rest of the curriculum and does not touch one_stud_*.json.

    .venv\\Scripts\\python.exe scripts/phase_neg1_stage0_round.py --role geometry
    ranks45 .venv: --role pointcept
    ranks45 .venv-o3dml: --role o3dml
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.synthetic import stage0_single_stud  # noqa: E402

SCENE_NAME = "stage0_2x4_lean0.000"
OUT = ROOT / "artifacts" / "scorecards"


def scene():
    cloud = stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)
    if cloud.name != SCENE_NAME:
        raise SystemExit(f"scene name {cloud.name} != {SCENE_NAME}")
    return cloud


def _summary(algorithm: str, card: dict) -> dict:
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    cost = card.get("cost") or {}
    return {
        "algorithm": algorithm,
        "scorecard": card.get("scorecard_name"),
        "status": card.get("status"),
        "pass_fail": card.get("stage0_pass_fail"),
        "precision": det.get("precision"),
        "recall": det.get("recall"),
        "section_mm": geom.get("max_section_error_mm"),
        "length_mm": geom.get("max_length_error_mm"),
        "angle_mae_deg": ang.get("mae_deg"),
        "runtime_s": cost.get("runtime_s"),
        "stud_metrics_scored": card.get("stud_metrics_scored", True),
    }


def run_geometry() -> list[dict]:
    from openwall_stud.angle_reference import REFERENCE_GENERATOR_Z, scene_has_floor
    from openwall_stud.contenders.pcl_region_grow import run_one_stud as run_pcl
    from openwall_stud.contenders.pyransac3d_cuboid import run_one_stud as run_pyransac
    from openwall_stud.one_stud_publish import publish_attempt
    from openwall_stud.open3d_baseline import run_baseline, score_run
    from openwall_stud.results_by_day import append_day_row
    from openwall_stud.scorecard import write_scorecard

    cloud = scene()
    rows = []

    run = run_baseline(cloud)
    sections = score_run(cloud, run)
    if scene_has_floor(cloud) or run.reference != REFERENCE_GENERATOR_Z:
        raise SystemExit(f"unexpected angle reference {run.reference}")
    card = {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": "A1",
        "algorithm": "Refined Open3D stud prior",
        "rank": 1,
        "stage": cloud.stage,
        "status": "ran_synthetic",
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process",
        "scene": {
            "name": cloud.name,
            "description": cloud.description,
            "seed": cloud.seed,
            "spacing_m": cloud.spacing_m,
            "noise_std_m": cloud.noise_std_m,
            "n_points": cloud.n_points,
            "lean_deg": cloud.studs[0].lean_deg,
            "reference": run.reference,
            "floor_found": run.floor_found,
            "removed_z_intervals_m": run.removed_z_intervals_m,
        },
        **sections,
    }
    dest = OUT / f"open3d_stage0_{cloud.name}.json"
    card["scorecard_name"] = dest.name
    write_scorecard(dest, card)
    det = sections["detection"]
    geom = sections["geometry"]
    ang = sections["angle"]
    paint = sections["paint"]
    failures = []
    if det["precision"] != 1.0 or det["recall"] != 1.0:
        failures.append("detection")
    if geom["max_section_error_mm"] is None or geom["max_section_error_mm"] > 10.0:
        failures.append("section")
    if geom["max_length_error_mm"] is None or geom["max_length_error_mm"] > 25.0:
        failures.append("length")
    if ang["max_abs_error_deg"] is None or ang["max_abs_error_deg"] > 0.05:
        failures.append("angle")
    if any(color != "yellow" for color in paint["production_colors"]):
        failures.append("paint")
    verdict = "fail" if failures else "pass"
    append_day_row(
        algorithm="open3d",
        stage=0,
        scene=cloud.name,
        ground_truth_source="synthetic",
        pass_fail=verdict,
        notes=(
            "Synthetic generator. device ε unlocked, so paint_correct_pct counts yellow "
            f"production colors only. Scorecard: {dest.name}."
        ),
        card=card,
        root=ROOT,
    )
    row = _summary("open3d", card)
    row["pass_fail"] = verdict
    rows.append(row)

    for algorithm, runner in (("pcl", run_pcl), ("pyransac3d", run_pyransac)):
        card, detections = runner(cloud)
        dest = OUT / f"{algorithm}_stage0_{cloud.name}.json"
        publish_attempt(
            algorithm=algorithm,
            card=card,
            detections=detections,
            scene=cloud,
            out=dest,
            figure=None,
            write_day_row=True,
        )
        rows.append(_summary(algorithm, card))
    return rows


def run_pointcept() -> list[dict]:
    from openwall_stud.contenders.pointcept_ptv3 import run_one_stud
    from openwall_stud.finetune_pointcept import (
        build_model,
        load_bimstruct_backbone,
        load_finetuned,
        predict_full,
        weight_path,
    )
    from openwall_stud.finetune_score import score_stud_labels
    from openwall_stud.finetune_synth import estimate_normals
    from openwall_stud.one_stud_publish import publish_attempt
    from openwall_stud.scorecard import write_scorecard

    cloud = scene()
    card, detections = run_one_stud(cloud)
    dest = OUT / f"pointcept_stage0_{cloud.name}.json"
    publish_attempt(
        algorithm="pointcept",
        card=card,
        detections=detections,
        scene=cloud,
        out=dest,
        figure=None,
    )
    rows = [_summary("pointcept", card)]

    model = build_model("cuda")
    load_bimstruct_backbone(model)
    meta = load_finetuned(model, weight_path())
    normals = estimate_normals(cloud.points_m)
    started = time.perf_counter()
    labels = predict_full(model, cloud.points_m, normals)
    runtime_s = time.perf_counter() - started
    ft_card, _ = score_stud_labels(
        cloud,
        labels,
        runtime_s=runtime_s,
        algorithm_id="A4",
        algorithm="Pointcept PTv3 fine-tuned stud/clutter (synthetic)",
        rank=4,
        license_name="MIT code; BIMStruct3D weights CC BY-NC-SA 4.0, not committed",
        hardware="cuda",
        failure_modes=["Trained on synthetic dressed studs only.", "Color features are zeros."],
        implementation={"weight": str(weight_path()), "meta": meta},
        implementation_short="PTv3 backbone plus a 2-class head, minimal OBB on stud points.",
    )
    from openwall_stud.one_stud import apply_verdict

    apply_verdict(ft_card)
    ft_dest = OUT / f"pointcept_finetune_stage0_{cloud.name}.json"
    ft_card["scorecard_name"] = ft_dest.name
    write_scorecard(ft_dest, ft_card)
    rows.append(_summary("pointcept_finetune", ft_card))
    return rows


def run_o3dml() -> list[dict]:
    import torch

    from openwall_stud.contenders.open3d_ml_s3dis import run_one_stud
    from openwall_stud.finetune_randlanet import (
        build_model,
        load_checkpoint,
        predict_labels,
        weight_path,
    )
    from openwall_stud.finetune_score import score_stud_labels
    from openwall_stud.one_stud import apply_verdict
    from openwall_stud.one_stud_publish import publish_attempt
    from openwall_stud.scorecard import write_scorecard

    cloud = scene()
    card, detections = run_one_stud(cloud)
    dest = OUT / f"open3d_ml_stage0_{cloud.name}.json"
    publish_attempt(
        algorithm="open3d_ml",
        card=card,
        detections=detections,
        scene=cloud,
        out=dest,
        figure=None,
    )
    rows = [_summary("open3d_ml", card)]

    model = build_model("cuda")
    meta = load_checkpoint(model, weight_path())
    labels, runtime_s = predict_labels(model, cloud.points_m)
    ft_card, _ = score_stud_labels(
        cloud,
        labels,
        runtime_s=runtime_s,
        algorithm_id="A5",
        algorithm="Open3D-ML RandLA-Net fine-tuned stud/clutter (synthetic)",
        rank=5,
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware=f"cuda; torch {torch.__version__}",
        failure_modes=["Trained on synthetic dressed studs and a floor slab only.", "RGB features are zeros."],
        implementation={"weight": str(weight_path()), "meta": meta},
        implementation_short="RandLA-Net S3DIS encoder, 2-class head, minimal OBB on stud points.",
    )
    apply_verdict(ft_card)
    ft_dest = OUT / f"open3d_ml_finetune_stage0_{cloud.name}.json"
    ft_card["scorecard_name"] = ft_dest.name
    write_scorecard(ft_dest, ft_card)
    rows.append(_summary("open3d_ml_finetune", ft_card))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage0 lean 0 first round for the tools that smoked.")
    parser.add_argument("--role", choices=("geometry", "pointcept", "o3dml"), required=True)
    args = parser.parse_args(argv)
    if args.role == "geometry":
        rows = run_geometry()
    elif args.role == "pointcept":
        rows = run_pointcept()
    else:
        rows = run_o3dml()
    dest = ROOT / "artifacts" / "phase_neg1" / f"stage0_round_{args.role}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
