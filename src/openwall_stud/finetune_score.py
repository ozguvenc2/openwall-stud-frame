"""Score a stud/clutter labeling with the same minimal OBB the classical finders use."""

from __future__ import annotations

from typing import Any

import numpy as np

from openwall_stud.contenders.common import ran_card
from openwall_stud.finetune_synth import CLASS_NAMES, STUD, STUD_MIN_POINTS
from openwall_stud.one_stud import scene_record
from openwall_stud.poststep import score_clusters
from openwall_stud.synthetic import Scene


def histogram(labels: np.ndarray) -> list[dict[str, Any]]:
    ids = np.asarray(labels).reshape(-1)
    rows = []
    for index, name in enumerate(CLASS_NAMES):
        rows.append({"id": index, "name": name, "count": int(np.sum(ids == index))})
    return rows


def score_stud_labels(
    scene: Scene,
    labels: np.ndarray,
    *,
    runtime_s: float,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    implementation: dict[str, Any],
    implementation_short: str,
) -> tuple[dict[str, Any], list]:
    """Fit one minimal OBB on stud-labeled points when enough of them exist."""
    pred = np.asarray(labels).reshape(-1)
    if pred.shape[0] != scene.n_points:
        raise ValueError(f"label length {pred.shape[0]} != cloud {scene.n_points}")
    stud_idx = np.flatnonzero(pred == STUD)
    n_stud = int(stud_idx.size)
    clusters: list[np.ndarray] = []
    if n_stud >= STUD_MIN_POINTS:
        clusters.append(np.asarray(scene.points_m[stud_idx], dtype=np.float64))
    detection_note = (
        f"{n_stud} points labeled stud (class {STUD}) of {scene.n_points}. "
        f"A box is fit when that count is at least {STUD_MIN_POINTS}. "
        "Counts are this synthetic scene, not a field accuracy."
    )
    if n_stud < STUD_MIN_POINTS:
        detection_note += " This scene stayed clutter-only for the box."
    sections, detections = score_clusters(
        scene,
        clusters,
        runtime_s=runtime_s,
        detection_note=detection_note,
        geometry_note=(
            "Section and length are the minimal OBB of the stud-labeled points "
            "versus the dressed generator stud. Same box as the classical finders."
        ),
        angle_note="Truth is the generator lean against +Z. Not a SKIL reading.",
        cost={
            "runtime_s": round(float(runtime_s), 4),
            "license": license_name,
            "hardware": hardware,
            "bbox_kind": "minimal_oriented",
            "failure_modes": failure_modes,
            "n_stud_points": n_stud,
            "stud_min_points": STUD_MIN_POINTS,
            "note": "Runtime is this inference on this scene, after weights were already loaded.",
        },
    )
    card = ran_card(
        algorithm_id=algorithm_id,
        algorithm=algorithm,
        rank=rank,
        scene=scene_record(scene),
        sections=sections,
        implementation=implementation,
        implementation_short=implementation_short,
    )
    card["measurement_scope"] = (
        "synthetic fine-tune inference; stud box is the minimal OBB of points labeled stud"
    )
    card["finetune"] = {
        "classes": list(CLASS_NAMES),
        "label_histogram": histogram(pred),
        "n_stud_points": n_stud,
        "stud_fraction": round(n_stud / max(scene.n_points, 1), 4),
        "stud_box": bool(detections),
        "synthetic_only": True,
    }
    return card, detections
