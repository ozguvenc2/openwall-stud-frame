# Methods that could beat the TruePlank stud shortlist

Research date: **2026-09-25** (America/Los_Angeles). This note asks which open or commercial methods could beat the five-stack bake-off in [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md) for TruePlank: instance a vertical 2×4, fit a tight oriented box, and report lean against the floor now and gravity later. OpenWall is the engineering pipeline in this repo. BeamWeaver / TruePlank is the product name. The sensing and gravity stack in [02-software-segmentation-angles.md](02-software-segmentation-angles.md) is unchanged.

Machine-readable twin: [17-methods-that-beat-shortlist.json](17-methods-that-beat-shortlist.json).

Nothing in this pass was downloaded or executed. No checkpoint, LAS, PLY, or vendor trial was committed. A number below is copied from the cited page, or it is marked **unknown**. A result on KITTI, nuScenes, COCO, S3DIS, a historic roof, a reinforced-concrete specimen, or one turntable stud is **not** a TruePlank score.

## Finding

**No method surveyed here is scored `beat_shortlist`.** None has a published 2×4 instance rate and a floor-relative lean error on a bare stud wall, and this repo has not run any of them against ranks 1–5.

Two stacks are worth adding to the bake-off because their outputs match the scorecard and they attack a failure mode rank 1 has not closed:

1. **Sequential cuboid RANSAC** ([pyRANSAC-3D](https://github.com/leomariga/pyRANSAC-3D) v0.7.0) after the same plate peel as rank 1.
2. **A registered-image mask, lifted back onto the points, then the shared box.** Implement the mask with Meta SAM 2 (Apache-2.0). Run it only when the capture already has a camera pose. Skip it on a pure LAS/PLY.

The third slot stays empty. YOLO, Vuforia, RoomPlan, and the commercial scan-to-BIM tools do not take that slot.

Do not drop ranks 1–5. Rank 1 is still the first experiment. Rank 2 is still the timber-cuboid recipe. Rank 3 stays as the Schnabel disagreement check. Ranks 4 and 5 stay as labeled-learning and office-vocabulary controls.

## What a win would have to show

Same clouds, same floor normal, same tolerance, same device band as doc 11.

| Stage | A method that beats rank 1 must do this |
| --- | --- |
| Instance | One box per physical 2×4 on a bare wall. A merged bay is a miss. Plates are not studs. |
| Box | A tight oriented box in the cloud frame. An axis-aligned wall box, a 2D image box, or a CAD axis-aligned box of a model is a different object. |
| Angle | The long-axis angle against the stored floor normal, later against gravity. Forcing the member to global Z, or to a horizontal rectangle in XY, erases the lean. |
| Paint | The shared green / yellow / red rule. Until the device band exists, yellow. A 2° industrial pose bar is about sixteen times the working ~0.12°. |

Fit is 1–5 for that pipeline. It is not a score of the tool on its own market.

## Shortlist this note is trying to beat

| Rank | Stack | Fit | What a challenger has to beat |
| --- | --- | --- | --- |
| 1 | Refined Open3D: peel near-horizontal plates, DBSCAN below the bay gap, vertical-stick filter, tight box | 5 | Separated sticks once plates are gone. Unmeasured on a field wall. Fails when members touch or a face is shattered. |
| 2 | PCL region-grow, then a cuboid, Özkan / Pöchtrager rules, no remote coplanar merge | 4 | Partial faces and joints. Published object is a historic roof, not a 2×4 wall. |
| 3 | CloudCompare RANSAC Shape Detection (Schnabel planes, spheres, cylinders, cones, tori) | 3 | An independent primitive fitter. A 2×4 is not one of those five shapes. |
| 4 | Pointcept PTv3 / PointGroup. BIMStruct3D weights are a control only | 3 | The path after we label studs. Zero-shot classes are walls and columns. |
| 5 | Open3D-ML RandLA-Net or KPConv, S3DIS weights | 2 | One controlled failure so an office mIoU is not reused. |

## YOLO — no as the stud finder

**No.** A YOLO detector does not replace ranks 1–2 on a point cloud, and it does not report plumb.

YOLO is an image detector. Ultralytics YOLO11 (and the v8 line and YOLO-World in that repo) predicts a 2D box, an optional instance mask, 2D keypoints, or a **2D** oriented box of the kind used on aerial images. The [YOLO11 docs](https://docs.ultralytics.com/models/yolo11) cite COCO detection (the Hugging Face card lists mAP 54.7 at 0.5:0.95). That number is COCO. It is not a stud, not a 3D box, and not an angle. [Ultralytics licensing](https://www.ultralytics.com/license) is AGPL-3.0, or a paid Enterprise license whose price was **not** on that page. Shipping TruePlank closed-source on the AGPL weights would obligate the whole application, or the Enterprise license.

Where an image really is the sensor, YOLO has been used on wood, and the published task is still not this scorecard:

| Use | What was measured | Why it is not a TruePlank win |
| --- | --- | --- |
| Xie and Alwisy, Automation in Construction 2026, [WFC dataset README](https://github.com/yigediao/wfcdataset) | YOLOv8 is the **detector** in front of a separate 6D pose fitter, on 288 close-range ZED 2i views of **one** 2×4. Their pose method, not YOLO alone: mean rotation **1.43°** (median 1.00°), mean translation 2.18 mm, 73.61% of poses inside 20 mm and 2°. | The strict bar they publish is 2°, not ~0.12°. The scene is a turntable stud, not a wall. Pose code is listed as “coming soon”. The 10.65 GB Dropbox archive was not downloaded. |
| Panelized framing, [Journal of Industrialized Construction](https://journalofindustrializedconstruction.com/index.php/jic/article/view/341) | Abstract: a fine-tuned YOLOv8s finds stud centers and nailer positions on a framing machine; defect-detection accuracy 99.7%; average alignment error below 1 mm. | Factory cameras and a nail actuator. Authors were not extracted. The full article was not opened. The 1 mm figure is nailing alignment in that abstract, not lean of a site stud. |
| WDNET-YOLO, [Buildings 2025](https://doi.org/10.3390/buildings15132281) | Surface cracks and knots. mAP50 65.5% to 69.2% and mAP50-95 36.7% to 40.2% versus YOLOv8n, on their timber-defect images. | Defect pixels. The paper says the RGB model cannot see internal defects. |
| ISARC 2025, [DOI 10.22260/isarc2025/0179](https://doi.org/10.22260/isarc2025/0179) | YOLOv8 variants on images of stud bends, twists, and missing parts. Precision, recall, and mAP are named. | Values were not extracted. Image defects, not a wall schedule. |
| Heritage HBIM, [npj Heritage Science 2025](https://doi.org/10.1038/s40494-025-02151-6) | YOLO boxes on **images of** a timber point cloud. Width and height are pixels until a scale conversion. | Traditional components, image scale, no floor-relative lean. |

**YOLO3D and BEV detectors are the wrong geometry.** Ali et al., ECCV 2018 workshop ([YOLO3D](https://openaccess.thecvf.com/content_ECCVW_2018/papers/11131/Ali_YOLO3D_End-to-end_real-time_3D_Oriented_Object_Bounding_Box_Detection_from_ECCVW_2018_paper.pdf)), feed a bird’s-eye image of a LiDAR cloud to a YOLO v2 variant and regress a 3D box plus a **heading in that bird’s-eye plane**, evaluated on KITTI. [BEVFusion](https://arxiv.org/pdf/2205.13542) (NeurIPS 2022) fuses camera and LiDAR in a bird’s-eye grid for nuScenes driving. A stud’s lean is the tilt of its long axis away from the floor normal. A bird’s-eye heading is rotation about the vertical. Those are different angles. No construction-stud class was found for either model.

**When RGB helps.** A registered photo can propose which points belong to one stud when DBSCAN bridges a plate or two studs that touch. The angle still has to be computed on the lifted points with the shared box. YOLO-World’s text prompt (“wood stud”) was **not** tested here; zero-shot accuracy is **unknown**. That proposal is the gated bake-off add below, and SAM 2 is the implementation to use so the engineering repo does not take an AGPL dependency for the same experiment.

**When RGB does not help.** A pure LAS/PLY has no image. Projecting the cloud to a picture and reading a 2D box throws away the metric axis unless the projection is inverted. Even then the 2D box is not the lean.

## Vuforia — no

**No.** Vuforia Engine is the wrong tool for a stud schedule or a plumb angle.

[Model Targets](https://developer.vuforia.com/library/vuforia-engine/images-and-objects/model-targets/model-targets-api-overview/) track a physical object that matches a **CAD model** in shape and in meters. The pose is the model in the camera frame. The origin is the CAD origin and cannot be moved from the API. `vuModelTargetObserverGetAABB` returns the **axis-aligned** box of that CAD model in the target frame, not a box fitted to scanned points and not a lean against the floor. [Best-practice guidance](https://developer.vuforia.com/library/vuforia-engine/images-and-objects/model-targets/best-practices/model-targets-supported-objects-cad-model-best-practices/) wants one distinctive object (machinery, a vehicle, an appliance) whose CAD matches the part. A wall of identical 2×4s is the case that guidance is written against: repeated geometry, no unique CAD, and the lean is the thing that makes the as-built differ from a plumb model.

[Area Targets](https://www.ptc.com/en/products/vuforia/vuforia-engine/pricing) localize the device inside a pre-scanned room. They are an environment anchor. They do not emit a stud instance.

Pricing, from the [PTC pricing page](https://www.ptc.com/en/products/vuforia/vuforia-engine/pricing) and the [license FAQ](https://developer.vuforia.com/library/vuforia-engine/FAQ/pricing-and-licensing-options/), read this pass: the Basic plan is free and can develop Model Targets and Area Targets, with a watermark and without store publishing (20 Model Targets and 20 Area Targets in the generators). Publishing those features needs Premium or Enterprise. Dollar amounts for Premium and Enterprise were **not** on those pages (quote). No stud, OBB-of-a-cloud, or gravity API was found.

A later AR overlay of an already measured stud could use a phone pose. That is display. Doc 02 already names ARKit gravity as a reference vector for our own capture. Vuforia does not compute the stud.

## Capture apps and phone AR

These produce a cloud, a mesh, or a room model. They are not stud segmenters. Doc 01 and doc 02 already cover Polycam export tiers and ARKit gravity.

| Tool | Input | Stud instances | Box and angle | License / price this pass | Verdict |
| --- | --- | --- | --- | --- | --- |
| ARKit RoomPlan | iPhone / iPad LiDAR plus camera | Walls, openings, doors, windows, and furniture. [WWDC22](https://developer.apple.com/videos/play/wwdc2022/10127/) lists those surface categories. No stud category. | Surfaces are planes. Furniture objects are cuboids. No stud lean. Gravity is a separate ARKit session (doc 02). | Apple platform. No fee found for the API. | **no** |
| ARCore Depth / Raw Depth | Android depth image, optional hardware depth | No object class. [Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) is a denser depth map plus confidence. | No box. | Google platform API. | **wrong_modality** |
| Polycam | Phone LiDAR or photos | Capture and export. Not a segmenter (doc 01). | No stud box. | Point-cloud export is Business and Enterprise (doc 01). | **wrong_modality** |
| Scaniverse (Niantic Spatial) | Phone, and 360° cameras on paid tiers | Capture, mesh, splat, visual-positioning map. No stud tool on the pages read. | No stud box. [Pricing](https://www.nianticspatial.com/en/pricing): Free, Plus **$20/mo or $200/yr**, Pro **$50/mo or $500/yr**, Enterprise custom. Exports named there include FBX, SPZ, and PLY. | Closed app. A [community reply on 12 Sep 2026](https://community.nianticspatial.com/t/not-able-to-locate-scaniverse-api-documentation-to-integrate-it-in-project/5795) says there is no third-party scanning API; Pro and Enterprise are in-app commercial use. | **wrong_modality** |
| StudSpec API | Photo, video URL, or a document | The [public docs](https://developers.studspec.ai/docs) return tags and a component list whose sample `type` is `"stud"`, with `wall_location` and `height_from_floor` as strings (the sample uses `"0-96 inches"`). | No oriented box and no degree in the sample payload. `estimated_length` in the sample is a string (`"14 ft"`). | Private HTTP API. Price **unknown**. | **wrong_modality** |

An older Scaniverse support page on a `staging-isolated` host lists LAS export and says the app is free. That host is not the 2026 Niantic pricing page. LAS export is **unverified**. Gaussian splats remain a view, not a metrology cloud (doc 05).

## Classical point-cloud tools

### Sequential cuboid RANSAC — the first add

[pyRANSAC-3D](https://pypi.org/project/pyransac3d/) v0.7.0 (uploaded 2026-08-18; Apache-2.0; citation DOI [10.5281/zenodo.7212567](https://doi.org/10.5281/zenodo.7212567)) fits one cuboid to a NumPy cloud. The [cuboid page](https://leomariga.github.io/pyRANSAC-3D/api-documentation/cuboid/) defines the shape as six faces from three orthogonal normals, and v0.7.0 returns `center`, `extents`, and `axes` ([release notes](https://github.com/leomariga/pyRANSAC-3D/releases/tag/v0.7.0)). The axes are not locked to global Z. Lean would be our existing angle between the long axis and the floor normal.

The library fits **one** cuboid per call. It does not know a 2×4, a plate, or a bay. Used on a whole wall it can lock onto coplanar stud faces, which is the failure rank 1 refuses and rank 3 demonstrates with planes. The fair experiment is the rank 1 plate peel, then repeated fits with inlier removal, rejecting any cuboid whose section is not near a 2×4. That section test is ours. The documented default `thresh` is `0.05` in cloud units. The cuboid page’s inlier sentence still says “cylinder radius”, which is leftover wording, so the right threshold for a stud is **unknown** until we set it.

No stud accuracy is published. Fit **4**. Verdict **maybe**. This is bake-off add 1. It does not replace rank 2: region-grow cuboids are still the method for a stud that is only two faces and a joint. It does not replace rank 3: Schnabel’s five primitives remain the independent check, and this library adds the rectangular primitive those five do not have.

### CGAL shape detection — same job as rank 2, GPL

[CGAL Shape Detection](https://doc.cgal.org/latest/Shape_detection/index.html) (manual read for 6.2 / 6.3) implements Schnabel Efficient RANSAC and region growing. Region types named for 3D points are plane, sphere, and cylinder. There is no cuboid region. The [5.2.3 reference](https://doc.cgal.org/5.2.3/Shape_detection/group__PkgShapeDetectionRef.html) labels that package **GPL**. [CGAL’s license page](https://www.cgal.org/license.html) is dual: open-source GPL or LGPL by package, or a commercial license from GeometryFactory. The commercial price is **unknown**. A 6.x per-header license check was not opened; treat Shape Detection as GPL until that header is read.

Verdict **no** as a new stack. It is a second implementation of rank 2’s grow, with a license that blocks linking into closed-source TruePlank. Do not port it beside PCL.

### PDAL, LAStools, Potree

| Tool | What the page actually does | Stud / box / angle | Verdict |
| --- | --- | --- | --- |
| [PDAL `filters.dbscan`](https://pdal.io/en/stable/stages/filters.dbscan.html) and [`filters.cluster`](https://pdal.io/en/stable/stages/filters.cluster.html) | Density clusters or Euclidean clusters, writing `ClusterID`. BSD-family project (doc 02). | Same family as rank 1’s DBSCAN. No cuboid and no lean. Default `eps` / `tolerance` of 1.0 is in cloud units and is not a stud spacing. | **no** |
| LAStools | Doc 02: `las2las` reprojects and clips. No IMU or plumb flag on the README read then. Mixed rapidlasso license. Not re-read this pass. | No stud model. | **no** |
| Potree | Out-of-core web viewer. Doc 02 surveyed the Unity port (FastPoints) as display. The Potree repo was not re-fetched this pass. | No stud model. | **no** |

### Hough, supervoxels, GrowSP

Murtiyoso and Grussenmeyer, [Sensors 2020](https://doi.org/10.3390/s20082161), project a timber facet to a 2D image and use a Hough transform to split L- and Y-shaped faces. On a 100k-point subset of one castle dataset they report a median recall of **75.58%**. That is historic heavy timber, not a 2×4 wall. The split-the-joint idea is already inside rank 2 (Özkan’s linear split). Verdict **no** as its own stack. Fit **2**.

PCL’s supervoxel clustering (the library behind rank 2) over-segments a cloud into patches that a later step can merge. The class reference page was **not** opened this pass, and no stud metric was found. Verdict **maybe** as a preprocess inside rank 2 if faces shatter. Fit **2**. Not a bake-off row.

[GrowSP](https://github.com/vLAR-group/GrowSP) (CVPR 2023, [arXiv:2305.16404](https://arxiv.org/abs/2305.16404)) grows superpoints into unsupervised semantic classes. The README shows S3DIS, ScanNet, and SemanticKITTI. Those mIoU figures are not copied here. The LICENSE file was not opened (**unknown**). No instance head and no stud class. Verdict **no**. Fit **2**.

## Timber and frame papers, 2023–2026

### Xie and Alwisy 2026 — closest 2×4 pose, still not a wall

DOI [10.1016/j.autcon.2026.106858](https://doi.org/10.1016/j.autcon.2026.106858). The public artifact is the [WFC README](https://github.com/yigediao/wfcdataset), not a released fitter. Hardware is a ZED 2i. The object is one 2×4, turned through 12 orientations and 3 exposures, 288 samples, manual 6D labels. YOLOv8 finds the stud in the image. Their method then refines a point-cloud pose. FoundationPose, SAM-6D, and MegaPose are the baselines they publish.

README Table 2, rotation error in degrees (invalid outputs excluded; SAM-6D failed on 50/288):

| Method | Mean | Median |
| --- | ---: | ---: |
| Their pose method | 1.43 | 1.00 |
| FoundationPose | 7.25 | 5.30 |
| SAM-6D | 9.18 | 2.90 |
| MegaPose | 5.16 | 2.01 |
| Plane-fitting baseline | 28.28 | 23.93 |

README Table 3: their method is inside 20 mm and 2° on **73.61%** of samples. They describe that rate as up to 4.1× FoundationPose, 2.7× SAM-6D, and 1.8× MegaPose under those thresholds. Mean ADD-S for their method is 4.80 mm. The dataset license heading was empty in the README fetched here (**unknown**). Labeling and benchmark code are “coming soon”.

Two readings that this note refuses:

- Their 1.43° mean is a full rotation error on a single close-range stud. It is not evidence they beat ~0.12° on a wall, and it is not evidence they lose to rank 1, because rank 1 has no field angle either.
- The plane-fitting baseline at 28° mean rotation is a dominant plane on a close-up stud. It is not a measurement of rank 1’s plate peel.

Author posts quote grasping success and a “99.82% geometric accuracy”. Those phrases are **not** in the README tables and are not used here.

Verdict **maybe** as a single-stud RGB-D check once code exists. Fit **3**. Not a bake-off add while the fitter is unreleased and the archive is 10.65 GB. FoundationPose, SAM-6D, and MegaPose, on this same table, are worse than their method and still sit at several degrees. Verdict for those three on our pipeline: **no**. Fit **2**. They need RGB-D and, for FoundationPose and MegaPose, a model or a box. They do not read a registered TLS wall.

### Light-steel framing network — right words, wrong member

Lee, Rashidi, Talei, and Kong, [Buildings 2024](https://doi.org/10.3390/buildings14040952). Semantic labels on light-gauge **steel** wall frames (ENDUROFRAME C-channels, 90 mm deep), captured as HoloLens 2 meshes plus synthetic BIM, processed in MATLAB R2022b. Label names include stud, top plate, bottom plate, noggin, and bracing. Reported average testing accuracy: **82.88%** on as-built data alone, **86.15%** when synthetic BIM is added to training, **79.55%** on a hybrid test. The paper’s data statement: available on request, not public, because of ENDUROFRAME commercial sensitivity. The network architecture name was **not** established in the sections read (do not assume PointNet). The journal text treats dimensional inspection as future work. No lean number. Verdict **maybe** as a label list to copy when we annotate wood. Fit **2**. Not runnable.

### Reinforced-concrete frames — PCA axis, not a stud

Zhang, Liu, Li, Chen, and Xiong, [Electronics, 9 Jan 2026](https://www.mdpi.com/2079-9292/15/2/293). PointNet++ semantics, Fast Euclidean Clustering, then PCA for the member axis and RANSAC lines on the projected section, written out as IFC. Object: scaled reinforced-concrete frames, drone photos, ContextCapture. They report average dimensional error for beams and columns **within 3 mm**, with occluded exceptions. They do not report lean against a floor or against gravity. The PCA axis is free (it is not forced to Z), which is the property Chen 2025 gives up and which rank 1 already uses inside `get_oriented_bounding_box`. Code release: **not stated** in the sections read. Verdict **maybe** as a clustering variant (Euclidean clusters instead of DBSCAN) inside rank 1. Fit **3**. Not a new stack, and not wood.

### ERES 2026 timber deep learning — abstract only

Windapo, Bayonle, Lin, Mitropoulou, Raghu, Chen, and De Wolf, “Timber Structure Point Cloud Segmentation for Component-Level Reuse Valuation”, ERES 2026, [library record](https://eres.architexturez.net/doc/oai-eres-id-eres2026-160). The abstract says they fine-tune PointNet++, GrowSP, RandLA-Net, and SQN-DLA-Net on a purpose-built set of **20 timber structures**, and that they intend to report mIoU, per-class F1, quantities, and dimensional errors. The abstract contains **none of those numbers** and no code URL. A direct fetch of the record hit a bot check; the abstract text above is from the search snippet of that URL. Verdict **maybe** if a later paper ships weights and a stud or beam class. Fit **2**. Not a bake-off add. This is the same abstract doc 11 left unranked.

### Two papers that would erase the lean

- Chen, Jiang, and Xiong 2025 (doc 11, rank 6) force cylinders to axis (0, 0, 1). Already excluded.
- BIMStruct3D’s reconstruction note ([arXiv:2604.24311](https://arxiv.org/pdf/2604.24311)) fits a **horizontal** oriented box: the rectangle is level in XY under a Manhattan assumption. That is a wall model. A stud that leans by a fraction of a degree is flattened. Rank 4 may use the network as a zero-shot control. Do not adopt this box.

## Commercial and private tools

Prices below are only the figures read on a page this pass or already recorded in doc 02 / doc 11. “Quote” means no public number was found here. None of these enter the bake-off.

| Product | Stud instances of a bare 2×4 | Box and lean | Price | Verdict |
| --- | --- | --- | --- | --- |
| ClearEdge3D EdgeWise | Current product page was **not** re-fetched. Doc 11 (2026-09-24) found pipes, steel, ducts, walls, conduit, and cable trays, and did not find wood studs. A 2018 Aptella brochure says the structure tools extract “steel, concrete, and wood” from a **catalog**. That is not a 2×4 schedule and not a lean. | Vendor solid plus SmartSheet RMSE (fit-to-cloud). No floor-angle paint (doc 11). | Lite **USD 1,995 / year** on the page doc 11 fetched. Pro **unknown**. | **no** |
| ClearEdge3D Verity | Needs a design model. Not a segmenter (doc 11). | Rotation versus the model. | Quote (doc 02). | **no** |
| PointCab Origins + 4Revit | User-picked column, not an automatic stud (doc 11). | No plumb command found in doc 02. | 2026-09-23 shop prices later 404’d. Live price **unknown**. | **no** |
| FARO As-Built for Revit, BuildIT Construction | Walls and BIM elements. BuildIT’s wall-plumb workflow extracts a wall and can constrain the plane perpendicular to Z (doc 02). | A wall plane forced square to Z is the opposite of a measured stud lean. | **unknown** this pass. | **no** |
| Leica CloudWorx, Cyclone 3DR | CloudWorx fitters named in doc 02: steel, flanges, pipes, walls, floors, doors, windows. [Cyclone 3DR AI classification](https://leica-geosystems.com/products/laser-scanners/software/leica-cyclone/leica-cyclone-3dr/ai-classification-in-leica-cyclone-3dr-pt1) describes outdoor, road, and person/moving-object models. Studs are not named. | No stud lean. | **unknown** this pass. | **no** |
| Canvas Scan to CAD | [Help page](https://support.canvas.io/article/12-what-is-scan-to-cad), updated 15 Jan 2026: semi-automated model of walls, floors, cabinets, countertops, fireplaces, and the architectural shell. Revit output is aimed at LOD 200. Studs are not named. | Architectural shell, not a stud box. | **unknown** this pass. | **no** |
| Avvir (Hexagon) | [Product page](https://www.avvir.io/): compare a BIM to a cloud and flag installation discrepancies. The page says the brand folded into Hexagon Building Solutions as of 1 Feb 2024. | Needs the model. Not a raw-frame segmenter. | **unknown**. | **no** |
| Cupix | A 2021 trade article describes CupixWorks as 360° video to a cloud, with measurements and a vendor sentence about “98 to 99%” of laser-scan accuracy for plans. That sentence is a **vendor claim in a secondary article**, not a stud spec, and not a spec sheet. No stud extractor was found. | Measurements on a cloud. No stud OBB. | **unknown**. | **no** |
| Elysium InfiPoints | [Product page](https://www.elysium-global.com/en/product/infipoints/): pipes, cylinders, and planar walls, floors, and ceilings for plants. | No stud. | **unknown**. | **no** |
| StudSpec API | Photo and video language tags. See the capture table. | No metric box in the sample. | **unknown**. Private API. Worth a later look only if a geometry payload appears. | **wrong_modality** |

OPALS, which the Özkan workflow uses for region growing, is commercial. Price was not fetched in doc 11 and was not fetched here. Rank 2 does not depend on buying it; PCL region growing is the open implementation.

## Comparison against ranks 1–5

| Candidate | Fit | Verdict | Where it sits against the five |
| --- | --- | --- | --- |
| pyRANSAC-3D sequential cuboid | 4 | maybe | Could beat rank 1 when a stud is one rigid box and DBSCAN merges or splits it. Loses to rank 2 on partial faces. Adds the primitive rank 3 lacks. Does not touch ranks 4–5. |
| SAM 2 mask, lifted, then our box | 3 | maybe | Could beat rank 1’s **instance** step when a registered photo separates touching members. Does not replace the box or the angle. Useless on a colorless cloud. Not a substitute for ranks 2–5. |
| Ultralytics YOLO v8 / v11 / YOLO-World | 2 | no | Image proposal only. AGPL. See the YOLO section. |
| YOLO3D, BEVFusion | 1 | wrong_modality | Driving bird’s-eye heading, not stud lean. |
| WFC 6D pose (Xie and Alwisy 2026) | 3 | maybe | Right object, wrong scene, code unreleased, published rotation about 1°. Watch. Does not retire rank 1. |
| FoundationPose, SAM-6D, MegaPose | 2 | no | Several degrees on the WFC table. RGB-D pose, not a wall. |
| Lee et al. 2024 light-steel net | 2 | maybe | Label names match a wall schedule. Member is a steel C-channel. No public weights. |
| Zhang et al. 2026 RC frames | 3 | maybe | PCA axis is the right angle idea, already in rank 1. Euclidean clustering is a knob, not a new stack. |
| ERES 2026 timber DL | 2 | maybe | No number and no code. Would sit next to rank 4 if weights appear. |
| GrowSP | 2 | no | Unsupervised semantics on indoor/driving sets. |
| CGAL shape detection | 3 | no | Rank 2 again, under GPL. |
| PDAL cluster / DBSCAN | 1 | no | Rank 1’s cluster, in a LAS pipeline. |
| Hough facet split (2020) | 2 | no | Already the spirit of rank 2’s linear split. |
| PCL supervoxels | 2 | maybe | Optional preprocess for rank 2. |
| LAStools, Potree | 1 | no | Interchange and viewing. |
| BIMStruct3D horizontal box | 2 | no | Rank 4’s control network. The box forces level walls. |
| Vuforia, RoomPlan | 1 | no | Tracking and room surfaces. |
| ARCore, Polycam, Scaniverse, StudSpec | 1 | wrong_modality | Depth, capture, or photo language. |
| EdgeWise, Verity, PointCab, FARO, Leica, Canvas, Avvir, Cupix, InfiPoints | 1 | no | Steel, pipes, walls, or scan-versus-model. No bare 2×4 schedule with a lean. |

## Recommended bake-off changes

**Add**

1. **pyRANSAC-3D v0.7.0, sequential cuboid, after rank 1’s plate peel.** Same floor normal, same section prior, same yellow paint. Count merged bays and split studs against rank 1 and, when rank 2 exists, against the region-grow cuboid. Reject the run if the first cuboid swallows the wall; that result is a log, not a failure of the scorecard.
2. **SAM 2 (Apache-2.0 checkpoints), only on a capture that already has a registered image.** Prompt or a prior box, lift the mask to points, then the shared box. Compare instance precision and recall with rank 1. Do not train. Do not add a second image model (YOLO) unless SAM 2 fails to separate a bay that the photo clearly separates. Ultralytics YOLO stays off the engineering dependency list unless we accept AGPL or buy Enterprise.

**Do not add a third.** The WFC pose fitter, the light-steel network, ERES 2026, and a ScanNet instance transformer (Mask3D or OneFormer3D as a later rank 4 head) each fail at least one of: public code, a wood 2×4, a free long axis, or a scene that is a wall. Primary pages for Mask3D and OneFormer3D were **not** opened this pass; they are named only so a future label round does not assume PointGroup is the only instance head. No stud checkpoint was found for them in this search.

**Drop nothing.** Rank 3 stays. Rank 5 stays as the office-class control. EdgeWise stays out until a current vendor page names light-frame studs and a lean, which this pass did not find.

## Threats to validity

This pass did **not**:

- Run any segmenter, fitter, or network, including pyRANSAC-3D and SAM 2.
- Download the WFC archive (10.65 GB plus result zips), any checkpoint, the ENDUROFRAME scans, or a commercial trial.
- Read the paywalled full text of Xie and Alwisy 2026. Rotation and ADD-S figures are from the dataset README, which the authors present as the paper’s benchmark tables.
- Treat LinkedIn claims (grasp rate, “99.82% geometric accuracy”, a 6.1× factor) as measurements.
- Re-fetch the live EdgeWise, PointCab, Verity, or CloudWorx price pages. EdgeWise “wood” is from a 2018 brochure, not from the 2026-09-24 product-page reading in doc 11.
- Open the ERES 2026 PDF. The record URL returned a bot check on direct fetch.
- Extract author names or the full text of the panelized-framing article. The 99.7% and 1 mm figures are the abstract text returned for that URL.
- Confirm the WFC dataset license (the README heading was empty).
- Confirm GrowSP’s LICENSE file, the CGAL 6.x Shape Detection header, or a GeometryFactory quote.
- Confirm Scaniverse LAS export. The page that lists LAS is a staging host and disagrees with the 2026 Niantic pricing page.
- Test YOLO-World, RoomPlan, or StudSpec on a stud wall. StudSpec’s geometry is whatever the sample JSON shows, which is strings, not a box.
- Claim that rank 1 beats any of these methods. Synthetic Open3D numbers in doc 13 measure the generator.

A method can move to `beat_shortlist` only after it and rank 1 are scored on the same bare-frame cloud, with instance precision and recall and angle error against the same reference. Until the device band exists, that comparison still paints yellow.

## Sources

- Shortlist and tolerance: [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md), [02-software-segmentation-angles.md](02-software-segmentation-angles.md), [../tolerances.md](../tolerances.md)
- pyRANSAC-3D: https://pypi.org/project/pyransac3d/ — https://github.com/leomariga/pyRANSAC-3D/releases/tag/v0.7.0 — https://leomariga.github.io/pyRANSAC-3D/api-documentation/cuboid/ — https://doi.org/10.5281/zenodo.7212567
- SAM 2: https://github.com/facebookresearch/sam2/
- Ultralytics license and YOLO11: https://www.ultralytics.com/license — https://docs.ultralytics.com/models/yolo11
- YOLO3D: https://openaccess.thecvf.com/content_ECCVW_2018/papers/11131/Ali_YOLO3D_End-to-end_real-time_3D_Oriented_Object_Bounding_Box_Detection_from_ECCVW_2018_paper.pdf
- BEVFusion: https://arxiv.org/pdf/2205.13542
- WFC: https://github.com/yigediao/wfcdataset — https://doi.org/10.1016/j.autcon.2026.106858
- Panelized framing abstract: https://journalofindustrializedconstruction.com/index.php/jic/article/view/341
- WDNET-YOLO: https://doi.org/10.3390/buildings15132281
- ISARC 2025 timber defects: https://doi.org/10.22260/isarc2025/0179
- HBIM YOLO: https://doi.org/10.1038/s40494-025-02151-6
- Vuforia: https://developer.vuforia.com/library/vuforia-engine/images-and-objects/model-targets/model-targets-api-overview/ — https://developer.vuforia.com/library/vuforia-engine/FAQ/pricing-and-licensing-options/ — https://www.ptc.com/en/products/vuforia/vuforia-engine/pricing — https://developer.vuforia.com/references/native/group__ModelTargetObserverGroup.html
- RoomPlan: https://developer.apple.com/videos/play/wwdc2022/10127/ — https://machinelearning.apple.com/research/roomplan
- ARCore Raw Depth: https://developers.google.com/ar/develop/java/depth/raw-depth
- Scaniverse pricing and API reply: https://www.nianticspatial.com/en/pricing — https://community.nianticspatial.com/t/not-able-to-locate-scaniverse-api-documentation-to-integrate-it-in-project/5795
- StudSpec sample payloads: https://developers.studspec.ai/docs
- CGAL: https://doc.cgal.org/latest/Shape_detection/index.html — https://doc.cgal.org/5.2.3/Shape_detection/group__PkgShapeDetectionRef.html — https://www.cgal.org/license.html
- PDAL: https://pdal.io/en/stable/stages/filters.dbscan.html — https://pdal.io/en/stable/stages/filters.cluster.html
- GrowSP: https://github.com/vLAR-group/GrowSP — https://arxiv.org/abs/2305.16404
- Murtiyoso and Grussenmeyer 2020: https://doi.org/10.3390/s20082161
- Lee et al. 2024: https://doi.org/10.3390/buildings14040952
- Zhang et al. 2026: https://www.mdpi.com/2079-9292/15/2/293
- ERES 2026 record: https://eres.architexturez.net/doc/oai-eres-id-eres2026-160
- BIMStruct3D horizontal box: https://arxiv.org/pdf/2604.24311
- Cyclone 3DR AI: https://leica-geosystems.com/products/laser-scanners/software/leica-cyclone/leica-cyclone-3dr/ai-classification-in-leica-cyclone-3dr-pt1
- Canvas: https://support.canvas.io/article/12-what-is-scan-to-cad
- Avvir: https://www.avvir.io/
- InfiPoints: https://www.elysium-global.com/en/product/infipoints/
