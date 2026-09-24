"""Shared stub scorecard for contenders that are not executed here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openwall_stud.scorecard import empty_sections, write_scorecard


def stub_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    note: str,
) -> dict[str, Any]:
    sections = empty_sections()
    sections["detection"]["note"] = note
    sections["geometry"]["note"] = note
    sections["angle"]["note"] = note
    sections["paint"]["note"] = note
    sections["paint"]["epsilon_locked"] = False
    sections["cost"]["license"] = license_name
    sections["cost"]["hardware"] = hardware
    sections["cost"]["failure_modes"] = failure_modes
    sections["cost"]["note"] = note
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": None,
        "status": "stub_not_run",
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        **sections,
        "notes": [note],
    }


def emit_stub(path: Path, card: dict[str, Any]) -> Path:
    return write_scorecard(path, card)
