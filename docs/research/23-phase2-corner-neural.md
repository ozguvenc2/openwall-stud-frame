# Phase 2 — synthetic corner for the neural ranks

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC**. GPU: **NVIDIA GeForce RTX 4080 SUPER (16 GB)**. Suite: **OpenWall**. App: **TruePlank**.

This note is the synthetic half of phase 2. The field half is [22-phase2-wall-corner-field.md](22-phase2-wall-corner-field.md): a painted corner, a SKIL level, and two Open3D planes. This note builds a corner the neural ranks can score, with planted leans. It does not detect studs. Class F is still empty. ε stays unlocked. Production paint stays yellow.

## Generator

Script: `scripts/build_phase2_corner_synth.py`. Module: `src/openwall_stud/phase2_corner.py`.

| | |
| --- | --- |
| Scene | `phase2_corner_skil_means` |
| Seed | 25 |
| Faces | wall A is the YZ face, rotated about +Y. Wall B is the XZ face, rotated about +X. The +Z edge stays put, so the faces still meet |
| Planted lean | wall A **0.383°**, wall B **0.250°** (the SKIL face means) |
| Dihedral of the planted normals | 89.998° |
| Size | 0.80 m × 2.40 m each face |
| Spacing | 5 mm on the faces, 10 mm on the floor |
| Noise | isotropic Gaussian, 2 mm (inside the 1–5 mm phone-like band) |
| Points | 161,443 (77,441 + 77,441 + 6,561) |
| Vertical | export +Z |

Labels:

| id | name | what it is |
| --- | --- | --- |
| 0 | floor | the horizontal patch. Not a plumb reference |
| 1 | wall_a | the face planted at 0.383° |
| 2 | wall_b | the face planted at 0.250° |

There is no stud id. A stud/clutter head cannot name these classes.

An SVD on the noisy points of each true class recovers 0.384° and 0.250° (RMSE 2.0 mm on both walls). That is the noise floor of the generator, not a network result.

Committed cloud: `artifacts/phase2_corner_synth/corner_skil_means.npz` and `corner_skil_means.json`. The PLY next to them is gitignored by `*.ply`.

## What ran

Interpreters are the Oz_PC checkouts that already hold the phase-1 stacks. Pointcept is `openwall-stud-frame-ranks45\.venv` (torch 2.7.0+cu126). RandLA-Net is `.venv-o3dml` in that same checkout (torch 2.13.0+cu126). The scripts insert this branch’s `src/` first. The BIMStruct3D cache stays gitignored.

| Stack | What it is | Result on the held-out corner |
| --- | --- | --- |
| `control_pointcept` | BIMStruct3D office vocabulary, 10-pass TTA | 161,443 / 161,443 labeled clutter. Wall count 0. Two faces not recovered. 53.6 s |
| `control_randlanet` | S3DIS RandLA-Net | clutter 149,934, floor 11,315, bookcase 194, wall 0. Two faces not recovered. Inference 1.06 s |
| `finetune_pointcept` | phase-1 stud/clutter head | 139,945 points labeled stud (86.7%). Ground truth has 0 studs. Those labels are false. 13.4 s |
| `finetune_randlanet` | phase-1 stud/clutter head, per-cloud batch-norm | 161,100 points labeled stud (99.8%). Same false-stud reading. Inference 0.76 s |
| `corner_pointcept` | new 3-class head, this note | Floor IoU 0.935. Wall A IoU 0.522. Wall B IoU 0.091. Two faces not recovered. See below |

Cards: `artifacts/scorecards/phase2_corner_neural/`.

The office models have one `wall` class, not `wall_a` and `wall_b`. On this cloud that class was empty, so there was no wall subset to split into two planes. The stud heads have no wall classes. Scoring them as face detectors would invent a mapping. The number that is real is the false-stud count.

## 3-class head

`scripts/train_phase2_corner_head.py`. Eight other corners (seeds 101–108, noise 1–5 mm, leans a few hundredths off the SKIL means). The canonical seed-25 scene is not in that set. Twelve epochs train the new MLP with the BIMStruct3D backbone frozen (mean loss 1.069 → 0.594). Two more epochs unfreeze the decoder (mean loss 0.354, then 0.167). Train wall time 19.1 s. Checkpoint: `artifacts/weights/finetune/pointcept_corner_3class.pth` (30,072,111 bytes).

Held-out scores:

| Class | Precision | Recall | IoU | Plane on the predicted points |
| --- | ---: | ---: | ---: | --- |
| floor | 0.997 | 0.937 | 0.935 | horizontal, RMSE 2.0 mm |
| wall_a | 0.522 | 1.000 | 0.522 | RMSE 165 mm, normal 43° off the planted normal. Not a face |
| wall_b | 0.999 | 0.091 | 0.091 | 7,040 points, lean error 0.001°, normal error 0.005°, RMSE 2.0 mm. Misses 91% of the face |

A face counts only when the predicted points are vertical, within 0.5° of the planted lean, within 20° of the planted normal, and within 15 mm RMSE. Wall B’s small clean subset meets that geometric bar and fails as a detector because recall is 0.091. Wall A is the blend of both faces (normal between the two planted normals). `two_faces` is false.

The 0.5° bar is a synthetic bring-up check. It is not τ and it is not ε. No green and no red.

RandLA-Net was not given a 3-class corner layer in this pass. The stud head above is the rank-5 result. A 3-class RandLA train is still open.

## What this does not say

- The painted field corner and this generator are different clouds. The field planes leaned 1.003° and 0.763°. This generator was planted at 0.383° and 0.250° so the network would have a known answer. Matching the generator is not matching the level.
- Paint on the field cloud is not wood. This generator is not wood either. It is two planes and a floor.
- Class F waits on a bare stud and SKIL readings on that wood. That stub is phase 2b in the draft.
