"""Play CloudCompare RANSAC-SD knobs until one scene is one stud box.

CPU only. Does not run ranks 1, 2, 4, 5, or 6.

The grid is three phase-1 S1 leans: 0°, 0.15° about +X, and 4° about +Y.
``--full`` scores all 25 leans with the module default and writes scorecards
under ``artifacts/scorecards/phase1_s1_cc_tuned/``. It does not touch the
untuned ``r3_cloudcompare__*.json`` cards and it does not append the day table.

    python scripts/tune_cloudcompare_stud.py --self-check
    python scripts/tune_cloudcompare_stud.py --grid
    python scripts/tune_cloudcompare_stud.py --full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.cloudcompare_ransac import (  # noqa: E402
    DEFAULT_RANSAC_STUD,
    RansacStudParams,
    self_check_stud_merge,
)
from openwall_stud.one_stud import apply_verdict, stage0_bar_failures  # noqa: E402
from openwall_stud.synthetic import phase1_s1_single_stud  # noqa: E402

SCORE_DIR = ROOT / "artifacts" / "scorecards" / "phase1_s1_cc_tuned"
FIG_DIR = ROOT / "docs" / "research" / "images" / "phase1-s1-cc-tuned"
WORK_ROOT = ROOT / "artifacts" / "one_stud" / "cloudcompare" / "tune"

# Same three leans as the phase-1 representative figures.
GRID_SCENES = (
    (0.0, "none"),
    (0.15, "+X"),
    (4.0, "+Y"),
)
FULL_MAGNITUDES = (0.0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0)
FULL_AXES = ("+X", "-X", "+Y", "-Y")
REPRESENTATIVE = (
    "s1_2x4_lean0.000_axnone",
    "s1_2x4_lean0.150_ax+X",
    "s1_2x4_lean4.000_ax+Y",
)

# Each row is one knob set. The first two keep the untuned numbers so the
# merge can be compared with and without the cylinder primitive.
GRID: tuple[tuple[str, RansacStudParams], ...] = (
    (
        "untuned_plane_cylinder",
        RansacStudParams(
            epsilon_absolute_m=0.008,
            bitmap_epsilon_absolute_m=0.020,
            support_points=400,
            max_normal_dev_deg=25.0,
            primitives=("PLANE", "CYLINDER"),
        ),
    ),
    (
        "untuned_plane_only",
        RansacStudParams(
            epsilon_absolute_m=0.008,
            bitmap_epsilon_absolute_m=0.020,
            support_points=400,
            max_normal_dev_deg=25.0,
            primitives=("PLANE",),
        ),
    ),
    ("eps5_sup800_n15", RansacStudParams(epsilon_absolute_m=0.005, support_points=800, max_normal_dev_deg=15.0)),
    ("eps6_sup800_n15", RansacStudParams()),
    ("eps8_sup800_n15", RansacStudParams(epsilon_absolute_m=0.008, support_points=800, max_normal_dev_deg=15.0)),
    ("eps6_sup1500_n15", RansacStudParams(support_points=1500)),
    ("eps6_sup2000_n15", RansacStudParams(support_points=2000)),
    (
        "eps6_sup800_n25_bmp12",
        RansacStudParams(bitmap_epsilon_absolute_m=0.012, max_normal_dev_deg=25.0),
    ),
    (
        "eps10_sup800_n25",
        RansacStudParams(epsilon_absolute_m=0.010, max_normal_dev_deg=25.0),
    ),
)


def _scene(lean_deg: float, axis: str):
    return phase1_s1_single_stud(
        lean_deg=lean_deg,
        axis=axis,
        seed=2,
        spacing_m=0.005,
        noise_std_m=0.001,
        nominal="2x4",
    )


def _summarize(card: dict[str, Any]) -> dict[str, Any]:
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    merge = (card.get("implementation") or {}).get("merge") or {}
    return {
        "status": card.get("status"),
        "stage0_pass_fail": card.get("stage0_pass_fail"),
        "bar_failures": card.get("stage0_bar_failures"),
        "n_pred": det.get("n_pred"),
        "precision": det.get("precision"),
        "recall": det.get("recall"),
        "section_mm": geom.get("max_section_error_mm"),
        "length_mm": geom.get("max_length_error_mm"),
        "angle_deg": ang.get("max_abs_error_deg"),
        "n_primitive_clouds": ((card.get("implementation") or {}).get("attempt") or {}).get("n_primitive_clouds"),
        "merge_chosen": merge.get("chosen"),
        "n_long_faces": merge.get("n_long_faces"),
        "n_groups": merge.get("n_groups"),
        "runtime_s": (card.get("cost") or {}).get("runtime_s"),
    }


def _run_scene(lean_deg: float, axis: str, params: RansacStudParams, work: Path):
    from openwall_stud.contenders.cloudcompare_ransac import run_one_stud

    scene = _scene(lean_deg, axis)
    card, detections = run_one_stud(scene, params=params, work=work)
    if card.get("status") == "ran":
        apply_verdict(card)
    else:
        card["stage0_pass_fail"] = card.get("status")
        card["stage0_bar_failures"] = []
    return scene, card, detections


def _score_key(row: dict[str, Any]) -> tuple:
    """More passes, then tighter section and angle. Plane-only wins a tie."""
    passes = row["n_pass"]
    section = row["mean_section_mm"]
    angle = row["mean_angle_deg"]
    section_key = 1.0e9 if section is None else section
    angle_key = 1.0e9 if angle is None else angle
    plane_only = 0 if row["primitives"] == ["PLANE"] else 1
    return (-passes, section_key, angle_key, plane_only)


def run_grid() -> list[dict[str, Any]]:
    self_check_stud_merge()
    rows: list[dict[str, Any]] = []
    for name, params in GRID:
        scene_rows = []
        for lean_deg, axis in GRID_SCENES:
            work = WORK_ROOT / name / f"{lean_deg}_{axis.replace('+', 'p').replace('-', 'm')}"
            scene, card, _detections = _run_scene(lean_deg, axis, params, work)
            summary = _summarize(card)
            summary["scene"] = scene.name
            summary["lean_deg"] = lean_deg
            summary["axis"] = axis
            scene_rows.append(summary)
            print(
                f"{name} {scene.name} box={summary['n_pred']} "
                f"faces={summary['n_long_faces']} prim={summary['n_primitive_clouds']} "
                f"section={summary['section_mm']} angle={summary['angle_deg']} "
                f"bars={summary['stage0_pass_fail']}",
                flush=True,
            )
        measured = [item for item in scene_rows if item["section_mm"] is not None]
        angles = [item["angle_deg"] for item in measured if item["angle_deg"] is not None]
        sections = [item["section_mm"] for item in measured]
        row = {
            "name": name,
            "params": {
                "epsilon_absolute_m": params.epsilon_absolute_m,
                "bitmap_epsilon_absolute_m": params.bitmap_epsilon_absolute_m,
                "support_points": params.support_points,
                "max_normal_dev_deg": params.max_normal_dev_deg,
                "probability": params.probability,
                "primitives": list(params.primitives),
            },
            "primitives": list(params.primitives),
            "n_pass": sum(item["stage0_pass_fail"] == "pass" for item in scene_rows),
            "n_one_box": sum(item["n_pred"] == 1 for item in scene_rows),
            "mean_section_mm": None if not sections else round(sum(sections) / len(sections), 3),
            "mean_angle_deg": None if not angles else round(sum(angles) / len(angles), 5),
            "scenes": scene_rows,
        }
        rows.append(row)
    rows.sort(key=_score_key)
    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    dest = SCORE_DIR / "grid.json"
    dest.write_text(json.dumps({"winner": rows[0]["name"], "rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"grid written to {dest}", flush=True)
    print(f"best on the 3-scene grid: {rows[0]['name']} pass={rows[0]['n_pass']}/3", flush=True)
    return rows


def _full_specs() -> list[tuple[float, str]]:
    specs = [(0.0, "none")]
    for magnitude in FULL_MAGNITUDES:
        if magnitude == 0.0:
            continue
        for axis in FULL_AXES:
            specs.append((float(magnitude), axis))
    return specs


def run_full() -> None:
    self_check_stud_merge()
    from openwall_stud.one_stud_publish import publish_attempt

    params = DEFAULT_RANSAC_STUD
    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for lean_deg, axis in _full_specs():
        work = WORK_ROOT / "full" / f"{lean_deg}_{axis.replace('+', 'p').replace('-', 'm')}"
        scene, card, detections = _run_scene(lean_deg, axis, params, work)
        figure = None
        if scene.name in REPRESENTATIVE:
            slug = scene.name.replace("+", "p").replace("-", "m")
            figure = FIG_DIR / f"r3_cloudcompare__{slug}.png"
        out = SCORE_DIR / f"r3_cloudcompare__{scene.name}.json"
        publish_attempt(
            algorithm="cloudcompare",
            card=card,
            detections=detections,
            scene=scene,
            out=out,
            figure=figure,
            write_day_row=False,
        )
        summary = _summarize(card)
        summary["scene"] = scene.name
        summaries.append(summary)
        print(
            f"{scene.name} box={summary['n_pred']} section={summary['section_mm']} "
            f"angle={summary['angle_deg']} bars={summary['stage0_pass_fail']}",
            flush=True,
        )
    n_pass = sum(item["stage0_pass_fail"] == "pass" for item in summaries)
    n_one = sum(item["n_pred"] == 1 for item in summaries)
    dest = SCORE_DIR / "summary.json"
    dest.write_text(
        json.dumps(
            {
                "params": {
                    "epsilon_absolute_m": params.epsilon_absolute_m,
                    "bitmap_epsilon_absolute_m": params.bitmap_epsilon_absolute_m,
                    "support_points": params.support_points,
                    "max_normal_dev_deg": params.max_normal_dev_deg,
                    "probability": params.probability,
                    "primitives": list(params.primitives),
                },
                "n_scenes": len(summaries),
                "n_pass": n_pass,
                "n_one_box": n_one,
                "scenes": summaries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"full run {n_pass}/{len(summaries)} stage-0 pass, {n_one} one-box. {dest}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tune CloudCompare RANSAC-SD toward one stud box.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--grid", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    if not (args.self_check or args.grid or args.full):
        parser.error("pass --self-check, --grid, or --full")
    if args.self_check and not args.grid and not args.full:
        self_check_stud_merge()
        print("stud-face merge self-check passed")
        return 0
    if args.grid:
        run_grid()
    if args.full:
        run_full()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
