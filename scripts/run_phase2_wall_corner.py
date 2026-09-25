"""Phase-2 painted wall-corner plumb pilot.

Fits two dominant vertical planes on the gitignored Polycam WallCorner cloud
and a floor plane on the lower horizontal points. The plumb reference is that
floor normal (flipped into the room). Lean against export +Z is the before
column on the same wall planes. Both are set beside the SKIL face means.
Also records nearest-neighbor spacing for the Lot62 loft ladder.

This is a wall-plumb pilot. It does not detect studs and it does not lock ε.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d

REPO = Path(__file__).resolve().parents[1]
# PLY files live in the primary checkout and are gitignored. A worktree does
# not carry data/raw.
POLY = Path(r"C:\Repos\openwall-stud-frame\data\raw\polycam")
OUT = REPO / "artifacts" / "scorecards" / "phase2_wall_corner"

CAPTURES = [
    {
        "capture": "Lot62 Loft Medium",
        "file": "room_2026-09-25.ply",
        "note": "Space/room export. Filename in data/raw/polycam is room_2026-09-25.ply.",
    },
    {
        "capture": "Lot62 Loft High",
        "file": "lot62_loft_2026-09-25_high.ply",
        "note": "Space/room export, higher density.",
    },
    {
        "capture": "WallCorner Custom close",
        "file": "wall_corner_2026-09-25.ply",
        "note": "Close Custom capture of a painted outside corner. Not exposed studs.",
    },
]

SKIL = {
    "instrument": "SKIL digital level",
    "display_convention": "about 90 degrees on the display is plumb; lean from vertical is abs(90 - reading)",
    "display_step_deg": 0.05,
    "faces": {
        "A": {
            "where": "doorway / hall side",
            "readings": [
                {"height": "top", "display_deg": 89.95, "lean_deg": 0.05},
                {"height": "mid", "display_deg": 89.75, "lean_deg": 0.25},
                {"height": "bottom", "display_deg": 89.15, "lean_deg": 0.85},
            ],
        },
        "B": {
            "where": "cat-tree / plant side",
            "readings": [
                {"height": "top", "display_deg": 89.85, "lean_deg": 0.15},
                {"height": "mid", "display_deg": 89.95, "lean_deg": 0.05},
                {"height": "bottom", "display_deg": 89.45, "lean_deg": 0.55},
            ],
        },
    },
}

UP = np.array([0.0, 0.0, 1.0])
RANSAC_DIST_M = 0.010
REFIT_DIST_M = 0.010
VOXEL_M = 0.004
MAX_PLANES = 6
MIN_DOWNSAMPLED = 800
VERTICAL_MAX_ABS_NZ = 0.34  # normal within ~20 deg of horizontal
HORIZONTAL_MIN_ABS_NZ = 0.94
# Floor is fit only on the lower band, then on points whose normals are
# already near export-horizontal. 5 mm is tighter than the wall distance so
# a baseboard toe or a carpet ridge is less likely to own the plane.
FLOOR_BAND_M = 0.080
FLOOR_NORMAL_RADIUS_M = 0.030
FLOOR_GROUP_GAP_M = 0.020
FLOOR_RANSAC_DIST_M = 0.005
FLOOR_REFIT_DIST_M = 0.005
FLOOR_ERODE_M = 0.050


def lean_from_up_deg(normal: np.ndarray, up: np.ndarray) -> float:
    """Lean of a wall plane from the plumb line `up`, in degrees.

    For a unit wall normal n and a unit up vector u this is arcsin(|n · u|).
    Zero means n lies in the horizontal plane perpendicular to u, so the
    plumb line lies in the wall. The same number is the angle between the
    wall normal and that horizontal plane, and the angle between the wall
    plane and the plumb line. It is the wall-plane form of the stud rule
    (angle of the long axis to the stored up vector, zero when plumb).
    """
    n = np.asarray(normal, dtype=np.float64)
    u = np.asarray(up, dtype=np.float64)
    n = n / np.linalg.norm(n)
    u = u / np.linalg.norm(u)
    return float(np.degrees(np.arcsin(np.clip(abs(float(np.dot(n, u))), 0.0, 1.0))))


def lean_from_vertical_deg(normal: np.ndarray) -> float:
    return lean_from_up_deg(normal, UP)


def tilt_from_horizontal_deg(normal: np.ndarray) -> float:
    """Angle between a floor normal and export +Z. Zero is export-horizontal."""
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return float(np.degrees(np.arccos(np.clip(abs(float(n[2])), 0.0, 1.0))))


def angle_between_normals_deg(a: np.ndarray, b: np.ndarray) -> float:
    aa = a / np.linalg.norm(a)
    bb = b / np.linalg.norm(b)
    return float(np.degrees(np.arccos(np.clip(abs(float(np.dot(aa, bb))), 0.0, 1.0))))


def svd_plane(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - center, full_matrices=False)
    normal = vh[-1]
    normal = normal / np.linalg.norm(normal)
    if normal[2] < 0:
        normal = -normal
    residual = points - center
    rmse = float(np.sqrt(np.mean(np.square(residual @ normal))))
    return normal, center, rmse


def nn_stats(points: np.ndarray, query_cap: int = 12000, seed: int = 25) -> dict:
    n = len(points)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.ascontiguousarray(points, dtype=np.float64))
    if n <= query_cap:
        dists = np.asarray(pcd.compute_nearest_neighbor_distance(), dtype=np.float64)
        queried = n
    else:
        rng = np.random.default_rng(seed)
        query_idx = rng.choice(n, size=query_cap, replace=False)
        tree = o3d.geometry.KDTreeFlann(pcd)
        dists = np.empty(query_cap, dtype=np.float64)
        for i, qi in enumerate(query_idx):
            _, _, dist2 = tree.search_knn_vector_3d(points[qi], 2)
            dists[i] = np.sqrt(dist2[1])
        queried = query_cap
    return {
        "queries": int(queried),
        "nn_p50_mm": float(np.percentile(dists, 50) * 1000.0),
        "nn_p90_mm": float(np.percentile(dists, 90) * 1000.0),
        "nn_mean_mm": float(dists.mean() * 1000.0),
    }


def occupied_voxels(points: np.ndarray, voxel_m: float) -> int:
    q = np.floor(points / voxel_m).astype(np.int64)
    return int(np.unique(q, axis=0).shape[0])


def load_xyz(path: Path) -> np.ndarray:
    cloud = o3d.io.read_point_cloud(str(path))
    if cloud.is_empty():
        raise RuntimeError(f"empty cloud: {path}")
    return np.asarray(cloud.points)


def extract_models(points: np.ndarray) -> list[dict]:
    down = o3d.geometry.PointCloud()
    down.points = o3d.utility.Vector3dVector(np.ascontiguousarray(points, dtype=np.float64))
    down = down.voxel_down_sample(VOXEL_M)
    remaining = down
    found = []
    for _ in range(MAX_PLANES):
        if len(remaining.points) < MIN_DOWNSAMPLED:
            break
        model, inliers = remaining.segment_plane(
            distance_threshold=RANSAC_DIST_M,
            ransac_n=3,
            num_iterations=2500,
        )
        if len(inliers) < MIN_DOWNSAMPLED:
            break
        normal = np.array(model[:3], dtype=np.float64)
        normal = normal / np.linalg.norm(normal)
        found.append(
            {
                "ransac_normal": normal,
                "ransac_d": float(model[3]),
                "down_inliers": int(len(inliers)),
            }
        )
        remaining = remaining.select_by_index(inliers, invert=True)
    return found


def assign_full(points: np.ndarray, models: list[dict]) -> list[dict]:
    """Refit each RANSAC plane on full-resolution points near it.

    Points within REFIT_DIST_M of an earlier plane stay with that plane so
    the corner edge is not double-counted.
    """
    unused = np.ones(len(points), dtype=bool)
    planes = []
    for model in models:
        n = model["ransac_normal"]
        # plane: n·x + d = 0 in Open3D, with d = model[3]
        dist = np.abs(points @ n + model["ransac_d"])
        sel = unused & (dist <= REFIT_DIST_M)
        if int(sel.sum()) < 500:
            continue
        normal, center, rmse = svd_plane(points[sel])
        # Keep the SVD normal facing the same half-space as the RANSAC normal.
        if float(np.dot(normal, n)) < 0:
            normal = -normal
        dist2 = np.abs((points - center) @ normal)
        sel = unused & (dist2 <= REFIT_DIST_M)
        if int(sel.sum()) < 500:
            continue
        normal, center, rmse = svd_plane(points[sel])
        if float(np.dot(normal, n)) < 0:
            normal = -normal
        kind = "other"
        abs_nz = abs(float(normal[2]))
        if abs_nz >= HORIZONTAL_MIN_ABS_NZ:
            kind = "horizontal"
        elif abs_nz <= VERTICAL_MAX_ABS_NZ:
            kind = "vertical"
        planes.append(
            {
                "kind": kind,
                "normal": normal,
                "center": center,
                "rmse_mm": rmse * 1000.0,
                "inliers": int(sel.sum()),
                "mask": sel,
                "lean_from_vertical_deg": lean_from_vertical_deg(normal),
                "z_min_m": float(points[sel, 2].min()),
                "z_max_m": float(points[sel, 2].max()),
            }
        )
        unused[sel] = False
    return planes


def height_bins(
    points: np.ndarray,
    mask: np.ndarray,
    normal: np.ndarray,
    up: np.ndarray,
    *,
    axis_name: str,
) -> list[dict]:
    """Equal-count thirds along `up`. Bottom is the end toward decreasing up."""
    xyz = points[mask]
    if len(xyz) < 300:
        return []
    axis = np.asarray(up, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    coord = xyz @ axis
    edges = np.quantile(coord, [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0])
    labels = ["bottom", "mid", "top"]
    rows = []
    for i, label in enumerate(labels):
        if i == 2:
            band = (coord >= edges[i]) & (coord <= edges[i + 1])
        else:
            band = (coord >= edges[i]) & (coord < edges[i + 1])
        if int(band.sum()) < 200:
            continue
        n, _center, rmse = svd_plane(xyz[band])
        if float(np.dot(n, normal)) < 0:
            n = -n
        rows.append(
            {
                "height": label,
                "axis": axis_name,
                "s_lo_m": float(edges[i]),
                "s_hi_m": float(edges[i + 1]),
                "points": int(band.sum()),
                "lean_from_export_plus_z_deg": lean_from_up_deg(n, UP),
                "lean_from_floor_normal_deg": None,
                "rmse_mm": rmse * 1000.0,
                "normal_xyz": [float(x) for x in n],
            }
        )
    return rows


def _lowest_horizontal_slab(down_points: np.ndarray, down_normals: np.ndarray) -> tuple[np.ndarray, float, float]:
    horizontal = np.abs(down_normals[:, 2]) >= HORIZONTAL_MIN_ABS_NZ
    if int(horizontal.sum()) < 50:
        raise RuntimeError("lower band has too few horizontal points for a floor")
    z_h = down_points[horizontal, 2]
    order = np.argsort(z_h)
    splits = np.where(np.diff(z_h[order]) > FLOOR_GROUP_GAP_M)[0] + 1
    groups = [g for g in np.split(z_h[order], splits) if g.size >= 50]
    if not groups:
        raise RuntimeError("no horizontal z-group in the lower band")
    lowest = min(groups, key=lambda g: float(g.min()))
    lo, hi = float(lowest.min()), float(lowest.max())
    slab = horizontal & (down_points[:, 2] >= lo) & (down_points[:, 2] <= hi)
    return slab, lo, hi


def orient_into_room(normal: np.ndarray, floor_center: np.ndarray, room_point: np.ndarray) -> np.ndarray:
    """Flip so the normal points into the room, away from the floor."""
    n = np.asarray(normal, dtype=np.float64)
    if float(np.dot(n, room_point - floor_center)) < 0.0:
        n = -n
    return n


def fit_floor_gravity(points: np.ndarray, wall_masks: list[np.ndarray], room_point: np.ndarray) -> dict:
    """RANSAC plus SVD on the lowest horizontal slab.

    The band is the bottom FLOOR_BAND_M of export Z. Normals are estimated
    on a 4 mm voxel cloud. Only points already near horizontal enter the
    slab, so a vertical baseboard in that band does not tilt the SVD.
    The normal is then flipped into the room.
    """
    z0 = float(points[:, 2].min())
    band_limit = z0 + FLOOR_BAND_M
    band = points[points[:, 2] <= band_limit]
    down = o3d.geometry.PointCloud()
    down.points = o3d.utility.Vector3dVector(np.ascontiguousarray(band, dtype=np.float64))
    down = down.voxel_down_sample(VOXEL_M)
    down.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=FLOOR_NORMAL_RADIUS_M,
            max_nn=30,
        )
    )
    down_points = np.asarray(down.points)
    down_normals = np.asarray(down.normals)
    slab, slab_lo, slab_hi = _lowest_horizontal_slab(down_points, down_normals)
    slab_cloud = o3d.geometry.PointCloud()
    slab_cloud.points = o3d.utility.Vector3dVector(np.ascontiguousarray(down_points[slab], dtype=np.float64))
    model, inliers = slab_cloud.segment_plane(
        distance_threshold=FLOOR_RANSAC_DIST_M,
        ransac_n=3,
        num_iterations=4000,
    )
    if len(inliers) < 100:
        raise RuntimeError(f"floor RANSAC kept only {len(inliers)} downsampled points")
    ransac_normal = np.array(model[:3], dtype=np.float64)
    ransac_normal = ransac_normal / np.linalg.norm(ransac_normal)
    dist = np.abs(points @ ransac_normal + float(model[3]))
    sel = (dist <= FLOOR_REFIT_DIST_M) & (points[:, 2] >= slab_lo - FLOOR_REFIT_DIST_M)
    sel &= points[:, 2] <= slab_hi + FLOOR_REFIT_DIST_M
    for mask in wall_masks:
        sel &= ~mask
    if int(sel.sum()) < 500:
        raise RuntimeError(f"floor refit kept only {int(sel.sum())} points")
    normal, center, rmse = svd_plane(points[sel])
    if float(np.dot(normal, ransac_normal)) < 0.0:
        normal = -normal
    dist2 = np.abs((points - center) @ normal)
    sel = (dist2 <= FLOOR_REFIT_DIST_M) & (points[:, 2] >= slab_lo - FLOOR_REFIT_DIST_M)
    sel &= points[:, 2] <= slab_hi + FLOOR_REFIT_DIST_M
    for mask in wall_masks:
        sel &= ~mask
    normal, center, rmse = svd_plane(points[sel])
    normal = orient_into_room(normal, center, room_point)
    return {
        "normal": normal,
        "center": center,
        "rmse_mm": rmse * 1000.0,
        "inliers": int(sel.sum()),
        "mask": sel,
        "slab_z_lo_m": slab_lo,
        "slab_z_hi_m": slab_hi,
        "band_z_hi_m": float(band_limit),
        "down_horizontal": int(slab.sum()),
        "down_ransac_inliers": int(len(inliers)),
    }


def inplane_extent_m(points: np.ndarray, normal: np.ndarray, center: np.ndarray) -> list[float]:
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    helper = np.array([1.0, 0.0, 0.0]) if abs(float(n[0])) < 0.9 else np.array([0.0, 1.0, 0.0])
    axis_u = np.cross(n, helper)
    axis_u = axis_u / np.linalg.norm(axis_u)
    axis_v = np.cross(n, axis_u)
    centered = points - center
    spans = [float(np.ptp(centered @ axis_u)), float(np.ptp(centered @ axis_v))]
    spans.sort(reverse=True)
    return spans


def orient_outward(plane: dict, corner: np.ndarray) -> None:
    """Point the normal toward the scanned air, away from the corner edge."""
    if float(np.dot(plane["normal"], plane["center"] - corner)) < 0:
        plane["normal"] = -plane["normal"]


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)

    density_rows = []
    for spec in CAPTURES:
        path = POLY / spec["file"]
        pts = load_xyz(path)
        stats = nn_stats(pts)
        density_rows.append(
            {
                "capture": spec["capture"],
                "file": spec["file"],
                "points": int(len(pts)),
                "bytes": int(path.stat().st_size),
                **stats,
                "occupied_4mm_voxels": occupied_voxels(pts, 0.004) if spec["capture"].startswith("WallCorner") else None,
                "note": spec["note"],
            }
        )
        print(
            f"{spec['capture']}: n={len(pts)} nn_p50={stats['nn_p50_mm']:.2f} mm",
            flush=True,
        )

    corner_path = POLY / "wall_corner_2026-09-25.ply"
    corner = load_xyz(corner_path)
    models = extract_models(corner)
    planes = assign_full(corner, models)
    verticals = [p for p in planes if p["kind"] == "vertical"]
    verticals.sort(key=lambda p: p["inliers"], reverse=True)
    horizontals = [p for p in planes if p["kind"] == "horizontal"]
    horizontals.sort(key=lambda p: p["inliers"], reverse=True)
    walls = verticals[:2]
    if len(walls) < 2:
        raise RuntimeError(f"expected two vertical planes, found {len(verticals)}")

    # Corner edge is the cross of the two wall normals, near the shared seam.
    edge = np.cross(walls[0]["normal"], walls[1]["normal"])
    edge = edge / np.linalg.norm(edge)
    if edge[2] < 0:
        edge = -edge
    seam = 0.5 * (walls[0]["center"] + walls[1]["center"])
    for wall in walls:
        orient_outward(wall, seam)
    dihedral = angle_between_normals_deg(walls[0]["normal"], walls[1]["normal"])
    edge_from_vertical = float(np.degrees(np.arccos(np.clip(abs(edge[2]), 0.0, 1.0))))

    sequential_floor = horizontals[0] if horizontals else None
    for i, wall in enumerate(walls):
        wall["face_slot"] = f"plane_{i + 1}"
        wall["skil_face"] = None  # not registered to Face A or Face B

    room_point = np.mean([wall["center"] for wall in walls], axis=0)
    floor = fit_floor_gravity(corner, [wall["mask"] for wall in walls], room_point)
    floor_up = floor["normal"] / np.linalg.norm(floor["normal"])
    for wall in walls:
        wall["lean_from_floor_normal_deg"] = lean_from_up_deg(wall["normal"], floor_up)
        wall["height_bins_export_z"] = height_bins(
            corner, wall["mask"], wall["normal"], UP, axis_name="export_+Z"
        )
        wall["height_bins_floor_up"] = height_bins(
            corner, wall["mask"], wall["normal"], floor_up, axis_name="floor_normal"
        )
        for band in wall["height_bins_export_z"] + wall["height_bins_floor_up"]:
            n = np.array(band["normal_xyz"], dtype=np.float64)
            band["lean_from_floor_normal_deg"] = lean_from_up_deg(n, floor_up)

    skil_means = {}
    for key, face in SKIL["faces"].items():
        leans = [r["lean_deg"] for r in face["readings"]]
        skil_means[key] = float(np.mean(leans))

    # Unpaired comparison. Sorting both lists does not identify a face.
    def unpaired(cloud_values: list[float]) -> dict:
        cloud_sorted = sorted(cloud_values)
        skil_sorted = sorted(skil_means.values())
        return {
            "registered": False,
            "sorted_abs_delta_deg": [abs(c - s) for c, s in zip(cloud_sorted, skil_sorted)],
            "sorted_cloud_lean_deg": cloud_sorted,
            "sorted_skil_mean_lean_deg": skil_sorted,
        }

    pairing_before = unpaired([w["lean_from_vertical_deg"] for w in walls])
    pairing_after = unpaired([w["lean_from_floor_normal_deg"] for w in walls])
    pairing_before["reason"] = (
        "The close cloud is an outside corner patch. It does not contain the doorway or the cat tree, "
        "so plane 1 and plane 2 are not assigned to Face A or Face B. This column uses export +Z."
    )
    pairing_after["reason"] = (
        "Same unpaired sort as the export-+Z column. This column uses the floor normal as up."
    )

    edge_from_floor = float(
        np.degrees(np.arccos(np.clip(abs(float(np.dot(edge, floor_up))), 0.0, 1.0)))
    )
    floor_points = corner[floor["mask"]]
    inplane = inplane_extent_m(floor_points, floor["normal"], floor["center"])

    # Sensitivities. They are not the result. The primary up vector is floor_up.
    sensitivities = []
    if sequential_floor is not None:
        seq_n = orient_into_room(sequential_floor["normal"], sequential_floor["center"], room_point)
        sensitivities.append(
            {
                "name": "sequential_ransac_10mm",
                "note": "Third dominant plane from the wall pass (10 mm). The previous card used this patch only as a sensitivity, and its leans are not the result.",
                "inliers": sequential_floor["inliers"],
                "rmse_mm": sequential_floor["rmse_mm"],
                "tilt_from_export_horizontal_deg": tilt_from_horizontal_deg(seq_n),
                "normal_xyz": [float(x) for x in seq_n],
                "wall_lean_deg": [lean_from_up_deg(w["normal"], seq_n) for w in walls],
            }
        )
    d_walls = [
        np.abs((corner - wall["center"]) @ (wall["normal"] / np.linalg.norm(wall["normal"])))
        for wall in walls
    ]
    inner = floor["mask"].copy()
    for dist in d_walls:
        inner &= dist >= FLOOR_ERODE_M
    if int(inner.sum()) >= 500:
        eroded_n, eroded_c, eroded_rmse = svd_plane(corner[inner])
        eroded_n = orient_into_room(eroded_n, eroded_c, room_point)
        sensitivities.append(
            {
                "name": "primary_eroded_50mm_from_walls",
                "note": "Same primary inliers, then points within 50 mm of either wall plane are dropped and the plane is refit. A check for baseboard and carpet piled against the wall.",
                "inliers": int(inner.sum()),
                "rmse_mm": eroded_rmse * 1000.0,
                "tilt_from_export_horizontal_deg": tilt_from_horizontal_deg(eroded_n),
                "normal_xyz": [float(x) for x in eroded_n],
                "wall_lean_deg": [lean_from_up_deg(w["normal"], eroded_n) for w in walls],
            }
        )

    labels = np.full(len(corner), -1, dtype=np.int32)
    for i, wall in enumerate(walls):
        labels[wall["mask"]] = i
    labels[floor["mask"]] = 2

    summary_planes = []
    for wall in walls:
        summary_planes.append(
            {
                "slot": wall["face_slot"],
                "kind": "vertical_wall",
                "inliers": wall["inliers"],
                "lean_from_export_plus_z_deg": wall["lean_from_vertical_deg"],
                "lean_from_floor_normal_deg": wall["lean_from_floor_normal_deg"],
                "rmse_mm": wall["rmse_mm"],
                "normal_xyz": [float(x) for x in wall["normal"]],
                "center_xyz_m": [float(x) for x in wall["center"]],
                "z_min_m": wall["z_min_m"],
                "z_max_m": wall["z_max_m"],
                "height_bins_export_z": wall["height_bins_export_z"],
                "height_bins_floor_up": wall["height_bins_floor_up"],
                "skil_face_id": None,
            }
        )
    floor_summary = {
        "slot": "floor",
        "kind": "lower_horizontal_slab",
        "role": "plumb_reference",
        "inliers": floor["inliers"],
        "rmse_mm": floor["rmse_mm"],
        "tilt_from_export_horizontal_deg": tilt_from_horizontal_deg(floor_up),
        "normal_xyz": [float(x) for x in floor_up],
        "center_xyz_m": [float(x) for x in floor["center"]],
        "points_into_room": True,
        "orient": "Flipped so the normal points from the floor center toward the mean of the two wall centers (into the room, away from the floor). On this Z-up export that normal has positive z.",
        "slab_z_lo_m": floor["slab_z_lo_m"],
        "slab_z_hi_m": floor["slab_z_hi_m"],
        "band_z_hi_m": floor["band_z_hi_m"],
        "down_horizontal": floor["down_horizontal"],
        "down_ransac_inliers": floor["down_ransac_inliers"],
        "xyz_extent_m": [float(x) for x in (floor_points.max(0) - floor_points.min(0))],
        "inplane_extent_m": inplane,
        "z_min_m": float(floor_points[:, 2].min()),
        "z_max_m": float(floor_points[:, 2].max()),
        "note": "Up for the wall-lean result. Not a surveyed gravity vector. Carpet, baseboard, and a short corner patch can tilt it.",
    }

    scorecard = {
        "study": "TruePlank",
        "suite": "OpenWall",
        "app": "TruePlank",
        "phase": 2,
        "name": "painted_outside_wall_corner_plumb_pilot",
        "date": "2026-09-25",
        "timezone": "America/Los_Angeles",
        "machine": "Oz_PC",
        "class": "wall_plumb_pilot",
        "class_F_stud_qa": False,
        "stud_detection": "not_claimed",
        "production_paint": "yellow",
        "epsilon_locked": False,
        "epsilon_deg": None,
        "open3d": o3d.__version__,
        "numpy": np.__version__,
        "vertical_axis": "floor_plane_normal",
        "vertical_axis_before": "export_+Z",
        "lean_definition": "arcsin(|n_wall · u|) in degrees. u is export +Z before, and the floor normal after. Zero means the wall normal lies in the horizontal plane of u, so the plumb line lies in the wall. The same number is the angle between the wall normal and that horizontal plane.",
        "vertical_axis_note": "Lot62 loft exports sit on Z (floor near z=0, ceiling near 2.45 m). This corner's long axis is the same Z. The plumb proxy for this pilot is the normal of a floor plane fit to the lower horizontal points, flipped into the room. Export +Z remains the before column on the same wall planes. Neither vector is an IMU, and neither angle is a stud-axis angle. A floor that is not level is not gravity.",
        "cloud": {
            "path": "data/raw/polycam/wall_corner_2026-09-25.ply",
            "gitignored": True,
            "points": int(len(corner)),
            "bytes": int(corner_path.stat().st_size),
            "extent_m": [float(x) for x in (corner.max(0) - corner.min(0))],
            "min_xyz_m": [float(x) for x in corner.min(0)],
            "max_xyz_m": [float(x) for x in corner.max(0)],
        },
        "fit": {
            "walls": {
                "voxel_m": VOXEL_M,
                "ransac_distance_m": RANSAC_DIST_M,
                "refit_distance_m": REFIT_DIST_M,
                "ransac_iterations": 2500,
                "refit": "svd_on_full_resolution_inliers",
            },
            "floor": {
                "band_above_zmin_m": FLOOR_BAND_M,
                "voxel_m": VOXEL_M,
                "normal_radius_m": FLOOR_NORMAL_RADIUS_M,
                "horizontal_min_abs_nz": HORIZONTAL_MIN_ABS_NZ,
                "group_gap_m": FLOOR_GROUP_GAP_M,
                "ransac_distance_m": FLOOR_RANSAC_DIST_M,
                "refit_distance_m": FLOOR_REFIT_DIST_M,
                "ransac_iterations": 4000,
                "wall_inliers_excluded": True,
                "refit": "svd_on_full_resolution_inliers_of_the_lowest_horizontal_slab",
            },
        },
        "walls": summary_planes,
        "floor": floor_summary,
        "floor_sensitivities": sensitivities,
        "dihedral_between_wall_normals_deg": dihedral,
        "corner_edge_angle_from_plus_z_deg": edge_from_vertical,
        "corner_edge_angle_from_floor_normal_deg": edge_from_floor,
        "corner_edge_xyz": [float(x) for x in edge],
        "skil": SKIL,
        "skil_face_mean_lean_deg": skil_means,
        "pairing_export_plus_z": pairing_before,
        "pairing_floor_normal": pairing_after,
        "density_ladder": density_rows,
        "limits": [
            "Painted drywall is not stud wood.",
            "One global plane cannot reproduce three SKIL heights when the face bows.",
            "The floor normal is the up proxy. It is not a surveyed gravity vector. Carpet, baseboard, and a short corner patch can tilt it, and the floor itself may not be level.",
            "Faces are not registered. Sorting the two leans against the two SKIL means is an unpaired magnitude check.",
            "No stud instance, no oriented stud box, no class-F score.",
            "ε stays unlocked. Production paint stays yellow.",
        ],
        "runtime_s": None,
    }

    # Drop masks before timing close-out.
    scorecard["runtime_s"] = round(time.perf_counter() - t0, 3)

    with (OUT / "scorecard.json").open("w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)
        f.write("\n")

    with (OUT / "density_ladder.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "capture",
                "file",
                "points",
                "bytes",
                "nn_p50_mm",
                "nn_p90_mm",
                "nn_mean_mm",
                "queries",
                "occupied_4mm_voxels",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(density_rows)

    with (OUT / "planes.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "slot",
                "kind",
                "inliers",
                "lean_from_export_plus_z_deg",
                "lean_from_floor_normal_deg",
                "rmse_mm",
                "nx",
                "ny",
                "nz",
            ]
        )
        for wall in summary_planes:
            n = wall["normal_xyz"]
            writer.writerow(
                [
                    wall["slot"],
                    wall["kind"],
                    wall["inliers"],
                    f"{wall['lean_from_export_plus_z_deg']:.6f}",
                    f"{wall['lean_from_floor_normal_deg']:.6f}",
                    f"{wall['rmse_mm']:.4f}",
                    f"{n[0]:.6f}",
                    f"{n[1]:.6f}",
                    f"{n[2]:.6f}",
                ]
            )
        n = floor_summary["normal_xyz"]
        writer.writerow(
            [
                "floor",
                floor_summary["kind"],
                floor_summary["inliers"],
                "",
                "",
                f"{floor_summary['rmse_mm']:.4f}",
                f"{n[0]:.6f}",
                f"{n[1]:.6f}",
                f"{n[2]:.6f}",
            ]
        )

    with (OUT / "skil_vs_cloud.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "source",
                "height",
                "display_deg",
                "lean_from_export_plus_z_deg",
                "lean_from_floor_normal_deg",
                "notes",
            ]
        )
        for key, face in SKIL["faces"].items():
            for row in face["readings"]:
                writer.writerow(
                    [
                        f"SKIL Face {key}",
                        row["height"],
                        f"{row['display_deg']:.2f}",
                        f"{row['lean_deg']:.2f}",
                        f"{row['lean_deg']:.2f}",
                        face["where"] + "; level reads gravity, so both columns repeat the same lean",
                    ]
                )
            writer.writerow(
                [
                    f"SKIL Face {key} mean",
                    "mean",
                    "",
                    f"{skil_means[key]:.4f}",
                    f"{skil_means[key]:.4f}",
                    "mean of three leans",
                ]
            )
        for wall in summary_planes:
            writer.writerow(
                [
                    wall["slot"],
                    "global_plane",
                    "",
                    f"{wall['lean_from_export_plus_z_deg']:.6f}",
                    f"{wall['lean_from_floor_normal_deg']:.6f}",
                    "not registered to a SKIL face",
                ]
            )
            for band in wall["height_bins_export_z"]:
                writer.writerow(
                    [
                        wall["slot"],
                        band["height"],
                        "",
                        f"{band['lean_from_export_plus_z_deg']:.6f}",
                        "",
                        f"equal-count third along export Z, s {band['s_lo_m']:.3f} to {band['s_hi_m']:.3f} m",
                    ]
                )
            for band in wall["height_bins_floor_up"]:
                writer.writerow(
                    [
                        wall["slot"],
                        band["height"],
                        "",
                        "",
                        f"{band['lean_from_floor_normal_deg']:.6f}",
                        f"equal-count third along the floor normal, s {band['s_lo_m']:.3f} to {band['s_hi_m']:.3f} m",
                    ]
                )

    floor_gravity = {
        "study": "TruePlank",
        "suite": "OpenWall",
        "app": "TruePlank",
        "phase": 2,
        "name": "wall_corner_floor_gravity",
        "date": "2026-09-25",
        "stud_detection": "not_claimed",
        "class_F_stud_qa": False,
        "epsilon_locked": False,
        "production_paint": "yellow",
        "lean_definition": scorecard["lean_definition"],
        "up_before": "export_+Z",
        "up_after": "floor_plane_normal",
        "faces_registered": False,
        "skil_face_mean_lean_deg": skil_means,
        "walls": [
            {
                "slot": wall["slot"],
                "lean_from_export_plus_z_deg": wall["lean_from_export_plus_z_deg"],
                "lean_from_floor_normal_deg": wall["lean_from_floor_normal_deg"],
                "height_thirds_along_floor_up_deg": {
                    band["height"]: band["lean_from_floor_normal_deg"] for band in wall["height_bins_floor_up"]
                },
            }
            for wall in summary_planes
        ],
        "floor": {
            "inliers": floor_summary["inliers"],
            "rmse_mm": floor_summary["rmse_mm"],
            "tilt_from_export_horizontal_deg": floor_summary["tilt_from_export_horizontal_deg"],
            "normal_xyz": floor_summary["normal_xyz"],
            "inplane_extent_m": floor_summary["inplane_extent_m"],
            "orient": floor_summary["orient"],
        },
        "pairing_export_plus_z": pairing_before,
        "pairing_floor_normal": pairing_after,
        "corner_edge_angle_from_plus_z_deg": edge_from_vertical,
        "corner_edge_angle_from_floor_normal_deg": edge_from_floor,
        "sensitivities": sensitivities,
        "limits": scorecard["limits"],
    }
    with (OUT / "floor_gravity.json").open("w", encoding="utf-8") as f:
        json.dump(floor_gravity, f, indent=2)
        f.write("\n")

    write_figures(corner, labels, summary_planes, skil_means, dihedral)
    print(
        json.dumps(
            {
                "plus_z": [wall["lean_from_export_plus_z_deg"] for wall in summary_planes],
                "floor": [wall["lean_from_floor_normal_deg"] for wall in summary_planes],
                "tilt": floor_summary["tilt_from_export_horizontal_deg"],
                "pairing_before": pairing_before["sorted_abs_delta_deg"],
                "pairing_after": pairing_after["sorted_abs_delta_deg"],
                "runtime_s": scorecard["runtime_s"],
            },
            indent=2,
        )
    )


def write_figures(points, labels, walls, skil_means, dihedral: float) -> None:
    rng = np.random.default_rng(25)
    take = min(80000, len(points))
    idx = rng.choice(len(points), size=take, replace=False)
    sample = points[idx]
    slab = labels[idx]
    colors = {
        -1: "#d5d8dc",
        0: "#c0392b",
        1: "#2471a3",
        2: "#7f8c8d",
    }
    names = {-1: "other", 0: "plane 1", 1: "plane 2", 2: "floor"}

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.6))
    for ax, (xi, yi, title) in zip(
        axes,
        ((0, 1, "Plan, export XY"), (0, 2, "Elevation, export XZ")),
    ):
        for key in (-1, 2, 0, 1):
            m = slab == key
            if not np.any(m):
                continue
            ax.scatter(
                sample[m, xi],
                sample[m, yi],
                s=1,
                c=colors[key],
                linewidths=0,
                label=names[key],
                rasterized=True,
            )
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x (m)" if xi == 0 else "y (m)")
        ax.set_ylabel("y (m)" if yi == 1 else "z (m)")
        ax.set_title(title)
        ax.grid(True, linewidth=0.3, alpha=0.4)
    axes[0].legend(markerscale=6, frameon=False, loc="best")
    fig.suptitle("Phase 2 wall corner — painted faces, not studs", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "preview_views.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    labels_bar = [
        "SKIL A\nmean",
        "SKIL B\nmean",
        "plane 1\nexport +Z",
        "plane 2\nexport +Z",
        "plane 1\nfloor normal",
        "plane 2\nfloor normal",
    ]
    values = [
        skil_means["A"],
        skil_means["B"],
        walls[0]["lean_from_export_plus_z_deg"],
        walls[1]["lean_from_export_plus_z_deg"],
        walls[0]["lean_from_floor_normal_deg"],
        walls[1]["lean_from_floor_normal_deg"],
    ]
    bar_colors = ["#1a5276", "#1a5276", "#b03a2e", "#1a5276", "#c0392b", "#2471a3"]
    # plane 2 before should stay visually distinct from SKIL. Use a lighter blue.
    bar_colors[3] = "#7fb3d5"
    ax.bar(labels_bar, values, color=bar_colors, width=0.72)
    ax.set_ylabel("Lean from plumb (degrees)")
    ax.set_title("SKIL means vs the same wall planes (faces not registered)")
    ax.axhline(0.1194, color="#b7950b", linestyle="--", linewidth=1, label="τ ≈ 0.119° (not a paint call)")
    ax.legend(frameon=False)
    ax.set_ylim(0, max(values) * 1.25 + 0.05)
    fig.tight_layout()
    fig.savefig(OUT / "skil_vs_cloud_lean.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.2), sharey=True)
    for ax, wall, color in zip(axes, walls, ("#c0392b", "#2471a3")):
        names_h = [b["height"] for b in wall["height_bins_floor_up"]]
        leans = [b["lean_from_floor_normal_deg"] for b in wall["height_bins_floor_up"]]
        ax.bar(names_h, leans, color=color, width=0.7)
        ax.axhline(wall["lean_from_floor_normal_deg"], color="black", linewidth=0.8, linestyle=":")
        ax.set_title(f"{wall['slot']} by height third")
        ax.set_ylabel("Lean from the floor normal (degrees)")
        ax.grid(True, axis="y", linewidth=0.3, alpha=0.4)
    fig.suptitle(f"Local plane lean along the floor normal. Dihedral {dihedral:.2f}°", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "height_thirds.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
