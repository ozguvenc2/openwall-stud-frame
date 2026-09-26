# Oz_PC: SAM 2 rank 7 measured, and S1b on the classical ranks

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC** (RTX 4080 SUPER). Writer: **Other**.

Cloud PR [#26](https://github.com/ozguvenc2/openwall-stud-frame/pull/26) already ranks SAM 2 as bake-off rank 7 and scores Open3D through a synthetic room. This note is the Oz_PC continuation: one SAM 2 forward pass, and the S1b probes through Open3D, the PCL/NumPy cuboid, CloudCompare, and pyRANSAC-3D. Corner phase-2 (PRs #23–#25) is not a gate.

Device epsilon is unlocked. Production paint is yellow. A bow row's angle is the chord. The rigid bars on the day table are not a bow-amplitude error.

## SAM 2

Status: **ran**. 

Checkpoint: `facebook/sam2.1-hiera-tiny`. Device: NVIDIA GeForce RTX 4080 SUPER. Torch: 2.7.0+cu126.

Pixel agreement with the generator stud raster: intersection 8266, union 18201, ratio 0.4542. Ratio of this mask against generator stud pixels on this render. The generator raster is not a field label.

Lifted points: 8266. Part counts: `{"floor": 0, "plate": 0, "stud": 8266}`.

Scorecard: P=None R=0.0 section=None mm length=None mm MAE=None ° paint=[].

The shared stud gate kept this box: False. Extents mm: [44.78, 95.73, 1010.1]. Angle vs +Z: 0.07649°. Drop reasons: ['length 1.010 m outside 1.2–3.3 m'].

Minimal oriented box of the points lifted from this SAM 2 mask. The stud-length gate may still drop it, which leaves detection null. The network does not emit the box.

The image is the scaffold camera from `sam2_mask.default_stud_camera` on the one-stud 0.05° cloud. The prompt is the centroid of generator stud pixels. A pure LAS or PLY still skips this rank.

## S1b classical scorecards

| Rank | Scene | Status | Rigid bars | P | R | Section mm | Length mm | MAE ° | Paint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `s1b_bow_2x4_amp19.05mm_lean0.000` | ran | fail | null | 0 | null | null | null | null |
| 1 | `s1b_bow_2x4_amp6.35mm_lean0.000` | ran | fail | 1 | 1 | 13.35 | 5.98 | 0.00958 | yellow x1 |
| 1 | `s1b_bow_2x4_amp6.35mm_lean0.300` | ran | fail | 1 | 1 | 11.65 | 4.63 | 0.00684 | yellow x1 |
| 1 | `s1b_bow_wall_3` | ran | fail | 1 | 1 | 11.54 | 22.23 | 0.01325 | yellow x3 |
| 2 | `s1b_bow_2x4_amp19.05mm_lean0.000` | ran | fail | 1 | 1 | 23.9 | 4.48 | 0.04434 | yellow x1 |
| 2 | `s1b_bow_2x4_amp6.35mm_lean0.000` | ran | fail | 1 | 1 | 13.15 | 5.96 | 0.00847 | yellow x1 |
| 2 | `s1b_bow_2x4_amp6.35mm_lean0.300` | ran | fail | 1 | 1 | 11.14 | 4.63 | 0.00684 | yellow x1 |
| 2 | `s1b_bow_wall_3` | ran | fail | 1 | 0.3333 | 1511.5 | 83.71 | 0.08964 | yellow x1 |
| 3 | `s1b_bow_2x4_amp19.05mm_lean0.000` | ran | fail | 0.25 | 1 | 30.24 | 3.61 | 0.12807 | yellow x4 |
| 3 | `s1b_bow_2x4_amp6.35mm_lean0.000` | ran | fail | 0.125 | 1 | 30.63 | 4.63 | 0.1221 | yellow x8 |
| 3 | `s1b_bow_2x4_amp6.35mm_lean0.300` | ran | fail | 0.125 | 1 | 31.1 | 4.59 | 0.04542 | yellow x8 |
| 3 | `s1b_bow_wall_3` | ran | fail | 0.1765 | 1 | 31.13 | 7.72 | 0.03796 | yellow x17 |
| 6 | `s1b_bow_2x4_amp19.05mm_lean0.000` | ran | fail | null | 0 | null | null | null | null |
| 6 | `s1b_bow_2x4_amp6.35mm_lean0.000` | ran | fail | 1 | 1 | 13.35 | 5.98 | 0.00958 | yellow x1 |
| 6 | `s1b_bow_2x4_amp6.35mm_lean0.300` | ran | fail | 1 | 1 | 11.65 | 4.63 | 0.00684 | yellow x1 |
| 6 | `s1b_bow_wall_3` | ran | fail | null | 0 | null | null | null | null |

Open3D on these four scenes was already measured on the cloud curriculum. The rows above are the same generator calls on Oz_PC, plus ranks 2, 3, and 6. Rank 3 is one box per RANSAC primitive, not the tuned face merge on PR #22.

Synthetic tests measure lean against the fitted floor normal when the scene has a floor or slab, and against generator +Z only when it does not. They do not use a SKIL or any other level reading. The three floorless S1b studs stay on generator +Z. `s1b_bow_wall_3` has a floor, so its reference is `floor_normal`.

Rank 2 is the in-process NumPy smoothness port. `native_pcl_region_growing` is false on these cards. The libpcl binary was not built, so these numbers are not a PCL measurement.

This script does not re-score the room. Ranks 1–7 on `stage5_room_bay_lot62_look` are the Oz_PC cards in doc 24.

