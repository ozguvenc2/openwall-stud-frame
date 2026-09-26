"""Green / yellow / red paint for a stud lean error.

Production paint stays yellow while the device band is unlocked. The dual-pass
report colors mean |measured − synthetic truth| against two published gauges,
each with an absolute column (no device error) and a sensor column.

The interval rule matches the ranking note: green when the whole interval sits
inside the gauge, red when the whole interval sits outside it, yellow when the
interval overlaps the gauge. An unlocked device band (epsilon unknown) is
yellow on every stud. That production lock is separate from the sensor column.
"""

from __future__ import annotations

from dataclasses import dataclass

from openwall_stud.lumber import NAHB_WARRANTY_DEG, TOLERANCE_DEG

# SKIL / digital-level device band used on the sensor-error column.
# Historically the placeholder illustration of this same 0.05° rule.
# Not human placement error and not lumber surface or warp.
PLACEHOLDER_EPSILON_DEG = 0.05
SENSOR_EPSILON_DEG = PLACEHOLDER_EPSILON_DEG

DUAL_PASS_RULE = (
    "Let e = |measured lean − synthetic truth lean| in degrees. "
    "Let τ be the gauge. Let ε be 0° on the absolute column and "
    "0.05° (SKIL device band) on the sensor column. "
    "Green if e + ε ≤ τ (the whole interval is inside the gauge). "
    "Red if e − ε > τ (the whole interval is outside the gauge). "
    "Yellow if the interval overlaps τ. "
    "When ε = 0 the interval is the point e, so green if e ≤ τ and red if e > τ; "
    "yellow does not occur, and e = τ is green. "
    "Production paint stays yellow while device ε is unlocked. "
    "The sensor column does not include human placement error or lumber surface defects."
)


@dataclass(frozen=True)
class PaintDecision:
    color: str
    reason: str
    theta_deg: float
    epsilon_deg: float | None
    epsilon_locked: bool
    tolerance_deg: float


def paint_stud(
    theta_deg: float,
    *,
    epsilon_deg: float | None = None,
    epsilon_locked: bool = False,
    tolerance_deg: float = TOLERANCE_DEG,
) -> PaintDecision:
    """Return the paint color for one stud.

    ``theta_deg`` is the angle between the stud long axis and the reference
    up vector. Zero means aligned with that reference.
    """
    if not epsilon_locked or epsilon_deg is None:
        return PaintDecision(
            color="yellow",
            reason="epsilon_unlocked",
            theta_deg=float(theta_deg),
            epsilon_deg=None if epsilon_deg is None else float(epsilon_deg),
            epsilon_locked=False,
            tolerance_deg=float(tolerance_deg),
        )
    if epsilon_deg < 0:
        raise ValueError("epsilon_deg must be >= 0")
    lo = float(theta_deg) - float(epsilon_deg)
    hi = float(theta_deg) + float(epsilon_deg)
    if hi <= tolerance_deg:
        color, reason = "green", "interval_inside"
    elif lo > tolerance_deg:
        color, reason = "red", "interval_outside"
    else:
        color, reason = "yellow", "interval_overlaps"
    return PaintDecision(
        color=color,
        reason=reason,
        theta_deg=float(theta_deg),
        epsilon_deg=float(epsilon_deg),
        epsilon_locked=True,
        tolerance_deg=float(tolerance_deg),
    )


def hypothetical_placeholder(theta_deg: float) -> PaintDecision:
    """Color measured lean as if the placeholder epsilon were locked.

    This is the old single-gauge illustration on θ itself. The forward report
    is ``dual_standard_passes`` on |measured − truth|. Not a field call.
    """
    return paint_stud(
        theta_deg,
        epsilon_deg=PLACEHOLDER_EPSILON_DEG,
        epsilon_locked=True,
    )


def _color_dict(decision: PaintDecision) -> dict[str, str]:
    return {"color": decision.color, "reason": decision.reason}


def dual_standard_passes(abs_error_deg: float) -> dict[str, object]:
    """Color one mean absolute lean error on both gauges and both references.

    ``abs_error_deg`` is |measured lean − known synthetic or absolute truth|.
    Absolute uses ε = 0. The sensor column uses the 0.05° SKIL device band
    with the same interval rule as ``paint_stud``. Production yellow-while-
    unlocked is not applied here.
    """
    if abs_error_deg < 0:
        raise ValueError("abs_error_deg must be >= 0")
    error = float(abs_error_deg)
    standards = (
        {
            "key": "handbook_finish_plumb",
            "name": "Handbook finish plumb (1/4 in in 10 ft)",
            "folklore_label": (
                "Finnish-style folklore plumb (~0.12°, sometimes cited ~0.1°). "
                "Same 1/4 inch in 10 feet geometry. Not an AHJ code number."
            ),
            "threshold_deg": float(TOLERANCE_DEG),
            "linear": "1/4 inch in 10 feet",
            "citation": (
                "Handbook of Construction Tolerances (Ballast), WoodWorks summary; "
                "docs/tolerances.md"
            ),
        },
        {
            "key": "nahb_warranty_gauge",
            "name": "NAHB warranty gauge (3/8 in in 32 in)",
            "folklore_label": None,
            "threshold_deg": float(NAHB_WARRANTY_DEG),
            "linear": "3/8 inch in 32 inches",
            "citation": (
                "NAHB Residential Construction Performance Guidelines 4-1-1; "
                "docs/research/36-az-framing-standards-inspector-tolerances.md"
            ),
        },
    )
    colored = []
    for spec in standards:
        absolute = paint_stud(
            error,
            epsilon_deg=0.0,
            epsilon_locked=True,
            tolerance_deg=spec["threshold_deg"],
        )
        sensor = paint_stud(
            error,
            epsilon_deg=SENSOR_EPSILON_DEG,
            epsilon_locked=True,
            tolerance_deg=spec["threshold_deg"],
        )
        colored.append(
            {
                **spec,
                "absolute": _color_dict(absolute),
                "sensor": _color_dict(sensor),
            }
        )
    return {
        "abs_error_deg": error,
        "sensor_epsilon_deg": SENSOR_EPSILON_DEG,
        "rule": DUAL_PASS_RULE,
        "standards": colored,
    }


def assert_paint_rules() -> None:
    """Lock the color boundaries so a later edit cannot silently flip them."""
    assert paint_stud(0.0, epsilon_locked=False).color == "yellow"
    assert paint_stud(2.0, epsilon_deg=0.05, epsilon_locked=False).color == "yellow"
    assert paint_stud(0.02, epsilon_deg=0.05, epsilon_locked=True).color == "green"
    assert paint_stud(0.10, epsilon_deg=0.05, epsilon_locked=True).color == "yellow"
    assert paint_stud(0.40, epsilon_deg=0.05, epsilon_locked=True).color == "red"
    # theta + epsilon == tolerance is inside, so green.
    tau = TOLERANCE_DEG
    assert paint_stud(tau - 0.05, epsilon_deg=0.05, epsilon_locked=True).color == "green"
    # theta - epsilon == tolerance is not outside (the red test is strict >).
    edge = paint_stud(tau + 0.05, epsilon_deg=0.05, epsilon_locked=True)
    assert edge.color == "yellow"

    # Absolute column: ε = 0. Equality is green. Yellow does not occur.
    on_gauge = dual_standard_passes(tau)
    handbook = on_gauge["standards"][0]
    nahb = on_gauge["standards"][1]
    assert handbook["key"] == "handbook_finish_plumb"
    assert nahb["key"] == "nahb_warranty_gauge"
    assert handbook["absolute"]["color"] == "green"
    assert handbook["absolute"]["reason"] == "interval_inside"
    just_over = dual_standard_passes(tau + 1e-9)["standards"][0]
    assert just_over["absolute"]["color"] == "red"
    assert just_over["absolute"]["reason"] == "interval_outside"

    # Sensor column reuses the interval overlap on the 0.05° SKIL band.
    handbook_sensor = dual_standard_passes(0.10)["standards"][0]["sensor"]
    assert handbook_sensor["color"] == "yellow"
    assert handbook_sensor["reason"] == "interval_overlaps"
    assert dual_standard_passes(0.02)["standards"][0]["sensor"]["color"] == "green"
    assert dual_standard_passes(0.40)["standards"][0]["sensor"]["color"] == "red"

    # NAHB warranty gauge is the wider published figure, not a new tolerance.
    assert nahb["threshold_deg"] == NAHB_WARRANTY_DEG
    assert dual_standard_passes(0.40)["standards"][1]["absolute"]["color"] == "green"
    assert dual_standard_passes(0.65)["standards"][1]["sensor"]["color"] == "yellow"
    assert dual_standard_passes(0.80)["standards"][1]["sensor"]["color"] == "red"
    assert dual_standard_passes(0.80)["standards"][1]["absolute"]["color"] == "red"
