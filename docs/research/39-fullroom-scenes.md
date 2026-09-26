# Full-room scenes A–J

Date (America/Los_Angeles): **2026-09-26**. Ten synthetic rooms, 28 studs each, seeds 1301–1310. Those seeds are the held-out range in [37-fullroom-training-decision.md](37-fullroom-training-decision.md). They are not in the stud-head train or val manifests.

Generator: `full_room_28`. Stud spacing 0.006 m, plate 0.010 m, floor 0.020 m, noise 0.001 m. Catalog: `artifacts/fullroom/scenes_expected.json`, written by `scripts/build_fullroom_scenes.py`. Each room built: 566,769 points, plan gap 0.1414 m.

Planted leans sit on interior slots (not the eight corner studs), about local +X. Unlisted studs are 0° with axis `none`. A 1° or 2° lean is interior-only so the stage-5 40 mm plan gap still holds.

## Expected color

Expected color is `dual_standard_passes` on the planted |lean| from vertical. That is the ground-truth plumb call: green if |lean| + ε ≤ τ, red if |lean| − ε > τ, yellow if the interval overlaps τ.

| Gauge | τ | ε absolute | ε sensor |
| --- | ---: | ---: | ---: |
| Handbook finish plumb | 0.11937° | 0° | 0.05° |
| NAHB warranty gauge | 0.67140° | 0° | 0.05° |

Experiment 1 colors |measured − truth| on a stud whose truth is 0°, so the plumb call and the error call are the same number there. On these rooms a perfect measure of a leaning stud is a red or yellow plumb call and a green error call. Phase 4 records both. **Catch rate uses the plumb call** against the counts below. The error call is not a supposed-red count.

## Counts

Handbook absolute red is the strict supposed-red count (ε = 0, so yellow does not occur). Scenes F and G/H are the two questions Oz named: 10 supposed-red and 1 supposed-red, on the Handbook gauge and on both gauges.

| Scene | Seed | Planted leans (interior) | Handbook abs red | Handbook sensor red | Handbook sensor yellow | NAHB abs red | NAHB sensor red | NAHB sensor yellow |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 1301 | 1 × 0.30° | 1 | 1 | 0 | 0 | 0 | 0 |
| B | 1302 | 2 × 0.30° | 2 | 2 | 0 | 0 | 0 | 0 |
| C | 1303 | 4 × 0.30° | 4 | 4 | 0 | 0 | 0 | 0 |
| D | 1304 | 6 × 0.50° | 6 | 6 | 0 | 0 | 0 | 0 |
| E | 1305 | 8 × 0.50° | 8 | 8 | 0 | 0 | 0 | 0 |
| F | 1306 | 10 × 0.30° | 10 | 10 | 0 | 0 | 0 | 0 |
| G | 1307 | 1 × 2.00° | 1 | 1 | 0 | 1 | 1 | 0 |
| H | 1308 | 10 × 1.00° | 10 | 10 | 0 | 10 | 10 | 0 |
| I | 1309 | 8 × 0.10°, 4 × 0.15°, 4 × 0.30° | 8 | 4 | 12 | 0 | 0 | 0 |
| J | 1310 | 6 × 0.67°, 2 × 2.00°, 8 × 0.05° | 8 | 8 | 0 | 2 | 2 | 6 |

Scene I: 0.10° is Handbook-green at ε = 0 and Handbook-yellow at ε = 0.05°. 0.15° is Handbook-red at ε = 0 and Handbook-yellow at ε = 0.05°. 0.30° is Handbook-red on both columns. All thirty stay NAHB-green.

Scene J: 0.67° is Handbook-red on both columns, NAHB-green at ε = 0 (0.67° ≤ 0.67140°), and NAHB-yellow at ε = 0.05°. 2.00° is red on both gauges and both columns. 0.05° is green on both, including the sensor column (0.10° ≤ 0.11937°).

The other studs in every room are 0°, green on both gauges and both columns.
