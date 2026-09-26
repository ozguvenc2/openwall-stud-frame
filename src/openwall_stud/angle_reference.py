"""Synthetic lean reference for TruePlank.

Synthetic tests measure lean against the fitted floor normal when the scene
has a floor or slab, and against generator +Z only when it does not. They do
not use a SKIL or any other level reading. Field and class F may still use a
level when wood readings exist. That protocol is not this module.
"""

from __future__ import annotations

import numpy as np

# Generator part id for a floor or slab. Plates are part 1. Studs are part 2.
FLOOR_PART_ID = 0

REFERENCE_FLOOR = "floor_normal"
REFERENCE_GENERATOR_Z = "gravity_z_no_floor_plane"
GENERATOR_UP = np.array([0.0, 0.0, 1.0])

SYNTHETIC_ANGLE_RULE = (
    "Synthetic tests measure lean against the fitted floor normal when the scene "
    "has a floor or slab, and against generator +Z only when it does not. "
    "They do not use a SKIL or any other level reading."
)


def scene_has_floor(scene: object) -> bool:
    """True when the generator marked a floor or slab on this cloud."""
    part = getattr(scene, "part", None)
    if part is None:
        return False
    return bool(np.any(np.asarray(part) == FLOOR_PART_ID))


def lock_synthetic_reference(
    floor_normal: np.ndarray | None,
    *,
    has_floor: bool,
) -> tuple[str, np.ndarray]:
    """Return ``(name, unit vector)`` for one synthetic cloud.

    A fitted slab normal wins. Generator +Z is allowed only when no slab was
    fit and the scene was not built with a floor. A missing fit on a floored
    scene is an error, not a silent fallback to +Z or to a level.
    """
    if floor_normal is not None:
        vec = np.asarray(floor_normal, dtype=float).reshape(3).copy()
        norm = float(np.linalg.norm(vec))
        if norm == 0.0 or not np.isfinite(norm):
            raise RuntimeError("fitted floor normal has zero length")
        vec = vec / norm
        if float(vec[2]) < 0.0:
            vec = -vec
        return REFERENCE_FLOOR, vec
    if has_floor:
        raise RuntimeError(
            "synthetic scene has a floor or slab, but no floor normal was fit; "
            "generator +Z is not the reference on that cloud"
        )
    return REFERENCE_GENERATOR_Z, GENERATOR_UP.copy()


def assert_synthetic_reference_name(name: str) -> str:
    """Reject a level reading and any name other than the two synthetic references."""
    if name not in (REFERENCE_FLOOR, REFERENCE_GENERATOR_Z):
        raise ValueError(
            f"synthetic angle_reference must be {REFERENCE_FLOOR!r} or "
            f"{REFERENCE_GENERATOR_Z!r}, got {name!r}. "
            "A SKIL or other level reading is not a synthetic reference."
        )
    return name


def synthetic_angle_note(reference_name: str, *, extra: str = "") -> str:
    """One scorecard sentence for the reference this synthetic run used."""
    assert_synthetic_reference_name(reference_name)
    if reference_name == REFERENCE_FLOOR:
        lead = "Truth is the generator axis against the fitted floor normal."
    else:
        lead = "Truth is the generator axis against +Z. This scene has no floor."
    text = f"{lead} {SYNTHETIC_ANGLE_RULE}"
    extra = extra.strip()
    if extra:
        text = f"{text} {extra}"
    return text


def card_is_synthetic(card: dict) -> bool:
    """True when a scorecard is a generator run, not a field capture."""
    scope = str(card.get("measurement_scope") or "").lower()
    if "synthetic" in scope or card.get("status") == "ran_synthetic":
        return True
    scene = card.get("scene") or {}
    name = str(scene.get("name") or "")
    if name.startswith(("stage", "s1_", "s1b_")):
        return True
    description = str(scene.get("description") or "").lower()
    return "synthetic" in description


def assert_synthetic_scorecard_reference(card: dict) -> None:
    """Refuse a level, and refuse +Z on a card that recorded a fitted floor."""
    if not card_is_synthetic(card):
        return
    angle = card.get("angle") or {}
    if "reference" not in angle or angle.get("reference") is None:
        return
    name = assert_synthetic_reference_name(str(angle["reference"]))
    scene = card.get("scene") or {}
    scene_name = scene.get("reference")
    if scene_name is not None:
        assert_synthetic_reference_name(str(scene_name))
        if str(scene_name) != name:
            raise ValueError(
                f"synthetic scene.reference {scene_name!r} does not match "
                f"angle.reference {name!r}"
            )
    floor_found = None
    if "floor_found" in scene:
        floor_found = bool(scene["floor_found"])
    elif "floor_found" in (card.get("cost") or {}):
        floor_found = bool(card["cost"]["floor_found"])
    if floor_found is True and name != REFERENCE_FLOOR:
        raise ValueError("synthetic card found a floor but angle_reference is not floor_normal")
    if floor_found is False and name != REFERENCE_GENERATOR_Z:
        raise ValueError(
            "synthetic card found no floor but angle_reference is not generator +Z"
        )
