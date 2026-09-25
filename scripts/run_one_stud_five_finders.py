"""Run five stud finders on one synthetic Stage 0 stud, then stop.

Scene: dressed 2x4, lean 0.05 degrees, seed 2. Reference is generator +Z.
This script does not build a floor, a mini wall, or a lean sweep.

    python scripts/run_one_stud_five_finders.py
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.cloudcompare_ransac import run_one_stud as run_cloudcompare
from openwall_stud.contenders.common import ran_card
from openwall_stud.contenders.open3d_ml_s3dis import run_one_stud as run_open3d_ml
from openwall_stud.contenders.pcl_region_grow import run_one_stud as run_pcl
from openwall_stud.contenders.pointcept_ptv3 import run_one_stud as run_pointcept
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.one_stud_publish import publish_attempt
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.paint import assert_paint_rules
from openwall_stud.results_by_day import today_la

SCORE = ROOT / "artifacts" / "scorecards"
FIG = ROOT / "docs" / "research" / "images" / "one-stud-five-finders"
REPORT_MD = ROOT / "docs" / "research" / "16-one-stud-five-finder-run.md"
REPORT_JSON = ROOT / "docs" / "research" / "16-one-stud-five-finder-run.json"


def _versions() -> dict[str, str]:
    import matplotlib
    import numpy
    import open3d

    def dpkg(package: str) -> str:
        proc = subprocess.run(
            ["dpkg-query", "-W", "-f", "${Version}", package],
            check=False,
            capture_output=True,
            text=True,
        )
        return (proc.stdout or "").strip() or "not installed"

    gxx = subprocess.run(["g++", "--version"], check=False, capture_output=True, text=True)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "open3d": open3d.__version__,
        "numpy": numpy.__version__,
        "matplotlib": matplotlib.__version__,
        "cloudcompare": dpkg("cloudcompare"),
        "libpcl_segmentation": dpkg("libpcl-segmentation1.14"),
        "g++": (gxx.stdout or gxx.stderr or "").splitlines()[0] if gxx.returncode == 0 else "not available",
        "nvidia_smi": "absent",
    }


def _run_open3d(scene) -> tuple[dict, list]:
    run = run_baseline(scene)
    sections = score_run(scene, run)
    sections["detection"]["note"] = (
        "Refined Open3D stud prior on this one synthetic stud. "
        "Counts are this scene, not a field accuracy."
    )
    sections["angle"]["note"] = "Truth is the generator lean against +Z. Stage 0 has no floor. Not a SKIL reading."
    card = ran_card(
        algorithm_id="A1",
        algorithm="Refined Open3D stud prior",
        rank=1,
        scene=scene_record(scene),
        sections=sections,
        implementation={
            "module": "openwall_stud.open3d_baseline",
            "reference": run.reference,
            "floor_found": run.floor_found,
            "dbscan_eps_m": run.dbscan_eps_m,
            "dbscan_min_points": run.dbscan_min_points,
            "bbox_kind": "minimal_oriented",
        },
        implementation_short="Refined Open3D DBSCAN and minimal OBB. Stage 0 reference is +Z.",
    )
    return card, run.detections


def _metric_row(card: dict) -> dict[str, Any]:
    if card.get("status") != "ran":
        return {
            "status": card.get("status"),
            "pass_fail": card.get("stage0_pass_fail"),
            "detection_precision": None,
            "detection_recall": None,
            "section_err_mm": None,
            "length_err_mm": None,
            "angle_mae_deg": None,
            "angle_max_abs_deg": None,
            "paint": None,
            "runtime_s": None,
            "blocker_short": card.get("blocker_short"),
        }
    det = card["detection"]
    geom = card["geometry"]
    ang = card["angle"]
    paint = card["paint"]
    cost = card["cost"]
    return {
        "status": "ran",
        "pass_fail": card.get("stage0_pass_fail"),
        "bar_failures": card.get("stage0_bar_failures") or [],
        "detection_precision": det.get("precision"),
        "detection_recall": det.get("recall"),
        "n_pred": det.get("n_pred"),
        "section_err_mm": geom.get("max_section_error_mm"),
        "length_err_mm": geom.get("max_length_error_mm"),
        "angle_mae_deg": ang.get("mae_deg"),
        "angle_max_abs_deg": ang.get("max_abs_error_deg"),
        "paint": paint.get("production_colors"),
        "runtime_s": cost.get("runtime_s"),
        "implementation_short": card.get("implementation_short"),
    }


def _finder_extra(card: dict) -> str:
    """Run-specific sentences that must stay tied to this scorecard."""
    rank = card.get("rank")
    if rank == 2:
        assembly = ((card.get("implementation") or {}).get("cuboid_assembly") or {})
        if assembly.get("n_face_clusters") == 1:
            return (
                "\nThe printed section, length, and angle can match the Open3D row because both boxes "
                "cover nearly the whole stud. They are separate measurements. "
                f"PCL left {assembly.get('n_unassigned')} points out.\n"
            )
    if rank == 3:
        files = ((card.get("implementation") or {}).get("attempt") or {}).get("output_files") or []
        n_planes = sum(1 for name in files if "PLANE" in name.upper())
        n_cylinders = sum(1 for name in files if "CYLINDER" in name.upper())
        return (
            "\nPlanes and cylinders were both enabled. This build's `-RANSAC` call was not given a seed, "
            "so a repeat can change the primitive count. "
            f"The scorecard for this process lists {len(files)} saved primitive clouds "
            f"({n_planes} planes, {n_cylinders} cylinders). "
            "They were not merged into one stud. The matched primitive is a thin face when the section bar fails. "
            "Recall stays 1 when one primitive still lands within 0.15 m of the stud center.\n"
        )
    return ""


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        text = f"{value:.5f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _write_report(scene_info: dict, versions: dict[str, str], cards: list[dict], date: str) -> None:
    rows = [_metric_row(card) for card in cards]
    payload = {
        "doc": "docs/research/16-one-stud-five-finder-run.md",
        "date_america_los_angeles": date,
        "stopped_after": "one synthetic stud and five finders",
        "not_field_accuracy": True,
        "epsilon_locked": False,
        "scene": scene_info,
        "stage0_bars": {
            "detection": "precision = 1 and recall = 1",
            "section_mm_max": 10.0,
            "length_mm_max": 25.0,
            "angle_deg_max_abs": 0.05,
            "paint": "yellow",
        },
        "notes": [
            "Synthetic stage 0 only. Not a field measurement.",
            "A blocked_install row has null metrics. It is not a detection miss.",
            "CloudCompare -RANSAC was not given a seed, so a repeat can change the primitive count.",
        ],
        "versions": versions,
        "commands": [
            "python scripts/run_one_stud_five_finders.py",
            "python -m openwall_stud.contenders.pcl_region_grow",
            "python -m openwall_stud.contenders.cloudcompare_ransac",
            "python -m openwall_stud.contenders.pointcept_ptv3",
            "python -m openwall_stud.contenders.open3d_ml_s3dis",
        ],
        "stacks": [
            {
                "rank": card.get("rank"),
                "algorithm": card.get("algorithm"),
                "scorecard": f"artifacts/scorecards/{card.get('scorecard_name')}",
                "figure": card.get("figure"),
                "metrics": _metric_row(card),
                "blocker": card.get("blocker"),
                "implementation": card.get("implementation"),
            }
            for card in cards
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    header = (
        "| Rank | Stack | Status | P | R | Section mm | Length mm | Angle MAE deg | Paint | Runtime s | Stage 0 bars |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    )
    body = []
    for card, row in zip(cards, rows):
        paint = row.get("paint")
        if isinstance(paint, list) and paint and all(color == paint[0] for color in paint):
            paint_text = f"{paint[0]} x{len(paint)}"
        elif isinstance(paint, list) and paint:
            paint_text = ",".join(paint)
        else:
            paint_text = "—"
        body.append(
            "| {rank} | {name} | {status} | {p} | {r} | {section} | {length} | {mae} | {paint} | {runtime} | {bars} |".format(
                rank=card.get("rank"),
                name=card.get("algorithm"),
                status=row["status"],
                p=_fmt(row["detection_precision"]),
                r=_fmt(row["detection_recall"]),
                section=_fmt(row["section_err_mm"]),
                length=_fmt(row["length_err_mm"]),
                mae=_fmt(row["angle_mae_deg"]),
                paint=paint_text,
                runtime=_fmt(row["runtime_s"]),
                bars=row["pass_fail"],
            )
        )
    table = header + "\n".join(body)

    sections = []
    for card, row in zip(cards, rows):
        figure = card.get("figure") or ""
        image = ""
        if figure.startswith("docs/research/"):
            rel = figure[len("docs/research/") :]
            image = f"\n\n![{card.get('algorithm')}]({rel})\n"
        if card.get("status") == "ran":
            detail = card.get("implementation_short") or ""
            fails = card.get("stage0_bar_failures") or []
            fail_text = "None. The stage 0 synthetic bars passed on this cloud." if not fails else "; ".join(fails)
            extra = _finder_extra(card)
            sections.append(
                f"### Rank {card.get('rank')}. {card.get('algorithm')}\n\n"
                f"Status: `ran`. Stage 0 bars: `{row['pass_fail']}`.\n\n"
                f"{detail}\n"
                f"{extra}"
                f"\nBar notes: {fail_text}\n"
                f"{image}"
            )
        else:
            sections.append(
                f"### Rank {card.get('rank')}. {card.get('algorithm')}\n\n"
                f"Status: `blocked_install`. Metrics were not filled.\n\n"
                f"{card.get('blocker')}\n"
                f"{image}"
            )

    version_lines = "\n".join(f"- `{key}`: {value}" for key, value in versions.items())
    text = f"""# One synthetic stud, five finders

Date (America/Los_Angeles): **{date}**. This note records one Stage 0 cloud through the five ranked finders, then stops. It is a synthetic bring-up. It is not a field measurement, not a phone-LiDAR result, and not a stage 2, stage 3, or lean-sweep result.

Machine-readable twin: [16-one-stud-five-finder-run.json](16-one-stud-five-finder-run.json).

## Scene

One call to `stage0_single_stud` in `src/openwall_stud/synthetic.py`.

| | |
| --- | --- |
| Nominal | dressed 2×4 |
| Lean | {scene_info['lean_deg']}° about +X |
| Seed | {scene_info['seed']} |
| Scene id | `{scene_info['name']}` |
| Points | {scene_info['n_points']} |
| Spacing | {scene_info['spacing_m']} m |
| Noise | {scene_info['noise_std_m']} m Gaussian |
| Angle reference | generator +Z (`gravity_z_no_floor_plane`). No floor was fit. The cloud was not rotated. |

The same arrays were passed to every finder. Device ε is unlocked, so a production color is yellow whenever a box exists.

## Stage 0 bars

From the design plan. These bars are for this generator, not a jobsite.

| Check | Bar |
| --- | --- |
| Detection | precision = 1 and recall = 1 |
| Section | max absolute error ≤ 10 mm |
| Length | max absolute error ≤ 25 mm |
| Angle | max absolute error ≤ 0.05° |
| Paint | every production color yellow |

## Result

{table}

Empty metric cells were not measured. `blocked_install` is not a detection miss. A detection miss would be precision or recall filled in from a finished segmentation.

## Versions

{version_lines}

## Commands

From the repo root, with `PYTHONPATH=src` for the module entry points:

```bash
python scripts/run_one_stud_five_finders.py
python -m openwall_stud.contenders.pcl_region_grow
python -m openwall_stud.contenders.cloudcompare_ransac
python -m openwall_stud.contenders.pointcept_ptv3
python -m openwall_stud.contenders.open3d_ml_s3dis
```

The module commands repeat this same stud. `python scripts/run_stage0_baseline.py` is unchanged: it still scores Open3D on stages 0, 2, and 3 and writes null stubs for the other four (`--stub`). It was not the command for this note.

## Finders

{chr(10).join(sections)}

## What this run did not do

No second lean, no stage 2 floor, no stage 3 mini wall, no real scan, no SKIL reading, no weight download, and no claim that a synthetic pass is field accuracy. S3DIS mIoU and Özkan's roof-beam percentages are not stud scores and are not copied into the table above.
"""
    REPORT_MD.write_text(text, encoding="utf-8")


def main() -> int:
    assert_paint_rules()
    scene = make_scene()
    info = scene_record(scene)
    print(
        f"Scene {info['name']} points={info['n_points']} lean={info['lean_deg']} seed={info['seed']}"
    )
    jobs = [
        ("open3d", "one_stud_open3d.json", FIG / "01-open3d.png", lambda: _run_open3d(scene)),
        ("pcl", "one_stud_pcl.json", FIG / "02-pcl.png", lambda: run_pcl(scene)),
        ("cloudcompare", "one_stud_cloudcompare.json", FIG / "03-cloudcompare.png", lambda: run_cloudcompare(scene)),
        ("pointcept", "one_stud_pointcept.json", FIG / "04-pointcept.png", lambda: run_pointcept(scene)),
        ("open3d_ml", "one_stud_open3d_ml.json", FIG / "05-open3d-ml.png", lambda: run_open3d_ml(scene)),
    ]
    cards = []
    for algorithm, filename, figure, runner in jobs:
        print(f"--- {algorithm} ---")
        card, detections = runner()
        publish_attempt(
            algorithm=algorithm,
            card=card,
            detections=detections,
            scene=scene,
            out=SCORE / filename,
            figure=figure,
            write_day_row=True,
        )
        row = _metric_row(card)
        print(
            f"{algorithm}: status={row['status']} bars={row['pass_fail']} "
            f"P={row['detection_precision']} R={row['detection_recall']} "
            f"section={row['section_err_mm']} length={row['length_err_mm']} "
            f"mae={row['angle_mae_deg']} runtime={row['runtime_s']}"
        )
        cards.append(card)
    versions = _versions()
    _write_report(info, versions, cards, today_la())
    print(f"Wrote {REPORT_MD}")
    print("Stopped after one stud and five finders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
