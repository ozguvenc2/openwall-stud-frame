# Related work — bibliography skeleton

Citation keys live in [`references.bib`](references.bib). The draft uses them in [`draft/paper.md`](draft/paper.md). This page is the reading map, not a second results table.

Checked on **2026-09-25** unless a row says the number sits only in the engineering survey.

## Timber cuboids

| Key | What it is for this paper | What it must not be used as |
| --- | --- | --- |
| `ozkan2022timber` | Region growing on beam side faces, a split of non-linear segments, then cuboids. On one historic roof the authors report automatic beam completeness, against a manual beam count, rising from 29% to 63%. With additional manual splits they report 75%. Both the abstract (29% to 63%) and the method comparison (75% with manual splits) were visible on the publisher page during this check. | A 2×4 stud score, an angle error, or a green/red rate. Transept beam counts printed in the engineering ranking were not re-copied here. |
| `pochtrager2018roof` | The cuboid workflow Özkan et al. extend. Beams are modeled as cuboids from planar side faces. The paper highlights sub-centimeter agreement of modeled beams with the reference cloud on historic roofs. | Stud plumb at ~0.12°. |
| `pochtrager2017roof` | Earlier development note on the same roof problem (Vienna Hofburg). | A light-frame dataset. |
| `ozkan2024completion` | Later completion of roof models that still depends on the 2022 cuboid workflow. | Evidence that the OpenWall rank-2 stub has been run. |
| `chen2025timberfe` | Geometric finite-element models from a timber point cloud (Buildings, 2025). The engineering ranking records, for one specimen, dimension error within 3%, plane angles within 1°, and cylinders forced to global Z. Those specimen figures were **not** re-tabulated from the PDF in this pass. | A stud-lean RMSE. Forcing a member axis to global Z would hide the lean TruePlank exists to report. |

Rank 2 in the engineering plan is “PCL region growing, then a cuboid in this sense,” with two refusals already written down: no remote coplanar merge, and no axis forced to Z. PCL has not been executed in this repository.

## Primitive fitting

| Key | What it is for this paper |
| --- | --- |
| `schnabel2007ransac` | Planes, spheres, cylinders, cones, and tori by efficient RANSAC. This is the algorithm behind CloudCompare’s RANSAC Shape Detection plugin, which the engineering plan keeps as an independent fitter (rank 3). A 2×4 is not one of those primitives. The plugin has not been run here. |
| `bassier2020walls` | Unsupervised reconstruction of BIM wall objects from point clouds (Automation in Construction, 2020). Cited at title level. The engineering plan refuses a merge of coplanar patches because stud faces that share a wall plane would become one component. |
| `ntiyakunze2023sensors` | **Citation hygiene.** Crossref resolves `10.3390/s23041924` to Ntiyakunze and Inoue (2023), Sensors 23(4):1924. The engineering ranking names that DOI as Bassier, Sensors 2023. This paper does not repeat that attribution. |

## Learned point clouds

| Key | What it is for this paper |
| --- | --- |
| `wu2024ptv3` | Point Transformer V3 (CVPR 2024, pages 4840–4851). The planned Pointcept backbone. No weights are loaded in this repository. Indoor and outdoor benchmark scores from that paper are not stud scores. |
| `pointcept` | The training codebase. The OpenWall hook is a stub until stage 5 has stud labels. |
| `jiang2020pointgroup` | PointGroup instance segmentation (CVPR 2020, pages 4866–4875). Named because the engineering plan’s rank 4 is “Pointcept PTv3 / PointGroup.” Office and indoor instance metrics stay on those benchmarks. |
| `zhou2018open3d` | Open3D library paper (arXiv:1801.09847). The rank-1 implementation uses Open3D 0.20. |
| `open3dSoftware` | The pinned software release. |
| `ester1996dbscan` | Density clustering used after the horizontal-slab peel. Bibliographic pagination is the usual KDD 1996 record; confirm the PDF before camera-ready. |

S3DIS, ScanNet, and SemanticKITTI numbers are intentionally absent. The engineering ranking already refuses to copy them onto studs.

## Construction tolerances

| Key | What it is for this paper |
| --- | --- |
| `woodworksTolerances` | Primary page actually re-read for this draft. WoodWorks states that the IBC and the AWC NDS do not set a light-frame wood construction-tolerance requirement. The page summarizes a Handbook tightening to 1/4 inch in 10 feet when finishes such as gypsum wallboard and plaster are used, an NAHB figure of 3/8 inch in 32 inches, and UFGS figures. Those other documents were not re-opened here. |
| `ballast2007handbook` | Handbook of Construction Tolerances, 2nd ed., Wiley, 2007. ISBN 978-0-471-93151-5 checked on the Wiley page. The angular working tolerance τ ≈ 0.1194° is **derived** in [`docs/tolerances.md`](../../docs/tolerances.md) by `atan((1/4 inch) / (10 feet))`. It is not a degree printed as code. |

The 2021 IRC wall chapter is discussed in `docs/tolerances.md` via an UpCodes reading: stud size, height, and spacing are specified; a general wood-stud plumb tolerance was not found there. That code viewer was not re-opened for this draft, so the paper points at WoodWorks for the IBC/NDS statement and at the repository note for the IRC reading.

## Sensing context

| Key | What it is for this paper |
| --- | --- |
| `erland2026iphone` | Crossref: Erland and Gaulton, Remote Sensing Letters 17, pages 1620–1631 (2026). The repository sensing survey attributes centimeter-class iPhone LiDAR RMSE to this article. Those centimeters were not re-extracted from the PDF here. Phone LiDAR remains a detection sensor in the capture protocol, not the instrument for a green/red call. |

Vendor TLS specifications (FARO Focus, Leica RTC360, and others) stay in [`docs/research/01-sensing-modalities.md`](../../docs/research/01-sensing-modalities.md) as vendor claims. They are not given BibTeX entries until a paper needs a specific brochure row, and they are not a measured stud-axis uncertainty.

## Gaps this related-work pass does not fill

- No public light-frame stud benchmark was found in the repository survey. This draft does not invent one.
- Commercial scan-to-BIM tools (EdgeWise, Verity, CloudWorx, PointCab) stay out of the five-stack bake-off, as in the ranking note.
- Forestry stem cylinders stay out. A stem is a different object.
