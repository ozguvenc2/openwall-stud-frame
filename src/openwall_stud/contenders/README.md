# Contender hooks

Rank 1 (refined Open3D) is the only stack this environment runs. It lives in
`openwall_stud.open3d_baseline` and is started with `scripts/run_stage0_baseline.py`.

Ranks 2–5 are stubs. Each module’s docstring is the install note and the
entrypoint. Running the module writes a scorecard whose detection, geometry,
and angle fields are null and whose status is `stub_not_run`. That is
intentional. No GPU training is started.

| Rank | Module | Command | Status now |
| --- | --- | --- | --- |
| 2 | `pcl_region_grow.py` | `python -m openwall_stud.contenders.pcl_region_grow` | stub — PCL not installed |
| 3 | `cloudcompare_ransac.py` | `python -m openwall_stud.contenders.cloudcompare_ransac` | stub — GUI / CloudComPy not installed |
| 4 | `pointcept_ptv3.py` | `python -m openwall_stud.contenders.pointcept_ptv3` | stub — hook until labeled Stage 5 |
| 5 | `open3d_ml_s3dis.py` | `python -m openwall_stud.contenders.open3d_ml_s3dis` | stub — control only, weights not loaded |

Run them from the repo root with `PYTHONPATH=src`.

Shared rule for every rank, once it actually segments: stud points, tight OBB,
angle versus the stored reference, then the paint in `openwall_stud.paint`.
Epsilon stays unlocked until a measured device band exists, and the production
color stays yellow.

`scripts/run_stage0_baseline.py` records a `not_run` row for each of these
four stacks on every synthetic scene it scores, with null metrics, in
`artifacts/scorecards/results_by_day.csv`.
