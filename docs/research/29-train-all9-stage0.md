# Train stud heads + all-nine stage0 one-beam

Date (America/Los_Angeles): **2026-09-25**. Host: **Oz_PC** (RTX 4080 SUPER). Builds on the Phase −1 install in [28-phase-neg1-nine-tool-install.md](28-phase-neg1-nine-tool-install.md) / PR #32. CloudCompare stays **out** of the bake-off.

Scene: `stage0_2x4_lean0.000` — `stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)`, **25,666** points, 5 mm spacing, 1 mm noise. Lean reference is generator **+Z** (no floor). Device ε unlocked → production paint yellow only. Stage 0 bars unchanged: precision=1, recall=1, section ≤ 10 mm, length ≤ 25 mm, angle ≤ 0.05°, paint all yellow.

This is **not** a full bake-off train and **not** a field score.

## Supervised train (separate stud heads)

Published BIMStruct3D and S3DIS semantic checkpoints were **not** rewritten. New 2-class (clutter / stud) heads were trained on the synthetic curriculum in `data/finetune/synthetic_stud_manifest.json` (386 train / 33 val clouds; phase-1 S1 seed-2 ladder held out of train).

| Stack | Epochs | Wall | Final train loss | Val selection score | Checkpoint |
| --- | --- | --- | --- | --- | --- |
| Open3D-ML RandLA-Net 2-class | 3 | 146.6 s | 0.0137 | 0.9898 (epoch 3) | `artifacts/checkpoints/stud-heads/randlanet_stud_2class.pth` |
| Pointcept PTv3 2-class MLP | 2 head-only (backbone frozen) | 58.6 s | 0.0010 | 0.9904 (epoch 2) | `artifacts/checkpoints/stud-heads/pointcept_stud_2class.pth` |

Logs: `artifacts/checkpoints/stud-heads/*_train_log.json`. README in that folder states these are stud heads, not published semantic weights. Older archive copies under `artifacts/weights/finetune/` were left in place; loaders prefer `stud-heads/`.

## All-nine stage0 outcomes

Coherent runner: `scripts/phase_neg1_all_nine_stage0.py`. Table JSON: `artifacts/phase_neg1/all_nine_stage0.json`.

| # | Tool | Bucket | Status | Runtime (s) | One-line reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Open3D | geometry-first | **pass** | 0.054 | Shared minimal OBB; section 7.86 mm, length 6.24 mm, angle MAE 0.03084°. |
| 2 | PCL 1.14 | geometry-first | **pass** | 3.339 | Native WSL RegionGrowing; 1 cluster. |
| 3 | pyRANSAC-3D | geometry-first | **pass** | 1.244 | Cuboid inliers 25,666/25,666. |
| 4 | Pointcept stud head | supervised | **pass** | 0.077 | New 2-class head; all points labeled stud. Published BIMStruct control stays `control` (~42 s). |
| 5 | Open3D-ML stud head | supervised | **pass** | 0.145 | New 2-class head; all points labeled stud. Published S3DIS control stays `control` (~0.51 s). |
| 6 | Point-SAM | promptable foundation | **pass** | 0.314 | Zero-shot point prompt; best IoU mask → stud labels (349 stud pts). Not a stud-trained head. |
| 7 | SAM3D (Yang et al.) | promptable foundation | **fail** | 0.243 | ViT-H scaffold pinhole lift only (ScanNet multi-frame not run). Bars: length 1427.98 mm > 25; angle 0.06871° > 0.05. **Superseded by doc 30** (full-stud multi-view → pass). |
| 8 | OpenMask3D | promptable foundation | **pass** | 0.025 | Class-agnostic **mask module** scored. CLIP / posed RGB-D open-vocab stage **blocked** (synth has no posed RGB-D). **Superseded by doc 30** (synth posed RGB-D + CLIP → pass, CLIP unblocked). |
| 9 | Segment3D | promptable foundation | **pass** | 0.552 | Zero-shot Mask3D best query → points via inverse_map. cuML demo postprocess not run. |

Scorecards: `artifacts/scorecards/{open3d,pcl,pyransac3d,pointcept,pointcept_finetune,open3d_ml,open3d_ml_finetune,pointsam,sam3d,openmask3d,segment3d}_stage0_stage0_2x4_lean0.000.json`.

## Reproduce (Oz_PC)

```bat
rem Train (short; not full bake-off)
C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml\Scripts\python.exe scripts\train_randlanet_stud.py --epochs 3
C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe scripts\train_pointcept_stud.py --epochs 2 --decoder-epochs 0

rem All nine on stage0
.\.venv\Scripts\python.exe scripts\phase_neg1_all_nine_stage0.py
```

Env cheat sheet (same as doc 28):

| Piece | Path |
| --- | --- |
| Open3D + pyRANSAC-3D | `C:\Repos\openwall-stud-frame\.venv` |
| Pointcept + SAM ViT-H | `C:\Repos\openwall-stud-frame-ranks45\.venv` |
| Open3D-ML | `C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml` |
| Point-SAM / OpenMask3D / Segment3D | WSL `/home/pegassy/mlenv` |
| PCL | `wsl $HOME/bin/pcl_region_grow` |

Foundation writers alone:

```bat
C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe scripts\phase_neg1_stage0_foundation.py --tool sam3d
wsl -e /home/pegassy/mlenv/bin/python /mnt/c/Repos/openwall-stud-frame/scripts/phase_neg1_stage0_foundation.py --tool pointsam
wsl -e /home/pegassy/mlenv/bin/python /mnt/c/Repos/openwall-stud-frame/scripts/phase_neg1_stage0_foundation.py --tool openmask3d
wsl -e /home/pegassy/mlenv/bin/python /mnt/c/Repos/openwall-stud-frame/scripts/phase_neg1_stage0_foundation.py --tool segment3d
```

OpenMask3D mask module must already have produced `artifacts/phase_neg1/openmask3d_masks/stage0_2x4_lean0_masks.pt` (from `scripts/phase_neg1_openmask3d_smoke.sh`). Do **not** run upstream OpenMask3D/Segment3D requirement scripts (old torch).

## Needs you at the keyboard

Nothing.

## Product locks honored

- Paint yellow only (device ε unlocked).
- Synth lean reference: generator +Z (no floor on this scene).
- τ ≈ 0.12° is industry in-band, not paint.
- Four-way classification unchanged; CloudCompare out.
- Stud heads labeled and stored separately from published semantic weights.
- No fabricated metrics; SAM3D fail and OpenMask3D CLIP block are recorded honestly.
