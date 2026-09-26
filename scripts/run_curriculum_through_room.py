"""Curriculum continuation through a synthetic room, plus the SAM 2 scaffold.

From the repo root:

    python scripts/run_curriculum_through_room.py

Stage 0 and the original stage-2 and stage-3 Open3D cards are linked, not
re-measured. New straight-stud scenes at 1 mm noise use the existing bars.
Bow (S1b), 2 mm noise, and the stage-5 room are probes: their cards are
written either way. Ranks 2–6 are not re-run on the room. SAM 2 does not
invent a mask. Stages 6 and 7 stay null.

Device epsilon stays unlocked. Production paint stays yellow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.scorecard import append_day_row, empty_sections, read_scorecard, write_scorecard
from openwall_stud.contenders.sam2_mask import (
    blocked_sam2_card,
    control_card,
    default_stud_camera,
    generator_mask_control,
    probe_install,
    raster_nearest,
    save_part_png,
)
from openwall_stud.angle_reference import (
    REFERENCE_FLOOR,
    REFERENCE_GENERATOR_Z,
    scene_has_floor,
)
from openwall_stud.lumber import TOLERANCE_DEG
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.paint import assert_paint_rules
from openwall_stud.synthetic import (
    s1b_bow_wall,
    s1b_bowed_stud,
    stage0_single_stud,
    stage2_stud_and_floor,
    stage3_mini_wall,
    stage5_room_bay,
)

# Same bring-up bars as scripts/run_stage0_baseline.py. Stage 5 has none.
BARS = {
    0: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    2: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    3: {"section_mm": 10.0, "length_mm": 30.0, "angle_deg": 0.10},
}

LINKED = {
    0: [
        "open3d_stage0_stage0_2x4_lean0.000.json",
        "open3d_stage0_stage0_2x4_lean0.050.json",
        "open3d_stage0_stage0_2x4_lean0.120.json",
        "open3d_stage0_stage0_2x4_lean4.000.json",
        "open3d_stage0_stage0_2x6_lean0.300.json",
    ],
    2: ["open3d_stage2_stage2_2x4_lean0.200.json"],
    3: ["open3d_stage3_stage3_mini_wall_4.json"],
}

ROOM_STUBS = (
    ("pcl", 2, "A2", "PCL region-grow cuboid", "PCL / the NumPy port was not re-run on this room."),
    ("cloudcompare", 3, "A3", "CloudCompare RANSAC-SD", "CloudCompare was not launched on this room."),
    ("pointcept", 4, "A4", "Pointcept PTv3", "No GPU weights on this process. Not a control pass."),
    ("open3d_ml", 5, "A5", "Open3D-ML RandLA-Net", "No GPU weights on this process. Not a control pass."),
    ("pyransac3d", 6, "A6", "pyRANSAC-3D sequential cuboid", "Not re-run on this room. Rank 1 is the classical pass."),
    (
        "sam2",
        7,
        "B7",
        "SAM 2 image/video mask",
        "Not run on the room. The one-stud scaffold is a separate card. No SAM 2 mask.",
    ),
)


def _failures(stage: int, sections: dict, label: str) -> list[str]:
    bar = BARS[stage]
    failures = []
    det = sections["detection"]
    geom = sections["geometry"]
    ang = sections["angle"]
    paint = sections["paint"]
    if det["precision"] != 1.0 or det["recall"] != 1.0:
        failures.append(f"{label}: detection P={det['precision']} R={det['recall']}")
    if geom["max_section_error_mm"] is None or geom["max_section_error_mm"] > bar["section_mm"]:
        failures.append(f"{label}: section {geom['max_section_error_mm']} mm > {bar['section_mm']}")
    if geom["max_length_error_mm"] is None or geom["max_length_error_mm"] > bar["length_mm"]:
        failures.append(f"{label}: length {geom['max_length_error_mm']} mm > {bar['length_mm']}")
    if ang["max_abs_error_deg"] is None or ang["max_abs_error_deg"] > bar["angle_deg"]:
        failures.append(f"{label}: angle {ang['max_abs_error_deg']} deg > {bar['angle_deg']}")
    colors = paint["production_colors"]
    if not colors or any(color != "yellow" for color in colors):
        failures.append(f"{label}: production paint was not all yellow")
    return failures


def _open3d_card(scene, run, sections) -> dict:
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": "A1",
        "algorithm": "Refined Open3D stud prior",
        "rank": 1,
        "stage": scene.stage,
        "status": "ran_synthetic",
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process",
        "epsilon_locked": False,
        "scene": {
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "spacing_m": scene.spacing_m,
            "noise_std_m": scene.noise_std_m,
            "n_points": scene.n_points,
            "n_studs": len(scene.studs),
            "reference": run.reference,
            "floor_found": run.floor_found,
            "removed_z_intervals_m": run.removed_z_intervals_m,
            "tolerance_deg": round(TOLERANCE_DEG, 5),
            "meta": scene.meta,
        },
        **sections,
    }


def _brief(card: dict) -> dict:
    det = card["detection"]
    geom = card["geometry"]
    ang = card["angle"]
    return {
        "scene": card["scene"]["name"],
        "stage": card["stage"],
        "status": card["status"],
        "n_points": card["scene"].get("n_points"),
        "n_true": det.get("n_true"),
        "n_pred": det.get("n_pred"),
        "precision": det.get("precision"),
        "recall": det.get("recall"),
        "section_mm": geom.get("max_section_error_mm"),
        "length_mm": geom.get("max_length_error_mm"),
        "mae_deg": ang.get("mae_deg"),
        "max_angle_deg": ang.get("max_abs_error_deg"),
        "pct_in_band": ang.get("pct_in_band"),
        "runtime_s": card["cost"].get("runtime_s"),
        "reference": ang.get("reference") or card["scene"].get("reference"),
        "paint": card["paint"].get("production_colors"),
        "epsilon_locked": card["paint"].get("epsilon_locked"),
    }


def _run_open3d(scene, out_dir: Path, *, gate: bool) -> tuple[dict, list[str]]:
    print(f"running {scene.name} stage {scene.stage} points {scene.n_points} studs {len(scene.studs)}", flush=True)
    run = run_baseline(scene)
    sections = score_run(scene, run)
    expected = REFERENCE_FLOOR if scene_has_floor(scene) else REFERENCE_GENERATOR_Z
    if run.reference != expected or sections["angle"]["reference"] != expected:
        raise SystemExit(
            f"{scene.name}: synthetic angle_reference {run.reference!r} / "
            f"{sections['angle']['reference']!r}, expected {expected!r}"
        )
    card = _open3d_card(scene, run, sections)
    dest = out_dir / f"open3d_{scene.name}.json"
    write_scorecard(dest, card)
    failures = _failures(scene.stage, sections, scene.name) if scene.stage in BARS else []
    if scene.stage not in BARS:
        det = sections["detection"]
        if det["precision"] != 1.0 or det["recall"] != 1.0:
            failures.append(
                f"{scene.name}: detection P={det['precision']} R={det['recall']} (no numeric stage bar)"
            )
        colors = sections["paint"]["production_colors"]
        if colors and any(color != "yellow" for color in colors):
            failures.append(f"{scene.name}: production paint was not all yellow")
    print(
        f"  P={sections['detection']['precision']} R={sections['detection']['recall']} "
        f"section={sections['geometry']['max_section_error_mm']} "
        f"length={sections['geometry']['max_length_error_mm']} "
        f"mae={sections['angle']['mae_deg']} max={sections['angle']['max_abs_error_deg']} "
        f"runtime={sections['cost']['runtime_s']}",
        flush=True,
    )
    note_gate = "Bring-up bars apply." if gate else "Probe. Not a stage gate."
    append_day_row(
        algorithm="open3d",
        stage=scene.stage,
        scene=scene.name,
        ground_truth_source="synthetic",
        pass_fail="fail" if failures else "pass",
        notes=(
            f"Curriculum continuation. {note_gate} device ε unlocked. "
            f"Scorecard: curriculum/{dest.name}."
        ),
        card=card,
    )
    return card, failures if gate else []


def _not_run_card(*, algorithm_id: str, algorithm: str, rank: int, stage: int, scene: str, note: str) -> dict:
    sections = empty_sections()
    for key in sections:
        sections[key]["note"] = note
    sections["paint"]["epsilon_locked"] = False
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": stage,
        "status": "stub_not_run",
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        "scene": {"name": scene},
        **sections,
        "notes": [note],
    }


def _link_existing(score_dir: Path) -> list[dict]:
    linked = []
    for stage, names in LINKED.items():
        for name in names:
            path = score_dir / name
            card = read_scorecard(path)
            expected = REFERENCE_FLOOR if stage >= 2 else REFERENCE_GENERATOR_Z
            got = (card.get("angle") or {}).get("reference")
            if got != expected:
                raise SystemExit(f"{name}: linked synthetic reference {got!r}, expected {expected!r}")
            failures = _failures(stage, card, name)
            linked.append(
                {
                    "stage": stage,
                    "file": f"artifacts/scorecards/{name}",
                    "scene": card["scene"]["name"],
                    "bars_ok": not failures,
                    "failures": failures,
                    "precision": card["detection"]["precision"],
                    "recall": card["detection"]["recall"],
                    "section_mm": card["geometry"]["max_section_error_mm"],
                    "length_mm": card["geometry"]["max_length_error_mm"],
                    "mae_deg": card["angle"]["mae_deg"],
                    "max_angle_deg": card["angle"].get("max_abs_error_deg"),
                    "paint": card["paint"]["production_colors"],
                    "epsilon_locked": card["paint"]["epsilon_locked"],
                }
            )
            if failures:
                print(f"LINK FAIL {name}: {failures}", flush=True)
            else:
                print(f"linked {name}", flush=True)
    return linked


def main() -> int:
    assert_paint_rules()
    score_dir = ROOT / "artifacts" / "scorecards"
    out_dir = score_dir / "curriculum"
    out_dir.mkdir(parents=True, exist_ok=True)
    linked = _link_existing(score_dir)
    link_failures = [item for item in linked if not item["bars_ok"]]

    gate_failures: list[str] = []
    measured: list[dict] = []

    gate_scenes = [
        stage2_stud_and_floor(nominal="2x4", lean_deg=0.0, seed=20),
        stage2_stud_and_floor(nominal="2x4", lean_deg=0.12, seed=21),
        stage2_stud_and_floor(nominal="2x4", lean_deg=1.0, seed=22),
        stage3_mini_wall(n_studs=3, leans_deg=(0.0, 0.12, 4.0), seed=30),
        stage3_mini_wall(n_studs=5, seed=31),
        stage3_mini_wall(
            n_studs=4,
            leans_deg=(0.05, 0.15, 0.30, 1.0),
            seed=33,
            scene_name="stage3_mini_wall_4_leanmild",
        ),
    ]
    probe_scenes = [
        stage3_mini_wall(
            n_studs=4,
            leans_deg=(0.0, 0.30, 0.80, 1.50),
            seed=32,
            noise_std_m=0.002,
            scene_name="stage3_mini_wall_4_noise2mm",
        ),
        s1b_bowed_stud(bow_m=0.00635, lean_deg=0.0, seed=40),
        s1b_bowed_stud(bow_m=0.00635, lean_deg=0.30, seed=42),
        s1b_bowed_stud(bow_m=0.01905, lean_deg=0.0, seed=43),
        s1b_bow_wall(n_studs=3, bow_slot=1, bow_m=0.00635, leans_deg=(0.0, 0.0, 0.20), seed=41),
        stage5_room_bay(),
    ]

    for scene in gate_scenes:
        card, failures = _run_open3d(scene, out_dir, gate=True)
        gate_failures.extend(failures)
        measured.append({**_brief(card), "role": "gate", "failures": failures})
    for scene in probe_scenes:
        card, failures = _run_open3d(scene, out_dir, gate=False)
        # Probe failures are recorded on the day row inside _run_open3d.
        # Recompute for the summary without affecting the exit code.
        probe_fail = _failures(scene.stage, card, scene.name) if scene.stage in BARS else []
        if scene.stage not in BARS:
            det = card["detection"]
            if det["precision"] != 1.0 or det["recall"] != 1.0:
                probe_fail.append(f"detection P={det['precision']} R={det['recall']}")
        measured.append({**_brief(card), "role": "probe", "failures": probe_fail})

    room_name = "stage5_room_bay_lot62_look"
    stub_files = []
    for algorithm, rank, algorithm_id, title, note in ROOM_STUBS:
        card = _not_run_card(
            algorithm_id=algorithm_id,
            algorithm=title,
            rank=rank,
            stage=5,
            scene=room_name,
            note=note + " Metrics left null. Not a control pass.",
        )
        dest = out_dir / f"{algorithm}_stage5_not_run.json"
        write_scorecard(dest, card)
        append_day_row(
            algorithm=algorithm,
            stage=5,
            scene=room_name,
            ground_truth_source="synthetic",
            pass_fail="not_run",
            notes=note + f" Scorecard: curriculum/{dest.name}.",
            card=card,
        )
        stub_files.append(dest.name)

    for stage, scene_name, note in (
        (
            6,
            "stage6_whole_story",
            "Stage 6 needs a real single-story capture. A synthetic room is not this stage. Metrics left null.",
        ),
        (
            7,
            "stage7_complex_frame",
            "Stage 7 needs a real two-story or complex capture. Metrics left null. Not a shortcut past stages 3–5.",
        ),
    ):
        for algorithm, rank, algorithm_id, title in (
            ("open3d", 1, "A1", "Refined Open3D stud prior"),
            ("pcl", 2, "A2", "PCL region-grow cuboid"),
            ("cloudcompare", 3, "A3", "CloudCompare RANSAC-SD"),
            ("pointcept", 4, "A4", "Pointcept PTv3"),
            ("open3d_ml", 5, "A5", "Open3D-ML RandLA-Net"),
            ("pyransac3d", 6, "A6", "pyRANSAC-3D sequential cuboid"),
            ("sam2", 7, "B7", "SAM 2 image/video mask"),
        ):
            card = _not_run_card(
                algorithm_id=algorithm_id,
                algorithm=title,
                rank=rank,
                stage=stage,
                scene=scene_name,
                note=note,
            )
            dest = out_dir / f"{algorithm}_stage{stage}_not_run.json"
            write_scorecard(dest, card)
            append_day_row(
                algorithm=algorithm,
                stage=stage,
                scene=scene_name,
                ground_truth_source="synthetic",
                pass_fail="not_run",
                notes=note + f" Scorecard: curriculum/{dest.name}.",
                card=card,
            )
            stub_files.append(dest.name)

    print("sam2 scaffold", flush=True)
    sam_scene = stage0_single_stud(nominal="2x4", lean_deg=0.05, seed=2)
    camera = default_stud_camera()
    raster = raster_nearest(sam_scene.points_m, sam_scene.part, camera)
    install = probe_install()
    png_path = out_dir / "sam2_projection_stage0_partids.png"
    save_part_png(png_path, raster["part_image"])
    blocked = blocked_sam2_card(sam_scene, raster, install, camera)
    write_scorecard(out_dir / "sam2_rank7_blocked.json", blocked)
    append_day_row(
        algorithm="sam2",
        stage=0,
        scene=sam_scene.name,
        ground_truth_source="synthetic",
        pass_fail="blocked_install",
        notes=(
            "Bake-off rank 7. Projection ran. SAM 2 weights did not. "
            f"Stud metrics null. {install['blocker_short']}. "
            "Scorecard: curriculum/sam2_rank7_blocked.json."
        ),
        card=blocked,
    )
    control = generator_mask_control(sam_scene, camera)
    control_payload = control_card(sam_scene, control, png_path.name)
    write_scorecard(out_dir / "sam2_generator_mask_control.json", control_payload)
    append_day_row(
        algorithm="sam2",
        stage=0,
        scene=sam_scene.name + "_generator_mask",
        ground_truth_source="synthetic",
        pass_fail="control",
        notes=(
            "Generator z-buffer mask lifted to points, then the shared box. "
            "Not a SAM 2 mask. Scorecard: curriculum/sam2_generator_mask_control.json."
        ),
        card=control_payload,
    )

    summary = {
        "epsilon_locked": False,
        "linked": linked,
        "link_failures": [item["file"] for item in link_failures],
        "gate_failures": gate_failures,
        "measured": measured,
        "sam2": {
            "status": "blocked_install",
            "blocker_short": install["blocker_short"],
            "install": {key: install[key] for key in install if key != "blocker"},
            "projection": blocked["attempt"]["projection"],
            "generator_mask_control": _brief(control_payload),
        },
        "room_stubs": stub_files,
        "parallel_corner_prs": [
            "https://github.com/ozguvenc2/openwall-stud-frame/pull/23",
            "https://github.com/ozguvenc2/openwall-stud-frame/pull/24",
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary -> {out_dir / 'summary.json'}", flush=True)
    if link_failures or gate_failures:
        print("GATE FAILURES", link_failures, gate_failures, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
