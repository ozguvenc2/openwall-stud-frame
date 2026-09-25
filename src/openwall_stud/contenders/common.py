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


def blocked_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    blocker: str,
    blocker_short: str,
    scene: dict[str, Any],
    attempt: dict[str, Any],
) -> dict[str, Any]:
    """Scorecard for a finder that loaded the cloud and could not run.

    Detection, geometry, angle, paint colors, and runtime stay null.
    """
    sections = empty_sections()
    for key in ("detection", "geometry", "angle", "paint", "cost"):
        sections[key]["note"] = blocker
    sections["paint"]["epsilon_locked"] = False
    sections["cost"]["license"] = license_name
    sections["cost"]["hardware"] = hardware
    sections["cost"]["failure_modes"] = failure_modes
    sections["cost"]["runtime_s"] = None
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": 0,
        "status": "blocked_install",
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        "measurement_scope": "not measured; the stack did not segment this cloud",
        "scene": scene,
        "attempt": attempt,
        "blocker": blocker,
        "blocker_short": blocker_short,
        **sections,
        "notes": [blocker],
    }


def ran_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    scene: dict[str, Any],
    sections: dict[str, Any],
    implementation: dict[str, Any],
    implementation_short: str,
) -> dict[str, Any]:
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": 0,
        "status": "ran",
        "epsilon_locked": False,
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process, one stud",
        "scene": scene,
        "implementation": implementation,
        "implementation_short": implementation_short,
        **sections,
        "notes": [
            "Synthetic stage 0 only. Not a field measurement. "
            "Device epsilon is unlocked, so production paint is yellow."
        ],
    }
