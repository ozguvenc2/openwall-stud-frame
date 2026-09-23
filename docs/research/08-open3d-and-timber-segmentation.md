# Open3D segmentation and timber-member labeling

Research date: **2026-09-23**. Scope: what Open3D **0.20.0** and Open3D-ML can segment, what public work exists for wooden structural parts, and whether a 3D LLM can label construction wood today. This note does not replace the gravity-up stack in [02-software-segmentation-angles.md](02-software-segmentation-angles.md) or the dataset ranking in [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md). The IntCDC timber clouds stay the near-term preview. They are not a labeled stud dataset.

Nothing was installed and no checkpoint was downloaded. mIoU figures are copied from the model-zoo page. They are scores on that dataset, not a stud score.

Status words match [README.md](README.md).

## If you only read one section

| Horizon | Do this | Do not do this |
| --- | --- | --- |
| **Near term** | Classical Open3D on one IntCDC LAS preview, after a LAS→PLY conversion. Downsample, drop outliers, peel planes, DBSCAN the remainder, fit an oriented box per cluster. | Treat a cluster id as “stud” or “plate.” The DaRUS record does not ship a class map. |
| **Mid term** | If we label members ourselves, fine-tune a Point Transformer (Pointcept PTv3). The closest public construction checkpoint is BIMStruct3D’s PTv3, and it has no timber class. | Ship S3DIS or ScanNet weights as a stud model. Beam and column there are office structure, not 2×4. |
| **Not available** | — | **No suitable public stud checkpoint** was found. No PointNet++, Pointcept, KPConv, RandLA-Net, or 3D-LLM weight file is trained to name stud, plate, and beam on a residential frame. |

## 1. Open3D 0.20 classical segmentation

This repo pins `open3d==0.20.0` ([requirements.txt](../../requirements.txt)). GitHub published **v0.20.0** on **2026-09-16**. License of the library is MIT. The Python API page used below is the 0.20 docs at https://www.open3d.org/docs/latest/python_api/open3d.geometry.PointCloud.html.

Open3D does **not** implement region growing and does **not** implement PCL-style Euclidean clustering as a separate call. Density clustering is `cluster_dbscan`. Plane extraction is `segment_plane` (one plane, RANSAC) and `detect_planar_patches` (many planes, robust statistics).

| API | What it returns | When to use it on a timber cloud | Where it fails |
| --- | --- | --- | --- |
| `voxel_down_sample` | A coarser cloud. Colors and normals are averaged if present. | First step. An IntCDC building LAS is gigabytes. Algorithms below are not an out-of-core reader. | Too coarse a voxel erases a stud edge. Spacing is a choice we have not measured on these files. |
| `remove_statistical_outlier`, `remove_radius_outlier` | Inlier cloud plus indices. | Spray and isolated returns before clustering. | A thin member can look like an outlier if `nb_neighbors` is large. |
| `estimate_normals` | Writes `normals`. Default search is 30-NN. | Required input for planar patches and for any normal-angle grow we write ourselves. | Normals flip. `orient_normals_to_align_with_direction` can point them at a chosen up axis. That is not a gravity sensor. |
| `segment_plane` | Plane `(a, b, c, d)` and inlier indices. RANSAC. Args: `distance_threshold`, `ransac_n`, `num_iterations`, `probability` (default 0.99999999). | Peel the largest surface (a floor, a wall, a deck) and repeat on the leftover. | Parallel faces of many members fall in one plane. One glulam face can be the largest plane and hide the member. |
| `detect_planar_patches` | A list of oriented boxes. The box Z axis is the patch normal. Defaults include normal-variance 60°, coplanarity 75°, outlier ratio 0.75, 30-NN. | Many faces at once, which is the right unit for a beam side. | A box per **face**, not per member. Joints and warp split one face into several patches. |
| `cluster_dbscan` | An integer label per point. **−1 is noise.** Args: `eps`, `min_points`. Ester et al. 1996, as cited in the docstring. | Separate members that do not touch, after large planes are gone. | `eps` larger than the gap merges two studs. `eps` smaller than the local spacing shatters one stud. A joint merges beam and post. |
| `get_oriented_bounding_box` | One box from the PCA of the convex hull. `robust` defaults to false. | After a cluster is a single member. Long axis versus a supplied up vector is the angle paint in doc 02. | A cluster that is two touching members produces one diagonal box. PCA is unstable on a nearly square section. |
| `get_minimal_oriented_bounding_box` | Minimum-volume box. `robust` defaults to false. | When the PCA box is a poor fit on a short, fat cluster. | Same membership problem. Volume minimization is not a class label. |

There is no `segment_stud`, no class enum, and no pretrained network inside `open3d.geometry.PointCloud`.

A hand-rolled region grow (neighbor search with `KDTreeFlann`, accept a neighbor if the normal angle is small) is what the timber-roof papers do, in other software. Open3D can host that loop. It does not ship it.

### Open3D-ML

Open3D-ML is a separate repository, [isl-org/Open3D-ML](https://github.com/isl-org/Open3D-ML). The `LICENSE` file on `main` is the **MIT** license, copyright 2020. GitHub’s API license field was `NOASSERTION`; the file itself is MIT. Tag **v0.20.0** was published **2026-09-16** (same day as the core library). The repo had **2350** stars on 2026-09-23.

The README says the ML package is inside the Open3D pip wheel from v0.11 onward (`import open3d.ml.torch` or `open3d.ml.tf`). That README’s framework list still says PyTorch 2.0 and TensorFlow 2.13, and it says that from v0.18 the Linux wheel does not ship TensorFlow. The core v0.20 announcement says the build uses PyTorch **2.13** and TensorFlow **2.20**, with TensorFlow ops unavailable on Python 3.14 and compiled TensorFlow ops unsupported on Windows. Those two pages were not reconciled by installing anything. Treat `import open3d.ml.torch` on 0.20.0 as **untested in this repo**.

Semantic-segmentation weights in [model_zoo.md](https://github.com/isl-org/Open3D-ML/blob/main/model_zoo.md), mIoU as printed there. Weight file dates are in the URLs (2020 and 2021). No 2025 or 2026 weight was added to that table.

| Model | Where a weight exists | mIoU on that cell | Timber / stud class |
| --- | --- | --- | --- |
| RandLA-Net (TensorFlow) | SemanticKITTI 53.7, Toronto3D 73.7, S3DIS 70.9, Semantic3D 76.0, Paris-Lille3D 70.0 (starred in the table) | Outdoor driving, outdoor MLS, indoor rooms | No |
| RandLA-Net (PyTorch) | Same datasets: 52.8, 74.0, 70.9, 76.0, 70.0 | Same | No |
| KPConv (TensorFlow) | SemanticKITTI 58.7, Toronto3D 65.6, S3DIS 65.0, Paris-Lille3D 76.7 | Same. No Semantic3D or ScanNet cell | No |
| KPConv (PyTorch) | SemanticKITTI 58.0, Toronto3D 65.6, S3DIS 60.0, Paris-Lille3D 76.7 | S3DIS torch number is 5 points under the TensorFlow cell | No |
| SparseConvUnet | ScanNet only: torch 68, TensorFlow 68.2 | Finished indoor scans | No |
| PointTransformer | S3DIS only: 69.2 in both frameworks | This is the 2021 Point Transformer, not Point Transformer V3 | No |

The prose under that table names KPConv and RandLA-Net only. SparseConvUnet and PointTransformer appear in the table and have weight links. ScanNet cells for RandLA-Net and KPConv are dashes. Object detection (PointPillars on KITTI, Waymo, nuScenes, and others) is a different task and is not a member segmenter.

Upstream licenses that still matter if we leave Open3D-ML: [QingyongHu/RandLA-Net](https://github.com/QingyongHu/RandLA-Net) is CC BY-NC-SA 4.0 (doc 02). An older Open3D release note called the **in-tree** RandLA-Net port MIT. Use the Open3D-ML copy under MIT only after confirming that file’s header; do not assume the upstream non-commercial terms vanished.

### Limits for timber and studs

- The APIs name **geometry** (plane, cluster, box). They do not name stud, plate, beam, or column.
- DBSCAN and RANSAC have no spacing prior. A 16-inch stud bay is something we would code, not something Open3D knows.
- IntCDC clouds are LAS. Open3D’s file I/O table does not read LAS. Convert first (doc 06).
- The DaRUS abstract does not say the scan Z axis is gravity. Angle paint still needs the gravity step in doc 02.
- Open3D-ML weights label roads, rooms, and furniture. Running the S3DIS PointTransformer on a timber hall will emit “beam” and “column” for whatever its indoor model fires on. That word is not a wood-member label.

## 2. Wooden and frame-component segmentation in the wild

People who publish on **wood members** mostly fit cuboids to historic roof beams with region growing, PCA, and RANSAC. People who publish **learning** weights mostly label concrete, masonry, or finished rooms. Residential 2×4 stud segmentation with a public checkpoint was not found.

### Classical pipelines (wood)

| Work | Year | What they segment | Method | Result they publish | Fit for a residential frame |
| --- | --- | --- | --- | --- | --- |
| Pöchtrager, Styhler-Aydın, Hochreiner, Pfeifer, and others, [Digital reconstruction of historic roof structures](https://doi.org/10.4995/var.2018.8855) | 2018 | Side faces of historic roof timbers, then cuboids | Region growing in OPALS. Example settings in the paper: 6° between normals, 0.03 m search radius. Adjacent faces grouped; cuboid fit. | Qualitative. They note one segment can cover several beams when the gap is smooth. | **Maybe** as the algorithm sketch. Historic roofs, not platform frame. Code is not an Open3D script. |
| Özkan, Pfeifer, Styhler-Aydın, Hochreiner, Herbig, Döring-Williams, [Historic Timber Roof Structure Reconstruction](https://www.mdpi.com/2313-433X/8/1/10) | 2022 | Beams in one historic roof, after removing the roof cover | Region growing on normals, then split non-linear segments (2D alpha shape, RANSAC), then cuboids. | Completeness of automatically modeled beams rose from **29% to 63%** against a manual beam count, on that one roof. | **Maybe** for large exposed timbers. Not a stud-wall prior (spacing, plates, king studs). |
| Özkan and colleagues, [Automatic completion of geometric models](https://doi.org/10.3389/fbuil.2024.1368918) | 2024 | Same historic-roof cuboids, plus closing gaps for a structural model | Follows the 2022 cuboid workflow. PCA shape factors, from Pöchtrager, separate linear faces from compact planes. | The page read here describes the pipeline. A new stud mIoU was not in that text. | Same limit: historic roof beams. |

A 2023 unsupervised structural paper (slabs, beams, walls, columns from planar patches and spatial rules) is [Bassier, Vergauwen, and Van Genechten, Sensors](https://doi.org/10.3390/s23041924). The abstract says the test set is existing buildings with occluders, not a wood-frame house. It is the same classical idea (planes, then rules) on generic structure.

### Learning-based and industrial Scan-to-BIM

| Work | Year | Classes | Wood? | Checkpoint |
| --- | --- | --- | --- | --- |
| Perez-Perez, Golparvar-Fard, El-Rayes, [Scan2BIM-NET](https://doi.org/10.1061/(ASCE)CO.1943-7862.0002132) | 2021 | Beam, ceiling, column, floor, pipe, wall. 83 rooms, industrial and commercial. Reported accuracies: beam 82.47%, column 59.31%, average 86.13%. | Not described as timber or studs. | A public weight file was not found in this pass. |
| Campagnolo and others, [BIM-Net++ / HePIC](https://github.com/LTTM/Scan-to-BIM), ICIP 2023 | 2023 | Point-wise labels from existing BIM on two large buildings, then instance extraction. | Not described as timber. | Repo exists. Weights and a timber class were not confirmed on the README section read. |
| CV4AEC Scan-to-BIM challenge, and the KUL/FBK write-up [Saiga1105/Scan-to-BIM-CVPR-2024](https://github.com/Saiga1105/Scan-to-BIM-CVPR-2024) | 2024 | Walls, columns, doors (and the repo text also discusses ceilings and floors for a PTv3 model). Columns were 0.7% of the scene in their table. They report a column detection f1 of 86.1% at 5 cm after adding a 2D detector and a grid prior. | Public buildings. Not a stud wall. | Training is described. A timber checkpoint is not. |
| [BIMStruct3D](https://huggingface.co/dfki-av/BIMStruct3D-segmentation) (Chamseddine and others, EC3 2026; arXiv html [2604.24311](https://arxiv.org/html/2604.24311v1)) | 2026 | **10 classes:** clutter, floor, ceiling, wall, column, door, window, stairs, railing, lights. No beam, no stud, no plate, no timber. | Fine-tuned on CV4AEC indoor/construction scans. Backbone PTv3, about 46M parameters, PPT pretraining on Structured3D + ScanNet + S3DIS. | **Yes, public.** `segment_scan.py` reads LAS/LAZ/PLY. Code MIT. **Weights CC BY-NC-SA 4.0.** Card example: about 8 minutes for 6.6M points on an RTX 4090 with 10× test-time augmentation. |

Industrial steel and pipe fitters (EdgeWise, CloudWorx) are already in doc 02. Their pages name steel, pipe, and walls. They do not name light-frame studs. No timber-CAD product page opened in this pass (hsbCAD, SEMA, cadwork) documents a point-cloud stud segmenter. That absence is “not found,” not a claim that none exists.

### Datasets that actually contain wood or a wood-like label

| Dataset | Wood in the cloud? | Labels a segmenter can train on | Use |
| --- | --- | --- | --- |
| [IntCDC / DaRUS timber scans](https://doi.org/10.18419/DARUS-3304) (D9) | **Yes.** 23 projects, Leica ScanStation P20, measured after assembly. Glulam and timber members; some buildings also have concrete columns. CC BY 4.0. Oz confirmed the preview is usable. | **No class map.** The record adds one example evaluation (2022-KW15, beam axis 4), not per-point stud/plate/beam labels. | Near-term **geometry** experiment. Convert LAS. Do not train a classifier on it until we label it. |
| [WFC-Dataset](https://github.com/yigediao/wfcdataset) (D3) | **Yes.** One 2×4 stud per sample, 288 samples, ZED 2i, PLY. | Manual **6D pose**, not a wall of classes. License on the GitHub heading is empty (doc 06). | Box and pose checks. It cannot teach plate vs stud. |
| [RefSite3D](https://doi.org/10.5281/zenodo.20285732) (D10) | **Partial.** PM2 includes timber elements in a concrete/steel module. A `01_timber_components` split exists. | Scene labels are environment, ground, and target. Not stud, beam, or plate. | Timber-versus-background only, and not a house. |
| [Rohbau3D](https://doi.org/10.1038/s41597-025-05827-7) (D1) | **No.** Shell construction: masonry, concrete, drywall. | 17 foreground classes plus background, plus instances. A third-party list names Beam and Column ([rohbau3d-benchmark](https://github.com/A-SHOJAEI/rohbau3d-benchmark)). Those names were not re-read from the Dataverse metadata in this pass. | Best public **labeled structure** for fine-tuning a shell model. Domain shift onto wood is untested. |
| S3DIS | No. Stanford indoor areas. | 13 classes in the [MMDetection3D S3DIS semantic config](https://mmdetection3d.readthedocs.io/en/v0.18.1/datasets/s3dis_sem_seg.html): ceiling, floor, wall, **beam**, **column**, window, door, table, chair, sofa, bookcase, board, clutter. | The only common checkpoint whose **vocabulary** includes beam and column. The beams are building structure in offices, not 2×4s. |
| ScanNet / ScanNet++ | Finished interiors. | Furniture and room surfaces. ScanNet++ has a large open vocabulary (doc 03), not a stud legend. | Pretraining only. |

### How transferable is the closest checkpoint?

| Checkpoint | Why someone would try it | Why it is not a stud model |
| --- | --- | --- |
| Open3D-ML PointTransformer, S3DIS, mIoU 69.2 | It will output a “beam” and a “column” id. | Trained on indoor RGB rooms. A bare timber hall has different density, color, and member size. The id is not calibrated to glulam or to 2×4. |
| Open3D-ML RandLA-Net or KPConv, S3DIS | Same vocabulary, higher S3DIS mIoU (70.9 and 65.0 / 60.0). | Same domain gap. Outdoor SemanticKITTI weights are a worse mismatch (roads, vegetation). |
| BIMStruct3D PTv3 | Construction scans, runs on LAS, wall/column/door. | No beam and no wood class. Weights are non-commercial. Column may fire on a timber post; a stud wall will mostly look like wall or clutter. That behavior was **not** tested here. |
| Pointcept PTv3 PPT weights (ScanNet, S3DIS, Structured3D) | Strong indoor segmenter, actively maintained (repo pushed **2026-09-11**, **3233** stars, MIT). | No Rohbau config in the README sections read for doc 02, and no timber config found this pass. |
| Scan2BIM-NET reported accuracies | Beam and column numbers exist. | No weight linked. Buildings are industrial/commercial. |

## 3. Non-LLM models and 3D LLMs

### Non-LLM

| Model | Public weights relevant to construction or timber | Maintenance seen this pass | Verdict for OpenWall |
| --- | --- | --- | --- |
| PointNet++ ([charlesq34/pointnet2](https://github.com/charlesq34/pointnet2)) | None for timber. Indoor benchmarks in later reimplementations. | Last push **2022-08-26**. 3709 stars. | Baseline architecture only. Too heavy on a full TLS cloud without sampling (doc 02). |
| Point Transformer (Zhao et al., the Open3D-ML one) | S3DIS 69.2, file dated 2021-09-24 in the URL. | Weight is frozen in the zoo. | Closest **vocabulary** (beam, column). Not transferable as a stud model. |
| Point Transformer V3 / Pointcept | Indoor PPT weights. BIMStruct3D is a CV4AEC fine-tune, not timber. | Pointcept pushed 2026-09-11. | Mid-term training stack once we have labels. |
| PointNeXt ([guochengqian/PointNeXt](https://github.com/guochengqian/PointNeXt)) | S3DIS / ScanNet style. SegPoint’s table lists ScanNet 71.5 and S3DIS 70.5. | Pushed **2026-07-06**. 1077 stars. MIT. | Stronger PointNet++ line. No timber weight found. |
| KPConv ([HuguesTHOMAS/KPConv](https://github.com/HuguesTHOMAS/KPConv), also Open3D-ML) | S3DIS and outdoor sets in the zoo. | Upstream last push **2021-02-23**. 788 stars. MIT. | Use the Open3D-ML copy if we stay in that stack. Not a wood model. |
| RandLA-Net | Large outdoor and S3DIS clouds. | Upstream push **2023-07-11**. 1564 stars. CC BY-NC-SA 4.0. | Can swallow a big cloud. Labels are still the benchmark’s labels. |
| SparseConv / Minkowski (Open3D-ML SparseConvUnet) | ScanNet 68 / 68.2. | Weights dated 2021-05-03 in the URL. | Finished rooms. |

No row above has a stud, plate, or glulam class in the weight file’s label list, except the generic “beam” and “column” of S3DIS and the “column” of BIMStruct3D.

### LLM and multimodal 3D

These models take a cloud (or multi-view images of a cloud) and emit **text**, a box, or a mask for a prompted object. None of the pages below show a residential wood-frame legend.

| Model | What it actually does | Maturity on 2026-09-23 | Usable to label studs today? |
| --- | --- | --- | --- |
| [PointLLM](https://github.com/InternRobotics/PointLLM) (Xu et al., ECCV 2024; V2 noted as TPAMI 2025 on the repo) | Colored **object** clouds → classification and captioning. Training data is Objaverse (660K simple and 70K complex pairs in the README). | 1056 stars. Pushed **2026-05-15**. Online demo closed (repo note 2025-04-21). | **No.** An object caption is not a per-point stud map. |
| [3D-LLM](https://github.com/UMass-Embodied-AGI/3D-LLM) (Hong et al., NeurIPS 2023) | Scene and object clouds → captioning, dense captioning, question answering, task decomposition, grounding, dialogue, navigation. Checkpoints released for ScanQA, SQA3D, and 3DMV-VQA. | 1217 stars. MIT. Pushed **2024-06-06**. | **No.** Answers and boxes on ScanNet-style rooms. Not a frame segmenter. |
| [GPT4Point](https://github.com/Pointcept/GPT4Point) (Qi et al., CVPR 2024) | Object point-text alignment, captioning, and generation. v1.0 note: Cap3D data, OPT 2.7B. | 447 stars. MIT. Pushed **2024-04-27**. | **No.** Object-level. No construction classes. |
| Point-Bind & Point-LLM | Named by PointLLM and GPT4Point as an alignment method that reasons through ImageBind without 3D instruction training. | Not re-audited as a separate repo this pass. | **No** basis to call it a stud segmenter. |
| [SegPoint](https://github.com/heshuting555/SegPoint) (He et al., ECCV 2024) | The one LLM paper here that **does** output point masks: instruction, referring, semantic, and open-vocabulary segmentation. Paper table: ScanNet 74.1, ScanNet200 35.3, S3DIS 72.4. Instruct3D has 2,565 instruction pairs. | Repo has **38** stars, pushed **2024-07-19**, no license field. The README content retrieved is a citation. | **Research only.** Benchmarks are ScanNet and S3DIS. No timber or stud split is stated. Not a tool we can point at an IntCDC LAS this week. |

A prompt such as “segment the studs” is not a capability these pages demonstrate. Open-vocabulary text in SegPoint was evaluated on indoor benchmarks, not on frame-stage wood.

## Recommended path

### Near term — classical Open3D on the IntCDC preview

1. Use a small public file from [DaRUS 10.18419/DARUS-3304](https://doi.org/10.18419/DARUS-3304), for example the timber-column preview already cited in doc 06 (`2020-KW27_additonal`). Do not commit the LAS.
2. Convert LAS to PLY outside Open3D. Keep the original LAS as the coordinate record.
3. In Open3D 0.20: voxel downsample, statistical outlier removal, `estimate_normals`, `detect_planar_patches` **or** repeated `segment_plane`, then `cluster_dbscan` on the non-plane points, then `get_oriented_bounding_box` per cluster.
4. Paint the long-axis angle only after a gravity vector exists (doc 02). The dataset page does not supply that vector.
5. Expect merged joints and split faces. The output is a set of boxes for a human to accept, not a stud schedule.

### Mid term — ML, only after labels exist

1. Label a few IntCDC or self-scanned bays with the classes we care about (stud, plate, beam, column, other). WFC poses and RefSite3D “target” tags are not that label set. Rohbau3D beam/column labels are the best **public** structural supervision and they are not wood.
2. Fine-tune Pointcept PTv3. BIMStruct3D shows that this backbone can be wrapped to read LAS and write a classification field; its class list and CC BY-NC-SA weights are not the ones to ship.
3. Keep the Open3D box-and-angle step after the network. The network does not know 0.12°.

### Explicit gap

**No suitable public stud checkpoint** was found. S3DIS “beam” / “column” and BIMStruct3D “column” are the nearest words in a weight file. They are not a residential frame model, and they were not run on IntCDC in this pass.

## Sources

- Open3D 0.20.0 release: https://github.com/isl-org/Open3D/releases/tag/v0.19.0 is the previous tag; v0.20.0 published 2026-09-16 (GitHub API). Docs: https://www.open3d.org/docs/latest/getting_started.html
- PointCloud API: https://www.open3d.org/docs/latest/python_api/open3d.geometry.PointCloud.html
- Plane and DBSCAN tutorial: https://www.open3d.org/docs/latest/tutorial/geometry/pointcloud.html
- Open3D-ML: https://github.com/isl-org/Open3D-ML — model zoo https://github.com/isl-org/Open3D-ML/blob/main/model_zoo.md — tag v0.20.0 published 2026-09-16 — LICENSE https://raw.githubusercontent.com/isl-org/Open3D-ML/main/LICENSE
- IntCDC data: https://doi.org/10.18419/DARUS-3304
- Özkan et al. 2022: https://www.mdpi.com/2313-433X/8/1/10
- Pöchtrager et al. 2018: https://doi.org/10.4995/var.2018.8855
- Özkan et al. 2024: https://doi.org/10.3389/fbuil.2024.1368918
- Bassier et al. 2023: https://doi.org/10.3390/s23041924
- Scan2BIM-NET: https://doi.org/10.1061/(ASCE)CO.1943-7862.0002132
- HePIC / BIM-Net++: https://github.com/LTTM/Scan-to-BIM
- CV4AEC write-up: https://github.com/Saiga1105/Scan-to-BIM-CVPR-2024
- BIMStruct3D weights: https://huggingface.co/dfki-av/BIMStruct3D-segmentation — paper html https://arxiv.org/html/2604.24311v1
- S3DIS class list (MMDetection3D): https://mmdetection3d.readthedocs.io/en/v0.18.1/datasets/s3dis_sem_seg.html
- Pointcept: https://github.com/Pointcept/Pointcept
- PointNeXt: https://github.com/guochengqian/PointNeXt
- KPConv: https://github.com/HuguesTHOMAS/KPConv
- PointNet++: https://github.com/charlesq34/pointnet2
- RandLA-Net: https://github.com/QingyongHu/RandLA-Net
- PointLLM: https://github.com/InternRobotics/PointLLM
- 3D-LLM: https://github.com/UMass-Embodied-AGI/3D-LLM — paper https://proceedings.neurips.cc/paper_files/paper/2023/hash/413885e70482b95dcbeeddc1daf39177-Abstract-Conference.html
- GPT4Point: https://github.com/Pointcept/GPT4Point
- SegPoint: https://github.com/heshuting555/SegPoint — paper https://arxiv.org/html/2407.13761
