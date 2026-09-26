"""Lettered 28-stud scenes for the full-room experiment.

Seeds 1301–1310 are the held-out range from doc 37. Leans are planted
explicitly. Expected colors use ``dual_standard_passes`` on the planted
|lean| from vertical. That is the ground-truth plumb call.

Experiment 1 colors |measured − truth| on a stud whose truth is 0°, so the
two quantities match there. On these rooms they differ: a perfect measure
of a 1° stud is a red plumb call and a green measurement-error call.
Phase 4 reports both. Catch rate uses the plumb call.
"""

from __future__ import annotations

from typing import Any

from openwall_stud.finetune_fullroom import CORNER_SLOTS, FLOOR_SPACING_M, PLATE_SPACING_M, SPACING_M
from openwall_stud.paint import dual_standard_passes
from openwall_stud.synthetic import FULL_ROOM_N_STUDS

INTERIOR_SLOTS = tuple(slot for slot in range(FULL_ROOM_N_STUDS) if slot not in CORNER_SLOTS)
SCENE_NOISE_M = 0.001

# (letter, seed, title, list of (slot, lean_deg) overrides; unspecified slots are 0°)
_OVERRIDES: tuple[tuple[str, int, str, tuple[tuple[int, float], ...]], ...] = (
    ("A", 1301, "1 Handbook red, interior 0.30°", ((INTERIOR_SLOTS[0], 0.30),)),
    ("B", 1302, "2 Handbook reds, interior 0.30°", tuple((INTERIOR_SLOTS[i], 0.30) for i in range(2))),
    ("C", 1303, "4 Handbook reds, interior 0.30°", tuple((INTERIOR_SLOTS[i], 0.30) for i in range(4))),
    ("D", 1304, "6 Handbook reds, interior 0.50°", tuple((INTERIOR_SLOTS[i], 0.50) for i in range(6))),
    ("E", 1305, "8 Handbook reds, interior 0.50°", tuple((INTERIOR_SLOTS[i], 0.50) for i in range(8))),
    (
        "F",
        1306,
        "10 Handbook reds at 0.30°, NAHB absolute still green",
        tuple((INTERIOR_SLOTS[i], 0.30) for i in range(10)),
    ),
    ("G", 1307, "1 red on both gauges, interior 2.00°", ((INTERIOR_SLOTS[0], 2.00),)),
    (
        "H",
        1308,
        "10 reds on both gauges, interior 1.00°",
        tuple((INTERIOR_SLOTS[i], 1.00) for i in range(10)),
    ),
    (
        "I",
        1309,
        "Mixed Handbook: 0.10° sensor-yellow, 0.15° absolute-red sensor-yellow, 0.30° red",
        tuple((INTERIOR_SLOTS[i], 0.10) for i in range(8))
        + tuple((INTERIOR_SLOTS[i], 0.15) for i in range(8, 12))
        + tuple((INTERIOR_SLOTS[i], 0.30) for i in range(12, 16)),
    ),
    (
        "J",
        1310,
        "Mixed NAHB: 0.67° sensor-yellow, 2.00° red, 0.05° green",
        tuple((INTERIOR_SLOTS[i], 0.67) for i in range(6))
        + tuple((INTERIOR_SLOTS[i], 2.00) for i in range(6, 8))
        + tuple((INTERIOR_SLOTS[i], 0.05) for i in range(8, 16)),
    ),
)


def _axes_for(leans: list[float]) -> list[str]:
    axes = []
    for lean in leans:
        axes.append("none" if lean == 0.0 else "+X")
    return axes


def scene_specs() -> list[dict[str, Any]]:
    """Ten scenes A–J. Each row is a full_room_28 argument set plus expected colors."""
    rows = []
    for letter, seed, title, overrides in _OVERRIDES:
        leans = [0.0] * FULL_ROOM_N_STUDS
        for slot, lean in overrides:
            if not 0 <= slot < FULL_ROOM_N_STUDS:
                raise ValueError(f"scene {letter} slot {slot} is outside 0..27")
            if slot in CORNER_SLOTS and lean > 0.67:
                raise ValueError(f"scene {letter} plants {lean}° on corner slot {slot}")
            leans[slot] = float(lean)
        axes = _axes_for(leans)
        studs = []
        counts = {
            "handbook_finish_plumb": {"absolute": {}, "sensor": {}},
            "nahb_warranty_gauge": {"absolute": {}, "sensor": {}},
        }
        for slot, lean in enumerate(leans):
            report = dual_standard_passes(abs(lean))
            colored = {}
            for spec in report["standards"]:
                key = spec["key"]
                colored[key] = {
                    "absolute": spec["absolute"]["color"],
                    "sensor": spec["sensor"]["color"],
                }
                for column in ("absolute", "sensor"):
                    color = spec[column]["color"]
                    bucket = counts[key][column]
                    bucket[color] = bucket.get(color, 0) + 1
            studs.append(
                {
                    "slot": slot,
                    "wall": ("south", "west", "north", "east")[slot // 7],
                    "corner": slot in CORNER_SLOTS,
                    "lean_deg": lean,
                    "lean_axis": axes[slot],
                    "expected_plumb": colored,
                }
            )
        rows.append(
            {
                "letter": letter,
                "seed": seed,
                "title": title,
                "name": f"fullroom_{letter}",
                "n_studs": FULL_ROOM_N_STUDS,
                "noise_std_m": SCENE_NOISE_M,
                "spacing_m": SPACING_M,
                "plate_spacing_m": PLATE_SPACING_M,
                "floor_spacing_m": FLOOR_SPACING_M,
                "leans_deg": leans,
                "lean_axes": axes,
                "expected_plumb_counts": counts,
                "studs": studs,
                "plumb_call": (
                    "Expected color is dual_standard_passes on the planted |lean| "
                    "from vertical. Catch rate compares that color to the color of "
                    "the measured lean from the same reference."
                ),
                "measurement_error_call": (
                    "Experiment 1 colors |measured − planted|. Phase 4 records that "
                    "per stud as well. It is not the supposed-red count."
                ),
            }
        )
    letters = [row["letter"] for row in rows]
    if letters != list("ABCDEFGHIJ"):
        raise RuntimeError(f"scene letters {letters}")
    seeds = [row["seed"] for row in rows]
    if seeds != list(range(1301, 1311)):
        raise RuntimeError(f"scene seeds {seeds}")
    return rows
