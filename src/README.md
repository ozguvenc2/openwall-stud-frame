# src

`open3d_smoke.py` imports Open3D and prints `open3d.__version__`. It does not open a cloud.

`openwall_stud/` is the stud-segmentation package:

- `synthetic.py` — stage 0 single stud, stage 2 stud plus floor, stage 3 mini wall. Generator up axis is +Z.
- `open3d_baseline.py` — rank 1 pipeline: peel horizontal slabs, DBSCAN, minimal OBB, lean, yellow paint while ε is unlocked.
- `paint.py` — green / yellow / red. Unlocked ε is yellow.
- `scorecard.py` — shared JSON writer (detection, geometry, angle, paint, cost).
- `contenders/` — stubs for PCL, CloudCompare / CloudComPy, Pointcept, and Open3D-ML. See `contenders/README.md`.

Run from the repo root:

```bash
python scripts/run_stage0_baseline.py
python scripts/render_algo_figures.py
```

Those scripts add `src` to `sys.path`. On a minimal Linux image, `import open3d` needs `libegl1` installed. The design plan is `docs/research/12-stud-seg-design-plan.md`.
