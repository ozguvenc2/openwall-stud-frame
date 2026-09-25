# scripts

`run_stage0_baseline.py` runs the Open3D baseline on synthetic stages 0, 2, and 3, writes scorecards under `artifacts/scorecards/`, writes stub scorecards for the other four contenders, and upserts `results_by_day.csv` (plus the JSON and `docs/research/13-stud-seg-results-by-day.md`). It exits non-zero if a synthetic bar fails. A same-day re-run updates those rows. It does not invent field numbers.

`run_one_stud_five_finders.py` runs Open3D, PCL, CloudCompare RANSAC-SD, Pointcept, Open3D-ML, and pyRANSAC-3D (rank 6, the doc 17 add) on one synthetic 2×4 (lean 0.05°, seed 2) and stops. It writes `docs/research/16-one-stud-five-finder-run.md`, one scorecard per finder, and the figures under `docs/research/images/one-stud-five-finders/`. A blocked install keeps metrics null. Rank 6 alone is `python -m openwall_stud.contenders.pyransac3d_cuboid`.

`render_algo_figures.py` writes the PNGs in `docs/research/images/algo-contenders/`. Rank 1 is the baseline. Ranks 2–5 in that older figure set are labeled scaffold diagrams, not the one-stud run.

Dataset download helpers are not here yet. Large clouds stay linked from `docs/research/`.
