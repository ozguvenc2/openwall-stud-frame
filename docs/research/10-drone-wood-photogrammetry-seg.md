# Drone photogrammetry and wood-member segmentation

Research date: **2026-09-24**. Scope: who captures aerial or drone imagery (or drone lidar), builds a 3D model, and segments wooden parts — framing lumber, structural timber, or forestry wood when that is the public “wooden parts” stack. The target job is still OpenWall residential stud QA. The house in the attached photos is a US platform-frame building at sheathing stage (OSB, open stud bays, porch trusses). That look is described in [11-residential-light-frame-scans.md](11-residential-light-frame-scans.md).

Nothing here was installed. No weight file was downloaded. A pipeline is named only when a page opened in this pass names the software. A product family whose class list was not opened is marked that way.

Status words match [README.md](README.md).

## If you only read one section

A LinkedIn post that is **both** aerial drone photogrammetry **and** segmentation of residential framing members was **not found**. Searches on 2026-09-24 for that combination returned three different things, and they should stay separate:

| What turned up | What it actually segments | 3D member boxes for a stud wall? |
| --- | --- | --- |
| Ultralytics, 25 Dec 2025, “Segment wood stacks with Ultralytics YOLO11” | 2D pixels of lumber in a pile | No. The “get started” link is the generic YOLO segment docs, not a released stud checkpoint. |
| DroneDeploy Progress AI | 2D jobsite photos (drone or 360). The blog says the model can tell framing from drywall. | No. Trade-level progress, closed weights. |
| Papers that do name a 3D pipeline | One lab glulam strip, railroad crossties, a heritage roof, or trees | No public stud/plate/OSB model. |

The 3D pipelines that were read use **Agisoft Metashape** (or a terrestrial scanner) and then **CloudCompare**, **PyVista**, **PointNet++**, or a Grasshopper cluster. Forestry substitutes (**FOR-instance**, **ForestFormer3D**, **3DFin**, **FSCT**, **OpenPointClass**) segment stems and crowns. They are open. They are the wrong object.

## LinkedIn

| Post | Date on the page | URL | Pipeline the post itself names | Open or closed | What this pass checked |
| --- | --- | --- | --- | --- | --- |
| Ultralytics, “Segment wood stacks with Ultralytics YOLO11” | 2025-12-25 | https://www.linkedin.com/posts/ultralytics_segment-wood-stacks-with-ultralytics-yolo11-activity-7409992609579945984-RfVd | YOLO11 instance segmentation of overlapping wooden pieces, for inspection, sorting, and robotic picking. The post’s link `https://bit.ly/49E5rza` redirects to https://docs.ultralytics.com/tasks/segment/ | Code: [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) is **AGPL-3.0** (LICENSE fetched 2026-09-24). Ultralytics HUB training is a hosted product. | The segment docs page is the generic task page. It does not publish a wood-stack weight file. COCO-pretrained `yolo11*-seg.pt` names are in the YOLO11 README. Those weights are not a framing model. |

Searches that did **not** return a post to cite: “aerial drone photogrammetry segmentation wooden parts timber construction,” and the same idea with “studs” or “light-frame.” Earlier unverified LinkedIn notes in [05-misc-resources.md](05-misc-resources.md) (M9–M11) are Gaussian-splat and RealityData threads. They are not this wood-member post. Do not treat a missing post as a product.

## Pipelines that put a drone (or a flight-configured camera) on wood

| ID | Who / paper | Year | Capture | Reconstruction | Segmentation | Weights or code public? | Fit for a US stud wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Ortiz-Sanz, Bastos, Gil-Docampo. [Deformation of a twisted timber beam](https://doi.org/10.1007/s00107-025-02245-9). Eur. J. Wood Prod. | 2025 | DJI Phantom 4 Pro v2.0, DJI Mavic Mini, and a Canon EOS 2000D, all in a flight-like setup, 1.5 m above one glulam strip (100 × 25 mm, 600 mm). Indoor. | **Agisoft Metashape 1.7.6**. Export PLY (mesh vertices). | Custom **Python 3.9** + **PyVista 0.34.1**. Centroid and rotation per cross-section. Not a learned segmenter. | Scripts are described. A repository URL was not in the article text read here. | Measures one strip to about 0.1 mm / 0.24° in that lab. A sheathing-stage house is a different scene: occluded studs, OSB planes, no targets. |
| A2 | Chen and Guan, Purdue. [Integrating BIM and UAV photogrammetry for 3D segmentation](https://arxiv.org/abs/2510.17609). Also the SHM 2025 PDF at https://www.dpi-proceedings.com/index.php/shm2025/article/download/37359/35933 | 2025 | DJI Mavic 3 Thermal, RTK, S-pattern over a railroad in Indiana. | **Agisoft Metashape Pro** (SfM + MVS). | Manual labels in **CloudCompare**. Train a **PointNet++** variant. Synthetic extras from BIM, also written out through CloudCompare. Reported example: hundred-thousand-point set with BIM augmentation, OA 82.64%, mIoU 0.6920, on rails and wood crossties. | A public weight file or dataset DOI was not in the PDF sections read. PointNet++ code upstream is MIT ([charlesq34/pointnet2](https://github.com/charlesq34/pointnet2)). Metashape is commercial. | Wood crossties are repetitive, separated, and seen from above. Studs in a sheathed wall touch plates and hide behind OSB. Do not transfer the mIoU. |
| A3 | DroneDeploy Progress AI | Product page fetched 2026-09-24 | “Any 360 camera or drone.” | Not described as a survey point cloud. The product returns visual progress reports. | Proprietary “visual intelligence.” Blog, fetched the same day: models “recognize the difference between framing and drywall.” Progress page: installed work across **80+ trade types**, no BIM required. | Closed. No weight download on the product page. | Useful as a photo tag that framing happened. It does not emit a stud OBB or an angle to gravity. |
| A4 | Schependomlaan as-built clouds (dataset, not a segmenter) | Thesis-era; README still up | Drone video of a housing site in Nijmegen, weeks 26–30. Pilot channel linked from the README. | Structure-from-motion by **RAAMAC** (University of Illinois). Software name inside RAAMAC was not in the README. | Comparison of the cloud to IFC in **MATLAB** (RAAMAC). Not a wood-member model. | Academic use, owner permission, stated in the README. The release zip URL returned **HTTP 404** on 2026-09-24. See [11-residential-light-frame-scans.md](11-residential-light-frame-scans.md). | Dutch housing site with prefab, steel, and roofs. Not the OSB house in the photos. |

Pix4D, Epic RealityCapture, Bentley iTwin Capture, and DJI Terra are the other commercial SfM products people fly for construction. This pass did not open a page from any of them that lists a stud, plate, joist, or OSB class. The Pix4D classification article URL returned an empty body. Treat “Pix4D classifies framing lumber” as **unverified**. Prior sensing notes already place Pix4D-class photogrammetry in Table 1 (S4) as a capture method, not a stud segmenter.

## Timber member segmentation that is not a drone flight

These are the stacks a “wood segmentation” search returns next. They are real. They are terrestrial, factory cameras, or a heritage roof.

| ID | Who | Capture | Pipeline as written | Open? | Why it is here |
| --- | --- | --- | --- | --- | --- |
| B1 | eCAADe 2024, Franko-Byzantine timber roof, Cyprus. PDF: https://papers.cumincad.org/data/works/att/ecaade2024_232.pdf | **FARO Focus M70** + **FARO SCENE**. Separate photogrammetry in **Agisoft Metashape** (Feb 2024). Not a drone. | Align in **CloudCompare** (7 picked points, RMS 0.0073 on that alignment). Segment with **Cockroach** `CloudClusterCilantro` in Grasshopper (Cilantro). IFC via VisualARQ. Pathology height map back in CloudCompare. | [petrasvestartas/Cockroach](https://github.com/petrasvestartas/Cockroach) is **LGPL-3.0**, 0 stars, last push **2021-11-26**. Rhino and Metashape are commercial. CloudCompare is GPL (doc 02, W2). | The clearest published “photos + TLS → cluster timber sticks” recipe. The building is a church roof, not a platform frame. |
| B2 | [Buildings 2025, geometric FE models from timber clouds](https://doi.org/10.3390/buildings15132213) | **Leica ScanStation P40**. Two stations. Registration in Leica software. Case cloud: 114,854 points. | Downsample and outliers in **Open3D**. Region growing (smoothing 6°, curvature 0.01). RANSAC planes (0.003 m) and lines (0.015 m). APDL out. | Open3D is MIT. The paper’s region-growing script was not linked in the sections read. Leica registration is commercial. | Same classical idea as the Open3D path in doc 08, on a small timber assembly. Not aerial. Not 2×4 walls. |
| B3 | Özkan and colleagues, historic roofs (already in doc 08) | TLS, roof cover removed in software | Region growing, RANSAC, cuboids. Completeness 29% → 63% on one roof (2022). | Methods paper. Not an Open3D package. | Large exposed beams. No stud spacing prior. |
| B4 | University of Alberta, timber stud defects. ISARC PDF: https://www.iaarc.org/publications/fulltext/179_Computer_Vision_based_Automated_Timber_Structural_Defect_Detection_Framework.pdf | Industrial cameras on studs (bends, twists, missing parts). Not a drone. | **YOLOv8** variants. Medium/large reported at high validation precision in the abstract (93.0% and related test figures in that abstract). | A public dataset URL was not in the PDF text read. Ultralytics YOLOv8 code is AGPL-3.0. | 2D boxes on a stud in a factory view. No 3D plumb angle. |
| B5 | University of Alberta, panelized wall QC. https://doi.org/10.29173/ijic341 | Camera on a wood framing machine. | Fine-tuned **YOLOv8s** for stud centers and nailer positions, plus a PLC correction. Abstract: 99.7% defect detection, mean alignment error under 1 mm, on that machine. | Dataset not stated as a public download in the abstract. | In-process 2D QC for panel plants. The photos Oz attached are a site-built house. |

## Forestry and lumber piles (open, wrong object)

Aerial “segmentation of wooden parts” in 2023–2026 is mostly trees, or boards on a truck.

| Piece | What it segments | License / access | Last activity seen | Use on a stud cloud |
| --- | --- | --- | --- | --- |
| [FOR-instance](https://doi.org/10.5281/zenodo.8287792) | UAV lidar (RIEGL). 1,130 trees. Semantic classes include stem, woody branches, live branches, terrain, low vegetation. | **CC BY 4.0**. Zip 1,643,251,814 bytes, listed as 1.6 GB. | Zenodo 27 Aug 2023. Paper: https://arxiv.org/abs/2309.01279 | No. Stems are not studs. |
| [FOR-instanceV2 + ForestFormer3D](https://doi.org/10.5281/zenodo.16742708) | Same task, more forests, plus MLS. ICCV 2025. | Zenodo record license **GPL-3.0-or-later** (dataset and pretrained model on that record). Code page named in the paper: https://bxiang233.github.io/FF3D/ | Zenodo 5 Aug 2025 | No. A GPL forest checkpoint will not name a plate. |
| [3DFin](https://github.com/3DFin/3DFin) | Forest inventory from TLS/UAV lidar (stems). | **GPL-3.0**. 99 stars. Pushed 2025-12-05. | Active | No. |
| [FSCT](https://github.com/SKrisanski/FSCT) | Semantic segmentation of forest TLS (terrain, vegetation, stem, and related structure). | **GPL-3.0**. 183 stars. Pushed 2024-03-03. | Stale relative to 2026 | No. |
| [OpenPointClass](https://github.com/uav4geo/OpenPointClass) | ASPRS-style classes for aerial clouds. Used by OpenDroneMap `pc-classify`. | **AGPL-3.0**. 200 stars. Pushed 2026-06-11. | Active | No. Classes are ground, vegetation, building, not stud. |
| [ODMSemantic3D](https://github.com/OpenDroneMap/ODMSemantic3D) | Photogrammetry clouds labeled for that classifier. Minimum classes: ground (2), low vegetation (3), building (6), human-made object (64). | Repo text: **CC BY-SA 4.0**. 24 stars. | README fetched 2026-09-24 | No. A “building” class is the whole house. |
| 3DMASC (Letard et al., ISPRS 2023, https://doi.org/10.1016/j.isprsjprs.2023.11.022) | Explainable point-cloud classification. A 2025 paper applies it to airborne and Zenmuse L2 drone lidar for ground vs vegetation, then Treeiso for trees. | Paper is the citation. A GitHub license was not confirmed this pass. | Paper 2023; application 2025 | No. |
| Ultralytics wood-stack post (above) | 2D lumber pieces | AGPL code; demo weights not released on the linked docs page | 2025-12-25 | No, unless someone labels wall photos and trains. That training set does not exist in this repo. |

OpenDroneMap itself ([OpenDroneMap/ODM](https://github.com/OpenDroneMap/ODM), AGPL) is OpenSfM + OpenMVS. The sample sets on https://www.opendronemap.org/odm/datasets/ are aukerman, bananas, brighton_beach, seneca, toledo, and a conch shell. None is a framed house.

## Open-source pieces, stated as they are

| Need | What exists | Honest limit |
| --- | --- | --- |
| Drone photos → cloud | WebODM / ODM (AGPL), COLMAP (already W29), Meshroom/AliceVision (not re-read this pass) | A cloud of the **outside** of a sheathed house. Interior studs facing the room are not in a roof flight. |
| Classify that cloud | OpenPointClass (AGPL) into ASPRS codes | Building vs ground. Not stud vs OSB. |
| Cluster sticks | Open3D `cluster_dbscan` + OBB (doc 08 and the classical script on draft PR #5). Cockroach/Cilantro (LGPL, last push 2021) if the cloud is already in Rhino. | Clusters are geometry. The label “stud” is still a heuristic or a hand label. |
| Learned wood in 2D | YOLO11-seg code (AGPL). Train it. | No public framing checkpoint was attached to the LinkedIn post. |
| Learned wood in 3D | PointNet++ code (MIT). ForestFormer3D weights (GPL, trees). | No stud checkpoint. Doc 08 already says this for Pointcept and Open3D-ML. |

## Fit for OpenWall residential stud QA

The photos are a ground-level view of open bays and OSB. A drone orbit of that house would see roof planes, the street elevation of OSB, and the porch truss profile. It would not see the inner face of a stud that is already sheathed, and it would not replace the gravity reference in [02-software-segmentation-angles.md](02-software-segmentation-angles.md).

| Job | Use this | Leave this alone |
| --- | --- | --- |
| Document the exterior at sheathing stage from photos | Metashape, or ODM if the license is acceptable, then a PLY for Open3D | A forestry checkpoint |
| Name studs, plates, and OSB | Still unsolved in public weights. Classical Open3D on a **ground** cloud, or a model we train | DroneDeploy’s “framing” trade tag, YOLO11 COCO weights, ForestFormer3D |
| Angle versus gravity | Open3D after a real up vector (doc 02) | The 0.24° lab figure from A1, which is one strip with targets |

A practical photo stack, if a flight is captured later: **Metashape or WebODM → PLY → the Open3D cluster and OBB path**. That is a reconstruction pipeline plus the geometry already planned in this repo. It is not a semantic stud product, and no 2023–2026 vendor page read here sells that product for light-frame houses.
