"""Synthetic 28-stud rooms for the full-room stud-head train.

Labels stay pointwise. Stud is generator part 2. Floor and plates are
clutter. Experiment 1's one-stud manifest and its checkpoints are a
different recipe and are not read or written here.

Held-out seeds 1301–1310 are reserved for lettered scenes. They are not
in this manifest. ``stage5_room_bay`` seed 62 is not in this manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.finetune_synth import (
    CLASS_NAMES,
    CLUTTER,
    STUD,
    estimate_normals,
    point_labels,
    repo_root,
)
from openwall_stud.synthetic import FULL_ROOM_N_STUDS, LEAN_AXES, Scene, full_room_28

# Planted magnitudes from docs/research/37-fullroom-training-decision.md.
# These sit in the locked Handbook / NAHB buckets. They are not new gauges.
# Corner studs stop at 0.67°. A 1° or 2° tip on a corner closes the 40 mm
# plan gap that stage 5 already requires. Interior studs keep 1° and 2°.
LEAN_MENU_DEG = (0.00, 0.05, 0.10, 0.15, 0.30, 0.50, 0.67, 1.00, 2.00)
CORNER_MENU_DEG = (0.00, 0.05, 0.10, 0.15, 0.30, 0.50, 0.67)
CORNER_SLOTS = (0, 6, 7, 13, 14, 20, 21, 27)
NOISES_M = (0.0005, 0.0010, 0.0015, 0.0020)
SPACING_M = 0.006
PLATE_SPACING_M = 0.010
FLOOR_SPACING_M = 0.020

TRAIN_SEEDS = tuple(range(1101, 1149))
VAL_SEEDS = tuple(range(1201, 1209))
HELD_OUT_SEEDS = tuple(range(1301, 1311))
STAGE5_SEED = 62

WEIGHT_DIR = repo_root() / "artifacts" / "checkpoints" / "stud-heads" / "fullroom"
EXPERIMENT1_WEIGHTS = (
    repo_root() / "artifacts" / "checkpoints" / "stud-heads" / "pointcept_stud_2class.pth",
    repo_root() / "artifacts" / "checkpoints" / "stud-heads" / "randlanet_stud_2class.pth",
)


def manifest_path() -> Path:
    return repo_root() / "data" / "finetune" / "fullroom_28_manifest.json"


def cache_dir() -> Path:
    return repo_root() / "data" / "cache" / "finetune-fullroom"


def assert_safe_weight_path(path: Path) -> Path:
    """Refuse a write that would replace an Experiment 1 stud head."""
    resolved = path.resolve()
    blocked = {item.resolve() for item in EXPERIMENT1_WEIGHTS}
    if resolved in blocked:
        raise RuntimeError(f"refusing to overwrite Experiment 1 checkpoint {path}")
    return path


def _spec(*, split: str, seed: int, index: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    leans: list[float] = []
    axes: list[str] = []
    for slot in range(FULL_ROOM_N_STUDS):
        menu = CORNER_MENU_DEG if slot in CORNER_SLOTS else LEAN_MENU_DEG
        lean = float(rng.choice(menu))
        leans.append(lean)
        if lean == 0.0:
            axes.append("none")
        else:
            axes.append(str(rng.choice(LEAN_AXES)))
    return {
        "split": split,
        "kind": "fullroom_28",
        "seed": int(seed),
        "leans_deg": leans,
        "lean_axes": axes,
        "noise_std_m": float(NOISES_M[index % len(NOISES_M)]),
        "spacing_m": SPACING_M,
        "plate_spacing_m": PLATE_SPACING_M,
        "floor_spacing_m": FLOOR_SPACING_M,
        "nominal": "2x4",
        "n_studs": FULL_ROOM_N_STUDS,
    }


def build_manifest() -> dict[str, Any]:
    train = [_spec(split="train", seed=seed, index=index) for index, seed in enumerate(TRAIN_SEEDS)]
    val = [_spec(split="val", seed=seed, index=index) for index, seed in enumerate(VAL_SEEDS)]
    for index, spec in enumerate(train):
        spec["id"] = f"train_{index:04d}"
    for index, spec in enumerate(val):
        spec["id"] = f"val_{index:04d}"

    used = {int(spec["seed"]) for spec in train + val}
    if used & set(HELD_OUT_SEEDS):
        raise RuntimeError("train or val consumed a held-out scene seed")
    if STAGE5_SEED in used:
        raise RuntimeError("stage5 seed 62 is in the full-room manifest")
    if len(train) != 48 or len(val) != 8:
        raise RuntimeError(f"expected 48/8 rooms, got {len(train)}/{len(val)}")
    for spec in train + val:
        if len(spec["leans_deg"]) != FULL_ROOM_N_STUDS:
            raise RuntimeError(f"{spec['id']} does not have 28 leans")

    return {
        "schema": "openwall.fullroom_28_finetune.v1",
        "decision": "docs/research/37-fullroom-training-decision.md",
        "classes": list(CLASS_NAMES),
        "label_ids": {"clutter": CLUTTER, "stud": STUD},
        "part_stud": 2,
        "part_clutter": [0, 1],
        "lean_menu_deg": list(LEAN_MENU_DEG),
        "corner_menu_deg": list(CORNER_MENU_DEG),
        "corner_slots": list(CORNER_SLOTS),
        "corner_menu_note": (
            "Corner studs draw from corner_menu_deg. A 1° or 2° lean at a corner "
            "closes the 40 mm plan gap stage 5 already enforces. Interior studs "
            "draw from lean_menu_deg, which includes 1° and 2°."
        ),
        "held_out_seeds": list(HELD_OUT_SEEDS),
        "held_out_note": "Scenes A–J. Not in train or val.",
        "excluded_stage5_seed": STAGE5_SEED,
        "excluded_experiment1_scene": "stage0_2x4_lean0.000",
        "train": train,
        "val": val,
        "counts": {"train": len(train), "val": len(val), "studs_per_room": FULL_ROOM_N_STUDS},
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
    return full_room_28(
        leans_deg=spec["leans_deg"],
        lean_axes=spec["lean_axes"],
        nominal=spec.get("nominal", "2x4"),
        seed=int(spec["seed"]),
        spacing_m=float(spec["spacing_m"]),
        plate_spacing_m=float(spec["plate_spacing_m"]),
        floor_spacing_m=float(spec["floor_spacing_m"]),
        noise_std_m=float(spec["noise_std_m"]),
        name=spec["id"],
    )


def cloud_path(spec_id: str) -> Path:
    return cache_dir() / f"{spec_id}.npz"


def ensure_cloud(spec: dict[str, Any]) -> dict[str, np.ndarray]:
    """Load a cached room, or generate, label, and cache it."""
    path = cloud_path(spec["id"])
    if path.is_file():
        with np.load(path) as blob:
            return {
                "points": np.asarray(blob["points"], dtype=np.float32),
                "labels": np.asarray(blob["labels"], dtype=np.int64),
                "normals": np.asarray(blob["normals"], dtype=np.float32),
            }
    scene = materialize(spec)
    if len(scene.studs) != FULL_ROOM_N_STUDS:
        raise RuntimeError(f"{spec['id']} generated {len(scene.studs)} studs")
    points = np.asarray(scene.points_m, dtype=np.float32)
    labels = point_labels(scene)
    if int(labels.min()) != CLUTTER or int(labels.max()) != STUD:
        raise RuntimeError(f"{spec['id']} labels are not clutter and stud")
    normals = estimate_normals(points)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        points=points,
        labels=labels.astype(np.int16),
        normals=normals,
        leans_deg=np.asarray(spec["leans_deg"], dtype=np.float32),
    )
    return {"points": points, "labels": labels, "normals": normals}
