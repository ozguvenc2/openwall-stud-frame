# Phase 2 — painted outside wall-corner field method

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC**. Suite: **OpenWall**. Apps: **BeamWeaver** and **TruePlank**. This note is the TruePlank phase-2 pilot.

Phase 1 is the synthetic class-S one-stud lean sweep (`docs/research/19-phase1-s1-lean-sweep.md`). Phase 2 is a different object: a residential painted outside wall corner, not exposed studs. The question is plumb of two finished faces against a SKIL digital level. It is not stud detection, not a stud box, and not class F.

Device ε is unlocked. Production paint stays yellow. A green or red call is not made.

Machine-readable card: `artifacts/scorecards/phase2_wall_corner/scorecard.json`. Script: `scripts/run_phase2_wall_corner.py`. The PLY files are gitignored under `data/raw/polycam/` and are not in this commit.

## Protocol

1. Hold a SKIL digital level vertical on each outside face of the painted corner. Read the display at the top, the middle, and the bottom.
2. Display convention: about 90° is plumb. Lean from vertical is `|90 − reading|` degrees. The display step on these readings is 0.05°.
3. Capture the same corner with Polycam Custom, close, and export PLY. The file used here is `data/raw/polycam/wall_corner_2026-09-25.ply` (2,560,150 points, 69,124,261 bytes).
4. In the export frame, fit two dominant vertical planes and, if present, one floor plane. Open3D 0.20.0 plane RANSAC on a 4 mm voxel downsample (distance 10 mm, 2,500 iterations), then an SVD refit on full-resolution points within 10 mm of that plane. An earlier plane keeps its points, so the corner seam is not counted twice.
5. A plane is vertical when `|n_z| ≤ 0.34` and horizontal when `|n_z| ≥ 0.94`. Lean from vertical is `asin(|n · +Z|)` in degrees. Export +Z is the vertical for this pilot. The floor normal is recorded and is not the reference.
6. Split each wall’s inliers into three equal-count bands along Z and refit a plane in each band.
7. Do not assign a cloud plane to SKIL Face A or Face B. The close cloud is a corner patch. It does not contain the doorway or the cat tree.

The design-plan rule still applies: when bottom, middle, and top disagree by more than the display step, do not publish an angle MAE against the level. Both painted faces disagree by more than 0.05°, so this note does not publish that MAE. It publishes the level leans and the plane leans as separate measurements.

Open3D `segment_plane` is unseeded. A repeat on the same file can move the third decimal of a degree. The numbers below are the committed scorecard.

## SKIL baseline

| Face | Where | Height | Display ° | Lean from vertical ° |
| --- | --- | --- | --- | ---: |
| A | doorway / hall | Top | 89.95 | 0.05 |
| A | doorway / hall | Mid | 89.75 | 0.25 |
| A | doorway / hall | Bottom | 89.15 | 0.85 |
| A | doorway / hall | Mean |  | **0.383** |
| B | cat-tree / plant | Top | 89.85 | 0.15 |
| B | cat-tree / plant | Mid | 89.95 | 0.05 |
| B | cat-tree / plant | Bottom | 89.45 | 0.55 |
| B | cat-tree / plant | Mean |  | **0.250** |

Face A spans 0.80° from top to bottom. Face B spans 0.50°. Both spans are larger than the 0.05° display step, so each face is not one lean.

## Point-cloud size ladder

Space and room exports stay sparse. A close Custom export reaches millimeter spacing on finished paint. Paint is still not stud wood.

| Capture | File | Points | Bytes | Measured 1st-nn p50 | Measured 1st-nn p90 |
| --- | --- | ---: | ---: | ---: | ---: |
| Lot62 Loft Medium | `room_2026-09-25.ply` | 3940 | 106,588 (~105 KB) | 102 mm | 158 mm |
| Lot62 Loft High | `lot62_loft_2026-09-25_high.ply` | 9850 | 266,158 (~266 KB) | 65 mm | 111 mm |
| WallCorner Custom close | `wall_corner_2026-09-25.ply` | 2,560,150 | 69,124,261 (~66 MB) | 0.49 mm | 0.87 mm |

Loft medians use every point. The corner median uses 12,000 queries against the full tree. The medium loft is about 10 cm (the planning phrase was “tens of centimeters”; the p90 of 158 mm sits in that phrase). The high loft matches the planning figure of about 65 mm.

The corner’s raw neighbor median is 0.49 mm, finer than the planning figure of about 4 mm. The same cloud occupies **180,814** cells of a 4 mm voxel grid. That grid is the 4 mm scale: the Custom export places many samples inside one 4 mm cell. A stud-scale surface sample is present. The surface is paint.

Lot62 loft extent is about 4.45 m × 7.28 m × 2.55 m, with the floor near z = 0 and the ceiling near z = 2.45 m, so those exports are Z-up. The corner’s long axis is the same Z (extent 0.83 m × 0.87 m × 2.50 m).

## Cloud planes

Hardware: Oz_PC, Windows, Python 3.12.10, Open3D 0.20.0, NumPy 2.5.3. Runtime on this run: 4.0 s.

| Slot | Inliers | Lean from +Z | RMSE | Height-third leans (bottom, mid, top) |
| --- | ---: | ---: | ---: | --- |
| Plane 1 | 943,764 | 1.003° | 5.0 mm | 0.369°, 1.441°, 0.080° |
| Plane 2 | 849,543 | 0.763° | 3.4 mm | 1.044°, 0.865°, 0.423° |
| Floor candidate | 203,967 | 0.855° from horizontal | 2.0 mm | not a wall |

The angle between the two wall normals is **89.80°**. The corner edge is **1.259°** from +Z. The floor candidate sits at the low end of Z (center z ≈ −1.23 m). It is a patch of floor, not the plumb reference.

Lean of the same two wall normals against that floor normal, as a sensitivity only, is 1.787° and 1.110°. Those angles are farther from the SKIL means than the +Z leans. They are not the result.

## SKIL versus cloud

The planes are not registered to the faces. Sorting both pairs and subtracting is an unpaired magnitude check, not a face match.

| | Smaller | Larger |
| --- | ---: | ---: |
| SKIL face mean | 0.250° (Face B) | 0.383° (Face A) |
| Cloud plane lean | 0.763° (plane 2) | 1.003° (plane 1) |
| Absolute difference | 0.513° | 0.620° |

Both cloud leans are larger than both SKIL means. The gap is several times the 0.05° display step and several times τ ≈ 0.119°. Height thirds on the cloud also move by about a degree, in a pattern that is not the SKIL top-to-bottom pattern. A single plane cannot stand in for three level readings on a face that bows.

What this comparison does not support:

- a claim that the phone cloud reproduces the level
- an assignment of plane 1 to Face A or Face B
- a stud-axis error
- a locked ε, or any color other than yellow

## Limits

- Painted drywall is not stud wood. Class F is still a bare stud, a level on lumber, and the finders.
- Export +Z is the vertical used here. It is not a surveyed gravity vector paired to the level. A floor is not gravity.
- The level was a straightedge at three heights. The cloud answer is one plane plus three bands. They are different instruments on a surface that is not straight.
- RANSAC inliers can shift. Quote the scorecard, not a re-run that was not committed.
- No person, address, or photograph is in git. The cloud stayed on the machine.

## Next

Open framing. One bare stud, the same three level readings on the wood, the finders on that cloud, and yellow paint until ε is measured. Registering which physical face is which plane can wait until the capture shows a landmark that is also in the cloud. This corner does not do that.

Figures from this run, offline, under `artifacts/scorecards/phase2_wall_corner/`:

- `preview_views.png`
- `skil_vs_cloud_lean.png`
- `height_thirds.png`

Tables: `density_ladder.csv`, `planes.csv`, `skil_vs_cloud.csv`.
