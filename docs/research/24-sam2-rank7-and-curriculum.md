# SAM 2 as rank 7, and the curriculum through a synthetic room

Date: **2026-09-25**. TruePlank is the app. OpenWall is the suite. The package is `openwall_stud`. Device ε is unlocked. Production paint is yellow.

This note does two things. It adds **SAM 2 as bake-off rank 7**, separate from ranks 1–6. It records a class-S continuation of the stage ladder in [12-stud-seg-design-plan.md](12-stud-seg-design-plan.md) through a synthetic room. It does not rewrite the corner experiment into that ladder.

Machine-readable scorecards: `artifacts/scorecards/curriculum/`. Summary: `artifacts/scorecards/curriculum/summary.json`. The day table picked up the new rows.

## Parallel, not a gate

The painted-corner pilot and the synthetic neural corner stay beside this ladder.

| PR | What it is | What it is not |
| --- | --- | --- |
| [#23](https://github.com/ozguvenc2/openwall-stud-frame/pull/23) | Synthetic outside corner for ranks 4 and 5. Planes, not studs. | Not stage 5. Not a pass bar for the room. |
| [#24](https://github.com/ozguvenc2/openwall-stud-frame/pull/24) | Phase-2 field corner (Polycam) plus a synthetic corner. Includes a Lot 62 loft density ladder. | Not this generator. Not class-F stud QA. |

Those branches are not merged here. A synthetic room does not close them, and they do not block stages 0–5.

## Bake-off rank 7 is SAM 2

Ranks 1–6 stay as already used in phase 1:

| Bake-off rank | Stack |
| --- | --- |
| 1 | Refined Open3D |
| 2 | PCL / NumPy region-grow cuboid |
| 3 | CloudCompare RANSAC shape detection |
| 4 | Pointcept / PTv3 |
| 5 | Open3D-ML RandLA-Net |
| 6 | pyRANSAC-3D v0.7.0 sequential cuboid |

Rank 7 is [SAM 2](https://arxiv.org/abs/2408.00714) (Ravi et al., 2024), a promptable segmenter for images and video. It is a separate test. It is not a seventh point-cloud backbone.

The master table in [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md) is unchanged. Row 6 there is still Chen, Jiang, and Xiong 2025. Row 7 there is still ClearEdge3D EdgeWise. Those rows are not this bake-off. The same split already exists for pyRANSAC-3D versus master-table row 6.

### How a mask would meet a stud cloud

SAM 2 does not read LAS or PLY. The path, when a capture already has a registered camera, is:

1. Project the cloud through that camera. A depth view, an RGB view, or several registered views are the image. A bare cloud with no pose skips the rank.
2. SAM 2 returns a mask on the image. This repository does not prompt it with a hand click in the runs below, and it did not run the network.
3. Points whose projection lands in the mask, and that are the visible surface, are the candidate stud.
4. Those points go to the shared box, the angle against the stored reference, and `openwall_stud.paint`. ε stays unlocked, so the color stays yellow.

A multi-view set would be several such lifts, unioned per stud, then one box. One view hides the far faces and can miss the stud ends. That limit showed up in the control below. It is not a SAM 2 accuracy.

Code: `openwall_stud.contenders.sam2_mask`. Command: `python -m openwall_stud.contenders.sam2_mask`. The curriculum script calls the same functions.

### What this process ran

This VM had no NVIDIA GPU (`nvidia-smi` absent), no PyTorch, and no `sam2` install. `SAM2_CHECKPOINT` was unset. The rank-7 card is `blocked_install`. Stud precision, recall, section, length, and angle on that card are null. No mask IoU was computed.

Oz_PC later ran the tiny checkpoint on an RTX 4080 SUPER. That measurement is [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md). It does not change the null card above.

What did run is the pinhole raster of one synthetic 2×4 (lean 0.05° about +X, seed 2, 25,666 points), the same stud as the one-stud protocol.

| Projection fact | Value |
| --- | --- |
| Image | 640 × 480, vertical field 42° |
| Eye (m) | (0.55, −1.15, 1.15), looking at (0, 0, 1.22), up +Z |
| Focal length (px) | 625.22 |
| Points inside the image | 10,214 |
| Occupied pixels | 8,269, all generator stud (the scene has no floor) |
| False-color PNG | `artifacts/scorecards/curriculum/sam2_projection_stage0_partids.png` |

Pixel colors in that PNG are part ids. They are not the green / yellow / red paint.

### Generator-mask control (not SAM 2)

The z-buffer’s stud pixels were lifted and passed to the shared Open3D box. Status on the card is `control`.

| | |
| --- | --- |
| Lifted points | 8,269 of 25,666 |
| Kept stud boxes | 0 (recall 0) |
| Visible minimal box | 44.78 × 95.73 × 1010.1 mm |
| Angle of that box vs +Z | 0.07649° |
| Z span of lifted points | 0.7286 m to 1.7386 m |
| Why the gate dropped it | Length 1.010 m is outside 1.2–3.3 m |

The section would have been called a 2×4. The camera never sees the stud ends, so the length gate refuses the box. A second view, or a mask that covered the full height, is still unmeasured. Card: `artifacts/scorecards/curriculum/sam2_generator_mask_control.json`.

## Curriculum

Stage 0 and the original stage-2 and stage-3 Open3D cards were linked and checked against the existing bars. They still pass. They were not re-measured. Paths:

- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.000.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.050.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.120.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean4.000.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x6_lean0.300.json`
- `artifacts/scorecards/open3d_stage2_stage2_2x4_lean0.200.json`
- `artifacts/scorecards/open3d_stage3_stage3_mini_wall_4.json`

New scenes were generated and scored with rank 1 only (Open3D 0.20, CPU). Script: `scripts/run_curriculum_through_room.py`.

**Gate** means the scene uses the stage bars already in the design plan (1 mm noise, rigid studs). **Probe** means the card is kept either way. Stage 5 has no numeric bar in the design plan. A day-table `pass` on the room means one box per generator stud and yellow paint. It is not a field acceptance test.

### Gates that passed

Reference is the floor normal. Paint is yellow. ε is unlocked. Percent in band is 100 on each of these rows (band τ ≈ 0.11937°).

| Scene | Studs | P / R | Section (mm) | Length (mm) | MAE (°) | Max (°) | Runtime (s) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Stage 2, lean 0° | 1 | 1 / 1 | 7.11 | 6.76 | 0.02551 | 0.02551 | 0.2184 |
| Stage 2, lean 0.12° | 1 | 1 / 1 | 7.67 | 6.96 | 0.01788 | 0.01788 | 0.1346 |
| Stage 2, lean 1° | 1 | 1 / 1 | 7.07 | 6.39 | 0.01714 | 0.01714 | 0.1373 |
| Stage 3, 3 studs, leans 0 / 0.12 / 4° | 3 | 1 / 1 | 8.71 | 27.47 | 0.01680 | 0.03139 | 0.3639 |
| Stage 3, 5 studs, default leans | 5 | 1 / 1 | 7.85 | 22.66 | 0.01846 | 0.03838 | 0.6085 |
| Stage 3, 4 studs, leans 0.05 / 0.15 / 0.30 / 1° | 4 | 1 / 1 | 7.55 | 24.31 | 0.01928 | 0.03317 | 0.4779 |

The original stage-2 card (lean 0.20°, section 7.84 mm, length 8.16 mm, MAE 0.01721°) and the original four-stud wall remain the 2026-09-24 rows. Together with the three new stage-2 leans, stage 2 is not a single scene. Together with the 3-stud and 5-stud walls, stage 3 covers the 3–5 stud band at 1 mm noise.

### Probes that did not clear the straight-stud bars

| Scene | What happened |
| --- | --- |
| Stage 3, four studs, **2 mm** noise, seed 32 | Precision 1, recall **0.25**. One box kept, section error 14.88 mm, length 24.7 mm, MAE 0.03765°. The same `run_baseline` built four DBSCAN clusters (about 25,100 points each), so the bays did not merge. Extents were about 53.2 × 102.6 × 2411.9 mm, 53.8 × 102.8 × 2412.6 mm, 52.1 × 103.8 × 2413.7 mm, and 55.5 × 102.8 × 2415.4 mm. Three fail the 15 mm section gate. The kept box is the one inside that gate and outside the 10 mm score bar. |
| S1b, bow 6.35 mm, lean 0° | One box. Section error **13.35 mm** (over the 10 mm bar). Length 5.98 mm. Chord MAE 0.00958°. |
| S1b, bow 6.35 mm, chord lean 0.30° | One box. Section error **11.65 mm**. Length 4.63 mm. Chord MAE 0.00684°. |
| S1b, bow **19.05 mm**, lean 0° | No kept box (recall 0). One DBSCAN cluster of all 25,666 points, minimal box **45.9 × 113.2 × 2442.9 mm**. Width versus 88.9 mm is outside the 15 mm section gate, so the scorecard geometry is null. |
| S1b wall, 3 studs, middle bow 6.35 mm | Three boxes, recall 1. Section error **11.54 mm** (the bow). Length 22.23 mm. MAE 0.01325°, max 0.02345°. |

S1b holds the ends and moves the midspan on a parabola. The stored truth axis is the chord. A straight minimal box follows that chord closely on the 6.35 mm bows and then fails the section bar, because the bow is inside the box. At 19.05 mm the box is dropped before an angle is stored. None of these rows is a bow measurement. The algorithm does not report midspan offset.

### Stage 5 synthetic room (LOT-62 look)

Scene `stage5_room_bay_lot62_look`, seed 62. Four walls, 16 inch centers, dressed 2×4, plates, floor. South wall omits the studs whose centers fall between x = 0.60 m and 1.55 m (five south studs kept, 26 studs in all). There is no door-height header: rank 1 peels a global Z slab, and a header band would cut every stud. Corner studs do not touch. The clear air is 0.10 m before lean; the generator’s minimum plan gap after lean-tip inflation is 0.123 m, above the 25 mm DBSCAN `eps`. A real corner is tight. This scene does not claim that joint.

Stud spacing is 6 mm. Plates are 10 mm. The floor is 20 mm. Noise is 1 mm. That is coarser than the 5 mm stage-0 faces, and it is the spacing this room was scored at.

This is not the Lot 62 Polycam loft. That file, and its density ladder, stay on PR #24.

| | Rank 1 (Open3D) |
| --- | --- |
| Points | 532,301 |
| Studs | 26 true, 26 predicted |
| Precision / recall | 1 / 1 |
| Max section error | 7.93 mm |
| Max length error | 22.12 mm |
| MAE | 0.01134° |
| Max absolute angle error | 0.04230° |
| Percent in band | 100 |
| Reference | Floor normal. The cloud was not rotated. |
| Paint | Yellow on all 26. ε unlocked. |
| Runtime | 1.9151 s, CPU, this process |

Compared with the stage-3 bring-up checks (section ≤ 10 mm, length ≤ 30 mm, angle ≤ 0.10°, recall 1), these figures sit inside those checks. The design plan still has **no numeric bar for stage 5**. The synthetic room does not unlock Pointcept training. Training still waits on a real capture with stud labels. Card: `artifacts/scorecards/curriculum/open3d_stage5_room_bay_lot62_look.json`.

Ranks 2–6 and rank 7 on this room are `not_run`. Null metrics. Ranks 4 and 5 were not given a forward pass here (no GPU weights), so those rows are not `control`.

### Stages 6 and 7

Stub cards only, one per rank, metrics null. Stage 6 needs a real single-story capture. Stage 7 needs a real two-story or complex frame. The synthetic room is not either stage.

## What this note refuses

- A SAM 2 mask IoU, a stud score, or a runtime for the network.
- Green or red paint. ε is unlocked.
- Calling the 2 mm miss or the bow misses a pass.
- Treating the synthetic room as the Lot 62 scan, as class F, or as the gate that lets ranks 4 and 5 train.
- Folding PR #23 or PR #24 into the stage list.
