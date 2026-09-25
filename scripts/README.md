# scripts

`run_stage0_baseline.py` runs the Open3D baseline on synthetic stages 0, 2, and 3, writes scorecards under `artifacts/scorecards/`, writes stub scorecards for the other four contenders, and upserts `results_by_day.csv` (plus the JSON and `docs/research/13-stud-seg-results-by-day.md`). It exits non-zero if a synthetic bar fails. A same-day re-run updates those rows. It does not invent field numbers.

`run_one_stud_five_finders.py` runs Open3D, PCL, CloudCompare RANSAC-SD, Pointcept, Open3D-ML, and pyRANSAC-3D (rank 6, the doc 17 add) on one synthetic 2×4 (lean 0.05°, seed 2) and stops. It writes `docs/research/16-one-stud-five-finder-run.md`, one scorecard per finder, and the figures under `docs/research/images/one-stud-five-finders/`. A blocked install keeps metrics null. Rank 6 alone is `python -m openwall_stud.contenders.pyransac3d_cuboid`.

`run_phase1_s1_lean_sweep.py` is experiment phase one (S1): 25 synthetic dressed 2×4 clouds (lean magnitudes 0, 0.05, 0.12, 0.15, 0.30, 1, and 4 degrees; nonzero leans about +X, −X, +Y, and −Y; seed 2). It scores ranks 1, 2, 3, and 6 on every cloud and runs ranks 4 and 5 as controls. Scorecards go to `artifacts/scorecards/phase1_s1/`. The note is `docs/research/19-phase1-s1-lean-sweep.md`. It is not a field measurement. Rank 3 alone is `--finder cloudcompare`. CloudCompare is resolved from `CLOUDCOMPARE_EXE`, then `C:\Program Files\CloudCompare\CloudCompare.exe`, then PATH. `python -m openwall_stud.contenders.cloudcompare_ransac --smoke` launches the binary once and writes `artifacts/scorecards/cloudcompare_smoke.json`.

`render_algo_figures.py` writes the PNGs in `docs/research/images/algo-contenders/`. Rank 1 is the baseline. Ranks 2–5 in that older figure set are labeled scaffold diagrams, not the one-stud run.

Dataset download helpers are not here yet. Large clouds stay linked from `docs/research/`.
