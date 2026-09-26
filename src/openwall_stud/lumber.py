"""Dressed lumber sizes used by the synthetic generator.

These are the usual US softwood dressed sections (1.5 in by 3.5 in for a 2x4,
1.5 in by 5.5 in for a 2x6), converted at 25.4 mm per inch. They are generator
inputs, not measurements from a scan.
"""

from __future__ import annotations

import math

INCH_M = 0.0254

# (thickness_m, width_m). Thickness is the narrow face, along the wall.
DRESSED_SECTION_M = {
    "2x4": (1.5 * INCH_M, 3.5 * INCH_M),
    "2x6": (1.5 * INCH_M, 5.5 * INCH_M),
}

STUD_LENGTH_8FT_M = 96.0 * INCH_M
OC_16_IN_M = 16.0 * INCH_M

# Handbook of Construction Tolerances (Ballast), as summarized by WoodWorks
# in docs/tolerances.md: 1/4 inch in 10 feet when gypsum or plaster is used.
# atan((1/4 inch) / (10 feet)) = atan(0.25 / 120). Oz's Finnish-style folklore
# label (~0.12°, sometimes ~0.1°) is this same geometry. Not an AHJ code number.
TOLERANCE_RAD = math.atan(0.25 / 120.0)
TOLERANCE_DEG = math.degrees(TOLERANCE_RAD)

# NAHB Residential Construction Performance Guidelines, 6th ed., guideline
# 4-1-1, as opened in docs/research/36-az-framing-standards-inspector-tolerances.md:
# 3/8 inch out of plumb in 32 inches. Warranty gauge, not an IRC red tag.
# atan((3/8 inch) / 32 inches) = atan(0.375 / 32). Doc 36 rounds this to 0.671°.
NAHB_WARRANTY_RAD = math.atan(0.375 / 32.0)
NAHB_WARRANTY_DEG = math.degrees(NAHB_WARRANTY_RAD)
