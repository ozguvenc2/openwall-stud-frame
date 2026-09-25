"""Synthetic outside wall corner: two planes, optional floor. Not studs.

Gravity is +Z. The interior is the +X/+Y quadrant. Each face is a
zero-thickness exterior plane. Lean is degrees from plumb, positive when
the top of the wall moves away from the interior. Face A (runs along +X,
plumb normal -Y) uses a right-hand rotation about +X. Face B (runs along
+Y, plumb normal -X) uses a right-hand rotation about +Y of the opposite
sign so the top also moves outward.

The planted magnitudes 0.383° and 0.250° are the SKIL Face A / Face B means
from the classical phase-2 note. This generator does not read a level and
it does not load the painted field cloud.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.results_by_day import repo_root

LABEL_FLOOR = 0
LABEL_FACE_A = 1
LABEL_FACE_B = 2
CLASS_NAMES = ("floor", "face_a", "face_b")

# SKIL digital-level means, lean from plumb, classical phase-2 note.
FACE_A_LEAN_DEG = 0.383
FACE_B_LEAN_DEG = 0.250

HEIGHT_M = 2.4384  # 8 ft, so the tip offset is larger than the noise
LENGTH_M = 1.2192  # 4 ft along each face
SPACING_M = 0.005
INTERIOR = np.array([LENGTH_M * 0.5, LENGTH_M * 0.5, HEIGHT_M * 0.5])

MANIFEST_PATH = repo_root() / "data" / "wall-corner" / "manifest.json"
CLOUD_DIR = repo_root() / "data" / "cache" / "wall-corner"


@dataclass(frozen=True)
class CornerCloud:
    name: str
    points_m: np.ndarray
    labels: np.ndarray
    seed: int
    noise_std_m: float
    floor: bool
    face_a_lean_deg: float
    face_b_lean_deg: float
    normal_a: np.ndarray
    normal_b: np.ndarray


def _rot_x(deg: float) -> np.ndarray:
    angle = np.deg2rad(deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    return np.array([[1.0, 0.0, 0.0], [0.0, cosine, -sine], [0.0, sine, cosine]], dtype=float)


def _rot_y(deg: float) -> np.ndarray:
    angle = np.deg2rad(deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    return np.array(
        [[cosine, 0.0, sine], [0.0, 1.0, 0.0], [-sine, 0.0, cosine]],
        dtype=float,
    )


def face_grid(origin: np.ndarray, axis_u: np.ndarray, axis_v: np.ndarray, spacing: float) -> np.ndarray:
    len_u = float(np.linalg.norm(axis_u))
    len_v = float(np.linalg.norm(axis_v))
    nu = max(2, int(round(len_u / spacing)) + 1)
    nv = max(2, int(round(len_v / spacing)) + 1)
    uu, vv = np.meshgrid(np.linspace(0.0, 1.0, nu), np.linspace(0.0, 1.0, nv), indexing="ij")
    return (origin + uu[..., None] * axis_u + vv[..., None] * axis_v).reshape(-1, 3)


def analytical_normals(face_a_lean_deg: float, face_b_lean_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Outward unit normals after the planted rotations."""
    normal_a = _rot_x(face_a_lean_deg) @ np.array([0.0, -1.0, 0.0])
    normal_b = _rot_y(-face_b_lean_deg) @ np.array([-1.0, 0.0, 0.0])
    normal_a = normal_a / np.linalg.norm(normal_a)
    normal_b = normal_b / np.linalg.norm(normal_b)
    return normal_a, normal_b


def make_corner(
    *,
    name: str,
    face_a_lean_deg: float = FACE_A_LEAN_DEG,
    face_b_lean_deg: float = FACE_B_LEAN_DEG,
    spacing_m: float = SPACING_M,
    height_m: float = HEIGHT_M,
    length_m: float = LENGTH_M,
    noise_std_m: float = 0.002,
    seed: int = 23,
    floor: bool = True,
) -> CornerCloud:
    if spacing_m <= 0:
        raise ValueError("spacing_m must be positive")
    if not 0.001 <= noise_std_m <= 0.005 and noise_std_m != 0.0:
        raise ValueError("noise_std_m must be 0 or between 1 mm and 5 mm")

    normal_a, normal_b = analytical_normals(face_a_lean_deg, face_b_lean_deg)
    origin = np.zeros(3)
    face_a = face_grid(
        origin,
        np.array([length_m, 0.0, 0.0]),
        np.array([0.0, 0.0, height_m]),
        spacing_m,
    )
    face_b = face_grid(
        origin,
        np.array([0.0, length_m, 0.0]),
        np.array([0.0, 0.0, height_m]),
        spacing_m,
    )
    face_a = face_a @ _rot_x(face_a_lean_deg).T
    face_b = face_b @ _rot_y(-face_b_lean_deg).T

    parts = [face_a, face_b]
    labels = [
        np.full(face_a.shape[0], LABEL_FACE_A, dtype=np.int64),
        np.full(face_b.shape[0], LABEL_FACE_B, dtype=np.int64),
    ]
    if floor:
        xs = np.arange(spacing_m, length_m + spacing_m * 0.5, spacing_m)
        ys = np.arange(spacing_m, length_m + spacing_m * 0.5, spacing_m)
        xx, yy = np.meshgrid(xs, ys, indexing="ij")
        floor_pts = np.column_stack([xx.ravel(), yy.ravel(), np.zeros(xx.size)])
        parts.append(floor_pts)
        labels.append(np.full(floor_pts.shape[0], LABEL_FLOOR, dtype=np.int64))

    points = np.vstack(parts)
    label = np.concatenate(labels)
    # The two faces share only the origin after the leans. Keep Face A.
    rounded = np.round(points, 5)
    _, keep = np.unique(rounded, axis=0, return_index=True)
    keep.sort()
    points = points[keep]
    label = label[keep]

    if noise_std_m > 0:
        rng = np.random.default_rng(seed)
        points = points + rng.normal(0.0, noise_std_m, size=points.shape)

    return CornerCloud(
        name=name,
        points_m=points.astype(np.float64),
        labels=label.astype(np.int64),
        seed=int(seed),
        noise_std_m=float(noise_std_m),
        floor=bool(floor),
        face_a_lean_deg=float(face_a_lean_deg),
        face_b_lean_deg=float(face_b_lean_deg),
        normal_a=normal_a,
        normal_b=normal_b,
    )


def orient_outward(normal: np.ndarray, point: np.ndarray, interior: np.ndarray = INTERIOR) -> np.ndarray:
    unit = np.asarray(normal, dtype=float)
    unit = unit / np.linalg.norm(unit)
    if float(np.dot(unit, np.asarray(interior, dtype=float) - np.asarray(point, dtype=float))) > 0.0:
        unit = -unit
    return unit


def signed_outward_lean_deg(normal_outward: np.ndarray) -> float:
    """Degrees from plumb. Positive when the outward normal tips downward.

    That sign matches an outward lean (top moves away from the interior)
    for both planted rotations in this generator.
    """
    nz = float(np.clip(normal_outward[2], -1.0, 1.0))
    return float(-np.degrees(np.arcsin(nz)))


def fit_plane(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cloud = np.asarray(points, dtype=float)
    center = cloud.mean(axis=0)
    _, _, vt = np.linalg.svd(cloud - center, full_matrices=False)
    normal = vt[-1]
    normal = normal / np.linalg.norm(normal)
    return center, normal


def plane_lean(points: np.ndarray, interior: np.ndarray = INTERIOR) -> dict[str, float]:
    center, normal = fit_plane(points)
    outward = orient_outward(normal, center, interior)
    return {
        "lean_deg": signed_outward_lean_deg(outward),
        "abs_nz": float(abs(outward[2])),
        "nx": float(outward[0]),
        "ny": float(outward[1]),
        "nz": float(outward[2]),
    }


def angle_between_deg(a: np.ndarray, b: np.ndarray) -> float:
    cosine = float(np.clip(np.dot(a, b), -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def refit_report(cloud: CornerCloud) -> dict[str, Any]:
    face_a = cloud.points_m[cloud.labels == LABEL_FACE_A]
    face_b = cloud.points_m[cloud.labels == LABEL_FACE_B]
    fit_a = plane_lean(face_a)
    fit_b = plane_lean(face_b)
    return {
        "face_a_refit_lean_deg": fit_a["lean_deg"],
        "face_b_refit_lean_deg": fit_b["lean_deg"],
        "face_a_abs_error_deg": abs(fit_a["lean_deg"] - cloud.face_a_lean_deg),
        "face_b_abs_error_deg": abs(fit_b["lean_deg"] - cloud.face_b_lean_deg),
        "corner_angle_deg": angle_between_deg(cloud.normal_a, cloud.normal_b),
        "n_face_a": int(face_a.shape[0]),
        "n_face_b": int(face_b.shape[0]),
        "n_floor": int(np.sum(cloud.labels == LABEL_FLOOR)),
        "n_points": int(cloud.points_m.shape[0]),
    }


def write_ply(path: Path, points: np.ndarray, labels: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    xyz = np.asarray(points, dtype=np.float32)
    lab = np.asarray(labels, dtype=np.uint8)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {xyz.shape[0]}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar label\n"
        "end_header\n"
    ).encode("ascii")
    record = np.empty(
        xyz.shape[0],
        dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("label", "u1")],
    )
    record["x"] = xyz[:, 0]
    record["y"] = xyz[:, 1]
    record["z"] = xyz[:, 2]
    record["label"] = lab
    blob = header + record.tobytes()
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def read_ply(path: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = path.read_bytes()
    marker = b"end_header\n"
    end = raw.find(marker)
    if end < 0:
        raise ValueError(f"{path} has no PLY header")
    header = raw[:end].decode("ascii", errors="replace")
    if "binary_little_endian" not in header or "property uchar label" not in header:
        raise ValueError(f"{path} is not the generator's binary PLY")
    count = 0
    for line in header.splitlines():
        if line.startswith("element vertex"):
            count = int(line.split()[-1])
    body = raw[end + len(marker) :]
    record = np.frombuffer(body, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("label", "u1")], count=count)
    points = np.column_stack([record["x"], record["y"], record["z"]]).astype(np.float64)
    return points, record["label"].astype(np.int64)


def default_scenes() -> list[dict[str, Any]]:
    return [
        {"name": "corner_skil_means_floor_n2", "floor": True, "noise_mm": 2.0, "seed": 23},
        {"name": "corner_skil_means_nofloor_n2", "floor": False, "noise_mm": 2.0, "seed": 23},
        {"name": "corner_skil_means_floor_n1", "floor": True, "noise_mm": 1.0, "seed": 23},
        {"name": "corner_skil_means_floor_n5", "floor": True, "noise_mm": 5.0, "seed": 29},
    ]


def scene_record(cloud: CornerCloud, ply_rel: str, sha256: str) -> dict[str, Any]:
    report = refit_report(cloud)
    return {
        "name": cloud.name,
        "ply": ply_rel,
        "sha256": sha256,
        "floor": cloud.floor,
        "seed": cloud.seed,
        "noise_std_mm": round(cloud.noise_std_m * 1000.0, 3),
        "spacing_mm": SPACING_M * 1000.0,
        "height_m": HEIGHT_M,
        "length_m": LENGTH_M,
        "gt_face_a_lean_deg": cloud.face_a_lean_deg,
        "gt_face_b_lean_deg": cloud.face_b_lean_deg,
        "gt_normal_a": [float(v) for v in cloud.normal_a],
        "gt_normal_b": [float(v) for v in cloud.normal_b],
        "interior_xyz_m": [float(v) for v in INTERIOR],
        **report,
    }


def write_manifest(scenes: list[dict[str, Any]], path: Path = MANIFEST_PATH) -> None:
    payload = {
        "generator": "scripts/gen_wall_corner.py",
        "module": "openwall_stud.wall_corner",
        "what": "synthetic outside wall corner, two planes plus optional floor",
        "not": [
            "not a stud box",
            "not a dressed 2x4",
            "not the painted Polycam field cloud",
            "not a SKIL session; the leans are planted at the recorded means",
        ],
        "gravity": "+Z",
        "interior_quadrant": "+X+Y",
        "labels": {"0": "floor", "1": "face_a", "2": "face_b"},
        "face_a": "exterior plane along +X, outward lean is +rotation about +X",
        "face_b": "exterior plane along +Y, outward lean is -rotation about +Y",
        "planted_face_a_lean_deg": FACE_A_LEAN_DEG,
        "planted_face_b_lean_deg": FACE_B_LEAN_DEG,
        "planted_from": "SKIL Face A mean 0.383 deg and Face B mean 0.250 deg, classical phase-2 note",
        "ply_note": "PLY bytes are gitignored (*.ply and data/cache/). Rebuild with scripts/gen_wall_corner.py.",
        "scenes": scenes,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def histogram(labels: np.ndarray, names: list[str]) -> list[dict[str, Any]]:
    rows = []
    flat = np.asarray(labels).reshape(-1)
    for index, name in enumerate(names):
        rows.append({"id": index, "name": str(name), "count": int(np.sum(flat == index))})
    return rows


def majority_name(pred: np.ndarray, mask: np.ndarray, names: list[str]) -> dict[str, Any]:
    chosen = np.asarray(pred).reshape(-1)[np.asarray(mask).reshape(-1)]
    if chosen.size == 0:
        return {"name": None, "count": 0, "fraction": None}
    ids, counts = np.unique(chosen, return_counts=True)
    best = int(np.argmax(counts))
    class_id = int(ids[best])
    name = names[class_id] if 0 <= class_id < len(names) else str(class_id)
    return {
        "name": name,
        "id": class_id,
        "count": int(counts[best]),
        "fraction": float(counts[best] / chosen.size),
    }


def _ransac_plane(
    points: np.ndarray,
    rng: np.random.Generator,
    *,
    thresh_m: float,
    iters: int,
    min_inliers: int,
) -> dict[str, Any] | None:
    cloud = np.asarray(points, dtype=float)
    count = cloud.shape[0]
    if count < min_inliers:
        return None
    best_count = 0
    best_inl: np.ndarray | None = None
    step = max(1, count // 40000)
    sample = cloud[::step]
    for _ in range(iters):
        ids = rng.choice(count, size=3, replace=False)
        tri = cloud[ids]
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        norm = float(np.linalg.norm(normal))
        if norm < 1e-8:
            continue
        normal = normal / norm
        dist = np.abs((sample - tri[0]) @ normal)
        hits = int(np.sum(dist < thresh_m))
        if hits > best_count:
            best_count = hits
            dist_full = np.abs((cloud - tri[0]) @ normal)
            best_inl = dist_full < thresh_m
    if best_inl is None or int(best_inl.sum()) < min_inliers:
        return None
    center, normal = fit_plane(cloud[best_inl])
    outward = orient_outward(normal, center)
    dist = np.abs((cloud - center) @ outward)
    inliers = dist < thresh_m
    if int(inliers.sum()) < min_inliers:
        return None
    center, normal = fit_plane(cloud[inliers])
    outward = orient_outward(normal, center)
    return {
        "inliers": int(inliers.sum()),
        "mask": inliers,
        "center": center,
        "normal": outward,
        "lean_deg": signed_outward_lean_deg(outward),
        "abs_nz": float(abs(outward[2])),
    }


def recover_faces(
    points: np.ndarray,
    pred: np.ndarray,
    names: list[str],
    gt_labels: np.ndarray,
    gt_normal_a: np.ndarray,
    gt_normal_b: np.ndarray,
    *,
    seed: int,
    gt_lean_a: float,
    gt_lean_b: float,
    wall_names: set[str] | None = None,
) -> dict[str, Any]:
    """Score wall-class points as two planes. Stud labels are not wall faces."""
    pred = np.asarray(pred).reshape(-1)
    gt_labels = np.asarray(gt_labels).reshape(-1)
    names = [str(name) for name in names]
    walls = wall_names if wall_names is not None else {"wall"}
    wall_ids = {index for index, name in enumerate(names) if name.lower() in walls}
    wall_mask = np.isin(pred, list(wall_ids)) if wall_ids else np.zeros(pred.shape[0], dtype=bool)

    parts = {
        "face_a": majority_name(pred, gt_labels == LABEL_FACE_A, names),
        "face_b": majority_name(pred, gt_labels == LABEL_FACE_B, names),
        "floor": majority_name(pred, gt_labels == LABEL_FLOOR, names),
    }
    recall = {}
    for key, class_id in (("face_a", LABEL_FACE_A), ("face_b", LABEL_FACE_B), ("floor", LABEL_FLOOR)):
        mask = gt_labels == class_id
        total = int(mask.sum())
        hit = int(np.sum(wall_mask & mask)) if total else 0
        recall[key] = None if total == 0 else float(hit / total)

    faces: dict[str, Any] = {
        "face_a": {
            "gt_lean_deg": gt_lean_a,
            "detected": False,
            "measured_lean_deg": None,
            "abs_error_deg": None,
            "inliers": 0,
            "normal_dot_gt": None,
        },
        "face_b": {
            "gt_lean_deg": gt_lean_b,
            "detected": False,
            "measured_lean_deg": None,
            "abs_error_deg": None,
            "inliers": 0,
            "normal_dot_gt": None,
        },
    }
    unmatched = []
    if wall_ids and int(wall_mask.sum()) >= 200:
        remaining = points[wall_mask]
        rng = np.random.default_rng(seed)
        gt_normals = {"face_a": np.asarray(gt_normal_a, dtype=float), "face_b": np.asarray(gt_normal_b, dtype=float)}
        used: set[str] = set()
        for _ in range(3):
            found = _ransac_plane(remaining, rng, thresh_m=0.015, iters=60, min_inliers=200)
            if found is None:
                break
            remaining = remaining[~found["mask"]]
            if found["abs_nz"] > 0.34:
                unmatched.append(
                    {
                        "reason": "normal too far from horizontal to be a wall",
                        "lean_deg": found["lean_deg"],
                        "inliers": found["inliers"],
                        "abs_nz": found["abs_nz"],
                    }
                )
                continue
            dots = {name: float(np.dot(found["normal"], vec)) for name, vec in gt_normals.items()}
            ranked = sorted(dots, key=dots.get, reverse=True)
            assigned = False
            for name in ranked:
                if name in used or dots[name] < 0.85:
                    continue
                used.add(name)
                measured = float(found["lean_deg"])
                target = gt_lean_a if name == "face_a" else gt_lean_b
                faces[name] = {
                    "gt_lean_deg": target,
                    "detected": True,
                    "measured_lean_deg": measured,
                    "abs_error_deg": abs(measured - target),
                    "inliers": found["inliers"],
                    "normal_dot_gt": dots[name],
                }
                assigned = True
                break
            if not assigned:
                unmatched.append(
                    {
                        "reason": "vertical plane did not match a free GT face at dot>=0.85",
                        "lean_deg": found["lean_deg"],
                        "inliers": found["inliers"],
                        "dots": dots,
                    }
                )
            if remaining.shape[0] < 200:
                break

    both = bool(faces["face_a"]["detected"] and faces["face_b"]["detected"])
    return _face_payload(walls, wall_ids, wall_mask, parts, recall, faces, both, unmatched)


def score_named_faces(
    points: np.ndarray,
    pred: np.ndarray,
    names: list[str],
    gt_labels: np.ndarray,
    gt_normal_a: np.ndarray,
    gt_normal_b: np.ndarray,
    *,
    gt_lean_a: float,
    gt_lean_b: float,
) -> dict[str, Any]:
    """Score a head whose classes are floor, face_a, and face_b.

    Lean is the plane fit on points predicted as that face. Ground truth
    picks the target angle and the normal check. It does not choose the points.
    """
    pred = np.asarray(pred).reshape(-1)
    gt_labels = np.asarray(gt_labels).reshape(-1)
    names = [str(name) for name in names]
    name_to_id = {name: index for index, name in enumerate(names)}
    parts = {
        "face_a": majority_name(pred, gt_labels == LABEL_FACE_A, names),
        "face_b": majority_name(pred, gt_labels == LABEL_FACE_B, names),
        "floor": majority_name(pred, gt_labels == LABEL_FLOOR, names),
    }
    gt_normals = {
        "face_a": np.asarray(gt_normal_a, dtype=float),
        "face_b": np.asarray(gt_normal_b, dtype=float),
    }
    gt_leans = {"face_a": gt_lean_a, "face_b": gt_lean_b}
    gt_ids = {"face_a": LABEL_FACE_A, "face_b": LABEL_FACE_B, "floor": LABEL_FLOOR}
    recall = {}
    faces: dict[str, Any] = {}
    for name in ("face_a", "face_b"):
        class_id = name_to_id.get(name)
        gt_mask = gt_labels == gt_ids[name]
        pred_mask = pred == class_id if class_id is not None else np.zeros(pred.shape[0], dtype=bool)
        gt_total = int(gt_mask.sum())
        pred_total = int(pred_mask.sum())
        hit = int(np.sum(pred_mask & gt_mask))
        recall[name] = None if gt_total == 0 else float(hit / gt_total)
        entry: dict[str, Any] = {
            "gt_lean_deg": gt_leans[name],
            "detected": False,
            "measured_lean_deg": None,
            "abs_error_deg": None,
            "inliers": pred_total,
            "normal_dot_gt": None,
            "precision": None if pred_total == 0 else float(hit / pred_total),
            "recall": recall[name],
            "svd_lean_deg": None,
            "svd_abs_error_deg": None,
        }
        if class_id is not None and pred_total >= 200:
            # Same 15 mm inlier plane as the control RANSAC. A few points from
            # the other wall would otherwise tilt a least-squares fit.
            chosen = points[pred_mask]
            svd_center, svd_normal = fit_plane(chosen)
            svd_out = orient_outward(svd_normal, svd_center)
            svd_lean = signed_outward_lean_deg(svd_out)
            entry["svd_lean_deg"] = svd_lean
            entry["svd_abs_error_deg"] = abs(svd_lean - gt_leans[name])
            rng = np.random.default_rng(class_id + 17)
            found = _ransac_plane(chosen, rng, thresh_m=0.015, iters=40, min_inliers=200)
            if found is None:
                center, normal = fit_plane(chosen)
                outward = orient_outward(normal, center)
                inliers = pred_total
            else:
                outward = found["normal"]
                inliers = found["inliers"]
            dot = float(np.dot(outward, gt_normals[name]))
            measured = signed_outward_lean_deg(outward)
            entry["inliers"] = inliers
            entry["normal_dot_gt"] = dot
            entry["measured_lean_deg"] = measured
            entry["abs_error_deg"] = abs(measured - gt_leans[name])
            entry["detected"] = bool(dot >= 0.85 and abs(outward[2]) <= 0.34 and inliers >= 200)
        faces[name] = entry
    floor_id = name_to_id.get("floor")
    floor_mask = gt_labels == LABEL_FLOOR
    if floor_id is None or int(floor_mask.sum()) == 0:
        recall["floor"] = None
    else:
        recall["floor"] = float(np.sum((pred == floor_id) & floor_mask) / floor_mask.sum())
    both = bool(faces["face_a"]["detected"] and faces["face_b"]["detected"])
    return _face_payload(
        {"face_a", "face_b"},
        {name_to_id[name] for name in ("face_a", "face_b") if name in name_to_id},
        np.isin(pred, [name_to_id[name] for name in ("face_a", "face_b") if name in name_to_id]),
        parts,
        recall,
        faces,
        both,
        [],
    )


def _face_payload(walls, wall_ids, wall_mask, parts, recall, faces, both, unmatched) -> dict[str, Any]:
    return {
        "wall_class_names": sorted(walls) if wall_ids else [],
        "wall_class_ids": sorted(wall_ids),
        "n_predicted_wall": int(wall_mask.sum()),
        "majority_on_gt": parts,
        "wall_recall_on_gt": recall,
        "faces": faces,
        "both_faces_detected": both,
        "unmatched_planes": unmatched,
        "empty_face_inference": not both,
    }
