# Residential light-frame scans at sheathing stage

Research date: **2026-09-24**. The target is a point cloud of a **US or Canadian platform-frame house** while the lumber is still visible: 2×4 / 2×6 studs, plates, OSB or plywood sheathing, a garage or porch, trusses. The reference is the three site photos attached with this research request (the LOT 62 look: sheathing stage, not an IntCDC timber hall).

What those photos show, so a later search can be checked against them:

- Two-story house on a dirt lot, sidewalk and street in front, block wall at the side.
- First floor largely sheathed in OSB, with window openings cut.
- Second floor still open studs under a roof frame.
- A front porch or carport on a slab: wood posts, trusses, and a small gable, open underneath so the back of the house is visible.
- Loose OSB sheets on the ground. A temporary power panel. Neighboring houses in the distance.

That is light-frame construction at **framing / sheathing**, before drywall and before finishes. It is not the IntCDC timber-hall scans, not a European shell (Rohbau), and not a finished facade.

Nothing below was downloaded.

## Result

A public point cloud of a house that looks like those photos was **not found**. The searches below were run on 2026-09-24. They add candidates to the ranking in [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md). They do not replace ranks 1–5. IntCDC, WFC, RefSite3D, Rohbau3D, and ConSLAM remain the closest downloadable clouds, and none of them is this house.

The new hits are, in order of usefulness for *seeing light-frame lumber*, not in order of “download this first”:

| Rank among new hits | What it is | Why it is not the photo |
| --- | --- | --- |
| 1 | NHERI wave-basin lidar of **1:6-scale light-frame wood** specimens (PRJ-2513) | Real light-frame wood, real lidar. Scale models in a flume, then damaged by waves. Not a lot, not OSB-on-a-street house, file size not read. |
| 2 | Rosenheim **synthetic** timber-wall point clouds (10,000 PLY/STL) | Wall-scale wood and labels. Generated in Blender. Not a scan, and not a stick-framed house. Non-commercial dataset license. |
| 3 | Augmented Carpentry mock-up scans (PLY/E57, about 10 GB) | Real scanned timber pieces and small assemblies. Carpentry joints, not a residential frame. |
| 4 | DesignSafe wood-frame projects whose clouds were not readable in the browser (PRJ-2180, and PRJ-5940 as a specimen only) | Titles match “wood-frame.” A sheathing-stage house cloud was not confirmed. |
| 5 | Schependomlaan drone SfM of a Dutch housing site | Real drone clouds of housing under construction. Prefab, steel, roofs. Zip link is dead. |
| — | vizHOME, ResFa, Sketchfab “framing” models, OpenDroneMap samples, USGS 3DEP | Real houses or real aerial data, wrong stage or wrong representation. Listed so they are not fetched again as if they were stud scans. |

## Search log

| Query or page | Date | What came back |
| --- | --- | --- |
| `residential light-frame wood stud point cloud dataset LAS E57 2x4 framing` | 2026-09-24 | Rohbau3D, a lab paper with three 2×4 test frames and a RealSense (no public cloud), Autodesk robotic wall framing (no public cloud), a 2019 nail-laminated pavilion scan (not a house). |
| `point cloud wood frame OR light-frame OR platform frame OR stud wall house scan zenodo github sketchfab` | 2026-09-24 | IntCDC again, Rohbau3D again, Augmented Carpentry, Rosenheim wall clouds. |
| `NHERI TallWood OR NEESWood OR NIST point cloud residential wood frame house laser scan` | 2026-09-24 | TallWood project site (mass timber shake-table building; no point-cloud download on the page fetched). NHERI REU 2019 wave-basin lidar. A separate lidar paper is a full-scale **RC** building, not wood. |
| `DesignSafe light-frame wood LiDAR` | 2026-09-24 | PRJ-2180 (wood-frame systems, a `Pointclouds` folder in the URL). PRJ-5940 (1:2-scale three-story light-frame timber building). |
| https://www.opendronemap.org/odm/datasets/ | 2026-09-24 | aukerman, bananas, brighton_beach, seneca, toledo, conch. No construction frame. |
| Sketchfab “standard house type framing only” and “wooden frame construction house” | 2026-09-24 | CAD meshes. See the table. |
| HUD / NIST as dataset hosts | 2026-09-24 | No framing-stage single-family cloud appeared in these queries. This pass did not crawl every NIST project page. |
| USGS 3DEP program page was not opened as a tile | 2026-09-24 | Nationwide elevation lidar is the wrong product (terrain and roofs). No tile was downloaded. Not counted as a stud scan. |

## Candidates

| ID | Name | What the bytes actually are | License | Size | Download | Vs the photos | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | NHERI PRJ-2513, wave-basin light-frame specimens | One on-slab and one elevated **1:6-scale light-frame wood** specimen. Terrestrial lidar during a wave-basin test. Damage tracked by fitting wall planes in Leica Cyclone (abstract). | DesignSafe public record. A separate data-use sentence was not in the abstract. | Not read. The data browser returned only the project title. | https://doi.org/10.17603/ds2-0rky-9w25 | Closest **new** “light-frame wood + lidar.” Scale model, storm damage, not a two-story OSB house on a lot. | `surveyed` abstract; files `not-downloaded`; size `unverified` |
| R2 | Rosenheim wall point clouds | **10,000 synthetic** timber-wall models. PLY and STL plus per-point labels. Blender generator. Paper: GNN segmentation of machining features, PointNet++ and DGCNN, F1 up to 0.994 on that synthetic set. | Dataset **CC BY-NC-SA 4.0**. Generator README does not state a code license. | Zenodo lists **1.1 GB** (`Dataset.zip`). | https://doi.org/10.5281/zenodo.16756219 — code https://github.com/SchulzDaniel/wall-point-cloud-generator | Wall-scale wood with labels. Generated, European panel workflow (boards, nails, machining), not a scanned 2×4 house. NC license blocks a commercial training set. | `surveyed; not-downloaded` |
| R3 | Augmented Carpentry supplementary scans | Raw scans of timber **mock-ups**: per-beam scans, a raw scan of the assembly, CAD execution model. PLY, E57, and Rhino 3dm. | **CC BY 4.0** (Zenodo API). | `raw_data.zip` is **10,012,523,182 bytes** (~9.3 GiB). `results.zip` 173,416,062 bytes. | https://doi.org/10.5281/zenodo.14610164 | Real timber points and joints. Not a house, no OSB street elevation, no garage. | `surveyed; not-downloaded` |
| R4 | DesignSafe PRJ-2180 | Project title: Japan–US collaboration on seismic resilience of **wood-frame building systems**. The public browser URL contains a `Pointclouds` folder under `06_20190201_Kobe_Takatori_50pct`. “50pct” in that folder name was **not** verified as a scale factor; it sits next to a ground-motion record name. | DesignSafe public project page. Terms of the files were not read (page is a script shell). | Not read. | https://doi.org/10.17603/ds2-4rf2-bj36 | Do not treat this as the OSB house until someone opens a cloud and sees studs. Contents `unverified`. | `unverified` contents; `not-downloaded` |
| R5 | DesignSafe PRJ-5940 | Title only: shake-table test of a **1:2-scale three-story light-frame timber building**. | Same browser limit. | Not read. | https://www.designsafe-ci.org/data/browser/public/designsafe.storage.published/PRJ-5940 | The specimen class matches light-frame better than IntCDC. A point-cloud file was not listed in the fetch, which returned the title only. | `unverified` as a cloud; `not-downloaded` |
| R6 | Schependomlaan | Drone video of a housing project in Nijmegen, weeks 26–30, turned into as-built clouds by RAAMAC. PLY, ASCII, some LAS. IFC design models alongside. Subcontractors include flooring, walls, stairs, fencing, steel, roofs, prefab. | README: scientific and academic use, with owner permission. Not a SPDX id. | Unknown. Release zip returned **HTTP 404** on 2026-09-24. | README: https://github.com/jakob-beetz/DataSetSchependomlaan — zip linked from that README did not resolve. | Drone SfM of housing under construction. Not US stick framing with OSB and open stud bays. | `surveyed` README; download `unverified` (404) |
| R7 | vizHOME | 20 occupied homes (detached and semi-detached), University of Wisconsin. Full XYZ point clouds and a 1 cm simplified cloud. Example from the documentation table: detached home D1 full cloud **2.72 GB**, simplified **0.02 GB**. | A license sentence was not in the HTML fetched this pass. Do not assume CC. | Per-home sizes are on the documentation table. | https://pages.discovery.wisc.edu/vizhome/documentation.html | Finished, furnished houses. Studs are behind finishes. | `surveyed` table; license `unverified`; `not-downloaded` |
| R8 | ResFa | Already in doc 06. 66 pre-1975 residential **wood-frame facades**. Terrestrial lidar PCD. Stud labels are inferred. | **CC BY-NC 4.0** (doc 06). | Not re-measured. | https://huggingface.co/datasets/resfa2026/ResFa | Finished exteriors. The wood frame is behind the facade. | `surveyed` previously; `not-downloaded` |
| R9 | Sketchfab “Standard house type framing only” | Mesh from Wolf Systems Horizon timber-frame software. Page text does not call it a scan. | License field on the page was empty. | Not a point cloud. | https://sketchfab.com/3d-models/standard-house-type-framing-only-2c7629f083ce494f83ef4be7a7b3c602 | Looks like framing in a viewer. It is a CAD model of a timber-frame system, not OSB platform frame, and not a scan. | `surveyed`; not a cloud |
| R10 | Sketchfab “Wooden frame construction - house #6825” | Mesh. **12.4k triangles, 7.4k vertices.** “Construction completed in 2025.” | **CC BY-NC-ND** | Mesh, not a cloud. | https://sketchfab.com/3d-models/wooden-frame-construction-house-6825-157e931232ce4010af483b2853cbfa66 | A finished-construction model with too few vertices to be a scan of studs. | `surveyed`; not a cloud |

## Against the sets already ranked

| Existing rank | Catalog | Still true on 2026-09-24 | Against the photos |
| --- | --- | --- | --- |
| 1 | D9 IntCDC | CC BY 4.0, LAS, ~223 GB, Leica P20, timber after assembly | Heavy timber members. Not 2×4 walls, not OSB, not a porch on a slab. |
| 2 | D3 WFC | One 2×4, ZED 2i, PLY, 10.65 GB raw zip, license unset | The right stick cross-section. One stud on a bench. |
| 3 | D10 RefSite3D | CC BY 4.0, 2.2 GB, timber inside a concrete/steel module | Not a house. |
| 4 | D1 Rohbau3D | CC BY 4.0, masonry and concrete shell, semantic classes | Residential buildings at shell stage, European, not wood studs. |
| 5 | D11 ConSLAM | Academic-use code license, London redevelopment floor | Concrete floor under construction. Not wood. |

R1 is the first public lidar this pass can point at that the authors call **light-frame wood**. It does not move above WFC for a stud OBB, because it is a 1:6 specimen and the files were not opened. R2 is the first public **labeled wall** point-cloud bundle, and it is synthetic. Neither one is a substitute for scanning a house like the photos.

## What was checked and is the wrong stage

- **NHERI TallWood** (https://nheritallwood.mines.edu/): 10-story mass-timber shake-table building. The fetched page has newsletters and a design PDF pointer. It does not link a framing point cloud.
- **OpenDroneMap samples**: landscapes and small objects. No house frame.
- **USGS 3DEP**: national elevation lidar. Not an interior or sheathing survey. No tile opened.
- **HUD**: no dataset hit in the queries above.
- **NIST**: no framing-stage house cloud in the queries above. The closed HUD robotics topic in doc 04 is a funding notice, not a scan archive.
- **Finished interiors** already set aside in doc 06 (ScanNet++, BIMNet) stay set aside.

## If a scan is captured on purpose

The photos are the specification for a useful file: a ground-level cloud, OSB and open bays both present, porch trusses included, coordinates in a local frame, and a note of whether Z is gravity. Phone lidar remains the accuracy class in Table 1 (S1–S2), not survey TLS. Keep the file out of git (`.gitignore` already ignores `*.ply`, `*.las`, `*.laz`).

Until that file exists, the honest training situation is unchanged from doc 06: no public complete light-frame house cloud, and the new rows above do not fill it.
