# Full-room stud-head train (Phase 1)

Date (America/Los_Angeles): **2026-09-26**. Host: **Oz_PC** (RTX 4080 SUPER). Recipe: [37-fullroom-training-decision.md](37-fullroom-training-decision.md). This pass trains the two supervised heads and smokes the three geometry-first tools. It does not score green / yellow / red and it does not edit Experiment 1.

## Weights

| Stack | Saved epoch | Wall | Selection score | Stud IoU | Clutter IoU | Stud recall | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pointcept PTv3, head only | 4 of 4 | 170.1 s | 0.9097 | 0.9695 | 0.8499 | 0.9717 | `artifacts/checkpoints/stud-heads/fullroom/pointcept_stud_2class_fullroom.pth` |
| Open3D-ML RandLA-Net | 7 of 8 | 332.5 s | 0.8918 | 0.9626 | 0.8210 | 0.9651 | `artifacts/checkpoints/stud-heads/fullroom/randlanet_stud_2class_fullroom.pth` |

Selection score is the mean of stud IoU and clutter IoU on the 8 val rooms (seeds 1201–1208). Every val room had both class ids. Pointcept copied 486 BIMStruct tensors and trained 4 head tensors. The doc 20 unfreeze rule did not fire (stud recall 0.9717, stud IoU 0.9695). RandLA-Net copied the S3DIS encoder and trained the new 2-class layer. Epoch 8 was slightly below epoch 7, so epoch 7 is the saved file.

Logs: `artifacts/checkpoints/stud-heads/fullroom/*_fullroom_train_log.json`.

Experiment 1 files `pointcept_stud_2class.pth` and `randlanet_stud_2class.pth` were not rewritten. The smoke recorded their SHA-256 before and after each role and they matched.

## Smoke on val seed 1201

Scene `val_0000`: 28 studs, 566,769 points. Artifact: `artifacts/fullroom/phase1_smoke.json`.

| Tool | What ran | Result |
| --- | --- | --- |
| Open3D | `run_baseline` on the room | 28 detections in 0.942 s |
| PCL 1.14 | native RegionGrowing via `grow_labels` | returned labels in 6.904 s (`native_pcl_region_growing` true) |
| pyRANSAC-3D | existing `Cuboid.fit` on the first stud's points only | 17,234 / 17,234 inliers in 0.792 s |
| Pointcept full-room head | one forward pass | classes clutter and stud, 1.077 s (97,379 clutter / 469,390 stud) |
| RandLA-Net full-room head | one forward pass | classes clutter and stud, 2.472 s (98,482 clutter / 468,287 stud) |

Open3D's 28 detections are a count of clusters on this one val room. They are not a catch table. pyRANSAC-3D's full-room sequential fit is still Phase 4. The first-stud fit only shows the library still runs at the thresholds already in `pyransac3d_cuboid.py`.

## What this is

A synthetic semantic train. Plates and the floor are clutter. Lean is still the shared minimal OBB, and color is still the doc 31 dual-gauge rule. Foundation models were not finetuned. No lettered scene has been scored.
