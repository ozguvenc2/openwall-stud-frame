# Stud segmentation design plan

Date: **2026-09-24**. This is the working plan for finding vertical studs, boxing them, and painting lean. The ranked stacks and the floor-versus-gravity rule live in [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md). This file is the curriculum, the pass bars, and the code that exists now.

Machine-readable twin: [12-stud-seg-design-plan.json](12-stud-seg-design-plan.json). Figures: [images/algo-contenders/INDEX.md](images/algo-contenders/INDEX.md).

## Goal

On a bare wood frame (no drywall, no sheathing), instance-segment **vertical studs**, fit one tight oriented box each, measure the long-axis angle, and paint **green / yellow / red** only after a device error band ε exists.

Until ε is locked, every stud is **yellow**. A binary green/red overclaims. The working tolerance τ is the derived **~0.12°** in [../tolerances.md](../tolerances.md): `atan((1/4 inch) / (10 feet)) ≈ 0.1194°`. It is the Handbook figure as summarized by WoodWorks, not an IRC clause.

The product phase reports that angle against the **floor normal** (doc 11). The cloud is not rotated onto the floor. A later inclinometer or IMU replaces the reference vector. The boxes stay. Stage 0 has no floor, so the generator’s **+Z** is the reference and the scorecard says so.

Plates are peeled. They are not a QA class in this plan. King, jack, and cripple names are not required.

## Scorecard

Every stage, every algorithm, one JSON object with these sections. The writer is `openwall_stud.scorecard`. Missing measurements are `null`. This plan does not fill them in from a paper.

| Section | What it holds |
| --- | --- |
| Detection | Precision and recall. One box per physical stud. A merged bay is a miss. Match radius on synthetic scenes is 0.15 m. |
| Geometry | The two smaller OBB extents versus dressed 2×4 (38.1 × 88.9 mm) or 2×6 (38.1 × 139.7 mm), and the long extent versus length. |
| Angle | MAE and the percent of studs whose absolute error versus the reference (synthetic truth, or SKIL once a stud is standing) is inside τ. |
| Paint | Production color. Unlocked ε forces yellow. A placeholder ε of **0.05°** may be stored beside it and is not a device measurement. |
| Cost | Runtime, license, hardware, and the failure modes we already know. |

Trial budget: about **five** Wrong / Expected / Change loops per algorithm family. Loop 0 for Open3D is the IntCDC log in doc 11. Loop 1 is the synthetic bring-up below. Loops 2–5 are unused. PCL, CloudCompare, Pointcept, and Open3D-ML have not spent a loop.

The living bake-off log is [13-stud-seg-results-by-day.md](13-stud-seg-results-by-day.md). Each row is one algorithm against one scene’s ground truth on one America/Los_Angeles date. The CSV (`artifacts/scorecards/results_by_day.csv`) is the copy to append. `scripts/run_stage0_baseline.py` upserts a row when a run finishes. Stub stacks are recorded as `not_run` with null metrics. While device ε is empty, `paint_correct_pct` only checks that the production color is yellow.

## Ranked contenders — what we do with each

Order is doc 11. Status is this repo today.

| Rank | Stack | This repo | Next real experiment |
| --- | --- | --- | --- |
| 1 | Refined Open3D. Horizontal slab peel, DBSCAN with `eps` below the bay gap, 2×4 / 2×6 prior, minimal OBB, shared paint. | **Ready** on synthetic stages 0, 2, 3, and the stage-5 room. `scripts/run_stage0_baseline.py` and `scripts/run_curriculum_through_room.py`. | A real single stud (stage 1) with SKIL on it. Keep ε unlocked. |
| 2 | PCL region growing, then a cuboid in the Özkan / Pöchtrager sense. **No** Bassier remote coplanar merge. **No** axis forced to Z. | Phase 1 scored a NumPy port. **Not re-run** on the room. | Same clouds as rank 1 when PCL is present. Count merged bays. |
| 3 | CloudCompare RANSAC Shape Detection, CloudComPy optional for batch. Schnabel primitives. GPL-3.0 if linked. | Phase 1 scored it. **Not re-run** on the room. | On a multi-stud cloud, compare primitive count to stud count. |
| 4 | Pointcept PTv3 / PointGroup. | Phase 1 control and a synthetic fine-tune exist. **Not run** on the room (no GPU weights here). The synthetic room is not the training gate. | Labels on a real stage-5 capture, then a fine-tune. BIMStruct3D zero-shot stays a control. |
| 5 | Open3D-ML RandLA-Net or KPConv, S3DIS weights. | **Stub on this curriculum pass.** Phase 1 already ran it as a control and as a synthetic fine-tune. | One forward pass on a real stage-5 capture. The synthetic room below is not that gate. Do not paint from S3DIS labels. Do not copy S3DIS mIoU. |
| 6 | pyRANSAC-3D v0.7.0 sequential cuboid after the rank-1 peel. Bake-off add. Not master-table row 6 (Chen 2025). | **Not re-run here.** Phase 1 S1 already scored it. | Same clouds as rank 1 when a machine runs the sweep. Not required for the synthetic room card. |
| 7 | SAM 2 image/video mask, lifted onto points. Bake-off add. Not master-table row 7 (EdgeWise). | **Scaffold.** Projection ran. Weights did not. Stud metrics null. `python -m openwall_stud.contenders.sam2_mask`. | A registered RGB or depth view, then a mask, then the shared box. Doc 24. |

Shared post-step, once a stack actually returns stud points: tight box, θ versus the stored reference, then `openwall_stud.paint`. Ranks differ in the first arrow only.

On 2026-09-25 the five finders were attempted on one synthetic 2×4 at 0.05° lean (seed 2). See [16-one-stud-five-finder-run.md](16-one-stud-five-finder-run.md). Phase 1 then ran the six-finder lean sweep. The curriculum continuation in [24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md) adds SAM 2 as bake-off rank 7 and carries rank 1 through a synthetic room. It does not replace those earlier notes.

The painted-corner pilot (PR [#24](https://github.com/ozguvenc2/openwall-stud-frame/pull/24)) and the synthetic neural corner (PR [#23](https://github.com/ozguvenc2/openwall-stud-frame/pull/23)) are a **parallel** experiment. They are not a stage in the ladder below and they are not a gate on it.

Pictures: rank 1 is a drawing of the real run. Ranks 2–5 are diagrams with a scaffold banner. The wall in those diagrams is the synthetic stage 3 input, not that stack’s output.

## Stage ladder

| Stage | Scene | What “done” means here | Angle reference |
| --- | --- | --- | --- |
| 0 | Synthetic single stud, 2×4 or 2×6, gravity +Z. | The baseline finds it, boxes it, and reports θ. **In this repo.** | Generator +Z. |
| 1 | One real stud, isolated. SKIL at BOT / MID / TOP if the stud is standing. | Detection on a real cloud. Angle MAE only if three level readings exist and agree. | SKIL mean, else no MAE and yellow. |
| 2 | Stud plus a floor or slab. Floor removed, stud kept. | **In this repo** on a synthetic slab. The cloud is not leveled onto that plane. | Floor normal. |
| 3 | Mini wall, 3–5 studs, little noise. First product-shaped milestone. | **In this repo** on four synthetic 2×4s at 16 inch centers, with plates. No merged bay. | Floor normal. |
| 4 | One real wall, plus opening clutter. | Same stud class. Do not require king / jack / cripple labels. | Floor normal, SKIL on a sample of studs. |
| 5 | One room or bay with a LOT-62 look (a single framed bay you can walk). | A **synthetic** look-alike is in this repo (`stage5_room_bay_lot62_look`). Rank 1 has a scorecard. It is not the Lot 62 Polycam file and not a real capture. It does not open training. A real stage-5 capture is still the cloud later training is allowed to see. | Floor normal on the synthetic room. SKIL sample only on a real capture. |
| 6 | Whole single-story frame. | Stub only. Needs a real capture. The synthetic room is not this stage. | Same reference rule. |
| 7 | Two-story or a complex frame. | Stub only. Needs a real capture. | Same reference rule. |

Stage 1 and stage 4 have no clouds in git. Stages 6 and 7 have stub cards with null metrics. Stage 5 has a synthetic cloud and a rank-1 card, and that card is not a field score.

## Capture protocol

Sensors, in the order we will actually touch them. Doc 01 still stands: phone LiDAR and a Livox Mid-360 are not the instrument whose published specs sit inside ~0.12°. Survey TLS (Focus / RTC360 class) is. Starting earlier is allowed for detection. It is not allowed to paint green or red.

1. **iPhone LiDAR**, Polycam PLY or LAS, for stage 1 detection. Point-cloud export is Business and Enterprise (doc 01). Do not treat the file as gravity-aligned unless the capture path stored an ARKit gravity vector. That fact is still unverified for Polycam.
2. **Livox Mid-360** on a tripod when the same stud needs a denser cloud. Static accelerometer for an up vector if we need one (doc 02). Range precision on the spec sheet is still coarser than the tip budget. Record the unit and the pose.
3. **Survey TLS** when a green/red call is the point of the session. Use the scanner inclinometer or DAC as the gravity vector (doc 02). Do not then level the cloud to the floor.

**SKIL (or any digital level), BOT / MID / TOP**, stages 1 and up, when the stud is standing and the face is reachable:

- One face of one stud. Bottom third, mid-height, top third.
- Write the level model, the resolution printed on that model, the three readings, and the sign (which way the face leans).
- Do not invent a resolution. If the three readings differ by more than that printed resolution, mark the stud yellow and do not publish an MAE for it. The spread rule stays that sentence until the first session shows a better one.
- The scorecard angle reference is the mean of the three only when they agree. Stage 0 uses the generator instead of a level. There is no SKIL number in this repo.

Every capture records: sensor, export format, whether Z is gravity or only the file axis, and the floor-normal vector if one was fit. Plates and headers stay in the cloud as things to peel or ignore.

## Working order

1. Stage 0 Open3D bars. Done on synthetic data in this tree.
2. Stage 2 floor peel on a synthetic slab. Done beside stage 0.
3. Stage 3 mini wall. Done on synthetic data. This is the gate for “the bay did not merge.”
4. The same three scenes through PCL, on a machine that has PCL. Stop if bays merge or studs split.
5. CloudCompare on the stage 3 cloud. Record primitive count versus stud count. Not a CI dependency.
6. Real stage 1: one stud, phone or Mid-360, SKIL if it is standing. Yellow paint only.
7. Stage 4: one wall and an opening. Still one class, “stud.”
8. Stage 5: one room. The synthetic look-alike can be scored with rank 1 before a capture exists. Label studs for training only after the classical scorecard on a **real** capture is written. Then Pointcept may be trained. Open3D-ML runs once as a histogram, not as a painter. The synthetic room does not replace that gate.
9. Stages 6 and 7 after stage 5 is a real capture, not a synthetic stand-in. Their cards stay null until then.

## Pass / fail bars

These bars are the synthetic bring-up checks in `scripts/run_stage0_baseline.py`. A miss fails that script. They are not a field acceptance test and not a claim about phone LiDAR.

| Stage | Detection | Section | Length | Angle | Paint |
| --- | --- | --- | --- | --- | --- |
| 0 | Precision = 1 and recall = 1 | Max absolute section error ≤ 10 mm | ≤ 25 mm | Max absolute error ≤ 0.05° | Every production color yellow |
| 2 | Same | ≤ 10 mm | ≤ 25 mm | ≤ 0.05° | Yellow |
| 3 | Same, and `n_pred` equals the stud count | ≤ 10 mm | ≤ 30 mm | ≤ 0.10° | Yellow |

The stage 3 length bar is wider because the plate slab removes a few millimeters at each end of the stud. The measured shortening on this run is about 20 mm, inside the bar.

Stages 1, 4, 6, and 7: no numeric bar yet. Stage 5 has generator truth on the synthetic room and still has no acceptance bar. Paint stays yellow.

“Percent in band” uses τ (~0.1194°) as the band on the angle error versus the reference. It is not the paint decision. Paint needs ε as well, and ε is unlocked.

## What this PR ran

Open3D 0.20, CPU, seed per scene, surface spacing 5 mm, Gaussian noise 1 mm standard deviation. Floor grid is coarser (10–12 mm). Dressed sizes are the generator’s inputs (1.5 × 3.5 in, 1.5 × 5.5 in, 8 ft). Scorecards: `artifacts/scorecards/open3d_stage*.json`.

| Scene | P / R | Max section error | Max length error | Angle error | Reference |
| --- | --- | ---: | ---: | ---: | --- |
| Stage 0, 2×4, lean 0° | 1 / 1 | 7.86 mm | 6.24 mm | 0.03084° | +Z |
| Stage 0, 2×4, lean 0.05° | 1 / 1 | 7.7 mm | 5.57 mm | 0.00345° | +Z |
| Stage 0, 2×4, lean 0.12° | 1 / 1 | 7.39 mm | 4.85 mm | 0.01358° | +Z |
| Stage 0, 2×4, lean 4° | 1 / 1 | 7.86 mm | 4.99 mm | 0.02471° | +Z |
| Stage 0, 2×6, lean 0.30° | 1 / 1 | 7.57 mm | 6.02 mm | 0.00582° | +Z |
| Stage 2, 2×4 on a slab, lean 0.20° | 1 / 1 | 7.84 mm | 8.16 mm | 0.01721° | Floor normal |
| Stage 3, four 2×4s | 1 / 1 | 7.76 mm | 22.19 mm | MAE 0.00426°, max 0.00719° | Floor normal |

All seven are inside the bars above. Percent in band is 100 on each of these scenes. Production colors are yellow. Runtimes on this process were about 0.07–0.09 s for one stud and 0.34 s for the mini wall. That is this machine, not a field budget.

The ~8 mm section error is the point cloud, not a loose box: 1 mm Gaussian tails on a face of ~25k points push the extrema several millimeters out, and the minimal OBB matches that extent. A PCA box on the same 4° stud was about 50 × 104 mm and was rejected for that reason.

Stage 3 length is short by 19–22 mm because the horizontal-slab peel deletes the plate and a thin band of stud end. Angle on that scene is the error against the generator axis expressed in the fitted floor frame, so a stud generated at 0° shows a few thousandths of a degree once the floor normal is not exactly +Z.

Placeholder ε = 0.05° (not locked) would have painted the stage 0 rows green, green, yellow, red, and red in the order of the table. Those colors are in the scorecards as `hypothetical_colors`. They are not the QA call.

### Open3D loop 1 (synthetic bring-up)

| | |
| --- | --- |
| Wrong | `eps` 20 mm and `min_points` 80 marked the whole stud as DBSCAN noise, because a 5 mm surface grid does not put 80 neighbors inside 20 mm. The PCA box then inflated the section. |
| Expected | One box per stud, section within 10 mm of dressed size, angle within 0.05° on a single stud, yellow paint. |
| Change | `eps` 25 mm, `min_points` 20, minimal OBB, and a slab peel that unions horizontal bands within one plate thickness so plate side faces do not bridge bays. Vertical stud faces are not peeled. |
| Result | Bars passed on the seven scenes. This spends one of the five Open3D loops. It is not a jobsite trial. |

Loops 2–5 are open. The IntCDC counts in doc 11 (449 components, 6 / 3 / 90 under a different paint) stay a negative log. IntCDC is not re-run here and is not the acceptance set.

## Curriculum continuation (2026-09-25)

Write-up: [24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md). Scorecards: `artifacts/scorecards/curriculum/`. Script: `scripts/run_curriculum_through_room.py`. ε unlocked. Paint yellow. Class S only.

Stage 0 and the original stage-2 and stage-3 cards were linked and still meet the bars above. New rank-1 gates at 1 mm noise also meet them: three more stage-2 leans (0°, 0.12°, 1°) and stage-3 walls of 3, 4 (milder leans), and 5 studs. A 2 mm noise wall does not: recall 0.25, four clusters, three dropped by the 15 mm section gate. S1b bows of 6.35 mm keep a box and miss the 10 mm section bar. A 19.05 mm bow is dropped by that gate. Details and the cluster extents are in doc 24.

Stage 5 synthetic room, rank 1, this process: 532,301 points, 26 studs, precision 1, recall 1, section 7.93 mm, length 22.12 mm, MAE 0.01134°, max angle 0.04230°, yellow, 1.9151 s, floor normal. Corner air gap 0.10 m. No header. Not the Lot 62 Polycam file (that file is PR #24). No stage-5 acceptance bar is declared from this row. Ranks 2–7 on the room are `not_run`. Stages 6 and 7 are stubs with null metrics.

SAM 2 rank 7: `blocked_install`. Projection of the seed-2 stud produced 8,269 occupied pixels. No mask metric. The generator-mask control lifted 8,269 points and kept no stud box, because the visible length is 1.010 m.

## Non-goals

- Plates, headers, and trusses as classes. Later. Plates are geometry to remove.
- King, jack, and cripple labels. Stage 4 does not need them.
- Training on IntCDC, or treating IntCDC as the acceptance cloud. It is a regression check and a negative control only: heavy timber, members touch, file Z is not a documented gravity vector.
- Bassier remote coplanar merge. It glues studs that share a wall plane.
- Forcing a cylinder axis to global Z. That hides the lean.
- Paid APIs, and the commercial scan-to-BIM tools ranked 6–12 in doc 11, in this bake-off.
- Treating the synthetic stage-5 room as the capture that unlocks Pointcept training.
- Treating SAM 2’s published video scores as a stud-angle result. The rank-7 card has null stud metrics.
- GPU training, a Pointcept fine-tune, or an Open3D-ML fine-tune in this tree. The fine-tune that does exist is the separate class-S note, doc 20, and it is not this curriculum pass.
- Painting green or red before ε is a measured band.
- Quoting S3DIS mIoU, Özkan’s roof-beam completeness, or a published 3% dimension error as if it were stud-angle accuracy.
- Leveling the cloud onto the floor and calling that Z gravity (doc 02).

## Code map

| Path | Role |
| --- | --- |
| `src/openwall_stud/synthetic.py` | Stages 0, 2, and 3, S1b bow, and the stage-5 room. |
| `src/openwall_stud/open3d_baseline.py` | Rank 1 pipeline and the synthetic scorer. |
| `src/openwall_stud/paint.py` | Green / yellow / red. Unlocked ε is yellow. |
| `src/openwall_stud/scorecard.py` | JSON writer. Detection, geometry, angle, paint, cost. `append_day_row` updates the day table. |
| `src/openwall_stud/results_by_day.py` | CSV, JSON, and markdown for the day-by-day results. |
| `docs/research/13-stud-seg-results-by-day.md` | Human-readable day table. Regenerated from the CSV. |
| `src/openwall_stud/contenders/` | Ranks 2–7. Rank 7 is `sam2_mask.py`. |
| `scripts/run_stage0_baseline.py` | Runs the bars and writes scorecards. |
| `scripts/run_curriculum_through_room.py` | Links stage 0, extends stages 2 and 3, runs S1b and the synthetic room, stubs stages 6 and 7, scaffolds SAM 2. |
| `scripts/render_algo_figures.py` | Writes the PNGs in `docs/research/images/algo-contenders/`. |
| `artifacts/scorecards/` | The JSON from the run above, plus four stub cards with null metrics. |

From the repo root, after `pip install -r requirements.txt`:

```bash
python scripts/run_stage0_baseline.py
python scripts/render_algo_figures.py
```

The scripts put `src` on `sys.path`. A minimal Linux image also needs `libegl1` before `import open3d` succeeds. Ranks 2–5 do not need that import to write their stub cards.
