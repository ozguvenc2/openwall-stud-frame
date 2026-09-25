"""The one synthetic stud used by the five-finder run.

Stage 0, dressed 2x4, lean 0.05 degrees, seed 2. There is no floor, so the
angle reference is the generator +Z axis. This module does not build stage 2
or stage 3 scenes.
"""

from __future__ import annotations

from typing import Any

from openwall_stud.synthetic import Scene, stage0_single_stud

NOMINAL = "2x4"
LEAN_DEG = 0.05
SEED = 2

# Design-plan stage 0 bars. A miss is a synthetic bring-up failure, not a
# field acceptance result.
STAGE0_SECTION_MM = 10.0
STAGE0_LENGTH_MM = 25.0
STAGE0_ANGLE_DEG = 0.05


def make_scene() -> Scene:
    """Return the single cloud every finder in this run must see."""
    return stage0_single_stud(nominal=NOMINAL, lean_deg=LEAN_DEG, seed=SEED)


def scene_record(scene: Scene) -> dict[str, Any]:
    stud = scene.studs[0]
    return {
        "name": scene.name,
        "stage": scene.stage,
        "nominal": stud.nominal,
        "lean_deg": stud.lean_deg,
        "seed": scene.seed,
        "spacing_m": scene.spacing_m,
        "noise_std_m": scene.noise_std_m,
        "n_points": scene.n_points,
        "length_m": stud.length_m,
        "section_m": [float(stud.section_m[0]), float(stud.section_m[1])],
        "reference": "gravity_z_no_floor_plane",
        "reference_meaning": (
            "Stage 0 has no floor. The generator +Z axis is the angle reference. "
            "The cloud is not rotated."
        ),
        "description": scene.description,
    }


def stage0_bar_failures(card: dict[str, Any]) -> list[str]:
    """Compare one ran scorecard with the stage 0 synthetic bars."""
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    paint = card.get("paint") or {}
    failures: list[str] = []
    precision = det.get("precision")
    recall = det.get("recall")
    if precision != 1.0 or recall != 1.0:
        failures.append(f"detection P={precision} R={recall}")
    section = geom.get("max_section_error_mm")
    if section is None or section > STAGE0_SECTION_MM:
        failures.append(f"section error {section} mm > {STAGE0_SECTION_MM}")
    length = geom.get("max_length_error_mm")
    if length is None or length > STAGE0_LENGTH_MM:
        failures.append(f"length error {length} mm > {STAGE0_LENGTH_MM}")
    angle = ang.get("max_abs_error_deg")
    if angle is None or angle > STAGE0_ANGLE_DEG:
        failures.append(f"angle error {angle} deg > {STAGE0_ANGLE_DEG}")
    colors = list(paint.get("production_colors") or [])
    if not colors or any(color != "yellow" for color in colors):
        failures.append(f"production paint was not yellow on every detection ({colors})")
    return failures


def apply_verdict(card: dict[str, Any]) -> str:
    """Set stage0_pass_fail on the card and return the day-table value."""
    status = card.get("status")
    if status == "blocked_install":
        card["stage0_pass_fail"] = "blocked_install"
        card["stage0_bar_failures"] = []
        card["stage0_bars"] = _bars_record()
        return "blocked_install"
    if status != "ran":
        card["stage0_pass_fail"] = "not_run"
        card["stage0_bar_failures"] = []
        return "not_run"
    failures = stage0_bar_failures(card)
    card["stage0_bar_failures"] = failures
    card["stage0_bars"] = _bars_record()
    card["stage0_pass_fail"] = "fail" if failures else "pass"
    return card["stage0_pass_fail"]


def day_notes(card: dict[str, Any], scorecard_name: str) -> str:
    if card.get("status") == "blocked_install":
        short = card.get("blocker_short") or "See the scorecard blocker."
        return f"Blocked install. Metrics left null. {short} Scorecard: {scorecard_name}."
    short = card.get("implementation_short") or card.get("algorithm") or ""
    verdict = card.get("stage0_pass_fail") or ""
    return (
        "Synthetic stage 0, 2x4 lean 0.05 deg, seed 2, reference +Z. "
        "Device epsilon unlocked. "
        f"{short} Stage 0 bars: {verdict}. Scorecard: {scorecard_name}."
    )


def figure_lines(card: dict[str, Any]) -> list[str]:
    if card.get("status") != "ran":
        return [
            "Scaffold. No oriented box was fit, so none is drawn.",
            str(card.get("blocker_short") or ""),
            "Synthetic 2x4, lean 0.05 deg, seed 2. Not a field cloud.",
        ]
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    cost = card.get("cost") or {}
    return [
        f"P={det.get('precision')}  R={det.get('recall')}  section {geom.get('max_section_error_mm')} mm  length {geom.get('max_length_error_mm')} mm",
        f"angle MAE {ang.get('mae_deg')} deg  max {ang.get('max_abs_error_deg')} deg  paint { (card.get('paint') or {}).get('production_colors') }",
        f"runtime {cost.get('runtime_s')} s    stage 0 bars: {card.get('stage0_pass_fail')}",
        "Synthetic 2x4, lean 0.05 deg, seed 2, reference +Z. Not a field measurement.",
    ]


def _bars_record() -> dict[str, Any]:
    return {
        "detection": "precision = 1 and recall = 1",
        "section_mm": STAGE0_SECTION_MM,
        "length_mm": STAGE0_LENGTH_MM,
        "max_abs_angle_deg": STAGE0_ANGLE_DEG,
        "paint": "every production color yellow",
        "scope": "synthetic stage 0 bring-up, not a field test",
    }
