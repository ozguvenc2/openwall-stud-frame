"""Score bake-off ranks 1–7 on the stage-5 synthetic room.

The scene is ``stage5_room_bay_lot62_look``. It has a floor, so a lean that
this process scores on the full cloud uses the fitted floor normal. A SKIL
or any other level reading is not the reference.

From the repo root, one rank per process:

    .venv\\Scripts\\python.exe scripts/run_room_all_ranks.py --rank pcl --skip-day-row

Pointcept needs a CUDA torch that can import the BIMStruct3D cache.
Open3D-ML needs the interpreter that imports ``open3d.ml.torch``.
SAM 2 uses ``transformers.Sam2Model`` on CUDA (``measure_rank7``).

``--record-days`` only upserts day-table rows from cards already written.
Stages 6 and 7 are not touched.

Device epsilon stays unlocked. Production paint stays yellow.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.angle_reference import REFERENCE_FLOOR, scene_has_floor
from openwall_stud.contenders.common import blocked_card
from openwall_stud.one_stud import scene_record
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.scorecard import append_day_row, write_scorecard
from openwall_stud.synthetic import stage5_room_bay

ROOM_NAME = "stage5_room_bay_lot62_look"
OUT_DIR = ROOT / "artifacts" / "scorecards" / "curriculum"

RANKS = (
    "open3d",
    "pcl",
    "cloudcompare",
    "pointcept",
    "open3d_ml",
    "pyransac3d",
    "sam2",
)

STUB_NAMES = {
    "pcl": "pcl_stage5_not_run.json",
    "cloudcompare": "cloudcompare_stage5_not_run.json",
    "pointcept": "pointcept_stage5_not_run.json",
    "open3d_ml": "open3d_ml_stage5_not_run.json",
    "pyransac3d": "pyransac3d_stage5_not_run.json",
    "sam2": "sam2_stage5_not_run.json",
}

_WORDING = (
    ("on this one synthetic stud", "on this stage-5 synthetic room"),
    ("this one synthetic stud", "this stage-5 synthetic room"),
    ("on this synthetic stud", "on this stage-5 synthetic room"),
    ("this synthetic stud", "this stage-5 synthetic room"),
    ("Runtime is this process on this one stud.", "Runtime is this process on this stage-5 room."),
    ("Counts are this synthetic stud, not a field accuracy.", "Counts are this stage-5 synthetic room, not a field accuracy."),
    (
        "synthetic generator, this process, one stud",
        "synthetic generator, this process, stage-5 room",
    ),
)

_ROOM_NOTE = (
    "Stage 5 synthetic room stage5_room_bay_lot62_look. "
    "The scene has a floor, so a lean scored on the full cloud uses the fitted floor normal. "
    "A SKIL or other level reading is not the reference. "
    "Device epsilon is unlocked, so any production paint is yellow. "
    "There is no numeric stage-5 acceptance bar. "
    "A day-table pass means one box per generator stud and yellow paint. "
    "Not stages 6 or 7. Not the Lot 62 Polycam file. "
    "Corner phase-2 (PRs #23, #24, #25) is parallel and is not a gate."
)


def _card_path(algorithm: str) -> Path:
    return OUT_DIR / f"{algorithm}_{ROOM_NAME}.json"


def _rewrite(value: Any) -> Any:
    if isinstance(value, str):
        text = value
        for old, new in _WORDING:
            text = text.replace(old, new)
        return text
    if isinstance(value, list):
        return [_rewrite(item) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite(item) for key, item in value.items()}
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items() if key != "_point_colors"}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item") and callable(value.item) and not isinstance(value, (bytes, str)):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _open3d_card(scene, run, sections) -> dict[str, Any]:
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": "A1",
        "algorithm": "Refined Open3D stud prior",
        "rank": 1,
        "stage": 5,
        "status": "ran_synthetic",
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process, stage-5 room",
        "epsilon_locked": False,
        "scene": {
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "spacing_m": scene.spacing_m,
            "noise_std_m": scene.noise_std_m,
            "n_points": scene.n_points,
            "n_studs": len(scene.studs),
            "has_floor": True,
            "reference": run.reference,
            "floor_found": run.floor_found,
            "removed_z_intervals_m": run.removed_z_intervals_m,
            "meta": scene.meta,
        },
        **sections,
        "notes": [_ROOM_NOTE],
    }


def _room_camera(scene):
    from openwall_stud.contenders.sam2_mask import Pinhole

    points = scene.points_m
    center = points.mean(axis=0)
    eye_y = float(points[:, 1].min() - 2.2)
    return Pinhole(
        eye_m=(float(center[0]), eye_y, float(center[2])),
        target_m=(float(center[0]), float(center[1]), float(center[2])),
        up=(0.0, 0.0, 1.0),
        fov_y_deg=60.0,
        width=768,
        height=512,
    )


def _blocked_crash(algorithm: str, rank: int, algorithm_id: str, title: str, scene, exc: BaseException) -> dict:
    detail = traceback.format_exc()[-4000:]
    short = f"{type(exc).__name__}: {exc}"
    card = blocked_card(
        algorithm_id=algorithm_id,
        algorithm=title,
        rank=rank,
        license_name="see the rank module",
        hardware="Oz_PC",
        failure_modes=[short, "No stud metrics were invented after the crash."],
        blocker=(
            f"{title} raised while scoring {ROOM_NAME} "
            f"({scene.n_points} points). {short} Stud metrics are null."
        ),
        blocker_short=short[:240],
        scene=scene_record(scene),
        attempt={"cloud_loaded": True, "n_points": scene.n_points, "traceback": detail, "algorithm": algorithm},
    )
    return card


def _run_sam2(scene) -> dict[str, Any]:
    from openwall_stud.contenders.sam2_mask import default_stud_camera, measure_rank7

    camera = _room_camera(scene)
    measured = measure_rank7(scene=scene, camera=camera)
    card = measured["card"]
    blocker = str((card.get("attempt") or {}).get("blocker_short") or card.get("blocker_short") or "")
    if card.get("status") == "blocked_install" and "prompt" in blocker.lower():
        measured = measure_rank7(scene=scene, camera=default_stud_camera())
        card = measured["card"]
        card.setdefault("notes", []).append(
            "The room overview camera produced no stud prompt. This card is the scaffold camera retry."
        )
    card.setdefault("implementation", {})
    if isinstance(card.get("implementation"), dict):
        card["implementation"]["room_limit"] = (
            "One pinhole and one mask. This is not 26 stud instances. "
            "The source room has a floor. The shared box, when one is scored, "
            "uses the reference of the lifted cloud."
        )
    rgb = measured.get("rgb")
    mask = measured.get("mask")
    if rgb is not None:
        try:
            from PIL import Image
            import numpy as np

            image = Image.fromarray(rgb, mode="RGB")
            image.save(OUT_DIR / "sam2_room_prompt.png")
            if mask is not None:
                overlay = np.array(image)
                overlay[np.asarray(mask).astype(bool)] = (220, 180, 40)
                Image.fromarray(overlay, mode="RGB").save(OUT_DIR / "sam2_room_mask.png")
        except Exception as exc:
            card.setdefault("notes", []).append(f"Room prompt image was not saved: {type(exc).__name__}: {exc}")
    return card


def _run(algorithm: str, scene) -> dict[str, Any]:
    if algorithm == "open3d":
        run = run_baseline(scene)
        sections = score_run(scene, run)
        if run.reference != REFERENCE_FLOOR or sections["angle"]["reference"] != REFERENCE_FLOOR:
            raise SystemExit(
                f"Open3D room reference {run.reference!r} / {sections['angle']['reference']!r}, "
                f"expected {REFERENCE_FLOOR!r}"
            )
        return _open3d_card(scene, run, sections)
    if algorithm == "pcl":
        from openwall_stud.contenders.pcl_region_grow import run_one_stud

        card, _ = run_one_stud(scene)
        return card
    if algorithm == "cloudcompare":
        from openwall_stud.contenders.cloudcompare_ransac import run_one_stud

        card, _ = run_one_stud(scene)
        return card
    if algorithm == "pointcept":
        from openwall_stud.contenders.pointcept_ptv3 import run_one_stud

        card, _ = run_one_stud(scene)
        return card
    if algorithm == "open3d_ml":
        from openwall_stud.contenders.open3d_ml_s3dis import run_one_stud

        card, _ = run_one_stud(scene)
        return card
    if algorithm == "pyransac3d":
        from openwall_stud.contenders.pyransac3d_cuboid import run_one_stud

        card, _ = run_one_stud(scene)
        return card
    if algorithm == "sam2":
        return _run_sam2(scene)
    raise SystemExit(f"unknown rank {algorithm}")


def _titles() -> dict[str, tuple[int, str, str]]:
    return {
        "open3d": (1, "A1", "Refined Open3D stud prior"),
        "pcl": (2, "A2", "PCL region-grow + cuboid"),
        "cloudcompare": (3, "A3", "CloudCompare RANSAC-SD"),
        "pointcept": (4, "A4", "Pointcept PTv3"),
        "open3d_ml": (5, "A5", "Open3D-ML RandLA-Net"),
        "pyransac3d": (6, "A6", "pyRANSAC-3D sequential cuboid"),
        "sam2": (7, "B7", "SAM 2 image mask"),
    }


def _finalize(card: dict[str, Any], *, algorithm: str) -> dict[str, Any]:
    card.pop("_point_colors", None)
    card = _jsonable(_rewrite(card))
    card["stage"] = 5
    notes = list(card.get("notes") or [])
    if _ROOM_NOTE not in notes:
        notes.append(_ROOM_NOTE)
    if card.get("stud_metrics_scored") is False:
        extra = (
            "This forward pass is the stage-5 room cloud. "
            "Stud detection, geometry, angle, and paint stay null. "
            "No stud box and no paint color were invented."
        )
        if extra not in notes:
            notes.append(extra)
    card["notes"] = notes
    angle_ref = (card.get("angle") or {}).get("reference")
    scene_ref = (card.get("scene") or {}).get("reference")
    if algorithm != "sam2" and card.get("status") in {"ran", "ran_synthetic"} and card.get("stud_metrics_scored") is not False:
        if angle_ref != REFERENCE_FLOOR or scene_ref != REFERENCE_FLOOR:
            raise SystemExit(
                f"{algorithm}: scored room card reference angle={angle_ref!r} scene={scene_ref!r}, "
                f"expected {REFERENCE_FLOOR!r}"
            )
    return card


def _keep_existing(dest: Path, card: dict[str, Any]) -> bool:
    if card.get("status") != "blocked_install" or not dest.is_file():
        return False
    try:
        old = json.loads(dest.read_text(encoding="utf-8"))
    except Exception:
        return False
    if old.get("status") in {"ran", "ran_synthetic"}:
        print(f"keep existing measured card {dest.name}; this attempt was blocked", flush=True)
        return True
    return False


def _pass_fail(card: dict[str, Any]) -> str:
    status = card.get("status")
    if status == "blocked_install":
        return "blocked_install"
    if status in {None, "stub_not_run"}:
        return "not_run"
    if card.get("stud_metrics_scored") is False or status == "control":
        return "control"
    detection = card.get("detection") or {}
    colors = (card.get("paint") or {}).get("production_colors") or []
    if (
        detection.get("precision") == 1.0
        and detection.get("recall") == 1.0
        and colors
        and all(color == "yellow" for color in colors)
    ):
        return "pass"
    return "fail"


def _store(algorithm: str, card: dict[str, Any], *, write_day: bool) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = _card_path(algorithm)
    if _keep_existing(dest, card):
        return dest
    write_scorecard(dest, card)
    stub = STUB_NAMES.get(algorithm)
    if stub:
        stale = OUT_DIR / stub
        if stale.is_file():
            stale.unlink()
    if write_day:
        _append_day(algorithm, card)
    det = card.get("detection") or {}
    print(
        f"{algorithm} status={card.get('status')} pass_fail={_pass_fail(card)} "
        f"P={det.get('precision')} R={det.get('recall')} "
        f"section={(card.get('geometry') or {}).get('max_section_error_mm')} "
        f"mae={(card.get('angle') or {}).get('mae_deg')} "
        f"ref={(card.get('angle') or {}).get('reference') or (card.get('scene') or {}).get('reference')} "
        f"runtime={(card.get('cost') or {}).get('runtime_s')}",
        flush=True,
    )
    return dest


def _append_day(algorithm: str, card: dict[str, Any]) -> None:
    verdict = _pass_fail(card)
    append_day_row(
        algorithm=algorithm,
        stage=5,
        scene=ROOM_NAME,
        ground_truth_source="synthetic",
        pass_fail=verdict,
        notes=(
            f"Stage 5 synthetic room on Oz_PC. {verdict}. "
            "Floor normal when a full-cloud lean is scored. ε unlocked. "
            f"Scorecard: curriculum/{_card_path(algorithm).name}."
        ),
        card=card,
    )


def _record_days() -> int:
    missing = []
    for algorithm in RANKS:
        path = _card_path(algorithm)
        if not path.is_file():
            missing.append(algorithm)
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        _append_day(algorithm, card)
        print(f"day row {algorithm} {_pass_fail(card)}", flush=True)
    if missing:
        print("missing cards: " + ", ".join(missing), flush=True)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score one bake-off rank on the stage-5 room.")
    parser.add_argument("--rank", choices=RANKS)
    parser.add_argument("--skip-day-row", action="store_true")
    parser.add_argument("--record-days", action="store_true")
    args = parser.parse_args(argv)
    if args.record_days:
        return _record_days()
    if not args.rank:
        raise SystemExit("pass --rank or --record-days")
    scene = stage5_room_bay()
    if scene.name != ROOM_NAME or scene.stage != 5 or not scene_has_floor(scene):
        raise SystemExit(f"unexpected room scene {scene.name} stage {scene.stage}")
    print(
        f"room {scene.name} points {scene.n_points} studs {len(scene.studs)} reference {REFERENCE_FLOOR}",
        flush=True,
    )
    rank, algorithm_id, title = _titles()[args.rank]
    try:
        card = _run(args.rank, scene)
    except Exception as exc:
        print(f"{args.rank} raised {type(exc).__name__}: {exc}", flush=True)
        card = _blocked_crash(args.rank, rank, algorithm_id, title, scene, exc)
    card = _finalize(card, algorithm=args.rank)
    _store(args.rank, card, write_day=not args.skip_day_row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
