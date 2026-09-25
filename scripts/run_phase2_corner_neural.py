"""Neural passes on the synthetic phase-2 corner.

Stacks
    control_pointcept   BIMStruct3D office vocabulary. No wall_a / wall_b.
    control_randlanet   S3DIS office vocabulary. No wall_a / wall_b.
    finetune_pointcept  Existing stud/clutter head. The corner has no stud.
    finetune_randlanet  Existing stud/clutter head. The corner has no stud.
    corner_pointcept    3-class head trained on other corner seeds, if present.

Office stacks are scored by fitting planes to the predicted wall class.
They are not scored as wall_a versus wall_b. The stud heads are scored as
a false-stud count: ground truth has zero stud points. ε stays unlocked.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.phase2_corner import (  # noqa: E402
    CLASS_NAMES,
    FLOOR,
    WALL_A,
    WALL_B,
    lean_from_vertical_deg,
    svd_plane,
)
from openwall_stud.synthetic import Scene  # noqa: E402

OUT = ROOT / "artifacts" / "scorecards" / "phase2_corner_neural"
NPZ = ROOT / "artifacts" / "phase2_corner_synth" / "corner_skil_means.npz"
GT = ROOT / "artifacts" / "phase2_corner_synth" / "corner_skil_means.json"
CORNER_WEIGHT = ROOT / "artifacts" / "weights" / "finetune" / "pointcept_corner_3class.pth"


def load_cloud() -> tuple[np.ndarray, np.ndarray, dict]:
    blob = np.load(NPZ)
    points = np.asarray(blob["points"], dtype=np.float64)
    labels = np.asarray(blob["labels"], dtype=np.int64)
    gt = json.loads(GT.read_text(encoding="utf-8"))
    return points, labels, gt


def as_scene(points: np.ndarray, seed: int) -> Scene:
    n = len(points)
    return Scene(
        name="phase2_corner_skil_means",
        stage=2,
        points_m=points,
        part=np.zeros(n, dtype=np.int64),
        stud_slot=np.full(n, -1, dtype=np.int64),
        studs=[],
        seed=seed,
        spacing_m=0.005,
        noise_std_m=0.002,
        description="Synthetic outside corner. Not a stud.",
    )


def histogram(labels: np.ndarray, names: list[str]) -> list[dict]:
    rows = []
    for index, name in enumerate(names):
        rows.append({"id": index, "name": name, "count": int(np.sum(labels == index))})
    return rows


def class_scores(pred: np.ndarray, gt_labels: np.ndarray, names: tuple[str, ...] = CLASS_NAMES) -> dict:
    rows = {}
    for index, name in enumerate(names):
        tp = int(np.sum((pred == index) & (gt_labels == index)))
        fp = int(np.sum((pred == index) & (gt_labels != index)))
        fn = int(np.sum((pred != index) & (gt_labels == index)))
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        iou = tp / (tp + fp + fn) if (tp + fp + fn) else None
        rows[name] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "iou": iou,
        }
    return rows


def plane_of(points: np.ndarray, mask: np.ndarray) -> dict | None:
    if int(mask.sum()) < 500:
        return None
    normal, rmse = svd_plane(points[mask])
    return {
        "points": int(mask.sum()),
        "lean_from_vertical_deg": lean_from_vertical_deg(normal),
        "rmse_mm": rmse * 1000.0,
        "normal_xyz": [float(x) for x in normal],
        "vertical": abs(float(normal[2])) <= 0.34,
    }


def match_leans(measured: list[float], planted: list[float]) -> dict:
    order_m = np.argsort(measured)
    order_p = np.argsort(planted)
    deltas = [abs(measured[int(i)] - planted[int(j)]) for i, j in zip(order_m, order_p)]
    return {
        "measured_deg": measured,
        "planted_deg": planted,
        "sorted_abs_delta_deg": deltas,
        "pairing": "sorted by lean magnitude, not a registered face id",
    }


def _normal_angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    aa = aa / np.linalg.norm(aa)
    bb = bb / np.linalg.norm(bb)
    return float(np.degrees(np.arccos(np.clip(abs(float(np.dot(aa, bb))), 0.0, 1.0))))


def score_named_faces(points: np.ndarray, pred: np.ndarray, gt: dict) -> dict:
    planes = {
        "wall_a": plane_of(points, pred == WALL_A),
        "wall_b": plane_of(points, pred == WALL_B),
        "floor": plane_of(points, pred == FLOOR),
    }
    planted_lean = {
        "wall_a": gt["planted"]["wall_a_lean_deg"],
        "wall_b": gt["planted"]["wall_b_lean_deg"],
    }
    planted_normal = {
        "wall_a": np.array(gt["planted"]["normal_a_xyz"], dtype=np.float64),
        "wall_b": np.array(gt["planted"]["normal_b_xyz"], dtype=np.float64),
    }
    detected = {}
    for name in ("wall_a", "wall_b"):
        plane = planes[name]
        if plane is None or not plane["vertical"]:
            detected[name] = False
            continue
        err = abs(plane["lean_from_vertical_deg"] - planted_lean[name])
        normal_err = _normal_angle_deg(plane["normal_xyz"], planted_normal[name])
        plane["abs_error_vs_planted_deg"] = err
        plane["normal_angle_vs_planted_deg"] = normal_err
        # A blended pair of perpendicular walls can sit near one lean number
        # and still point between the two faces. Require the normal as well.
        detected[name] = bool(err <= 0.5 and normal_err <= 20.0 and plane["rmse_mm"] <= 15.0)
    return {
        "planes": planes,
        "face_detected": detected,
        "bring_up_bar": "lean within 0.5°, normal within 20°, RMSE within 15 mm",
        "bring_up_bar_note": "Synthetic check only. Not τ, not ε, not a paint call.",
    }


def wall_class_ids(names: list[str]) -> list[int]:
    return [i for i, name in enumerate(names) if name.lower() == "wall"]


def two_planes_from_mask(points: np.ndarray, mask: np.ndarray) -> list[dict]:
    """Open3D RANSAC, two vertical planes, on one semantic class."""
    import open3d as o3d

    xyz = np.asarray(points[mask], dtype=np.float64)
    if len(xyz) < 2000:
        return []
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(xyz)
    cloud = cloud.voxel_down_sample(0.01)
    found = []
    remaining = cloud
    for _ in range(4):
        if len(remaining.points) < 800:
            break
        model, inliers = remaining.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1500)
        if len(inliers) < 800:
            break
        normal = np.array(model[:3], dtype=np.float64)
        normal = normal / np.linalg.norm(normal)
        sel = np.abs(xyz @ normal + float(model[3])) <= 0.01
        if int(sel.sum()) < 500:
            remaining = remaining.select_by_index(inliers, invert=True)
            continue
        fitted, rmse = svd_plane(xyz[sel])
        if abs(float(fitted[2])) <= 0.34:
            found.append(
                {
                    "points": int(sel.sum()),
                    "lean_from_vertical_deg": lean_from_vertical_deg(fitted),
                    "rmse_mm": rmse * 1000.0,
                }
            )
        remaining = remaining.select_by_index(inliers, invert=True)
        if len(found) == 2:
            break
    found.sort(key=lambda row: row["points"], reverse=True)
    return found[:2]


def run_control_pointcept(points: np.ndarray, gt_labels: np.ndarray, gt: dict) -> dict:
    from openwall_stud.contenders.pointcept_ptv3 import _cache_root, _forward

    started = time.perf_counter()
    result = _forward(as_scene(points, int(gt["seed"])), _cache_root(), "cuda")
    names = result["names"]
    labels = np.asarray(result["labels"])
    walls = wall_class_ids(names)
    wall_mask = np.isin(labels, walls) if walls else np.zeros(len(points), dtype=bool)
    planes = two_planes_from_mask(points, wall_mask)
    planted = [gt["planted"]["wall_a_lean_deg"], gt["planted"]["wall_b_lean_deg"]]
    card = {
        "stack": "control_pointcept",
        "role": "office vocabulary control",
        "vocabulary": names,
        "wall_class_ids": walls,
        "histogram": result["histogram"],
        "runtime_s": result["runtime_s"],
        "wall_clock_s": round(time.perf_counter() - started, 3),
        "recovered_vertical_planes": planes,
        "two_faces": len(planes) == 2,
        "lean_vs_planted": match_leans([p["lean_from_vertical_deg"] for p in planes], planted) if len(planes) == 2 else None,
        "named_face_iou": None,
        "note": "BIMStruct3D has one wall class, not wall_a and wall_b. Two planes are a split of that class. Not a stud score.",
    }
    return card


def run_control_randlanet(points: np.ndarray, gt_labels: np.ndarray, gt: dict) -> dict:
    from openwall_stud.contenders.common import gpu_probe
    from openwall_stud.contenders.open3d_ml_s3dis import _forward, _weight_path

    started = time.perf_counter()
    result = _forward(as_scene(points, int(gt["seed"])), _weight_path(), gpu_probe())
    names = result["names"]
    labels = np.asarray(result["labels"])
    if labels.shape[0] != len(points):
        raise RuntimeError(f"S3DIS labels {labels.shape[0]} != points {len(points)}")
    walls = wall_class_ids(names)
    wall_mask = np.isin(labels, walls) if walls else np.zeros(len(points), dtype=bool)
    planes = two_planes_from_mask(points, wall_mask)
    planted = [gt["planted"]["wall_a_lean_deg"], gt["planted"]["wall_b_lean_deg"]]
    return {
        "stack": "control_randlanet",
        "role": "office vocabulary control",
        "vocabulary": names,
        "wall_class_ids": walls,
        "histogram": result["histogram"],
        "runtime_s": result["runtime_s"],
        "wall_clock_s": round(time.perf_counter() - started, 3),
        "recovered_vertical_planes": planes,
        "two_faces": len(planes) == 2,
        "lean_vs_planted": match_leans([p["lean_from_vertical_deg"] for p in planes], planted) if len(planes) == 2 else None,
        "named_face_iou": None,
        "note": "S3DIS has one wall class, not wall_a and wall_b. RGB channels were zeros. Not a stud score.",
    }


def _normals(points: np.ndarray) -> np.ndarray:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cloud.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=24))
    return np.asarray(cloud.normals, dtype=np.float32)


def run_finetune_pointcept(points: np.ndarray, gt_labels: np.ndarray, gt: dict) -> dict:
    from openwall_stud.finetune_pointcept import build_model, load_bimstruct_backbone, load_finetuned, predict_full, weight_path

    started = time.perf_counter()
    model = build_model("cuda")
    backbone = load_bimstruct_backbone(model)
    meta = load_finetuned(model, weight_path())
    pred = predict_full(model, points, _normals(points))
    n_stud = int(np.sum(pred == 1))
    return {
        "stack": "finetune_pointcept",
        "role": "existing stud/clutter head on a stud-free corner",
        "vocabulary": ["clutter", "stud"],
        "histogram": histogram(pred, ["clutter", "stud"]),
        "stud_points": n_stud,
        "stud_fraction": n_stud / len(points),
        "gt_stud_points": 0,
        "false_stud_points": n_stud,
        "backbone_copied": backbone.get("copied"),
        "checkpoint_meta_epoch": meta.get("epoch") if isinstance(meta, dict) else None,
        "runtime_s": round(time.perf_counter() - started, 3),
        "named_face_iou": None,
        "two_faces": False,
        "note": "This head cannot name wall_a, wall_b, or floor. Every stud label is false. No stud box is fit.",
    }


def run_finetune_randlanet(points: np.ndarray, gt_labels: np.ndarray, gt: dict) -> dict:
    from openwall_stud.finetune_randlanet import build_model, load_checkpoint, predict_labels, weight_path

    started = time.perf_counter()
    model = build_model("cuda")
    load_checkpoint(model, weight_path())
    pred, infer_s = predict_labels(model, points.astype(np.float32))
    n_stud = int(np.sum(pred == 1))
    return {
        "stack": "finetune_randlanet",
        "role": "existing stud/clutter head on a stud-free corner",
        "vocabulary": ["clutter", "stud"],
        "histogram": histogram(pred, ["clutter", "stud"]),
        "stud_points": n_stud,
        "stud_fraction": n_stud / len(points),
        "gt_stud_points": 0,
        "false_stud_points": n_stud,
        "inference_s": infer_s,
        "runtime_s": round(time.perf_counter() - started, 3),
        "named_face_iou": None,
        "two_faces": False,
        "note": "This head cannot name wall_a, wall_b, or floor. predict_labels uses per-cloud batch-norm stats. Every stud label is false.",
    }


def run_corner_pointcept(points: np.ndarray, gt_labels: np.ndarray, gt: dict) -> dict:
    import openwall_stud.finetune_pointcept as fp

    fp.NUM_CLASSES = 3
    from openwall_stud.finetune_pointcept import build_model, load_bimstruct_backbone, load_finetuned, predict_full

    started = time.perf_counter()
    model = build_model("cuda")
    load_bimstruct_backbone(model)
    meta = load_finetuned(model, CORNER_WEIGHT)
    pred = predict_full(model, points, _normals(points))
    faces = score_named_faces(points, pred, gt)
    detected = faces["face_detected"]
    return {
        "stack": "corner_pointcept",
        "role": "3-class corner head, canonical scene held out of that train",
        "vocabulary": list(CLASS_NAMES),
        "histogram": histogram(pred, list(CLASS_NAMES)),
        "class_scores": class_scores(pred, gt_labels),
        "faces": faces,
        "two_faces": bool(detected.get("wall_a")) and bool(detected.get("wall_b")),
        "checkpoint": str(CORNER_WEIGHT),
        "checkpoint_meta": meta if isinstance(meta, dict) else {},
        "runtime_s": round(time.perf_counter() - started, 3),
        "production_paint": "yellow",
        "epsilon_locked": False,
        "note": "Labels are floor, wall_a, wall_b. Not studs. A face flag also requires the normal and a 15 mm RMSE, so a blended plane cannot pass on lean alone.",
    }


RUNNERS = {
    "control_pointcept": run_control_pointcept,
    "control_randlanet": run_control_randlanet,
    "finetune_pointcept": run_finetune_pointcept,
    "finetune_randlanet": run_finetune_randlanet,
    "corner_pointcept": run_corner_pointcept,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", required=True, choices=sorted(RUNNERS))
    args = parser.parse_args()
    if args.stack == "corner_pointcept" and not CORNER_WEIGHT.is_file():
        raise SystemExit(f"missing {CORNER_WEIGHT}")
    points, labels, gt = load_cloud()
    card = RUNNERS[args.stack](points, labels, gt)
    card["scene"] = gt["name"]
    card["n_points"] = int(len(points))
    card["class_F"] = False
    card["stud_detection"] = "not_claimed"
    card["production_paint"] = "yellow"
    card["epsilon_locked"] = False
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.stack}.json"
    path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: card[k] for k in card if k not in {"histogram", "checkpoint_meta"}}, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
