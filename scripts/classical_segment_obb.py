#!/usr/bin/env python3
"""Classical Open3D segmentation and oriented-box views.

Heuristic geometry only. Labels are not a trained stud/beam model and
this script does not report a measured accuracy.

Pipeline
--------
1. Load a PLY (``--input``, default ``data/raw/darus-intcdc/preview.ply``).
2. ``voxel_down_sample``.
3. ``remove_statistical_outlier`` (Open3D 0.20 returns the inlier cloud
   and the inlier indices).
4. Repeated ``segment_plane`` (RANSAC). A plane is peeled only when it
   is a large thin patch that actually fills its rectangle: enough
   inliers, a long side, a wide second side, a thin third, and inlier
   coverage above ``--plane-min-coverage``. Sparse coplanar faces
   (several studs in one RANSAC plane) fail the coverage test and
   peeling stops, so those points stay for clustering. Open3D has no
   region growing and no separate Euclidean-cluster call.
   ``detect_planar_patches`` is not used: it returns one box per face,
   which splits members.
5. ``cluster_dbscan`` on the points that remain. Label ``-1`` is noise
   and is dropped. Clusters smaller than ``--min-cluster-size`` are
   dropped.
6. ``get_oriented_bounding_box`` per kept cluster (PCA of the convex
   hull). If that raises (flat or too few points), retry with
   ``robust=True``. If that also raises, use an axis-aligned box.
   A peeled plane uses the RANSAC normal and a minimum-area rectangle
   in that plane (``bbox_kind=plane_obb``). The robust Open3D hull
   inflates a flat patch, so it is not the box written for planes.
7. Heuristic label from the box extents and ``--up`` (default +Z):

   * ``planar`` — smallest side is thin relative to the middle side
   * ``upright`` — one long side, mostly parallel to ``--up``
   * ``beam_like`` — one long side, mostly perpendicular to ``--up``
   * ``blob`` — three sides of similar length
   * ``clutter`` — everything else (diagonal braces, ambiguous ratios)

``--up`` is an axis you supply. It is not a gravity sensor. The DaRUS
IntCDC scans are not documented as gravity-aligned; see the written
report. Extents are in the PLY's own units. This script does not
rescale them and does not claim they are meters.

``--seed`` seeds NumPy (PNG point subsampling). Open3D 0.20
``segment_plane`` has no seed argument, so RANSAC inliers can differ
between runs.

Views are matplotlib Agg orthographic projections (front, side, top,
iso) with box edges drawn as 2D line segments. No OpenGL window.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "darus-intcdc" / "preview.ply"
DEFAULT_OUT = REPO_ROOT / "data" / "raw" / "darus-intcdc" / "seg_out"

LABELS = ("upright", "beam_like", "planar", "blob", "clutter")
LABEL_RGB = {
    "upright": np.array([0.11, 0.45, 0.28]),
    "beam_like": np.array([0.77, 0.42, 0.10]),
    "planar": np.array([0.22, 0.40, 0.72]),
    "blob": np.array([0.42, 0.30, 0.60]),
    "clutter": np.array([0.55, 0.22, 0.22]),
}
TIMBER_RGB = np.array([0.45, 0.28, 0.14])
UNASSIGNED_RGB = np.array([0.62, 0.60, 0.56])

# Open3D OrientedBoundingBox.get_box_points order for an identity rotation.
# Local corner = sign * extent/2, then world = R @ local + center.
_BOX_SIGNS = np.array(
    [
        [-1, -1, -1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, 1],
        [1, 1, 1],
        [-1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
    ],
    dtype=float,
)
_BOX_EDGES = (
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 6),
    (1, 7),
    (2, 5),
    (2, 7),
    (3, 5),
    (3, 6),
    (4, 5),
    (4, 6),
    (4, 7),
)

VIEW_NAMES = ("front", "side", "top", "iso")


def parse_up(text: str) -> np.ndarray:
    key = text.strip().lower()
    named = {
        "x": (1.0, 0.0, 0.0),
        "y": (0.0, 1.0, 0.0),
        "z": (0.0, 0.0, 1.0),
        "+x": (1.0, 0.0, 0.0),
        "+y": (0.0, 1.0, 0.0),
        "+z": (0.0, 0.0, 1.0),
        "-x": (-1.0, 0.0, 0.0),
        "-y": (0.0, -1.0, 0.0),
        "-z": (0.0, 0.0, -1.0),
    }
    if key in named:
        return np.array(named[key], dtype=float)
    parts = [p.strip() for p in text.replace(" ", ",").split(",") if p.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "up must be x, y, z, or three comma-separated numbers"
        )
    try:
        vec = np.array([float(p) for p in parts], dtype=float)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("up vector contains a non-number") from exc
    norm = float(np.linalg.norm(vec))
    if norm < 1e-12:
        raise argparse.ArgumentTypeError("up vector has zero length")
    return vec / norm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    io_group = parser.add_argument_group("input and output")
    io_group.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=(
            "PLY path. Default: data/raw/darus-intcdc/preview.ply under the "
            "repo root (gitignored; present only on a machine that has the file)."
        ),
    )
    io_group.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help=(
            "Directory for components.json, report.md, and views/. "
            "Default is under data/raw/, which this repo gitignores."
        ),
    )
    io_group.add_argument(
        "--save-colored-ply",
        action="store_true",
        help=(
            "Also write labeled.ply (downsampled inliers, colored by heuristic "
            "label). Off by default so a multi-MB cloud is not written unless asked."
        ),
    )
    io_group.add_argument(
        "--seed",
        type=int,
        default=0,
        help=(
            "NumPy seed for PNG point subsampling. Does not seed Open3D RANSAC "
            "(segment_plane has no seed argument in 0.20)."
        ),
    )

    down_group = parser.add_argument_group("downsample and outliers")
    down_group.add_argument(
        "--voxel-size",
        type=float,
        default=0.02,
        help="Voxel size passed to voxel_down_sample, in file units (default 0.02).",
    )
    down_group.add_argument(
        "--sor-neighbors",
        type=int,
        default=20,
        help="nb_neighbors for remove_statistical_outlier (default 20).",
    )
    down_group.add_argument(
        "--sor-std-ratio",
        type=float,
        default=2.0,
        help="std_ratio for remove_statistical_outlier (default 2).",
    )

    plane_group = parser.add_argument_group("large planes")
    plane_group.add_argument(
        "--max-planes",
        type=int,
        default=6,
        help="Maximum large planes to peel with segment_plane (default 6).",
    )
    plane_group.add_argument(
        "--plane-distance",
        type=float,
        default=None,
        help=(
            "RANSAC distance_threshold. Default: max(0.03, 1.5 * voxel-size), "
            "in file units."
        ),
    )
    plane_group.add_argument(
        "--plane-iterations",
        type=int,
        default=1000,
        help="RANSAC num_iterations (default 1000).",
    )
    plane_group.add_argument(
        "--ransac-n",
        type=int,
        default=3,
        help="RANSAC sample size (default 3).",
    )
    plane_group.add_argument(
        "--plane-min-points",
        type=int,
        default=0,
        help=(
            "Minimum inliers to accept a plane. 0 means "
            "max(100, plane-min-fraction * inlier count)."
        ),
    )
    plane_group.add_argument(
        "--plane-min-fraction",
        type=float,
        default=0.05,
        help="Used when --plane-min-points is 0 (default 0.05 of inliers).",
    )
    plane_group.add_argument(
        "--plane-min-extent",
        type=float,
        default=1.5,
        help="Peel a plane only if its longest side is at least this (default 1.5).",
    )
    plane_group.add_argument(
        "--plane-min-span",
        type=float,
        default=1.0,
        help=(
            "Peel a plane only if its middle side is at least this (default 1.0). "
            "Keeps a long narrow member face from being deleted as a wall."
        ),
    )
    plane_group.add_argument(
        "--thin-ratio",
        type=float,
        default=0.20,
        help=(
            "Smallest/middle extent at or below this is thin. Used both to accept "
            "a peeled plane and to label a box planar (default 0.20)."
        ),
    )
    plane_group.add_argument(
        "--plane-min-coverage",
        type=float,
        default=0.35,
        help=(
            "Minimum fraction of the plane's own rectangle occupied by inliers "
            "(default 0.35). Below this, the plane is treated as separated "
            "coplanar faces and peeling stops."
        ),
    )

    cluster_group = parser.add_argument_group("clustering")
    cluster_group.add_argument(
        "--dbscan-eps",
        type=float,
        default=0.06,
        help="cluster_dbscan eps in file units (default 0.06, about 3 voxels).",
    )
    cluster_group.add_argument(
        "--dbscan-min-points",
        type=int,
        default=10,
        help="cluster_dbscan min_points (default 10). Label -1 is noise.",
    )
    cluster_group.add_argument(
        "--min-cluster-size",
        type=int,
        default=30,
        help="Drop DBSCAN clusters with fewer points than this (default 30).",
    )

    label_group = parser.add_argument_group("heuristic labels")
    label_group.add_argument(
        "--up",
        type=parse_up,
        default=parse_up("z"),
        help=(
            "Up axis for upright vs beam_like: x, y, z, or 'x,y,z'. Default z. "
            "This is not measured gravity. DaRUS may not be Z-up."
        ),
    )
    label_group.add_argument(
        "--elongation",
        type=float,
        default=2.8,
        help="Longest/middle extent at or above this is a stick (default 2.8).",
    )
    label_group.add_argument(
        "--vertical-cos",
        type=float,
        default=0.85,
        help=(
            "abs(dot(long axis, up)) at or above this is upright "
            "(default 0.85, about 32 degrees from up)."
        ),
    )
    label_group.add_argument(
        "--horizontal-cos",
        type=float,
        default=0.34,
        help=(
            "abs(dot(long axis, up)) at or below this is beam_like "
            "(default 0.34, about 20 degrees from horizontal)."
        ),
    )
    label_group.add_argument(
        "--blob-ratio",
        type=float,
        default=2.5,
        help="Longest/shortest at or below this, and not a stick, is blob (default 2.5).",
    )

    view_group = parser.add_argument_group("views")
    view_group.add_argument(
        "--plot-max-points",
        type=int,
        default=60000,
        help="Random subsample cap for each PNG (default 60000).",
    )
    return parser


def validate_args(args: argparse.Namespace) -> str | None:
    if args.voxel_size <= 0:
        return "--voxel-size must be positive"
    if args.sor_neighbors < 1:
        return "--sor-neighbors must be >= 1"
    if args.sor_std_ratio <= 0:
        return "--sor-std-ratio must be positive"
    if args.max_planes < 0:
        return "--max-planes must be >= 0"
    if args.plane_distance is not None and args.plane_distance <= 0:
        return "--plane-distance must be positive"
    if args.plane_iterations < 1:
        return "--plane-iterations must be >= 1"
    if args.ransac_n < 3:
        return "--ransac-n must be >= 3"
    if args.plane_min_points < 0:
        return "--plane-min-points must be >= 0"
    if not 0 < args.plane_min_fraction <= 1:
        return "--plane-min-fraction must be in (0, 1]"
    if args.plane_min_extent <= 0 or args.plane_min_span <= 0:
        return "--plane-min-extent and --plane-min-span must be positive"
    if not 0 < args.thin_ratio <= 1:
        return "--thin-ratio must be in (0, 1]"
    if not 0 < args.plane_min_coverage <= 1:
        return "--plane-min-coverage must be in (0, 1]"
    if args.dbscan_eps <= 0:
        return "--dbscan-eps must be positive"
    if args.dbscan_min_points < 1:
        return "--dbscan-min-points must be >= 1"
    if args.min_cluster_size < 1:
        return "--min-cluster-size must be >= 1"
    if args.elongation <= 1:
        return "--elongation must be > 1"
    if not 0 <= args.horizontal_cos < args.vertical_cos <= 1:
        return "--vertical-cos must be greater than --horizontal-cos, both in [0, 1]"
    if args.blob_ratio <= 1:
        return "--blob-ratio must be > 1"
    if args.plot_max_points < 100:
        return "--plot-max-points must be >= 100"
    return None


@contextlib.contextmanager
def quiet_c_stderr():
    """Hide Qhull messages written straight to C stderr during a failed hull."""
    saved = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved, 2)
        os.close(saved)
        os.close(devnull)


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_jsonable(obj.tolist())
    if isinstance(obj, np.floating):
        value = float(obj)
        if not np.isfinite(value):
            return None
        return value
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def box_corners(center, rotation, extent) -> np.ndarray:
    local = _BOX_SIGNS * (np.asarray(extent, dtype=float).reshape(3) / 2.0)
    return local @ np.asarray(rotation, dtype=float).reshape(3, 3).T + np.asarray(
        center, dtype=float
    ).reshape(3)


def long_axis_alignment(extent, rotation, up: np.ndarray) -> float | None:
    ext = np.asarray(extent, dtype=float).reshape(3)
    rot = np.asarray(rotation, dtype=float).reshape(3, 3)
    axis = rot[:, int(np.argmax(ext))]
    norm = float(np.linalg.norm(axis))
    if norm < 1e-12:
        return None
    return abs(float(np.dot(axis / norm, up)))


def classify_box(
    extent,
    rotation,
    up: np.ndarray,
    *,
    thin_ratio: float,
    elongation: float,
    vertical_cos: float,
    horizontal_cos: float,
    blob_ratio: float,
) -> tuple[str, float | None]:
    """Return (label, abs cos of the long axis with up).

    Extent order follows Open3D: ``extent[i]`` matches column ``i`` of ``R``.
    Ratios use the sorted side lengths.
    """
    sides = np.sort(np.asarray(extent, dtype=float).reshape(3))
    small, mid, long = (float(sides[0]), float(sides[1]), float(sides[2]))
    align = long_axis_alignment(extent, rotation, up)
    if mid > 1e-8 and (small / mid) <= thin_ratio:
        return "planar", align
    if mid > 1e-8 and (long / mid) >= elongation and align is not None:
        if align >= vertical_cos:
            return "upright", align
        if align <= horizontal_cos:
            return "beam_like", align
        return "clutter", align
    if small > 1e-8 and (long / small) <= blob_ratio:
        return "blob", align
    return "clutter", align


def _monotone_chain(uv: np.ndarray) -> np.ndarray:
    """2D convex hull, counterclockwise, without repeating the start point."""
    if uv.shape[0] == 0:
        return uv.reshape(0, 2)
    order = np.lexsort((uv[:, 1], uv[:, 0]))
    pts = uv[order]
    if pts.shape[0] > 1:
        keep = np.ones(pts.shape[0], dtype=bool)
        keep[1:] = np.any(np.diff(pts, axis=0) != 0, axis=1)
        pts = pts[keep]

    def turn(o, a, b) -> float:
        return float((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]))

    lower: list[np.ndarray] = []
    for point in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[np.ndarray] = []
    for point in pts[::-1]:
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    ring = lower[:-1] + upper[:-1]
    if not ring:
        return pts[:1]
    return np.vstack(ring)


def plane_aligned_box(points: np.ndarray, plane_model):
    """Oriented box whose thin axis is the RANSAC normal.

    The in-plane rectangle is the minimum-area box of the 2D convex hull.
    Open3D's robust ``get_oriented_bounding_box`` inflates a flat patch
    (a square floor came back with the diagonal as its side), so peeled
    planes use this rectangle instead.
    """
    import open3d as o3d

    pts = np.asarray(points, dtype=float)
    normal = np.asarray(plane_model, dtype=float).reshape(-1)[:3]
    norm = float(np.linalg.norm(normal))
    if pts.shape[0] == 0 or norm < 1e-12:
        return None
    normal = normal / norm
    helper = np.array([1.0, 0.0, 0.0]) if abs(float(normal[0])) < 0.9 else np.array([0.0, 1.0, 0.0])
    axis_u = np.cross(normal, helper)
    axis_u = axis_u / np.linalg.norm(axis_u)
    axis_v = np.cross(normal, axis_u)
    axis_v = axis_v / np.linalg.norm(axis_v)
    origin = pts.mean(axis=0)
    rel = pts - origin
    uv = np.column_stack((rel @ axis_u, rel @ axis_v))
    hull = _monotone_chain(uv)
    direction = np.array([1.0, 0.0])
    if hull.shape[0] >= 2:
        best_area = None
        best_dir = direction
        count = hull.shape[0]
        for i in range(count):
            edge = hull[(i + 1) % count] - hull[i]
            length = float(np.linalg.norm(edge))
            if length < 1e-12:
                continue
            cand = edge / length
            perp = np.array([-cand[1], cand[0]])
            proj_u = hull @ cand
            proj_v = hull @ perp
            area = float(proj_u.max() - proj_u.min()) * float(proj_v.max() - proj_v.min())
            if best_area is None or area < best_area:
                best_area = area
                best_dir = cand
        direction = best_dir
    u_hat = direction[0] * axis_u + direction[1] * axis_v
    u_hat = u_hat / np.linalg.norm(u_hat)
    v_hat = np.cross(normal, u_hat)
    v_hat = v_hat / np.linalg.norm(v_hat)
    rotation = np.column_stack((u_hat, v_hat, normal))
    local = rel @ rotation
    lows = local.min(axis=0)
    highs = local.max(axis=0)
    extent = np.maximum(highs - lows, 0.0)
    center = origin + ((lows + highs) / 2.0) @ rotation.T
    return o3d.geometry.OrientedBoundingBox(center, rotation, extent)


def tighten_box(box, points: np.ndarray):
    """Keep the fitted rotation; set center and extent from the points.

    Open3D's robust hull can inflate a flat cloud. The replacement box
    is the axis-aligned box of the points in that same rotation, so it
    still contains every point.
    """
    import open3d as o3d

    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] == 0:
        return box
    rotation = np.asarray(box.R, dtype=float).reshape(3, 3)
    center = np.asarray(box.center, dtype=float).reshape(3)
    local = (pts - center) @ rotation
    lows = local.min(axis=0)
    highs = local.max(axis=0)
    extent = np.maximum(highs - lows, 0.0)
    mid = (lows + highs) / 2.0
    new_center = mid @ rotation.T + center
    return o3d.geometry.OrientedBoundingBox(new_center, rotation, extent)


def face_coverage(points: np.ndarray, rotation: np.ndarray, center: np.ndarray) -> float:
    """Share of the in-plane bounding rectangle that contains an inlier.

    Cell size follows the in-plane neighbour spacing, so a filled floor
    scores high and a few coplanar stud faces score low.
    """
    import open3d as o3d

    pts = np.asarray(points, dtype=float)
    if pts.shape[0] < 8:
        return 0.0
    local = (pts - np.asarray(center, dtype=float).reshape(3)) @ np.asarray(
        rotation, dtype=float
    ).reshape(3, 3)
    ranges = local.max(axis=0) - local.min(axis=0)
    axes = np.argsort(ranges)[-2:]
    uv = local[:, axes]
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(
        np.column_stack((uv, np.zeros(uv.shape[0], dtype=float)))
    )
    tree = o3d.geometry.KDTreeFlann(cloud)
    sample_n = min(300, uv.shape[0])
    sample = np.linspace(0, uv.shape[0] - 1, sample_n, dtype=int)
    dists = []
    for index in sample:
        _count, _idx, dist2 = tree.search_knn_vector_3d(cloud.points[int(index)], 2)
        if len(dist2) > 1 and dist2[1] > 0:
            dists.append(float(np.sqrt(dist2[1])))
    spacing = float(np.median(dists)) if dists else 0.0
    span_u = float(uv[:, 0].max() - uv[:, 0].min())
    span_v = float(uv[:, 1].max() - uv[:, 1].min())
    cell = max(spacing * 2.0, span_u / 400.0, span_v / 400.0, 1e-9)
    nu = max(int(np.ceil(span_u / cell)), 1)
    nv = max(int(np.ceil(span_v / cell)), 1)
    u0 = float(uv[:, 0].min())
    v0 = float(uv[:, 1].min())
    iu = np.clip(np.floor((uv[:, 0] - u0) / cell).astype(np.int64), 0, nu - 1)
    iv = np.clip(np.floor((uv[:, 1] - v0) / cell).astype(np.int64), 0, nv - 1)
    occupied = np.unique(iu * np.int64(nv) + iv).size
    return float(occupied) / float(nu * nv)


def plane_is_large(extent, *, thin_ratio: float, min_extent: float, min_span: float) -> bool:
    sides = np.sort(np.asarray(extent, dtype=float).reshape(3))
    small, mid, long = (float(sides[0]), float(sides[1]), float(sides[2]))
    if long < min_extent or mid < min_span or mid <= 1e-9:
        return False
    return (small / mid) <= thin_ratio


def fit_bbox(pcd):
    """PCA oriented box, then robust PCA, then axis-aligned.

    Returns (box, kind) with kind in {obb, obb_robust, aabb}, or None.
    """
    import open3d as o3d

    n_points = len(pcd.points)
    if n_points == 0:
        return None
    if n_points >= 4:
        for robust, kind in ((False, "obb"), (True, "obb_robust")):
            try:
                with quiet_c_stderr():
                    box = pcd.get_oriented_bounding_box(robust=robust)
                return box, kind
            except RuntimeError:
                continue
    aabb = pcd.get_axis_aligned_bounding_box()
    box = o3d.geometry.OrientedBoundingBox.create_from_axis_aligned_bounding_box(aabb)
    return box, "aabb"


def colors_or_none(pcd) -> np.ndarray | None:
    if not pcd.has_colors():
        return None
    cols = np.asarray(pcd.colors)
    n_points = len(pcd.points)
    if cols.ndim != 2 or cols.shape != (n_points, 3):
        return None
    finite = cols[np.isfinite(cols)]
    if finite.size == 0 or float(np.max(finite)) <= 1e-8:
        return None
    return cols


def component_record(
    cid: int,
    source: str,
    n_points: int,
    box,
    kind: str,
    up: np.ndarray,
    args: argparse.Namespace,
    *,
    force_label: str | None = None,
    plane_model=None,
) -> dict:
    extent = np.asarray(box.extent, dtype=float).reshape(3)
    rotation = np.asarray(box.R, dtype=float).reshape(3, 3)
    center = np.asarray(box.center, dtype=float).reshape(3)
    label, align = classify_box(
        extent,
        rotation,
        up,
        thin_ratio=args.thin_ratio,
        elongation=args.elongation,
        vertical_cos=args.vertical_cos,
        horizontal_cos=args.horizontal_cos,
        blob_ratio=args.blob_ratio,
    )
    if force_label is not None:
        label = force_label
    record = {
        "id": cid,
        "label": label,
        "source": source,
        "n_points": int(n_points),
        "extents_units": extent.tolist(),
        "volume": float(box.volume()),
        "center": center.tolist(),
        "R": rotation.tolist(),
        "bbox_kind": kind,
        "long_axis_abs_cos_up": align,
    }
    if plane_model is not None:
        record["plane_model_abcd"] = np.asarray(plane_model, dtype=float).reshape(-1).tolist()
    return record


def load_cloud(path: Path):
    import open3d as o3d

    if not path.is_file():
        print(
            "\n".join(
                [
                    f"Input point cloud was not found: {path}",
                    "",
                    "The default file is data/raw/darus-intcdc/preview.ply.",
                    "That path is gitignored. It exists only on a machine that",
                    "downloaded the DaRUS preview. Pass --input with the PLY path,",
                    "or run from a checkout where the default file is present.",
                ]
            ),
            file=sys.stderr,
        )
        return None
    try:
        cloud = o3d.io.read_point_cloud(
            str(path),
            remove_nan_points=True,
            remove_infinite_points=True,
            print_progress=False,
        )
    except Exception as exc:  # Open3D raises a few exception types on bad files
        print(f"Could not read {path}: {exc}", file=sys.stderr)
        return None
    if cloud.is_empty():
        print(f"Loaded 0 points from {path}", file=sys.stderr)
        return None
    return cloud


def downsample_and_clean(cloud, args: argparse.Namespace):
    down = cloud.voxel_down_sample(args.voxel_size)
    n_down = len(down.points)
    if n_down == 0:
        return down, down, "Voxel downsample kept 0 points."
    inlier, _indices = down.remove_statistical_outlier(
        nb_neighbors=min(args.sor_neighbors, max(n_down - 1, 1)),
        std_ratio=args.sor_std_ratio,
        print_progress=False,
    )
    note = ""
    if len(inlier.points) == 0:
        note = "Statistical outlier removal kept 0 points."
    return down, inlier, note


def peel_large_planes(inlier, args: argparse.Namespace, up: np.ndarray):
    """Tag and remove large thin planes. Return components and a boolean mask."""
    n_points = len(inlier.points)
    alive = np.ones(n_points, dtype=bool)
    components: list[dict] = []
    if args.max_planes == 0 or n_points < args.ransac_n:
        return components, alive
    if args.plane_min_points > 0:
        min_points = args.plane_min_points
    else:
        min_points = max(100, int(round(args.plane_min_fraction * n_points)))
    next_id = 0
    for _ in range(args.max_planes):
        alive_idx = np.flatnonzero(alive)
        if alive_idx.size < args.ransac_n:
            break
        subset = inlier.select_by_index(alive_idx.tolist())
        try:
            model, inliers = subset.segment_plane(
                distance_threshold=args.plane_distance,
                ransac_n=args.ransac_n,
                num_iterations=args.plane_iterations,
            )
        except RuntimeError:
            break
        local = np.asarray(inliers, dtype=np.int64)
        if local.size < min_points:
            break
        chosen = alive_idx[local]
        piece = inlier.select_by_index(chosen.tolist())
        piece_points = np.asarray(piece.points)
        box = plane_aligned_box(piece_points, model)
        kind = "plane_obb"
        if box is None:
            fitted = fit_bbox(piece)
            if fitted is None:
                break
            box, kind = fitted
            box = tighten_box(box, piece_points)
        if not plane_is_large(
            box.extent,
            thin_ratio=args.thin_ratio,
            min_extent=args.plane_min_extent,
            min_span=args.plane_min_span,
        ):
            break
        coverage = face_coverage(piece_points, box.R, box.center)
        if coverage < args.plane_min_coverage:
            break
        record = component_record(
            next_id,
            "plane",
            int(chosen.size),
            box,
            kind,
            up,
            args,
            force_label="planar",
            plane_model=model,
        )
        record["plane_coverage"] = coverage
        record["_indices"] = chosen
        components.append(record)
        alive[chosen] = False
        next_id += 1
    return components, alive


def cluster_remaining(inlier, alive: np.ndarray, args: argparse.Namespace, up: np.ndarray, next_id: int):
    alive_idx = np.flatnonzero(alive)
    kept: list[dict] = []
    n_dropped = 0
    n_dropped_points = 0
    n_noise = 0
    if alive_idx.size == 0:
        return kept, n_dropped, n_dropped_points, n_noise
    subset = inlier.select_by_index(alive_idx.tolist())
    labels = np.asarray(
        subset.cluster_dbscan(
            eps=args.dbscan_eps,
            min_points=args.dbscan_min_points,
            print_progress=False,
        )
    )
    if labels.shape[0] != alive_idx.shape[0]:
        raise RuntimeError("cluster_dbscan returned a label array of unexpected length")
    n_noise = int(np.count_nonzero(labels < 0))
    cluster_ids = sorted(int(v) for v in np.unique(labels) if int(v) >= 0)
    for lab in cluster_ids:
        local = np.flatnonzero(labels == lab)
        chosen = alive_idx[local]
        if chosen.size < args.min_cluster_size:
            n_dropped += 1
            n_dropped_points += int(chosen.size)
            continue
        piece = inlier.select_by_index(chosen.tolist())
        fitted = fit_bbox(piece)
        if fitted is None:
            n_dropped += 1
            n_dropped_points += int(chosen.size)
            continue
        box, kind = fitted
        box = tighten_box(box, np.asarray(piece.points))
        record = component_record(next_id, "dbscan", int(chosen.size), box, kind, up, args)
        record["_indices"] = chosen
        kept.append(record)
        next_id += 1
    return kept, n_dropped, n_dropped_points, n_noise


def view_axes(up: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Screen X and screen Y, in world coordinates, for four orthographic views.

    With ``up`` = +Z the views are: front drops Y, side drops X, top drops Z,
    iso looks from the +horiz/+other/+up corner.
    """
    vertical = np.asarray(up, dtype=float)
    vertical = vertical / np.linalg.norm(vertical)
    helper = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(helper, vertical))) > 0.85:
        helper = np.array([0.0, 1.0, 0.0])
    horiz = helper - vertical * float(np.dot(helper, vertical))
    horiz = horiz / np.linalg.norm(horiz)
    other = np.cross(vertical, horiz)
    other = other / np.linalg.norm(other)
    look = horiz + other + vertical
    look = look / np.linalg.norm(look)
    iso_y = vertical - look * float(np.dot(vertical, look))
    iso_y = iso_y / np.linalg.norm(iso_y)
    iso_x = np.cross(look, iso_y)
    iso_x = iso_x / np.linalg.norm(iso_x)
    return {
        "front": (horiz, vertical),
        "side": (other, vertical),
        "top": (horiz, other),
        "iso": (iso_x, iso_y),
    }


def project(points: np.ndarray, screen_x: np.ndarray, screen_y: np.ndarray) -> np.ndarray:
    return np.column_stack((points @ screen_x, points @ screen_y))


def write_views(
    out_dir: Path,
    points: np.ndarray,
    colors: np.ndarray | None,
    components: list[dict],
    up: np.ndarray,
    up_token: str,
    rng: np.random.Generator,
    plot_max_points: int,
    empty_note: str,
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D

    views = out_dir / "views"
    views.mkdir(parents=True, exist_ok=True)
    n_points = int(points.shape[0])
    if n_points > plot_max_points:
        chosen = rng.choice(n_points, size=plot_max_points, replace=False)
        plot_points = points[chosen]
        plot_colors = None if colors is None else colors[chosen]
    else:
        plot_points = points
        plot_colors = colors
    shown = int(plot_points.shape[0])
    if plot_colors is None:
        point_color = TIMBER_RGB
        color_note = "points: timber-brown (RGB missing or all zero)"
    else:
        point_color = np.clip(plot_colors, 0.0, 1.0)
        color_note = "points: source RGB"
    marker = 4.0 if shown < 4000 else (1.4 if shown < 30000 else 0.35)
    alpha = 0.85 if shown < 4000 else 0.45
    frames = view_axes(up)
    present = [label for label in LABELS if any(c["label"] == label for c in components)]
    written: list[Path] = []
    for name in VIEW_NAMES:
        screen_x, screen_y = frames[name]
        fig, ax = plt.subplots(figsize=(7.6, 7.2), dpi=140)
        fig.patch.set_facecolor("#f6f3ec")
        ax.set_facecolor("#f7f4ee")
        if shown:
            projected = project(plot_points, screen_x, screen_y)
            scatter_kw = dict(
                s=marker,
                linewidths=0,
                alpha=alpha,
                rasterized=True,
                zorder=1,
            )
            if plot_colors is None:
                ax.scatter(
                    projected[:, 0],
                    projected[:, 1],
                    color=tuple(float(v) for v in TIMBER_RGB),
                    **scatter_kw,
                )
            else:
                ax.scatter(
                    projected[:, 0],
                    projected[:, 1],
                    c=point_color,
                    **scatter_kw,
                )
        segments = []
        segment_colors = []
        projected_corners = []
        for comp in components:
            corners = box_corners(comp["center"], comp["R"], comp["extents_units"])
            flat = project(corners, screen_x, screen_y)
            projected_corners.append(flat)
            rgb = LABEL_RGB[comp["label"]]
            for i, j in _BOX_EDGES:
                segments.append((flat[i], flat[j]))
                segment_colors.append(rgb)
        if segments:
            ax.add_collection(
                LineCollection(
                    segments,
                    colors=segment_colors,
                    linewidths=1.35,
                    zorder=3,
                )
            )
        xs = np.empty(0)
        ys = np.empty(0)
        if shown:
            base = project(plot_points, screen_x, screen_y)
            xs = base[:, 0]
            ys = base[:, 1]
        if projected_corners:
            stacked = np.vstack(projected_corners)
            xs = stacked[:, 0] if xs.size == 0 else np.concatenate((xs, stacked[:, 0]))
            ys = stacked[:, 1] if ys.size == 0 else np.concatenate((ys, stacked[:, 1]))
        if xs.size:
            pad_x = 0.04 * (float(xs.max() - xs.min()) + 1e-6)
            pad_y = 0.04 * (float(ys.max() - ys.min()) + 1e-6)
            ax.set_xlim(float(xs.min()) - pad_x, float(xs.max()) + pad_x)
            ax.set_ylim(float(ys.min()) - pad_y, float(ys.max()) + pad_y)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e4ddd0", linewidth=0.4)
        ax.tick_params(labelsize=8, colors="#5c5346")
        for spine in ax.spines.values():
            spine.set_color("#d9d2c5")
        ax.set_xlabel("file units", fontsize=8, color="#5c5346")
        ax.set_ylabel("file units", fontsize=8, color="#5c5346")
        title = f"{name}  ·  {shown} points shown  ·  {len(components)} boxes"
        if empty_note:
            title = f"{name}  ·  {empty_note}"
        ax.set_title(title, fontsize=11, color="#2c2822", pad=8)
        if present:
            handles = [
                Line2D([0], [0], color=LABEL_RGB[label], lw=2.0, label=label)
                for label in present
            ]
            ax.legend(
                handles=handles,
                loc="upper right",
                frameon=True,
                fontsize=8,
                title="heuristic",
            )
        fig.text(
            0.01,
            0.01,
            f"up={up_token}   {color_note}   boxes: OBB wireframe",
            fontsize=8,
            color="#5c5346",
        )
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        path = views / f"{name}.png"
        fig.savefig(path, dpi=140)
        plt.close(fig)
        written.append(path)
    return written


def _fmt(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return f"{value:.4g}"


def summarize_extents(components: list[dict]) -> dict:
    if not components:
        return {}
    stacked = np.sort(np.array([c["extents_units"] for c in components], dtype=float), axis=1)
    longs = stacked[:, 2]
    summary = {}
    for name, column in (("short", stacked[:, 0]), ("mid", stacked[:, 1]), ("long", longs)):
        summary[name] = {
            "min": float(np.min(column)),
            "median": float(np.median(column)),
            "max": float(np.max(column)),
        }
    return summary


def histogram_lines(values: list[float], bins: int = 6) -> list[str]:
    if not values:
        return ["No kept components, so there is no extent histogram."]
    array = np.asarray(values, dtype=float)
    vmin = float(array.min())
    vmax = float(array.max())
    if vmax <= vmin:
        return [f"All longest extents are {_fmt(vmin)} (n={array.size})."]
    counts, edges = np.histogram(array, bins=np.linspace(vmin, vmax, bins + 1))
    lines = [
        "| bin (longest extent, file units) | count |",
        "| --- | ---: |",
    ]
    for i, count in enumerate(counts):
        end = "]" if i == len(counts) - 1 else ")"
        lines.append(
            f"| [{_fmt(float(edges[i]))}, {_fmt(float(edges[i + 1]))}{end} | {int(count)} |"
        )
    return lines


def write_report(
    path: Path,
    *,
    args: argparse.Namespace,
    up_token: str,
    raw_extent: np.ndarray,
    n_raw: int,
    n_down: int,
    n_inlier: int,
    clean_note: str,
    components: list[dict],
    n_dropped: int,
    n_dropped_points: int,
    n_noise: int,
    plane_min_points: int,
) -> None:
    public = [{k: v for k, v in c.items() if k != "_indices"} for c in components]
    by_label = {label: 0 for label in LABELS}
    points_by_label = {label: 0 for label in LABELS}
    bbox_kinds = {"obb": 0, "obb_robust": 0, "aabb": 0}
    for comp in public:
        by_label[comp["label"]] = by_label.get(comp["label"], 0) + 1
        points_by_label[comp["label"]] = points_by_label.get(comp["label"], 0) + comp["n_points"]
        bbox_kinds[comp["bbox_kind"]] = bbox_kinds.get(comp["bbox_kind"], 0) + 1
    n_planes = sum(1 for c in public if c["source"] == "plane")
    n_kept = sum(1 for c in public if c["source"] == "dbscan")
    extent_summary = summarize_extents(public)
    longest = [float(np.max(c["extents_units"])) for c in public]
    raw_max = float(np.max(raw_extent)) if raw_extent.size else 0.0
    scale_note = (
        "Defaults for voxel size, DBSCAN eps, and the large-plane size cuts "
        "were chosen for coordinates on the order of a building in meters. "
        f"This file's axis-aligned size is [{_fmt(float(raw_extent[0]))}, "
        f"{_fmt(float(raw_extent[1]))}, {_fmt(float(raw_extent[2]))}]. "
        "If that size is far from a few metres, retune those arguments. "
        "The script does not convert units."
    )
    lines = [
        "# Classical segmentation report",
        "",
        "Heuristic boxes from Open3D 0.20. These labels are not a stud schedule",
        "and this file does not state a measured accuracy.",
        "",
        "## Gravity and units",
        "",
        f"Up axis used for the labels: `{up_token}` = "
        f"[{args.up[0]:.6g}, {args.up[1]:.6g}, {args.up[2]:.6g}].",
        "",
        "The DaRUS IntCDC record (Leica ScanStation P20, timber buildings) does",
        "not state that the stored Z axis is gravity. When the input is that",
        "preview, `upright` and `beam_like` mean parallel or perpendicular to the",
        "axis you passed, which may not be plumb. A floor plane is not a gravity",
        "vector. The ~0.12° plumb check from `docs/tolerances.md` is a later step",
        "and is not computed here.",
        "",
        "Extents are in the PLY coordinate units (`extents_units`). They are not",
        "rescaled to metres.",
        "",
        scale_note,
        "",
        "## Pipeline",
        "",
        "1. Voxel downsample, then statistical outlier removal.",
        "2. Repeated `segment_plane`. A plane is tagged `planar` and removed only",
        "   when it is large, thin, and its inliers fill their rectangle.",
        "   The loop stops at the first plane that fails, so a stud face or a",
        "   set of separated coplanar faces stays in the cloud. Open3D has no",
        "   region growing.",
        "   `detect_planar_patches` is not used, because it returns a box per face.",
        "3. `cluster_dbscan` on the points that remain. `-1` is noise.",
        "4. PCA oriented box per kept cluster (`get_oriented_bounding_box`).",
        "   Flat clusters retry with `robust=True`, then an axis-aligned box.",
        "   Peeled planes are a minimum-area rectangle in the RANSAC plane",
        "   (`bbox_kind` `plane_obb`), because the robust hull inflates a flat patch.",
        "5. Label from extent ratios and the up axis. A dense slab can still be",
        "   peeled. Members that touch can still become one DBSCAN cluster.",
        "",
        f"`--seed {args.seed}` seeds the PNG subsample only. `segment_plane` in",
        "Open3D 0.20 has no seed argument.",
        "",
        "## Counts",
        "",
        f"- Raw points: {n_raw}",
        f"- After voxel downsample: {n_down}",
        f"- After outlier removal: {n_inlier}",
        f"- Large planes tagged: {n_planes}",
        f"- DBSCAN clusters kept: {n_kept}",
        f"- DBSCAN clusters dropped (under min size or no box): {n_dropped} "
        f"({n_dropped_points} points)",
        f"- DBSCAN noise points: {n_noise}",
        f"- Components written: {len(public)}",
        "",
    ]
    if clean_note:
        lines.extend([clean_note, ""])
    if n_inlier and n_noise > 0.5 * max(n_inlier - sum(c["n_points"] for c in public if c["source"] == "plane"), 1):
        lines.extend(
            [
                "More than half of the points sent to DBSCAN were noise.",
                "If members look shattered, raise `--dbscan-eps` (and maybe `--voxel-size`).",
                "",
            ]
        )
    lines.extend(
        [
            "| label | components | points |",
            "| --- | ---: | ---: |",
        ]
    )
    for label in LABELS:
        lines.append(f"| {label} | {by_label[label]} | {points_by_label[label]} |")
    lines.extend(
        [
            "",
            "| box fit | count |",
            "| --- | ---: |",
            f"| obb (PCA) | {bbox_kinds.get('obb', 0)} |",
            f"| obb_robust | {bbox_kinds.get('obb_robust', 0)} |",
            f"| plane_obb (RANSAC normal, minimum-area rectangle) | {bbox_kinds.get('plane_obb', 0)} |",
            f"| aabb fallback | {bbox_kinds.get('aabb', 0)} |",
            "",
            f"Plane inlier gate: {plane_min_points} points, longest side ≥ "
            f"{_fmt(args.plane_min_extent)}, middle side ≥ {_fmt(args.plane_min_span)}, "
            f"thin ratio ≤ {_fmt(args.thin_ratio)}, "
            f"rectangle coverage ≥ {_fmt(args.plane_min_coverage)}.",
            f"DBSCAN eps={_fmt(args.dbscan_eps)}, min_points={args.dbscan_min_points}, "
            f"min cluster size={args.min_cluster_size}.",
            "",
            "## Extent summary",
            "",
            "Sides are sorted per box into short, mid, and long. Values are file units.",
            "",
        ]
    )
    if not extent_summary:
        lines.append("No kept components.")
    else:
        lines.extend(
            [
                "| | short | mid | long |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for stat in ("min", "median", "max"):
            lines.append(
                "| {stat} | {s} | {m} | {l} |".format(
                    stat=stat,
                    s=_fmt(extent_summary["short"][stat]),
                    m=_fmt(extent_summary["mid"][stat]),
                    l=_fmt(extent_summary["long"][stat]),
                )
            )
        lines.extend(["", "### Longest-side histogram", ""])
        lines.extend(histogram_lines(longest))
        lines.extend(["", "### Per label (longest side)", ""])
        lines.extend(
            [
                "| label | n | min | median | max |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for label in LABELS:
            group = [float(np.max(c["extents_units"])) for c in public if c["label"] == label]
            if not group:
                lines.append(f"| {label} | 0 | — | — | — |")
                continue
            arr = np.asarray(group, dtype=float)
            lines.append(
                f"| {label} | {arr.size} | {_fmt(float(arr.min()))} | "
                f"{_fmt(float(np.median(arr)))} | {_fmt(float(arr.max()))} |"
            )
    lines.extend(
        [
            "",
            "## Parameters",
            "",
            "```",
            " ".join(sys.argv),
            "```",
            "",
            f"- voxel size: {args.voxel_size}",
            f"- outlier neighbors / std ratio: {args.sor_neighbors} / {args.sor_std_ratio}",
            f"- plane distance: {args.plane_distance}",
            f"- plane iterations / ransac n / max planes: "
            f"{args.plane_iterations} / {args.ransac_n} / {args.max_planes}",
            f"- elongation / vertical cos / horizontal cos / blob ratio: "
            f"{args.elongation} / {args.vertical_cos} / {args.horizontal_cos} / {args.blob_ratio}",
            "",
            "Label rules, in order: thin third side → `planar`; one dominant side",
            "nearly parallel to up → `upright`; one dominant side nearly",
            "perpendicular to up → `beam_like`; three similar sides → `blob`;",
            "otherwise `clutter`.",
            "",
        ]
    )
    if raw_max > 500 or (raw_max > 0 and raw_max < 0.2):
        lines.extend(
            [
                "## Scale warning",
                "",
                "The raw axis-aligned longest side is outside the range these",
                "defaults were written for. Read the size above and retune",
                "`--voxel-size`, `--dbscan-eps`, `--plane-distance`,",
                "`--plane-min-extent`, and `--plane-min-span` before using the labels.",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_labeled_ply(path: Path, inlier, components: list[dict]) -> None:
    import open3d as o3d

    n_points = len(inlier.points)
    colors = np.tile(UNASSIGNED_RGB, (n_points, 1))
    for comp in components:
        colors[comp["_indices"]] = LABEL_RGB[comp["label"]]
    labeled = o3d.geometry.PointCloud()
    labeled.points = inlier.points
    labeled.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_point_cloud(str(path), labeled, write_ascii=False, print_progress=False)


def run(args: argparse.Namespace, up_token: str) -> int:
    import open3d as o3d

    o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)
    if args.plane_distance is None:
        args.plane_distance = max(0.03, 1.5 * args.voxel_size)
    cloud = load_cloud(args.input)
    if cloud is None:
        return 2
    n_raw = len(cloud.points)
    raw_extent = np.asarray(cloud.get_axis_aligned_bounding_box().get_extent(), dtype=float)
    print(
        f"loaded {n_raw} points  aabb extent "
        f"[{raw_extent[0]:.4g}, {raw_extent[1]:.4g}, {raw_extent[2]:.4g}]"
    )
    down, inlier, clean_note = downsample_and_clean(cloud, args)
    n_down = len(down.points)
    n_inlier = len(inlier.points)
    print(f"downsampled {n_down}  inliers {n_inlier}")
    if clean_note:
        print(clean_note)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    up = np.asarray(args.up, dtype=float)
    components: list[dict] = []
    n_dropped = 0
    n_dropped_points = 0
    n_noise = 0
    plot_points = np.asarray(inlier.points) if n_inlier else np.zeros((0, 3))
    plot_colors = colors_or_none(inlier) if n_inlier else None
    empty_note = clean_note
    if n_inlier:
        planes, alive = peel_large_planes(inlier, args, up)
        clustered, n_dropped, n_dropped_points, n_noise = cluster_remaining(
            inlier, alive, args, up, next_id=len(planes)
        )
        components = planes + clustered
        print(
            f"planes {len(planes)}  clusters kept {len(clustered)}  "
            f"dropped {n_dropped}  noise {n_noise}"
        )
    if args.plane_min_points > 0:
        plane_min_points = args.plane_min_points
    else:
        plane_min_points = max(100, int(round(args.plane_min_fraction * max(n_inlier, 0))))
    public = []
    for comp in components:
        public.append({k: v for k, v in comp.items() if k != "_indices"})
    by_label = {label: sum(1 for c in public if c["label"] == label) for label in LABELS}
    payload = {
        "schema": "openwall.classical_seg.components.v1",
        "semantic_note": (
            "Heuristic labels from oriented-box extent ratios and the supplied "
            "up axis. Not a trained model and not a measured accuracy."
        ),
        "input": str(args.input),
        "extent_unit": "file_units",
        "units_note": (
            "extents_units are the Open3D box side lengths in the PLY coordinate "
            "units, in the same order as the columns of R. This file does not "
            "claim metres."
        ),
        "up": up.tolist(),
        "up_token": up_token,
        "up_assumption": (
            "Default up is +Z. That is an assumption you can override with --up. "
            "DaRUS IntCDC is not documented as gravity-aligned."
        ),
        "n_points_raw": n_raw,
        "n_points_down": n_down,
        "n_points_inlier": n_inlier,
        "counts": {
            "by_label": by_label,
            "planes_tagged": sum(1 for c in public if c["source"] == "plane"),
            "dbscan_clusters_kept": sum(1 for c in public if c["source"] == "dbscan"),
            "dbscan_clusters_dropped": n_dropped,
            "dbscan_points_dropped": n_dropped_points,
            "noise_points": n_noise,
        },
        "params": {
            "voxel_size": args.voxel_size,
            "sor_neighbors": args.sor_neighbors,
            "sor_std_ratio": args.sor_std_ratio,
            "max_planes": args.max_planes,
            "plane_distance": args.plane_distance,
            "plane_iterations": args.plane_iterations,
            "ransac_n": args.ransac_n,
            "plane_min_points_effective": plane_min_points,
            "plane_min_fraction": args.plane_min_fraction,
            "plane_min_extent": args.plane_min_extent,
            "plane_min_span": args.plane_min_span,
            "plane_min_coverage": args.plane_min_coverage,
            "thin_ratio": args.thin_ratio,
            "dbscan_eps": args.dbscan_eps,
            "dbscan_min_points": args.dbscan_min_points,
            "min_cluster_size": args.min_cluster_size,
            "elongation": args.elongation,
            "vertical_cos": args.vertical_cos,
            "horizontal_cos": args.horizontal_cos,
            "blob_ratio": args.blob_ratio,
            "seed": args.seed,
        },
        "components": public,
    }
    json_path = args.out_dir / "components.json"
    json_path.write_text(
        json.dumps(to_jsonable(payload), indent=2) + "\n",
        encoding="utf-8",
    )
    report_path = args.out_dir / "report.md"
    write_report(
        report_path,
        args=args,
        up_token=up_token,
        raw_extent=raw_extent,
        n_raw=n_raw,
        n_down=n_down,
        n_inlier=n_inlier,
        clean_note=clean_note,
        components=components,
        n_dropped=n_dropped,
        n_dropped_points=n_dropped_points,
        n_noise=n_noise,
        plane_min_points=plane_min_points,
    )
    rng = np.random.default_rng(args.seed)
    view_paths = write_views(
        args.out_dir,
        plot_points,
        plot_colors,
        public,
        up,
        up_token,
        rng,
        args.plot_max_points,
        empty_note,
    )
    if args.save_colored_ply and n_inlier:
        ply_path = args.out_dir / "labeled.ply"
        write_labeled_ply(ply_path, inlier, components)
        print(f"wrote {ply_path}")
    print(f"wrote {json_path}")
    print(f"wrote {report_path}")
    for view_path in view_paths:
        print(f"wrote {view_path}")
    print(
        "labels "
        + "  ".join(f"{label}={by_label[label]}" for label in LABELS)
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    error = validate_args(args)
    if error:
        print(error, file=sys.stderr)
        return 2
    # Preserve the token the user typed. argparse has already replaced --up.
    up_token = "z"
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--up" in raw:
        idx = raw.index("--up")
        if idx + 1 < len(raw):
            up_token = raw[idx + 1]
    try:
        return run(args, up_token)
    except ImportError as exc:
        print(
            f"Missing dependency ({exc}). From the repo root: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
