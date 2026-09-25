# Contender hooks

Rank 1 (refined Open3D) lives in `openwall_stud.open3d_baseline`.

`scripts/run_one_stud_five_finders.py` runs all five finders on one synthetic
2×4 at 0.05° lean (seed 2) and stops. The write-up is
`docs/research/16-one-stud-five-finder-run.md`.

Each module below loads that same cloud unless `--stub` is set. `--stub` is
what `scripts/run_stage0_baseline.py` still uses when it records null cards
for the multi-scene Open3D sweep. A stub does not segment.

| Rank | Module | Command | One-stud result |
| --- | --- | --- | --- |
| 2 | `pcl_region_grow.py` | `python -m openwall_stud.contenders.pcl_region_grow` | `ran` when `libpcl` 1.14 region growing executes |
| 3 | `cloudcompare_ransac.py` | `python -m openwall_stud.contenders.cloudcompare_ransac` | `ran` when `CloudCompare -RANSAC` returns primitive clouds |
| 4 | `pointcept_ptv3.py` | `python -m openwall_stud.contenders.pointcept_ptv3` | `blocked_install` without a GPU and a stud checkpoint |
| 5 | `open3d_ml_s3dis.py` | `python -m openwall_stud.contenders.open3d_ml_s3dis` | `blocked_install` without weights and a forward pass |

Run them from the repo root with `PYTHONPATH=src`.

Shared rule for every rank, once it actually returns stud points: tight OBB,
angle versus the stored reference, then the paint in `openwall_stud.paint`.
Epsilon stays unlocked, and the production color stays yellow. A blocked
install leaves the metric cells null.
