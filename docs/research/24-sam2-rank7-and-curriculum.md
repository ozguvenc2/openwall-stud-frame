# SAM 2 as rank 7, and the curriculum through a synthetic room

Date: **2026-09-25**. TruePlank is the app. OpenWall is the suite. The package is `openwall_stud`. Device ε is unlocked. Production paint is yellow.

This note does two things. It adds **SAM 2 as bake-off rank 7**, separate from ranks 1–6. It records a class-S continuation of the stage ladder in [12-stud-seg-design-plan.md](12-stud-seg-design-plan.md) through a synthetic room. It does not rewrite the corner experiment into that ladder.

Synthetic tests measure lean against the fitted floor normal when the scene has a floor or slab, and against generator +Z only when it does not. They do not use a SKIL or any other level reading.

Machine-readable scorecards: `artifacts/scorecards/curriculum/`. Summary: `artifacts/scorecards/curriculum/summary.json`. The day table picked up the new rows.

## Parallel, not a gate

The painted-corner pilot and the synthetic neural corner stay beside this ladder.

| PR | What it is | What it is not |
| --- | --- | --- |
| [#23](https://github.com/ozguvenc2/openwall-stud-frame/pull/23) | Synthetic outside corner for ranks 4 and 5. Planes, not studs. | Not stage 5. Not a pass bar for the room. |
| [#24](https://github.com/ozguvenc2/openwall-stud-frame/pull/24) | Phase-2 field corner (Polycam) plus a synthetic corner. Includes a Lot 62 loft density ladder. | Not this generator. Not class-F stud QA. |

Those branches are not merged here. A synthetic room does not close them, and they do not block stages 0–5. PR [#25](https://github.com/ozguvenc2/openwall-stud-frame/pull/25) stays a parallel field note: floor-up widened the SKIL gap on that painted corner. This note does not tell the field protocol to ignore that finding. The synthetic room still uses the fitted floor normal.

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

Stage 0 and the original stage-2 and stage-3 Open3D cards were linked and checked against the existing bars. They still pass. The floor-normal lock re-run kept their angle, section, and length. Paths:

- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.000.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.050.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean0.120.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x4_lean4.000.json`
- `artifacts/scorecards/open3d_stage0_stage0_2x6_lean0.300.json`
- `artifacts/scorecards/open3d_stage2_stage2_2x4_lean0.200.json`
- `artifacts/scorecards/open3d_stage3_stage3_mini_wall_4.json`

New scenes other than the room were generated and scored with rank 1 only (Open3D 0.20, CPU). Script: `scripts/run_curriculum_through_room.py`. The room was scored on Oz_PC with ranks 1–7. Script: `scripts/run_room_all_ranks.py`.

**Gate** means the scene uses the stage bars already in the design plan (1 mm noise, rigid studs). **Probe** means the card is kept either way. Stage 5 has no numeric bar in the design plan. A day-table `pass` on the room means one box per generator stud and yellow paint. It is not a field acceptance test.

### Gates that passed

Reference is the floor normal. Paint is yellow. ε is unlocked. Percent in band is 100 on each of these rows (band τ ≈ 0.11937°). A later pass locked that reference in the scorer and rewrote the JSON. Angle, section, and length in this table did not move. `runtime_s` in the scorecard is that later process.

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

**Full room, ranks 1–7, Oz_PC (RTX 4080 SUPER).** A lean scored on the full cloud uses the fitted floor normal. ε is unlocked. Yellow is recorded only where a box was kept. A day-table `pass` means precision 1, recall 1, and yellow paint. It is not a field acceptance test.

| Rank | Stack | Day row | P / R | Section (mm) | Length (mm) | MAE (°) | Max (°) | Paint | Runtime (s) | Reference |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | Open3D | pass | 1 / 1 (26/26) | 7.93 | 22.12 | 0.01134 | 0.04230 | yellow ×26 | 0.8955 | `floor_normal` |
| 2 | NumPy region-grow cuboid | fail | 0 / 0 (1 false positive) | — | — | — | — | yellow ×1 | 14.7016 | `floor_normal` |
| 3 | CloudCompare RANSAC-SD, untuned | fail | 0.2737 / 1 (26 tp, 69 fp) | 31.63 | 61.33 | 0.04529 | 0.15542 | yellow ×95 | 2.5988 | `floor_normal` |
| 4 | Pointcept PTv3, BIMStruct3D | control | — | — | — | — | — | — | 94.0376 | `floor_normal` |
| 5 | Open3D-ML RandLA-Net, S3DIS | control | — | — | — | — | — | — | 1.5528 | `floor_normal` |
| 6 | pyRANSAC-3D 0.7.0 | fail | — / 0 (0 boxes) | — | — | — | — | — | 18.3118 | `floor_normal` |
| 7 | SAM 2.1 hiera-tiny, one view | fail | — / 0 (0 boxes) | — | — | — | — | — | 4.2568 | `gravity_z_no_floor_plane` on the lift |

Rank 1 percent in band is 100. The first write-up recorded 1.9151 s, and the floor-normal lock re-run stored 0.9466 s. This pass stored 0.8955 s. Angle, section, and length are the same figures. They sit inside the stage-3 bring-up checks (section ≤ 10 mm, length ≤ 30 mm, angle ≤ 0.10°, recall 1). The design plan still has **no numeric bar for stage 5**. The room does not unlock Pointcept training. Card: `artifacts/scorecards/curriculum/open3d_stage5_room_bay_lot62_look.json`.

Rank 2 is the in-process NumPy port. The PCL binary did not build, so `native_pcl_region_growing` is false and these numbers are not a libpcl measurement. The grow returned 90 face clusters. The 20 mm adjacency step merged 89 of them, because the plates connect the studs, and left one member. That box is one false positive. Section, length, and angle stay null.

Rank 3 is CloudCompare 2.14.beta. Each RANSAC-SD primitive is its own box. Primitives are not merged into a stud. Recall is 1. Precision is 0.2737 (95 boxes). Percent in band on the matched studs is 96.15. The extra boxes fail the day-table pass.

Rank 4 ran with CUDA torch 2.7.0+cu126. The BIMStruct3D classes are clutter, floor, ceiling, wall, column, door, window, stairs, railing, and lights. None is a stud. Counts on this cloud: clutter 448,396, floor 79,300, railing 4,566, wall 39. No stud box and no paint. The histogram is the measurement. Weights are CC BY-NC-SA 4.0 and are not committed. PointGroup did not run.

Rank 5 ran in the torch 2.13 interpreter that imports `open3d.ml.torch`. S3DIS names have no stud. Counts: window 314,597, door 139,612, floor 50,390, clutter 27,348, wall 354. S3DIS mIoU was not copied. No stud box and no paint.

Rank 6 wall-swallowed. The first cuboid was 2480.9 × 2885.8 × 2886.6 mm, which is past the single-stud extent check. That cuboid was rejected and sequential fitting stopped. Recall is 0. The scored angle stays null. The card still names the floor normal as the reference for this cloud.

Rank 7 is one pinhole south of the bay (768 × 512, 60° vertical field, eye near (1.23, −2.60, 1.18) m, target at the room center). `facebook/sam2.1-hiera-tiny` loaded as `transformers.Sam2Model` on CUDA. The prompt is the centroid of generator stud pixels on that render, not a field click. The mask covers 1,184 pixels against 79,434 generator stud pixels (intersection 781, ratio 0.0098). The chosen mask score is 0.829. The lift is 781 stud points and no floor or plate points. A visible box of those points is 38.00 × 90.54 × 2337.34 mm at 0.0308° against +Z, and that span would pass the stud-length gate. The shared DBSCAN prior kept no box, so recall is 0 and the scored angle is null. The lift has no floor part, so this card’s angle reference is generator +Z. That is the rule for a cloud with no floor. It is not a level reading, and one mask is not 26 studs. Images: `artifacts/scorecards/curriculum/sam2_room_prompt.png` and `sam2_room_mask.png`.

### Stages 6 and 7

Stub cards only, one per rank, metrics null. Stage 6 needs a real single-story capture. Stage 7 needs a real two-story or complex frame. The synthetic room is not either stage.

## What this note refuses

- Reading the SAM 2 pixel ratio, the visible span, or the network runtime as stud detection. One mask is not 26 studs.
- Copying a Pointcept or S3DIS histogram into a stud MAE or a paint color.
- Green or red paint. ε is unlocked.
- Calling the 2 mm miss or the bow misses a pass.
- Treating the synthetic room as the Lot 62 scan, as class F, or as the gate that lets ranks 4 and 5 train.
- Folding PR #23, PR #24, or PR #25 into the stage list.
- Inventing stage 6 or stage 7 metrics. Those cards stay null until a real whole-frame capture exists.
