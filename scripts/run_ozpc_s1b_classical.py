"""S1b bow and bow-wall through the classical ranks that run on Oz_PC.

Open3D, the NumPy PCL stand-in (native PCL if that binary runs), CloudCompare
RANSAC-SD, and pyRANSAC-3D. The four scenes are the S1b probes already defined
for rank 1 in scripts/run_curriculum_through_room.py. This script does not
re-score the synthetic room and does not touch corner PRs #23–#25.

Scorecards: artifacts/scorecards/ozpc_s1b/

Device epsilon stays unlocked. Production paint stays yellow.
Rigid stage bars are recorded on the day row. They are not a bow-amplitude error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.cloudcompare_ransac import run_one_stud as run_cloudcompare
from openwall_stud.contenders.common import ran_card
from openwall_stud.contenders.pcl_region_grow import run_one_stud as run_pcl
from openwall_stud.contenders.pyransac3d_cuboid import run_one_stud as run_pyransac
from openwall_stud.one_stud import scene_record
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.paint import assert_paint_rules
from openwall_stud.results_by_day import append_day_row, today_la
from openwall_stud.scorecard import write_scorecard
from openwall_stud.synthetic import s1b_bow_wall, s1b_bowed_stud

OUT = ROOT / "artifacts" / "scorecards" / "ozpc_s1b"
REPORT_MD = ROOT / "docs" / "research" / "25-ozpc-sam2-s1b.md"
REPORT_JSON = ROOT / "docs" / "research" / "25-ozpc-sam2-s1b.json"

# Same numeric bars the curriculum script uses. S1b is still a probe.
BARS = {
    0: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    3: {"section_mm": 10.0, "length_mm": 30.0, "angle_deg": 0.10},
}


def scenes():
    return [
        s1b_bowed_stud(bow_m=0.00635, lean_deg=0.0, seed=40),
        s1b_bowed_stud(bow_m=0.00635, lean_deg=0.30, seed=42),
        s1b_bowed_stud(bow_m=0.01905, lean_deg=0.0, seed=43),
        s1b_bow_wall(n_studs=3, bow_slot=1, bow_m=0.00635, leans_deg=(0.0, 0.0, 0.20), seed=41),
    ]


def _open3d(scene):
    run = run_baseline(scene)
    sections = score_run(scene, run)
    sections["detection"]["note"] = (
        "Refined Open3D on this S1b probe. Counts are this synthetic scene, not a field accuracy."
    )
    sections["angle"]["note"] = (
        "Truth is the generator chord against the reference this run used. "
        "A bow amplitude is not this angle. Not a SKIL reading."
    )
    card = ran_card(
        algorithm_id="A1",
        algorithm="Refined Open3D stud prior",
        rank=1,
        scene=scene_record(scene),
        sections=sections,
        implementation={
            "reference": run.reference,
            "floor_found": run.floor_found,
            "dbscan_eps_m": run.dbscan_eps_m,
        },
        implementation_short="Refined Open3D on an S1b probe. Oz_PC.",
    )
    card["stage"] = scene.stage
    return card


def _bar_failures(scene, card: dict) -> list[str]:
    bars = BARS.get(scene.stage)
    if not bars:
        return []
    failures = []
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    paint = card.get("paint") or {}
    if det.get("precision") != 1.0 or det.get("recall") != 1.0:
        failures.append(f"detection P={det.get('precision')} R={det.get('recall')}")
    section = geom.get("max_section_error_mm")
    if section is None or section > bars["section_mm"]:
        failures.append(f"section {section} mm > {bars['section_mm']}")
    length = geom.get("max_length_error_mm")
    if length is None or length > bars["length_mm"]:
        failures.append(f"length {length} mm > {bars['length_mm']}")
    angle = ang.get("max_abs_error_deg")
    if angle is None or angle > bars["angle_deg"]:
        failures.append(f"angle {angle} deg > {bars['angle_deg']}")
    colors = list(paint.get("production_colors") or [])
    if colors and any(color != "yellow" for color in colors):
        failures.append(f"paint {colors}")
    if not colors and card.get("status") == "ran":
        failures.append("no production color")
    return failures


def _store(key: str, rank: int, scene, card: dict) -> Path:
    card["curriculum"] = "s1b"
    card["machine"] = "Oz_PC"
    card["stage_gate"] = False
    scene_meta = getattr(scene, "meta", None) or {}
    card["scene"]["n_studs"] = len(scene.studs)
    card["scene"]["bow_m"] = scene_meta.get("bow_m")
    card["scene"]["bow_axis"] = scene_meta.get("bow_axis")
    card["scene"]["chord_note"] = "Stored long axis is the chord. Section error is not a bow amplitude."
    failures = _bar_failures(scene, card)
    card["rigid_bar_failures"] = failures
    card["rigid_bars_note"] = (
        "These are the rigid dressed-stud bars. A bow fattens the section. "
        "This list is not a bow-amplitude error and not a field acceptance test."
    )
    dest = OUT / f"r{rank}_{key}__{scene.name}.json"
    write_scorecard(dest, card)
    status = card.get("status")
    if status in {"blocked_install", "stub_not_run", "not_run"}:
        verdict = status
        stored = None
    else:
        verdict = "fail" if failures else "pass"
        stored = card
    append_day_row(
        algorithm=key,
        stage=int(scene.stage),
        scene=scene.name,
        ground_truth_source="synthetic",
        pass_fail=verdict,
        notes=(
            f"Oz_PC S1b probe. Not a stage gate. Rigid bars: {verdict}. "
            f"Device epsilon unlocked. Scorecard: ozpc_s1b/{dest.name}."
        ),
        card=stored,
    )
    print(
        f"{key} {scene.name} status={status} bars={verdict} "
        f"P={card['detection'].get('precision')} R={card['detection'].get('recall')} "
        f"section={card['geometry'].get('max_section_error_mm')}",
        flush=True,
    )
    return dest


def run() -> None:
    assert_paint_rules()
    OUT.mkdir(parents=True, exist_ok=True)
    runners = {
        "open3d": _open3d,
        "pcl": run_pcl,
        "cloudcompare": run_cloudcompare,
        "pyransac3d": run_pyransac,
    }
    ranks = {"open3d": 1, "pcl": 2, "cloudcompare": 3, "pyransac3d": 6}
    for scene in scenes():
        for key, runner in runners.items():
            result = runner(scene)
            card = result[0] if isinstance(result, tuple) else result
            _store(key, ranks[key], scene, card)


def write_report() -> None:
    cards = []
    for path in sorted(OUT.glob("r*.json")):
        cards.append(json.loads(path.read_text(encoding="utf-8")))
    sam_path = ROOT / "artifacts" / "scorecards" / "curriculum" / "sam2_rank7_ozpc.json"
    sam = json.loads(sam_path.read_text(encoding="utf-8")) if sam_path.exists() else None
    payload = {"date": today_la(), "machine": "Oz_PC", "writer": "Other", "cards": cards, "sam2": sam}
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Oz_PC: SAM 2 rank 7 measured, and S1b on the classical ranks",
        "",
        f"Date (America/Los_Angeles): **{payload['date']}**. Machine: **Oz_PC** (RTX 4080 SUPER). Writer: **Other**.",
        "",
        "Cloud PR [#26](https://github.com/ozguvenc2/openwall-stud-frame/pull/26) already ranks SAM 2 as bake-off rank 7 and scores Open3D through a synthetic room. This note is the Oz_PC continuation: one SAM 2 forward pass, and the S1b probes through Open3D, the PCL/NumPy cuboid, CloudCompare, and pyRANSAC-3D. Corner phase-2 (PRs #23–#25) is not a gate.",
        "",
        "Device epsilon is unlocked. Production paint is yellow. A bow row's angle is the chord. The rigid bars on the day table are not a bow-amplitude error.",
        "",
        "## SAM 2",
        "",
    ]
    if sam is None:
        lines.append("No Oz_PC SAM 2 card was found. Status is not_run. Metrics were not filled.")
    else:
        impl = sam.get("implementation") or {}
        lines.append(f"Status: **{sam.get('status')}**. {sam.get('blocker_short') or ''}")
        lines.append("")
        if impl:
            lines.append(f"Checkpoint: `{impl.get('model_id')}`. Device: {impl.get('device')}. Torch: {impl.get('torch')}.")
            lines.append("")
            agree = impl.get("pixel_agreement_with_generator_stud") or {}
            if agree:
                lines.append(
                    f"Pixel agreement with the generator stud raster: intersection {agree.get('intersection_px')}, "
                    f"union {agree.get('union_px')}, ratio {agree.get('ratio')}. {agree.get('note')}"
                )
                lines.append("")
            lines.append(f"Lifted points: {impl.get('n_lifted_points')}. Part counts: `{json.dumps(impl.get('lifted_part_counts'))}`.")
            lines.append("")
            if impl.get("load_warnings"):
                lines.append("Load warning stored on the card:")
                lines.append("")
                for warning in impl["load_warnings"]:
                    lines.append(f"- {warning}")
                lines.append("")
        det = sam.get("detection") or {}
        geom = sam.get("geometry") or {}
        ang = sam.get("angle") or {}
        lines.append(
            f"Scorecard: P={det.get('precision')} R={det.get('recall')} "
            f"section={geom.get('max_section_error_mm')} mm length={geom.get('max_length_error_mm')} mm "
            f"MAE={ang.get('mae_deg')} ° paint={ (sam.get('paint') or {}).get('production_colors') }."
        )
        lines.append("")
        box = sam.get("visible_box")
        if box:
            lines.append(f"Visible box (kept or dropped): `{json.dumps(box)}`.")
            lines.append("")
    lines.extend(
        [
            "The image is the scaffold camera from `sam2_mask.default_stud_camera` on the one-stud 0.05° cloud. The prompt is the centroid of generator stud pixels. A pure LAS or PLY still skips this rank.",
            "",
            "## S1b classical scorecards",
            "",
            "| Rank | Scene | Status | Rigid bars | P | R | Section mm | Length mm | MAE ° | Paint |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    def fmt(value):
        if value is None:
            return "null"
        if isinstance(value, float):
            return f"{value:.5g}"
        return str(value)

    for card in cards:
        scene = (card.get("scene") or {}).get("name")
        paint = (card.get("paint") or {}).get("production_colors") or []
        paint_text = "null" if not paint else ("yellow x%d" % len(paint) if all(c == "yellow" for c in paint) else ",".join(paint))
        lines.append(
            f"| {card.get('rank')} | `{scene}` | {card.get('status')} | "
            f"{'fail' if card.get('rigid_bar_failures') else 'pass'} | "
            f"{fmt((card.get('detection') or {}).get('precision'))} | "
            f"{fmt((card.get('detection') or {}).get('recall'))} | "
            f"{fmt((card.get('geometry') or {}).get('max_section_error_mm'))} | "
            f"{fmt((card.get('geometry') or {}).get('max_length_error_mm'))} | "
            f"{fmt((card.get('angle') or {}).get('mae_deg'))} | {paint_text} |"
        )
    lines.extend(
        [
            "",
            "Open3D on these four scenes was already measured on the cloud curriculum. The rows above are the same generator calls on Oz_PC, plus ranks 2, 3, and 6. Rank 3 is one box per RANSAC primitive, not the tuned face merge on PR #22.",
            "",
            "A room was not re-run here. Rank 1 on `stage5_room_bay_lot62_look` stays the cloud card in doc 24. Ranks 2–7 on that room stay not_run.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT_MD}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if args.report_only:
        write_report()
    else:
        run()
        write_report()
