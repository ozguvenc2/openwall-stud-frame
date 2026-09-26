# Phase -1 nine-tool install status

Date: **2026-09-26**. Install and smoke for all nine, then a bounded first round on `stage0_2x4_lean0.000` only. No other curriculum stage, no phase-2 run, and no ranking trial. Stud numbers below use the existing scorecard and day-table writers. No new metric was added.

Identities follow [27-four-way-tool-classification.md](27-four-way-tool-classification.md) and [26-point-sam-and-3d-peers.md](26-point-sam-and-3d-peers.md). SAM3D is Yang et al., `Pointcept/SegmentAnything3D` (`yang2023sam3d`). It is not Meta's image-to-mesh SAM 3D Bodies. CloudCompare stays in bucket 4 and was not installed.

Scene: `stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)` → `stage0_2x4_lean0.000`, 25,666 points, 5 mm spacing, 1 mm noise. Regenerated with `openwall_stud.synthetic`. The cloud files under `artifacts/phase_neg1/` are local smoke inputs and are not committed.

Host: Oz_PC, Windows 11, RTX 4080 SUPER 16 GB (sm_89). Windows has no `nvcc`, no MSVC, and no `sudo` inside WSL. CUDA builds used a user micromamba prefix, not a CUDA toolkit MSI.

## Status

| Tool | Installed | Version | Smoke on stage0_2x4_lean0.000 | Errors | needs_user_at_keyboard |
| --- | --- | --- | --- | --- | --- |
| Open3D | yes | 0.20.0 | yes | | no |
| PCL 1.14 | yes | 1.14.1 (`PCL_VERSION_PRETTY`) | yes | The ELF stays in WSL. On Windows, `grow_labels` now calls `wsl $HOME/bin/pcl_region_grow` when that binary exists. | no |
| pyRANSAC-3D | yes | 0.7.0 | yes | | no |
| Pointcept | yes | torch 2.7.0+cu126, CUDA 12.6, 4080 SUPER | yes | Control histogram is all `clutter` (BIMStruct classes, not the stud head). One in-memory step did not save the published 2-class weight. | no |
| Open3D-ML | yes | torch 2.13.0+cu126, `open3d.ml.torch` | yes | S3DIS control top class `clutter` (11,920). One in-memory step did not save the published 2-class weight. | no |
| Point-SAM | yes | commit `25f4fd9`; torch 2.14.0+cu126; torkit3d 0.1.2 sm_89 | yes | Apex was not compiled. `predict_masks` on the large config did not need it. Hugging Face login was not required. | no |
| SAM3D | yes | repo `2aaa8c9`; segment-anything 1.0; pointops 1.0 | yes | Official README pins torch 1.11 / CUDA 11.3, which cannot target sm_89. The ScanNet multi-frame folder was not used. Smoke was one ViT-H forward on the existing stud pinhole plus one `pointops.knn_query` on the 25,666-point cloud. | no |
| OpenMask3D | yes | repo `3bc3fc5`; MinkowskiEngine 0.6.0; detectron2 0.6 | yes | Mask module only. Checkpoint `mask_module_arbitrary.ckpt` (952,327,000 bytes). Output `stage0_2x4_lean0_masks.pt` shape `(25666, 100)`. The stud PLY has no RGB, so vertices were filled with a constant gray. The CLIP / posed RGB-D stage was not run. | no |
| Segment3D | yes | repo `c510d89`; same MinkowskiEngine 0.6.0 stack | yes | Checkpoint `segment3d.ckpt` (475,931,578 bytes). 469 tensors loaded, 0 missing. `pred_logits` shape `[1, 100, 2]` on the 4080 SUPER. Hydra 1.3 cannot compose this repo's Hydra 1.0 defaults, so the smoke loads `conf/model/mask3d_no_aux.yaml` directly. `demo.py` cuML DBSCAN was not run. | no |

Smoke details that are not a new stud metric:

- Open3D: 1 cluster, 25,666 kept, about 0.064 s, env `C:\Repos\openwall-stud-frame\.venv`.
- pyRANSAC-3D: first cuboid inliers 25,666. Same env.
- PCL: `/home/pegassy/bin/pcl_region_grow` with smoothness 10, curvature 1, k 30, min cluster 50. 1 cluster, 154 points labeled `-1`, 25,512 in cluster 0.
- Pointcept: backbone copy 486, existing 2-class head loaded, one-step loss 0.0000 because that head already labels this all-stud cloud. Env `C:\Repos\openwall-stud-frame-ranks45\.venv`.
- Open3D-ML: encoder copy 328, dry prediction length 25,666, one-step loss 0.0067, about 0.19 s. Env `C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml`.
- Point-SAM: `predict_masks` mask shape `(1, 3, 25666)`, IoU 0.6446, missing 0, unexpected 0. Weights `yuchen0187/Point-SAM` `model.safetensors`.
- SAM3D 2D half: image `(480, 640, 3)`, prompt pixel about `(319.4, 236.8)`, 3 masks, best score 1.0047. Weights `sam_vit_h_4b8939.pth`.
- SAM3D 3D half: `knn_query` index shape `(25666, 8)` on the 4080 SUPER.

## Needs you at the keyboard

Nothing. No license dialog, dongle, GUI, Windows UAC, Hugging Face login, CUDA toolkit MSI, or reboot was required, and none of the nine is waiting on one.

These are notes, not clicks:

- On Windows, `grow_labels` shells out to `wsl $HOME/bin/pcl_region_grow`. The binary and `libpcl_segmentation.so.1.14` stay under the WSL home. If `wsl` or that binary is missing, the NumPy fallback still runs.
- Do not `pip install` the OpenMask3D or Segment3D requirement scripts as written. They pin torch 1.12.1+cu113 and would replace the working CUDA stacks. sm_89 needs the torch 2.x builds already on this machine.
- A later full OpenMask3D run (CLIP features) needs posed RGB-D frames. This synthetic stud does not have them.
- A later Segment3D `scripts/run_demo.sh` run needs cuML (RAPIDS). That package was not installed. The network forward does not need it.

## First round (`stage0_2x4_lean0.000` only)

Runner: `scripts/phase_neg1_stage0_round.py` (`--role geometry` in the main `.venv`, `--role pointcept` in the ranks45 torch 2.7 env, `--role o3dml` in the ranks45 torch 2.13 env). Date on the new day-table rows: **2026-09-25** (America/Los_Angeles). The 2026-09-24 `not_run` stubs for this scene stay. CloudCompare was not run.

Shared geometry on every `pass` row below: precision 1, recall 1, one true positive, section error 7.86 mm, length error 6.24 mm, angle MAE 0.03084 deg, 100% in band, production paint all yellow. Stage 0 bars are precision = 1 and recall = 1, section ≤ 10 mm, length ≤ 25 mm, angle ≤ 0.05 deg, paint all yellow.

| Tool | Entered | Where the result lives | Outcome |
| --- | --- | --- | --- |
| Open3D | yes | Day table `open3d`, card `open3d_stage0_stage0_2x4_lean0.000.json` | **pass**, runtime 0.078 s. The card file is the 2026-09-25 measurement. The 2026-09-24 day row still records the earlier 0.0584 s runtime. |
| PCL 1.14 | yes | Day table `pcl`, card `pcl_stage0_stage0_2x4_lean0.000.json` | **pass**, runtime 3.2854 s. `native_pcl_region_growing` true, binary `wsl:$HOME/bin/pcl_region_grow`, 1 cluster, 154 unassigned. |
| pyRANSAC-3D | yes | Day table `pyransac3d`, card `pyransac3d_stage0_stage0_2x4_lean0.000.json` | **pass**, runtime 1.1904 s. First cuboid inliers 25,666 of 25,666. Wall-swallow did not fire. |
| Pointcept control | yes | Day table `pointcept`, card `pointcept_stage0_stage0_2x4_lean0.000.json` | **control**, runtime 43.0777 s. BIMStruct vocabulary has no stud class. Stud cells stay null. |
| Open3D-ML control | yes | Day table `open3d_ml`, card `open3d_ml_stage0_stage0_2x4_lean0.000.json` | **control**, runtime 0.7651 s. S3DIS vocabulary has no stud class. Stud cells stay null. |
| Pointcept 2-class head | yes | Card only: `pointcept_finetune_stage0_stage0_2x4_lean0.000.json` | **pass**, runtime 0.0937 s. All 25,666 points labeled stud. No day-table row, so the control row is not replaced. Weight `pointcept_stud_2class.pth` was not rewritten. |
| Open3D-ML 2-class head | yes | Card only: `open3d_ml_finetune_stage0_stage0_2x4_lean0.000.json` | **pass**, runtime 0.1777 s. All 25,666 points labeled stud. No day-table row. Weight `randlanet_stud_2class.pth` was not rewritten. |
| Point-SAM | smoke forward only | No stud-bar scorecard in this repo | Mask `(1, 3, 25666)`, IoU 0.6446. No mask-to-stud mapping was added. |
| SAM3D | smoke forward only | No stud-bar scorecard in this repo | ViT-H: 3 masks, best score 1.0047. `pointops.knn_query` index `(25666, 8)`. The ScanNet multi-frame path was not run. |
| OpenMask3D | smoke forward only | No stud-bar scorecard in this repo | Mask module output `(25666, 100)`. CLIP / posed RGB-D was not run. |
| Segment3D | smoke forward only | No stud-bar scorecard in this repo | `pred_logits` `[1, 100, 2]`, 469 tensors loaded. cuML demo postprocess was not run. |

## Env cheat sheet

| Piece | Path |
| --- | --- |
| Open3D and pyRANSAC-3D | `C:\Repos\openwall-stud-frame\.venv\Scripts\python.exe` |
| Pointcept and the SAM ViT-H half | `C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe` (torch 2.7.0+cu126) |
| Open3D-ML | `C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml\Scripts\python.exe` (torch 2.13.0+cu126) |
| PCL 1.14.1 binary | WSL `/home/pegassy/bin/pcl_region_grow` |
| PCL libraries | `/home/pegassy/src/pcl-1.14.1-build/lib` plus `/home/pegassy/pclenv/lib` on `LD_LIBRARY_PATH` |
| PCL rebuild | `tools/wsl_build_pcl_1_14.sh` (builds `pcl_ml` and `pcl_segmentation` only; gcc 15 breaks `pcl_registration`) |
| Point-SAM Python | WSL `/home/pegassy/mlenv/bin/python` (torch 2.14.0+cu126) |
| nvcc | `/home/pegassy/cudaenv/bin/nvcc` 12.6.85, host gcc 12.4.0. `TORCH_CUDA_ARCH_LIST=8.9` |
| torkit3d | `tools/wsl_build_torkit3d.sh` |
| Point-SAM weights | `data/cache/phase_neg1/pointsam/model.safetensors` (gitignored) |
| SAM ViT-H weights | `data/cache/phase_neg1/sam/sam_vit_h_4b8939.pth` (gitignored) |
| SAM3D pointops | `tools/wsl_build_sam3d_pointops.sh` |
| MinkowskiEngine | fork `L-Reichardt/MinkowskiEngine` commit `1a9aab5`, installed 0.6.0 into `mlenv`. Build: `tools/wsl_build_minkowski.sh`. OpenBLAS: `/home/pegassy/blasenv` |
| pointnet2 | `tools/wsl_build_pointnet2.sh` |
| detectron2 | `tools/wsl_build_detectron2.sh` |
| OpenMask3D mask smoke | `scripts/phase_neg1_openmask3d_smoke.sh` |
| OpenMask3D weights | `data/cache/phase_neg1/openmask3d/mask_module_arbitrary.ckpt` |
| Segment3D smoke | `scripts/phase_neg1_segment3d_smoke.py` |
| Segment3D weights | `data/cache/phase_neg1/segment3d/segment3d.ckpt` |
| Clones (gitignored) | `artifacts/third_party/Point-SAM`, `SegmentAnything3D`, `openmask3d`, `Segment3D` |

Published fine-tune weights under `artifacts/weights/finetune/` were not overwritten. The supervised one-step ran in memory only.
