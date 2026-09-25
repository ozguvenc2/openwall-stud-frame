# Figure captions

No new images were rendered for this draft. Existing algorithm pictures stay in [`docs/research/images/algo-contenders/`](../../../docs/research/images/algo-contenders/). They were produced by `scripts/render_algo_figures.py` on 2026-09-24. Credit that script and [`docs/research/images/algo-contenders/INDEX.md`](../../../docs/research/images/algo-contenders/INDEX.md). Do not crop the scaffold banner off ranks 2–5.

Numbers drawn on the rank-1 figures are the synthetic scorecards. They are not a field accuracy.

## Placeholders (not drawn)

### Figure 1. Pipeline block diagram

**Status: caption only.**

Horizontal-slab peel, DBSCAN, minimal oriented box, angle against the stored reference, paint. Show ε unlocked as a yellow output. Show the floor normal and generator +Z as two labeled reference choices. Do not draw a green/red example as the production path.

### Figure 2. Error-budget stack

**Status: caption only.**

Three empty columns: level, LiDAR, algorithm. Caption should say the cells are unfilled. Do not illustrate the stack with the 0.05° placeholder as if it were a measured band.

### Figure 3. Claim-class diagram

**Status: caption only.**

Class S (synthetic generator, run), class R (realisticized sensor model, not defined), class F (experimental level or total station, not collected). Arrows from class S do not land on a field claim.

## Existing images, credited

### Figure 4. Synthetic stage 0, Open3D

**File:** [`docs/research/images/algo-contenders/01-open3d-stage0.png`](../../../docs/research/images/algo-contenders/01-open3d-stage0.png)

**Credit:** `scripts/render_algo_figures.py`, 2026-09-24, rank-1 redraw of a real stage-0 run.

One synthetic 2×4 at a 4° generator lean, minimal oriented box, long axis, and the five stage-0 scorecard rows. Production paint is yellow. The last table column is a placeholder ε of 0.05°, not a device band.

### Figure 5. Synthetic stage 3, Open3D

**File:** [`docs/research/images/algo-contenders/01-open3d-stage3-miniwall.png`](../../../docs/research/images/algo-contenders/01-open3d-stage3-miniwall.png)

**Credit:** same script and date.

Four synthetic studs at 16 inch centers. Gray points are the floor and plates the peeler removed. Four boxes, no merged bay. Angle labels are that run’s measured θ versus the floor normal. Synthetic only.

### Figures 6–9. Contender scaffolds

These are diagrams with a scaffold banner. The wall in the corner is the synthetic stage-3 **input**, not that stack’s output. PCL, CloudCompare, Pointcept, and Open3D-ML were not executed.

| Figure | File | Credit line to keep on the figure |
| --- | --- | --- |
| 6 | [`02-pcl-region-grow-scaffold.png`](../../../docs/research/images/algo-contenders/02-pcl-region-grow-scaffold.png) | Scaffold. PCL was not executed. Region growing, a non-linear split, and a cuboid; Bassier coplanar merge crossed out. |
| 7 | [`03-cloudcompare-ransac-scaffold.png`](../../../docs/research/images/algo-contenders/03-cloudcompare-ransac-scaffold.png) | Scaffold. CloudCompare was not run. Schnabel primitives. A wall of studs is not one plane. |
| 8 | [`04-pointcept-ptv3-scaffold.png`](../../../docs/research/images/algo-contenders/04-pointcept-ptv3-scaffold.png) | Scaffold. No training and no weights. Hook waits for labeled stage 5. |
| 9 | [`05-open3d-ml-s3dis-scaffold.png`](../../../docs/research/images/algo-contenders/05-open3d-ml-s3dis-scaffold.png) | Scaffold. No forward pass. S3DIS office classes are not studs. |

## Regeneration

From the repository root, after Open3D is installed:

```bash
python scripts/render_algo_figures.py
```

If a figure is regenerated, update this caption with the date and say whether the pixels are a new run or a copy of the 2026-09-24 file.
