# Blender and Unity — point-cloud visualization and semantic labels

Research date: **2026-09-23**. Scope: authoring, review, and XR for a residential **frame-stage** cloud (timber, studs, plates, beams), including labeled classes and a red/green angle-versus-gravity paint. This note does not repeat the Open3D measurement stack. That stack stays in [02-software-segmentation-angles.md](02-software-segmentation-angles.md): gravity-up first, then an oriented box and a paint in Python. Blender and Unity **show** that result. They do not replace it.

Nothing here was installed. No Blender binary, Unity editor, or Asset Store package was run. Prices and point-count limits are copied from the page named on the row. A vendor or author demo is marked as such. A page that did not return article text is `unverified`.

Status words match [README.md](README.md).

## If starting this week

| Job | Pick | Why this one | Link |
| --- | --- | --- | --- |
| **Blender viz** | **Point Cloud Visualizer**, Standard, on **Blender 4.5 LTS** | Reads PLY, LAS/LAZ, E57, and PCD into the viewport, shades scalars, and is the add-on the 2024–2026 docs still maintain. Pro tiles are only for a multi-file cloud that does not fit in RAM. | https://superhivemarket.com/products/pcv |
| **Blender seg** | **No segmenter.** Review imported labels in PCV or in **Point Cloud I/O**. Correct a selection with PCV’s set-scalar edit, or with Blender 4.5 **Set Attribute**. | No Blender add-on found that runs PointNet, PointNeXt, Pointcept, or a stud/plate/beam model. Class colors and integer fields round-trip; the network stays in Python. | https://extensions.blender.org/add-ons/point-cloud-io/ |
| **Unity viz** | **Point Cloud Viewer and Tools 3** | The Asset Store package that is still updated in 2026, lists LAS, and is aimed at runtime and VR. Convert binary PLY and LAZ with the external converter. Bake the paint into RGB before import. | https://assetstore.unity.com/packages/tools/utilities/point-cloud-viewer-and-tools-3-310385 |
| **Unity seg** | **No segmenter.** Show a cloud whose RGB is already the class color or the angle paint. | No Asset Store or GitHub package found that paints semantic classes or runs a point network inside Unity. The Toolkit “segmentation” control splits the cloud into cubes for culling. | https://docs.unity3d.com/Packages/com.unity.industry.toolkit@3.3/manual/import-point-clouds.html |

Gaussian-splat videos from 2024–2026 are real and easy to mistake for a point-cloud workflow. They reconstruct appearance from photos. They are listed below so they are not used as the stud path.

## How the two jobs differ

**Visualize** means load a survey cloud, orbit it, and see RGB or a scalar (class id, intensity, or the Open3D angle paint).

**Semantically segment** means assign each point a class such as stud, plate, or beam. Three different actions get called “segmentation” on these product pages:

| Phrase on a product page | What it actually is |
| --- | --- |
| Blender edit mode, PCV “set color / set scalar” | A person selects points and writes one class value. |
| Point Cloud I/O “classification” attribute | The ASPRS code, or any integer we stored, **read from the file**. |
| Unity Asset Transformer “segmentation” | A grid of cubes so frustum culling can drop hidden cubes. |
| PCV DBSCAN, or a Pointcept run | Clustering or a neural model. DBSCAN is not a stud label. Pointcept is not a Blender node. |

## Blender — visualize

Ranked for a frame-stage cloud (house-scale TLS or a Polycam PLY), not for a country-scale aerial tile.

| Rank | Option | License | Maturity / last activity | Large-cloud limit (as published) | Formats | OpenWall fit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [Point Cloud Visualizer](https://superhivemarket.com/products/pcv) (Jakub Uhlík), Standard | **GPL** (store listing). Store page fetched this pass: Standard **$85**, Pro **$150**. 12 months of updates included; extending updates is 25% of price. | Store: published over 6 years, **2400+** sales, 19 ratings, Blender **4.2–5.2**. Docs title on fetch: **3.12**. | Standard: “hundreds of millions,” limited by system and GPU memory. Docs: the file is loaded into RAM (peak “4 and more” times the runtime use); an **8 GB** GPU calculator example is **~300M** points with the default shader and scalars off. Display percentage can upload a subset. Pro **tiles**: author demo of **1,505,076,907** points in 395 LAZ files on a Mac mini M4 Pro 64 GB, Blender 4.5. That is an author screen capture, not a guarantee. | Read: PLY, LAS/LAZ, E57, PCD, PTS, XYZ, TXT, CSV. Write: PLY, LAS/LAZ, E57, PTS. Also reads 3D Gaussian Splatting PLY. | **Yes** for review and stills of a timber cloud. Keep the survey file as the coordinate record (see interop). |
| 2 | [Point Cloud I/O](https://extensions.blender.org/add-ons/point-cloud-io/) (StudioMedio) | **GPL-3.0-or-later**. Free on Blender Extensions. | Version **0.6.0**, published 28 May 2026, updated **11 Sep 2026**. GitHub [`studiomedio/blender-point-cloud-io`](https://github.com/studiomedio/blender-point-cloud-io): **6** stars, pushed **2026-09-11**. Requires **Blender 5.1+**. | Extension text: “million-point datasets.” No independent count and no out-of-core mode were published. LAS export quantizes positions to **1 mm**. | E57, PLY, LAS/LAZ, PCD, XYZ, PTS, both directions. Native **PointCloud** object, not a mesh. | **Yes** on Blender 5.1+ when the cloud fits in RAM and we need a free round-trip of class attributes. Young project. |
| 3 | Blender **4.5 LTS** Point Cloud object, Geometry Nodes | GPL, same as Blender. | 4.5 LTS manual, current LTS as used in doc 02. | No published scan-size limit. A mesh-vertex import of tens of millions is the workflow in the 2023 Poux video (16 million vertices in that demo). | Built-in PLY import and the 4.5 **Import PLY** node produce a **mesh**. Mesh to Points makes a Point Cloud. **No LAS, LAZ, or E57** in the manual pages read. | **Maybe.** Useful once a cloud is already a Point Cloud. Weak as the importer for scanner files. |
| 4 | Blender **5.3** Point Cloud type `3D Gaussian Splats` | GPL, in the Blender alpha. | [blender.org/releases/blender-5-3](https://www.blender.org/releases/blender-5-3/): expected **10 Nov 2026**. Release notes are for the alpha. PCV’s store text: native splat object “currently requires experimental Blender 5.3 alpha.” | Release notes: “Performance is not ideal.” A secondary article (80 Level, 18 Sep 2026) quotes an earlier design target of 10 million, then 100 million. That target is **not** in the release notes read here. | Import **PLY** (auto-detect splat vs mesh) and **SPZ** through v4. **No export.** | **No** for a survey cloud. Appearance only. |

### Blender add-ons

| Name | Price | What the opened page says | Link |
| --- | --- | --- | --- |
| Point Cloud Visualizer, Standard / Pro | $85 / $150 | Viewport draw, filters, scalar shading, selection edit, PLY/LAS/E57 I/O. Pro adds tiled LOD for many files, measure tools, and a height shader for clouds with no color. | https://superhivemarket.com/products/pcv |
| Point Cloud I/O | Free | Import/export of the six formats above onto a native PointCloud, with color, normals, intensity, ASPRS classification, and other scalars as attributes. | https://extensions.blender.org/add-ons/point-cloud-io/ |
| Point Cloud Wizard for Point Cloud Visualizer | $22 on the Superhive lidar tag | Product page was **not** opened. Capability beyond the title is `unverified`. | https://superhivemarket.com/tags/lidar |
| Pcm_Clean | $40 on the same tag | Same. Title says cleaning and optimization. Page not opened. | https://superhivemarket.com/tags/lidar |
| Laser Scan It | $2.90 on the laser-scan tag | Page not opened. Do not assume LAS import. | https://superhivemarket.com/tags/laser-scan |
| Point Cloud Density Splatter (Punto de Ancla) | **$69.99** on the creator’s Superhive page | Store listing only. A Radiance Fields article describes E57-to-splat conversion; the article URL returned a script shell on fetch, so those format and GPL details stay `unverified`. | https://superhivemarket.com/creators/punto-de-ancla |

PCV’s older GitHub tree [`uhlik/bpy`](https://github.com/uhlik/bpy) (1082 stars, last push **2023-07-04**, no GitHub license field) says the add-ons **in that repository** are unmaintained. The maintained PCV 3.x build is the Superhive extension, not that repo.

### Blender GitHub repos

| Repo | Stars | Last push | License | What it does | Fit |
| --- | --- | --- | --- | --- | --- |
| [studiomedio/blender-point-cloud-io](https://github.com/studiomedio/blender-point-cloud-io) | 6 | 2026-09-11 | GPL-3.0 | The extension above. | Yes, as the free I/O path. |
| [ln-12/blainder-range-scanner](https://github.com/ln-12/blainder-range-scanner) | 164 | 2024-12-29 | GPL-3.0 | Simulates a lidar/sonar in a Blender scene and writes a **labeled** cloud from `categoryID` / `partID` or material names. | Maybe for synthetic training meshes. No on a scanned frame. |
| [neumicha/Blender2Helios](https://github.com/neumicha/Blender2Helios) | 22 | 2025-04-23 | GPL-3.0 | Exports a Blender scene to HELIOS / HELIOS++ and can carry semantic labels from collections. | Same: synthetic only. |
| [uhlik/bpy](https://github.com/uhlik/bpy) | 1082 | 2023-07-04 | not set on the API | Old PCV and other scripts. Upstream says unmaintained. | No. Use the store build. |

### Blender videos and write-ups (2023–2026)

| Title | Channel / place | Date | URL | Technique shown | Use for OpenWall |
| --- | --- | --- | --- | --- | --- |
| 3D Point Clouds in Blender: Starter Guide | Dr. Florent Poux. Write-up on BlenderNation. | BlenderNation post **3 Nov 2023**. Video uses Blender **3.6.4**. | https://www.youtube.com/watch?v=DCkFhHNeSc0 | Stanford PLY (experimental) imports as a **mesh** (demo: 16 million vertices, ~500 MB). Geometry Nodes **Mesh to Points**, Attribute shader on `Col`, **Cycles**. He had already split the cloud into ground, walls, and objects **before** Blender. | The still-valid “PLY → points → colored render” path. The class split happened outside Blender. |
| The Blender Handbook for 3D Point Cloud Visualization and Rendering | Florent Poux, Medium / Towards Data Science. LinkedIn pointer. | LinkedIn post dated **24 Jan 2025** in search. Article body was fetched. | https://medium.com/data-science/the-blender-handbook-for-3d-point-cloud-visualization-and-rendering-1700ebe69c7b | Written, not a new video. Same Geometry Nodes and shader setup, plus storyboarding. | Handbook for the native mesh-to-points look. No LAS, no classes. |
| SkySplat Tutorial: From drone video to photo-realistic 3D scene — Blender Conference 2025 | Blender (official). Speaker Kyle Johnson. | Conference **2025**. Speaker’s Reddit post linking the upload is 18 Sep 2025. | https://www.youtube.com/watch?v=Q5FISs0gkiE | Frames → COLMAP → alignment in Blender → **3D Gaussian splats** with the free SkySplat add-on, inside the viewport. | Splat lookdev from drone video. Not a timber TLS cloud and not a labeler. |
| Converting your 3D Scene into NeRFs & Splats | Colin Behrens, Svenja Strobel. Blender Conference 2024 schedule. | Conference **2024**. Exact day not copied; the schedule page lists the talk. Video page required JavaScript, so the abstract was not read. | Schedule: https://conference.blender.org/2024/schedule/ — video: https://video.blender.org/w/jCxSPPY5L3BCJ4k3sAPiDT | Title is scene-to-NeRF/splat. Treat the technique list as the title only. | Not a survey workflow. |
| Blender 5.3 Got Gaussian Splats! | CGMatter | Cited by 80 Level on **18 Sep 2026**. YouTube oEmbed confirmed the title and channel. Upload timestamp was not in oEmbed. | https://youtu.be/CniycUnvcX4 | 5.3 **alpha**: import a Gaussian PLY, render in EEVEE and Cycles, separate points in Geometry Nodes by the splat `scale` attribute. Transcript: about 600,000 splats in the apple demo. | Shows where Blender is going for splats. Alpha, no export, not metrology. |

### Blender viz — fit

**Yes** for orbiting a stud cloud, checking an imported class color, and rendering a still for a review. PCV is the practical importer on 4.5 LTS. Point Cloud I/O is the practical importer on 5.1+ when we also need to write attributes back out.

**No** as the place that decides plumb. PCV’s height shader colors an axis of the cloud. That axis is gravity only when the file is already Z-up. Doc 02 still owns that paint.

## Blender — semantically segment

| Rank | Option | What it does | Limit | OpenWall fit |
| --- | --- | --- | --- | --- |
| 1 | Import the labels | Point Cloud I/O stores ASPRS **classification** as an integer attribute, plus any other PLY scalar. PCV shows a scalar with a color ramp and can **split an integer scalar into one object per value** (docs: useful after classification or DBSCAN). | Neither tool invents stud / plate / beam ids. ASPRS codes are a lidar convention (ground, building, vegetation), not a framing legend. | **Yes** as the viewer for labels that Pointcept or a hand label already wrote. |
| 2 | Manual class edit | Blender 4.5 manual: Edit Mode → **Point Cloud → Set Attribute** writes one value onto the **selected** points. **Separate** (`P`) makes a new point-cloud object from the selection. PCV: Enable Edit Mode converts points to mesh vertices, then operators **set color or a scalar** on the selection. Filter → Scalars → Remove Value can select an exact value or a range and split those points out. | This is a selection, then one value. A continuous class brush on a point cloud was **not** in the PCV or 4.5 manual pages read. Editing millions of points by hand is the wrong scale for a house. | **Maybe** for fixing a mislabeled stud after a model run, on a cloud that fits in memory. |
| 3 | Synthetic scanners | BLAINDER and Blender2Helios label points from the **mesh objects** in the scene, then simulate a sensor. | They do not classify an imported Focus or Polycam cloud. | **Maybe** later, if we build a stud wall as meshes to mint training pairs. **No** on site scans. |
| 4 | PCV DBSCAN | Docs: clustering via Open3D, result stored as an integer scalar, then split. | PCV’s Blender **5.1** note: Open3D has no official Python 3.13 wheel, so Open3D filters (DBSCAN, outlier removal, point-set registration, estimate normals) **do not run** in that build. They are documented for the 4.5-era bundle. DBSCAN ids are clusters, not stud vs plate. | **No** as a semantic model. Optional coarse grouping on Blender 4.5 only. |

No Blender extension in this pass wraps PointNet, PointNeXt, RandLA-Net, or Pointcept. Those stay in [02-software-segmentation-angles.md](02-software-segmentation-angles.md) (W5–W9).

### Blender seg — fit

**Maybe** for looking at classes and for small manual corrections.

**No** for automatic stud, plate, and beam labels. A framed wall still needs a model trained on frame labels, which we do not have in this repo, or a person painting a small cloud.

## Unity — visualize

Ranked for an XR or desktop review of the same cloud. The separate product repo [openWall](https://github.com/ozguvenc2/openWall) is `separate-track`; this table is about public tools, not that project’s contents.

| Rank | Option | License / price | Maturity / last activity | Large-cloud limit (as published) | Formats | OpenWall fit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [Point Cloud Viewer and Tools 3](https://assetstore.unity.com/packages/tools/utilities/point-cloud-viewer-and-tools-3-310385) (unitycoder) | Commercial Asset Store. Listing fetched this pass: **$110** (tax at checkout; one regional mirror showed €101.21). Standard Unity Asset Store EULA. GitHub viewer repo has **no** SPDX license on the API — do not treat the repo as a free copy of the paid asset. | Store listing: version **3.0.3**, **10 Jun 2026**. Unity 6000.0.66f2, 2022.3.26f1, 2021.3.19f1. URP, HDRP, Built-in. VR. A Unity Discussions post describes a later **v3.04** (classification stats reader, URP as default). The store version field and that post were not reconciled. | No official maximum point count on the store page. A June 2026 thread: in-editor conversion of a **300 million** point PLY “does nothing”; the author said the in-editor converter supports **ASCII PLY** and pointed at the external converter. WebGL, mobile, and standalone VR are **point meshes only**. | **In the editor (store text):** XYZ, XYZRGB, CGO, ASC, CATIA ASC, **PLY ASCII only**, LAS, PTS. **Not** Gaussian splats. **External converter** ([`unitycoder/PointCloudConverter`](https://github.com/unitycoder/PointCloudConverter), 39 stars, pushed **2026-09-08**, SPDX `NOASSERTION`): LAS/LAZ, PLY ascii/binary (“initial”), E57 (“experimental”), out to UCPC v2 and PCROOT v3. | **Yes** for an XR review after conversion, with class or angle colors baked into RGB. Try the external converter before assuming a full TLS fits. |
| 2 | [Asset Transformer Toolkit](https://docs.unity3d.com/Packages/com.unity.industry.toolkit@3.3/manual/import-point-clouds.html) 3.3 (formerly PiXYZ), inside Unity Industry | Commercial. Product page: Toolkit **$1,350 per seat per year**, and “part of Unity Industry.” Industry seat price: **contact sales**. Support article (3 Sep 2024): the separate Toolkit license is no longer sold; Industry includes it. Those two pages disagree on whether $1,350 is still a SKU. | Docs used here: package **3.3.0**. Editor support on the support article: Unity 2022.3 LTS and Unity 6, from Toolkit 3.0. | Import manual: over **100 million** points needs a workstation with at least **32 GB** RAM, or the import may be slow or crash. Density can drop points. LOD from the Model tab. | Import manual: **E57, RCP, PTS, PTX, glTF**. Formats table also lists **PLY** (note 5: mesh or points, use the matching importer). RCP/RCS needs the ReCap SDK, Windows, and an Autodesk ADN account. | **Yes** if an Industry seat already exists and the file is E57 or PTS. **No** as a low-cost viewer. macOS uses the slower `Splats_limited` shader. |
| 3 | [FastPoints](https://github.com/eliasnd/FastPoints) | **GPL-3.0**. | **41** stars, last push **2023-11-21**. Paper: [arXiv:2302.05002](https://arxiv.org/abs/2302.05002). | Built as an out-of-core Potree octree so the cloud can exceed GPU memory. No point-count figure copied from the README. Unity version not stated on the README section read. | Drag-and-drop **PLY, LAS, LAZ**. Potree Converter 2.0. | **Maybe** for a large-cloud prototype. Stale relative to Unity 6. GPL if the plugin is shipped. |
| 4 | [keijiro/Pcx](https://github.com/keijiro/Pcx) | **Unlicense**. | **1517** stars, last push **2022-08-23**. | Mesh path uses Unity’s mesh vertex limits (not restated in the README). ComputeBuffer path is the one meant for bigger sets. No LAS. | PLY. Shaders: point primitives, or disks via a **geometry shader**. | **No** for scanner files. Fine for a small colored PLY demo. |
| 5 | [SFraissTU/BA_PointCloud](https://github.com/SFraissTU/BA_PointCloud) | **BSD-2-Clause**. | **197** stars, last push **2024-08-20**. | Out-of-core Potree loader (dynamic LOD). Upstream README text found in search describes Potree Converter **up to 1.7** (format 1.8). A fork claiming Potree 2 was not reviewed. | Potree folders (`cloud.js`), not a raw LAS drop. | **Maybe** only when a Potree 1.x conversion already exists. |
| 6 | [StoryLab pointcloudrenderer](https://github.com/StoryLab-Research-Institute/pointcloudrenderer) | No license field on the GitHub API. Based on Pcx (Unlicense). | **4** stars, pushed **2026-06-08**. Developed on Unity **2022.3.5f1**, URP 14. | Chunks plus LOD. No count published. Geometry shaders where the platform has them. | **PLY**. | **Maybe** for a modest PLY in VR. Not LAS/E57. |
| 7 | [Point Cloud Free Viewer](https://assetstore.unity.com/packages/tools/utilities/point-cloud-free-viewer-19811) | Asset Store, price free. Code mirror MIT. | Store: version **0.2**, **20 Apr 2018**. Mirror says the code has not been updated since 2014. | Store text: “more than 10 million RGB points.” | **OFF**. | **No.** |
| — | [aras-p/UnityGaussianSplatting](https://github.com/aras-p/UnityGaussianSplatting) | **MIT**. Author: education / toy viz. | **3416** stars, pushed **2025-10-17**. README: Unity **2022.3**, **DX12 or Vulkan**, not DX11. | Author benchmark in the README is a frame-time comparison, not a survey point count. | Gaussian **PLY** and Scaniverse **SPZ**. Not LAS. | **No** for studs. |
| — | [arloopa/UnitySplats](https://github.com/arloopa/UnitySplats) | **MIT**. | **43** stars, pushed **2026-08-18**. | Not a survey-cloud limit. | 3DGS PLY, SOG, SPZ, gaussian GLB. Unity 6, URP/HDRP/Built-in, XR, WebGL 2. | **No** for studs. Active splat viewer if a photo capture is the deliverable. |

The Toolkit display shader is named `Splats` and is a **point** shader (geometry shader, target 4.0). On macOS, WebGL, and visionOS the package swaps in `Splats_limited` (vertex color). That name is not 3D Gaussian Splatting.

### Unity videos (2023–2026)

A Unity talk that imports LAS and segments studs was **not** found. The recent Unity-side videos that search returns are Gaussian splat talks:

| Title | Channel | Date | URL | Technique | Use for OpenWall |
| --- | --- | --- | --- | --- | --- |
| Gaussian Splats — Aras Pranckevičius | Metaverse Standards Forum | **7 Feb 2024** (MSF library and the talk listing). | https://www.youtube.com/watch?v=4E5WqZjzx-g | How Gaussian splats relate to USD/glTF, from the author of the Unity toy viewer. | Context for why splat files showed up in Unity threads. Not a LAS viewer. |
| Gaussian Splatting is pretty cool! (and two follow-ups) | Aras Pranckevičius, blog | 5 Sep 2023, 13 Sep 2023, 27 Sep 2023, plus “Gaussian Explosion” 8 Dec 2023 | https://aras-p.info/blog/2023/09/05/Gaussian-Splatting-is-pretty-cool/ | Blog, not video. Implementation notes for the Unity viewer. README links these. | Same boundary: splat means, not survey points. |

Khronos / MSF town halls in 2025 (“Gaussian Splats: Ready for Standardization?”, SIGGRAPH 2025 and the January 2025 town hall) discuss **file interchange for splats**. They are not construction-QA tutorials. Index: https://metaverse-standards.org/presentations-videos/

### Unity viz — fit

**Yes** for a VR or desktop review of a house cloud that has already been colored, using Point Cloud Viewer and Tools 3 plus the external converter.

**Yes** for E57 inside an existing Unity Industry seat, with the 32 GB / 100-million-point guidance.

**No** for measuring a stud, and no for a Gaussian splat standing in for the cloud. Doc 05 already separates those representations.

## Unity — semantically segment

| Rank | Option | What the page actually says | OpenWall fit |
| --- | --- | --- | --- |
| 1 | Nothing automatic | No Asset Store package and no maintained GitHub repo in this pass runs PointNet, Pointcept, or a stud classifier inside Unity. | **No.** |
| 2 | Show baked colors | PCVT and the Toolkit both display vertex color from the imported file. The Open3D paint (class hue, or red/green against ~0.12°) can be that color. | **Yes** as a viewer of a finished paint. |
| 3 | LAS classification index | Discussions post on PCVT **v3.04**: a classification **stats reader** “allows searching tiles that contain specific classification points,” fed by the external converter. The store page does not document a per-class shader or a paint brush. | **Maybe** later, as a “which tile has class N” index. Not a labeler. `unverified` as a legend shader. |
| 4 | Toolkit segmentation slider | Manual: a value of 10 divides the cloud into at most 10×10×10 GameObjects for **frustum culling**. | **No** for semantics. |

Unity Perception (image labels on rendered frames) was not surveyed. It is not a point-class tool on the pages read for this note.

### Outside both editors

These are not Blender or Unity plugins. They are the closest public **paint** tools found while looking for a class brush:

| Tool | License / activity | What it does | Fit |
| --- | --- | --- | --- |
| [3D-Annotator](https://github.com/3D-Annotator/3D-Annotator) | MIT. 41 stars, pushed **2026-06-02**. | Web app. Point-cloud mode has a **brush**. README: export PNG or their annotation file. A PLY class column round-trip was **not** in the README section read. | Maybe for a labeling trial. Confirm export before depending on it. |
| [augustin-bresset/toaster](https://github.com/augustin-bresset/toaster) | MIT. **0** stars, pushed **2026-08-03**. | Local lidar annotator: classes, brush, and cluster- or model-assisted grouping so one click labels a cluster. | Too new to pick. Worth a look only if we need a brush and Blender’s selection edit is too coarse. |

## Cross-cutting

### Import formats

“Yes” means the **opened** doc or store text names the format. Wiki pages that describe the older DX11 converter are not used as the v3 feature list.

| Format | Open3D (contrast) | Blender 4.5 built-in | Point Cloud I/O (5.1+) | PCV 3.x | Unity PCVT 3 in-editor | PCVT external converter | Asset Transformer 3.3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PLY | Yes | Yes, as a **mesh** (then Mesh to Points) | Yes, as a PointCloud, scalars kept | Yes, including Gaussian PLY | **ASCII only** | Ascii and binary, called “initial” | Yes (mesh or points; pick the importer) |
| LAS | No | No | Yes. Export is LAS 1.2 point format 3, **1 mm** quantization | Yes | Yes | Yes | Not in the import manual list |
| LAZ | No | No | Yes (`lazrs`) | Yes | No | Yes | Not listed |
| E57 | No | No | Yes. Export does **not** write normals | Yes | No | Experimental | Yes |
| PCD | Yes | No | Yes (ASCII, binary, binary_compressed) | Yes | Not in the v3 store sentence. Wiki lists ASCII PCD for the older converter | Not in the converter README lead | Not listed |
| XYZ / TXT / CSV | xyz, pts | No | Yes, column layout inferred | Yes | XYZ, XYZRGB | Not in the lead list | No |
| PTS | pts (Open3D’s pts, not necessarily Leica PTS) | No | Yes (Leica Cyclone text) | Yes (write too) | Yes | Not in the lead list | Yes |
| PTX | No | No | No | No | No | No | Yes |
| RCP / RCS | No | No | No | No | No | No | Yes, with ReCap SDK, Windows, ADN |
| Gaussian PLY / SPZ | Do not use as measurements | 5.3 alpha: PLY and SPZ import, no export | Not the point of this add-on (ordinary PLY) | Yes, Gaussian PLY; can talk to the 5.3 alpha splat object | **Explicitly not supported** | No | No (the `Splats` shader is points) |

Polycam’s point export (LAS, PLY, PTS, XYZ, DXF on Business and Enterprise) is in [01-sensing-modalities.md](01-sensing-modalities.md). PLY is the file Open3D and Blender share without a second library. LAS/LAZ is the file PCV, Point Cloud I/O, and the Unity converter share with CloudCompare.

### Label workflows

1. **Paint classes in a DCC.** Blender can do this at selection scale (Set Attribute, or PCV set-scalar / set-color). Unity, on the pages read, cannot. A house-scale frame is the wrong place to paint every stud by hand.
2. **Import ML labels.** Run Pointcept or a classical cluster in Python (doc 02). Write an integer attribute and/or a color. Point Cloud I/O will carry that integer into Blender and back out to PLY or to a LAS classification byte. For Unity, bake the legend into **RGB** so either viewer shows it without a custom shader.
3. **Splats.** The 2025–2026 Blender Conference and CGMatter videos, and the 2024 Aras talk, are this path. Use them for a photo walkthrough. Do not fit a stud box to Gaussian means, and do not read a Gaussian PLY with a survey importer and expect XYZ+RGB. PCV and Blender 5.3 detect that distinction; a naive PLY reader may not.

Angle-versus-gravity stays a **color or a scalar produced in Open3D** after Z is up. Blender can ramp that scalar. It should not recompute plumb from a floor plane (doc 02).

### Interop with Python + Open3D

| Step | File | Notes |
| --- | --- | --- |
| Measure and paint | Open3D PLY | `ply` with positions, colors, optional normals. Open3D’s file table still has **no LAS/LAZ**. The angle paint is RGB (and, if we add it, a scalar column). |
| Look in Blender 4.5 | Same PLY via PCV, or mesh import + Mesh to Points | PCV does not store the points inside the blend file unless **Pack** is used. Pack converts to a hidden mesh and the FAQ warns that Blender’s float32 vertices **drop geolocated precision**. Leave Pack off when the LAS must round-trip. |
| Look in Blender 5.1+ | Point Cloud I/O | Classification and custom scalars survive. Export can point a LAS classification channel at any integer attribute, including one Geometry Nodes created (0.6.0 notes). |
| Write LAS for Unity or CloudCompare | Point Cloud I/O or PCV, not Open3D | Remember the **1 mm** LAS scale on Point Cloud I/O export. For a stud tip budget on the order of a few millimetres, do not replace the survey coordinates with that export. Write a **sidecar** (class id, paint color) or export a copy used only for viewing. |
| Unity runtime | External converter → PCROOT, then PCVT 3 | ASCII PLY can skip the converter and will choke on a large or binary scan. E57 in that converter is marked experimental. |
| Industry Unity | E57 or PTS directly into the Toolkit | Spatial “segmentation” is for culling. Colors come from the file. |

OBJ is a mesh. Exporting a stud cloud to OBJ triangulates or drops the point representation. Use it only when a downstream tool cannot read points. The ML input should stay a point file.

## What this pass did not find

- A Blender or Unity control that estimates gravity or paints stud plumb.
- A maintained Unity package that segments a point cloud.
- A Blender class **brush** (stroke painting). Selection plus Set Attribute is the documented edit.
- Opened product pages for Point Cloud Wizard, Pcm_Clean, and Laser Scan It. Prices on tag pages only.
- A primary-page reading of the Radiance Fields PCD Splatter article (fetch returned a script shell).
- A tested point count for our own frame clouds inside either editor. The numbers above are the vendors’ numbers.

## Sources

- Point Cloud Visualizer store: https://superhivemarket.com/products/pcv
- PCV docs (intro, large data, edit, scalars, colors, tiles): https://jakubuhlik.com/docs/pcv/ — https://jakubuhlik.com/docs/pcv/datasets.html — https://jakubuhlik.com/docs/pcv/edit.html — https://jakubuhlik.com/docs/pcv/scalars.html — https://jakubuhlik.com/docs/pcv/pro_tiles.html — https://jakubuhlik.com/docs/pcv/installation.html
- Point Cloud I/O: https://extensions.blender.org/add-ons/point-cloud-io/ and https://github.com/studiomedio/blender-point-cloud-io
- Blender 4.5 point cloud: https://docs.blender.org/manual/en/4.5/modeling/point_cloud/index.html and https://docs.blender.org/manual/en/4.5/modeling/point_cloud/editing.html
- Blender 4.5 Import PLY (mesh): https://docs.blender.org/manual/en/4.5/modeling/geometry_nodes/input/import/ply.html
- Blender 5.3 schedule: https://www.blender.org/releases/blender-5-3/
- Blender 5.3 Gaussian splat notes: https://developer.blender.org/docs/release_notes/5.3/rendering/
- Florent Poux video: https://www.youtube.com/watch?v=DCkFhHNeSc0 — BlenderNation: https://www.blendernation.com/2023/11/03/3d-point-clouds-in-blender-starter-guide/
- Florent Poux handbook: https://medium.com/data-science/the-blender-handbook-for-3d-point-cloud-visualization-and-rendering-1700ebe69c7b
- SkySplat, Blender Conference 2025: https://www.youtube.com/watch?v=Q5FISs0gkiE — https://conference.blender.org/2025/presentations/3999/
- Blender Conference 2024 schedule (NeRF/splat talk): https://conference.blender.org/2024/schedule/
- CGMatter, Blender 5.3 splats: https://youtu.be/CniycUnvcX4 — 80 Level citation: https://80.lv/articles/blender-5-3-is-getting-native-3d-gaussian-splat-support
- BLAINDER: https://github.com/ln-12/blainder-range-scanner
- Blender2Helios: https://github.com/neumicha/Blender2Helios
- Point Cloud Viewer and Tools 3: https://assetstore.unity.com/packages/tools/utilities/point-cloud-viewer-and-tools-3-310385
- PCVT discussions (v3.04 notes and the 300M PLY report): https://discussions.unity.com/t/released-point-cloud-viewer-tools/534863/994
- PCVT formats wiki (older in-editor converter; not the v3 store list): https://github.com/unitycoder/UnityPointCloudViewer/wiki/Import-Formats
- PointCloudConverter: https://github.com/unitycoder/PointCloudConverter
- Asset Transformer import: https://docs.unity3d.com/Packages/com.unity.industry.toolkit@3.3/manual/import-point-clouds.html
- Asset Transformer formats: https://docs.unity3d.com/Packages/com.unity.industry.toolkit@3.3/manual/supported-formats.html
- Toolkit in Industry: https://unity.com/products/unity-asset-transformer and https://support.unity.com/hc/en-us/articles/31818343083924-How-can-I-use-my-Asset-Transformer-Toolkit-as-a-Unity-Industry-subscriber
- FastPoints: https://github.com/eliasnd/FastPoints
- Pcx: https://github.com/keijiro/Pcx
- BA_PointCloud: https://github.com/SFraissTU/BA_PointCloud
- Unity Gaussian splatting: https://github.com/aras-p/UnityGaussianSplatting and https://github.com/arloopa/UnitySplats
- Aras talk: https://www.youtube.com/watch?v=4E5WqZjzx-g
- 3D-Annotator: https://github.com/3D-Annotator/3D-Annotator
- Toaster: https://github.com/augustin-bresset/toaster
