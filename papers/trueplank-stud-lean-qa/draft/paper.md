<!--
Pandoc / Quarto metadata lives in header.yaml (same title, authors, keywords,
bibliography). A later PDF does not need a journal class:

  pandoc draft/paper.md --metadata-file=draft/header.yaml \
    --citeproc --bibliography=references.bib -s -o draft/paper.pdf

See ../Makefile. This file is the draft of record.
-->

# Instance detection and lean assessment of light-frame wood studs from point clouds

**Draft.** 2026-09-25. Venue-agnostic Markdown in the shape of an Automation in Construction / ISPRS / Journal of Computing in Civil Engineering article. Not submitted. Not an arXiv upload.

**Authors.** Oz (placeholder). Gwench (placeholder). Legal names, affiliations, and CRediT roles are unassigned. Prior agents that edited the engineering notes are not authors.

**Products.** BeamWeaver is the platform. TruePlank is the stud QA module. OpenWall is the engineering name of this repository and of the pipeline in `src/openwall_stud/`.

**Claim classes.**

| Class | Meaning | In this draft |
| --- | --- | --- |
| S | Synthetic bring-up against the generator | Every number in Section 5 |
| R | A sensor model applied to generator geometry | Not defined in the design documents |
| F | A level, a total station, or a hand label | No rows |

ε, the device-plus-software half-width on the lean angle, is unlocked. Production paint is yellow.

## Abstract

Light-frame wood studs are checked in the field with a level and a finish guideline. WoodWorks states that the International Building Code and the American Wood Council’s National Design Specification do not set a light-frame wood construction tolerance, and it summarizes a Handbook tightening to 1/4 inch in 10 feet when finishes such as gypsum wallboard are used. That figure converts to a working angle τ ≈ 0.1194°. Scan-to-BIM systems and historic-timber cuboid pipelines answer a modeling or roof-completeness question. They do not publish one oriented box per bare 2×4, a long-axis angle against a named reference, and a paint rule that stays yellow until a measured instrument band exists.

This paper describes that conjunction as implemented in TruePlank. The cloud stays in its capture frame (Z-up in the generator). Each finder returns stud points. A shared step fits one minimal oriented bounding box, measures θ between the long axis and a stored reference, and paints yellow while ε is unknown. Six finders share that post-step. On a class-S protocol of 25 synthetic dressed 2×4 clouds (no floor; leans of 0°, 0.05°, 0.12°, 0.15°, 0.30°, 1°, and 4° about ±X and ±Y), Open3D, a NumPy region-grow cuboid, and sequential pyRANSAC-3D cuboids met the synthetic stage-0 bars on 25 of 25 scenes. CloudCompare RANSAC shape detection returned a lean on 25 of 25 scenes and failed the one-stud bar on all 25, because each stud became several face primitives. Office-vocabulary controls (a BIMStruct3D Point Transformer V3 and an S3DIS RandLA-Net) contain no stud class. A later synthetic fine-tune, head-only for the transformer (about 98 s) and a new 2-class layer for RandLA-Net (about 237 s), placed a stud box on 25 of 25 phase-1 clouds. Those clouds have no floor, and both models labeled every point as stud. No jobsite cloud, no level reading, and no measured ε are reported. A stud-only CloudCompare parameter tune is in progress and is not given a pass rate here.

## Keywords

point cloud; Scan-to-BIM; light-frame wood; stud instance detection; plumbness; oriented bounding box; LiDAR; construction tolerance

## 1. Introduction

A point-cloud product can miss the decision a framer makes with a level. Historic-roof pipelines fit cuboids to heavy timber [ozkan2022timber, pochtrager2018roof]. Primitive fitters return planes and cylinders [schnabel2007ransac]. Indoor networks report scores on offices and finished rooms [wu2024ptv3, jiang2020pointgroup]. A vision pipeline can put an image detector in front of a 6D pose on one close-range stud [xie2026wfc]. None of those outputs is a per-stud lean against a stated reference, with an error bar wide enough to refuse a pass/fail call.

TruePlank’s target, on a bare frame with no drywall and no sheathing, is narrower:

1. Instance-segment each vertical stud. Plates are geometry to remove, not a QA class. King, jack, and cripple names are not required.
2. Fit one tight oriented box per stud. A merged bay is a miss.
3. Measure θ, the angle between the box’s long axis and a stored reference. In the current product phase the reference is the floor normal, and the cloud is not rotated onto the floor. Stage 0 and the phase-1 S1 matrix have no floor, so the synthetic generator’s +Z is the reference. A later inclinometer or IMU replaces the vector and repaints the same boxes. A floor is not gravity. The generator axis is Z-up. An ARKit gravity session is Y-up and, if used later, is converted into this Z-up frame before it replaces the reference [appleArkitGravity].
4. Paint green only when the whole interval [θ − ε, θ + ε] lies inside τ, red only when the whole interval lies outside τ, and yellow when the interval overlaps τ or when ε is unknown.

ε is unknown. The honest production paint is yellow on every stud.

The implementation that exists today is a synthetic bring-up. It covers one classical Open3D stack on curriculum stages 0, 2, and 3 [zhou2018open3d, open3dSoftware], a six-finder pass on one synthetic stud, a 25-scene lean sweep (phase 1, S1), office-vocabulary controls on a GPU workstation, and a synthetic fine-tune of those two networks. No jobsite cloud is in the repository. Section 5 is entirely class S.

### 1.1 Gap

Scan-to-BIM reviews and Scan-vs-BIM systems turn a laser scan into, or against, a building model [tang2010asbuilt, bosche2015scan]. Those systems answer a modeling or progress question. Timber cuboid pipelines answer a historic-roof completeness question [ozkan2022timber, pochtrager2018roof]. Phone room capture names walls and openings, and an ARKit session can name gravity, without emitting a stud lean [apple2022roomplan, appleArkitGravity].

A house-alike hunt (draft PR #12, `docs/research/15-house-alike-frame-clouds.md` on branch `cursor/house-alike-cloud-hunt-0474`) did not find a public cloud that looks like a US platform-frame house at sheathing stage and that could bake off a phone or robotics lidar. The conclusion recorded there is to wait for an own residential scan. That is why this draft has a class-S arm and an empty class-F arm.

The gap for TruePlank is the conjunction: one box per vertical stud on a bare light-frame wall, a long-axis angle against a named reference, and a paint rule that stays yellow until a measured device band exists. This draft does not claim to have closed that gap on a jobsite.

### 1.2 Contributions and their status

C1–C5 were candidates. The status column is what the repository supports on 2026-09-25. None of them is a field accuracy.

| ID | Candidate | Status in this draft |
| --- | --- | --- |
| C1 | A light-frame stud can be an instance: one tight box, plates peeled, a merged bay counted as a miss, then a long-axis angle against a stored reference. | **Illustrated on class S.** The seven-scene Open3D bring-up (including a four-stud mini-wall) and the 25-scene S1 sweep produce one box and a θ against generator +Z or a fitted floor normal. No independent count on a real bare frame. |
| C2 | Lean QA stays yellow until a measured device-plus-algorithm band ε exists. | **Implemented, not measured.** Every production color in the scorecards is yellow. The 0.05° placeholder remains an illustration. |
| C3 | Floor-normal angle and gravity plumb are different references. Replacing the vector repaints the same boxes. | **Specified, not paired.** Stage 0 and S1 use generator +Z. Stages 2 and 3 use a floor normal. No inclinometer or IMU pair exists. |
| C4 | Historic-roof cuboid completeness, Schnabel primitives, indoor mIoU, and a single-stud pose error are the wrong score for 2×4 lean. | **Exercised on class S as a disagreement check.** Schnabel primitives fail the one-stud bar by returning several faces. Office histograms have no stud class. A synthetic fine-tune can emit a box and still is not a field lean. The shared-cloud field bake-off is still open. |
| C5 | An end-to-end budget (level, LiDAR, algorithm) can sit beside the paint, with empty terms left empty. | **Form still mostly empty.** Algorithm residuals on the generator are recorded in Section 5. Level and LiDAR terms are unfilled. They are not ε. |

Drop a candidate if a later experiment does not support it.

## 2. Related work

Citation keys live in [`references.bib`](../references.bib). Entries marked unverified in that file stay unverified. A methods shortlist that was not re-executed for this draft is `docs/research/17-methods-that-beat-shortlist.md` on branch `cursor/methods-beat-shortlist-e9dc` (draft PR #14). Numbers below that come only from that note are labeled as such. This revision did not add bibliography keys for papers that note surveyed and this pass did not re-open.

### 2.1 Timber member cuboids

Pöchtrager and colleagues reconstruct historic roof beams as cuboids from planar side faces in terrestrial laser scans [pochtrager2017roof, pochtrager2018roof]. Özkan and colleagues extend that workflow with a split of non-linear segments. On one historic roof they report automatic beam completeness, against a manual count, rising from 29% to 63%, and 75% after additional manual splits [ozkan2022timber]. A later paper completes roof models with the same cuboid route [ozkan2024completion]. Chen, Jiang, and Xiong generate geometric finite-element models from timber point clouds [chen2025timberfe]. The OpenWall ranking records, from that paper’s specimen, dimension errors within 3%, plane angles within 1°, and cylinders forced to a global vertical axis. Those specimen digits were not re-tabulated from the PDF for this draft. Forcing an axis to global Z would erase the lean TruePlank measures.

These papers motivate rank 2: region growing, then a cuboid, without a remote coplanar merge and without a forced vertical axis. They do not supply a 2×4 angle error. On the phase-1 matrix the rank-2 row is a NumPy smoothness port, because the PCL binary did not run (`native_pcl_region_growing` is false on those scorecards) [rusu2011pcl].

### 2.2 Primitives and wall objects

Schnabel, Wahl, and Klein detect planes, spheres, cylinders, cones, and tori in unorganized point clouds [schnabel2007ransac]. CloudCompare’s RANSAC Shape Detection plugin implements that family. A rectangular stud is not one of those primitives, and coplanar stud faces can collapse to one plane. Rank 3 exists so that primitive count can be compared with stud count on the same cloud. Section 5 records that comparison on the 25-scene matrix. A stud-only parameter tune of that plugin is in progress. This draft does not report a tuned pass rate.

Bassier and Vergauwen reconstruct BIM wall objects from point clouds without supervision [bassier2020walls]. The engineering plan refuses a merge of remote coplanar patches because studs that share a wall plane would become one instance. A Sensors 2023 DOI written next to the name Bassier in the engineering ranking resolves, on Crossref, to a different paper [ntiyakunze2023sensors]. This draft does not use that DOI as a Bassier citation.

### 2.3 Learned instance and semantic models

Point Transformer V3 is a scalable point backbone with reported results on indoor and outdoor benchmarks [wu2024ptv3]. Pointcept is the codebase in which that backbone is trained [pointcept]. PointGroup is an instance-segmentation head from the same research line [jiang2020pointgroup]. Rank 4 in this repository is a BIMStruct3D semantic checkpoint used first as a control (no stud class) and then, in a separate experiment, as a frozen backbone with a new 2-class head. PointGroup itself was not run. Published ScanNet or S3DIS figures are left on those benchmarks.

Open3D-ML RandLA-Net with S3DIS weights is rank 5, first as a label histogram and then as a 2-class fine-tune. KPConv was not run. Open3D is the library behind the rank-1 baseline [zhou2018open3d, open3dSoftware]. Clustering after the plate peel is DBSCAN [ester1996dbscan]. The DBSCAN pagination in the bibliography is marked unverified until the KDD PDF is checked.

### 2.4 Cuboid RANSAC and a gated image mask

The methods shortlist (PR #14) proposed two bake-off adds and ran neither. Sequential cuboid fitting with pyRANSAC-3D v0.7.0 is now rank 6 and has been run on class S [mariga2026pyransac, fischler1981ransac]. Schnabel’s primitive set does not include that cuboid [schnabel2007ransac]. The library fits one cuboid per call. The fair experiment peels plates first, then repeats the fit with inlier removal and a 2×4 section test that is ours. No stud accuracy is published for the library. The numbers in Section 5 are this repository’s generator runs.

SAM 2 is a promptable segmenter for images and video [ravi2024sam2]. The shortlist would lift a mask onto points only when the capture already has a registered camera, then hand the points to the shared box. A pure LAS or PLY would skip it. It has not been run.

The same shortlist declines YOLO as the stud finder [jocher2023ultralytics]. Where an image detector sits in front of a 6D pose, Xie and Alwisy’s WFC README, as recorded in that note and not re-tabulated from the journal PDF here, gives their pose method a mean rotation of 1.43° and a median of 1.00°, with 73.61% of samples inside 20 mm and 2° [xie2026wfc]. That bar is about sixteen times τ. It is related context, not a wall-lean result.

### 2.5 Tolerances and sensors

The tolerance chain used in software is the WoodWorks summary and the derived Handbook angle, not a new code interpretation [woodworksTolerances, ballast2007handbook]. WoodWorks also summarizes an NAHB figure of 3/8 inch in 32 inches and UFGS figures of 1/4 inch in 8 feet and 1/8 inch in 8 feet. The NAHB book and the UFGS section were not opened; their bibliography entries are placeholders [nahbGuidelines, ufgs061000].

The same `atan` that produces τ ≈ 0.1194° from 1/4 inch in 10 feet produces ≈ 0.1492° from the summarized UFGS figure of 1/4 inch in 8 feet. This draft calls that second angle an alternate, about 0.15°. It is not the band stored in the scorecards, and the code does not paint against it. The phase-1 matrix includes a requested lean of 0.15° as a scene magnitude near that alternate. A requested lean is not a second τ.

Phone LiDAR comparisons are centimeter-class in the repository sensing survey, which points at Erland and Gaulton for a cross-model iPhone study [erland2026iphone]. The centimeters in that survey were not re-extracted from the PDF here. The sensing note’s conclusion, which this paper adopts as a protocol constraint, is that survey terrestrial scanners are the instrument class whose published specifications sit near τ, while phone LiDAR and robotics lidars are detection sensors. Brochure specifications are not ε. The Livox Mid-360 angular brochure figure of < 0.15°, recorded in that sensing note, is a ray specification. It is not a fitted stud-axis error, and it is not the UFGS alternate above.

## 3. Method

Parameters, the blank error budget, and the statement that the names Hypothetical / Ideal / Realistic / Absolute are not a method in the design documents are in [`METHODS.md`](../METHODS.md).

### 3.1 Pipeline

One cloud, then five steps. The six finders differ in the instance step. The box, the angle, and the paint are shared. The frame is Z-up. The cloud is not rotated onto the floor.

1. **Peel.** Remove near-horizontal slabs (floor and plates). Bands within one plate thickness go together so a plate’s vertical side faces do not bridge bays. Vertical stud faces stay.
2. **Instance.** On the remainder, form one point set per physical stud. The six finders are listed in Table 1. A merged bay is a miss.
3. **Box.** Fit one minimal oriented bounding box. Keep clusters whose section is near a dressed 2×4 or 2×6, whose length is between 1.2 m and 3.3 m, and whose long axis is within 20° of the reference.
4. **Angle.** θ is the angle between that long axis and the stored reference. Zero means aligned with the reference. Stage 0 and phase-1 S1 use generator +Z (`gravity_z_no_floor_plane`). Stages 2 and 3 use the floor normal from the lowest peeled slab. A later gravity vector replaces the reference and repaints the same boxes.
5. **Paint.** Green when θ + ε ≤ τ, red when θ − ε > τ, yellow when the interval overlaps τ or when ε is unknown. ε is unknown, so production paint is yellow.

### 3.2 Tolerance

Working tolerance τ = atan(0.25 / 120) degrees ≈ 0.1194° (scorecards store 0.11937° when rounded to five decimals). The 0.25 inch and the 120 inches are the Handbook figure as summarized by WoodWorks: 1/4 inch in 10 feet. τ is derived geometry, not a published angular code clause [woodworksTolerances, ballast2007handbook].

The alternate ≈ 0.1492° is the same derivation applied to WoodWorks’s summary of UFGS 1/4 inch in 8 feet. The specification PDF was not opened [ufgs061000]. Paint uses τ, not the alternate.

### 3.3 Scorecard

Every contender writes one scorecard: detection, geometry, angle, paint, and cost. Missing measurements are null. Definitions are in Table 2. They are the schema, not a result. Synthetic match radius is 0.15 m. A field match radius is not defined yet.

Stage-0 bars used as bring-up checks, not as a field acceptance test: precision = 1 and recall = 1, section error ≤ 10 mm, length error ≤ 25 mm, absolute angle error ≤ 0.05°, production paint yellow. `control` means the forward pass ran and those bars were not scored. `blocked_install` means the cloud was built and the stack did not segment it.

### 3.4 Table 1. Six finders

| Rank | Stack | Role on 2026-09-25 | Where it was run |
| --- | --- | --- | --- |
| 1 | Refined Open3D: horizontal peel, DBSCAN (`eps` 25 mm, `min_points` 20), minimal oriented box [zhou2018open3d, ester1996dbscan] | Classical stud prior | Class S: stages 0, 2, 3, one-stud, and phase-1 S1 (25/25 stage-0 bars) |
| 2 | Region growing, then a cuboid in the Özkan / Pöchtrager sense, no remote coplanar merge, axis not forced to Z [rusu2011pcl, ozkan2022timber] | Classical. On S1 the scorecard is a NumPy port (`native_pcl_region_growing` false). One Linux stud used PCL 1.14 | Class S: one-stud and S1 (25/25). Not a libpcl measurement on the 25-scene matrix |
| 3 | CloudCompare RANSAC shape detection, Schnabel primitives, one box per primitive, primitives not merged [schnabel2007ransac] | Disagreement check. Several faces per stud | Class S: Linux one-stud (fail); Oz_PC S1 after `CLOUDCOMPARE_EXE` discovery (lean on 25/25, stage-0 bars 0/25). Stud-only parameter tune in progress |
| 4 | Pointcept / BIMStruct3D PTv3 [wu2024ptv3, pointcept] | Control histogram, then a synthetic 2-class head on a frozen backbone. PointGroup not run | Class S control on Oz_PC (no stud class). Class S fine-tune in Section 5.3 |
| 5 | Open3D-ML RandLA-Net, S3DIS weights, then a 2-class layer [zhou2018open3d] | Control histogram, then a synthetic fine-tune. KPConv not run | Same split as rank 4 |
| 6 | pyRANSAC-3D v0.7.0 sequential cuboid after the rank-1 peel [mariga2026pyransac] | Rectangular primitive rank 3 does not have | Class S: one-stud and S1 (25/25). SAM 2 remains unrun [ravi2024sam2] |

### 3.5 Table 2. Scorecard fields

| Section | Field | Definition used in this repo |
| --- | --- | --- |
| Detection | Precision, recall, TP / FP / FN | One predicted box per physical stud. A merged bay is a miss |
| Geometry | Section error | The two smaller minimal-OBB extents versus dressed size (38.1 × 88.9 mm for a 2×4), as a maximum |
| Geometry | Length error | Longest OBB extent versus generator length (2438.4 mm on these scenes) |
| Angle | MAE | Mean absolute error of θ against the stored reference |
| Angle | Percent in band | Share of matched studs whose absolute angle error is within τ. This does not set the paint |
| Paint | Production color | Yellow while ε is unlocked |
| Paint | Hypothetical colors | Colors if a placeholder ε of 0.05° were locked. Not a QA call |
| — | `device_eps_deg` | Empty until a measured band exists |

### 3.6 Error budget

Three terms are reserved. Level and LiDAR are unfilled. Algorithm cells below are class S and are not ε.

- **Level.** Identity of the reference (floor normal, generator +Z, or a later gravity vector). For a standing field stud, three level readings (bottom, middle, top) on one face, the printed resolution, and the sign. Disagreement beyond that resolution yields yellow and no angle MAE. No readings are in the repository.
- **LiDAR.** Sensor class and export. Phone and Mid-360 may support detection. A green/red session waits on a survey scanner, and even then the brochure is not the stud-axis error.
- **Algorithm.** Peel, cluster, and box. On the synthetic mini-wall the peel shortens studs by about 19–22 mm. Section residuals of about 7–8 mm on the generator match the note’s account of Gaussian tails on the face extrema.

## 4. Experiments

The ledger of what ran is [`EXPERIMENTS.md`](../EXPERIMENTS.md). All executed rows are class S. Class F is empty.

**Generator.** Dressed 2×4 at 38.1 × 88.9 mm, length 2438.4 mm, surface spacing 5 mm, isotropic Gaussian noise. Phase-1 S1 uses 1 mm standard deviation and seed 2 on every scene, 25,666 points, no floor. The long axis is +Z before a right-hand lean. Lean 0 runs once. Nonzero leans use +X, −X, +Y, and −Y. Magnitudes are 0°, 0.05°, 0.12°, 0.15°, 0.30°, 1.0°, and 4.0° (25 clouds). The 1 mm noise is a bring-up perturbation. It is not a phone, Mid-360, or TLS model.

**E0 (2026-09-24).** Open3D on seven generator scenes: five stage-0 studs, one stage-2 stud-and-slab, one stage-3 four-stud wall. Pass bars inside that script are the bring-up checks in Section 3.3, with length ≤ 30 mm and angle ≤ 0.10° on stage 3.

**E-one (2026-09-25, Linux).** One stage-0 2×4, lean 0.05° about +X, seed 2, through ranks 1–6. Ranks 4 and 5 were `blocked_install` on that VM (no GPU, no weights). Write-up: `docs/research/16-one-stud-five-finder-run.md`.

**E-gpu (2026-09-25, Oz_PC).** Ranks 4 and 5 only, same stud, as controls. NVIDIA GeForce RTX 4080 SUPER, 16,376 MiB. Write-up: `docs/research/18-ozpc-ranks4-5-run.md`.

**E-S1 (2026-09-25, Oz_PC).** The 25-scene matrix through all six finders. Ranks 1, 2, and 6 were measured against the stage-0 bars. Rank 3 was `blocked_install` on the first sweep because CloudCompare was not on PATH (PR #18). PR #19 discovered the binary via `CLOUDCOMPARE_EXE`, then `C:\Program Files\CloudCompare\CloudCompare.exe`, then PATH, smoked CloudCompare 2.14.beta (29 Aug 2026), and re-ran rank 3 only. Ranks 4 and 5 were controls. Write-up: `docs/research/19-phase1-s1-lean-sweep.md`. The per-scene table in that note is the source for Section 5.2. This paper does not reprint all 150 rows.

**E-ft (2026-09-25, Oz_PC).** Synthetic fine-tune of ranks 4 and 5 so the label set contains `stud` (and `clutter` for floor points). Train: 386 clouds (304 stud-only, 82 stud plus floor). Val: 33 clouds, including the phase-1 magnitude ladder at seed 9001 and 1.5 mm noise, plus eight stud-plus-floor clouds. The 25 phase-1 cards are in neither split. Write-up: `docs/research/20-synthetic-stud-finetune.md`.

**Not executed.** SAM 2. Any real capture. Native PCL on the 25-scene matrix. A tuned CloudCompare stud-only parameter set (in progress; no pass rate in this draft). Stages 4–7. Class R.

**Intended field protocol, still empty.** Record sensor, export format, whether Z is gravity, and the floor normal if one was fit. On a standing stud, record the level model and bottom / middle / top. Do not publish an angle MAE when the three readings disagree by more than the printed resolution.

## 5. Results

Every table in this section is class S. `device_eps_deg` is empty. Production paint is yellow wherever a box exists. Percent-in-band and hypothetical colors at 0.05° are not a QA call.

### 5.1 Seven-scene Open3D bring-up (2026-09-24)

Table 3 quotes the day log from `artifacts/scorecards/results_by_day.csv`, matching `artifacts/scorecards/open3d_stage*.json`. Detection precision and recall are 1. Section and length columns are maxima. Angle is the mean absolute error against the generator reference.

**Table 3. Synthetic Open3D day log, 2026-09-24 (class S).**

| Scene | Section (mm) | Length (mm) | Angle MAE (°) | Runtime (s) |
| --- | ---: | ---: | ---: | ---: |
| Stage 0, 2×4, lean 0° | 7.86 | 6.24 | 0.03084 | 0.089 |
| Stage 0, 2×4, lean 0.05° | 7.7 | 5.57 | 0.00345 | 0.0795 |
| Stage 0, 2×4, lean 0.12° | 7.39 | 4.85 | 0.01358 | 0.0727 |
| Stage 0, 2×4, lean 4° | 7.86 | 4.99 | 0.02471 | 0.0747 |
| Stage 0, 2×6, lean 0.30° | 7.57 | 6.02 | 0.00582 | 0.0963 |
| Stage 2, 2×4 on a slab, lean 0.20° | 7.84 | 8.16 | 0.01721 | 0.0864 |
| Stage 3, four 2×4s | 7.76 | 22.19 | 0.00426 | 0.3512 |

Stage 3 length is short because the plate peel removes a thin band at the stud ends (per-stud length errors in the JSON run from about 19 mm to 22 mm). Stage 3 angle is the generator axis expressed in the fitted floor frame. Runtimes are that process on that machine.

### 5.2 Phase 1 S1, 25 scenes × six finders (2026-09-25)

**Table 4. Stage-0 bar counts on the 25-scene matrix (class S).** Source: the counts table in `docs/research/19-phase1-s1-lean-sweep.md` after the PR #19 rank-3 refresh. Ranges in the last column are the minimum and maximum of the 25 published scorecard rows in that note, not a new measurement.

| Rank | Role | Pass | Fail | Control | What the 25 rows show |
| --- | --- | ---: | ---: | ---: | --- |
| 1 Open3D | classical | 25 | 0 | 0 | P = R = 1. Section 7.63–7.74 mm. Length 5.48–5.62 mm. Angle MAE 0.00023–0.00948°. Runtime 0.0454–0.0671 s. Yellow ×1 |
| 2 NumPy region-grow cuboid | classical | 25 | 0 | 0 | P = R = 1. Section 7.63–7.77 mm. Length 5.49–5.62 mm. Angle MAE 0.00023–0.01569°. Runtime 0.6185–0.6542 s. Yellow ×1. Not native PCL |
| 3 CloudCompare RANSAC-SD | classical | 0 | 25 | 0 | Lean filled on 25/25. P 0.125–0.25, R = 1, 4–8 boxes. Angle MAE 0.00123–0.08872°. Section over 10 mm on 22 scenes (row range 4.95–30.73 mm). Runtime 1.3308–1.5905 s. Yellow on every primitive box. Stage-0 bars fail because the stud is several faces |
| 4 PTv3 control | control | 0 | 0 | 25 | Every histogram is 25,666 points of `clutter` and zeros elsewhere. No stud-named class. Stud cells null. Runtime 38.5–67.2 s, including checkpoint load, normals, and 10-pass test-time augmentation |
| 5 RandLA-Net control | control | 0 | 0 | 25 | 25 distinct S3DIS histograms. No stud-named class. Stud cells null. On the one-stud card (same cloud as E-one): floor 2,229, door 7,239, chair 4,421, clutter 11,777. Runtime on the matrix 0.211–0.560 s after checkpoint load |
| 6 pyRANSAC-3D | classical | 25 | 0 | 0 | P = R = 1. Section, length, and angle MAE match rank 1’s ranges above (shared minimal OBB when the cuboid inliers are the whole stud). Runtime 1.0944–1.2426 s. Yellow ×1 |

The first Oz_PC sweep (PR #18) left rank 3 as `blocked_install` on all 25. Table 4 uses the later measurement (PR #19): primitive boxes on 25 of 25, stage-0 pass 0, `blocked_install` 0. Discovery order was the `CLOUDCOMPARE_EXE` environment variable, then `C:\Program Files\CloudCompare\CloudCompare.exe`, then PATH. Version recorded: 2.14.beta (29 Aug 2026).

A stud-only parameter tune of rank 3 is in progress. Table 4 is the untuned multi-face result. No tuned pass rate is stated.

Rank 2’s angle MAE reaches 0.01569° on the 4° lean about −X, where rank 1 records 0.00864°. The boxes are not copies of each other on every scene. On the earlier Linux one-stud cloud, PCL 1.14 returned one cluster, left 133 points unassigned, and matched rank 1’s printed section, length, and angle (7.7 mm, 5.57 mm, 0.00345°) at a runtime of 0.1816 s. That Linux CloudCompare 2.11.3 card failed the same way as the matrix: precision 0.125, eight planes, section 30.46 mm, angle 0.08836°, recall 1.

### 5.3 Synthetic fine-tune of ranks 4 and 5 (2026-09-25)

Source: `docs/research/20-synthetic-stud-finetune.md`. Both trains finished on the same RTX 4080 SUPER. The control cards in Section 5.2 were not rewritten.

**Table 5. Fine-tune training (class S).**

| Stack | Wall time | What changed | Checkpoint |
| --- | --- | --- | --- |
| Rank 4 PTv3 | 98.1 s (3 head epochs) | New 2-class MLP only. Backbone frozen (486 tensors copied, 4 trained). Decoder-unfreeze rule did not fire | `pointcept_stud_2class.pth`, 38,801 bytes, epoch 2 |
| Rank 5 RandLA-Net | 237.5 s (5 epochs, saved epoch 3) | S3DIS encoder copied. New 2-class layer trained | `randlanet_stud_2class.pth`, 20,171,595 bytes, epoch 3 |

Validation on the 33 held-out synthetic clouds, as recorded in that note: rank 4 stud recall on stud-only scenes 1.0, floor stud IoU 0.998, floor clutter IoU 0.993. Rank 5, scored with per-cloud batch-norm statistics (`randlanet_val_corrected.json`): stud recall 1.0, floor stud IoU 0.992, floor clutter IoU 0.977. A clutter IoU near 0 inside `randlanet_train_log.json` is `model.eval()` using S3DIS running statistics and is not the result reported here.

**Table 6. Fine-tune on the 25 phase-1 clouds and on one extra stud (class S).** The phase-1 clouds have no floor. Both models labeled all 25,666 points as stud, so the lean is that cloud’s minimal OBB and is identical for the two ranks.

| Check | Rank 4 | Rank 5 |
| --- | --- | --- |
| Stud box and a lean on phase-1 cards | 25 / 25 | 25 / 25 |
| Clutter only on phase-1 cards | 0 | 0 |
| Mean absolute lean error on the 25 cards | 0.004° | 0.004° |
| Largest absolute lean error | 0.009° (true 4° about +X, measured 3.991°) | same |
| Timed infer after warmup, weights on GPU, cloud `stage0_2x4_lean0.200_ax+Y` (not a phase-1 card) | 0.050 s, 25,666 stud points, measured lean 0.216°, absolute error 0.016° | 0.149 s, same points, same lean, same error |
| 0.05° +X phase-1 card, section and length | 7.7 mm and 5.6 mm | same, because the labels match |

**Table 7. Two held-out stud-plus-floor clouds (class S).** 34,502 points each. A dressed stud in this generator is 25,666 points. Section error on these boxes is about 20 mm in the source note.

| Scene | True lean | Rank 5 stud points | Rank 5 measured | Rank 5 abs. error | Rank 4 stud points | Rank 4 measured | Rank 4 abs. error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| val_0025 | 0° | 25,466 | 0.194° | 0.194° | 25,675 | 0.138° | 0.138° |
| val_0026 | 0.15° | 25,458 | 0.043° | 0.107° | 25,672 | 0.138° | 0.012° |

Rank 5 misses a couple of hundred stud points on these two clouds. Rank 4 takes a handful of floor points. One floor cloud takes about 0.31 s (rank 5) or 0.07 s (rank 4). A 25/25 box rate on the floorless phase-1 set does not show that either model rejects clutter.

### 5.4 Field

No class F numbers exist. ε is null. The one-stud protocol with a level has not been run on lumber.

## 6. Discussion

The synthetic passes show that the peel, a density cluster or a cuboid fit, the minimal box, and the yellow paint are connected on generator geometry with a clear gap and 1 mm noise. Perfect detection on that geometry is the bring-up the bars were written to enforce. The cloud was sampled from the same dressed boxes the fitter expects, and the Open3D `eps` threshold was adjusted after a failure on this generator (`eps` 20 mm, `min_points` 80 had marked the stud as noise).

Section residuals near 8 mm are large next to a tip offset of about 5 mm at τ over 8 ft, and they are still a statement about Gaussian tails on a complete surface. Length bias on the mini-wall is mostly the peeler. Angle errors of a few thousandths of a degree, and at most 0.01569° for rank 2 on the published S1 rows, sit under τ and under the 0.05° synthetic bar. They are errors against the generator. They are not a prediction of error under beam divergence, dropout, or an unleveled instrument.

Rank 3 is the useful negative. RANSAC shape detection does return an angle — from about 0.001° to 0.089° on the 25 rows — and still fails the stud definition, because a 2×4 is several planes. Recall stays 1 when one of those planes lands within 0.15 m of the stud center. Precision between 0.125 and 0.25 is the miss. A parameter tune aimed at one stud rather than one face is in progress. Until that note exists, the measured outcome is 0 of 25 stage-0 passes.

Ranks 4 and 5, before fine-tuning, show the vocabulary failure C4 names: a forward pass can label every point and still have no stud. After a synthetic fine-tune the opposite risk appears. On a cloud that is only a stud, labeling every point stud and fitting the shared box recovers the generator OBB (mean absolute error 0.004° on the 25 cards). That number is the box of a complete surface, shared with the classical finders, not evidence that the network found a stud inside a room. The two floor clouds are the first place the labels diverge, and the absolute lean errors there (0.012° to 0.194°) already exceed the largest classical S1 error. Section error of about 20 mm fails the 10 mm synthetic bar. The training set, the validation set, and the phase-1 set are synthetic. BIMStruct3D weights are CC BY-NC-SA 4.0 and are not a commercial model. The rank-4 checkpoint in git is the small head (38,801 bytes). Reload still needs the gitignored backbone.

Yellow paint is the result that should survive contact with a real cloud. A placeholder ε of 0.05° would have painted several of the early synthetic leans red or green. Those colors are stored so the rule can be inspected. They are not evidence that a sensor can support them.

The validity threats in [`THREATS_TO_VALIDITY.md`](../THREATS_TO_VALIDITY.md) remain part of the discussion: construct (floor versus gravity, τ versus the 0.15° alternate versus code), internal (generator circularity, one threshold loop, peel shortening, NumPy region growing standing in for PCL, fine-tune batch-norm statistics), and external (no openings, no sensor model, no public LOT-62 cloud). The citation collision on the Bassier DOI is a documentation threat, and it is corrected in the bibliography.

What would change the claim is class F: one real stud, the finders on that cloud, a level protocol with the resolution written down, and ε still unlocked.

## 7. Conclusion

TruePlank instance-segments vertical studs, fits a minimal oriented box, and reports lean against an explicit Z-up reference. The paint rule refuses green and red while the device band is unknown. On synthetic dressed studs, Open3D, a NumPy region-grow cuboid, and pyRANSAC-3D meet the stage-0 bars on a 25-scene lean sweep. CloudCompare shape detection measures a lean and fails the one-stud bar by splitting the member into faces. Office-vocabulary networks do not name a stud until they are fine-tuned, and a synthetic fine-tune that labels an entire floorless cloud as stud is a bring-up, not a field detector.

Future work, in the order the design plan already uses: a real stud and a level (ε still unlocked, so the color stays yellow); bow with the ends held (S1b); a multi-stud wall with plates; native PCL if the binary is built; the CloudCompare stud-only parameter tune, reported only after its scorecards exist; SAM 2 only when a capture already has a registered image. Stages 4–7 wait on that lumber. No class-F number is implied by the tables above.

## Data and code

Repository code: `src/openwall_stud/`. Scorecards: `artifacts/scorecards/` (phase 1 under `phase1_s1/`, fine-tune under `phase1_s1_finetune/`). Human logs:

- `docs/research/13-stud-seg-results-by-day.md`
- `docs/research/16-one-stud-five-finder-run.md`
- `docs/research/18-ozpc-ranks4-5-run.md`
- `docs/research/19-phase1-s1-lean-sweep.md`
- `docs/research/20-synthetic-stud-finetune.md`
- Design notes: `docs/research/12-stud-seg-design-plan.md`, `docs/research/11-stud-segmentation-algorithm-ranking.md`, `docs/tolerances.md`

Notes that are not on this branch, cited above by branch path: house-alike hunt on `cursor/house-alike-cloud-hunt-0474`, methods shortlist on `cursor/methods-beat-shortlist-e9dc`.

No point-cloud files of real buildings are stored in git. BIMStruct3D `model_best.pth` and the S3DIS zoo checkpoint are gitignored. The two fine-tune weight files named in Section 5.3 are in `artifacts/weights/finetune/`.

A re-run that changes a quoted number needs a new dated row, not a silent edit of Section 5.

## Ethics

Jobsite and residential scans can identify people and addresses. None are included. A color on a stud can be misread as a code or safety decision. τ is a derived finish guideline, the 0.15° figure is a second derived guideline from a summary that was not opened as a PDF, and ε is unlocked. License constraints for later stacks (CloudCompare GPL-3.0 if linked, CC BY-NC-SA 4.0 on the BIMStruct3D checkpoint, AGPL-3.0 on Ultralytics YOLO) are not a license to ship those components inside a closed application.

## References

Markdown list keyed to [`references.bib`](../references.bib). A later Pandoc pass can resolve the same keys (`make pdf` in the paper directory, when pandoc is installed). Entries marked **UNVERIFIED** must be checked before camera-ready. This revision did not add keys. DOI collisions are footnoted under Bassier.

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

**ester1996dbscan.** Ester, M., Kriegel, H.-P., Sander, J., and Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining (KDD)*, 226–231. AAAI Press. **UNVERIFIED PAGINATION.**

**mariga2026pyransac.** Mariga, L. (2026). pyRANSAC-3D (version 0.7.0) [software]. Zenodo. https://doi.org/10.5281/zenodo.21988437 — Run on class S in this repository (rank 6). No published stud accuracy for the library.

**bassier2020walls.** Bassier, M., and Vergauwen, M. (2020). Unsupervised reconstruction of Building Information Modeling wall objects from point cloud data. *Automation in Construction*, 120, 103338. https://doi.org/10.1016/j.autcon.2020.103338

**Footnote, DOI collision.** The engineering ranking cites Sensors 2023, DOI 10.3390/s23041924, as Bassier. Crossref resolves that DOI to **ntiyakunze2023sensors**: Ntiyakunze, J., and Inoue, T. (2023). Segmentation of structural elements from 3D point cloud using spatial dependencies for sustainability studies. *Sensors*, 23(4), 1924. https://doi.org/10.3390/s23041924

### Learned point clouds, and gated image segmentation

**wu2024ptv3.** Wu, X., Jiang, L., Wang, P.-S., Liu, Z., Liu, X., Qiao, Y., Ouyang, W., He, T., and Zhao, H. (2024). Point Transformer V3: Simpler, faster, stronger. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 4840–4851. https://openaccess.thecvf.com/content/CVPR2024/html/Wu_Point_Transformer_V3_Simpler_Faster_Stronger_CVPR_2024_paper.html — Also arXiv:2312.10035. The open-access bibtex did not print a DOI, so none is invented here.

**pointcept.** Pointcept contributors. Pointcept [software]. https://github.com/Pointcept/Pointcept

**jiang2020pointgroup.** Jiang, L., Zhao, H., Shi, S., Liu, S., Fu, C.-W., and Jia, J. (2020). PointGroup: Dual-set point grouping for 3D instance segmentation. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 4866–4875. https://doi.org/10.1109/CVPR42600.2020.00492 — Named in the plan. Not run here.

**zhou2018open3d.** Zhou, Q.-Y., Park, J., and Koltun, V. (2018). Open3D: A modern library for 3D data processing. arXiv:1801.09847. https://arxiv.org/abs/1801.09847

**open3dSoftware.** Open3D authors. Open3D (version 0.20.0) [software]. https://github.com/isl-org/Open3D

**ravi2024sam2.** Ravi, N., Gabeur, V., Hu, Y.-T., Hu, R., Ryali, C., Ma, T., Khedr, H., Rädle, R., Rolland, C., Gustafson, L., Mintun, E., Pan, J., Alwala, K. V., Carion, N., Wu, C.-Y., Girshick, R., Dollár, P., and Feichtenhofer, C. (2024). SAM 2: Segment anything in images and videos. arXiv:2408.00714. https://arxiv.org/abs/2408.00714 — Planned gated mask only. Not run.

### Wood-stud pose and the image detector in front of it

**xie2026wfc.** Xie, C., and Alwisy, A. (2026). Advancing robotic automation in wood-framed construction using vision-driven adaptive control. *Automation in Construction*, 185, 106858. https://doi.org/10.1016/j.autcon.2026.106858 — Related only. README rotation figures were not re-tabulated from the journal PDF.

**jocher2023ultralytics.** Jocher, G., Qiu, J., and Chaurasia, A. (2023). Ultralytics YOLO (version 8.0.0) [software]. https://github.com/ultralytics/ultralytics — Related only as the detector in front of pose in xie2026wfc.

### As-built LiDAR and scan-to-BIM

**tang2010asbuilt.** Tang, P., Huber, D., Akinci, B., Lipman, R., and Lytle, A. (2010). Automatic reconstruction of as-built building information models from laser-scanned point clouds: A review of related techniques. *Automation in Construction*, 19(7), 829–843. https://doi.org/10.1016/j.autcon.2010.06.007

**bosche2015scan.** Bosché, F., Ahmed, M., Turkan, Y., Haas, C. T., and Haas, R. (2015). The value of integrating Scan-to-BIM and Scan-vs-BIM techniques for construction monitoring using laser scanning and BIM: The case of cylindrical MEP components. *Automation in Construction*, 49, 201–213. https://doi.org/10.1016/j.autcon.2014.05.014

### Construction tolerances

**woodworksTolerances.** WoodWorks. Construction tolerances for light wood-frame projects. Wood Products Council expert tip. https://www.woodworks.org/resources/construction-tolerances-for-light-wood-frame-projects/ — Page text checked 2026-09-25.

**ballast2007handbook.** Ballast, D. K. (2007). *Handbook of Construction Tolerances* (2nd ed.). John Wiley & Sons. ISBN 978-0-471-93151-5. The 1/4 inch in 10 feet figure used here is WoodWorks’s summary of this handbook, not a re-reading of the handbook page.

**nahbGuidelines.** National Association of Home Builders. Residential Construction Performance Guidelines. **UNVERIFIED PLACEHOLDER.**

**ufgs061000.** Unified Facilities Guide Specifications. UFGS 06 10 00, Rough Carpentry. **UNVERIFIED PLACEHOLDER.** The 1/4 inch in 8 feet figure, and the derived alternate ≈ 0.1492°, rest on WoodWorks’s summary only.

### Sensing context

**erland2026iphone.** Erland, B. M., and Gaulton, R. (2026). A comparison of lidar accuracy across iPhone models, with implications for reproducibility and cross-study comparison. *Remote Sensing Letters*, 17, 1620–1631. https://doi.org/10.1080/2150704X.2026.2720055 — RMSE centimeters in the repository sensing survey were not re-extracted from the PDF.

**apple2022roomplan.** Apple. (2022). RoomPlan. Apple Machine Learning Research; WWDC22 session 10127. https://machinelearning.apple.com/research/roomplan — **UNVERIFIED THIS PASS** as a live fetch.

**appleArkitGravity.** Apple. ARKit `ARConfiguration.WorldAlignment`. Apple Developer Documentation. https://developer.apple.com/documentation/arkit/arconfiguration/worldalignment-swift.enum — **UNVERIFIED THIS PASS** as a live fetch. Y-up. Not ε.
