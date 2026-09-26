"""pyRANSAC-3D sequential cuboid on the one Stage 0 stud.

Install
    Apache-2.0 ``pyransac3d==0.7.0``. The pin is in ``requirements.txt``.
    Citation concept DOI: https://doi.org/10.5281/zenodo.7212567

    The library fits one cuboid per call and does not know a 2x4. This module
    peels horizontal slabs the same way rank 1 does, then repeats
    ``Cuboid.fit`` and removes inliers. Stage 0 has no floor and no plate, so
    the peel keeps the stud cloud. The angle reference stays generator +Z.

Entrypoint
    python -m openwall_stud.contenders.pyransac3d_cuboid

    That loads the one synthetic 2x4 at 0.05 degree lean (seed 2) and writes
    ``artifacts/scorecards/one_stud_pyransac3d.json``. ``--stub`` writes a null
    card and does not fit a cuboid.

Wall swallow
    If the first cuboid's second-largest extent exceeds 0.30 m, or its longest
    extent exceeds 4.0 m, the box is a wall panel rather than a stud. The run
    stops, the cuboid is not a detection, and the scorecard logs that. The log
    is not a schema failure. On this single stud the check should pass.

Post-step
    Accepted inliers go through the shared minimal OBB, angle versus +Z, and
    yellow paint. The library's own extents are stored on the card. They are
    coarser than that OBB, so the stud-section gate uses the OBB (the same
    15 mm nominal gate as rank 1). Device epsilon stays unlocked.

Do not
    Do not force the cuboid axis to global Z.
    Do not score the library extents as the section error.
    Do not run a second lean, a mini wall, or SAM 2 from this module.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import random
import time
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.common import blocked_card, emit_stub, ran_card, stub_card
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.open3d_baseline import (
    MAX_LENGTH_M,
    MAX_UPRIGHT_DEG,
    MIN_LENGTH_M,
    peel_horizontal_slabs,
)
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

PYRANSAC = {
    "rank": 6,
    "algorithm_id": "A6",
    "status": "stub",
    "name": "pyRANSAC-3D sequential cuboid",
}

# Library default. On this 5 mm / 1 mm stud it already covers both faces of the
# 38 mm thickness, and the best planes sit near enough to the section that the
# 89 mm width is inside the threshold as well. A 16 inch bay is still open air.
THRESH_M = 0.05
MAX_ITERATION = 1000
# Cap so a noisy tail cannot loop. One stud should accept on the first call.
MAX_CUBOIDS = 4
MIN_POINTS = 200
# A stick has one long axis. Two extents above 0.30 m are a panel. 4 m is
# longer than the studs rank 1 keeps (3.3 m).
WALL_SWALLOW_SECOND_EXTENT_M = 0.30
WALL_SWALLOW_LONG_EXTENT_M = 4.0
LICENSE_URL = "https://github.com/leomariga/pyRANSAC-3D/blob/v0.7.0/LICENSE"
DOI_URL = "https://doi.org/10.5281/zenodo.7212567"


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A6",
        algorithm=PYRANSAC["name"],
        rank=6,
        license_name="Apache-2.0",
        hardware="CPU",
        failure_modes=[
            "pyRANSAC-3D was not imported, so no cuboid was fit.",
            "One cuboid on a whole wall can lock onto coplanar stud faces.",
            "The library extents are coarser than the shared minimal OBB.",
        ],
        note="Stub only. pyRANSAC-3D was not executed. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    """Backward-compatible name for the null stub card."""
    return build_stub_card()


def _round_m(values: np.ndarray) -> list[float]:
    return [float(round(float(value), 5)) for value in values]


def is_wall_swallow(extents_sorted_m: np.ndarray) -> bool:
    """True when a cuboid is too large to be one stud."""
    return bool(
        float(extents_sorted_m[1]) > WALL_SWALLOW_SECOND_EXTENT_M
        or float(extents_sorted_m[2]) > WALL_SWALLOW_LONG_EXTENT_M
    )


def _swallow_log(extents_sorted_m: np.ndarray, triggered: bool) -> str:
    millimeters = ", ".join(f"{float(value) * 1000.0:.1f}" for value in extents_sorted_m)
    if triggered:
        return (
            "WALL SWALLOW: first cuboid extents "
            f"[{millimeters}] mm exceed a single stud "
            f"(second extent > {WALL_SWALLOW_SECOND_EXTENT_M:.2f} m or longest extent > {WALL_SWALLOW_LONG_EXTENT_M:.1f} m). "
            "That cuboid was rejected and sequential fitting stopped. "
            "This is a log on the scorecard, not a schema failure."
        )
    return (
        "Wall-swallow check passed. First cuboid extents "
        f"[{millimeters}] mm stay inside a single-stud limit "
        f"(second extent <= {WALL_SWALLOW_SECOND_EXTENT_M:.2f} m and longest extent <= {WALL_SWALLOW_LONG_EXTENT_M:.1f} m)."
    )


def _fit_once(points: np.ndarray, seed: int) -> Any:
    import pyransac3d as pyrsc

    random.seed(seed)
    cuboid = pyrsc.Cuboid()
    return cuboid.fit(
        np.ascontiguousarray(points, dtype=np.float64),
        thresh=THRESH_M,
        maxIteration=MAX_ITERATION,
    )


def sequential_cuboids(
    points: np.ndarray,
    *,
    seed: int,
    has_floor: bool = False,
) -> dict[str, Any]:
    """Peel, then repeated cuboid fits. Returns clusters and the run log."""
    from openwall_stud.angle_reference import lock_synthetic_reference
    from openwall_stud.poststep import detections_from_clusters

    keep, floor_normal, intervals = peel_horizontal_slabs(points)
    reference_name, reference_vec = lock_synthetic_reference(floor_normal, has_floor=has_floor)
    work = np.ascontiguousarray(points[keep], dtype=np.float64)
    accepted: list[np.ndarray] = []
    attempts: list[dict[str, Any]] = []
    wall_log = "Wall-swallow check did not run because no cuboid was fit."
    triggered = False
    stopped = "no_cuboid"

    for index in range(MAX_CUBOIDS):
        if len(work) < MIN_POINTS:
            stopped = "too_few_points_remaining"
            break
        attempt_seed = int(seed) + index
        result = _fit_once(work, attempt_seed)
        inliers = np.asarray(result.inliers, dtype=int)
        extents = np.asarray(result.extents, dtype=float).reshape(-1)
        record: dict[str, Any] = {
            "index": index,
            "random_seed": attempt_seed,
            "n_points_in": int(len(work)),
            "n_inliers": int(inliers.size),
        }
        if extents.size != 3 or inliers.size < MIN_POINTS or not np.all(np.isfinite(extents)):
            record["decision"] = "rejected_no_cuboid"
            attempts.append(record)
            stopped = "fit_returned_no_cuboid"
            break
        ordered = np.sort(extents)
        record["extents_sorted_m"] = _round_m(ordered)
        if index == 0:
            triggered = is_wall_swallow(ordered)
            wall_log = _swallow_log(ordered, triggered)
            record["wall_swallow"] = triggered
            if triggered:
                record["decision"] = "rejected_wall_swallow"
                attempts.append(record)
                stopped = "wall_swallow"
                break
        detections = detections_from_clusters([work[inliers]], reference=reference_vec)
        if not detections:
            record["decision"] = "rejected_too_few_points_for_obb"
            attempts.append(record)
        else:
            detection = detections[0]
            length_m = float(detection.extent_sorted_m[2])
            record["nominal_guess"] = detection.nominal_guess
            record["obb_extent_sorted_m"] = _round_m(detection.extent_sorted_m)
            record["theta_deg"] = float(round(float(detection.theta_deg), 5))
            stud_like = (
                detection.nominal_guess is not None
                and MIN_LENGTH_M <= length_m <= MAX_LENGTH_M
                and float(detection.theta_deg) <= MAX_UPRIGHT_DEG
            )
            if stud_like:
                record["decision"] = "accepted"
                accepted.append(work[inliers])
            else:
                record["decision"] = "rejected_section_prior"
            attempts.append(record)
        mask = np.ones(len(work), dtype=bool)
        mask[inliers] = False
        work = work[mask]
        if record["decision"] == "accepted" and len(work) < MIN_POINTS:
            stopped = "accepted_and_remainder_below_min_points"
            break
    else:
        stopped = "max_cuboids"

    return {
        "clusters": accepted,
        "attempts": attempts,
        "stopped": stopped,
        "wall_swallow": {
            "triggered": triggered,
            "second_extent_limit_m": WALL_SWALLOW_SECOND_EXTENT_M,
            "long_extent_limit_m": WALL_SWALLOW_LONG_EXTENT_M,
            "log": wall_log,
        },
        "peel": {
            "floor_found": floor_normal is not None,
            "n_points_in": int(len(points)),
            "n_points_after_peel": int(keep.sum()),
            "removed_z_intervals_m": [[float(lo), float(hi)] for lo, hi in intervals],
            "reference": reference_name,
            "note": (
                "Same horizontal-slab peel as rank 1. "
                f"Angle reference for this cloud is {reference_name}. "
                "The cloud is not rotated. A level reading is not the synthetic reference."
            ),
        },
    }


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    """Fit cuboids on the one stud. Returns the scorecard and OBB detections."""
    from openwall_stud.poststep import score_clusters

    scene = scene or make_scene()
    record = scene_record(scene)
    try:
        import pyransac3d  # noqa: F401

        version = importlib.metadata.version("pyransac3d")
    except Exception as exc:
        blocker = (
            "pyRANSAC-3D did not import, so no cuboid was fit. "
            f"{type(exc).__name__}: {exc}. "
            f"The stage 0 cloud was generated in-process ({scene.n_points} points). "
            "Detection, geometry, angle, paint, and runtime are null."
        )
        card = blocked_card(
            algorithm_id="A6",
            algorithm=PYRANSAC["name"],
            rank=6,
            license_name="Apache-2.0",
            hardware="CPU",
            failure_modes=[
                "pyransac3d is not installed, so Cuboid.fit was not called.",
                "A first cuboid on a whole wall can swallow coplanar faces.",
            ],
            blocker=blocker,
            blocker_short="pyRANSAC-3D import failed. Cloud was generated and not segmented.",
            scene=record,
            attempt={"cloud_loaded": True, "n_points": scene.n_points, "pinned_version": "0.7.0"},
        )
        return card, []

    started = time.perf_counter()
    from openwall_stud.angle_reference import scene_has_floor

    fitted = sequential_cuboids(
        scene.points_m,
        seed=int(scene.seed),
        has_floor=scene_has_floor(scene),
    )
    runtime_s = time.perf_counter() - started
    swallow = fitted["wall_swallow"]
    attempts = fitted["attempts"]
    n_accepted = len(fitted["clusters"])
    n_inliers = int(sum(len(cluster) for cluster in fitted["clusters"]))
    if swallow["triggered"]:
        short = swallow["log"]
    elif n_accepted == 1:
        short = (
            f"pyRANSAC-3D {version} Cuboid, thresh {THRESH_M} m, {MAX_ITERATION} iterations, seed {scene.seed}. "
            "Plate peel kept every Stage 0 point. "
            f"First cuboid inliers were {attempts[0]['n_inliers']} of {attempts[0]['n_points_in']}. "
            "Wall-swallow did not fire. Shared minimal OBB, axis not forced to Z."
        )
    else:
        short = (
            f"pyRANSAC-3D {version} sequential cuboid accepted {n_accepted} clusters "
            f"(stop={fitted['stopped']}). Wall-swallow triggered={swallow['triggered']}. "
            "Shared minimal OBB, axis not forced to Z."
        )
    sections, detections = score_clusters(
        scene,
        fitted["clusters"],
        runtime_s=runtime_s,
        detection_note=(
            "Sequential pyRANSAC-3D cuboids after the rank 1 horizontal-slab peel. "
            "A cuboid is kept only when the shared minimal OBB is a 2x4 or 2x6 stick. "
            f"{swallow['log']} "
            "Counts are this synthetic stud, not a field accuracy."
        ),
        geometry_note=(
            "Section and length are the shared minimal OBB of accepted inliers versus the dressed generator size. "
            "The library extents are on the implementation record and are not this section error. "
            "The long axis is not forced to Z."
        ),
        angle_extra="The long axis is not forced to Z.",
        cost={
            "runtime_s": round(runtime_s, 4),
            "license": "Apache-2.0",
            "license_url": LICENSE_URL,
            "hardware": "CPU",
            "n_points_in": scene.n_points,
            "n_points_after_peel": fitted["peel"]["n_points_after_peel"],
            "floor_found": fitted["peel"]["floor_found"],
            "failure_modes": [
                "One cuboid on a whole wall can lock onto coplanar stud faces. The first-cuboid extent check logs that and stops.",
                "Library extents are a min-area rectangle after snapping the dominant face. They run fatter than the shared minimal OBB.",
                "thresh 0.05 m is the library default. A much smaller thresh can drop the far face of the 89 mm width.",
                "Removing inliers from a one-face cuboid would carve the stud. This run did not do that when the first box covered the member.",
                "Forcing the axis to Z would hide lean. This run does not.",
            ],
            "note": "Runtime is this process on this one stud. It is not a field budget.",
            "pyransac3d_version": version,
            "thresh_m": THRESH_M,
            "max_iteration": MAX_ITERATION,
        },
    )
    card = ran_card(
        algorithm_id="A6",
        algorithm=PYRANSAC["name"],
        rank=6,
        scene=record,
        sections=sections,
        implementation={
            "module": "openwall_stud.contenders.pyransac3d_cuboid",
            "library": "pyransac3d",
            "version": version,
            "license": "Apache-2.0",
            "doi": DOI_URL,
            "thresh_m": THRESH_M,
            "max_iteration": MAX_ITERATION,
            "random_seed": int(scene.seed),
            "random_note": "Python random.seed(scene.seed + attempt) immediately before each Cuboid.fit. v0.7.0 has no seed argument.",
            "peel": fitted["peel"],
            "wall_swallow": swallow,
            "attempts": attempts,
            "stopped": fitted["stopped"],
            "n_accepted": n_accepted,
            "n_inliers_accepted": n_inliers,
            "section_gate": (
                "Shared minimal OBB versus dressed 2x4 or 2x6, 15 mm gate, length 1.2 m to 3.3 m. "
                "Library extents are the wall-swallow check only."
            ),
        },
        implementation_short=short,
    )
    card["notes"].append(swallow["log"])
    return card, detections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="pyRANSAC-3D cuboid on the one synthetic stud, or write a stub card.")
    parser.add_argument("--stub", action="store_true", help="Write the null stub card and do not segment.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/pyransac3d_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"pyRANSAC-3D stub scorecard written to {path}. No cuboid was fit.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_pyransac3d.json")
    figure = args.figure or (repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "06-pyransac3d.png")
    publish_attempt(
        algorithm="pyransac3d",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    swallow = (card.get("implementation") or {}).get("wall_swallow") or {}
    print(swallow.get("log", ""))
    print(
        f"pyRANSAC-3D one-stud scorecard written to {dest}. "
        f"status={card['status']} bars={card.get('stage0_pass_fail')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
