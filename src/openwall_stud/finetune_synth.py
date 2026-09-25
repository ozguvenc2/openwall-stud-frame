"""Synthetic stud/clutter clouds for the rank 4 and rank 5 fine-tune.

Labels are pointwise. ``stud`` is generator part 2. Everything else (the
stage-2 floor) is ``clutter``. Plates are not a class in this pass.

The 25 phase-1 S1 cards (seed 2, 1 mm noise, 5 mm spacing, the locked lean
ladder) are not in train or val. Val still uses that ladder's magnitudes,
with a different seed and a different noise.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.synthetic import (
    LEAN_AXES,
    Scene,
    phase1_s1_single_stud,
    stage0_single_stud,
    stage2_stud_and_floor,
)

CLUTTER = 0
STUD = 1
CLASS_NAMES = ("clutter", "stud")

PHASE1_MAGNITUDES = (0.0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0)
PHASE1_SEED = 2
PHASE1_NOISE_M = 0.001
PHASE1_SPACING_M = 0.005

TRAIN_MAGNITUDES = (
    0.02, 0.08, 0.10, 0.18, 0.22, 0.40, 0.55, 0.65, 0.75, 0.90,
    1.20, 1.60, 2.00, 2.40, 3.00, 3.50, 4.50, 5.50, 7.00,
    0.05, 0.12, 0.15, 0.30, 1.00, 4.00,
)
FLOOR_MAGNITUDES = (0.05, 0.15, 0.40, 0.65, 1.00, 1.60, 2.40, 4.00, 5.50, 7.00)
NOISES_M = (0.0005, 0.0010, 0.0015, 0.0020)
SPACING_M = 0.005
FLOOR_SPACING_M = 0.015

# Minimum stud-labeled points before a minimal OBB is fit.
STUD_MIN_POINTS = 50


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest_path() -> Path:
    return repo_root() / "data" / "finetune" / "synthetic_stud_manifest.json"


def cache_dir() -> Path:
    return repo_root() / "data" / "cache" / "finetune-synth"


def _spec(
    *,
    split: str,
    kind: str,
    lean_deg: float,
    axis: str,
    seed: int,
    noise_std_m: float,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "split": split,
        "kind": kind,
        "lean_deg": float(lean_deg),
        "axis": axis,
        "seed": int(seed),
        "noise_std_m": float(noise_std_m),
        "spacing_m": SPACING_M,
        "nominal": "2x4",
    }
    if kind == "stud_floor":
        row["floor_spacing_m"] = FLOOR_SPACING_M
    return row


def _is_phase1_card(spec: dict[str, Any]) -> bool:
    if spec["kind"] != "stud":
        return False
    if int(spec["seed"]) != PHASE1_SEED:
        return False
    if abs(float(spec["noise_std_m"]) - PHASE1_NOISE_M) > 1e-12:
        return False
    if abs(float(spec["spacing_m"]) - PHASE1_SPACING_M) > 1e-12:
        return False
    lean = float(spec["lean_deg"])
    axis = spec["axis"]
    if lean == 0.0:
        return axis == "none"
    return any(abs(lean - mag) < 1e-12 for mag in PHASE1_MAGNITUDES if mag != 0.0) and axis in LEAN_AXES


def build_manifest() -> dict[str, Any]:
    """Deterministic train and val lists. Ids are assigned after the loops."""
    train: list[dict[str, Any]] = []
    for seed in (11, 17, 41):
        for axis in LEAN_AXES:
            for magnitude in TRAIN_MAGNITUDES:
                train.append(
                    _spec(
                        split="train",
                        kind="stud",
                        lean_deg=magnitude,
                        axis=axis,
                        seed=seed,
                        noise_std_m=0.0,
                    )
                )
    for seed in (11, 17, 41, 53):
        train.append(
            _spec(
                split="train",
                kind="stud",
                lean_deg=0.0,
                axis="none",
                seed=seed,
                noise_std_m=0.0,
            )
        )
    for seed in (23, 29):
        for axis in LEAN_AXES:
            for magnitude in FLOOR_MAGNITUDES:
                train.append(
                    _spec(
                        split="train",
                        kind="stud_floor",
                        lean_deg=magnitude,
                        axis=axis,
                        seed=seed,
                        noise_std_m=0.0,
                    )
                )
        train.append(
            _spec(
                split="train",
                kind="stud_floor",
                lean_deg=0.0,
                axis="+X",
                seed=seed,
                noise_std_m=0.0,
            )
        )

    val: list[dict[str, Any]] = []
    val.append(
        _spec(
            split="val",
            kind="stud",
            lean_deg=0.0,
            axis="none",
            seed=9001,
            noise_std_m=0.0015,
        )
    )
    for magnitude in PHASE1_MAGNITUDES:
        if magnitude == 0.0:
            continue
        for axis in LEAN_AXES:
            val.append(
                _spec(
                    split="val",
                    kind="stud",
                    lean_deg=magnitude,
                    axis=axis,
                    seed=9001,
                    noise_std_m=0.0015,
                )
            )
    for lean_deg, axis in (
        (0.0, "+X"),
        (0.15, "+X"),
        (0.15, "+Y"),
        (0.30, "-X"),
        (1.0, "-X"),
        (1.0, "-Y"),
        (4.0, "+X"),
        (4.0, "+Y"),
    ):
        val.append(
            _spec(
                split="val",
                kind="stud_floor",
                lean_deg=lean_deg,
                axis=axis,
                seed=9101,
                noise_std_m=0.0015,
            )
        )

    for index, spec in enumerate(train):
        spec["id"] = f"train_{index:04d}"
        spec["noise_std_m"] = float(NOISES_M[index % len(NOISES_M)])
    for index, spec in enumerate(val):
        spec["id"] = f"val_{index:04d}"

    for spec in train + val:
        if _is_phase1_card(spec):
            raise RuntimeError(f"{spec['id']} matches a phase-1 S1 card")

    val_leans = {round(float(spec["lean_deg"]), 3) for spec in val if spec["kind"] == "stud"}
    missing = [mag for mag in PHASE1_MAGNITUDES if round(mag, 3) not in val_leans]
    if missing:
        raise RuntimeError(f"val stud set is missing phase-1 magnitudes {missing}")
    if len([spec for spec in val if spec["kind"] == "stud"]) != 25:
        raise RuntimeError("val stud ladder is not 25 clouds")

    return {
        "schema": "openwall.synthetic_stud_finetune.v1",
        "classes": list(CLASS_NAMES),
        "label_ids": {"clutter": CLUTTER, "stud": STUD},
        "part_stud": 2,
        "excluded_phase1": {
            "seed": PHASE1_SEED,
            "noise_std_m": PHASE1_NOISE_M,
            "spacing_m": PHASE1_SPACING_M,
            "magnitudes_deg": list(PHASE1_MAGNITUDES),
            "note": "Those 25 clouds are the inference set. They are not in train or val.",
        },
        "train": train,
        "val": val,
        "counts": {
            "train": len(train),
            "train_stud": sum(1 for spec in train if spec["kind"] == "stud"),
            "train_stud_floor": sum(1 for spec in train if spec["kind"] == "stud_floor"),
            "val": len(val),
            "val_stud": sum(1 for spec in val if spec["kind"] == "stud"),
            "val_stud_floor": sum(1 for spec in val if spec["kind"] == "stud_floor"),
        },
    }


def write_manifest(path: Path | None = None) -> Path:
    dest = path or manifest_path()
    payload = build_manifest()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    dest = path or manifest_path()
    return json.loads(dest.read_text(encoding="utf-8"))


def materialize(spec: dict[str, Any]) -> Scene:
    """Build one cloud from the existing generator. Does not write a file."""
    kind = spec["kind"]
    lean = float(spec["lean_deg"])
    axis = str(spec["axis"])
    seed = int(spec["seed"])
    noise = float(spec["noise_std_m"])
    spacing = float(spec["spacing_m"])
    if kind == "stud":
        if axis == "none" or lean == 0.0:
            return phase1_s1_single_stud(
                lean_deg=0.0 if axis == "none" else lean,
                axis="none" if lean == 0.0 else axis,
                seed=seed,
                spacing_m=spacing,
                noise_std_m=noise,
                nominal="2x4",
            )
        return stage0_single_stud(
            nominal="2x4",
            lean_deg=lean,
            seed=seed,
            spacing_m=spacing,
            noise_std_m=noise,
            lean_axis=axis,
        )
    if kind == "stud_floor":
        return stage2_stud_and_floor(
            nominal="2x4",
            lean_deg=lean,
            seed=seed,
            spacing_m=spacing,
            floor_spacing_m=float(spec.get("floor_spacing_m", FLOOR_SPACING_M)),
            noise_std_m=noise,
            lean_axis="+X" if lean == 0.0 else axis,
        )
    raise ValueError(f"unknown kind {kind!r}")


def point_labels(scene: Scene) -> np.ndarray:
    """Map generator parts onto clutter=0 and stud=1."""
    labels = np.full(scene.n_points, CLUTTER, dtype=np.int64)
    labels[np.asarray(scene.part) == 2] = STUD
    return labels


def estimate_normals(points: np.ndarray) -> np.ndarray:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    cloud.estimate_normals()
    return np.asarray(cloud.normals, dtype=np.float32)


def cloud_path(spec_id: str) -> Path:
    return cache_dir() / f"{spec_id}.npz"


def ensure_cloud(spec: dict[str, Any]) -> dict[str, np.ndarray]:
    """Load a cached cloud, or generate, label, and cache it.

    The cache lives under ``data/cache/`` and is gitignored.
    """
    path = cloud_path(spec["id"])
    if path.is_file():
        with np.load(path) as blob:
            return {
                "points": np.asarray(blob["points"], dtype=np.float32),
                "labels": np.asarray(blob["labels"], dtype=np.int64),
                "normals": np.asarray(blob["normals"], dtype=np.float32),
            }
    scene = materialize(spec)
    points = np.asarray(scene.points_m, dtype=np.float32)
    labels = point_labels(scene)
    normals = estimate_normals(points)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, points=points, labels=labels.astype(np.int16), normals=normals)
    return {"points": points, "labels": labels, "normals": normals}


def iter_split(manifest: dict[str, Any], split: str, *, repeat_floor: int = 1) -> list[dict[str, Any]]:
    rows = list(manifest[split])
    if split != "train" or repeat_floor <= 1:
        return rows
    expanded: list[dict[str, Any]] = []
    for spec in rows:
        copies = repeat_floor if spec["kind"] == "stud_floor" else 1
        expanded.extend(spec for _ in range(copies))
    return expanded
