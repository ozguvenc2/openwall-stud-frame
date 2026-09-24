"""Green / yellow / red paint for a stud lean angle.

The rule matches the ranking note: green when the whole error interval sits
inside the working tolerance, red when the whole interval sits outside it,
yellow when the interval overlaps the tolerance. An unlocked device band
(epsilon unknown) is yellow on every stud. A placeholder epsilon may be
evaluated separately and must not be reported as a measured device band.
"""

from __future__ import annotations

from dataclasses import dataclass

from openwall_stud.lumber import TOLERANCE_DEG

# Round number used only to illustrate the color rule. Not a sensor spec.
PLACEHOLDER_EPSILON_DEG = 0.05


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
    """Color as if the placeholder epsilon were locked. Not a field call."""
    return paint_stud(
        theta_deg,
        epsilon_deg=PLACEHOLDER_EPSILON_DEG,
        epsilon_locked=True,
    )


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
