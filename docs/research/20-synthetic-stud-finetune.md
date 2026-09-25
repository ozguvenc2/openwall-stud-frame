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

Rank 5 is initialized from the S3DIS RandLA-Net zoo checkpoint (`randlanet_s3dis_202201071330utc.pth`, also gitignored). Every tensor whose shape still matches is copied. The last convolution was 13-way and is a new 2-class layer. Architecture matches `randlanet_s3dis.yml`: 5 layers, 6 input channels (xyz + zero RGB), grid 0.02 m. Each step uses 16384 points, which covers a whole subsampled cloud here instead of a stud-only neighborhood.

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

Use the `.venv-o3dml` interpreter (torch 2.13). Call `predict_labels` (or `use_batch_norm_stats` before a forward). A plain `model.eval()` still uses the S3DIS batch-norm averages and labels the cloud as stud. `predict_labels` also puts the training point sampler back after Open3D inference, which replaces it.

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

Both trains finished on the 4080 SUPER. The desktop was using about 2.6 GB and the GPU was otherwise idle, so this pass did not wait on the rank-3 CloudCompare job.

| stack | wall time | what changed | checkpoint |
| --- | --- | --- | --- |
| Rank 5 RandLA-Net | 237.5 s (5 epochs, about 48 s each, 468 presentations) | S3DIS encoder copied; new 2-class layer trained | `randlanet_stud_2class.pth`, 20,171,595 bytes, epoch 3 |
| Rank 4 PTv3 | 98.1 s (3 head epochs, about 32 s each) | new 2-class MLP only; backbone frozen (486 tensors copied, 4 trained) | `pointcept_stud_2class.pth`, 38,801 bytes, epoch 2 |

The decoder-unfreeze rule did not fire. Val stud recall on stud-only clouds was 1.0 and floor stud IoU stayed above 0.99, so the decoder epochs did not run.

### Validation

Rank 4, saved epoch-2 head, on the 33 val clouds:

| metric | value |
| --- | --- |
| stud recall, stud-only scenes | 1.0 |
| stud IoU, floor scenes | 0.998 |
| clutter IoU, floor scenes | 0.993 |

Rank 5 is a different reading. `randlanet_train_log.json` scored each epoch with `model.eval()`. Those batch-norm running stats are still the S3DIS averages, so clutter IoU in that log sits near 0. That number is not the result. The same epoch-3 file, scored with per-cloud batch-norm statistics, is `randlanet_val_corrected.json`:

| metric | value |
| --- | --- |
| stud recall, stud-only scenes | 1.0 |
| stud IoU, floor scenes | 0.992 |
| clutter IoU, floor scenes | 0.977 |
| mean runtime on the 33 val clouds | 0.165 s |

Epoch 5 train loss was 0.0057 and that epoch was not saved, because the eval-mode score preferred epoch 3. The measurements below use the epoch-3 file.

### One synthetic stud

Timed after a warmup pass, weights already on the GPU. The cloud is `stage0_2x4_lean0.200_ax+Y` (0.2° about +Y, seed 777). It is not a phase-1 card.

| stack | time | stud points | measured lean | abs error |
| --- | --- | --- | --- | --- |
| Rank 5 | 0.149 s | 25,666 (every point) | 0.216° | 0.016° |
| Rank 4 | 0.050 s | 25,666 (every point) | 0.216° | 0.016° |

The leans match because both models labeled the whole cloud stud, and the box is that cloud's minimal OBB.

### Phase-1 S1

Scorecards are under `artifacts/scorecards/phase1_s1_finetune/`. Summaries are `summary_randlanet.json` and `summary_pointcept.json`. The control cards in `artifacts/scorecards/phase1_s1/` are unchanged.

| stack | stud box and a lean | clutter only |
| --- | --- | --- |
| Rank 5 | 25 / 25 | 0 |
| Rank 4 | 25 / 25 | 0 |

These 25 clouds have no floor. A box on every card does not show that the model rejects clutter. On every phase-1 cloud both models labeled all 25,666 points stud, so the lean is the generator cloud's OBB, identical for both ranks. Mean absolute lean error across the 25 cards is 0.004°. The largest is 0.009° (true 4° about +X, measured 3.991°). On the 0.05° +X card the section error is 7.7 mm and the length error is 5.6 mm.

### Held-out floor

Two val stage-2 clouds, 34,502 points each. A dressed stud in this generator is 25,666 points.

| scene | true lean | rank 5 stud points | rank 5 measured | rank 5 abs error | rank 4 stud points | rank 4 measured | rank 4 abs error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| val_0025 | 0° | 25,466 | 0.194° | 0.194° | 25,675 | 0.138° | 0.138° |
| val_0026 | 0.15° | 25,458 | 0.043° | 0.107° | 25,672 | 0.138° | 0.012° |

Rank 5 misses a couple of hundred stud points. Rank 4 takes a handful of floor points. Section error on these boxes is about 20 mm. One floor cloud takes about 0.31 s (rank 5) or 0.07 s (rank 4).

### Left out of git

`data/cache/finetune-synth/` (the npz clouds), `data/cache/bimstruct3d/` including `model_best.pth` (about 555 MB, CC BY-NC-SA 4.0), and the S3DIS zoo checkpoint. The two fine-tune weight files above are ordinary git blobs.

## What this is not

Not a real stud. Not a multi-stud wall. Not a plate class. Not a field mIoU. S3DIS mIoU is not copied. BIMStruct3D's published class list is not a stud score. CC BY-NC-SA base weights are not a commercial model.
