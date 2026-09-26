# Full-room catch tables

Date (America/Los_Angeles): **2026-09-26**. Numbers are read from `artifacts/fullroom/results/`. A blank model is `not run`. A foundation tool whose stage-0 writer cannot take a 28-stud room is `not adapted` and has no invented rate.

Catch rate is the plumb call: measured lean from the floor normal, colored with the locked dual gauges, compared with the planted lean. |measured − planted| is the error call on each result file and is not the supposed-red count. Production paint stays yellow. Experiment 1 tables are unchanged.

Calibration ran `assert_paint_rules()` before each scenario. Display rounding of the Handbook and NAHB atan values is the only delta. No threshold was edited (`improvement: none`).

## Handbook absolute red catch

| Scene | open3d | pointcept | open3d_ml | pcl | pyransac3d | pointsam | sam3d | openmask3d | segment3d |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 1/1 (1.0) | 1/1 (1.0) | 0/1 (0.0) | 0/1 (0.0) | 0/1 (0.0) | not adapted | not adapted | not adapted | not adapted |
| B | 2/2 (1.0) | 1/2 (0.5) | 1/2 (0.5) | 0/2 (0.0) | 0/2 (0.0) | not adapted | not adapted | not adapted | not adapted |
| C | 4/4 (1.0) | 4/4 (1.0) | 1/4 (0.25) | 0/4 (0.0) | 0/4 (0.0) | not adapted | not adapted | not adapted | not adapted |
| D | 6/6 (1.0) | 4/6 (0.6667) | 3/6 (0.5) | 0/6 (0.0) | 0/6 (0.0) | not adapted | not adapted | not adapted | not adapted |
| E | 8/8 (1.0) | 8/8 (1.0) | 5/8 (0.625) | 0/8 (0.0) | 0/8 (0.0) | not adapted | not adapted | not adapted | not adapted |
| F | 10/10 (1.0) | 10/10 (1.0) | 4/10 (0.4) | 0/10 (0.0) | 0/10 (0.0) | not adapted | not adapted | not adapted | not adapted |
| G | 1/1 (1.0) | 1/1 (1.0) | 1/1 (1.0) | 0/1 (0.0) | 0/1 (0.0) | not adapted | not adapted | not adapted | not adapted |
| H | 10/10 (1.0) | 9/10 (0.9) | 6/10 (0.6) | 0/10 (0.0) | 0/10 (0.0) | not adapted | not adapted | not adapted | not adapted |
| I | 8/8 (1.0) | 6/8 (0.75) | 2/8 (0.25) | 0/8 (0.0) | 0/8 (0.0) | not adapted | not adapted | not adapted | not adapted |
| J | 8/8 (1.0) | 7/8 (0.875) | 2/8 (0.25) | 0/8 (0.0) | 0/8 (0.0) | not adapted | not adapted | not adapted | not adapted |

## NAHB absolute red catch

| Scene | open3d | pointcept | open3d_ml | pcl | pyransac3d | pointsam | sam3d | openmask3d | segment3d |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 0 expected (28/28 matched) | 0 expected (26/28 matched) | 0 expected (14/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| B | 0 expected (28/28 matched) | 0 expected (25/28 matched) | 0 expected (12/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| C | 0 expected (28/28 matched) | 0 expected (26/28 matched) | 0 expected (13/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| D | 0 expected (28/28 matched) | 0 expected (21/28 matched) | 0 expected (13/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| E | 0 expected (28/28 matched) | 0 expected (28/28 matched) | 0 expected (10/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| F | 0 expected (28/28 matched) | 0 expected (25/28 matched) | 0 expected (12/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| G | 1/1 (1.0) | 1/1 (1.0) | 1/1 (1.0) | 0/1 (0.0) | 0/1 (0.0) | not adapted | not adapted | not adapted | not adapted |
| H | 10/10 (1.0) | 9/10 (0.9) | 6/10 (0.6) | 0/10 (0.0) | 0/10 (0.0) | not adapted | not adapted | not adapted | not adapted |
| I | 0 expected (28/28 matched) | 0 expected (17/28 matched) | 0 expected (16/28 matched) | 0 expected (0/28 matched) | 0 expected (0/28 matched) | not adapted | not adapted | not adapted | not adapted |
| J | 2/2 (1.0) | 2/2 (1.0) | 1/2 (0.5) | 0/2 (0.0) | 0/2 (0.0) | not adapted | not adapted | not adapted | not adapted |

## Sensor-column red catch (ε = 0.05°)

Same catch rule. Yellow catches for scenes that plant a sensor yellow are in the result JSON (`n_caught_yellow`).

| Scene | Model | Handbook sensor red | NAHB sensor red | Handbook sensor yellow | NAHB sensor yellow |
| --- | --- | ---: | ---: | ---: | ---: |
| A | open3d | 1/1 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| A | pointcept | 1/1 (1.0) | 0 expected (26/28 matched) | 0 expected | 0 expected |
| A | open3d_ml | 0/1 (0.0) | 0 expected (14/28 matched) | 0 expected | 0 expected |
| A | pcl | 0/1 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| A | pyransac3d | 0/1 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| B | open3d | 2/2 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| B | pointcept | 1/2 (0.5) | 0 expected (25/28 matched) | 0 expected | 0 expected |
| B | open3d_ml | 1/2 (0.5) | 0 expected (12/28 matched) | 0 expected | 0 expected |
| B | pcl | 0/2 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| B | pyransac3d | 0/2 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| C | open3d | 4/4 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| C | pointcept | 4/4 (1.0) | 0 expected (26/28 matched) | 0 expected | 0 expected |
| C | open3d_ml | 1/4 (0.25) | 0 expected (13/28 matched) | 0 expected | 0 expected |
| C | pcl | 0/4 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| C | pyransac3d | 0/4 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| D | open3d | 6/6 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| D | pointcept | 4/6 (0.6667) | 0 expected (21/28 matched) | 0 expected | 0 expected |
| D | open3d_ml | 3/6 (0.5) | 0 expected (13/28 matched) | 0 expected | 0 expected |
| D | pcl | 0/6 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| D | pyransac3d | 0/6 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| E | open3d | 8/8 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| E | pointcept | 8/8 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| E | open3d_ml | 5/8 (0.625) | 0 expected (10/28 matched) | 0 expected | 0 expected |
| E | pcl | 0/8 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| E | pyransac3d | 0/8 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| F | open3d | 10/10 (1.0) | 0 expected (28/28 matched) | 0 expected | 0 expected |
| F | pointcept | 10/10 (1.0) | 0 expected (25/28 matched) | 0 expected | 0 expected |
| F | open3d_ml | 4/10 (0.4) | 0 expected (12/28 matched) | 0 expected | 0 expected |
| F | pcl | 0/10 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| F | pyransac3d | 0/10 (0.0) | 0 expected (0/28 matched) | 0 expected | 0 expected |
| G | open3d | 1/1 (1.0) | 1/1 (1.0) | 0 expected | 0 expected |
| G | pointcept | 1/1 (1.0) | 1/1 (1.0) | 0 expected | 0 expected |
| G | open3d_ml | 1/1 (1.0) | 1/1 (1.0) | 0 expected | 0 expected |
| G | pcl | 0/1 (0.0) | 0/1 (0.0) | 0 expected | 0 expected |
| G | pyransac3d | 0/1 (0.0) | 0/1 (0.0) | 0 expected | 0 expected |
| H | open3d | 10/10 (1.0) | 10/10 (1.0) | 0 expected | 0 expected |
| H | pointcept | 9/10 (0.9) | 9/10 (0.9) | 0 expected | 0 expected |
| H | open3d_ml | 6/10 (0.6) | 6/10 (0.6) | 0 expected | 0 expected |
| H | pcl | 0/10 (0.0) | 0/10 (0.0) | 0 expected | 0 expected |
| H | pyransac3d | 0/10 (0.0) | 0/10 (0.0) | 0 expected | 0 expected |
| I | open3d | 4/4 (1.0) | 0 expected (28/28 matched) | 10/12 | 0 expected |
| I | pointcept | 2/4 (0.5) | 0 expected (17/28 matched) | 7/12 | 0 expected |
| I | open3d_ml | 1/4 (0.25) | 0 expected (16/28 matched) | 5/12 | 0 expected |
| I | pcl | 0/4 (0.0) | 0 expected (0/28 matched) | 0/12 | 0 expected |
| I | pyransac3d | 0/4 (0.0) | 0 expected (0/28 matched) | 0/12 | 0 expected |
| J | open3d | 8/8 (1.0) | 2/2 (1.0) | 0 expected | 6/6 |
| J | pointcept | 7/8 (0.875) | 2/2 (1.0) | 0 expected | 5/6 |
| J | open3d_ml | 2/8 (0.25) | 1/2 (0.5) | 0 expected | 1/6 |
| J | pcl | 0/8 (0.0) | 0/2 (0.0) | 0 expected | 0/6 |
| J | pyransac3d | 0/8 (0.0) | 0/2 (0.0) | 0 expected | 0/6 |

## What the zeros are

PCL on scene A: native region growing True, 1 member after adjacency, 0 detections after the existing stud gate (section, length, upright). Catch stays 0 because nothing matched. pyRANSAC-3D on scene A: stopped `wall_swallow`, accepted 0 cuboids, MAX_CUBOIDS 4. Those existing limits were not raised.

Result files on disk when this note was written: 90.

Self-healing queue: `scripts/experiment_queue_runner.py`. Invoke note: [40-experiment-queue-runner.md](40-experiment-queue-runner.md). Scenes: [39-fullroom-scenes.md](39-fullroom-scenes.md).
