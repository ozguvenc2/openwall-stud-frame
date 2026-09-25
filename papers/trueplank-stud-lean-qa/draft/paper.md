# Stud instance detection and lean QA from point clouds

**Working title.** Automated stud instance detection and lean QA from LiDAR and other point clouds.

**Products.** BeamWeaver is the platform. TruePlank is the stud QA product. OpenWall is the engineering name of this repository and of the pipeline in `src/openwall_stud/`.

**Status.** First draft of the section skeleton. Venue-agnostic Markdown. Not submitted. Abstract is TBD.

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

## 1. Introduction

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

This paper is the public write-up of that method. The implementation that exists today is a synthetic bring-up of one classical stack (Open3D) on curriculum stages 0, 2, and 3. Four other stacks are specified and not run. No jobsite cloud is in the repository. Section 5 therefore contains one labeled synthetic excerpt and an explicit placeholder for field results.

## 2. Related work

### 2.1 Timber member cuboids

Pöchtrager and colleagues reconstruct historic roof beams as cuboids from planar side faces in terrestrial laser scans [pochtrager2017roof, pochtrager2018roof]. Özkan and colleagues extend that workflow with a split of non-linear segments. On one historic roof they report automatic beam completeness, against a manual count, rising from 29% to 63%, and 75% after additional manual splits [ozkan2022timber]. A later paper completes roof models with the same cuboid route [ozkan2024completion]. Chen, Jiang, and Xiong generate geometric finite-element models from timber point clouds [chen2025timberfe]. The OpenWall ranking records, from that paper’s specimen, dimension errors within 3%, plane angles within 1°, and cylinders forced to a global vertical axis. Those specimen digits were not re-tabulated from the PDF for this draft. Forcing an axis to global Z would erase the lean TruePlank measures.

These papers motivate rank 2 of the planned bake-off: region growing, then a cuboid, without a remote coplanar merge and without a forced vertical axis. They do not supply a 2×4 angle error. Roof-beam completeness stays in this section.

### 2.2 Primitives and wall objects

Schnabel, Wahl, and Klein detect planes, spheres, cylinders, cones, and tori in unorganized point clouds [schnabel2007ransac]. CloudCompare’s RANSAC Shape Detection plugin implements that family. A rectangular stud is not one of those primitives, and coplanar stud faces can collapse to one plane. Rank 3 exists so that primitive count can be compared with stud count on the same cloud. The plugin has not been run.

Bassier and Vergauwen reconstruct BIM wall objects from point clouds without supervision [bassier2020walls]. The engineering plan refuses a merge of remote coplanar patches because studs that share a wall plane would become one instance. A Sensors 2023 DOI written next to the name Bassier in the engineering ranking resolves, on Crossref, to a different paper [ntiyakunze2023sensors]. This draft does not use that DOI as a Bassier citation.

### 2.3 Learned instance and semantic models

Point Transformer V3 is a scalable point backbone with reported results on indoor and outdoor benchmarks [wu2024ptv3]. Pointcept is the codebase in which that backbone is trained [pointcept]. PointGroup is an instance-segmentation head from the same research line [jiang2020pointgroup]. The planned rank 4 uses that stack only after stud labels exist on a real room (stage 5). No weights are loaded here. Published ScanNet or S3DIS figures are left on those benchmarks.

Open3D is the library behind the implemented baseline [zhou2018open3d, open3dSoftware]. Clustering after the plate peel is DBSCAN [ester1996dbscan].

### 2.4 Tolerances and sensors

The tolerance chain used in software is the WoodWorks summary and the derived angle above, not a new code interpretation [woodworksTolerances, ballast2007handbook]. Phone LiDAR comparisons are centimeter-class in the repository sensing survey, which points at Erland and Gaulton for a cross-model iPhone study [erland2026iphone]. The centimeters in that survey were not re-extracted from the PDF here. The sensing note’s conclusion, which this paper adopts as a protocol constraint, is that survey terrestrial scanners are the instrument class whose published specifications sit near τ, while phone LiDAR and robotics lidars are detection sensors. Brochure specifications are not ε. A full stack — range, registration, segmentation, box fit, and the gravity or level reference — is unmeasured [docs/tolerances.md, docs/research/01-sensing-modalities.md].

## 3. Method

The outline with parameters, the blank error budget, and the statement that the names Hypothetical / Ideal / Realistic / Absolute are not a method in the design documents is [`METHODS.md`](../METHODS.md). This section is the narrative form.

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

Class S compares the box to the generator. Class F will compare it to a level, a total station, or a hand label, using the source names already reserved in the day-table writer. Class R, a realisticized cloud whose noise comes from a scanner model, is not implemented. The 1 mm Gaussian is class S.

## 4. Experiments

The plan, including what is run and what is owned elsewhere, is [`EXPERIMENTS.md`](../EXPERIMENTS.md).

**Executed (class S).** On 2026-09-24 (America/Los_Angeles) the Open3D baseline was run on seven generator scenes by `scripts/run_stage0_baseline.py`. Stub cards were written for the other four stacks and marked `not_run`. Pass bars inside that script are bring-up checks: perfect detection, section error at most 10 mm, length error at most 25 mm (30 mm on stage 3), angle error at most 0.05° (0.10° on stage 3), and yellow production paint. A miss fails the script. The bars are not a field acceptance test.

**Not executed.** PCL on the same scenes. CloudCompare primitive counts. Any real capture. The one-stud five-finder (one physical stud, five finders, a level if the stud is standing, yellow paint) is specified as stage 1 and is owned by another agent. This draft does not report it. Stages 4–7 have no clouds. No realisticized generator is specified.

**Intended field protocol, still empty.** Record sensor, export format, whether Z is gravity, and the floor normal if one was fit. On a standing stud, record the level model and BOT / MID / TOP. Do not publish an angle MAE when the three readings disagree by more than the printed resolution.

## 5. Results

### 5.1 PLACEHOLDER — field and five-finder

No class F numbers exist. The one-stud five-finder has not been copied into this draft. Ranks 2–5 have null metrics. Stages 1 and 4–7 have null metrics. ε is null. Do not fill this subsection from Section 5.2.

### 5.2 Class S excerpt — synthetic Open3D, 2026-09-24

The table quotes the day log regenerated from `artifacts/scorecards/results_by_day.csv`, which matches the per-scene JSON files `artifacts/scorecards/open3d_stage*.json`. Ground-truth source on every row is `synthetic`. Detection precision and recall are 1. Section and length columns are the maxima. Angle is the mean absolute error against the generator reference; with one stud that equals the absolute error. Stage 3 also stores a maximum absolute error of 0.00719° in `open3d_stage3_stage3_mini_wall_4.json`. Percent of studs inside τ is 100 on each scene. Production colors are yellow, so the day-log paint column is 100 under the yellow-only rule. That percentage is not agreement with a level. `device_eps_deg` is empty.

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

Rendered from [`references.bib`](../references.bib). Keys are in square brackets above so a later Pandoc or LaTeX pass can resolve them. This Markdown file does not embed a generated bibliography.
