# scripts

`run_stage0_baseline.py` runs the Open3D baseline on synthetic stages 0, 2, and 3, writes scorecards under `artifacts/scorecards/`, writes stub scorecards for the other four contenders, and upserts `results_by_day.csv` (plus the JSON and `docs/research/13-stud-seg-results-by-day.md`). It exits non-zero if a synthetic bar fails. A same-day re-run updates those rows. It does not invent field numbers.

`render_algo_figures.py` writes the PNGs in `docs/research/images/algo-contenders/`. Rank 1 is the baseline. Ranks 2–5 are labeled scaffold diagrams.

Dataset download helpers are not here yet. Large clouds stay linked from `docs/research/`.
