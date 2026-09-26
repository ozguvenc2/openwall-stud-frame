# Algorithm contender figures

Research date: **2026-09-24**. These are the pictures for the top five in [11-stud-segmentation-algorithm-ranking.md](../../11-stud-segmentation-algorithm-ranking.md). The design plan is [12-stud-seg-design-plan.md](../../12-stud-seg-design-plan.md).

**Reclassification (2026-09-26).** Live buckets are [27-four-way-tool-classification.md](../../27-four-way-tool-classification.md). The rank-3 PNG is still the 2026-09-24 scaffold: that drawing did not execute CloudCompare. Later measurements did run and stay in the day table. Former bake-off rank 3 = CloudCompare, now bucket 4 (interactive GUI), not a geometry-first automated finder.

Regenerate with `python scripts/render_algo_figures.py` from the repo root after `pip install -r requirements.txt`. Rank 1 is redrawn from the Open3D baseline. Ranks 2–5 are scaffold diagrams and stay labeled that way until those stacks actually run.

| Rank | File | What you are looking at |
| --- | --- | --- |
| 1 | [01-open3d-stage0.png](01-open3d-stage0.png) | Real Stage 0 run. One synthetic 2×4 at a 4° generator lean, minimal oriented box, long axis, and the five Stage 0 scorecard rows. Production paint is yellow. The last table column is a placeholder ε of 0.05°, not a device band. |
| 1 | [01-open3d-stage3-miniwall.png](01-open3d-stage3-miniwall.png) | Real Stage 3 run. Four studs at 16 inch centers. Gray points are the floor and plates the peeler removed. Four boxes, no merged bay. Angle labels are this run’s measured θ versus the floor normal. |
| 2 | [02-pcl-region-grow-scaffold.png](02-pcl-region-grow-scaffold.png) | Scaffold / illustrative. PCL was not executed. Steps are region growing, a non-linear split, and a cuboid, with Bassier coplanar merge crossed out. The wall in the corner is the synthetic Stage 3 input, not a PCL result. |
| 3 | [03-cloudcompare-ransac-scaffold.png](03-cloudcompare-ransac-scaffold.png) | Scaffold / illustrative. CloudCompare and CloudComPy were not run. Schnabel primitives, and the warning that a wall of studs is not one plane. |
| 4 | [04-pointcept-ptv3-scaffold.png](04-pointcept-ptv3-scaffold.png) | Scaffold / illustrative. No training and no weights. The hook waits for labeled Stage 5. BIMStruct3D is a control, not a stud model. |
| 5 | [05-open3d-ml-s3dis-scaffold.png](05-open3d-ml-s3dis-scaffold.png) | Scaffold / illustrative. No forward pass. S3DIS office classes are the control we refuse to treat as studs. |

Numbers in the rank 1 figures are the scorecards under `artifacts/scorecards/`. They are synthetic. They are not a field accuracy.
