# Tolerances

Research date: 2026-09-23. These are **published framing or finish guidelines**, not a sensor error budget and not a pass/fail threshold implemented in this repo. Red/green paint should not ship until a measurement-error term is measured on the capture path.

Sources and the sensing comparison: [research/01-sensing-modalities.md](research/01-sensing-modalities.md).

## Plumb guidelines (linear)

The 2021 IRC wall chapter reviewed via UpCodes specifies stud size, height, and spacing. It does **not** state a general plumb tolerance for wood studs. [IRC 2021 Chapter 6 (UpCodes, Texas IHB)](https://up.codes/viewer/texas/irc-2021/chapter/6/wall-construction). WoodWorks makes the same point for the IBC and the AWC NDS: no light-frame wood construction-tolerance requirement there. [WoodWorks expert tip](https://www.woodworks.org/resources/construction-tolerances-for-light-wood-frame-projects/).

WoodWorks summarizes commonly cited **finish-driven** guidelines (quotes are their summary of other documents):

| Source as summarized by WoodWorks | Vertical plumb figure | What it applies to |
| --- | --- | --- |
| Residential Construction Performance Guidelines (NAHB) | 3/8 inch in 32 inches | Face of wood-framed walls |
| Handbook of Construction Tolerances | 1/4 inch in 10 feet | Tightened when finishes such as gypsum wallboard and plaster are used |
| UFGS (as summarized) | 1/4 inch in 8 feet | Stud plumb when wallboard, plaster, or mortar-bed ceramic tile is used |
| UFGS (as summarized) | 1/8 inch in 8 feet | Tighter finishes (dry-set / latex-portland / organic-adhesive tile) |
| Residential and Light Commercial Construction Standards | 1/4 inch in 32 inches | Vertical tolerance |

The product sketch “about ±1/4 inch per 10 feet” matches the **Handbook** row above, not an IRC clause.

## Derived angle (not a code number)

`atan((1/4 inch) / (10 feet × 12)) = atan(0.25/120) ≈ 0.1194°`.

That is why notes say **~0.12°**. It is geometry applied to the 1/4 inch in 10 feet guideline. It is not a published degree tolerance.

Tip offset of a plumb line over an 8 foot stud, same small-angle geometry:

| Angle | Offset over 96 inches | Note |
| --- | --- | --- |
| 0.1194° (derived from 1/4 inch in 10 feet) | 0.20 inch (about 5.1 mm) | `96 × tan(0.1194°)` |
| 0.10° | about 4.3 mm | `2438 mm × tan(0.10°)` |

A sensor whose local surface noise is already several millimeters to centimeters cannot, by itself, support a pass/fail call at this offset. See the phone-LiDAR versus TLS rows in the sensing table. An end-to-end error budget (sensor, registration, segmentation, box fit, gravity reference) is still **unknown**.

## What is still missing

- A chosen margin (NAHB 3/8 inch in 32 inches versus Handbook 1/4 inch in 10 feet versus UFGS 1/4 inch in 8 feet). They are not the same angle.
- A measured uncertainty for the capture path actually used (Polycam / phone LiDAR versus a TLS check).
- Gravity-vector error (phone IMU versus scanner inclinometer). Not quantified in this pass.
