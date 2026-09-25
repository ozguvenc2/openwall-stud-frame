# Methods outline

Aligned with the code and design notes as of the `cursor/stud-seg-design-plan-6289` line this paper branches from. Sections marked **planned** have no measurements. Sections marked **in code** are what `src/openwall_stud/` does on synthetic scenes.

Product names in the prose: BeamWeaver (platform), TruePlank (stud QA), OpenWall (this engineering pipeline).

## Claim classes

| Class | Ground truth | Status |
| --- | --- | --- |
| S — synthetic bring-up | Generator geometry in `openwall_stud.synthetic` | **Run** for Open3D on stages 0, 2, and 3 |
| R — realisticized | A sensor simulator or noise model fitted to a real scanner, applied to generator geometry | **Not defined** in the design documents or the code. Do not describe the 1 mm Gaussian as this class |
| F — experimental | `skil`, `total_station`, or `hand_label`, the ground-truth sources named for later rows in `results_by_day` | **Planned.** No row uses them |

Class S passing a bar is a software bring-up. Class F is the validation arm. Class R does not exist yet; adding it would be a new generator, not a reinterpretation of the current scorecards.

## Scene ladder

From [`docs/research/12-stud-seg-design-plan.md`](../../docs/research/12-stud-seg-design-plan.md).

| Stage | Scene | In this repo | Angle reference |
| --- | --- | --- | --- |
| 0 | One dressed stud, 2×4 or 2×6 | Synthetic generator, **run** | Generator +Z. No floor |
| 1 | One real stud, isolated | **Not run.** One-stud five-finder belongs here when that cloud exists | SKIL mean of BOT / MID / TOP only if the three readings agree; otherwise no MAE, yellow paint |
| 2 | Stud plus floor or slab | Synthetic slab, **run**. Cloud is not rotated onto the slab | Floor normal from the lowest peeled slab |
| 3 | Mini wall, 3–5 studs | Four synthetic 2×4s at 16 inch centers, plates and floor, **run** | Floor normal |
| 4 | One real wall, plus opening clutter | No cloud | Floor normal, SKIL on a sample |
| 5 | One room or bay | No cloud. Later training is allowed to see this cloud only after a classical scorecard is written | Floor normal, SKIL sample |
| 6 | Whole single-story frame | Blocked on a real stage 5 | Same |
| 7 | Two-story or a complex frame | Last | Same |

Plates are peeled. They are not a QA class. King, jack, and cripple labels are not required.

## Generator (class S only)

`openwall_stud.synthetic`, Open3D 0.20, CPU.

| Parameter | Value in the 2026-09-24 run |
| --- | --- |
| Dressed 2×4 | 1.5 × 3.5 in → 38.1 × 88.9 mm |
| Dressed 2×6 | 1.5 × 5.5 in → 38.1 × 139.7 mm |
| Length | 8 ft → 2438.4 mm |
| Stud surface spacing | 5 mm |
| Floor spacing | 10 mm (stage 2) or 12 mm (stage 3) |
| Noise | Isotropic Gaussian, standard deviation 1 mm, after the surface grid |
| Lean | Rotation about +X through the base. The generator long-axis angle from +Z equals the requested lean |
| Stage 3 layout | 4 studs, 16 inch centers, bottom and top plates of plate height equal to the 1.5 in dressed thickness, default leans 0°, 0.30°, 0.80°, 1.50° |
| Seeds | 1 through 7 in `scripts/run_stage0_baseline.py`, one seed per scene |

The 1 mm noise is a bring-up perturbation. It is not a phone-LiDAR model, a Mid-360 model, or a TLS model.

## Rank-1 pipeline (in code)

`openwall_stud.open3d_baseline`.

1. Peel horizontal slabs (floor and plates). Bands within one plate thickness are removed together so a plate’s vertical side faces do not bridge bays. Vertical stud faces stay.
2. DBSCAN on the remainder. Defaults: `eps` 25 mm, `min_points` 20. A 16 inch bay of 2×4s has a clear gap on the order of 368 mm, so this `eps` is far below a bay merge and large enough for a 5 mm surface grid.
3. Minimal oriented bounding box on each cluster. Keep a cluster whose section is near a 2×4 or 2×6 (gate 15 mm, wider than the scorecard bar) and whose long axis is within 20° of the reference, with length between 1.2 m and 3.3 m.
4. θ is the angle between that long axis and the reference. The reference is the floor normal when a slab was peeled, otherwise generator +Z. The cloud is not leveled onto the floor.
5. Paint with `openwall_stud.paint`.

Loop 1 of the Open3D family changed `eps` from 20 mm and `min_points` from 80, which had marked the stud as noise, to the defaults above, and replaced an unstable PCA box with the minimal box. That loop is the synthetic bring-up. Loops 2–5 are unused. The IntCDC classical trial recorded in the ranking note is a prior negative log (heavy timber, members touching). It is not re-run in this tree and it is not the acceptance set.

## Ranks 2–5 (planned, not run)

Same post-step once a stack returns stud points: tight box, θ versus the stored reference, then the shared paint. The ranks differ in the first step only.

| Rank | First step | Repository state |
| --- | --- | --- |
| 2 | PCL region growing, then a cuboid following Özkan / Pöchtrager, without a Bassier-style remote coplanar merge and without forcing the axis to Z | Stub. PCL is not installed |
| 3 | CloudCompare RANSAC Shape Detection (Schnabel primitives). Expect planes, not four studs, on the stage 3 cloud | Stub. Not a CI dependency. GPL-3.0 if linked |
| 4 | Pointcept PTv3 / PointGroup, trained only after stage 5 stud labels exist. BIMStruct3D zero-shot is a control, not the model | Stub. No CUDA train, no weights |
| 5 | Open3D-ML RandLA-Net or KPConv with S3DIS weights, one histogram on the stage 5 cloud | Stub. Do not paint from it. Do not copy S3DIS mIoU |

## Angle, tolerance, and paint (in code)

Let θ be the angle between the stud long axis and the reference. Zero means aligned with that reference.

Working tolerance τ = `atan(0.25 / 120)` degrees ≈ 0.1194° (scorecards store 0.11937° when rounded to five decimals). The 0.25 inch and the 120 inches are the Handbook figure as summarized by WoodWorks: 1/4 inch in 10 feet. τ is derived geometry, not a published angular code clause.

Let ε be the half-width of device-plus-software error on θ. ε is unlocked. The production rule is yellow on every stud.

When ε is locked, the code paints:

| Color | Rule |
| --- | --- |
| Green | θ + ε ≤ τ |
| Red | θ − ε > τ |
| Yellow | The interval overlaps τ |

A placeholder ε of 0.05° can be evaluated beside the production color and stored as `hypothetical_colors`. The scorecard note says it is a round illustration, not a measured device band. Placeholder colors are not the QA call.

“Percent in band” uses τ as the band on |measured − reference|. It is not the paint decision. Paint needs ε as well.

### QA names that are not in the design documents

The four labels **Hypothetical**, **Ideal**, **Realistic**, and **Absolute** do not appear as a QA stack in the design plan, the ranking note, `paint.py`, or `docs/tolerances.md`. This outline does not adopt them.

What does exist, and must not be renamed into those four layers without an explicit decision from Oz:

| Existing object | Where |
| --- | --- |
| Production color, yellow while ε is unlocked | `paint_stud`, scorecard `production_colors` |
| Hypothetical placeholder colors at 0.05° | `hypothetical_placeholder`, scorecard `hypothetical_colors` |
| Green / yellow / red once ε is locked | `paint.py`, unit-style asserts in `assert_paint_rules` |
| Unfilled end-to-end budget: sensor, registration, segmentation, box fit, gravity reference | `docs/tolerances.md` |

If those four product words are meant to map onto the rows above, the mapping is a human edit. It is not inferred here.

## Error budget (blank form)

`docs/tolerances.md` states that the end-to-end budget is unknown. The sensing note adds registration, wood reflectance, occlusion, and box fit on top of any brochure specification. The paper should carry the budget as three columns. Empty cells stay empty.

### Level

| Term | Plan | Filled? |
| --- | --- | --- |
| Reference identity | Floor normal in the product phase; generator +Z only on stage 0; gravity later from a scanner inclinometer, DAC, ARKit gravity, or a static IMU. The cloud is not rotated onto the floor | Rule written. No paired readings |
| SKIL (or other digital level) | BOT / MID / TOP on one face. Record model, printed resolution, three readings, and sign. If the spread exceeds the printed resolution, yellow and no MAE | No level model and no readings in the repo |
| Floor versus gravity | A stud square to a tilted slab is a different call from a stud plumb to gravity | Unquantified |

### LiDAR

| Term | Plan | Filled? |
| --- | --- | --- |
| Phone LiDAR / Polycam | Allowed for stage 1 detection. Point-cloud export is Business and Enterprise. Not the green/red instrument. Repository survey: centimeter-class | No capture in git |
| Livox Mid-360 | Denser cloud on a tripod when needed. Published range precision is coarser than the ~5 mm tip that corresponds to τ on an 8 ft stud | No capture |
| Survey TLS (Focus / RTC360 class) | The class whose published ranging and angular specifications sit inside τ as a single-point equivalent in the sensing note. Still not a lumber measurement | No capture |
| Registration, reflectance, occlusion | Required notes on any TLS session | Empty |

Derived single-point equivalents in the sensing note (`atan` of a range error over 8 ft) are not the standard error of a fitted axis. They are not copied into the scorecard as ε.

### Algorithm

| Term | What class S already shows | What it does not fill |
| --- | --- | --- |
| Peel | Stage 3 length runs short by about 19–22 mm because the slab peel deletes the plate and a thin band of stud end (scorecard max length error 22.19 mm) | Peel error on a scanned plate of uneven thickness |
| Box | Section errors of about 7–8 mm on these scenes. The design note attributes that to 1 mm Gaussian tails on the face extrema, which the minimal OBB matches. A PCA box on the 4° stud was about 50 × 104 mm and was rejected | Bias from one-sided scans, missing faces, or warp |
| Cluster | `eps` 25 mm did not merge the four synthetic bays. The failure mode if `eps` exceeds the bay gap is a merged box, counted as a miss | Occlusion, touching blocking, or sheathing (sheathing is out of scope) |
| Angle fit | On these seven scenes, absolute angle error versus the generator is a few hundredths of a degree or less | Transfer to a scanner, and any covariance that could become ε |

ε is the sum that paint needs. It is not equal to any single row above, and it is not the placeholder 0.05°.

## Scorecard

Writer: `openwall_stud.scorecard`. One JSON object per algorithm per scene. Missing measurements are null.

| Section | Contents |
| --- | --- |
| Detection | Precision, recall, one box per stud. A merged bay is a miss. Synthetic match radius 0.15 m |
| Geometry | Two smaller OBB extents versus dressed section; long extent versus length |
| Angle | MAE and percent of studs with absolute error inside τ |
| Paint | Production colors; placeholder colors stored separately |
| Cost | Runtime, license, hardware, known failure modes |

Synthetic pass bars in `scripts/run_stage0_baseline.py` (bring-up checks, not a field acceptance test):

| Stage | Detection | Section | Length | Angle | Paint |
| --- | --- | --- | --- | --- | --- |
| 0 | Precision = 1 and recall = 1 | ≤ 10 mm | ≤ 25 mm | ≤ 0.05° | All yellow |
| 2 | Same | ≤ 10 mm | ≤ 25 mm | ≤ 0.05° | Yellow |
| 3 | Same, and predicted count equals stud count | ≤ 10 mm | ≤ 30 mm | ≤ 0.10° | Yellow |

Stages 1 and 4–7 have no numeric bar.

## Out of scope for the method

Paid scan-to-BIM APIs, training on IntCDC, king/jack/cripple labels, sheathing and drywall, and any green/red decision before ε is measured.
