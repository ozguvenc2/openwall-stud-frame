# Residential Frame Point Cloud and PCL Stud Isolation Search

Research date: **2026-09-24**. 

## Goal A: Public Residential Bare-Frame Point Cloud

The target is an exact visual match for the LOT-62 / US light-frame style house at **frame / sheathing stage** (exposed 2x4/2x6 studs, OSB, porch/garage trusses, before drywall), as documented in `11-residential-light-frame-scans.md`. The search exhaustively queried OpenTopography, pointclouds.org, PCL package managers, Zenodo, DesignSafe, and Dataverse, specifically avoiding European shell construction (Rohbau3D) and heavy mass timber (IntCDC) as the primary match, although they are referenced as nearest misses.

**Result: None found.** A point cloud dataset matching the visual specification of the US light-frame sheathing-stage house was **not found** hosted publicly on the searched portals. 

### Nearest-Miss Datasets

The search yielded the following datasets that are technically related but visually incorrect:

| Dataset / Project | URL | Format | Why it's a miss vs the target photos |
| --- | --- | --- | --- |
| **SIP Dataset (Sites in Pieces)** | [arXiv](https://doi.org/10.48550/arxiv.2512.09062) | PCD | Terrestrial LiDAR collected at active construction sites, containing "opening framing" labels. It includes fragmented jobsite scans, but it is not a complete 2x4 residential light-frame platform house. |
| **Rohbau3D Dataset** | [GitHub](https://github.com/RauchLukas/Rohbau3D) | PCD/XYZ | 504 LiDAR scans of 14 construction sites. It is European shell construction (concrete/masonry/steel), not US wood studs. |
| **NHERI E-Defense Shake Table (PRJ-5940)** | [DesignSafe](https://www.designsafe-ci.org/data/browser/public/designsafe.storage.published/PRJ-5940) | Unverified | A 1:2 scale three-story light-frame timber building. While the structural class matches, it is a shake-table test specimen, not a two-story OSB-sheathed home on a street lot. |
| **ENDUROFRAME Light Steel (Synthetic/MR)** | [MDPI Paper](https://www.mdpi.com/2075-5309/14/4/952) | PCD (converted) | Light steel framing dataset captured with Mixed Reality (MR) headsets and synthetic BIM. The data is not publicly linked for download. |

### Better Search Keywords for Follow-up
If future searches are conducted, the following keywords should be used to avoid mass timber and civil engineering concrete shells:
- `"platform frame" OR "stick framing"`
- `"residential construction" AND "terrestrial LiDAR" -concrete -steel -CLT`
- `"residential wood frame" AND "point cloud" OR "PCD" OR "E57"`

## Goal B: PCL Stack for Isolating Studs

**1) Which PCL modules isolate vertical studs from floor/ceiling/clutter?**
- **`filters`**: `pcl::VoxelGrid` (downsampling) and `pcl::PassThrough` (cropping out the ceiling and irrelevant bounds).
- **`features`**: `pcl::NormalEstimation` (critical for calculating surface normals to distinguish planes).
- **`sample_consensus` / `segmentation`**: `pcl::SACSegmentation` with `pcl::SACMODEL_PLANE` (to extract and remove the floor and ceiling).
- **`segmentation`**: `pcl::RegionGrowing` (merging points based on smoothness/normals) or `pcl::EuclideanClusterExtraction` (separating the remaining physical studs).
- **`sample_consensus`**: `pcl::SACMODEL_CYLINDER` or `pcl::SACMODEL_LINE` (for fitting an axis to each isolated cluster).

**2) Does PCL ship any ready demo/tutorial that extracts studs?**
- **No.** PCL does not ship a "residential framing" or "wooden stud" tutorial.
- **Closest Proxies:** 
  1. The [Region Growing Segmentation Tutorial](https://pcl.readthedocs.io/projects/tutorials/en/latest/region_growing_segmentation.html) demonstrates clustering points that belong to the same smooth surface, which is how individual faces of a stud are grouped.
  2. The [Cylinder Model Segmentation Tutorial](https://pcl.readthedocs.io/projects/tutorials/en/latest/cylinder_segmentation.html) demonstrates using RANSAC to remove a planar surface (a table) and then isolating an upright object (a cylinder).

**3) Practical Recipe Sketch**
1. **Filter:** Downsample the point cloud with `pcl::VoxelGrid` (~1-2 cm).
2. **Normals:** Estimate normals with `pcl::NormalEstimation` using a search radius.
3. **Floor/Ceiling Removal:** Use `pcl::SACSegmentation` with `pcl::SACMODEL_PLANE` (RANSAC). Extract and remove the inliers (floor/ceiling) from the cloud.
4. **Segmentation (Clustering):** Use `pcl::RegionGrowing` (checking angles between normals, e.g., `setSmoothnessThreshold(3.0)`) or `pcl::EuclideanClusterExtraction` (checking spatial distance, e.g., `setClusterTolerance(0.05)`) to group the remaining points into individual stud clusters.
5. **Feature Fitting:** Iterate through each cluster's `pcl::PointIndices`. Compute the centroid and principal axis using PCA (`pcl::MomentOfInertiaEstimation`) or fit a bounding box (OBB) to represent the physical stud. *Note: PCL uses a BSD license, meaning this stack can be used in commercial code without GPL constraints.*

**4) Is there a one-click tool?**
- **No.** There is definitively no one-click "isolate wooden studs" tool or API in PCL. Developers must string together the low-level filtering, segmentation, and clustering classes manually to achieve this.
