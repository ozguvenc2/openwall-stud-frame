"""Dressed lumber sizes used by the synthetic generator.

These are the usual US softwood dressed sections (1.5 in by 3.5 in for a 2x4,
1.5 in by 5.5 in for a 2x6), converted at 25.4 mm per inch. They are generator
inputs, not measurements from a scan.
"""

from __future__ import annotations

INCH_M = 0.0254

# (thickness_m, width_m). Thickness is the narrow face, along the wall.
DRESSED_SECTION_M = {
    "2x4": (1.5 * INCH_M, 3.5 * INCH_M),
    "2x6": (1.5 * INCH_M, 5.5 * INCH_M),
}

STUD_LENGTH_8FT_M = 96.0 * INCH_M
OC_16_IN_M = 16.0 * INCH_M

# Working angular tolerance from docs/tolerances.md:
# atan((1/4 inch) / (10 feet)) = atan(0.25 / 120). Not an IRC clause.
TOLERANCE_RAD = __import__("math").atan(0.25 / 120.0)
TOLERANCE_DEG = __import__("math").degrees(TOLERANCE_RAD)
