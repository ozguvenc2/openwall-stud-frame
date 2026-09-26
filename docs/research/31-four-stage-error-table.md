# Four-stage error evolution — all nine on stage0 lean0

Date (America/Los_Angeles): **2026-09-26**. Follows [30-fix-sam3d-openmask3d-stage0.md](30-fix-sam3d-openmask3d-stage0.md) / PR #34. CloudCompare stays **out**. Paint yellow; device ε unlocked. No fabricated metrics.

Scene: `stage0_2x4_lean0.000` — `stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)`, **25,666** points, `spacing_m=0.005`, `noise_std_m=0.001`. Scorecard table: `artifacts/phase_neg1/all_nine_stage0.json` (underscore path).

This note decomposes each model’s scorecard error into four stages. It is **not** Absolute field GT and **not** a bake-off re-run.

## The four stages

| Stage | Name | What it is | Section / length / angle |
| --- | --- | --- | --- |
| 1 | **Absolute truth (Synthetic GT)** | Planted generator values. Errors = 0 by definition. | Dressed 2×4 section **38.1 × 88.9 mm** (`DRESSED_SECTION_M`), length **2438.4 mm** (`STUD_LENGTH_8FT_M` = 96×0.0254 m), lean **0°**. |
| 2 | **Post-sampling noise** | Cloud scatter from the generator **before** any finder. Isotropic Gaussian `noise_std_m=0.001` (1 mm) per axis on surface points. | Measured: fit shared **minimal OBB** on the full noisy cloud with perfect stud labels (all 25,666 points — stage0 has no floor or clutter). Method below. |
| 3 | **Realisticized GT** | Stage1 planted values plus a **Skil-class level-device** uncertainty band of **~±0.05°** on angle (`PLACEHOLDER_EPSILON_DEG` / near-plumb band). Calibrated theoretical — **not** Absolute field GT. | Section and length: device adds **nothing** (angle-only). Angle truth remains **0°** with **±0.05°** uncertainty. |
| 4 | **Algorithm measurement** | Existing `all_nine_stage0.json` scorecard cells versus Synthetic GT. | `section_mm`, `length_mm`, `angle_mae_deg`, `runtime_s` as published in doc 30. |

### Stage2 method (measured, not invented)

One-shot on this agent, same code path as the bake-off scorer:

1. Build `stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)` (`src/openwall_stud/synthetic.py`).
2. Fit `PointCloud.get_minimal_oriented_bounding_box()` via `_obb_segments` in `open3d_baseline.py` on **all** points (perfect mask).
3. Score like `score_run`: max abs section error vs dressed nominal, abs length error vs planted length, abs lean vs generator +Z.

**Measured Stage2 (seed=1, bake-off scene):**

| Metric | Stage2 noise deviation |
| --- | --- |
| Section | **7.86 mm** (components ≈ +7.86 / +7.16 mm on thickness/width) |
| Length | **6.24 mm** (signed +6.24 mm; box fat from Gaussian tails) |
| Angle | **0.03084°** (not ~0; OBB long axis tilts under 1 mm noise even at planted lean 0°) |

`stage0_single_stud` defaults `seed=0`; the phase −1 / all-nine runners use **seed=1** ([29-train-all9-stage0.md](29-train-all9-stage0.md)). Seed 0 on the same generator yields a different OBB (section 7.52 mm, length 5.45 mm, angle 0.01897°) — not the bake-off cloud.

### Stage3 / algorithm-only attribution

- **Stage3 truth** keeps planted section, length, and lean **0°**, with a Skil-class **±0.05°** band on angle only.
- **Error vs Stage3 (algorithm-only):**
  - Section / length: Stage3 does not move those truths, so these columns equal Stage4 measured (same numbers as cumulative vs Stage1). They still include Stage2 sampling inflation; they are **not** “finder-only after subtracting noise.”
  - Angle: residual after attributing **up to 0.05°** of the absolute scorecard error to the device band: `max(0, angle_mae_deg − 0.05)`. Every model on this scene has `angle_mae_deg ≤ 0.05°`, so algorithm-only angle residual is **0°**.
- **Cumulative error vs Stage1** = Stage4 scorecard errors as today (vs Synthetic GT).

## Compact summary table

Cells are `section_mm / length_mm / angle_deg` unless noted. Stage1 and Stage3 truths are planted values (Stage3 angle carries ±0.05°). Stage2 is one shared cloud measurement. Stage4 and Cumulative are from `artifacts/phase_neg1/all_nine_stage0.json`.

| Model | Family | Stage1 truth | Stage2 noise | Stage3 realisticized | Stage4 measured | Err vs Stage3 (algo) | Cumul. vs Stage1 | Runtime (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| open3d | geometry-first | 38.1×88.9 / 2438.4 / 0° | 7.86 / 6.24 / 0.03084° | 38.1×88.9 / 2438.4 / 0°±0.05° | 7.86 / 6.24 / 0.03084° | 7.86 / 6.24 / **0°** | 7.86 / 6.24 / 0.03084° | 0.0546 |
| pcl | geometry-first | same | same | same | 7.86 / 6.24 / 0.03084° | 7.86 / 6.24 / **0°** | 7.86 / 6.24 / 0.03084° | 2.3064 |
| pyransac3d | geometry-first | same | same | same | 7.86 / 6.24 / 0.03084° | 7.86 / 6.24 / **0°** | 7.86 / 6.24 / 0.03084° | 1.2024 |
| pointcept_stud_head | supervised | same | same | same | 7.86 / 6.24 / 0.03084° | 7.86 / 6.24 / **0°** | 7.86 / 6.24 / 0.03084° | 0.0798 |
| open3d_ml_stud_head | supervised | same | same | same | 7.86 / 6.24 / 0.03084° | 7.86 / 6.24 / **0°** | 7.86 / 6.24 / 0.03084° | 0.1965 |
| pointsam | promptable-foundation | same | same | same | 4.45 / 6.22 / 0.03817° | 4.45 / 6.22 / **0°** | 4.45 / 6.22 / 0.03817° | 0.3496 |
| sam3d | promptable-foundation | same | same | same | 7.83 / 4.30 / 0.03177° | 7.83 / 4.30 / **0°** | 7.83 / 4.30 / 0.03177° | 0.2401 |
| openmask3d | promptable-foundation | same | same | same | 7.21 / 6.24 / 0.03019° | 7.21 / 6.24 / **0°** | 7.21 / 6.24 / 0.03019° | 3.2926 |
| segment3d | promptable-foundation | same | same | same | 7.88 / 6.04 / 0.02398° | 7.88 / 6.04 / **0°** | 7.88 / 6.04 / 0.02398° | 0.4658 |

Family labels match doc 27 / JSON `bucket`: geometry-first / supervised / promptable-foundation.

## Why the first five share identical Stage4

Open3D, PCL, pyRANSAC-3D, Pointcept stud head, and Open3D-ML stud head all return a **full or near-full stud mask** on this one-beam cloud (precision=1, recall=1, effectively all stud points). Every bake-off path then runs the **same shared minimal OBB** post-step (`poststep.detections_from_clusters` / `_obb_segments`). On a perfect mask that OBB is exactly the Stage2 noise box — so Stage4 equals Stage2 to the published digits (7.86 / 6.24 / 0.03084°). Finder identity does not move the geometry once the mask is complete.

## Per-model: which stage dominates

| Model | Dominating stage | Note |
| --- | --- | --- |
| open3d | **Stage2** | Stage4 − Stage2 = 0 on all three metrics. |
| pcl | **Stage2** | Same shared OBB after full mask. |
| pyransac3d | **Stage2** | Cuboid inliers → same shared OBB. |
| pointcept_stud_head | **Stage2** | Stud head labels all points stud → same OBB. |
| open3d_ml_stud_head | **Stage2** | Same. |
| pointsam | **Stage2** (section eased by mask) | Partial mask (zero-shot point prompt) **shrinks** section error vs Stage2 (4.45 vs 7.86 mm) by dropping noisy extremity points; length ≈ Stage2; angle slightly above Stage2 but still inside the 0.05° Stage3 band. |
| sam3d | **Stage2** | Full-stud multi-view lift: section ≈ Stage2; length **below** Stage2 (4.30 vs 6.24 mm); angle ≈ Stage2. |
| openmask3d | **Stage2** | Mask module + synth posed RGB-D CLIP: section slightly below Stage2; length = Stage2; angle ≈ Stage2. |
| segment3d | **Stage2** | Zero-shot Mask3D: section ≈ Stage2; length slightly below; angle lowest of the nine but still Stage2-class. |

On this lean0 scene, **no model’s Stage4 angle exceeds the Stage3 ±0.05° device band**, so algorithm-only angle residual is zero for all nine. Section and length residuals versus Stage1 remain mostly **sampling-noise OBB inflation** (Stage2), not finder failure.

## Product locks honored

- Paint yellow only (device ε unlocked). `PLACEHOLDER_EPSILON_DEG` / Skil near-plumb ±0.05° is Stage3 theoretical only — not a locked measured ε. The dual-pass table below reports colors; it does not flip this lock.
- Synth lean reference: generator +Z (no floor). Stage0 planted lean stays **0°**.
- CloudCompare out of the bake-off.
- No fabricated metrics: Stage2 computed; Stage4 copied from `all_nine_stage0.json`.
- Path: `artifacts/phase_neg1/` (underscore), not `phase-neg1`.

## Dual-standard, dual-reference passes

Date (America/Los_Angeles): **2026-09-26**. Policy for every model on every experiment from here on. **Experiment 1** is this scene: one stud, no floor, no ceiling, planted lean **0°** (`stage0_2x4_lean0.000`). Colors use the stored `angle_mae_deg` cells. Models were not re-run.

Production paint stays **yellow** while device ε is unlocked. The matrix is a reported comparison of model error against two published gauges. It does not choose a new code tolerance and it does not replace the yellow production color.

### Gauges (established, not new)

| Standard | Linear figure | Decision threshold | What it is |
| --- | --- | --- | --- |
| Handbook finish plumb | 1/4 inch in 10 feet | `atan(0.25/120)` = **0.11937°** | Handbook of Construction Tolerances (Ballast), as summarized by WoodWorks ([tolerances.md](../tolerances.md)). This is the literature name for the figure Oz calls **Finnish-style folklore plumb** (~0.12°, sometimes ~0.1°). **Not an AHJ code number.** The repo has no Finnish code citation for it. |
| NAHB warranty gauge | 3/8 inch in 32 inches | `atan(0.375/32)` = **0.67140°** | NAHB Residential Construction Performance Guidelines, guideline 4-1-1 ([doc 36](36-az-framing-standards-inspector-tolerances.md)). Doc 36 rounds the same derivation to **0.671°** (~0.67°). Warranty booklet, not an IRC red tag. |

UFGS and the RSMeans 1/4 inch in 32 inches stay in doc 36. They are not columns.

### Decision rule

Implemented by `dual_standard_passes` in `src/openwall_stud/paint.py`. It calls the existing `paint_stud` interval tests with ε locked **for that column only**.

Let **e** = |measured lean − synthetic truth lean| in degrees. On Experiment 1 the truth lean is 0°, so **e** is the stored `angle_mae_deg` (one stud, so the mean is that single error). Let **τ** be the gauge above. Let **ε** be **0°** on the absolute column and **0.05°** on the sensor column (`SENSOR_EPSILON_DEG`, the same constant as `PLACEHOLDER_EPSILON_DEG`).

- **Green** if the whole interval sits inside the gauge: **e + ε ≤ τ** (`interval_inside`).
- **Red** if the whole interval sits outside the gauge: **e − ε > τ** (`interval_outside`). The outside test is strict.
- **Yellow** if the interval overlaps τ (`interval_overlaps`).

When ε = 0 the interval is the point e, so the color is green if e ≤ τ and red if e > τ. Yellow does not occur. **e = τ is green**, the same edge as the existing “θ + ε = τ is inside” test.

The 0.05° band is the SKIL / digital-level **device** error only. Human placement error and lumber surface or warp defects stay out (doc 33). They are not added to ε.

Stage0 synth lean **0.0°** stays locked. Yellow-until-ε-locked still designs the production color. Yellow in this rule is only the sensor-column overlap.

### Experiment 1 matrix

One matrix for this experiment. Recomputed by `python scripts/score_experiment1_dual_pass.py` from `artifacts/phase_neg1/all_nine_stage0.json`, checked against each scorecard’s `abs_error_deg` and `true_deg = 0`. Artifact: `artifacts/phase_neg1/experiment1_dual_pass.json`. The four-stage cells above keep the same errors and are not given a second color grid. Doc 29’s pre-fix SAM3D angle (0.06871°) is a superseded card, not this round. Published BIMStruct3D and S3DIS controls have null stud lean and are not colored.

| Model | Standard | Threshold (°) | Mean \|err\| (°) | Absolute | With sensor ε 0.05° |
| --- | --- | ---: | ---: | --- | --- |
| open3d | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03084 | green | green |
| open3d | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03084 | green | green |
| pcl | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03084 | green | green |
| pcl | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03084 | green | green |
| pyransac3d | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03084 | green | green |
| pyransac3d | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03084 | green | green |
| pointcept_stud_head | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03084 | green | green |
| pointcept_stud_head | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03084 | green | green |
| open3d_ml_stud_head | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03084 | green | green |
| open3d_ml_stud_head | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03084 | green | green |
| pointsam | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03817 | green | green |
| pointsam | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03817 | green | green |
| sam3d | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03177 | green | green |
| sam3d | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03177 | green | green |
| openmask3d | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.03019 | green | green |
| openmask3d | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.03019 | green | green |
| segment3d | Handbook finish plumb (1/4 in in 10 ft) | 0.11937 | 0.02398 | green | green |
| segment3d | NAHB warranty gauge (3/8 in in 32 in) | 0.67140 | 0.02398 | green | green |

Every model is green on both gauges and both columns. The largest stored error is Point-SAM **0.03817°**. Handbook sensor-green needs e + 0.05° ≤ 0.11937° (e ≤ 0.06937°). The NAHB gauge is wider. The stage 0 bar “angle ≤ 0.05°” is a separate bring-up check. It is not these colors.
