# Experiment queue runner

Date (America/Los_Angeles): **2026-09-26**. Self-healing is on for the remaining full-room work. Experiment 1 dual-pass stays the file from PR #41. The dual G/Y/R gauges are unchanged.

## Invoke

From the repo root, with the geometry interpreter:

```
.venv\Scripts\python.exe scripts/experiment_queue_runner.py
.venv\Scripts\python.exe scripts/experiment_queue_runner.py --dry-run
.venv\Scripts\python.exe scripts/experiment_queue_runner.py --status
.venv\Scripts\python.exe scripts/experiment_queue_runner.py --self-test
.venv\Scripts\python.exe scripts/experiment_queue_runner.py --retry-failed
```

`--dry-run` lists what would run. `--status` prints finished, running, skipped, failed, and pending from `logs/experiment_queue_state.json`. `--self-test` uses a throwaway directory: one fake CUDA out-of-memory is recovered, one hard failure is marked failed, and the queue still finishes. `--retry-failed` re-queues stages already marked failed. A normal second invocation skips successes and skips stages already marked failed.

## What is queued

| Stage | When it runs |
| --- | --- |
| `exp1_dual_pass` | Skipped when `artifacts/phase_neg1/experiment1_dual_pass.json` is present. That file is the PR #41 rebuild. The queue does not call `score_experiment1_dual_pass.py`. |
| `fullroom_phase0` | Skipped when `docs/research/37-fullroom-training-decision.md` is present. |
| `fullroom_phase1` | Skipped when both full-room checkpoints under `artifacts/checkpoints/stud-heads/fullroom/` are present. |
| `fullroom_phase2` | Skipped when `artifacts/fullroom/scenes_expected.json` is present. |
| `fullroom_{A–J}_{model}` | One process per scene and model: `scripts/run_fullroom_scenario.py`. Calibration (`assert_paint_rules`) runs before the model. |
| `fullroom_phase5_aggregate` | Writes `artifacts/fullroom/catch_summary.json` and `docs/research/41-fullroom-catch-tables.md` from whatever result files exist. |

Models: Open3D, PCL, pyRANSAC-3D (repo `.venv`); Pointcept (ranks45 torch 2.7); Open3D-ML RandLA-Net (ranks45 `.venv-o3dml`); Point-SAM, SAM3D, OpenMask3D, Segment3D. The four foundation tools record `not_adapted` because `scripts/phase_neg1_stage0_foundation.py` builds a single stage-0 stud. They are not finetuned, and the scenario script does not invent a catch rate.

## Failure handling

A non-zero exit, timeout, CUDA out-of-memory, missing module, bad path, or other CUDA error is appended to `logs/experiment_queue_failures.log` with the timestamp, stage id, and stderr. The diagnosis and the applied fix go to `logs/experiment_queue_recovery.jsonl` and to `logs/experiment_queue.log`.

| Cause | Fix, then retry that stage only |
| --- | --- |
| GPU out of memory | Set `FULLROOM_BATCH=1`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, and `FULLROOM_OOM_RETRY=1`. The next process is new, clears the CUDA cache, and does not change the trained point sampler. |
| Missing module | `pip install` that top-level name into the stage venv, once. Torch, Open3D, and NumPy are refused so a retry cannot replace the pinned stack. |
| Bad path | Walk the interpreter list and use the first executable that exists. |
| Other CUDA error | `FULLROOM_CUDA_RESET=1` and a fresh process that clears the cache. |
| Anything else, including a timeout | Restart the same stage. No other stage is aborted. |

Each stage may retry three times after the first failure. The fourth failure is marked failed and the next stage starts.
