"""Phase-2 painted wall-corner plumb pilot.

Fits two dominant vertical planes (and a floor plane when one is present)
on the gitignored Polycam WallCorner cloud, measures lean from the export
vertical, and compares those leans to the SKIL face means. Also records
nearest-neighbor spacing for the Lot62 loft ladder.

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


def lean_from_vertical_deg(normal: np.ndarray) -> float:
    n = normal / np.linalg.norm(normal)
    return float(np.degrees(np.arcsin(np.clip(abs(float(np.dot(n, UP))), 0.0, 1.0))))


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


def height_bins(points: np.ndarray, mask: np.ndarray, normal: np.ndarray) -> list[dict]:
    z = points[mask, 2]
    if len(z) < 300:
        return []
    edges = np.quantile(z, [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0])
    labels = ["bottom", "mid", "top"]
    # Bottom is the low-Z third. Export Z is up on the loft clouds and is
    # the long axis of this corner.
    rows = []
    xyz = points[mask]
    for i, label in enumerate(labels):
        band = (xyz[:, 2] >= edges[i]) & (xyz[:, 2] <= edges[i + 1] if i == 2 else xyz[:, 2] < edges[i + 1])
        if int(band.sum()) < 200:
            continue
        n, center, rmse = svd_plane(xyz[band])
        if float(np.dot(n, normal)) < 0:
            n = -n
        rows.append(
            {
                "height": label,
                "z_lo_m": float(edges[i]),
                "z_hi_m": float(edges[i + 1]),
                "points": int(band.sum()),
                "lean_from_vertical_deg": lean_from_vertical_deg(n),
                "rmse_mm": rmse * 1000.0,
            }
        )
    return rows


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

    floor = horizontals[0] if horizontals else None
    for i, wall in enumerate(walls):
        wall["face_slot"] = f"plane_{i + 1}"
        wall["height_bins"] = height_bins(corner, wall["mask"], wall["normal"])
        wall["skil_face"] = None  # not registered to Face A or Face B

    skil_means = {}
    for key, face in SKIL["faces"].items():
        leans = [r["lean_deg"] for r in face["readings"]]
        skil_means[key] = float(np.mean(leans))

    # Unpaired comparison. Sorting both lists does not identify a face.
    cloud_leans = sorted(w["lean_from_vertical_deg"] for w in walls)
    skil_sorted = sorted(skil_means.values())
    sorted_abs_delta = [abs(c - s) for c, s in zip(cloud_leans, skil_sorted)]

    labels = np.full(len(corner), -1, dtype=np.int32)
    for i, wall in enumerate(walls):
        labels[wall["mask"]] = i
    if floor is not None:
        labels[floor["mask"]] = 2

    summary_planes = []
    for wall in walls:
        summary_planes.append(
            {
                "slot": wall["face_slot"],
                "kind": "vertical_wall",
                "inliers": wall["inliers"],
                "lean_from_vertical_deg": wall["lean_from_vertical_deg"],
                "rmse_mm": wall["rmse_mm"],
                "normal_xyz": [float(x) for x in wall["normal"]],
                "center_xyz_m": [float(x) for x in wall["center"]],
                "z_min_m": wall["z_min_m"],
                "z_max_m": wall["z_max_m"],
                "height_bins": wall["height_bins"],
                "skil_face_id": None,
                "lean_vs_floor_normal_deg": None,
            }
        )
    floor_summary = None
    if floor is not None:
        floor_summary = {
            "slot": "floor",
            "kind": "horizontal_floor_candidate",
            "inliers": floor["inliers"],
            "lean_from_vertical_deg": floor["lean_from_vertical_deg"],
            "tilt_from_horizontal_deg": float(90.0 - floor["lean_from_vertical_deg"]),
            "rmse_mm": floor["rmse_mm"],
            "normal_xyz": [float(x) for x in floor["normal"]],
            "center_xyz_m": [float(x) for x in floor["center"]],
            "z_min_m": floor["z_min_m"],
            "z_max_m": floor["z_max_m"],
            "note": "Optional. A floor normal is not the plumb reference for this pilot. Export +Z is the vertical used for wall lean. Lean versus this normal is a sensitivity only.",
        }
        floor_up = np.array(floor_summary["normal_xyz"], dtype=np.float64)
        floor_up = floor_up / np.linalg.norm(floor_up)
        for wall in summary_planes:
            n = np.array(wall["normal_xyz"], dtype=np.float64)
            n = n / np.linalg.norm(n)
            wall["lean_vs_floor_normal_deg"] = float(
                np.degrees(np.arcsin(np.clip(abs(float(np.dot(n, floor_up))), 0.0, 1.0)))
            )

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
        "vertical_axis": "export_+Z",
        "vertical_axis_note": "Lot62 loft exports sit on Z (floor near z=0, ceiling near 2.45 m). This corner's long axis is the same Z, span about 2.50 m, plan extent under 0.9 m. Wall lean is the angle between the fitted plane and +Z. It is not an IMU pair and it is not a stud-axis angle.",
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
            "voxel_m": VOXEL_M,
            "ransac_distance_m": RANSAC_DIST_M,
            "refit_distance_m": REFIT_DIST_M,
            "ransac_iterations": 2500,
            "refit": "svd_on_full_resolution_inliers",
        },
        "walls": summary_planes,
        "floor": floor_summary,
        "dihedral_between_wall_normals_deg": dihedral,
        "corner_edge_angle_from_plus_z_deg": edge_from_vertical,
        "corner_edge_xyz": [float(x) for x in edge],
        "skil": SKIL,
        "skil_face_mean_lean_deg": skil_means,
        "pairing": {
            "registered": False,
            "reason": "The close cloud is an outside corner patch. It does not contain the doorway or the cat tree, so plane 1 and plane 2 are not assigned to Face A or Face B.",
            "sorted_abs_delta_deg": sorted_abs_delta,
            "sorted_cloud_lean_deg": cloud_leans,
            "sorted_skil_mean_lean_deg": skil_sorted,
        },
        "density_ladder": density_rows,
        "limits": [
            "Painted drywall is not stud wood.",
            "One global plane cannot reproduce three SKIL heights when the face bows.",
            "Export +Z is the vertical used here. It is not a surveyed gravity vector paired to the level.",
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
            ["slot", "kind", "inliers", "lean_from_vertical_deg", "rmse_mm", "nx", "ny", "nz"]
        )
        for wall in summary_planes:
            n = wall["normal_xyz"]
            writer.writerow(
                [
                    wall["slot"],
                    wall["kind"],
                    wall["inliers"],
                    f"{wall['lean_from_vertical_deg']:.6f}",
                    f"{wall['rmse_mm']:.4f}",
                    f"{n[0]:.6f}",
                    f"{n[1]:.6f}",
                    f"{n[2]:.6f}",
                ]
            )
        if floor_summary:
            n = floor_summary["normal_xyz"]
            writer.writerow(
                [
                    "floor",
                    floor_summary["kind"],
                    floor_summary["inliers"],
                    f"{floor_summary['lean_from_vertical_deg']:.6f}",
                    f"{floor_summary['rmse_mm']:.4f}",
                    f"{n[0]:.6f}",
                    f"{n[1]:.6f}",
                    f"{n[2]:.6f}",
                ]
            )

    with (OUT / "skil_vs_cloud.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "height", "display_deg", "lean_from_vertical_deg", "notes"])
        for key, face in SKIL["faces"].items():
            for row in face["readings"]:
                writer.writerow(
                    [
                        f"SKIL Face {key}",
                        row["height"],
                        f"{row['display_deg']:.2f}",
                        f"{row['lean_deg']:.2f}",
                        face["where"],
                    ]
                )
            writer.writerow(
                [
                    f"SKIL Face {key} mean",
                    "mean",
                    "",
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
                    f"{wall['lean_from_vertical_deg']:.6f}",
                    "not registered to a SKIL face",
                ]
            )
            for band in wall["height_bins"]:
                writer.writerow(
                    [
                        wall["slot"],
                        band["height"],
                        "",
                        f"{band['lean_from_vertical_deg']:.6f}",
                        f"z {band['z_lo_m']:.3f} to {band['z_hi_m']:.3f} m",
                    ]
                )

    write_figures(corner, labels, summary_planes, skil_means, dihedral)
    print(json.dumps({k: scorecard[k] for k in ("dihedral_between_wall_normals_deg", "corner_edge_angle_from_plus_z_deg", "runtime_s")}, indent=2))
    for wall in summary_planes:
        print(wall["slot"], "lean", round(wall["lean_from_vertical_deg"], 5), "n", wall["inliers"], "rmse", round(wall["rmse_mm"], 3))
        for band in wall["height_bins"]:
            print(" ", band["height"], round(band["lean_from_vertical_deg"], 5), "n", band["points"])
    if floor_summary:
        print("floor inliers", floor_summary["inliers"], "tilt_from_horizontal", round(floor_summary["tilt_from_horizontal_deg"], 5))


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

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    labels_bar = [
        "SKIL A mean\n0.383°",
        "SKIL B mean\n0.250°",
        f"plane 1\n{walls[0]['lean_from_vertical_deg']:.3f}°",
        f"plane 2\n{walls[1]['lean_from_vertical_deg']:.3f}°",
    ]
    values = [
        skil_means["A"],
        skil_means["B"],
        walls[0]["lean_from_vertical_deg"],
        walls[1]["lean_from_vertical_deg"],
    ]
    bar_colors = ["#1a5276", "#1a5276", "#c0392b", "#2471a3"]
    ax.bar(labels_bar, values, color=bar_colors, width=0.72)
    ax.set_ylabel("Lean from vertical (degrees)")
    ax.set_title("SKIL face means vs cloud planes (faces not registered)")
    ax.axhline(0.1194, color="#b7950b", linestyle="--", linewidth=1, label="τ ≈ 0.119° (not a paint call)")
    ax.legend(frameon=False)
    ax.set_ylim(0, max(values) * 1.25 + 0.05)
    fig.tight_layout()
    fig.savefig(OUT / "skil_vs_cloud_lean.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.2), sharey=True)
    for ax, wall, color in zip(axes, walls, ("#c0392b", "#2471a3")):
        names_h = [b["height"] for b in wall["height_bins"]]
        leans = [b["lean_from_vertical_deg"] for b in wall["height_bins"]]
        ax.bar(names_h, leans, color=color, width=0.7)
        ax.axhline(wall["lean_from_vertical_deg"], color="black", linewidth=0.8, linestyle=":")
        ax.set_title(f"{wall['slot']} by height third")
        ax.set_ylabel("Lean from vertical (degrees)")
        ax.grid(True, axis="y", linewidth=0.3, alpha=0.4)
    fig.suptitle(f"Local plane lean. Dihedral between normals {dihedral:.2f}°", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "height_thirds.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
