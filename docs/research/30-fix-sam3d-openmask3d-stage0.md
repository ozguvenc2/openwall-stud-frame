# Fix SAM3D + OpenMask3D; all-nine stage0 re-run

Date (America/Los_Angeles): **2026-09-26**. Host: **Oz_PC** (RTX 4080 SUPER). Follows [29-train-all9-stage0.md](29-train-all9-stage0.md) / PR #33. CloudCompare stays **out**.

Scene unchanged: `stage0_2x4_lean0.000` — 25,666 points, lean ref generator **+Z**, paint yellow (ε unlocked). Stage 0 bars: precision=1, recall=1, section ≤ 10 mm, length ≤ 25 mm, angle ≤ 0.05°.

## What was broken (PR #33)

| Tool | PR #33 | Cause |
| --- | --- | --- |
| SAM3D | **fail** — length 1427.98 mm, angle 0.06871° | `default_stud_camera` FOV-cropped the 8 ft stud to ~1.0 m of visible height; z-buffer lift could not recover full length. |
| OpenMask3D | **pass** on mask module only; CLIP **blocked** | Synth PLY had no posed RGB-D, so the open-vocab CLIP stage never ran. |

## Fixes

### SAM3D

- Added `full_stud_camera()` / `full_stud_cameras()` in `sam2_mask.py` (pulled-back front+back pinholes that keep the full stud in 640×480).
- Left `default_stud_camera` alone for the SAM 2 rank-7 scaffold (that crop is documented).
- `run_sam3d` unions ViT-H mask lifts from both full-stud views.

### OpenMask3D

- `scripts/generate_stage0_posed_rgbd.py` writes ScanNet-style `color/` `depth/` `pose/` `intrinsic/` under `artifacts/phase_neg1/stage0_posed_rgbd/`.
- `openmask3d_clip_stage0.py` runs OpenAI CLIP (`ViT-B/32`) on bbox crops of mask-module instances from those views, scores `(stud−neg) + 0.05×size prior`, picks the stud instance.
- Upstream SAM multi-round crop refiner is **not** run (documented). CLIP stage status is `ran_synth_posed_rgbd`, not blocked.
- mlenv needed `openai-clip`, `ftfy`, `regex`, `segment-anything`, and `setuptools<81` (for `pkg_resources`).

## All-nine stage0 outcomes (this re-run)

Coherent runner: `scripts/phase_neg1_all_nine_stage0.py`. Table JSON: `artifacts/phase_neg1/all_nine_stage0.json`.

| # | Tool | Bucket | Status | Runtime (s) | One-line reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Open3D | geometry-first | **pass** | 0.055 | Shared minimal OBB. |
| 2 | PCL 1.14 | geometry-first | **pass** | 2.306 | Native WSL RegionGrowing. |
| 3 | pyRANSAC-3D | geometry-first | **pass** | 1.202 | Cuboid inliers. |
| 4 | Pointcept stud head | supervised | **pass** | 0.080 | Separate 2-class head. |
| 5 | Open3D-ML stud head | supervised | **pass** | 0.197 | Separate 2-class head. |
| 6 | Point-SAM | promptable foundation | **pass** | 0.350 | Zero-shot point prompt. |
| 7 | SAM3D (Yang et al.) | promptable foundation | **pass** | 0.240 | Full-stud multi-view ViT-H lift; length 4.3 mm, angle 0.03177°. |
| 8 | OpenMask3D | promptable foundation | **pass** | 3.293 | Mask module + synth posed RGB-D CLIP; CLIP no longer blocked. |
| 9 | Segment3D | promptable foundation | **pass** | 0.466 | Zero-shot Mask3D. |

**Verdict: 9/9 pass on stage0_2x4_lean0.000.** SAM3D and OpenMask3D now pass. Published BIMStruct3D / S3DIS controls remain `control` (~42 s / ~0.47 s).

Industry green/yellow/red for this same one-stud scene (Experiment 1) is the dual-pass matrix in [31-four-stage-error-table.md](31-four-stage-error-table.md): Handbook finish plumb (0.11937°) and NAHB warranty gauge (0.67140°), each with an absolute column and a SKIL 0.05° sensor column. Those colors were recomputed from the stored `angle_mae_deg` cells. They do not replace the stage 0 bars above, and production paint stays yellow.

## Reproduce (Oz_PC)

```bat
.\.venv\Scripts\python.exe scripts\generate_stage0_posed_rgbd.py
.\.venv\Scripts\python.exe scripts\phase_neg1_all_nine_stage0.py
```

Foundation-only:

```bat
C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe scripts\phase_neg1_stage0_foundation.py --tool sam3d
wsl -e /home/pegassy/mlenv/bin/python /mnt/c/Repos/openwall-stud-frame/scripts/phase_neg1_stage0_foundation.py --tool openmask3d
```

OpenMask3D mask module artifact must already exist at `artifacts/phase_neg1/openmask3d_masks/stage0_2x4_lean0_masks.pt` (from `scripts/phase_neg1_openmask3d_smoke.sh`). Do **not** run upstream OpenMask3D/Segment3D requirement scripts (old torch).

## Needs you at the keyboard

Nothing.

## Product locks honored

- Paint yellow only (device ε unlocked).
- Synth lean reference: generator +Z (no floor).
- τ ≈ 0.12° is industry in-band, not paint.
- CloudCompare out. No fabricated metrics.
- Synth designed leans only.
