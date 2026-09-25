# Stud segmentation algorithm ranking

Research date: **2026-09-24**. This note ranks segmenters for the OpenWall residential XR path under the assumptions below. It refines [02-software-segmentation-angles.md](02-software-segmentation-angles.md), [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md), and the unmerged draft notes on classical Open3D (PR [#5](https://github.com/ozguvenc2/openwall-stud-frame/pull/5)), timber labels (PR [#4](https://github.com/ozguvenc2/openwall-stud-frame/pull/4)), and the IntCDC paint trial (PR [#7](https://github.com/ozguvenc2/openwall-stud-frame/pull/7)). It does not replace the gravity-up stack in doc 02. Floor-as-reference here is a **temporary product choice**, not a claim that a floor is plumb.

Machine-readable twin: [11-stud-segmentation-algorithm-ranking.json](11-stud-segmentation-algorithm-ranking.json).

File-number note: unmerged PR [#6](https://github.com/ozguvenc2/openwall-stud-frame/pull/6) also uses a `11-*.md` name (`11-residential-light-frame-scans.md`) on another branch. These are different documents. One of them should be renumbered if both land on `main`.

The stage ladder, capture protocol, pass bars, and the runnable synthetic Open3D path are in [12-stud-seg-design-plan.md](12-stud-seg-design-plan.md). This ranking’s order is unchanged. Figures for the five contenders are in [images/algo-contenders/INDEX.md](images/algo-contenders/INDEX.md).

Nothing in this pass was downloaded. No checkpoint, LAS, or PLY was committed.

## Pipeline this ranking serves

1. Input is a **pure wood frame** point cloud: studs, plates, and later beams. No drywall and no sheathing. The LiDAR device is not named yet.
2. First target is **vertical studs only**. Plates and beams stay in the cloud as things to peel or ignore, not as the QA class.
3. Stages, in order: instance-segment each stud, fit a **tight oriented box**, measure that box’s long-axis angle against the **floor** (see below), fold in **device and software error** when Oz supplies it, then paint **green / yellow / red**.
4. Later, a digital level on the same studs becomes the ground truth. Accuracy is computed **per algorithm on the same clouds**. This note does not invent that score.
5. Finished-interior models (ScanNet, S3DIS rooms) and forestry stem tools are the wrong object. They are ranked at the bottom so a published mIoU is not reused as a stud score.

Working tolerance remains the derived **~0.12°** in [../tolerances.md](../tolerances.md): `atan((1/4 inch) / (10 feet)) ≈ 0.1194°`, from the Handbook of Construction Tolerances figure as summarized by WoodWorks (1/4 inch in 10 feet when finishes such as gypsum are used). The 2021 IRC wall chapter does not state a general wood-stud plumb angle, and WoodWorks says the IBC and the AWC NDS do not either. NAHB’s 3/8 inch in 32 inches and the UFGS 1/4 inch in 8 feet are different angles. **0.12° is the working band, not a code clause.**

## Floor now, gravity later

Two different “up” vectors must not be mixed.

| Reference | What it is | What a green stud means |
| --- | --- | --- |
| **Floor normal (this phase)** | RANSAC plane on the slab, or file Z **only if** registration already set Z perpendicular to that floor. Store which one was used. | The stud axis is perpendicular to the **floor**, inside the tolerance, after the device band is applied. |
| **True gravity (later)** | Scanner inclinometer or DAC, or a device IMU. Doc 02 names SCENE (Focus, within ±5°), Cyclone REGISTER 360 level-from-DAC (RTC360 / P-series / C-series), ARKit `WorldAlignment.gravity`, or a static accelerometer. | The stud axis is plumb in the gravity frame. |

A floor is not gravity. A slab can be out of level. A stud that is square to a tilted slab will look green against the floor and out of plumb against gravity. A stud that is gravity-plumb on a tilted slab will look tilted against the floor. Doc 02’s warning still stands: do not **level the cloud onto the floor** and then treat that Z as a plumb measurement. This phase **reports the angle to the floor on purpose**, and the paint must say so.

When the inclinometer or IMU arrives, keep the same stud boxes and replace the reference vector. That is a repaint, not a new segmenter. Phone and scanner tilt error are still unquantified here (doc 01, doc 02).

## Green, yellow, red

Let θ be the angle between the stud’s long axis and the floor normal. θ = 0° means perpendicular to the floor. Let τ be the working tolerance (~0.12°). Let ε be the half-width of the **device plus software** error on θ. Oz will supply ε later. It is **unknown** today.

| Color | Rule | Meaning |
| --- | --- | --- |
| Green | θ + ε ≤ τ | The whole error interval is inside the tolerance. |
| Red | θ − ε > τ | The whole error interval is outside the tolerance. |
| Yellow | The interval overlaps τ, **or ε is unknown** | Do not call pass or fail. |

Until ε exists, the honest paint is **yellow on every stud**. A binary green/red overclaims.

Draft PR #7 (`paint_gravity_deviation.py`) is not this rule. It paints pass / warn / fail with warn = 2 × 0.12° = 0.24°, and it has no device band. That warn stripe is a fixed factor. It is not yellow.

No stack in this table emits ε. EdgeWise SmartSheet RMSE is fit-to-cloud, not an angle band. Verity tolerances are user thresholds against a **model**. We wrap ε ourselves, in the same post-step for every algorithm, so the bake-off compares segmentation and boxes rather than five different paint rules.

## What the IntCDC classical run showed

PR #5 sketches `scripts/classical_segment_obb.py` (voxel, statistical outlier removal, repeated `segment_plane`, `cluster_dbscan`, `get_oriented_bounding_box`, aspect heuristics). PR #7 runs the paint on that JSON. Neither script is on `main` yet. The IntCDC preview is not in git.

Recorded on that preview (runbook on PR #7, 2026-09-24), **not an accuracy**:

| | n |
| --- | ---: |
| Components | 449 |
| Checked (`upright` + `beam_like`) | 99 |
| Pass at 0.12° | 6 |
| Warn at 0.24° | 3 |
| Fail | 90 |
| Skip | 350 |

The paint script’s own failure note, with the tildes it prints: about **12 upright**, about **87 beam-like**, **109 clutter**, about **520k** inlier points. 12 + 87 = 99, which matches the checked count. DaRUS does not document scan Z as gravity. The cloud is heavy timber, not a 2×4 wall (doc 06).

### Wrong / expected / change

| | Wrong (that trial) | Expected on a bare 2×4 wall | Change |
| --- | --- | --- | --- |
| Building | Heavy timber. Members touch at joints. | Exposed studs, plates, open bays. No sheathing. | Accept the trial only as a negative control. Score algorithms on a bare frame. |
| Instances | DBSCAN bridges anything that touches. A wall-plane RANSAC would also glue coplanar stud faces into one plane. | One box per stud. Plates removed as horizontal structure. Bay gap kept. | Peel **near-horizontal** plates only. Do not peel the stud-face plane. Set DBSCAN `eps` below the clear spacing. |
| Reference | File Z, not a measured floor and not gravity. | Angle versus the floor normal, labeled as floor-relative. | Fit the floor. Store its normal. θ = `arccos` of the absolute dot product of the long axis with that normal. |
| Color | 6 / 3 / 90 using a 0.24° warn factor. | Green / yellow / red from ε versus ~0.12°. | Until ε is supplied, force yellow. Do not treat 6-of-99 as a pass rate. |
| Claim | Heuristic labels called a stud schedule. | Instance hit rate and angle error versus a digital level, later, on the same clouds. | No mIoU transfer. No stud accuracy claimed from this trial. |

Open3D 0.20 has no region growing and no separate Euclidean-cluster call (doc 08; `cluster_dbscan` is the density cluster). `detect_planar_patches` returns one box per **face**. PR #5 correctly avoids it for members.

## Top 5 to run on the same clouds

Run these five. Same clouds, same floor normal, same τ, same ε once it exists, same outputs: stud id, tight box, θ, interval, color. Do not download the ~223 GB IntCDC set (doc 06). A local bare-frame scan is the acceptance cloud. One already-local IntCDC preview, if it is on disk, is only the negative control above. WFC-Dataset is one stud and a box check, not a wall.

| Rank | Stack | Why it is in the five |
| --- | --- | --- |
| 1 | Refined Open3D stud prior | The geometry of a bare stud wall is separated vertical sticks once the plates are gone. This is the shortest path to a floor-relative box and a yellow paint. The IntCDC recipe is the thing we change, not the library we drop. |
| 2 | PCL region-grow, then a cuboid (Özkan / Pöchtrager rules) | The timber papers that actually build member cuboids. Use it where DBSCAN splits a stud into faces or merges a stud into a plate. Do **not** add Bassier’s remote coplanar merge: that glues neighboring studs. |
| 3 | CloudCompare RANSAC-SD through CloudComPy | An independent primitive fitter (Schnabel). Planes and cylinders, not a 2×4 instance model. Kept so a second classical library can disagree with ranks 1–2 on the same cloud. |
| 4 | Pointcept PTv3 / PointGroup | The fine-tune path after we label studs on these clouds. The only public construction checkpoint found (BIMStruct3D) has no stud class; run it once as a negative control, not as the model. |
| 5 | Open3D-ML RandLA-Net or KPConv, S3DIS weights | Office “beam” and “column” vocabulary. Run once so the S3DIS mIoU is not mistaken for stud accuracy. Not a production segmenter for this frame. |

Ranks 6–12 in the master table below are not in the original five-stack bake-off.

Bake-off **rank 6** is a later add, not that master-table row. Doc 17 (`17-methods-that-beat-shortlist`, the methods brief on PR #14) names pyRANSAC-3D v0.7.0 sequential cuboid, after rank 1’s plate peel, as an add. Oz approved it. The one-stud run is in [16-one-stud-five-finder-run.md](16-one-stud-five-finder-run.md). The Chen, Jiang, and Xiong 2025 row numbered 6 in the table stays out of the bake-off.

## Master table

Every cell is filled. `unknown` and `n/a` say why. Metrics are from the named source only. A number from S3DIS, ScanNet, a historic roof, or one small timber specimen is **not** a 2×4 stud score.

| Rank | Stack | License | Pricing | Stud instances on a bare 2×4 | Tight OBB | Floor angle then green/yellow/red | Device error | Hardware | Labels? | Wood-stud checkpoint | Cited metrics (benchmark named) | Fit (1–5) | Next experiment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Refined Open3D stud prior | MIT ([Open3D](https://github.com/isl-org/Open3D)) | OSS, no fee | Expected: good **if** plates are peeled and `eps` < bay gap. Unmeasured. IntCDC trial merged joints (449 clusters, not a score). | Yes. `get_oriented_bounding_box` / minimal box. A merged cluster makes a bad box. | Bolt-on. Floor normal, then our ε rule. PR #7 paint is the wrong yellow. | None native. We wrap. ε unknown → all yellow. | CPU. Open3D 0.20 pin. | No | n/a (no network) | None on studs. IntCDC counts above are a trial log, not accuracy. | **5.** Bare studs are separated sticks; this stack already speaks boxes and angles. | On one bare-frame cloud: plate peel, DBSCAN, one box per stud, θ vs floor, all yellow until ε exists. |
| 2 | PCL `RegionGrowing` + cuboid, Özkan/Pöchtrager rules, no remote coplanar merge | BSD ([PCL LICENSE](https://raw.githubusercontent.com/PointCloudLibrary/pcl/master/LICENSE.txt)) | OSS, no fee. OPALS (the app Özkan used) price not fetched. | Expected: better on broken faces and joints; risk of merging studs if coplanar patches are joined. Unmeasured on 2×4. | Yes, as a fitted cuboid (the papers’ output), then the same Open3D box if we want one schema. | Bolt-on, same θ and ε wrap. The papers do not paint plumb. | None native. We wrap. | CPU. `pcl::RegionGrowing` is a CPU segmentation class. | No | None | Özkan 2022, one historic roof: beam completeness 29% → 63% vs a manual beam count (not studs). Chen 2025, one small timber specimen: dimension relative error within 3%; plane angles within 1°; cylinders **forced** to global Z. | **4.** Right timber-member idea; wrong published object (roofs, one specimen); we must port it. | Port grow + linear split + cuboid. Same cloud as rank 1. Count merged bays and split studs. |
| 3 | CloudCompare RANSAC-SD / CloudComPy | GPL-3.0 (CloudCompare README; CloudComPy CMake header). Cannot ship closed-source linked to it. | OSS, no fee | Weak. Primitives are planes, spheres, cylinders, cones, tori. A 2×4 is not a cylinder. Coplanar stud faces become one plane. | No stud box. We fit our OBB on each primitive’s points. | Bolt-on after that box. | None native. We wrap. | CPU desktop. CloudComPy embeds the plugin. | No | n/a | Schnabel 2007 detects those five primitives. No stud accuracy in that paper. | **3.** Independent check, poor instance model for a rectangular stud. | Run RANSAC-SD on the same cloud. Compare primitive count to rank 1’s stud count. |
| 4 | Pointcept PTv3 / PointGroup; BIMStruct3D weights only as a control | Code MIT. BIMStruct3D **weights** CC BY-NC-SA 4.0. | OSS code, no fee. NC weights block commercial use of that file. | Zero-shot: poor. Classes are walls and columns, not studs. Fine-tune: unknown until we label. | No box head. Cluster a stud class, then Open3D OBB. | Bolt-on after the box. The network does not know 0.12° or ε. | None native. We wrap. | CUDA. Card example: ~8 min for 6.6M points on an RTX 4090 with 10× TTA (BIMStruct3D README). | Yes for a real model. Zero-shot needs none and is the wrong domain. | **None.** Nearest public file is BIMStruct3D: clutter, floor, ceiling, wall, column, door, window, stairs, railing, lights. | No stud metric. S3DIS/ScanNet scores are not copied here. DeKH mIoU was not re-fetched. | **3.** Right stack after labels; wrong stack if we ship ScanNet weights. | Zero-shot BIMStruct3D on one bare frame (expect wall/clutter). Fine-tune only after stud labels on that same cloud. |
| 5 | Open3D-ML RandLA-Net or KPConv | Open3D-ML MIT. Upstream RandLA-Net repo is CC BY-NC-SA 4.0. Confirm the in-tree header before shipping (doc 02). | OSS, no fee for the MIT copy. NC if we use the upstream repo. | Poor. Semantic labels, not instances. Office beam/column, or roads if the outdoor weights are loaded. | No. We would cluster a class and fit a box. The class will not be “stud.” | Bolt-on only after a box we do not trust. | None native. We wrap. | GPU typical for the zoo models. CPU-only runtime not established here. | Pretrained weights exist. They are the wrong classes. Fine-tune would need stud labels we do not have. | **None.** | Model zoo as recorded in doc 08 (2026-09-23; not re-fetched 2026-09-24): RandLA-Net S3DIS mIoU 70.9; KPConv S3DIS TensorFlow 65.0, PyTorch 60.0. **S3DIS rooms, not studs.** | **2.** Run once to retire the idea. Vocabulary collision is not a stud model. | One forward pass on the same cloud. Record the label histogram. Do not paint green/red from it. |
| 6 | Chen, Jiang, Xiong 2025 region-grow FE | Paper CC BY 4.0. **No public code found** this pass. | n/a (method only) | Unknown on 2×4. Their case is one small timber structure (114,854 points), not a stud wall. | Hexahedra from planes, but cylinders are forced to axis (0,0,1). That is not a measured lean. | **Cannot** as published: vertical members are assumed plumb in global Z. | None. Scanner spec in the paper is not ε. | CPU in their case (laptop i7, ~9.75 s). | No | None | Their specimen: dimension relative error within 3%; absolute plane-to-horizontal/vertical error within 1°. Not a stud-plumb RMSE. | **2.** Useful grow recipe, already covered by rank 2, and it erases the angle we need. | Do not reimplement separately. Steal the “do not force Z” lesson into rank 2. |
| 7 | ClearEdge3D EdgeWise | Commercial | Lite **USD 1,995 / year** on the product page (fetched 2026-09-24). Pro price **unknown** (not on that page). | Not expected. Page names piping, structure, ducts, walls, conduit, cable trays, and structural **steel**. Wood studs are not named. Pro “automated wall extraction” is a wall, not a stud schedule. | Vendor fits spec geometry, not our stud OBB. | No floor-angle paint found. SmartSheet has coverage, spec, length, RMSE (fit-to-cloud). | RMSE is not ε on θ. We would still wrap, if we had studs. | Desktop. CPU vs GPU **unknown**. | No training by us. Models are the vendor’s. | None | No stud metric. “Up to 73%” is a vendor speed claim, not accuracy. | **1.** Wall and steel extractor. Wrong unit for a bare 2×4. | Not in the bake-off. Revisit only if a vendor page names light-frame studs. |
| 8 | PointCab Origins + 4Revit | Commercial | Shop URLs cited in doc 02 (Core €3,000, 3D €4,900 excl. VAT, 2026-09-23) returned **HTTP 404** on 2026-09-24. Live price **unknown**. | Poor as an automatic segmenter. 4Revit builds a column from picked points. Not a stud instance model. | User-guided column, not an automatic tight stud box. | No gravity or floor-angle command found (doc 02). We would export and wrap. | None found. | Desktop CPU. GPU **unknown**. | No | None | No stud metric found. | **1.** Click path, not a head-to-head algorithm. | Skip until stud automation is documented. |
| 9 | Leica CloudWorx for Revit | Commercial | List price **unknown** this pass. Not taken from a reseller snippet. | Poor. Documented fitters are steel, flanges, pipes, walls, floors, doors, windows (doc 02). Not light-frame studs. | BIM solids from fitters, not a stud OBB of a raw cloud. | No gravity number (doc 02). | None for stud angle. | Desktop plugin. CPU vs GPU **unknown**. | No | None | No stud metric found. | **1.** Steel and pipe. | Skip for raw stud segmentation. |
| 10 | Forestry stem tools (cylinder stems) | Varies by tool. Not surveyed tool-by-tool. | unknown | Wrong object. A stem in a canopy is not a 2×4 in a bay. Demoted on purpose. | Often a cylinder, which is the wrong section. | Not a floor-relative stud paint. | unknown | Often CPU. Not confirmed per tool. | Some need plots or allometry, not stud labels. | None for studs | Do not copy forest RMSE or detection rates into this table. | **1.** Domain mismatch. | Do not run. |
| 11 | Finished-interior zero-shot (ScanNet / S3DIS instance nets beyond rank 4–5) | Usually research code; read each LICENSE. Pointcept itself is MIT. | OSS, no fee, unless a weight file is NC. | Wrong scene. Finished rooms, furniture, office structure. A stud wall is not that domain. | No stud head. | Bolt-on would paint nonsense boxes. | None. | CUDA typical. | Weights exist for the benchmark, not for studs. | **None** | Leave ScanNet AP and S3DIS mIoU on those benchmarks. Not recopied. | **1.** Domain shift. | Do not run a second indoor net beyond the rank 5 control. |
| 12 | ClearEdge3D Verity | Commercial | Quote. No public list price on the product page read for doc 02. Still **unknown**. | **Not a segmenter.** Needs an as-built cloud **plus a design model**. | Compares elements already in the model. | Rotation versus the **model**, not versus the floor, unless the model is square to the floor. User tolerances. DPR’s public case used 1 inch on steel beams (doc 02), not 0.12°. | User threshold, not a sensor ε. | Desktop, with Navisworks or Revit. | Needs the model, not point labels. | n/a | No stud-segmentation score. The 1 inch figure is a project tolerance, not wood QA. | **1.** Right only after a stud model exists. Wrong for this stage. | Hold for a later scan-versus-model check. Do not use it to find studs. |

Fit is 1–5 for **this** pipeline (vertical studs → tight box → floor angle → green/yellow/red with a device band). It is not a score of the tool on its own market.

## Rank notes

### 1. Refined Open3D stud prior

Start from the PR #5 script. Change the peel and the cluster, then point the angle at the floor.

1. Voxel downsample and statistical outlier removal, as now.
2. RANSAC the **floor**. Keep its normal as the reference. Do not rotate the cloud onto that plane.
3. Peel other **near-horizontal** planes (top and bottom plates) with a normal close to the floor normal, a small thickness, and a minimum area. Stop. Do not peel a vertical plane: the faces of many studs are coplanar, and one plane would delete the wall.
4. `cluster_dbscan` on what remains. Choose `eps` below the clear gap between studs (a 16 inch bay is on the order of 14 inches of air; the exact gap depends on the lumber). If two studs share one box, lower `eps`. If one stud shatters, the stud is under-sampled or touching something that was not peeled; that is a rank 2 case, not a reason to raise `eps` until bays merge.
5. Keep clusters whose box is a vertical stick (long axis near the floor normal, section near a 2×4). Drop plates that survived and drop clutter.
6. Tight box: `get_oriented_bounding_box`. If the PCA box is unstable on a short stick, try the minimal box. Record `bbox_kind` as PR #5 does.
7. θ against the floor normal. Color with ε. If ε is missing, yellow.

**Why rank 1 after a bad IntCDC run.** The trial failed the way a joint-bridged heavy-timber hall fails. A bare stud wall’s signal is the gap, which that hall does not have. Rank 1 is the corrected recipe. It is still unmeasured. Fit 5 means it is the experiment to run first, not that it has already passed.

### 2. PCL region-grow and a timber cuboid

Özkan et al. (2022) extend Pöchtrager et al.: region growing on beam side faces, split non-linear segments, fit cuboids. On one historic roof, automatic beam completeness against a manual count went from **29%** (Pöchtrager method) to **63%** (Özkan method). With extra manual splits, **75%**. Northern transept: 199 beams counted, 61 / 129 / 150 modeled. Southern transept: 194, 53 / 117 / 146. They also report 1179 cuboid beams from 4758 linear side-face segments on that roof. Those figures are **that roof’s beam count**, not a stud mIoU and not an angle error.

Lin Chen, Liufang Jiang, and Haibei Xiong (2025) use region growing (their case: smoothing threshold 6°, curvature threshold 0.01), then planes and cylinders, on a Leica P40 cloud of 114,854 points. Dimension relative errors were within 3%. Plane angles versus horizontal or vertical were within 1°. A cylinder is **assumed** vertical with axis (0, 0, 1). Copying that assumption would zero the lean this project exists to paint. Their 1° band is also much coarser than 0.12°.

Bassier and colleagues segment slabs, beams, walls, and columns by growing planes and **joining coplanar patches**, including patches separated by occlusions (Sensors 2023; earlier CRF work). That join is correct for a wall surface and wrong for studs in one wall plane. Do not port it into rank 2.

Open3D cannot host this grow as a library call. PCL can: `pcl::RegionGrowing` groups points by normal smoothness. Implement the cuboid and the “no remote coplanar merge” rule ourselves. CGAL also grows regions; its license was **not** re-read this pass, so it is not a separate rank.

OPALS is what the Özkan workflow names for segmentation. It is not an Open3D plugin. Price not fetched. Do not block rank 2 on OPALS.

### 3. CloudCompare RANSAC-SD / CloudComPy

Schnabel, Wahl, and Klein (2007) detect planes, spheres, cylinders, cones, and tori. CloudCompare’s RANSAC Shape Detection plugin is that algorithm. CloudComPy 2.14.beta exposes `computeRANSAC_SD`. License is GPL-3.0 for CloudCompare and for the CloudComPy sources read this pass. Fine for an internal bake-off. Not fine to link into a closed app.

A cylinder on a 2×4 is the wrong section. A plane on a wall face is the failure mode rank 1 refuses. Rank 3 stays in the five because it is a different fitter on the same points, not because we expect it to win.

### 4. Pointcept PTv3 / PointGroup

Pointcept is the maintained training stack (MIT). PointGroup-style instance heads exist in that line; they were trained on indoor benchmarks. No weight file names stud, plate, or 2×4.

BIMStruct3D (Hugging Face `dfki-av/BIMStruct3D-segmentation`) is a PTv3 model, about 46M parameters, PPT-pretrained on Structured3D + ScanNet + S3DIS, fine-tuned on CV4AEC indoor/construction scans. Ten classes, listed in the model card: clutter, floor, ceiling, wall, column, door, window, stairs, railing, lights. No beam, no stud, no plate, no timber. Code MIT. Weights CC BY-NC-SA 4.0. `segment_scan.py` reads LAS/LAZ/PLY. That is the zero-shot control: run it, expect wall or clutter on a stud face, do not paint QA from those labels.

After we label studs on our clouds, fine-tune and **then** fit boxes and θ. Labels are the gate. WFC poses, RefSite3D “target,” and Rohbau3D beam/column names are not that label set (doc 06 and doc 08).

An ERES 2026 abstract (Windapo and others) says they fine-tune PointNet++, GrowSP, RandLA-Net, and SQN on a purpose-built set of 20 timber structures. The abstract does not give mIoU, F1, or a code URL. Not a stack we can run. Not ranked.

### 5. Open3D-ML RandLA-Net / KPConv

The zoo ships semantic weights for SemanticKITTI, Toronto3D, S3DIS, Semantic3D, Paris-Lille-3D, and ScanNet (model zoo; numbers in doc 08). S3DIS includes beam and column as **office** classes. Loading those weights on a bare frame will emit some class id. That id is not a stud. Outdoor weights are a worse mismatch.

Fit 2, and still in the five, because one controlled failure on our cloud is cheaper than a later argument from a 70.9 S3DIS mIoU.

### Commercial scan-to-BIM

EdgeWise, PointCab, and CloudWorx do not document bare wood studs. Verity does not segment; it compares a model. None of them enter the five. EdgeWise Lite’s published price is the only fresh commercial number this pass (USD 1,995 per year). Pro, Verity, CloudWorx, and a live PointCab cart were not available as list prices here.

## Shared post-step (every rank)

Segmentation output → points of one stud → tight OBB → θ versus the stored floor normal → interval with ε → green, yellow, or red. Ranks 1–5 differ in the first arrow only. Reporting S3DIS mIoU, roof-beam completeness, or a 3% dimension error as if it were stud-angle accuracy is out of scope for the bake-off.

Later metric, same clouds, digital level per stud:

- Instance precision and recall (one box per physical stud; a merged bay is a miss).
- Angle error of θ against the level, in degrees.
- Agreement of green/red with the level **after** ε is real. While ε is unknown, this agreement is not computed.

## Sources

- Tolerances and the derived 0.12°: [../tolerances.md](../tolerances.md), WoodWorks summary https://www.woodworks.org/resources/construction-tolerances-for-light-wood-frame-projects/
- Open3D PointCloud API: https://www.open3d.org/docs/latest/python_api/open3d.geometry.PointCloud.html
- Open3D oriented box: https://www.open3d.org/html/python_api/open3d.geometry.OrientedBoundingBox.html
- Open3D license (MIT header cited in doc 02): https://github.com/isl-org/Open3D
- PCL BSD license: https://raw.githubusercontent.com/PointCloudLibrary/pcl/master/LICENSE.txt
- PCL region growing: https://pointclouds.org/documentation/classpcl_1_1_region_growing.html
- Özkan et al. 2022, historic roof, 29% to 63%: https://doi.org/10.3390/jimaging8010010 and https://www.mdpi.com/2313-433X/8/1/10
- Pöchtrager et al. 2018, the Method 1 baseline in that paper: https://doi.org/10.4995/var.2018.8855
- Özkan et al. 2024, completion of roof models, cuboids via the 2022 workflow: https://doi.org/10.3389/fbuil.2024.1368918
- Lin Chen, Liufang Jiang, and Haibei Xiong 2025: https://doi.org/10.3390/buildings15132213
- Bassier et al. 2023, structural classes, coplanar patches: https://doi.org/10.3390/s23041924
- Schnabel, Wahl, Klein 2007: https://doi.org/10.1111/j.1467-8659.2007.01016.x
- CloudCompare GPL note: https://github.com/CloudCompare/CloudCompare
- CloudCompare RANSAC-SD: https://www.cloudcompare.org/doc/wiki/index.php/RANSAC_Shape_Detection_(plugin)
- CloudComPy RANSAC_SD: https://www.simulation.openfields.fr/documentation/CloudComPy/html/RANSAC_SD.html
- Pointcept: https://github.com/Pointcept/Pointcept
- BIMStruct3D model card (classes, MIT code, CC BY-NC-SA weights): https://huggingface.co/dfki-av/BIMStruct3D-segmentation
- Open3D-ML model zoo (S3DIS numbers live in doc 08’s 2026-09-23 reading): https://github.com/isl-org/Open3D-ML/blob/main/model_zoo.md
- RandLA-Net upstream NC license: https://github.com/QingyongHu/RandLA-Net
- EdgeWise editions and Lite price: https://www.clearedge3d.com/products/edgewise/
- Verity (model required): https://www.clearedge3d.com/products/verity/
- Draft scripts and the IntCDC counts: PR https://github.com/ozguvenc2/openwall-stud-frame/pull/5 and https://github.com/ozguvenc2/openwall-stud-frame/pull/7
