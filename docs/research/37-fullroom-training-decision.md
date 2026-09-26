# Full-room training decision (TruePlank, 28 studs)

Date (America/Los_Angeles): **2026-09-26**. Host for the later train: **Oz_PC** (RTX 4080 SUPER, 16 GB). This note is the Phase 0 decision for the full-room experiment. It does not train a weight, does not write a scorecard, and does not edit Experiment 1.

Experiment 1 stays the one-stud scene `stage0_2x4_lean0.000` scored in [31-four-stage-error-table.md](31-four-stage-error-table.md) and `artifacts/phase_neg1/experiment1_dual_pass.json`. Those files, `scripts/score_experiment1_dual_pass.py`, and the stud-head checkpoints named in [29-train-all9-stage0.md](29-train-all9-stage0.md) stay as they landed.

## Decision

**Train the two supervised stud heads on full rooms of 28 studs. Do not train them on per-stud crops for this experiment.**

The scored unit is still one stud. The cloud the model sees at test time is the room. The heads that exist today were trained on one stud, sometimes plus a floor ([20-synthetic-stud-finetune.md](20-synthetic-stud-finetune.md), doc 29). On a floorless stud they label every point stud (25,666 / 25,666). That answer matches Experiment 1. In a room it paints plates, the floor, and the gaps as stud, and the shared minimal OBB then measures a blend of members.

A 28-stud room is small enough to be one training cloud. The new thing the head has to learn is which points are studs and which points are plates or floor, so a later cluster can keep the 28 members apart. A per-stud crop already removes the plate and the neighbor, so it cannot teach that split.

## What gets trained

Bucket 2 from [27-four-way-tool-classification.md](27-four-way-tool-classification.md) only:

| Stack | What changes | Init | Checkpoint (new file) |
| --- | --- | --- | --- |
| Pointcept / PTv3 | 2-class MLP head (clutter / stud). Backbone stays the BIMStruct3D PT-v3m1. Head-only first. The doc 20 unfreeze rule still applies if val stud recall on rooms is under 0.80 or stud IoU is under 0.35. | Published BIMStruct3D cache (gitignored). Experiment 1 `pointcept_stud_2class.pth` is not the init and is not overwritten. | `artifacts/checkpoints/stud-heads/fullroom/pointcept_stud_2class_fullroom.pth` |
| Open3D-ML RandLA-Net | 2-class last layer. Encoder tensors whose shapes match are copied from the S3DIS zoo file. | `randlanet_s3dis_202201071330utc.pth` (gitignored). Experiment 1 `randlanet_stud_2class.pth` is not overwritten. | `artifacts/checkpoints/stud-heads/fullroom/randlanet_stud_2class_fullroom.pth` |

Both heads stay pointwise semantic labels. They do not emit an instance id, a lean, or a green/yellow/red color. Lean stays the shared minimal OBB on points labeled stud (BoxFit). Color stays the locked dual-gauge rule below.

No other bake-off model is trained.

| Bucket | Models | This experiment |
| --- | --- | --- |
| Geometry-first | Open3D, PCL / NumPy region-grow cuboid, pyRANSAC-3D | No train. Phase 1 only checks that each one still runs. |
| Promptable foundation | Point-SAM, SAM3D, OpenMask3D, Segment3D | Prompt or zero-shot, same path as docs 26, 29, and 30. No finetune, no stud-labeled weight update. |
| Interactive GUI | CloudCompare | Out of the nine. |
| Adjacent | SAM 2 | Out of the nine. Image-prompted lift stays where docs 24 and 25 left it. |

Foundation handling, one line each:

- **Point-SAM.** Published ViT-L weights. A point prompt on the cloud. The mask is not a stud-trained head.
- **SAM3D.** Doc 30 full-stud multi-view lift from the ViT-H scaffold. Weights are not updated.
- **OpenMask3D.** Class-agnostic mask module plus CLIP on synth posed RGB-D, query text for a stud. Mask-module and CLIP weights are not updated.
- **Segment3D.** Zero-shot Mask3D query, points taken through the inverse map. Weights are not updated.

Finetuning those four would put them in the supervised bucket and would make their full-room cards a different method from the Experiment 1 cards.

## Data recipe

Generator: a new full-room function beside `stage5_room_bay`. `stage5_room_bay` stays the 26-stud LOT-62-look bay (four walls at seven 16-inch centers, then the south door drops two studs). This experiment wants **28 studs**, so the new function keeps all four walls, seven studs each, plates, and a floor. Corner air gap stays the stage-5 gap (clear air above the 25 mm DBSCAN eps). No header. The stage-5 scene name, seed 62, and its scorecards stay put.

Labels, same two classes as doc 20:

| id | name | generator part |
| --- | --- | --- |
| 0 | clutter | floor and both plates |
| 1 | stud | the dressed 2×4 (part 2) |

RGB stays zeros. Pointcept still receives Open3D normals. Reference up axis on these synthetic rooms is the floor normal when a floor is present, matching the synthetic-angle lock. The head does not see that angle as a target.

Dials already in the generator (CloudSmith), not new sensor numbers:

| Dial | Value | Why this value |
| --- | --- | --- |
| Stud spacing | 0.006 m | `stage5_room_bay` default |
| Plate spacing | 0.010 m | `stage5_room_bay` default |
| Floor spacing | 0.020 m | `stage5_room_bay` default |
| Noise | 0.0005, 0.0010, 0.0015, 0.0020 m, cycled | doc 20 noise cycle |
| Nominal | 2×4 dressed | same section as Experiment 1 |
| Length | 8 ft | `STUD_LENGTH_8FT_M` |

Samplers stay the ones already compiled into the heads:

- RandLA-Net: `NUM_POINTS = 16384`, `GRID_SIZE = 0.02` m.
- Pointcept: `GridSample` at `GRID_SIZE = 0.02` m.

A 5 mm single stud is 25,666 points. Twenty-eight of those, plus plates and a floor, do not fit in one 16,384-point RandLA step. Each step remains a spatial sample of a **whole room**. Many rooms and more than one epoch are how every stud is seen. Those two constants are the existing model layout. They are not a new plumb tolerance.

### Splits

Evaluation scenes are reserved here so the train script cannot consume them. Phase 2 assigns letters A–J to these seeds and may use fewer than ten. None of them enter train or val.

| Split | Seeds | Rooms | Role |
| --- | --- | --- | --- |
| Train | 1101–1148 | 48 | Full rooms, 28 studs each |
| Val | 1201–1208 | 8 | Selection score only |
| Held out (Phase 2) | 1301–1310 | up to 10 | Scenes A–J. Not in the manifest. |

Also kept out of this manifest: `stage0_2x4_lean0.000`, the 25 phase-1 S1 cards (seed 2), and `stage5_room_bay` seed 62.

Cache: `data/cache/finetune-fullroom/` (gitignored, same rule as `data/cache/finetune-synth/`). Manifest: `data/finetune/fullroom_28_manifest.json`.

### Planted leans inside a training room

The head is not trained on color. Leans are still mixed inside each room so a plumb member and an out-of-plumb member both appear as stud points. Magnitudes below are the planted angle from vertical. They sit in buckets of the locked gauges so Phase 2 can reuse the same menu. The gauges themselves are unchanged.

| Planted \|lean\| | Handbook finish plumb (τ = 0.11937°) | NAHB warranty gauge (τ = 0.67140°) | Sensor column (ε = 0.05°) |
| --- | --- | --- | --- |
| 0.00°, 0.05° | green | green | Handbook green (0.05° + 0.05° = 0.10° ≤ 0.11937°) |
| 0.10°, 0.15° | 0.10° green at ε = 0; 0.15° red at ε = 0 (0.15° > 0.11937°) | green | Handbook sensor yellow for both (the 0.05° band overlaps 0.11937°) |
| 0.30°, 0.50° | red | green | Handbook red; NAHB still green at ε = 0.05° (0.50° + 0.05° = 0.55° ≤ 0.67140°) |
| 0.67° | red | green at ε = 0 (0.67° ≤ 0.67140°); yellow at ε = 0.05° | NAHB interval overlaps τ |
| 1.00°, 2.00° | red | red | outside both gauges after ε = 0.05° is removed |

Each training room draws a permutation of that menu across the 28 studs (with replacement). Axes stay ±X and ±Y in the stud frame, the same axes as doc 20. Val rooms use the same menu and disjoint seeds.

## How long, and what “trained” means

Doc 29’s one-beam train (RandLA 3 epochs, Pointcept 2 head epochs) is a bring-up. This pass trains on rooms until the val score stops improving, with a cap that fits one idle 4080 SUPER session:

| Stack | Cap | Selection score |
| --- | --- | --- |
| RandLA-Net | 8 epochs | mean of stud IoU and clutter IoU on the 8 val rooms |
| Pointcept | 4 head epochs, then up to 2 decoder epochs if the doc 20 unfreeze rule fires | same score |

Save the epoch with the best selection score. A head that labels the whole room stud fails clutter IoU and is not the saved epoch.

Smoke after the weights exist, before any lettered scene: load each new checkpoint on CUDA, run one forward pass on val seed 1201, and require both class ids in the prediction. Geometry-first tools get an import-and-one-room run with metrics left for Phase 4. Foundation models get a load of the published checkpoint on that same room, prompt or zero-shot, and no weight write.

## Color rule this train does not touch

Locked from doc 31 / the Experiment 1 dual pass. Repeated here so a later phase does not invent a third tolerance.

| Column | τ | ε |
| --- | --- | --- |
| Handbook finish plumb, absolute | atan(0.25/120) = **0.11937°** | 0° |
| Handbook finish plumb, sensor | 0.11937° | **0.05°** (SKIL device band only) |
| NAHB warranty gauge, absolute | atan(0.375/32) = **0.67140°** | 0° |
| NAHB warranty gauge, sensor | 0.67140° | **0.05°** |

Green if e + ε ≤ τ. Red if e − ε > τ. Yellow if the interval overlaps τ. Human placement error and lumber surface defects stay out of ε. Production paint stays yellow while device ε is unlocked. The full-room catch tables apply this same rule per stud. They do not edit the Experiment 1 matrix.

## What Phase 1 is allowed to add

A manifest builder, a train script for each head, the new checkpoint directory, and a smoke script. Phase 1 writes the smoke log. It does not write catch tables and it does not retune τ, ε, `NUM_POINTS`, or `GRID_SIZE`.
