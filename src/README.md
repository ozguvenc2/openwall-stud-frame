# src

`open3d_smoke.py` imports Open3D and prints `open3d.__version__`. It does not open a cloud.

`openwall_stud/` is the stud-segmentation package:

- `synthetic.py` — stage 0 single stud, stage 2 stud plus floor, stage 3 mini wall. Generator up axis is +Z.
- `open3d_baseline.py` — rank 1 pipeline: peel horizontal slabs, DBSCAN, minimal OBB, lean, yellow paint while ε is unlocked.
- `paint.py` — green / yellow / red. Unlocked ε is yellow. `dual_standard_passes` reports Handbook finish plumb and the NAHB warranty gauge, absolute and with the 0.05° SKIL device band.
- `scorecard.py` — shared JSON writer (detection, geometry, angle, paint, cost) and `append_day_row`.
- `results_by_day.py` — day table CSV, JSON, and markdown. Dates are America/Los_Angeles.
- `contenders/` — PCL, CloudCompare RANSAC-SD, Pointcept, Open3D-ML, and pyRANSAC-3D rank 6 (the doc 17 add). See `contenders/README.md`.
- `one_stud.py` — the single Stage 0 cloud (2×4, lean 0.05°, seed 2) and the stage 0 bars.

Run from the repo root:

```bash
python scripts/run_stage0_baseline.py
python scripts/run_one_stud_five_finders.py
python scripts/render_algo_figures.py
```

Those scripts add `src` to `sys.path`. On a minimal Linux image, `import open3d` needs `libegl1` installed. The design plan is `docs/research/12-stud-seg-design-plan.md`.
