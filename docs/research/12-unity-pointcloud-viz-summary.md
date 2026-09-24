# Unity point-cloud visualization — summary for Oz

Research date: **2026-09-24**. This note compresses the Blender/Unity survey that already exists on draft **PR #4**, branch `cursor/blender-unity-pointcloud-1ad9`, file `docs/research/07-blender-unity-pointcloud-viz-and-seg.md` (commits `2d55128` and the follow-on Open3D note `7ffb040`). That branch is **not merged**. Main does not contain doc 07. The summary below follows that file. Prices and point-count limits were not re-fetched except where a later page was opened for the box question.

The question this note adds: an editor that shows **colored clusters and bounding boxes**, the way CloudCompare shows a colored cloud and the way the matplotlib views on draft PR #5 draw oriented boxes.

Status words match [README.md](README.md).

## What PR #4 concluded

Blender and Unity **show** a cloud. They do not plumb a stud. Gravity-up and the angle paint stay in Python ([02-software-segmentation-angles.md](02-software-segmentation-angles.md)).

| Job | Pick in that survey | Why |
| --- | --- | --- |
| Blender, look at a frame cloud | **Point Cloud Visualizer** (Standard, about $85 on the page fetched then) on **Blender 4.5 LTS** | PLY, LAS/LAZ, E57 in the viewport. Scalars can be colored. Pro tiles are for a cloud that does not fit in RAM. GPL on the store listing. |
| Blender, labels | **No segmenter.** Point Cloud I/O (free, GPL-3.0, Blender 5.1+, updated 11 Sep 2026) round-trips an integer attribute. | No add-on found that runs PointNet or Pointcept. |
| Unity, look at a frame cloud | **Point Cloud Viewer and Tools 3** (Asset Store, about $110, version 3.0.3 listed 10 Jun 2026) | LAS and ASCII PLY in the editor. Binary PLY and LAZ go through the external converter. VR. Bake class color into RGB before import. |
| Unity, labels | **No segmenter.** | The Asset Transformer “segmentation” control splits the cloud into cubes for culling. It is not a class label. |
| Gaussian splats | Listed so they are not used as the stud path | Appearance from photos. Do not fit a box to Gaussian means. |

Other Unity viewers in that table, short form:

| Package | License | What it is for a house cloud | Boxes? |
| --- | --- | --- | --- |
| Asset Transformer Toolkit 3.3 (ex PiXYZ), Unity Industry | Commercial. Docs used: package 3.3. Import manual: E57, RCP, PTS, PTX, glTF, and PLY if the matching importer is chosen. Over 100 million points wants ≥32 GB RAM (that manual). | Import and LOD when an Industry seat already exists. | The segmentation slider is a culling grid, not a member OBB. |
| [FastPoints](https://github.com/eliasnd/FastPoints) | **GPL-3.0**. Last push cited in doc 07: **2023-11-21**. | Out-of-core PLY/LAS/LAZ. README: attributes other than color are not visualized. | Gizmos draw **octree node** boxes and camera frustums. Not one box per stud. |
| [SFraissTU/BA_PointCloud](https://github.com/SFraissTU/BA_PointCloud) | **BSD-2-Clause**. Last push cited in doc 07: **2024-08-20**. | Potree 1.x loader. Editor preview can show points. | Preview draws the **one** bounding box of the whole set, and optional LOD node boxes. Not per-cluster OBBs. |
| [keijiro/Pcx](https://github.com/keijiro/Pcx) | Unlicense. Last push 2022. | Small PLY demo. | No. |
| Point Cloud Free Viewer | Asset Store, version 0.2 dated 2018. | OFF files. | No. |
| aras-p UnityGaussianSplatting, arloopa UnitySplats | MIT | Splat viewers. | No survey boxes. |

Doc 07 also names two web brushes that are not Unity: [3D-Annotator](https://github.com/3D-Annotator/3D-Annotator) (MIT, pushed 2026-06-02) and [toaster](https://github.com/augustin-bresset/toaster) (MIT, 0 stars, pushed 2026-08-03). Both are labeling experiments. Neither is an in-editor Unity view of `components.json`.

## Colored clusters and boxes

“Like the matplotlib OBB views” means: points colored by a heuristic label, and a wire box around each kept cluster, orbitable. Draft PR #5 (`cursor/classical-seg-obb-1a3e`) writes that as PNGs plus `components.json`. It does not open a window.

| Editor | Colored points | A box per cluster | Reads `components.json` | In-editor vs play mode |
| --- | --- | --- | --- | --- |
| Open3D `draw_geometries` | Yes, if the PLY has colors or the script paints them | Yes. `LineSet.create_from_oriented_bounding_box` (0.20 docs). Spec: [13-open3d-interactive-obb-viewer.md](13-open3d-interactive-obb-viewer.md). | With a short loader. The JSON is center, `R`, extents, label. | Desktop window. Orbit, pan, zoom. Press `H` for the key list. |
| CloudCompare | Yes. Scalar field or RGB. | The bounding box command shows the **axis-aligned** box of the **selected** cloud. A primitive fit is a plane, sphere, or cylinder (RANSAC-SD), not a stud OBB imported from JSON. | No. | Desktop GUI. Best when the file is LAS/E57 and a person is cropping by hand. GPL if the code is embedded (doc 02, W2). |
| Matplotlib views (PR #5 script) | Yes, by label | Yes, projected edges | It **writes** the JSON | PNG only. No orbit. |
| Unity PCVT 3 | Yes, from vertex color baked in the file | Not found on the store page or in doc 07 | No | Editor and play mode, after conversion |
| FastPoints gizmos | Color only | Octree nodes | No | Scene view |
| BA_PointCloud preview | Coarse points if enabled | One set AABB, plus LOD nodes | No | Editor, gizmos on |
| Blender PCV | Scalar ramp, and split by an integer | No member-OBB tool in the pages read for doc 07 | No | Viewport |

No Asset Store package and no Unity repo in doc 07 is an in-editor stud editor: class colors **and** one oriented box per member, loaded from the JSON this project writes. Building that in Unity means a custom gizmo on top of a point renderer. That is a second project. The openWall Unity repo stays a separate track (https://github.com/ozguvenc2/openWall).

## Which editor to open

| Ask | Open this |
| --- | --- |
| “I have a blank Open3D window and I want colors and boxes.” | Open3D, this week. Load the PLY and the line sets in **one** `draw_geometries` call. Steps and the blank-window causes are in doc 13. Same environment as `open3d==0.20.0`. |
| “I want to orbit a LAS, crop it, and color a scalar by hand.” | CloudCompare. It will not read `components.json`. Export a colored PLY from the Python script if the boxes must be visible there, or keep the boxes in Open3D. |
| “I want this inside Unity, in the editor or in play mode, for the XR track.” | Later. Bake label colors into RGB, convert with the PCVT external converter, and accept that the boxes are not in that package. A member box is a small script (eight corners, twelve lines) fed by the same JSON. Do not start the QA look in Unity. |
| “I want a still for a slide.” | The PR #5 matplotlib PNGs, or Blender PCV if a rendered frame is the deliverable. |

CloudCompare remains the survey file browser. Open3D is the interactive match for the colored clusters and oriented boxes. Unity is the review shell after the paint exists, not the tool that creates it.
