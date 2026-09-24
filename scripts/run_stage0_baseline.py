"""Run the Open3D baseline on synthetic stages 0, 2, and 3 and write scorecards.

From the repo root:

    python scripts/run_stage0_baseline.py

The process exits non-zero if a stage misses its synthetic bar. Bars are the
bring-up checks in the design plan, not a field acceptance test.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.cloudcompare_ransac import main as cc_main
from openwall_stud.contenders.open3d_ml_s3dis import main as ml_main
from openwall_stud.contenders.pcl_region_grow import main as pcl_main
from openwall_stud.contenders.pointcept_ptv3 import main as pt_main
from openwall_stud.lumber import TOLERANCE_DEG
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.paint import assert_paint_rules
from openwall_stud.scorecard import write_scorecard
from openwall_stud.synthetic import stage0_single_stud, stage2_stud_and_floor, stage3_mini_wall

# Synthetic bring-up bars. A miss fails the process so a broken peeler is not
# described as a pass in the design plan.
BARS = {
    0: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    2: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    3: {"section_mm": 10.0, "length_mm": 30.0, "angle_deg": 0.10},
}


def _card(scene, run, sections: dict) -> dict:
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": "A1",
        "algorithm": "Refined Open3D stud prior",
        "rank": 1,
        "stage": scene.stage,
        "status": "ran_synthetic",
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process",
        "scene": {
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "spacing_m": scene.spacing_m,
            "noise_std_m": scene.noise_std_m,
            "n_points": scene.n_points,
            "reference": run.reference,
            "floor_found": run.floor_found,
            "removed_z_intervals_m": run.removed_z_intervals_m,
            "tolerance_deg": round(TOLERANCE_DEG, 5),
        },
        **sections,
    }


def _check(stage: int, sections: dict, label: str) -> list[str]:
    bar = BARS[stage]
    failures = []
    det = sections["detection"]
    geom = sections["geometry"]
    ang = sections["angle"]
    paint = sections["paint"]
    if det["precision"] != 1.0 or det["recall"] != 1.0:
        failures.append(f"{label}: detection P={det['precision']} R={det['recall']}")
    if geom["max_section_error_mm"] is None or geom["max_section_error_mm"] > bar["section_mm"]:
        failures.append(f"{label}: section error {geom['max_section_error_mm']} mm > {bar['section_mm']}")
    if geom["max_length_error_mm"] is None or geom["max_length_error_mm"] > bar["length_mm"]:
        failures.append(f"{label}: length error {geom['max_length_error_mm']} mm > {bar['length_mm']}")
    if ang["max_abs_error_deg"] is None or ang["max_abs_error_deg"] > bar["angle_deg"]:
        failures.append(f"{label}: angle error {ang['max_abs_error_deg']} deg > {bar['angle_deg']}")
    if any(color != "yellow" for color in paint["production_colors"]):
        failures.append(f"{label}: production paint was not all yellow")
    return failures


def _run_scene(scene, out_dir: Path) -> tuple[dict, list[str]]:
    run = run_baseline(scene)
    sections = score_run(scene, run)
    card = _card(scene, run, sections)
    dest = out_dir / f"open3d_stage{scene.stage}_{scene.name}.json"
    write_scorecard(dest, card)
    failures = _check(scene.stage, sections, scene.name)
    det = sections["detection"]
    ang = sections["angle"]
    geom = sections["geometry"]
    print(
        f"{scene.name}: P={det['precision']} R={det['recall']} "
        f"section_mm={geom['max_section_error_mm']} length_mm={geom['max_length_error_mm']} "
        f"mae_deg={ang['mae_deg']} max_angle_deg={ang['max_abs_error_deg']} "
        f"in_band_pct={ang['pct_in_band']} runtime_s={sections['cost']['runtime_s']} "
        f"ref={run.reference} -> {dest.name}"
    )
    return card, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic Open3D baseline scorecards.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "scorecards")
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    assert_paint_rules()
    failures: list[str] = []
    scenes = [
        stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1),
        stage0_single_stud(nominal="2x4", lean_deg=0.05, seed=2),
        stage0_single_stud(nominal="2x4", lean_deg=0.12, seed=3),
        stage0_single_stud(nominal="2x4", lean_deg=4.0, seed=4),
        stage0_single_stud(nominal="2x6", lean_deg=0.30, seed=5),
        stage2_stud_and_floor(nominal="2x4", lean_deg=0.20, seed=6),
        stage3_mini_wall(n_studs=4, seed=7),
    ]
    for scene in scenes:
        _, scene_failures = _run_scene(scene, args.out_dir)
        failures.extend(scene_failures)

    pcl_main(["--out", str(args.out_dir / "pcl_stub.json")])
    cc_main(["--out", str(args.out_dir / "cloudcompare_stub.json")])
    pt_main(["--out", str(args.out_dir / "pointcept_stub.json")])
    ml_main(["--out", str(args.out_dir / "open3d_ml_stub.json")])

    if failures:
        print("BARS FAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print("Synthetic bars passed. Production paint is yellow because epsilon is unlocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
