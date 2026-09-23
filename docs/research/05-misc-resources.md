# Misc resources

Links that do not belong in the four tables, plus brief items the research pass could not verify. Same status words as [README.md](README.md).

## Representation: cloud vs splat vs mesh

| ID | Item | Why it matters here | Status |
| --- | --- | --- | --- |
| M1 | 3D Gaussian Splatting (Kerbl et al., SIGGRAPH 2023 / ACM TOG) | Radiance-field view synthesis from photos. Real-time novel views. The representation is anisotropic Gaussians, not a surveyed point with a range residual. **Do not fit stud OBBs to splat centers.** Official page: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/ — Code: https://github.com/graphdeco-inria/gaussian-splatting — arXiv: https://arxiv.org/abs/2308.04079 | `surveyed` |
| M2 | Unity and Unreal splat viewers | Listed in Table 2 (W20, W24). They render M1. They do not add a plumb measurement. | `surveyed` |
| M3 | iTwin RealityData type `GS_3DT` | CesiumJS PR adds Gaussian Splat OGC 3D Tiles as an iTwin RealityData type so a splat tileset can stream like other reality data. https://github.com/CesiumGS/cesium/pull/13208 — This is the “RealityData” hit found for the brief. It is **not** a scan-to-CAD LinkedIn post, and it is not a stud fitter. | `surveyed` |
| M4 | BrepGaussian (CVPR 2026) | Research: multi-view images → 2D Gaussian splatting → sampled points → primitive CAD. Shows the long road from splats to B-rep. Not a tool we can run on a frame cloud today. https://openaccess.thecvf.com/content/CVPR2026/papers/Yu_BrepGaussian_CAD_reconstruction_from_Multi-View_Images_with_Gaussian_Splatting_CVPR_2026_paper.pdf | `surveyed` |

## Courses and methods

| ID | Item | Note | Status |
| --- | --- | --- | --- |
| M5 | MIT 16.485 VNAV | Visual navigation for autonomous vehicles: geometry, optimization, VIO, dense fusion. Course home: https://vnav.mit.edu/ — Lecture 25 (Fall 2020 OCW) covers multi-view stereo and dense fusion (KinectFusion, Voxblox, Kimera): https://ocw.mit.edu/courses/16-485-visual-navigation-for-autonomous-vehicles-vnav-fall-2020/1b66e60e1f3a952f2530af013c3135b0_MIT16_485F20_lec25.pdf — Background for Aura-class tracking. Not a stud-QA course. | `surveyed` |
| M6 | Aerial / large-scale open-source segmenters | These classify **aerial** LiDAR (ground, vegetation, building, wires), which is the bias the brief warned about. Do not fine-tune them on studs and expect walls. Aerial LiDAR Classifier (QGIS, 3D SegFormer, ASPRS codes; weights CC BY-NC 4.0): https://github.com/akharroubi/AerialLidarClassifier — OpenPointClass: https://github.com/uav4geo/OpenPointClass — Myria3D (French Lidar HD): https://github.com/IGNF/myria3d | `surveyed` |

## Brief links that did not open or did not match the expected post

| ID | URL or name | What happened | Status |
| --- | --- | --- | --- |
| M7 | https://youtu.be/Sj3eCphnDX0 | Not returned by search and not fetched as a watch page. The brief says it is an open-source point-cloud semantic-segmentation video with an **aerial bias**. Treat that description as the author’s note. Related aerial tools are M6. A different indoor video that *was* found (SAM + CLIP + DINO, human-in-the-loop, not aerial) is https://www.youtube.com/watch?v=_p_zwjqvI_k — it is **not** claimed to be this ID. | `unverified` |
| M8 | https://share.gemini.google/0FEuisJUh7DE and https://share.gemini.google/5MzElLQcDxFc | Fetch returned **403**. Polycam claims in Table 1 were checked on learn.poly.cam instead. Do not cite the Gemini shares as sources. | `unverified` |
| M9 | LinkedIn: “Javier Medel DeepMind/MIT” | Posts under Javier Medel, MSc, were found (Gaussian-splat uncertainty, NVIDIA/University of Toronto reconstruction). Profile snippet in search results places him in the Toronto area in industry roles. **No DeepMind or MIT affiliation was verified.** Do not use that affiliation. Example post: https://www.linkedin.com/posts/javier-medel_eccv2026-activity-7475720674817540096-o_qj | `unverified` affiliation; posts `surveyed` as existing |
| M10 | LinkedIn: “Yoshi Gaussian splatting” | No unique public post matched this name in search. | `unverified` |
| M11 | LinkedIn: “RealityData scan-to-CAD AI” | No LinkedIn post retrieved. The engineering hit is M3 (iTwin RealityData gaussian tiles), which is streaming, not scan-to-CAD. | `unverified` |

## Format cheat sheet (already known, re-checked)

| Format | Use here | Evidence | Status |
| --- | --- | --- | --- |
| PLY | Default file for Open3D and for Polycam → Python. | Open3D file I/O table includes `ply`. Polycam documents PLY as a colored point-cloud export. | `known; surveyed` |
| LAS / LAZ | CAD, BIM, CloudCompare, ReCap, Unreal’s LiDAR plugin. | Polycam LAS notes; CloudCompare and Leica sample libraries. Open3D does **not** list LAS. | `known; surveyed` |
| E57 | Scanner interchange (Leica, Unity Asset Transformer, Unreal). | Vendor pages in Table 2. | `surveyed` |
| RCP/RCS | Revit / Navisworks via ReCap. | Autodesk path assumed by CloudWorx and As-Built docs. | `surveyed` |
| Gaussian PLY / SPZ | Viz only. | Kerbl repo and Unity splat readers. | `surveyed` |
| Mesh (OBJ, GLB, USDZ) | Engines and sharing. Polycam Basic tier. | Polycam export matrix. Avoid as the ML input if the goal is points on stud faces. | `known; surveyed` |
| PSY | Not a format. | No vendor page uses it. | `known` |

## Prior internal work (not re-executed)

| Item | Status |
| --- | --- |
| Origin agents `bc-d567e2f1` and `bc-c355a90c` finished a dataset-hook and segmentation/angle sketch. `bc-63a01dad` failed on Origin auth. Source: root README. Transcripts were not pulled in this pass. | `known; not-in-repo` |
| openWall Unity / MultiSet product repo is separate: https://github.com/ozguvenc2/openWall | `known; separate-track` |
