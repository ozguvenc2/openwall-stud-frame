"""Synthetic residential outside corner for phase 2.

Two painted-wall planes meet on a vertical edge. An optional floor patch
sits at z = 0. Labels are floor, wall_a, and wall_b. There is no stud class
and no stud box. Planted leans are the SKIL face means from the 2026-09-25
painted-corner session unless the caller overrides them.

Export +Z is the vertical. Lean of a plane is asin(|n · +Z|) in degrees.
A floor is not the plumb reference.
"""

from __future__ import annotations

from typing import Any

import numpy as np

FLOOR = 0
WALL_A = 1
WALL_B = 2
CLASS_NAMES = ("floor", "wall_a", "wall_b")

# SKIL face means, 2026-09-25. Lean from plumb = |90 - display|.
SKIL_FACE_A_MEAN_DEG = 0.3833333333333333
SKIL_FACE_B_MEAN_DEG = 0.25


def lean_from_vertical_deg(normal: np.ndarray) -> float:
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return float(np.degrees(np.arcsin(np.clip(abs(float(n[2])), 0.0, 1.0))))


def svd_plane(points: np.ndarray) -> tuple[np.ndarray, float]:
    center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - center, full_matrices=False)
    normal = vh[-1]
    normal = normal / np.linalg.norm(normal)
    if normal[2] < 0:
        normal = -normal
    rmse = float(np.sqrt(np.mean(np.square((points - center) @ normal))))
    return normal, rmse


def _rot_x(deg: float) -> np.ndarray:
    a = np.deg2rad(deg)
    c, s = float(np.cos(a)), float(np.sin(a))
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float64)


def _rot_y(deg: float) -> np.ndarray:
    a = np.deg2rad(deg)
    c, s = float(np.cos(a)), float(np.sin(a))
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float64)


def _grid(axis_u: np.ndarray, axis_v: np.ndarray, spacing: float) -> np.ndarray:
    len_u = float(np.linalg.norm(axis_u))
    len_v = float(np.linalg.norm(axis_v))
    nu = max(2, int(round(len_u / spacing)) + 1)
    nv = max(2, int(round(len_v / spacing)) + 1)
    u = np.linspace(0.0, 1.0, nu)
    v = np.linspace(0.0, 1.0, nv)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    return (uu[..., None] * axis_u + vv[..., None] * axis_v).reshape(-1, 3)


def synthesize_corner(
    *,
    lean_a_deg: float = SKIL_FACE_A_MEAN_DEG,
    lean_b_deg: float = SKIL_FACE_B_MEAN_DEG,
    width_m: float = 0.80,
    height_m: float = 2.40,
    spacing_m: float = 0.005,
    floor_spacing_m: float = 0.010,
    noise_std_m: float = 0.002,
    seed: int = 25,
    include_floor: bool = True,
    name: str = "phase2_corner_skil_means",
) -> dict[str, Any]:
    """Outside corner. Wall A is the YZ face, rotated about Y. Wall B is XZ, about X.

    Both rotations leave the +Z edge fixed, so the faces still meet. Small
    leans keep the dihedral near 90°.
    """
    wall_a = _grid(
        np.array([0.0, width_m, 0.0]),
        np.array([0.0, 0.0, height_m]),
        spacing_m,
    )
    wall_b = _grid(
        np.array([width_m, 0.0, 0.0]),
        np.array([0.0, 0.0, height_m]),
        spacing_m,
    )
    rot_a = _rot_y(lean_a_deg)
    rot_b = _rot_x(lean_b_deg)
    wall_a = wall_a @ rot_a.T
    wall_b = wall_b @ rot_b.T
    normal_a = rot_a @ np.array([1.0, 0.0, 0.0])
    normal_b = rot_b @ np.array([0.0, 1.0, 0.0])
    parts = [wall_a, wall_b]
    labels = [
        np.full(len(wall_a), WALL_A, dtype=np.int64),
        np.full(len(wall_b), WALL_B, dtype=np.int64),
    ]
    if include_floor:
        floor = _grid(
            np.array([width_m, 0.0, 0.0]),
            np.array([0.0, width_m, 0.0]),
            floor_spacing_m,
        )
        parts.append(floor)
        labels.append(np.full(len(floor), FLOOR, dtype=np.int64))
    points = np.vstack(parts)
    label = np.concatenate(labels)
    rng = np.random.default_rng(seed)
    if noise_std_m > 0:
        points = points + rng.normal(0.0, noise_std_m, size=points.shape)
    points = np.asarray(points, dtype=np.float64)

    dot = float(np.clip(abs(np.dot(normal_a, normal_b)), 0.0, 1.0))
    dihedral = float(np.degrees(np.arccos(dot)))
    fitted = {}
    for class_id, key in ((WALL_A, "wall_a"), (WALL_B, "wall_b"), (FLOOR, "floor")):
        mask = label == class_id
        if int(mask.sum()) < 20:
            continue
        normal, rmse = svd_plane(points[mask])
        fitted[key] = {
            "points": int(mask.sum()),
            "lean_from_vertical_deg": lean_from_vertical_deg(normal),
            "rmse_mm": rmse * 1000.0,
            "normal_xyz": [float(x) for x in normal],
        }

    return {
        "name": name,
        "points": points,
        "labels": label,
        "class_names": list(CLASS_NAMES),
        "label_ids": {"floor": FLOOR, "wall_a": WALL_A, "wall_b": WALL_B},
        "not_studs": True,
        "seed": int(seed),
        "spacing_m": float(spacing_m),
        "floor_spacing_m": float(floor_spacing_m),
        "noise_std_m": float(noise_std_m),
        "width_m": float(width_m),
        "height_m": float(height_m),
        "include_floor": bool(include_floor),
        "planted": {
            "wall_a_lean_deg": float(lean_a_deg),
            "wall_b_lean_deg": float(lean_b_deg),
            "wall_a_rotation": "right-hand about +Y, YZ face",
            "wall_b_rotation": "right-hand about +X, XZ face",
            "normal_a_xyz": [float(x) for x in normal_a],
            "normal_b_xyz": [float(x) for x in normal_b],
            "dihedral_deg": dihedral,
            "vertical": "export_+Z",
            "source": "SKIL face means 2026-09-25 unless overridden",
        },
        "svd_on_noisy_labels": fitted,
    }


def train_variants(n: int = 8, seed0: int = 101) -> list[dict[str, Any]]:
    """Small corner set for a short head fine-tune. The canonical scene is not here."""
    noises = (0.001, 0.002, 0.003, 0.005)
    specs = []
    for i in range(n):
        specs.append(
            {
                "name": f"phase2_corner_train_{i:02d}",
                "seed": seed0 + i,
                "noise_std_m": noises[i % len(noises)],
                "lean_a_deg": SKIL_FACE_A_MEAN_DEG + (0.05 if i % 2 == 0 else -0.04),
                "lean_b_deg": SKIL_FACE_B_MEAN_DEG + (0.04 if i % 3 == 0 else -0.03),
            }
        )
    return specs
