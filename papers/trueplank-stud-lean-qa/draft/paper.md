# Stud instance detection and lean QA from point clouds

**Working title.** Automated stud instance detection and lean QA from LiDAR and other point clouds.

**Products.** BeamWeaver is the platform. TruePlank is the stud QA product. OpenWall is the engineering name of this repository and of the pipeline in `src/openwall_stud/`.

**Status.** PRELIMINARY / DRAFT. Revise later. Venue-agnostic Markdown. Not submitted. Abstract is TBD. The References section is the part intended to be usable now; intro, methodology, and tables are preliminary.

## What remains to write

- [ ] Abstract. Do not draft it from the synthetic table.
- [ ] Legal names, affiliations, and CRediT for the Oz and Gwench placeholders.
- [ ] Keep or drop contribution candidates C1–C5 after a class F capture exists.
- [ ] Confirm DBSCAN pagination against the KDD 1996 PDF (`ester1996dbscan` is marked unverified).
- [ ] Open the NAHB guidelines and UFGS 06 10 00 PDFs. Those two bib entries are placeholders.
- [ ] Re-fetch the RoomPlan and ARKit documentation pages before camera-ready.
- [ ] When PR #14 merges, point the rank-6 and SAM 2 rows at `docs/research/17-methods-that-beat-shortlist.md` in-tree. Until then they are planned contenders only.
- [ ] Class F results, including the one-stud five-finder, after scorecards exist.
- [ ] Draw the pipeline figure. The prose diagram in Section 3 is the stand-in.
- [ ] Re-tabulate Chen et al. (2025) specimen numbers from the PDF before they move out of related work.
- [ ] Venue formatting. No arXiv upload and no publisher submission from this draft.

**Authors.** Oz (placeholder). Gwench (placeholder). Legal names, affiliations, and CRediT roles are unassigned. See the [paper-space README](../README.md).

**Claim classes used below.**

| Class | Meaning |
| --- | --- |
| S | Synthetic bring-up against the generator |
| R | Realisticized ground truth (a sensor model on generator geometry) |
| F | Experimental ground truth (level, total station, or hand labels) |

Class R is not defined in the design documents. Class F has no rows. Every number in Section 5 is class S unless the cell says PLACEHOLDER.

---

## Abstract

**TBD.**

Do not promote the synthetic table into this paragraph. A usable abstract needs at least a one-sentence field protocol and an explicit statement that green/red paint is withheld until a measured device band exists. Candidate claims C1–C5 are listed in the paper-space README. They are not results.

Working scope, not a substitute abstract: TruePlank finds vertical studs on a bare wood frame, fits one tight oriented box each, measures the long-axis angle against a stored reference, and paints green, yellow, or red only after a device-plus-software band ε is known. Until that band exists the production color is yellow. This draft describes that method as implemented for synthetic scenes and leaves field results empty.

---

## 1. Introduction (PRELIMINARY / DRAFT — revise later)

Light-frame wood studs are checked, in the field, with a level and a finish tolerance. WoodWorks states that the International Building Code and the American Wood Council’s National Design Specification do not set a light-frame wood construction-tolerance requirement, and it summarizes a Handbook tightening to 1/4 inch in 10 feet when finishes such as gypsum wallboard and plaster are used [woodworksTolerances, ballast2007handbook]. The OpenWall notes convert that Handbook figure to an angle,

τ = atan((1/4 inch) / (10 feet)) ≈ 0.1194°,

and treat τ as a working band, not as a code clause [docs/tolerances.md]. The same notes record other published linear figures (NAHB 3/8 inch in 32 inches, UFGS 1/4 inch in 8 feet) and do not collapse them into τ.

A point-cloud product can miss the decision those figures are about. Historic-roof pipelines fit cuboids to heavy timber [ozkan2022timber, pochtrager2018roof]. Primitive fitters return planes and cylinders [schnabel2007ransac]. Indoor networks report scores on offices and finished rooms [wu2024ptv3, jiang2020pointgroup]. None of those outputs is a per-stud lean against a stated reference, with an error bar wide enough to refuse a pass/fail call.

TruePlank’s target, on a bare frame with no drywall and no sheathing, is narrower:

1. Instance-segment each vertical stud. Plates are geometry to remove, not a QA class. King, jack, and cripple names are not required.
2. Fit one tight oriented box per stud. A merged bay is a miss.
3. Measure θ, the angle between the box’s long axis and a stored reference. In the current product phase the reference is the floor normal, and the cloud is not rotated onto the floor. Stage 0 has no floor, so the synthetic generator’s +Z is the reference. A later inclinometer or IMU replaces the vector and repaints the same boxes. A floor is not gravity.
4. Paint green only when the whole interval [θ − ε, θ + ε] lies inside τ, red only when the whole interval lies outside τ, and yellow when the interval overlaps τ or when ε is unknown.

ε is unknown. The honest production paint is yellow on every stud.

This paper is the public write-up of that method. The implementation that exists today is a synthetic bring-up of one classical stack (Open3D) on curriculum stages 0, 2, and 3 [zhou2018open3d, open3dSoftware]. Four other stacks are specified and not run. No jobsite cloud is in the repository. Section 5 therefore contains one labeled synthetic excerpt and an explicit placeholder for field results.

### 1.1 Gap

Scan-to-BIM reviews and Scan-vs-BIM systems turn a laser scan into, or against, a building model [tang2010asbuilt, bosche2015scan]. Those systems answer a modeling or progress question. Timber cuboid pipelines answer a historic-roof completeness question [ozkan2022timber, pochtrager2018roof]. A vision pipeline for wood framing can put an image detector in front of a 6D pose on one close-range stud [xie2026wfc, jocher2023ultralytics]. Phone room capture names walls and openings, and an ARKit session can name gravity, without emitting a stud lean [apple2022roomplan, appleArkitGravity].

The gap for TruePlank is the conjunction: one box per vertical stud on a bare light-frame wall, a long-axis angle against a named reference, and a paint rule that stays yellow until a measured device band exists. None of the related lines above publishes that conjunction, and this draft does not claim to have closed it on a jobsite.

### 1.2 Contribution candidates

C1–C5 are candidates for a later abstract. They are not findings, and they are not field accuracy.

| ID | Candidate | What would have to be true before it is a result |
| --- | --- | --- |
| C1 | A light-frame stud can be an instance: one tight box, plates peeled, a merged bay counted as a miss, then a long-axis angle against a stored reference. | A real bare-frame cloud with an independent stud count. Synthetic stage 3 is bring-up only. |
| C2 | Lean QA stays yellow until a measured device-plus-algorithm band ε exists. | A measured ε on the capture path that would actually ship. The 0.05° placeholder is an illustration. |
| C3 | Floor-normal angle and gravity plumb are different references. Replacing the vector repaints the same boxes. | Paired floor-normal and inclinometer or IMU readings on the same studs. |
| C4 | Historic-roof cuboid completeness, Schnabel primitives, indoor mIoU, and a single-stud pose error are the wrong score for 2×4 lean. | The bake-off on one shared cloud, including finders that are still stubs. |
| C5 | An end-to-end budget (level, LiDAR, algorithm) can sit beside the paint, with empty terms left empty. | At least one filled term from a real capture. |

Drop a candidate if the experiment does not support it.

## 2. Related work

### 2.1 Timber member cuboids

Pöchtrager and colleagues reconstruct historic roof beams as cuboids from planar side faces in terrestrial laser scans [pochtrager2017roof, pochtrager2018roof]. Özkan and colleagues extend that workflow with a split of non-linear segments. On one historic roof they report automatic beam completeness, against a manual count, rising from 29% to 63%, and 75% after additional manual splits [ozkan2022timber]. A later paper completes roof models with the same cuboid route [ozkan2024completion]. Chen, Jiang, and Xiong generate geometric finite-element models from timber point clouds [chen2025timberfe]. The OpenWall ranking records, from that paper’s specimen, dimension errors within 3%, plane angles within 1°, and cylinders forced to a global vertical axis. Those specimen digits were not re-tabulated from the PDF for this draft. Forcing an axis to global Z would erase the lean TruePlank measures.

These papers motivate rank 2 of the planned bake-off: region growing, then a cuboid, without a remote coplanar merge and without a forced vertical axis. They do not supply a 2×4 angle error. Roof-beam completeness stays in this section.

### 2.2 Primitives and wall objects

Schnabel, Wahl, and Klein detect planes, spheres, cylinders, cones, and tori in unorganized point clouds [schnabel2007ransac]. CloudCompare’s RANSAC Shape Detection plugin implements that family. A rectangular stud is not one of those primitives, and coplanar stud faces can collapse to one plane. Rank 3 exists so that primitive count can be compared with stud count on the same cloud. The plugin has not been run.

Bassier and Vergauwen reconstruct BIM wall objects from point clouds without supervision [bassier2020walls]. The engineering plan refuses a merge of remote coplanar patches because studs that share a wall plane would become one instance. A Sensors 2023 DOI written next to the name Bassier in the engineering ranking resolves, on Crossref, to a different paper [ntiyakunze2023sensors]. This draft does not use that DOI as a Bassier citation.

### 2.3 Learned instance and semantic models

Point Transformer V3 is a scalable point backbone with reported results on indoor and outdoor benchmarks [wu2024ptv3]. Pointcept is the codebase in which that backbone is trained [pointcept]. PointGroup is an instance-segmentation head from the same research line [jiang2020pointgroup]. The planned rank 4 uses that stack only after stud labels exist on a real room (stage 5). No weights are loaded here. Published ScanNet or S3DIS figures are left on those benchmarks.

Open3D is the library behind the implemented baseline [zhou2018open3d, open3dSoftware]. Clustering after the plate peel is DBSCAN [ester1996dbscan]. The DBSCAN pagination in the bibliography is marked unverified until the KDD PDF is checked. PCL is the planned host for region growing [rusu2011pcl]. It is not installed here, and the rank-2 stub has not been executed.

### 2.4 Planned image and cuboid adds (not run)

A separate research note, `docs/research/17-methods-that-beat-shortlist.md` on draft pull request #14, proposes two bake-off adds and does not run them. This branch does not contain that file. They appear in Table 1 as planned contenders.

Sequential cuboid fitting with pyRANSAC-3D v0.7.0 would run after the same plate peel as rank 1 [mariga2026pyransac]. The library fits one cuboid per call. The fair experiment, as that note describes it, is repeated fits with inlier removal and a 2×4 section test that is ours. Schnabel’s primitive set does not include that cuboid [schnabel2007ransac, fischler1981ransac]. No stud accuracy is published for the library, and this repository has not called it.

SAM 2 is a promptable segmenter for images and video [ravi2024sam2]. The note would lift a mask onto points only when the capture already has a registered camera, then hand the points to the shared box. A pure LAS or PLY would skip it. It is not a stud finder and it has not been run.

### 2.5 Wood-stud pose, as related work only

Xie and Alwisy study vision-driven automation for wood-framed construction and release the WFC pose dataset: one 2×4 under controlled views, with a detector in front of a separate 6D pose [xie2026wfc, jocher2023ultralytics]. That detector is not this paper’s method. The engineering survey of their README, recorded on PR #14, describes a published rotation on the order of a degree and a 2° acceptance bar. Those README digits were not re-tabulated from the journal PDF here, and they are not a wall-lean result at τ. YOLO stays related context. It does not replace an oriented box on a point cloud.

### 2.6 Tolerances and sensors

The tolerance chain used in software is the WoodWorks summary and the derived angle above, not a new code interpretation [woodworksTolerances, ballast2007handbook]. WoodWorks also summarizes an NAHB figure of 3/8 inch in 32 inches and UFGS figures of 1/4 inch in 8 feet and 1/8 inch in 8 feet. The NAHB book and the UFGS section were not opened; their bibliography entries are placeholders [nahbGuidelines, ufgs061000].

Phone LiDAR comparisons are centimeter-class in the repository sensing survey, which points at Erland and Gaulton for a cross-model iPhone study [erland2026iphone]. The centimeters in that survey were not re-extracted from the PDF here. The sensing note’s conclusion, which this paper adopts as a protocol constraint, is that survey terrestrial scanners are the instrument class whose published specifications sit near τ, while phone LiDAR and robotics lidars are detection sensors. Brochure specifications are not ε.

As-built modeling from laser scans is the neighboring literature [tang2010asbuilt, bosche2015scan, bassier2020walls]. It reconstructs or checks building objects, including MEP cylinders in the Bosché case. It does not supply a bare-stud lean. RoomPlan and ARKit gravity are sensing context only [apple2022roomplan, appleArkitGravity]. RoomPlan’s published surface list is walls, openings, and furniture, not studs. An ARKit session can store a Y-up gravity axis for a capture we run ourselves. The engineering notes say that vector does not travel inside a Polycam PLY by any page they found, and phone tilt error is unquantified. A full stack — range, registration, segmentation, box fit, and the gravity or level reference — is unmeasured [docs/tolerances.md, docs/research/01-sensing-modalities.md].

## 3. Methodology (PRELIMINARY / DRAFT — revise later)

The outline with parameters, the blank error budget, and the statement that the names Hypothetical / Ideal / Realistic / Absolute are not a method in the design documents is [`METHODS.md`](../METHODS.md). This section is the preliminary narrative.

### 3.0 Pipeline in prose

One cloud, then five steps. Ranks differ in the instance step only. The box, the angle, and the paint are shared.

1. **Peel.** Remove near-horizontal slabs (floor and plates). Bands within one plate thickness go together so a plate’s vertical side faces do not bridge bays. Vertical stud faces stay. The cloud is not rotated onto the floor.
2. **Instance.** On the remainder, form one point set per physical stud. Rank 1 uses DBSCAN (`eps` 25 mm, `min_points` 20) [ester1996dbscan]. A merged bay is a miss. Planned replacements for this step alone are PCL region growing [rusu2011pcl], Schnabel primitives [schnabel2007ransac], a later Pointcept or PointGroup head [wu2024ptv3, jiang2020pointgroup, pointcept], an Open3D-ML control histogram, and, only as planned adds from PR #14, sequential pyRANSAC-3D cuboids [mariga2026pyransac] and a SAM 2 mask lifted from a registered image [ravi2024sam2].
3. **Box.** Fit one minimal oriented bounding box. Keep clusters whose section is near a dressed 2×4 or 2×6, whose length is between 1.2 m and 3.3 m, and whose long axis is within 20° of the reference.
4. **Angle.** θ is the angle between that long axis and the stored reference. Zero means aligned with the reference. Stage 0 uses generator +Z. Later stages use the floor normal from the lowest peeled slab. A later gravity vector (scanner inclinometer, dual-axis compensator, or an ARKit gravity session converted from Y-up to Z-up) replaces the reference and repaints the same boxes [appleArkitGravity]. A floor is not gravity.
5. **Paint.** Green when θ + ε ≤ τ, red when θ − ε > τ, yellow when the interval overlaps τ or when ε is unknown. ε is unknown, so production paint is yellow.

### 3.1 Inputs and references

The input is a point cloud of a bare wood frame. Synthetic scenes are generated as dressed surface grids: 2×4 at 38.1 × 88.9 mm, 2×6 at 38.1 × 139.7 mm, length 2438.4 mm, stud spacing 5 mm, isotropic Gaussian noise of 1 mm standard deviation. Stage 3 adds a floor (12 mm spacing) and top and bottom plates, with four 2×4s at 16 inch centers. Seeds and requested leans are listed in [`EXPERIMENTS.md`](../EXPERIMENTS.md).

The angle reference is stored, not implied by the file axis. Stage 0 uses generator +Z. Stages 2 and 3 use the normal of the lowest peeled horizontal slab. The points stay in the original frame.

### 3.2 Instance boxes

The implemented stack peels horizontal slabs, including plate side faces that sit within one plate thickness of a horizontal band, then runs DBSCAN with `eps` = 25 mm and `min_points` = 20. Each surviving cluster receives a minimal oriented bounding box. Clusters must look like an upright stud: section near a dressed 2×4 or 2×6, length between 1.2 m and 3.3 m, long axis within 20° of the reference. θ is the angle between that long axis and the reference.

An earlier setting (`eps` 20 mm, `min_points` 80) labeled the synthetic stud as noise, and a PCA box on the 4° stud inflated the section to about 50 × 104 mm. Both were rejected inside the first Open3D debugging loop. That loop is class S. It is not a jobsite trial.

### 3.3 Paint

Production paint calls `paint_stud` with ε unlocked and returns yellow. A side computation stores colors as if ε were 0.05°. The scorecard field is `hypothetical_colors`, and the writer’s note says those colors are not a pass/fail call. Percent of studs inside τ is an angle-error summary. It does not set the color.

### 3.4 Shared scorecard and unrun stacks

Every contender writes one scorecard: detection, geometry, angle, paint, and cost. Unrun stacks write nulls. The planned first steps are PCL region growing plus a timber cuboid, Schnabel primitives through CloudCompare, Pointcept after stage-5 labels, and one Open3D-ML forward pass as a histogram. They share the box, the angle, and the paint. Ranks 2–5 have not spent a debugging loop.

### 3.5 Error budget

Three terms are reserved and unfilled.

- **Level.** Identity of the reference (floor normal, generator +Z, or a later gravity vector). For a standing field stud, three level readings (bottom, middle, top) on one face, the printed resolution, and the sign. Disagreement beyond that resolution yields yellow and no angle MAE.
- **LiDAR.** Sensor class and export. Phone and Mid-360 may support detection. A green/red session waits on a survey scanner, and even then the brochure is not the stud-axis error.
- **Algorithm.** Peel, cluster, and box, each with its own residual. On the synthetic mini-wall the peel shortens studs by about 19–22 mm. Section residuals of about 7–8 mm match Gaussian tails on the face extrema. Those sentences are class S. They are not ε.

### 3.6 Ground-truth classes

Class S compares the box to the generator. Class F will compare it to a level, a total station, or a hand label, using the source names already reserved in the day-table writer. Class R, a realisticized cloud whose noise comes from a scanner model, is not implemented. The 1 mm Gaussian is class S. Synthetic bring-up and later real ground truth stay in separate tables.

### 3.7 Table 1. Algorithm shortlist (PRELIMINARY)

Ranks 1–5 are the engineering bake-off in `docs/research/11-stud-segmentation-algorithm-ranking.md`. Rank 6 and the gated SAM 2 row are the adds proposed in PR #14’s research note (2026-09-25). Nothing in the last two rows has been executed. “Run” means a synthetic Open3D scorecard exists. “Stub” means a null scorecard was written.

| Rank | Stack | Role | State |
| --- | --- | --- | --- |
| 1 | Refined Open3D: horizontal peel, DBSCAN, minimal oriented box [zhou2018open3d, ester1996dbscan] | First experiment | **Run**, class S only |
| 2 | PCL region growing, then a cuboid in the Özkan / Pöchtrager sense, no remote coplanar merge, axis not forced to Z [rusu2011pcl, ozkan2022timber, pochtrager2018roof] | Partial faces and joints | **Stub** |
| 3 | CloudCompare RANSAC shape detection, Schnabel primitives [schnabel2007ransac, fischler1981ransac] | Disagreement check. Expect planes, not four studs | **Stub** |
| 4 | Pointcept PTv3 / PointGroup after stage-5 stud labels [wu2024ptv3, jiang2020pointgroup, pointcept] | Learning path. BIMStruct3D is a control, not the model | **Stub** |
| 5 | Open3D-ML RandLA-Net or KPConv, S3DIS weights | One histogram so an office mIoU is not reused as a stud score | **Stub**. Do not paint from it |
| 6 (planned) | pyRANSAC-3D v0.7.0, sequential cuboid after the rank-1 peel [mariga2026pyransac] | Rectangular primitive rank 3 does not have | **Not run.** Proposed on PR #14 |
| Gated (planned) | SAM 2 mask, lifted onto points, then the shared box [ravi2024sam2] | Instance help only when a registered image already exists | **Not run.** Skip on a pure LAS/PLY |

### 3.8 Table 2. Scorecard fields (definitions)

Writer: `openwall_stud.scorecard`. Missing measurements are null. These definitions are the schema. They are not results.

| Section | Field | Definition used in this repo |
| --- | --- | --- |
| Detection | Precision, recall, TP / FP / FN | One predicted box per physical stud. A merged bay is a miss. Synthetic match radius 0.15 m. Field match radius is not defined yet |
| Geometry | Section error | The two smaller minimal-OBB extents versus dressed size (38.1 × 88.9 mm for a 2×4, 38.1 × 139.7 mm for a 2×6), reported as a maximum in the day log |
| Geometry | Length error | Longest OBB extent versus generator length (2438.4 mm on these scenes), as a maximum in the day log |
| Angle | MAE | Mean absolute error of θ against the stored reference (generator on class S; SKIL only when three readings agree on class F) |
| Angle | Percent in band | Share of matched studs whose absolute angle error is within τ ≈ 0.1194°. This does not set the paint |
| Paint | Production color | Yellow while ε is unlocked. `paint_correct_pct` is then the share of studs painted yellow |
| Paint | Hypothetical colors | Colors if a placeholder ε of 0.05° were locked. Stored beside production colors. Not a QA call |
| Cost | Runtime, license, hardware, failure modes | Runtime is the process that wrote the card. It is not a field budget |
| — | `device_eps_deg` | Empty until a measured band exists |

## 4. Experiments (PRELIMINARY / DRAFT — revise later)

The plan, including what is run and what is owned elsewhere, is [`EXPERIMENTS.md`](../EXPERIMENTS.md).

**Executed (class S).** On 2026-09-24 (America/Los_Angeles) the Open3D baseline was run on seven generator scenes by `scripts/run_stage0_baseline.py`. Stub cards were written for the other four stacks and marked `not_run`. Pass bars inside that script are bring-up checks: perfect detection, section error at most 10 mm, length error at most 25 mm (30 mm on stage 3), angle error at most 0.05° (0.10° on stage 3), and yellow production paint. A miss fails the script. The bars are not a field acceptance test.

**Not executed.** PCL on the same scenes. CloudCompare primitive counts. pyRANSAC-3D. SAM 2. Any real capture. The one-stud five-finder (one physical stud, five finders, a level if the stud is standing, yellow paint) is specified as stage 1 and is owned by another agent. This draft does not report it. Stages 4–7 have no clouds. No realisticized generator is specified.

**Intended field protocol, still empty.** Record sensor, export format, whether Z is gravity, and the floor normal if one was fit. On a standing stud, record the level model and BOT / MID / TOP. Do not publish an angle MAE when the three readings disagree by more than the printed resolution.

## 5. Results

### 5.1 PLACEHOLDER — field and five-finder

No class F numbers exist. The one-stud five-finder has not been copied into this draft. Ranks 2–5 have null metrics. Stages 1 and 4–7 have null metrics. ε is null. Do not fill this subsection from Section 5.2.

### 5.2 Class S excerpt — synthetic Open3D, 2026-09-24

**SYNTHETIC.** Table 3 quotes the day log regenerated from `artifacts/scorecards/results_by_day.csv`, which matches the per-scene JSON files `artifacts/scorecards/open3d_stage*.json`. Ground-truth source on every row is `synthetic`. Detection precision and recall are 1. Section and length columns are the maxima. Angle is the mean absolute error against the generator reference; with one stud that equals the absolute error. Stage 3 also stores a maximum absolute error of 0.00719° in `open3d_stage3_stage3_mini_wall_4.json`. Percent of studs inside τ is 100 on each scene. Production colors are yellow, so the day-log paint column is 100 under the yellow-only rule. That percentage is not agreement with a level. `device_eps_deg` is empty. These numbers are not a field accuracy.

**Table 3. Synthetic Open3D day log, 2026-09-24 (class S only).**

| Scene | Section (mm) | Length (mm) | Angle MAE (°) | Runtime (s) |
| --- | ---: | ---: | ---: | ---: |
| Stage 0, 2×4, lean 0° | 7.86 | 6.24 | 0.03084 | 0.089 |
| Stage 0, 2×4, lean 0.05° | 7.7 | 5.57 | 0.00345 | 0.0795 |
| Stage 0, 2×4, lean 0.12° | 7.39 | 4.85 | 0.01358 | 0.0727 |
| Stage 0, 2×4, lean 4° | 7.86 | 4.99 | 0.02471 | 0.0747 |
| Stage 0, 2×6, lean 0.30° | 7.57 | 6.02 | 0.00582 | 0.0963 |
| Stage 2, 2×4 on a slab, lean 0.20° | 7.84 | 8.16 | 0.01721 | 0.0864 |
| Stage 3, four 2×4s | 7.76 | 22.19 | 0.00426 | 0.3512 |

All seven scenes fall inside the synthetic bars in Section 4. Runtimes are that process on that machine. They are not a field budget.

Stage 0 reference is generator +Z. Stage 2 and stage 3 references are the fitted floor normal. Stage 3 length is short because the plate peel removes a thin band at the stud ends (per-stud length errors in the JSON run from about 19 mm to 22 mm). Stage 3 angle is the generator axis expressed in that floor frame, so a stud requested at 0° is not an error of exactly 0° against the fitted normal.

Placeholder colors at 0.05°, stored and **not** a QA call, are green, green, yellow, red, and red for the five stage-0 scenes in the order of the table. Stage 3 stores green, red, red, red. Production paint on all of these studs is yellow.

Figures for this run are the rank-1 images credited in [`figures/CAPTIONS.md`](../figures/CAPTIONS.md). Scaffold drawings of ranks 2–5 are not results.

## 6. Discussion

The synthetic pass shows that the peel, the density cluster, the minimal box, and the yellow paint are connected on generator geometry with a clear bay and 1 mm noise. Perfect detection on that geometry is the bring-up the bars were written to enforce. It is a weak stress test: the cloud was sampled from the same dressed boxes the fitter expects, and the `eps` threshold was adjusted after a failure on this generator.

Section residuals near 8 mm are large next to a tip offset of about 5 mm at τ over 8 ft, and they are still a statement about Gaussian tails on a complete surface, not about a one-sided phone scan. Length bias on the mini-wall is mostly the peeler. Angle errors of a few hundredths of a degree sit under τ and under the 0.05° synthetic bar. They are errors against the generator, with the reference either +Z or a floor fit on a nearly perfect slab. They are not a prediction of error under beam divergence, dropout, or an unleveled instrument.

Yellow paint is the result that should survive contact with a real cloud. A placeholder ε of 0.05° would have painted several of these synthetic leans red or green. Those colors are in the JSON so the rule can be inspected. They are not evidence that a sensor can support them. Phone and robotics lidars remain, in the sensing survey, outside the instrument class for a τ call. Survey-scanner brochures are closer on paper and still are not a lumber trial.

Related timber numbers (29% to 63% beam completeness, sub-centimeter cuboid fit on historic roofs, a 1° plane band on a small specimen) describe other objects and other questions. Copying them into a TruePlank accuracy line would change the construct. The same applies to indoor mIoU.

The validity threats in [`THREATS_TO_VALIDITY.md`](../THREATS_TO_VALIDITY.md) are part of the discussion: construct (floor versus gravity, τ versus code), internal (generator circularity, one threshold loop, peel shortening), and external (no openings, no sensor model). The citation collision on the Bassier DOI is a documentation threat, not a geometric one, and it is corrected in the bibliography rather than papered over.

What would change the claim is class F: one real stud, five finders, a level protocol with the resolution written down, and ε still unlocked. That experiment is specified and not in this draft.

## 7. Conclusion

OpenWall’s TruePlank path instance-segments vertical studs, fits a minimal oriented box, and reports lean against an explicit reference. The paint rule refuses green and red while the device band is unknown. A synthetic Open3D bring-up on seven generator scenes meets the bring-up bars written for that script, with yellow production colors, and is archived as class S. Field detection, a measured ε, and the other four finders are planned. They are not results of this draft.

---

## Data and code

Repository code: `src/openwall_stud/`, `scripts/run_stage0_baseline.py`, `scripts/render_algo_figures.py`. Scorecards: `artifacts/scorecards/`. Human log: `docs/research/13-stud-seg-results-by-day.md`. Design notes: `docs/research/12-stud-seg-design-plan.md`, `docs/research/11-stud-segmentation-algorithm-ranking.md`, `docs/tolerances.md`. No point-cloud files of real buildings are stored in git.

Re-run instructions are in the paper-space README. A re-run that changes a quoted number needs a new dated row, not a silent edit of Section 5.2.

## Ethics

Jobsite and residential scans can identify people and addresses. None are included. A color on a stud can be misread as a code or safety decision; τ is a derived finish guideline, and ε is unlocked. License constraints for later stacks (CloudCompare GPL-3.0, non-commercial weights on some public checkpoints) are recorded in the paper-space README and are not a license to ship those components inside a closed application.

## References

Markdown list keyed to [`references.bib`](../references.bib). A later Pandoc pass can resolve the same keys. Entries marked **UNVERIFIED PLACEHOLDER** or **UNVERIFIED PAGINATION** or **UNVERIFIED THIS PASS** must be checked before camera-ready. DOI collisions are footnoted under Bassier.

### Timber cuboids and region growing

**ozkan2022timber.** Özkan, T., Pfeifer, N., Styhler-Aydın, G., Hochreiner, G., Herbig, U., and Döring-Williams, M. (2022). Historic timber roof structure reconstruction through automated analysis of point clouds. *Journal of Imaging*, 8(1), 10. https://doi.org/10.3390/jimaging8010010

**pochtrager2018roof.** Pöchtrager, M., Styhler-Aydın, G., Döring-Williams, M., and Pfeifer, N. (2018). Digital reconstruction of historic roof structures: Developing a workflow for a highly automated analysis. *Virtual Archaeology Review*, 9(19), 21–33. https://doi.org/10.4995/var.2018.8855

**pochtrager2017roof.** Pöchtrager, M., Styhler-Aydın, G., Döring-Williams, M., and Pfeifer, N. (2017). Automated reconstruction of historic roof structures from point clouds — development and examples. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, IV-2/W2, 195–202. https://doi.org/10.5194/isprs-annals-IV-2-W2-195-2017

**ozkan2024completion.** Özkan, T., Pfeifer, N., and Hochreiner, G. (2024). Automatic completion of geometric models from point clouds for analyzing historic timber roof structures. *Frontiers in Built Environment*, 10, 1368918. https://doi.org/10.3389/fbuil.2024.1368918

**chen2025timberfe.** Chen, L., Jiang, L., and Xiong, H. (2025). Automated generation of geometric FE models for timber structures using 3D point cloud data. *Buildings*, 15(13), 2213. https://doi.org/10.3390/buildings15132213

**rusu2011pcl.** Rusu, R. B., and Cousins, S. (2011). 3D is here: Point Cloud Library (PCL). *2011 IEEE International Conference on Robotics and Automation*, 1–4. https://doi.org/10.1109/ICRA.2011.5980567

### Primitives, RANSAC, and instance clustering

**schnabel2007ransac.** Schnabel, R., Wahl, R., and Klein, R. (2007). Efficient RANSAC for point-cloud shape detection. *Computer Graphics Forum*, 26(2), 214–226. https://doi.org/10.1111/j.1467-8659.2007.01016.x

**fischler1981ransac.** Fischler, M. A., and Bolles, R. C. (1981). Random sample consensus: A paradigm for model fitting with applications to image analysis and automated cartography. *Communications of the ACM*, 24(6), 381–395. https://doi.org/10.1145/358669.358692

**ester1996dbscan.** Ester, M., Kriegel, H.-P., Sander, J., and Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining (KDD)*, 226–231. AAAI Press. **UNVERIFIED PAGINATION.** No DOI retrieved on this pass.

**mariga2026pyransac.** Mariga, L. (2026). pyRANSAC-3D (version 0.7.0) [software]. Zenodo. https://doi.org/10.5281/zenodo.21988437 — Concept record id 7212567. PR #14 names https://doi.org/10.5281/zenodo.7212567. Not run here.

**bassier2020walls.** Bassier, M., and Vergauwen, M. (2020). Unsupervised reconstruction of Building Information Modeling wall objects from point cloud data. *Automation in Construction*, 120, 103338. https://doi.org/10.1016/j.autcon.2020.103338

**Footnote, DOI collision.** The engineering ranking cites Sensors 2023, DOI 10.3390/s23041924, as Bassier. Crossref resolves that DOI to **ntiyakunze2023sensors**: Ntiyakunze, J., and Inoue, T. (2023). Segmentation of structural elements from 3D point cloud using spatial dependencies for sustainability studies. *Sensors*, 23(4), 1924. https://doi.org/10.3390/s23041924 — This draft does not treat that paper as Bassier’s.

### Learned point clouds, and gated image segmentation

**wu2024ptv3.** Wu, X., Jiang, L., Wang, P.-S., Liu, Z., Liu, X., Qiao, Y., Ouyang, W., He, T., and Zhao, H. (2024). Point Transformer V3: Simpler, faster, stronger. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 4840–4851. https://openaccess.thecvf.com/content/CVPR2024/html/Wu_Point_Transformer_V3_Simpler_Faster_Stronger_CVPR_2024_paper.html — Also arXiv:2312.10035. The open-access bibtex did not print a DOI, so none is invented here.

**pointcept.** Pointcept contributors. Pointcept [software]. https://github.com/Pointcept/Pointcept — Codebase for the planned rank-4 hook. The backbone paper is wu2024ptv3.

**jiang2020pointgroup.** Jiang, L., Zhao, H., Shi, S., Liu, S., Fu, C.-W., and Jia, J. (2020). PointGroup: Dual-set point grouping for 3D instance segmentation. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 4866–4875. https://doi.org/10.1109/CVPR42600.2020.00492

**zhou2018open3d.** Zhou, Q.-Y., Park, J., and Koltun, V. (2018). Open3D: A modern library for 3D data processing. arXiv:1801.09847. https://arxiv.org/abs/1801.09847

**open3dSoftware.** Open3D authors. Open3D (version 0.20.0) [software]. https://github.com/isl-org/Open3D — MIT. Version pinned in this repository.

**ravi2024sam2.** Ravi, N., Gabeur, V., Hu, Y.-T., Hu, R., Ryali, C., Ma, T., Khedr, H., Rädle, R., Rolland, C., Gustafson, L., Mintun, E., Pan, J., Alwala, K. V., Carion, N., Wu, C.-Y., Girshick, R., Dollár, P., and Feichtenhofer, C. (2024). SAM 2: Segment anything in images and videos. arXiv:2408.00714. https://arxiv.org/abs/2408.00714 — Planned gated mask only. Not run.

### Wood-stud pose and the image detector in front of it

**xie2026wfc.** Xie, C., and Alwisy, A. (2026). Advancing robotic automation in wood-framed construction using vision-driven adaptive control. *Automation in Construction*, 185, 106858. https://doi.org/10.1016/j.autcon.2026.106858 — Related only. Not this method.

**jocher2023ultralytics.** Jocher, G., Qiu, J., and Chaurasia, A. (2023). Ultralytics YOLO (version 8.0.0) [software]. https://github.com/ultralytics/ultralytics — Authors and version from CITATION.cff on 2026-09-25. AGPL-3.0 in that file. Related only as the detector in front of pose in xie2026wfc. Not a point-cloud stud finder.

### As-built LiDAR and scan-to-BIM

**tang2010asbuilt.** Tang, P., Huber, D., Akinci, B., Lipman, R., and Lytle, A. (2010). Automatic reconstruction of as-built building information models from laser-scanned point clouds: A review of related techniques. *Automation in Construction*, 19(7), 829–843. https://doi.org/10.1016/j.autcon.2010.06.007

**bosche2015scan.** Bosché, F., Ahmed, M., Turkan, Y., Haas, C. T., and Haas, R. (2015). The value of integrating Scan-to-BIM and Scan-vs-BIM techniques for construction monitoring using laser scanning and BIM: The case of cylindrical MEP components. *Automation in Construction*, 49, 201–213. https://doi.org/10.1016/j.autcon.2014.05.014

### Construction tolerances

**woodworksTolerances.** WoodWorks. Construction tolerances for light wood-frame projects. Wood Products Council expert tip. https://www.woodworks.org/resources/construction-tolerances-for-light-wood-frame-projects/ — Page text checked 2026-09-25. Access year is the check year. The page states that the IBC and the AWC NDS do not set a light-frame wood construction-tolerance requirement, and it summarizes Ballast, NAHB, and UFGS.

**ballast2007handbook.** Ballast, D. K. (2007). *Handbook of Construction Tolerances* (2nd ed.). John Wiley & Sons. ISBN 978-0-471-93151-5. Publisher page checked 2026-09-25. The 1/4 inch in 10 feet figure used here is WoodWorks’s summary of this handbook, not a re-reading of the handbook page. τ ≈ 0.1194° is derived from that summary.

**nahbGuidelines.** National Association of Home Builders. Residential Construction Performance Guidelines. **UNVERIFIED PLACEHOLDER.** Edition and year were not opened. The 3/8 inch in 32 inches figure is WoodWorks’s summary only.

**ufgs061000.** Unified Facilities Guide Specifications. UFGS 06 10 00, Rough Carpentry. **UNVERIFIED PLACEHOLDER.** The specification PDF was not opened. WoodWorks’s summary is the only text used: 1/4 inch in 8 feet, and 1/8 inch in 8 feet for tighter finishes. Confirm the section title and the “United” versus “Unified” wording against the PDF.

### Sensing context

**erland2026iphone.** Erland, B. M., and Gaulton, R. (2026). A comparison of lidar accuracy across iPhone models, with implications for reproducibility and cross-study comparison. *Remote Sensing Letters*, 17, 1620–1631. https://doi.org/10.1080/2150704X.2026.2720055 — Bibliographic record verified. RMSE centimeters in the repository sensing survey were not re-extracted from the PDF.

**apple2022roomplan.** Apple. (2022). RoomPlan. Apple Machine Learning Research; WWDC22 session 10127. https://machinelearning.apple.com/research/roomplan — **UNVERIFIED THIS PASS** as a live fetch. Sensing context only. Not a stud schedule.

**appleArkitGravity.** Apple. ARKit `ARConfiguration.WorldAlignment`. Apple Developer Documentation. https://developer.apple.com/documentation/arkit/arconfiguration/worldalignment-swift.enum — **UNVERIFIED THIS PASS** as a live fetch. Sensing context for a capture that runs ARKit. Y-up. Not ε.

