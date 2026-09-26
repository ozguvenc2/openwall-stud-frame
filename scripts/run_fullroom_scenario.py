"""Calibrate, then score one full-room scene with one bake-off model.

The queue runner starts one process per scene and model. This script exits
non-zero on a crash so that runner can retry this pair only.

    .venv\\Scripts\\python.exe scripts/run_fullroom_scenario.py --letter A --model open3d

Catch rate compares the measured lean from the floor normal (plumb call) with
the planted-lean color in scenes A–J. |measured − planted| is recorded as the
error call and is not the supposed-red count. Production paint stays yellow.
Experiment 1 checkpoints are hashed and must not change.

Foundation models (Point-SAM, SAM3D, OpenMask3D, Segment3D) have no full-room
adapter: their stage-0 writers build one stud. This script records
status=not_adapted and does not invent catch numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if not ROOT.exists():
    ROOT = Path("/mnt/c/Repos/openwall-stud-frame")
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.angle_reference import lock_synthetic_reference, scene_has_floor  # noqa: E402
from openwall_stud.finetune_fullroom import EXPERIMENT1_WEIGHTS, WEIGHT_DIR  # noqa: E402
from openwall_stud.fullroom_scenes import scene_specs  # noqa: E402
from openwall_stud.lumber import NAHB_WARRANTY_DEG, TOLERANCE_DEG  # noqa: E402
from openwall_stud.open3d_baseline import (  # noqa: E402
    DEFAULT_DBSCAN_EPS_M,
    DEFAULT_DBSCAN_MIN_POINTS,
    MAX_LENGTH_M,
    MAX_UPRIGHT_DEG,
    MIN_LENGTH_M,
    BaselineRun,
    _angle_deg,
    _point_cloud,
    match_detections,
    peel_horizontal_slabs,
    run_baseline,
)
from openwall_stud.paint import SENSOR_EPSILON_DEG, assert_paint_rules, dual_standard_passes  # noqa: E402
from openwall_stud.poststep import detections_from_clusters  # noqa: E402
from openwall_stud.synthetic import full_room_28  # noqa: E402

DISPLAY_HANDBOOK_DEG = 0.11937
DISPLAY_NAHB_DEG = 0.67140
GAUGES = ("handbook_finish_plumb", "nahb_warranty_gauge")
COLUMNS = ("absolute", "sensor")
FOUNDATION_REASON = (
    "No full-room adapter. scripts/phase_neg1_stage0_foundation.py builds "
    "stage0_single_stud (lean 0°, seed 1) only. Prompt/zero-shot weights are "
    "not finetuned here, and this run does not invent a catch table."
)

RESULTS = ROOT / "artifacts" / "fullroom" / "results"
CALIBRATION = ROOT / "artifacts" / "fullroom" / "calibration"


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _maybe_reset_cuda() -> None:
    if os.environ.get("FULLROOM_OOM_RETRY") != "1" and os.environ.get("FULLROOM_CUDA_RESET") != "1":
        return
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def _colors(value_deg: float) -> dict[str, dict[str, str]]:
    report = dual_standard_passes(abs(float(value_deg)))
    colored: dict[str, dict[str, str]] = {}
    for spec in report["standards"]:
        colored[spec["key"]] = {
            "absolute": spec["absolute"]["color"],
            "sensor": spec["sensor"]["color"],
        }
    return colored


def calibrate(letter: str, model: str) -> dict:
    """Lock the dual-gauge rule, then record display rounding. No threshold edit."""
    assert_paint_rules()
    report = dual_standard_passes(0.0)
    handbook = float(report["standards"][0]["threshold_deg"])
    nahb = float(report["standards"][1]["threshold_deg"])
    if handbook != float(TOLERANCE_DEG) or nahb != float(NAHB_WARRANTY_DEG):
        raise RuntimeError("dual_standard_passes thresholds drifted from lumber.py")
    payload = {
        "letter": letter,
        "model": model,
        "assert_paint_rules": "passed",
        "handbook_threshold_deg": handbook,
        "nahb_threshold_deg": nahb,
        "display_handbook_deg": DISPLAY_HANDBOOK_DEG,
        "display_nahb_deg": DISPLAY_NAHB_DEG,
        "display_rounding_delta_handbook_deg": handbook - DISPLAY_HANDBOOK_DEG,
        "display_rounding_delta_nahb_deg": nahb - DISPLAY_NAHB_DEG,
        "absolute_epsilon_deg": 0.0,
        "sensor_epsilon_deg": float(SENSOR_EPSILON_DEG),
        "improvement": "none",
        "policy": "locked",
        "note": (
            "Display figures 0.11937° and 0.67140° are rounded atan values. "
            "The delta is that rounding. Thresholds were not changed."
        ),
    }
    dest = CALIBRATION / f"{letter}_{model}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _scene_for(spec: dict):
    return full_room_28(
        leans_deg=spec["leans_deg"],
        lean_axes=spec["lean_axes"],
        seed=int(spec["seed"]),
        spacing_m=float(spec["spacing_m"]),
        plate_spacing_m=float(spec["plate_spacing_m"]),
        floor_spacing_m=float(spec["floor_spacing_m"]),
        noise_std_m=float(spec["noise_std_m"]),
        name=spec["name"],
    )


def _run_from_clusters(scene, clusters: list[np.ndarray], runtime_s: float) -> BaselineRun:
    """Same section, length, and upright gates as the Open3D baseline."""
    _, floor_normal, intervals = peel_horizontal_slabs(scene.points_m)
    reference_name, reference_vec = lock_synthetic_reference(
        floor_normal,
        has_floor=scene_has_floor(scene),
    )
    raw = detections_from_clusters(clusters, reference=reference_vec)
    kept = []
    for det in raw:
        length = float(det.extent_sorted_m[2])
        if det.nominal_guess is None or not (MIN_LENGTH_M <= length <= MAX_LENGTH_M):
            continue
        if float(det.theta_deg) > MAX_UPRIGHT_DEG:
            continue
        kept.append(det)
    kept.sort(key=lambda item: float(item.center_m[0]))
    return BaselineRun(
        scene_name=scene.name,
        stage=scene.stage,
        keep_mask=np.ones(scene.n_points, dtype=bool),
        cluster_labels=np.full(scene.n_points, -1, dtype=int),
        detections=kept,
        floor_found=floor_normal is not None,
        floor_normal=reference_vec,
        reference=reference_name,
        runtime_s=runtime_s,
        n_in=int(scene.n_points),
        n_after_peel=int(scene.n_points),
        removed_z_intervals_m=intervals,
    )


def _clusters_from_stud_mask(points: np.ndarray, stud_mask: np.ndarray) -> list[np.ndarray]:
    idx = np.flatnonzero(stud_mask)
    if idx.size < DEFAULT_DBSCAN_MIN_POINTS:
        return []
    cloud = _point_cloud(points[idx])
    raw = np.asarray(
        cloud.cluster_dbscan(
            eps=DEFAULT_DBSCAN_EPS_M,
            min_points=DEFAULT_DBSCAN_MIN_POINTS,
            print_progress=False,
        )
    )
    clusters = []
    for cluster_id in sorted(int(value) for value in np.unique(raw) if int(value) >= 0):
        member = idx[raw == cluster_id]
        if member.size < DEFAULT_DBSCAN_MIN_POINTS:
            continue
        clusters.append(points[member])
    return clusters


def _run_open3d(scene) -> tuple[BaselineRun, dict]:
    started = time.perf_counter()
    run = run_baseline(scene)
    return run, {"runtime_s": round(time.perf_counter() - started, 3)}


def _run_pcl(scene) -> tuple[BaselineRun, dict]:
    from openwall_stud.region_grow import grow_labels, members_from_labels

    work = ROOT / "artifacts" / "fullroom" / "pcl_work" / scene.name
    started = time.perf_counter()
    labels, provenance = grow_labels(scene.points_m, work)
    members, info = members_from_labels(scene.points_m, labels)
    runtime_s = time.perf_counter() - started
    run = _run_from_clusters(scene, members, runtime_s)
    return run, {
        "runtime_s": round(runtime_s, 3),
        "native_pcl_region_growing": bool(provenance.get("native_pcl_region_growing")),
        "n_members": info.get("n_members"),
    }


def _run_pyransac(scene) -> tuple[BaselineRun, dict]:
    from openwall_stud.contenders.pyransac3d_cuboid import MAX_CUBOIDS, sequential_cuboids

    started = time.perf_counter()
    fitted = sequential_cuboids(scene.points_m, seed=int(scene.seed), has_floor=scene_has_floor(scene))
    runtime_s = time.perf_counter() - started
    clusters = list(fitted.get("clusters") or [])
    run = _run_from_clusters(scene, clusters, runtime_s)
    return run, {
        "runtime_s": round(runtime_s, 3),
        "max_cuboids": MAX_CUBOIDS,
        "stopped": fitted.get("stopped"),
        "n_accepted": len(clusters),
        "note": (
            "Existing sequential cuboid stops at MAX_CUBOIDS (4) or on a wall-swallow. "
            "Those limits were not raised for this room."
        ),
    }


def _run_pointcept(scene) -> tuple[BaselineRun, dict]:
    import torch

    from openwall_stud.finetune_pointcept import build_model, load_bimstruct_backbone, load_finetuned, predict_full
    from openwall_stud.finetune_synth import STUD, estimate_normals

    path = WEIGHT_DIR / "pointcept_stud_2class_fullroom.pth"
    if not path.is_file():
        raise SystemExit(f"missing full-room Pointcept head {path}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    _maybe_reset_cuda()
    model = build_model("cuda")
    load_bimstruct_backbone(model)
    load_finetuned(model, path)
    points = np.asarray(scene.points_m, dtype=np.float32)
    normals = estimate_normals(points)
    started = time.perf_counter()
    pred = predict_full(model, points, normals)
    runtime_s = time.perf_counter() - started
    clusters = _clusters_from_stud_mask(scene.points_m, pred == STUD)
    run = _run_from_clusters(scene, clusters, runtime_s)
    return run, {
        "runtime_s": round(runtime_s, 3),
        "weight": str(path.relative_to(ROOT)),
        "n_stud_pred": int((pred == STUD).sum()),
        "n_clusters": len(clusters),
    }


def _run_open3d_ml(scene) -> tuple[BaselineRun, dict]:
    import torch

    from openwall_stud.finetune_randlanet import build_model, load_checkpoint, predict_labels
    from openwall_stud.finetune_synth import STUD

    path = WEIGHT_DIR / "randlanet_stud_2class_fullroom.pth"
    if not path.is_file():
        raise SystemExit(f"missing full-room RandLA-Net head {path}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    _maybe_reset_cuda()
    model = build_model("cuda")
    load_checkpoint(model, path)
    points = np.asarray(scene.points_m, dtype=np.float32)
    pred, runtime_s = predict_labels(model, points)
    clusters = _clusters_from_stud_mask(scene.points_m, pred == STUD)
    run = _run_from_clusters(scene, clusters, runtime_s)
    return run, {
        "runtime_s": round(runtime_s, 3),
        "weight": str(path.relative_to(ROOT)),
        "n_stud_pred": int((pred == STUD).sum()),
        "n_clusters": len(clusters),
    }


RUNNERS = {
    "open3d": _run_open3d,
    "pcl": _run_pcl,
    "pyransac3d": _run_pyransac,
    "pointcept": _run_pointcept,
    "open3d_ml": _run_open3d_ml,
}


def _slot_of(stud_id: str) -> int:
    number = int(stud_id[1:])
    return number - 1


def score_catches(scene, run: BaselineRun, spec: dict) -> dict:
    expected_by_slot = {int(row["slot"]): row["expected_plumb"] for row in spec["studs"]}
    matches = match_detections(scene, run)
    matched_truth = {truth_i: det_i for truth_i, det_i in matches}
    matched_det = {det_i for _, det_i in matches}
    per_stud = []
    for truth_i, truth in enumerate(scene.studs):
        slot = _slot_of(truth.stud_id)
        expected = expected_by_slot[slot]
        planted = abs(float(truth.lean_deg))
        row = {
            "stud_id": truth.stud_id,
            "slot": slot,
            "planted_lean_deg": planted,
            "expected_plumb": expected,
            "matched": truth_i in matched_truth,
        }
        if truth_i in matched_truth:
            det = run.detections[matched_truth[truth_i]]
            true_theta = float(_angle_deg(truth.long_axis, run.floor_normal))
            measured = float(det.theta_deg)
            error = abs(measured - true_theta)
            row.update(
                {
                    "true_theta_deg": round(true_theta, 5),
                    "measured_deg": round(measured, 5),
                    "abs_error_deg": round(error, 5),
                    "plumb": _colors(measured),
                    "error_call": _colors(error),
                    "production_color": det.production_color,
                }
            )
        per_stud.append(row)

    unmatched_red = {gauge: {column: 0 for column in COLUMNS} for gauge in GAUGES}
    for det_i, det in enumerate(run.detections):
        if det_i in matched_det:
            continue
        colored = _colors(float(det.theta_deg))
        for gauge in GAUGES:
            for column in COLUMNS:
                if colored[gauge][column] == "red":
                    unmatched_red[gauge][column] += 1

    tallies = {}
    for gauge in GAUGES:
        tallies[gauge] = {}
        for column in COLUMNS:
            expected_red = [row for row in per_stud if row["expected_plumb"][gauge][column] == "red"]
            expected_yellow = [row for row in per_stud if row["expected_plumb"][gauge][column] == "yellow"]
            caught_red = [
                row
                for row in expected_red
                if row["matched"] and row["plumb"][gauge][column] == "red"
            ]
            caught_yellow = [
                row
                for row in expected_yellow
                if row["matched"] and row["plumb"][gauge][column] == "yellow"
            ]
            false_red = [
                row
                for row in per_stud
                if row["matched"] and row["plumb"][gauge][column] == "red" and row["expected_plumb"][gauge][column] != "red"
            ]
            exact = [
                row
                for row in per_stud
                if row["matched"] and row["plumb"][gauge][column] == row["expected_plumb"][gauge][column]
            ]
            n_expected = len(expected_red)
            tallies[gauge][column] = {
                "n_expected_red": n_expected,
                "n_caught_red": len(caught_red),
                "n_missed_red": n_expected - len(caught_red),
                "catch_rate_red": None if n_expected == 0 else round(len(caught_red) / n_expected, 4),
                "n_expected_yellow": len(expected_yellow),
                "n_caught_yellow": len(caught_yellow),
                "n_false_red_matched": len(false_red),
                "n_false_red_unmatched_detections": unmatched_red[gauge][column],
                "n_exact_color": len(exact),
                "n_studs": len(per_stud),
                "n_matched": sum(1 for row in per_stud if row["matched"]),
            }
    return {
        "reference": run.reference,
        "n_detections": len(run.detections),
        "n_matched": len(matches),
        "tallies": tallies,
        "per_stud": per_stud,
        "plumb_call": spec["plumb_call"],
        "measurement_error_call": spec["measurement_error_call"],
    }


def _write_result(payload: dict) -> Path:
    dest = RESULTS / f"{payload['letter']}_{payload['model']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(dest)
    return dest


def _not_adapted(spec: dict, model: str, calibration: dict, before: dict) -> int:
    after = {str(path.relative_to(ROOT)): _sha256(path) for path in EXPERIMENT1_WEIGHTS}
    if before != after:
        raise SystemExit("Experiment 1 checkpoint bytes changed")
    payload = {
        "status": "not_adapted",
        "letter": spec["letter"],
        "seed": spec["seed"],
        "model": model,
        "reason": FOUNDATION_REASON,
        "calibration": calibration,
        "catch": None,
        "experiment1_sha256_unchanged": True,
    }
    dest = _write_result(payload)
    print(f"not_adapted {spec['letter']} {model} wrote {dest.relative_to(ROOT)}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score one full-room scene with one model.")
    parser.add_argument("--letter", required=True, choices=tuple("ABCDEFGHIJ"))
    parser.add_argument(
        "--model",
        required=True,
        choices=(
            "open3d",
            "pcl",
            "pyransac3d",
            "pointcept",
            "open3d_ml",
            "pointsam",
            "sam3d",
            "openmask3d",
            "segment3d",
        ),
    )
    args = parser.parse_args(argv)
    spec = next(row for row in scene_specs() if row["letter"] == args.letter)
    before = {str(path.relative_to(ROOT)): _sha256(path) for path in EXPERIMENT1_WEIGHTS}
    calibration = calibrate(args.letter, args.model)
    if args.model not in RUNNERS:
        return _not_adapted(spec, args.model, calibration, before)
    scene = _scene_for(spec)
    if len(scene.studs) != 28:
        raise SystemExit(f"{args.letter} generated {len(scene.studs)} studs")
    run, extra = RUNNERS[args.model](scene)
    catch = score_catches(scene, run, spec)
    after = {str(path.relative_to(ROOT)): _sha256(path) for path in EXPERIMENT1_WEIGHTS}
    if before != after:
        raise SystemExit("Experiment 1 checkpoint bytes changed")
    payload = {
        "status": "ok",
        "letter": spec["letter"],
        "seed": spec["seed"],
        "title": spec["title"],
        "model": args.model,
        "n_points": scene.n_points,
        "calibration": calibration,
        "model_extra": extra,
        "catch": catch,
        "experiment1_sha256_unchanged": True,
        "production_paint": "yellow while epsilon is unlocked",
    }
    dest = _write_result(payload)
    handbook = catch["tallies"]["handbook_finish_plumb"]["absolute"]
    print(
        f"ok {args.letter} {args.model} matched={catch['n_matched']} "
        f"handbook_abs_caught_red={handbook['n_caught_red']}/{handbook['n_expected_red']} "
        f"wrote {dest.relative_to(ROOT)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
