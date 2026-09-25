# Related work — bibliography skeleton

Citation keys live in [`references.bib`](references.bib). The draft uses them in [`draft/paper.md`](draft/paper.md). This page is the reading map. Checked on **2026-09-25** unless a row says the number sits only in an engineering note.

Runs that changed what “related” means for a stack already in the plan:

- Rank 2 has been executed on class S as a NumPy port on the 25-scene matrix, and as PCL 1.14 on one Linux stud. It is still not a historic-roof result.
- Rank 3 (Schnabel / CloudCompare) has been executed on class S twice. Untuned, it fails the one-stud bar by returning 4–8 faces. Tuned (PR #22), plane only plus a four-face merge, it passes the stage-0 bars on 25 of 25 scenes with one box. The plugin still has no cuboid.
- Rank 6 (pyRANSAC-3D) has been executed on class S. SAM 2 has not.
- Ranks 4 and 5 have been executed as controls (no stud class) and as a synthetic fine-tune. PointGroup and KPConv have not been run.

## Timber cuboids

| Key | What it is for this paper | What it must not be used as |
| --- | --- | --- |
| `ozkan2022timber` | Region growing on beam side faces, then cuboids. On one historic roof, automatic beam completeness 29% to 63% against a manual count, and 75% with additional manual splits. | A 2×4 stud score or a green/red rate. |
| `pochtrager2018roof` | Cuboids from planar side faces. Sub-centimeter agreement on historic roofs, as the paper highlights. | Stud plumb at ~0.12°. |
| `pochtrager2017roof` | Earlier note on the same roof problem. | A light-frame dataset. |
| `ozkan2024completion` | Later completion that still depends on the 2022 cuboid workflow. | Evidence that a native PCL binary ran on S1. |
| `chen2025timberfe` | Geometric FE models from a timber point cloud. Specimen digits in the engineering ranking (within 3%, plane angles within 1°, cylinders forced to global Z) were **not** re-tabulated from the PDF. | A stud-lean RMSE. Forcing the axis to global Z would hide the lean. |

## Primitive fitting

| Key | What it is for this paper |
| --- | --- |
| `schnabel2007ransac` | Planes, spheres, cylinders, cones, and tori. This is the family behind CloudCompare RANSAC Shape Detection (rank 3). Untuned, the plugin returned 4–8 primitives per synthetic stud and failed the stage-0 bars on 25 of 25 scenes. The stud-only tune (PR #22) keeps plane only and merges four long faces: stage-0 pass 25/25, one box. |
| `fischler1981ransac` | Original RANSAC article. Context for Schnabel and for pyRANSAC-3D. |
| `mariga2026pyransac` | pyRANSAC-3D v0.7.0. Rank 6. Run on class S (one stud and the 25-scene matrix, 25/25 stage-0 bars). The library publishes no stud accuracy. |
| `bassier2020walls` | Unsupervised BIM wall objects. The plan refuses a remote coplanar merge. |
| `ntiyakunze2023sensors` | **Citation hygiene.** Crossref resolves `10.3390/s23041924` to Ntiyakunze and Inoue (2023), not to Bassier. |

## Learned point clouds

| Key | What it is for this paper |
| --- | --- |
| `wu2024ptv3` | Point Transformer V3. The rank-4 backbone. Indoor and outdoor scores from that paper are not stud scores. |
| `pointcept` | Training codebase. Used for the BIMStruct3D control and for the synthetic 2-class head. |
| `jiang2020pointgroup` | PointGroup, named in the rank-4 plan. **Not run.** |
| `zhou2018open3d` | Open3D library paper. Rank 1 uses Open3D 0.20. Rank 5 uses `open3d.ml.torch`. |
| `open3dSoftware` | The pinned software release. |
| `ester1996dbscan` | Density clustering after the plate peel. **UNVERIFIED PAGINATION.** |
| `ravi2024sam2` | Planned gated mask when a registered image exists. **Not run.** |

S3DIS and ScanNet mIoU stay off the stud table. The rank-5 control records a histogram on the generator cloud and does not copy a benchmark mIoU.

## Methods shortlist that is not in this branch

`docs/research/17-methods-that-beat-shortlist.md` on branch `cursor/methods-beat-shortlist-e9dc` (PR #14) surveys YOLO, Vuforia, RoomPlan, commercial scan-to-BIM tools, CGAL, and several 2023–2026 timber or frame papers. This bibliography pass did **not** re-open those pages and did **not** add keys for them. The draft repeats only the WFC README rotation figures that note already attributes to the dataset README (mean 1.43°, median 1.00°, 73.61% inside 20 mm and 2°), and it keeps the journal-PDF caveat on `xie2026wfc`.

| Key | What it is for this paper |
| --- | --- |
| `xie2026wfc` | One 2×4, vision in front of 6D pose. Not our pipeline. |
| `jocher2023ultralytics` | The image detector in front of that pose. Not a point-cloud lean method. |

## Construction tolerances

| Key | What it is for this paper |
| --- | --- |
| `woodworksTolerances` | Primary page re-read for the earlier draft. IBC and AWC NDS do not set a light-frame wood construction-tolerance requirement. Summarizes Handbook, NAHB, and UFGS. |
| `ballast2007handbook` | Handbook of Construction Tolerances, 2nd ed. τ ≈ 0.1194° is **derived** by `atan((1/4 inch) / (10 feet))`. |
| `nahbGuidelines` | **UNVERIFIED PLACEHOLDER.** 3/8 inch in 32 inches is WoodWorks’s summary only. |
| `ufgs061000` | **UNVERIFIED PLACEHOLDER.** 1/4 inch in 8 feet is WoodWorks’s summary only. The same `atan` yields ≈ 0.1492° (about 0.15°). That alternate is not the paint band. |

## As-built scanning, house-alike data, and phone context

| Key | What it is for this paper |
| --- | --- |
| `tang2010asbuilt` | Review of automatic as-built BIM from laser scans. Not a stud score. |
| `bosche2015scan` | Scan-to-BIM plus Scan-vs-BIM for cylindrical MEP. Not lumber. |
| `apple2022roomplan` | **UNVERIFIED THIS PASS** as a live fetch. Walls and openings, not studs. |
| `appleArkitGravity` | **UNVERIFIED THIS PASS** as a live fetch. Y-up gravity for a later reference vector. Not ε. |
| `erland2026iphone` | Bibliographic record verified. RMSE centimeters in the sensing survey were not re-extracted. |

The house-alike hunt is `docs/research/15-house-alike-frame-clouds.md` on branch `cursor/house-alike-cloud-hunt-0474` (PR #12). Its conclusion, adopted here without re-fetching every listing: no public cloud was found that looks like a US platform-frame house at sheathing stage and that could bake off a phone or robotics lidar. Class F waits on an own scan. File sizes and licenses in that note were not re-checked for this paper pass.

## Gaps this related-work pass does not fill

- No public light-frame stud benchmark was found in the repository survey. This draft does not invent one.
- Commercial scan-to-BIM tools stay out of the bake-off, as in the ranking note and the PR #14 shortlist.
- NAHB and UFGS primary documents are still closed.
- Doc 17 papers beyond the keys already in `references.bib` stay outside the bibliography until a later pass opens them.
