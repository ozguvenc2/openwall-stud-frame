"""Map foundation-tool masks onto the shared stud-bar scorecard.

Promptable / zero-shot only. No foundation backbone is trained here.
Binary stud labels (0=clutter, 1=stud) feed ``score_stud_labels``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from openwall_stud.finetune_score import score_stud_labels
from openwall_stud.finetune_synth import STUD
from openwall_stud.one_stud import apply_verdict
from openwall_stud.scorecard import write_scorecard
from openwall_stud.synthetic import Scene


def labels_from_mask(mask: np.ndarray, n_points: int) -> np.ndarray:
    """Boolean or {0,1} mask of length n_points → clutter/stud labels."""
    flat = np.asarray(mask).reshape(-1)
    if flat.shape[0] != n_points:
        raise ValueError(f"mask length {flat.shape[0]} != {n_points}")
    labels = np.zeros(n_points, dtype=np.int64)
    labels[flat.astype(bool)] = STUD
    return labels


def write_foundation_card(
    scene: Scene,
    labels: np.ndarray,
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    runtime_s: float,
    dest,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    implementation: dict[str, Any],
    implementation_short: str,
) -> dict[str, Any]:
    card, _ = score_stud_labels(
        scene,
        labels,
        runtime_s=runtime_s,
        algorithm_id=algorithm_id,
        algorithm=algorithm,
        rank=rank,
        license_name=license_name,
        hardware=hardware,
        failure_modes=failure_modes,
        implementation=implementation,
        implementation_short=implementation_short,
    )
    card["status"] = "ran"
    card["measurement_scope"] = (
        "foundation zero-shot / promptable mask → stud labels → minimal OBB; "
        "synthetic scene only; not a field accuracy"
    )
    apply_verdict(card)
    dest = __import__("pathlib").Path(dest)
    card["scorecard_name"] = dest.name
    write_scorecard(dest, card)
    return card


def summary_row(algorithm: str, card: dict[str, Any]) -> dict[str, Any]:
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    cost = card.get("cost") or {}
    return {
        "algorithm": algorithm,
        "scorecard": card.get("scorecard_name"),
        "status": card.get("status"),
        "pass_fail": card.get("stage0_pass_fail"),
        "precision": det.get("precision"),
        "recall": det.get("recall"),
        "section_mm": geom.get("max_section_error_mm"),
        "length_mm": geom.get("max_length_error_mm"),
        "angle_mae_deg": ang.get("mae_deg"),
        "runtime_s": cost.get("runtime_s"),
        "stud_metrics_scored": card.get("stud_metrics_scored", True),
        "n_stud_points": (card.get("finetune") or {}).get("n_stud_points"),
    }


def blocked_row(algorithm: str, reason: str) -> dict[str, Any]:
    return {
        "algorithm": algorithm,
        "scorecard": None,
        "status": "blocked",
        "pass_fail": "blocked",
        "precision": None,
        "recall": None,
        "section_mm": None,
        "length_mm": None,
        "angle_mae_deg": None,
        "runtime_s": None,
        "stud_metrics_scored": False,
        "reason": reason,
    }
