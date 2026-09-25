# Experiments plan

Curriculum stages match [`METHODS.md`](METHODS.md) and the design plan. This file says what has been executed and what is only planned. It does not add a new matrix.

The one-stud five-finder is **owned by another agent**. This paper space does not run it, does not invent its numbers, and does not redefine its factors. When that work lands, copy its scorecards into the day table and cite them here as class F (or as class S, if the finder is still on the generator).

## Run versus planned

| ID | What | Class | State on 2026-09-25 |
| --- | --- | --- | --- |
| E0 | Open3D on seven synthetic scenes (five stage-0 studs, one stage-2 stud-and-slab, one stage-3 four-stud wall) | S | **Run** 2026-09-24. Scorecards under `artifacts/scorecards/open3d_stage*.json`. Day table in `docs/research/13-stud-seg-results-by-day.md` |
| E0-stubs | PCL, CloudCompare, Pointcept, Open3D-ML stub cards on those same scene names | — | **Written, not executed.** `pass_fail = not_run`, metrics null |
| E1 | Same three synthetic stage families through PCL. Stop if bays merge or studs split | S | **Planned.** Needs a machine with PCL |
| E2 | CloudCompare RANSAC-SD on the stage-3 cloud. Record primitive count versus stud count | S | **Planned.** Not a CI dependency |
| E3 | One-stud five-finder: one real stud, five finders (ranks 1–5), SKIL if the stud is standing | F | **Planned, other owner.** Protocol below. No cloud in git |
| E4 | One real wall with an opening. One class, “stud” | F | **Planned.** After E3 |
| E5 | One room. Classical scorecard first. Then Pointcept may be trained. Open3D-ML once, as a label histogram | F | **Planned.** After E4 |
| E6–E7 | Story, then a complex frame | F | **Planned.** After a real stage 5 |
| ER | Realisticized generator (scanner noise, dropout, reflectance) | R | **Not specified.** Do not build it inside this paper pass |
| E-py | pyRANSAC-3D v0.7.0 sequential cuboid after the rank-1 peel | S, then the same clouds as E1 | **Planned, not run.** Proposed in PR #14 (`docs/research/17-methods-that-beat-shortlist.md`). Not in this branch |
| E-sam | SAM 2 mask lifted onto points, then the shared box | F or a capture that already has a registered image | **Planned, not run.** Same PR #14 note. Skip when the cloud has no image |

Trial budget in the design plan: about five Wrong / Expected / Change loops per algorithm family. Open3D has spent loop 1 on E0. Loops 2–5 are open. The other four families have spent zero loops.

## E0 scenes (already run)

From `scripts/run_stage0_baseline.py`:

| Scene | Nominal | Requested lean | Seed |
| --- | --- | --- | --- |
| `stage0_2x4_lean0.000` | 2×4 | 0° | 1 |
| `stage0_2x4_lean0.050` | 2×4 | 0.05° | 2 |
| `stage0_2x4_lean0.120` | 2×4 | 0.12° | 3 |
| `stage0_2x4_lean4.000` | 2×4 | 4° | 4 |
| `stage0_2x6_lean0.300` | 2×6 | 0.30° | 5 |
| `stage2_2x4_lean0.200` | 2×4 on a slab | 0.20° | 6 |
| `stage3_mini_wall_4` | four 2×4s | 0°, 0.30°, 0.80°, 1.50° | 7 |

Reported metrics, all class S: detection precision and recall, max section error, max length error, angle MAE, max absolute angle error, percent inside τ, production paint (must be yellow), runtime of that process. Placeholder colors may be stored and are not a result.

## E3 — one-stud five-finder (when available)

Protocol already written in the design plan. Restated so the paper and the other agent share one checklist.

1. One physical stud, isolated, bare wood. Sensor in the capture order: iPhone LiDAR (Polycam PLY or LAS) for detection, Livox Mid-360 if a denser cloud is needed, survey TLS only when a green/red call is the point of the session. Record sensor, export, and whether file Z is gravity.
2. If the stud is standing and the face is reachable: one digital level, BOT / MID / TOP, model name, printed resolution, three readings, sign. If they disagree by more than that resolution, the stud stays yellow and angle MAE is null.
3. Run the five finders on that same cloud. Ranks 2–5 may still be stubs; a stub remains `not_run` and is not filled from rank 1.
4. Shared outputs: stud id, tight box, θ, ε interval (empty until ε is measured), color. Production color is yellow.
5. Score detection against a human count of one. Do not invent a second stud. Match radius for a field cloud is not defined yet; do not reuse 0.15 m without writing down why.

This paper’s results section gains an E3 table only after those scorecards exist.

## What this plan refuses to add

- A full factorial of noise, spacing, lean, and occlusion beyond the seven E0 scenes, unless a later methods revision needs it. The design plan is the matrix.
- Painting green or red on E3.
- Training Pointcept before stage 5 labels.
- Treating IntCDC component counts as an experiment of this branch.
- Quoting S3DIS mIoU, Özkan roof-beam completeness, or a published dimension error as the stud-angle result.

## Reporting rules

- Date rows in America/Los_Angeles, the way `results_by_day` already does.
- `ground_truth_source` is `synthetic`, `skil`, `total_station`, or `hand_label`. Do not type a field number that was not measured.
- `paint_correct_pct` while ε is empty is the fraction of studs painted yellow. It is not agreement with a level.
- Separate tables for class S and class F. A caption that omits the class is a bug.
