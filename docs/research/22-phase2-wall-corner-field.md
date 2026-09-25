# Phase 2 — painted outside wall-corner field method

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC**. Suite: **OpenWall**. Apps: **BeamWeaver** and **TruePlank**. This note is the TruePlank phase-2 pilot.

Phase 1 is the synthetic class-S one-stud lean sweep (`docs/research/19-phase1-s1-lean-sweep.md`). Phase 2 is a different object: a residential painted outside wall corner, not exposed studs. The question is plumb of two finished faces against a SKIL digital level. It is not stud detection, not a stud box, and not class F.

Device ε is unlocked. Production paint stays yellow. A green or red call is not made.

Machine-readable cards: `artifacts/scorecards/phase2_wall_corner/scorecard.json` and `floor_gravity.json`. Script: `scripts/run_phase2_wall_corner.py`. The PLY files are gitignored under `data/raw/polycam/` and are not in this commit.

## Protocol

1. Hold a SKIL digital level vertical on each outside face of the painted corner. Read the display at the top, the middle, and the bottom.
2. Display convention: about 90° is plumb. Lean from vertical is `|90 − reading|` degrees. The display step on these readings is 0.05°.
3. Capture the same corner with Polycam Custom, close, and export PLY. The file used here is `data/raw/polycam/wall_corner_2026-09-25.ply` (2,560,150 points, 69,124,261 bytes).
4. Fit two dominant vertical planes in the export frame. Open3D 0.20.0 plane RANSAC on a 4 mm voxel downsample (distance 10 mm, 2,500 iterations), then an SVD refit on full-resolution points within 10 mm of that plane. An earlier plane keeps its points, so the corner seam is not counted twice. A plane is vertical when `|n_z| ≤ 0.34`.
5. Fit the floor on the lower horizontal points. Keep the bottom 80 mm of export Z, voxel-downsample at 4 mm, and estimate normals in a 30 mm radius. Keep points with `|n_z| ≥ 0.94`. Take the lowest z-group of those points (gap 20 mm). Run Open3D plane RANSAC at 5 mm (4,000 iterations), then an SVD refit within 5 mm on full-resolution points in that slab. Points already on either wall stay off the floor. Flip the normal so it points from the floor center toward the mean of the two wall centers. That direction is into the room and away from the floor. On this Z-up export the flipped normal has positive z.
6. Lean from plumb is `arcsin(|n_wall · u|)` in degrees. The before column uses `u = export +Z`. The after column, which is the result, uses `u` = the floor normal. Zero means the wall normal lies in the horizontal plane perpendicular to `u`, so the plumb line lies in the wall. The same number is the angle between the wall normal and that horizontal plane. It is the wall-plane form of the stud rule in `docs/research/11-stud-segmentation-algorithm-ranking.md`: a long axis parallel to the stored up vector is plumb, and a wall normal perpendicular to that up vector is plumb.
7. Split each wall’s inliers into three equal-count bands along the up vector of that column and refit a plane in each band. The result bands run along the floor normal.
8. Do not assign a cloud plane to SKIL Face A or Face B. The close cloud is a corner patch. It does not contain the doorway or the cat tree.

The design-plan rule still applies: when bottom, middle, and top disagree by more than the display step, do not publish an angle MAE against the level. Both painted faces disagree by more than 0.05°, so this note does not publish that MAE. It publishes the level leans and the plane leans as separate measurements.

Open3D `segment_plane` is unseeded. A repeat can move the third decimal of a degree. The previous card, which treated export +Z as the reference, reported 1.003° and 0.763°. This run’s export-+Z leans on the refit planes are 1.005° and 0.763°. The before/after table uses this run, so both columns share the wall planes. The numbers below are this scorecard.

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

Hardware: Oz_PC, Windows, Python 3.12.10, Open3D 0.20.0, NumPy 2.5.3. Runtime on this run: 4.3 s.

The floor slab used as up has 201,263 inliers, RMSE 1.6 mm, and an in-plane extent of 0.76 m × 0.66 m. Its normal is 0.712° from export +Z. The normal points into the room.

| Slot | Inliers | Lean from export +Z (before) | Lean from floor normal (after) | RMSE |
| --- | ---: | ---: | ---: | ---: |
| Plane 1 | 941,452 | 1.005° | **1.685°** | 5.0 mm |
| Plane 2 | 848,857 | 0.763° | **0.976°** | 3.4 mm |

Height thirds along the floor normal, lean from that normal (bottom, mid, top):

| Slot | Bottom | Mid | Top |
| --- | ---: | ---: | ---: |
| Plane 1 | 1.043° | 2.162° | 0.762° |
| Plane 2 | 1.260° | 1.075° | 0.638° |

The angle between the two wall normals is **89.72°**. The corner edge is **1.259°** from export +Z and **1.943°** from the floor normal.

Two other floor fits are recorded and are not the result. The 10 mm sequential plane from the wall pass (207,531 inliers, 0.849° from export horizontal) gives wall leans of 1.786° and 1.100°. Dropping primary-floor points within 50 mm of either wall and refitting (149,747 inliers, 0.824° from export horizontal) gives 1.777° and 1.056°. The floor choice moves each lean by about a tenth of a degree.

## SKIL versus cloud

The planes are not registered to the faces. Sorting both pairs and subtracting is an unpaired magnitude check, not a face match. SKIL means are leans from the level’s plumb, which is gravity. The cloud columns are the two choices of `u` on the same wall planes.

| | Smaller | Larger |
| --- | ---: | ---: |
| SKIL face mean | 0.250° (Face B) | 0.383° (Face A) |
| Cloud, export +Z | 0.763° (plane 2) | 1.005° (plane 1) |
| Absolute difference, export +Z | 0.513° | 0.622° |
| Cloud, floor normal | 0.976° (plane 2) | 1.685° (plane 1) |
| Absolute difference, floor normal | 0.726° | 1.302° |

Both floor-normal leans are larger than both SKIL means, and both are larger than the export-+Z leans of the same planes. The unpaired gaps grow. The gap is several times the 0.05° display step and several times τ ≈ 0.119°. Height thirds along the floor normal still move by about a degree, and they do not follow the SKIL top-to-bottom pattern (Face A rises toward the bottom; Face B is smallest in the middle). A single plane cannot stand in for three level readings on a face that bows.

What this comparison does not support:

- a claim that the phone cloud reproduces the level
- a claim that the floor normal is gravity, or that it closed the gap to the SKIL
- an assignment of plane 1 to Face A or Face B
- a stud-axis error
- a locked ε, or any color other than yellow

## Limits

- Painted drywall is not stud wood. Class F is still a bare stud, a level on lumber, and the finders.
- The floor normal is the up proxy for the result. It is not a surveyed gravity vector paired to the level. SKIL reads gravity. A floor that is not level is not gravity. This patch sits 0.712° off export horizontal, and that tilt is what moves the wall leans from 1.005° / 0.763° to 1.685° / 0.976°.
- Carpet and baseboard. The horizontal-normal test and the 5 mm distance are there so a vertical baseboard does not own the plane. The surface is still carpet: RMSE 1.6 mm, about 16 mm thick in Z. The two sensitivity fits above move the leans by about 0.1°, which is larger than the 0.05° display step.
- Short floor patch. The in-plane extent is 0.76 m × 0.66 m in the corner, not a room slab. A local slope on that patch is not building level.
- The level was a straightedge at three heights. The cloud answer is one plane plus three bands. They are different instruments on a surface that is not straight.
- RANSAC inliers can shift. Quote the scorecard, not a re-run that was not committed.
- No person, address, or photograph is in git. The cloud stayed on the machine.

## Next

Open framing. One bare stud, the same three level readings on the wood, the finders on that cloud, and yellow paint until ε is measured. Registering which physical face is which plane can wait until the capture shows a landmark that is also in the cloud. This corner does not do that.

Figures from this run, offline, under `artifacts/scorecards/phase2_wall_corner/`:

- `preview_views.png`
- `skil_vs_cloud_lean.png`
- `height_thirds.png`

Tables: `density_ladder.csv`, `planes.csv`, `skil_vs_cloud.csv`. The before/after card is `floor_gravity.json`.
