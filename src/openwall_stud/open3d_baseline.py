"""Refined Open3D stud baseline (rank 1).

Pipeline on one cloud:

1. Peel horizontal slabs (floor and plates). A stud face is vertical, so it
   stays. Slabs within one plate-thickness of each other are removed together
   so a plate's vertical side faces do not remain and bridge bays.
2. DBSCAN the remainder with ``eps`` below a clear 16 inch bay gap.
3. Oriented box on each cluster. Keep clusters whose section is near a 2x4 or
   2x6 and whose long axis is upright relative to the reference.
4. Lean is the angle between that long axis and the reference. The reference
   is the floor normal when a slab was peeled, otherwise generator +Z.
   The cloud is not rotated onto the floor.

Device epsilon stays unlocked. Production paint is yellow. A placeholder
epsilon is recorded beside it and is not a measured band.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import open3d as o3d

from openwall_stud.angle_reference import (
    lock_synthetic_reference,
    scene_has_floor,
    synthetic_angle_note,
)
from openwall_stud.lumber import DRESSED_SECTION_M, TOLERANCE_DEG
from openwall_stud.paint import PLACEHOLDER_EPSILON_DEG, hypothetical_placeholder, paint_stud
from openwall_stud.synthetic import Scene

# 20 mm connects a 5 mm surface sample, including across a face edge, and is
# far below the ~368 mm clear gap of a 16 inch bay of 2x4s.
# 25 mm reaches neighboring samples on a 5 mm surface grid (a core point then
# has several dozen neighbors) and stays far under a ~368 mm bay gap.
DEFAULT_DBSCAN_EPS_M = 0.025
DEFAULT_DBSCAN_MIN_POINTS = 20
# Section gate is wider than the scorecard bar so a slightly fat box is still
# counted, and the scorecard can report the real error.
SECTION_GATE_M = 0.015
MIN_LENGTH_M = 1.2
MAX_LENGTH_M = 3.3
MAX_UPRIGHT_DEG = 20.0


@dataclass
class Detection:
    cluster_id: int
    n_points: int
    center_m: np.ndarray
    extent_sorted_m: np.ndarray
    long_axis: np.ndarray
    theta_deg: float
    nominal_guess: str | None
    segments_m: np.ndarray
    production_color: str
    hypothetical_color: str


@dataclass
class BaselineRun:
    scene_name: str
    stage: int
    keep_mask: np.ndarray
    cluster_labels: np.ndarray
    detections: list[Detection] = field(default_factory=list)
    floor_found: bool = False
    floor_normal: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0]))
    reference: str = "gravity_z_no_floor_plane"
    runtime_s: float = 0.0
    dbscan_eps_m: float = DEFAULT_DBSCAN_EPS_M
    dbscan_min_points: int = DEFAULT_DBSCAN_MIN_POINTS
    n_in: int = 0
    n_after_peel: int = 0
    removed_z_intervals_m: list[tuple[float, float]] = field(default_factory=list)


def _point_cloud(points: np.ndarray) -> o3d.geometry.PointCloud:
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.ascontiguousarray(points, dtype=np.float64))
    return cloud


def _svd_normal(points: np.ndarray) -> np.ndarray:
    center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - center, full_matrices=False)
    normal = vh[-1]
    if normal[2] < 0.0:
        normal = -normal
    return normal / np.linalg.norm(normal)


def peel_horizontal_slabs(
    points: np.ndarray,
    *,
    normal_radius_m: float = 0.03,
    horizontal_cos: float = 0.85,
    min_horizontal_points: int = 800,
    group_gap_m: float = 0.02,
    union_gap_m: float = 0.05,
    margin_m: float = 0.006,
) -> tuple[np.ndarray, np.ndarray | None, list[tuple[float, float]]]:
    """Return a keep-mask, the lowest slab normal (or None), and removed z ranges."""
    if len(points) < 50:
        return np.ones(len(points), dtype=bool), None, []
    cloud = _point_cloud(points)
    cloud.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=normal_radius_m, max_nn=30)
    )
    normals = np.asarray(cloud.normals)
    horizontal = np.abs(normals[:, 2]) >= horizontal_cos
    z_h = points[horizontal, 2]
    if z_h.size < min_horizontal_points:
        return np.ones(len(points), dtype=bool), None, []

    order = np.argsort(z_h)
    z_sorted = z_h[order]
    splits = np.where(np.diff(z_sorted) > group_gap_m)[0] + 1
    groups = np.split(z_sorted, splits)
    large = [group for group in groups if group.size >= min_horizontal_points]
    if not large:
        return np.ones(len(points), dtype=bool), None, []

    intervals = [(float(group.min()), float(group.max())) for group in large]
    intervals.sort()
    merged: list[list[float]] = [[intervals[0][0], intervals[0][1]]]
    for lo, hi in intervals[1:]:
        if lo - merged[-1][1] <= union_gap_m:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    removed = [(lo - margin_m, hi + margin_m) for lo, hi in merged]

    keep = np.ones(len(points), dtype=bool)
    z = points[:, 2]
    for lo, hi in removed:
        keep &= ~((z >= lo) & (z <= hi))

    # Fit the floor normal on horizontal points in the lowest slab only.
    # Vertical stud faces that fall inside the removal margin would tilt an
    # SVD taken on every point in that z band.
    lo0, hi0 = merged[0]
    horizontal_pts = points[horizontal]
    slab = horizontal_pts[(horizontal_pts[:, 2] >= lo0) & (horizontal_pts[:, 2] <= hi0)]
    normal = _svd_normal(slab if len(slab) >= 3 else horizontal_pts)
    return keep, normal, removed


def _angle_deg(axis: np.ndarray, reference: np.ndarray) -> float:
    axis_u = axis / np.linalg.norm(axis)
    ref_u = reference / np.linalg.norm(reference)
    if float(np.dot(axis_u, ref_u)) < 0.0:
        axis_u = -axis_u
    cosine = float(np.clip(np.dot(axis_u, ref_u), -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def _guess_nominal(section_m: np.ndarray) -> str | None:
    ordered = np.sort(section_m)
    best_name = None
    best_err = SECTION_GATE_M
    for name, (thickness, width) in DRESSED_SECTION_M.items():
        target = np.sort(np.array([thickness, width]))
        err = float(np.max(np.abs(ordered - target)))
        if err <= best_err:
            best_err = err
            best_name = name
    return best_name


def _obb_segments(cloud: o3d.geometry.PointCloud) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # PCA boxes yaw on a surface-sampled stud and inflate the section.
    # The minimal box matches the point extent. Ranking note allows this fallback.
    obb = cloud.get_minimal_oriented_bounding_box()
    lines = o3d.geometry.LineSet.create_from_oriented_bounding_box(obb)
    pts = np.asarray(lines.points)
    seg_idx = np.asarray(lines.lines)
    segments = pts[seg_idx]
    extent = np.asarray(obb.extent, dtype=float)
    rotation = np.asarray(obb.R, dtype=float)
    center = np.asarray(obb.center, dtype=float)
    return center, extent, rotation, segments


def run_baseline(
    scene: Scene,
    *,
    dbscan_eps_m: float = DEFAULT_DBSCAN_EPS_M,
    dbscan_min_points: int = DEFAULT_DBSCAN_MIN_POINTS,
) -> BaselineRun:
    """Run the rank-1 pipeline on one synthetic scene."""
    import time

    started = time.perf_counter()
    points = scene.points_m
    keep, floor_normal, intervals = peel_horizontal_slabs(points)
    reference_name, reference_vec = lock_synthetic_reference(
        floor_normal,
        has_floor=scene_has_floor(scene),
    )
    labels_full = np.full(len(points), -2, dtype=int)
    detections: list[Detection] = []
    kept_idx = np.flatnonzero(keep)
    if kept_idx.size >= dbscan_min_points:
        cloud = _point_cloud(points[kept_idx])
        raw = np.asarray(
            cloud.cluster_dbscan(eps=dbscan_eps_m, min_points=dbscan_min_points, print_progress=False)
        )
        labels_full[kept_idx] = raw
        for cluster_id in sorted(int(v) for v in np.unique(raw) if v >= 0):
            member = kept_idx[raw == cluster_id]
            if member.size < dbscan_min_points:
                continue
            cluster = _point_cloud(points[member])
            center, extent, rotation, segments = _obb_segments(cluster)
            order = np.argsort(extent)
            extent_sorted = extent[order]
            long_axis = rotation[:, order[-1]]
            theta = _angle_deg(long_axis, reference_vec)
            nominal = _guess_nominal(extent_sorted[:2])
            length = float(extent_sorted[2])
            if nominal is None or not (MIN_LENGTH_M <= length <= MAX_LENGTH_M):
                continue
            if theta > MAX_UPRIGHT_DEG:
                continue
            production = paint_stud(theta, epsilon_locked=False)
            hypo = hypothetical_placeholder(theta)
            detections.append(
                Detection(
                    cluster_id=cluster_id,
                    n_points=int(member.size),
                    center_m=center,
                    extent_sorted_m=extent_sorted,
                    long_axis=long_axis / np.linalg.norm(long_axis),
                    theta_deg=theta,
                    nominal_guess=nominal,
                    segments_m=segments,
                    production_color=production.color,
                    hypothetical_color=hypo.color,
                )
            )
    detections.sort(key=lambda item: float(item.center_m[0]))
    return BaselineRun(
        scene_name=scene.name,
        stage=scene.stage,
        keep_mask=keep,
        cluster_labels=labels_full,
        detections=detections,
        floor_found=floor_normal is not None,
        floor_normal=reference_vec,
        reference=reference_name,
        runtime_s=time.perf_counter() - started,
        dbscan_eps_m=dbscan_eps_m,
        dbscan_min_points=dbscan_min_points,
        n_in=int(len(points)),
        n_after_peel=int(keep.sum()),
        removed_z_intervals_m=intervals,
    )


def match_detections(
    scene: Scene,
    run: BaselineRun,
    *,
    match_radius_m: float = 0.15,
) -> list[tuple[int, int]]:
    """Greedy nearest-center matches as (truth_index, detection_index)."""
    if not scene.studs or not run.detections:
        return []
    truth_centers = np.vstack([stud.center_m for stud in scene.studs])
    pred_centers = np.vstack([det.center_m for det in run.detections])
    distances = np.linalg.norm(truth_centers[:, None, :] - pred_centers[None, :, :], axis=2)
    pairs: list[tuple[float, int, int]] = []
    for i in range(distances.shape[0]):
        for j in range(distances.shape[1]):
            if distances[i, j] <= match_radius_m:
                pairs.append((float(distances[i, j]), i, j))
    pairs.sort()
    used_t: set[int] = set()
    used_p: set[int] = set()
    matches: list[tuple[int, int]] = []
    for _, i, j in pairs:
        if i in used_t or j in used_p:
            continue
        used_t.add(i)
        used_p.add(j)
        matches.append((i, j))
    return matches


def _round(value: float, digits: int) -> float:
    return float(round(value, digits))


def score_run(scene: Scene, run: BaselineRun, *, match_radius_m: float = 0.15) -> dict:
    """Build the five scorecard sections from one synthetic run.

    Numbers come from this run. Unmatched geometry stays null.
    """
    matches = match_detections(scene, run, match_radius_m=match_radius_m)
    n_true = len(scene.studs)
    n_pred = len(run.detections)
    tp = len(matches)
    fp = n_pred - tp
    fn = n_true - tp
    precision = None if (tp + fp) == 0 else tp / (tp + fp)
    recall = None if (tp + fn) == 0 else tp / (tp + fn)

    per_geom = []
    per_angle = []
    section_errors = []
    length_errors = []
    angle_errors = []
    for truth_i, det_i in matches:
        truth = scene.studs[truth_i]
        det = run.detections[det_i]
        target = np.sort(np.array(truth.section_m))
        measured_section = np.sort(det.extent_sorted_m[:2])
        section_err_mm = (measured_section - target) * 1000.0
        length_err_mm = (float(det.extent_sorted_m[2]) - truth.length_m) * 1000.0
        true_theta = _angle_deg(truth.long_axis, run.floor_normal)
        abs_err = abs(det.theta_deg - true_theta)
        section_errors.append(float(np.max(np.abs(section_err_mm))))
        length_errors.append(abs(length_err_mm))
        angle_errors.append(abs_err)
        per_geom.append(
            {
                "stud_id": truth.stud_id,
                "nominal": truth.nominal,
                "nominal_guess": det.nominal_guess,
                "section_true_mm": [_round(v * 1000.0, 2) for v in target],
                "section_measured_mm": [_round(v * 1000.0, 2) for v in measured_section],
                "section_error_mm": [_round(float(v), 2) for v in section_err_mm],
                "length_true_mm": _round(truth.length_m * 1000.0, 2),
                "length_measured_mm": _round(float(det.extent_sorted_m[2]) * 1000.0, 2),
                "length_error_mm": _round(length_err_mm, 2),
            }
        )
        per_angle.append(
            {
                "stud_id": truth.stud_id,
                "true_deg": _round(true_theta, 5),
                "measured_deg": _round(det.theta_deg, 5),
                "abs_error_deg": _round(abs_err, 5),
                "production_color": det.production_color,
                "hypothetical_color": det.hypothetical_color,
            }
        )

    in_band = [err <= TOLERANCE_DEG for err in angle_errors]
    return {
        "detection": {
            "n_true": n_true,
            "n_pred": n_pred,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": None if precision is None else _round(precision, 4),
            "recall": None if recall is None else _round(recall, 4),
            "match_radius_m": match_radius_m,
            "scope": "synthetic_scene_only",
            "note": "Counts are this synthetic scene, not a field accuracy.",
        },
        "geometry": {
            "max_section_error_mm": None if not section_errors else _round(max(section_errors), 2),
            "max_length_error_mm": None if not length_errors else _round(max(length_errors), 2),
            "per_stud": per_geom,
            "bbox_kind": "minimal_oriented",
            "note": "Section is the two smaller minimal-OBB extents versus the dressed nominal. Length is the longest extent versus the generator length. Gaussian tails and the plate slab margin both move these numbers.",
        },
        "angle": {
            "mae_deg": None if not angle_errors else _round(float(np.mean(angle_errors)), 5),
            "max_abs_error_deg": None if not angle_errors else _round(max(angle_errors), 5),
            "pct_in_band": None if not in_band else _round(100.0 * sum(in_band) / len(in_band), 2),
            "band_deg": _round(TOLERANCE_DEG, 5),
            "band_meaning": "Percent of matched studs whose |measured - synthetic truth| is within the working tolerance.",
            "reference": run.reference,
            "per_stud": per_angle,
            "note": synthetic_angle_note(run.reference),
        },
        "paint": {
            "epsilon_locked": False,
            "epsilon_deg": None,
            "tolerance_deg": _round(TOLERANCE_DEG, 5),
            "production_colors": [det.production_color for det in run.detections],
            "production_rule": "epsilon unlocked, so every stud is yellow",
            "hypothetical_placeholder_epsilon_deg": PLACEHOLDER_EPSILON_DEG,
            "hypothetical_placeholder_note": "0.05 deg is a round illustration of the color rule. It is not a measured device band.",
            "hypothetical_colors": [det.hypothetical_color for det in run.detections],
            "note": "Do not read hypothetical colors as a pass/fail call.",
        },
        "cost": {
            "runtime_s": _round(run.runtime_s, 4),
            "dbscan_eps_m": run.dbscan_eps_m,
            "dbscan_min_points": run.dbscan_min_points,
            "bbox_kind": "minimal_oriented",
            "license": "MIT",
            "license_url": "https://github.com/isl-org/Open3D",
            "hardware": "CPU",
            "n_points_in": run.n_in,
            "n_points_after_peel": run.n_after_peel,
            "floor_found": run.floor_found,
            "failure_modes": [
                "DBSCAN eps above the bay gap merges neighboring studs into one box.",
                "DBSCAN eps below the surface spacing splits one stud into faces.",
                "A plate side face left behind bridges bays.",
                "Peeling a vertical stud-face plane would delete the wall.",
                "PCA OBB on a short or one-sided cluster can yaw the long axis.",
            ],
            "note": "Runtime is this process on this scene. It is not a field budget.",
        },
    }
