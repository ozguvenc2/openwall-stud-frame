# Synthetic stud fine-tune (ranks 4 and 5)

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC**. GPU: **NVIDIA GeForce RTX 4080 SUPER (16 GB)**.

This pass fine-tunes rank 4 (Pointcept / BIMStruct3D PTv3) and rank 5 (Open3D-ML RandLA-Net) so they have a `stud` class. The clouds are synthetic. No real stud, no phone scan, and no SKIL reading is in the train set, the val set, or the phase-1 inference set. A stud box on these clouds is not field accuracy.

The 25 phase-1 S1 cards (seed 2, 1 mm noise, 5 mm spacing, the locked lean ladder) are not in train or val. Val uses that same magnitude ladder with seed 9001 and 1.5 mm noise, plus eight held-out stud-plus-floor clouds.

## Labels

| id | name | generator part |
| --- | --- | --- |
| 0 | clutter | floor (stage 2). Plates are not a class here. |
| 1 | stud | part 2, the dressed 2×4 |

RGB is zeros on both models, matching the rank 4 and rank 5 controls. Pointcept also gets Open3D normals. Gravity in the generator stays +Z.

## Dataset

Manifest: `data/finetune/synthetic_stud_manifest.json`. Clouds are cached under `data/cache/finetune-synth/` and that cache is gitignored.

| split | clouds | stud only | stud + floor |
| --- | --- | --- | --- |
| train | 386 | 304 | 82 |
| val | 33 | 25 (phase-1 magnitudes) | 8 |

Train leans use ±X and ±Y, including the phase-1 magnitudes at other seeds, plus magnitudes off that ladder (0.02° through 7°). Seeds are 11, 17, 23, 29, 41, and 53. Noise cycles through 0.5 mm, 1 mm, 1.5 mm, and 2 mm. Spacing stays 5 mm. Floor spacing is 15 mm. Each training epoch shows every floor cloud twice so the stud-only clouds do not drown the clutter class.

Rebuild:

```bash
.venv-o3dml\Scripts\python.exe scripts/build_finetune_synth.py
```

## Environment

Both interpreters are Python 3.12.10. CUDA build is 12.6. The GPU is the 4080 SUPER above.

| stack | interpreter | torch | what it loads |
| --- | --- | --- | --- |
| Rank 5 RandLA-Net | `.venv-o3dml` | 2.13.0+cu126 | Open3D 0.20.0 `open3d.ml.torch`. Windows wheel `BUILD_CUDA_MODULE` is false. RandLA-Net itself is PyTorch and runs on the GPU. |
| Rank 4 PTv3 | `.venv` | 2.7.0+cu126 | Pointcept from the gitignored BIMStruct3D cache (`data/cache/bimstruct3d`), plus spconv and peft already in that venv. Flash-attention is off in the bundled config. |

Rank 5 is initialized from the S3DIS RandLA-Net zoo checkpoint (`randlanet_s3dis_202201071330utc.pth`, also gitignored). Every tensor whose shape still matches is copied. The last convolution was 13-way and is a new 2-class layer. Architecture matches `randlanet_s3dis.yml`: 5 layers, 6 input channels (xyz + zero RGB), grid 0.02 m, 8192 points per step.

Rank 4 keeps the bundled PT-v3m1 backbone (`in_channels=6`, color + normal) and replaces the 10-class head with a 2-class MLP (64 → 64 → 2). Training starts on that head with the backbone frozen. If val stud recall on stud-only clouds is under 0.80, or stud IoU on floor clouds is under 0.35, the decoder is unfrozen for two more epochs. The BIMStruct3D `model_best.pth` (about 555 MB, CC BY-NC-SA 4.0) is not committed.

## Commands

From the repo root:

```bash
.venv-o3dml\Scripts\python.exe scripts/train_randlanet_stud.py
.venv\Scripts\python.exe scripts/train_pointcept_stud.py
.venv-o3dml\Scripts\python.exe scripts/infer_finetune_phase1.py --stack randlanet
.venv\Scripts\python.exe scripts/infer_finetune_phase1.py --stack pointcept
```

Scorecards go to `artifacts/scorecards/phase1_s1_finetune/` as `r4_pointcept__…` and `r5_open3d_ml__…`. The control histograms in `artifacts/scorecards/phase1_s1/` are left alone. A stud box is the same minimal OBB the classical finders use, fit on points labeled stud when at least 50 of them exist. Lean is that box's long axis versus generator +Z.

## Reload

Rank 5 is one file, `artifacts/weights/finetune/randlanet_stud_2class.pth`. It does not need the S3DIS zoo file at inference time.

```python
from openwall_stud.finetune_randlanet import build_model, load_checkpoint, weight_path

model = build_model("cuda")
load_checkpoint(model, weight_path())
```

Use the `.venv-o3dml` interpreter (torch 2.13).

Rank 4 needs the gitignored BIMStruct3D cache plus `artifacts/weights/finetune/pointcept_stud_2class.pth` (the new head, and the decoder only if that phase ran).

```python
from openwall_stud.finetune_pointcept import (
    build_model,
    load_bimstruct_backbone,
    load_finetuned,
    weight_path,
)

model = build_model("cuda")
load_bimstruct_backbone(model)
load_finetuned(model, weight_path())
```

Use the `.venv` interpreter (torch 2.7). The cache is the same one `openwall_stud.contenders.pointcept_ptv3` downloads from `dfki-av/BIMStruct3D-segmentation`.

## Results

The Oz_PC train logs and the phase-1 scorecard summaries fill this section. Until those files are written, do not read a stud box here as a finished measurement.

## What this is not

Not a real stud. Not a multi-stud wall. Not a plate class. Not a field mIoU. S3DIS mIoU is not copied. BIMStruct3D's published class list is not a stud score. CC BY-NC-SA base weights are not a commercial model.
