# Research: Residential Frame Point Cloud and PCL Stud Isolation

## Goal A: Residential Bare-Frame Point Cloud Candidates

A thorough search across OpenTopography, PointClouds.org, PCL GitHub/SourceForge, and broad academic dataset portals (Zenodo, DesignSafe-CI, Dataverse) was conducted to find public US light-frame style house point clouds at the frame stage (exposed 2x4/2x6 studs).

The primary portals (OpenTopography, pointclouds.org, etc.) do not host interior stud-frame datasets natively. Airborne LiDAR datasets (e.g., OpenTopography's São Paulo or New Zealand collections) cover building exteriors and roofs but do not penetrate to bare framing. However, specialized academic datasets yielded strong candidates.

### Candidate Clouds Table

| Name / Source | URL | Format | License | Match / Reject vs LOT-62 Residential Frame |
| --- | --- | --- | --- | --- |
| **Rohbau3D Dataset** (Lukas Rauch) | [GitHub / OpenData UniBw M](https://github.com/RauchLukas/rohbau3d) | XYZ/PCD | CC BY 4.0 | **Match / Nearest Miss**: Real construction sites in shell-stage (Rohbau). Contains labeled instances and semantic classes for structural elements. It's European construction, but includes timber frame/woodwork elements resembling studs. |
| **E-Defense / NHERI Wood-Frame Tests** (Koliou et al.) | [DesignSafe-CI PRJ-5940 / PRJ-2180](https://www.designsafe-ci.org/data/browser/public/designsafe.storage.published/PRJ-5940) | Point Cloud (sub-cm) | ODC-By | **Strong Match**: Terrestrial LiDAR scans of full-scale and 1:2 scale US-style light-frame timber buildings before and during shake table testing. Captured with Leica and Maptek scanners. |
| **NHERI 2019 Storm Surge Damage** (Yu, Cox, et al.) | [DesignSafe-CI (DOI: 10.17603/ds2-0rky-9w25)](https://doi.org/10.17603/ds2-0rky-9w25) | Undefined | ODC-By | **Partial Match**: 1:6 scale light-frame wood specimens. Excellent bare-frame geometry, but physically scaled down. |
| **SUM4Re LiDAR Dataset** | [Zenodo (19678608)](https://zenodo.org/records/19678608) | LAZ | CC BY 4.0 | **Nearest Miss**: Contains indoor/outdoor structural scans including a `Target_RS10_woodwork.laz` scene for urban mining, but not a full residential frame house. |
| **EXC IntCDC Associated Project 11** (Stuttgart) | [Darus (DOI: 10.18419/DARUS-3304)](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi%3A10.18419%2FDARUS-3304) | LAS | CC BY 4.0 | **Reject**: 23 timber building projects, but typically heavy timber/columns (glulam/CLT styles) rather than US 2x4 light framing. |

### Best Download Links to Try Next
1. **Rohbau3D (OpenData UniBw M)**: Use their [download.py script](https://github.com/RauchLukas/rohbau3d) to pull targeted semantic timber scenes without downloading the entire database.
2. **NHERI E-Defense Shake Table (DesignSafe-CI)**: Browse `PRJ-5940` or search for PI Maria Koliou's RAPID deployment data in the DesignSafe Data Depot to get real light-frame point clouds.
3. **NHERI 2019 1:6 Scale (DesignSafe-CI)**: [Download here](https://doi.org/10.17603/ds2-0rky-9w25) - while 1:6 scale, it perfectly isolates stud structures without drywall.

*Note: There were "none found" natively hosted on OpenTopography, PCL sample data, or conda/brew repos that matched residential bare-frame.*

## Goal B: PCL Stack for Isolating Studs

1) **Which PCL modules are the right path?**
   - **`filters`**: `pcl::PassThrough` (to crop height/bounds) and `pcl::VoxelGrid` (for downsampling).
   - **`features`**: `pcl::NormalEstimation` (critical for orienting models and ensuring studs are vertical).
   - **`sample_consensus` & `segmentation`**: `pcl::SACSegmentation` with `pcl::SACMODEL_PLANE` (to extract and remove floor/ceiling).
   - **`segmentation`**: `pcl::EuclideanClusterExtraction` or `pcl::RegionGrowing` (to cluster the remaining disconnected upright studs).
   - **`sample_consensus`**: `pcl::SACMODEL_CYLINDER` or `pcl::SACMODEL_LINE` inside a RANSAC loop to fit the axis of each stud cluster.

2) **Does PCL ship any ready demo/tutorial that extracts studs?**
   - **No.** PCL does not ship a tutorial specifically named for building frames or wooden studs.
   - **Closest Proxy:** PCL does provide a tutorial for extracting upright geometry from a plane: the [Cylinder Model Segmentation Tutorial](https://pcl.readthedocs.io/projects/tutorials/en/latest/cylinder_segmentation.html). It demonstrates extracting a flat table (`SACMODEL_PLANE`) and then extracting a mug (`SACMODEL_CYLINDER`). The algorithmic flow is identical to segmenting a floor and then extracting vertical studs.

3) **Practical Recipe Sketch (High Level)**
   - **Filter:** `VoxelGrid` downsample the cloud to a workable resolution (e.g., 1-2 cm). Use `PassThrough` filter to remove ceiling if it occludes walls.
   - **Normals:** Run `NormalEstimation` (or `NormalEstimationOMP`) to compute surface normals.
   - **Floor Extraction:** Run `SACSegmentation` with `SACMODEL_PLANE`, `SAC_RANSAC`, and a `DistanceThreshold` of ~0.02m. Extract indices and remove them from the cloud.
   - **Stud Clustering:** Run `EuclideanClusterExtraction` on the remaining points. A distance threshold of ~0.1m will separate discrete vertical studs into distinct `PointIndices` clusters.
   - **Stud Fitting:** For each cluster, either compute an Oriented Bounding Box (OBB) using `pcl::MomentOfInertiaEstimation` (PCA), or fit a `SACMODEL_LINE` (with a constraint restricting the axis to `[0,0,1]` vertical) to find the stud centroid and orientation.
   - *(Note: PCL is BSD-licensed, allowing commercial/research use without GPL constraints).*

4) **One-Click Tool Availability**
   - **There is NO one-click "isolate wooden studs" tool in PCL.** It is a low-level algorithmic toolkit; you must write the C++ (or Python wrappers) pipeline to chain filtering, RANSAC, and clustering together yourself.
