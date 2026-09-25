# Methods outline

Aligned with the code and the class-S runs through 2026-09-25 (phase-1 S1 lean sweep, untuned and tuned CloudCompare, synthetic fine-tune). Sections marked **planned** have no measurements. The narrative paper is [`draft/paper.md`](draft/paper.md).

Product names (Oz, 2026-09-25): OpenWall is the suite. BeamWeaver and TruePlank are the apps. This paper is the TruePlank stud-lean draft. The package in this repository is `openwall_stud`.

## Claim classes

| Class | Ground truth | Status |
| --- | --- | --- |
| S — synthetic bring-up | Generator geometry in `openwall_stud.synthetic` | **Run.** Open3D on stages 0, 2, and 3. Six finders on one stud and on the 25-scene S1 matrix. Ranks 4 and 5 as controls, then a synthetic fine-tune. Rank 3 again after the stud-only CloudCompare tune (PR #22) |
| R — realisticized | A sensor simulator on generator geometry | **Not defined.** The 1 mm Gaussian is class S |
| F — experimental | `skil`, `total_station`, or `hand_label` | **Planned.** No row uses them |

## Scene ladder

From [`docs/research/12-stud-seg-design-plan.md`](../../docs/research/12-stud-seg-design-plan.md).

| Stage | Scene | In this repo | Angle reference |
| --- | --- | --- | --- |
| 0 | One dressed stud, 2×4 or 2×6 | Synthetic generator, **run** (seven-scene bring-up and the one-stud card) | Generator +Z. No floor. Z-up |
| S1 | Phase 1: one rigid lean, one dressed 2×4, 25 scenes | **Run** 2026-09-25 on Oz_PC. Not a bow (S1b) | Generator +Z (`gravity_z_no_floor_plane`) |
| 1 | One real stud, isolated | **Not run.** The five-finder protocol belongs here when that cloud exists | SKIL mean of BOT / MID / TOP only if the three readings agree; otherwise no MAE, yellow paint |
| 2 | Stud plus floor or slab | Synthetic slab, **run** for Open3D. Two held-out floor clouds also scored by the fine-tuned ranks 4 and 5 | Floor normal from the lowest peeled slab. Cloud is not rotated |
| 3 | Mini wall, 3–5 studs | Four synthetic 2×4s at 16 inch centers, plates and floor, **run** for Open3D | Floor normal |
| 4–7 | Real wall, room, story, complex frame | No cloud | Floor normal, SKIL on a sample |

Plates are peeled. They are not a QA class. King, jack, and cripple labels are not required.

## Generator (class S only)

`openwall_stud.synthetic`, Open3D 0.20.

| Parameter | Value |
| --- | --- |
| Dressed 2×4 | 1.5 × 3.5 in → 38.1 × 88.9 mm |
| Dressed 2×6 | 1.5 × 5.5 in → 38.1 × 139.7 mm |
| Length | 8 ft → 2438.4 mm |
| Stud surface spacing | 5 mm |
| Noise | Isotropic Gaussian. 1 mm on the 2026-09-24 scenes and on phase-1 S1. The fine-tune train set cycles 0.5, 1, 1.5, and 2 mm |
| Lean | Right-hand rotation. S1 magnitudes: 0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0 degrees. Nonzero leans about +X, −X, +Y, −Y. Lean 0 once |
| S1 seed | 2 on every scene. 25,666 points. No floor |
| S1 scene count | 25 |

The 1 mm noise is a bring-up perturbation. It is not a phone-LiDAR model, a Mid-360 model, or a TLS model. The 0.15° entry in the magnitude list is a requested lean. It is not the paint tolerance.

## Shared post-step (in code)

Once a finder returns stud points:

1. Peel horizontal slabs when the scene has them. Bands within one plate thickness are removed together.
2. One point set per physical stud. A merged bay is a miss.
3. Minimal oriented bounding box. Keep a cluster whose section is near a 2×4 or 2×6 (gate 15 mm) and whose long axis is within 20° of the reference, with length between 1.2 m and 3.3 m.
4. θ is the angle between that long axis and the reference. The reference is the floor normal when a slab was peeled, otherwise generator +Z. The cloud is not leveled onto the floor. The generator vertical is +Z.
5. Paint with `openwall_stud.paint`.

Rank 1’s instance step is DBSCAN, `eps` 25 mm, `min_points` 20. An earlier setting (`eps` 20 mm, `min_points` 80) labeled the synthetic stud as noise. That edit is class S.

## Six finders

| Rank | First step | State on 2026-09-25 |
| --- | --- | --- |
| 1 | Open3D peel, DBSCAN, minimal box | **Run**, class S, including S1 25/25 stage-0 bars |
| 2 | Region growing, then a cuboid, no remote coplanar merge, axis not forced to Z | **Run** on class S. S1 scorecards set `native_pcl_region_growing` false (NumPy port). One Linux stud used PCL 1.14 |
| 3 | CloudCompare RANSAC Shape Detection. Untuned: one OBB per plane or cylinder. Tuned: plane only, then a merge of the four long faces | **Run** on class S. Linux one-stud failed the bars. Oz_PC untuned S1: lean on 25/25, stage-0 bars 0/25 (4–8 boxes). Oz_PC tuned S1 (PR #22): stage-0 bars 25/25, one box. Binary discovery: `CLOUDCOMPARE_EXE`, then the default Windows install path, then PATH. The plugin has no cuboid |
| 4 | BIMStruct3D PTv3 semantic control, then a 2-class head on a frozen backbone | Control **run** on Oz_PC (no stud class). Synthetic fine-tune **run** (head only, about 98.1 s). PointGroup not run |
| 5 | Open3D-ML RandLA-Net, S3DIS weights, then a 2-class layer | Control **run** (no stud class). Synthetic fine-tune **run** (about 237.5 s). KPConv not run |
| 6 | pyRANSAC-3D v0.7.0 sequential cuboid after the peel | **Run**, class S, S1 25/25. SAM 2 is still not run |

## Angle, tolerance, and paint (in code)

Let θ be the angle between the stud long axis and the reference. Zero means aligned with that reference.

Working tolerance τ = `atan(0.25 / 120)` degrees ≈ 0.1194°. The 0.25 inch and the 120 inches are the Handbook figure as summarized by WoodWorks: 1/4 inch in 10 feet. τ is derived geometry, not a published angular code clause.

Alternate, same derivation, not the paint band: WoodWorks’s summary of UFGS 1/4 inch in 8 feet gives `atan(0.25 / 96)` ≈ 0.1492° (about 0.15°). The UFGS PDF was not opened. Scorecards and `paint.py` use τ.

Let ε be the half-width of device-plus-software error on θ. ε is unlocked. The production rule is yellow on every stud.

When ε is locked, the code paints:

| Color | Rule |
| --- | --- |
| Green | θ + ε ≤ τ |
| Red | θ − ε > τ |
| Yellow | The interval overlaps τ |

A placeholder ε of 0.05° can be stored as `hypothetical_colors`. Those colors are not the QA call.

### QA names that are not in the design documents

The four labels **Hypothetical**, **Ideal**, **Realistic**, and **Absolute** do not appear as a QA stack in the design plan, the ranking note, `paint.py`, or `docs/tolerances.md`. This outline does not adopt them.

| Existing object | Where |
| --- | --- |
| Production color, yellow while ε is unlocked | `paint_stud`, scorecard `production_colors` |
| Hypothetical placeholder colors at 0.05° | `hypothetical_placeholder`, scorecard `hypothetical_colors` |
| Green / yellow / red once ε is locked | `paint.py` |
| Unfilled end-to-end budget | `docs/tolerances.md` |

## Error budget (blank form)

Empty cells stay empty. Class-S residuals are not ε.

### Level

| Term | Plan | Filled? |
| --- | --- | --- |
| Reference identity | Floor normal in the product phase; generator +Z on stage 0 and S1; gravity later, converted into the Z-up frame. The cloud is not rotated onto the floor | Rule written. No paired readings |
| SKIL (or other digital level) | BOT / MID / TOP. If the spread exceeds the printed resolution, yellow and no MAE | Painted-corner readings in the draft, Section 5.6. Spread exceeds 0.05°, so no MAE. No stud readings |
| Floor versus gravity | A stud square to a tilted slab is a different call from a stud plumb to gravity | Unquantified |

### LiDAR

| Term | Plan | Filled? |
| --- | --- | --- |
| Phone LiDAR / Polycam | Allowed for detection. Not the green/red instrument | Phase-2 corner processed on Oz_PC and gitignored. Not a stud capture. No PLY in git |
| Livox Mid-360 | Denser cloud when needed. Brochure angular figure < 0.15° is a ray spec, not a fitted axis and not the UFGS alternate | No capture |
| Survey TLS | The class whose published specifications sit near τ in the sensing note | No capture |

### Algorithm

| Term | What class S already shows | What it does not fill |
| --- | --- | --- |
| Peel | Stage 3 length runs short by about 19–22 mm (scorecard max length error 22.19 mm) | Peel error on a scanned plate |
| Box | Section errors of about 7–8 mm on the Open3D, NumPy, and pyRANSAC rows. Fine-tune floor clouds are about 20 mm in the fine-tune note | One-sided scans, missing faces, warp |
| Cluster | `eps` 25 mm did not merge the four synthetic bays. Rank 3 returns 4–8 primitives per stud | Occlusion and touching members |
| Angle fit | On the 25 S1 rows, rank-1 angle MAE is 0.00023–0.00948°. Rank 2 reaches 0.01569°. Rank 3 spans 0.00123–0.08872° and still fails the one-stud bar | Transfer to a scanner. Not ε |

## Scorecard

Writer: `openwall_stud.scorecard`. Synthetic pass bars in `scripts/run_stage0_baseline.py` and the S1 sweep (bring-up checks):

| Check | Bar |
| --- | --- |
| Detection | Precision = 1 and recall = 1 |
| Section | ≤ 10 mm |
| Length | ≤ 25 mm (≤ 30 mm on stage 3) |
| Angle | ≤ 0.05° (≤ 0.10° on stage 3) |
| Paint | All yellow |

`control` and `blocked_install` leave stud cells empty. Stages 1 and 4–7 have no numeric bar.

## Out of scope for the method

Paid scan-to-BIM APIs, training on IntCDC, king/jack/cripple labels, sheathing and drywall, green/red paint before ε is measured, and a CloudCompare pass rate from a tune that has not landed.
