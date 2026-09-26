"""Shared scorecard JSON for every stud-segmentation contender.

Every card has detection, geometry, angle, paint, and cost sections.
Missing measurements are JSON null. This writer does not invent them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openwall_stud.angle_reference import assert_synthetic_scorecard_reference

SECTION_KEYS = ("detection", "geometry", "angle", "paint", "cost")

REQUIRED_KEYS = (
    "schema",
    "algorithm_id",
    "algorithm",
    "rank",
    "stage",
    "status",
    "detection",
    "geometry",
    "angle",
    "paint",
    "cost",
)


def empty_sections() -> dict[str, Any]:
    return {
        "detection": {
            "n_true": None,
            "n_pred": None,
            "true_positives": None,
            "false_positives": None,
            "false_negatives": None,
            "precision": None,
            "recall": None,
            "note": "not run",
        },
        "geometry": {
            "max_section_error_mm": None,
            "max_length_error_mm": None,
            "per_stud": [],
            "note": "not run",
        },
        "angle": {
            "mae_deg": None,
            "pct_in_band": None,
            "band_deg": None,
            "per_stud": [],
            "note": "not run",
        },
        "paint": {
            "epsilon_locked": False,
            "epsilon_deg": None,
            "production_colors": [],
            "hypothetical_placeholder_epsilon_deg": None,
            "hypothetical_colors": [],
            "note": "not run",
        },
        "cost": {
            "runtime_s": None,
            "license": None,
            "hardware": None,
            "failure_modes": [],
            "note": "not run",
        },
    }


def validate_scorecard(card: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in card]
    if missing:
        raise ValueError(f"scorecard missing keys: {missing}")
    for key in SECTION_KEYS:
        if not isinstance(card[key], dict):
            raise ValueError(f"scorecard section {key} must be an object")
    assert_synthetic_scorecard_reference(card)


def write_scorecard(path: str | Path, card: dict[str, Any]) -> Path:
    """Validate and write one scorecard. Returns the path written.

    Day-table rows are a separate append. Call ``append_day_row`` after this
    so a finished run is recorded without inventing numbers the card does not
    contain.
    """
    validate_scorecard(card)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(card, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return dest


def append_day_row(**kwargs: Any) -> dict[str, Any]:
    """Append or update one results-by-day row from a finished scorecard."""
    from openwall_stud.results_by_day import append_day_row as _append

    return _append(**kwargs)


def read_scorecard(path: str | Path) -> dict[str, Any]:
    card = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_scorecard(card)
    return card
