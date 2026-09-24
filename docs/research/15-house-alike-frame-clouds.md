# House-alike frame clouds (LOT-62 hunt, completed)

Research date: **2026-09-24**. This note finishes the hunt started in [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md) and on draft [PR #9](https://github.com/ozguvenc2/openwall-stud-frame/pull/9). The visual target is the LOT 62 / KB Home Arizona sheathing-stage house in [PR #10](https://github.com/ozguvenc2/openwall-stud-frame/pull/10): two-story US platform frame, OSB and open studs together, porch or garage trusses, dirt lot, before drywall.

Doc 06 ranked the closest **obtainable** clouds (IntCDC timber, one 2×4, a mixed module, a masonry shell, a concrete floor). That ranking still stands for “what wood or shell file can we open.” It is **not** a LOT-62 ranking. IntCDC is heavy timber measured after assembly. It is not US 2×4 / 2×6 light-frame studs.

Nothing multi-gigabyte was committed. `.gitignore` already ignores `*.ply`, `*.las`, and `*.laz`. Previews are in [images/house-alike-clouds/](images/house-alike-clouds/INDEX.md).

## Conclusion

**Wait for Oz’s own residential 2×4 / 2×6 scan.** A public cloud that looks like LOT 62, and that could bake off a Livox Mid-360 or iPhone pipeline, was **not found**.

What is public is survey TLS, a BLK360, or a drone photo cloud of other buildings, or one stud on a bench, or a synthetic wall, or a scale model whose cloud file was not published. None of those is a paired Mid-360-versus-iPhone test on US light-frame sheathing. The Adelaide iPhone paper that does name framing, insulation, and plastered drywall does not link a download. The Mid-360 sets opened here are offices and roads, not houses. ScanNet and ARKitScenes are finished interiors.

The five rows below are the closest **house-alike contenders**. They are regressors or viewers. They are not the bake-off.

## Ranked contenders

Likeness to LOT 62 is the sort: wood light-frame, whole building, construction date, then a real 2×4, then a scale model, then synthetic walls, then carpentry mock-ups. Download certainty is stated in the row. A mass-timber hall is not in this five.

| Rank | Name | Source | License | Modality | Why it is / is not LOT-62-like | Download size | Recommended use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | E-Defense 2019 full-scale wood dwellings, construction-day scans (DesignSafe PRJ-2180) | https://doi.org/10.17603/ds2-4rf2-bj36 | **Open Data Commons Attribution** (publication record phrase; version not printed on the record) | Leica **BLK360** E57 (59 setups, Cyclone REGISTER 360, bundle error 0.004 m) plus a **Pix4D** / DJI **FC6310** LAS | Full-scale wood houses, and one folder is dated during construction (6 Jan 2019), before the 31 Jan shake tests. B-building in the Nagoya paper is Japanese **two-by-four** shear-wall construction; A-building is post-and-beam. **Not** a US OSB house on a dirt lot. An E57 was not opened here, so open studs versus sheathing on that day is **not claimed**. Later folders are pre-test and post-shake clouds of the same dwellings, including finished rooms in the test papers. | Public listing, 2026-09-24: project about **266.5 GB** (221 LAS ≈ 252.9 GB, 59 E57 ≈ 13.5 GB). Construction folder `01_20190106_Construction/Pointclouds`: those **59 E57 (13.5 GB)** and `20190106_sfm.las` (**393.5 MB**). | Stage X regressor for a whole wood building (TLS and drone SfM). Viewer after a local download. **Not** the Mid-360 / iPhone bake-off. |
| 2 | WFC-Dataset | https://github.com/yigediao/wfcdataset | **Not stated.** README heading is `TODO: specify license` (raw README fetched 2026-09-24). | ZED 2i stereo RGB-D, PLY. Not LiDAR. | The only public **real 2×4** point clouds found, with manual 6D poses. **Not** a wall, a house, OSB, or a lot. | README: raw zip **10.65 GB**, annotations **461.77 MB**. | Stage X regressor for a single stud OBB. Not a house pipeline. |
| 3 | NHERI wave-basin 1:6 light-frame specimens (PRJ-2513) | https://doi.org/10.17603/ds2-0rky-9w25 | **Creative Commons Attribution** (publication record) | Terrestrial LiDAR, processed in Leica Cyclone (abstract and poster). Scanner model not named in the files read. | Authors call them **light-frame wood** specimens (on-slab and elevated) and “houses” in the poster. Right structural phrase. **Not** LOT 62: **1:6 scale**, wave basin, then storm damage. | Public listing is **three PDFs, 6.6 MB** (poster, paper, slides). **No** LAS, E57, or PLY in that listing. | Viewer of the poster only. Do not plan a bake-off on a cloud that was not published here. |
| 4 | Rosenheim wall point clouds | https://doi.org/10.5281/zenodo.16756219 | **CC BY-NC-SA 4.0** (Zenodo). Generator code on GitHub is **GPL-3.0**. | Synthetic. Blender walls, PLY and STL, per-point labels. Not a scan. | Timber **walls** with machining / sheathing features for a prefab line (Zenodo abstract and the IEEE DtM paper). **Not** a scanned US site-built 2×4 house. NC-SA is not a commercial training set. | Zenodo: `Dataset.zip` **1,066.1 MB**. | Stage X regressor for labeled wall geometry, non-commercial only. Not a sensor bake-off. |
| 5 | Augmented Carpentry mock-up scans | https://doi.org/10.5281/zenodo.14610164 | **CC BY 4.0** (Zenodo) | Real scans of timber mock-ups. PLY, E57, and Rhino 3dm. | Real timber points and joints (EPFL IBOIS). **Not** a residential platform frame, no OSB street elevation, no garage. | `raw_data.zip` **10,012.5 MB**. `results.zip` **173.4 MB**. | Stage X regressor for scanned timber members. Viewer. Not LOT 62. |

Previews: [INDEX.md](images/house-alike-clouds/INDEX.md).

### 1. What was verified on PRJ-2180

The publication tree names an event **“Lidar scans during construction”** plus baseline and test-day events. The public file API (`/api/datafiles/agave/public/listing/…`, 2026-09-24) lists the bytes under `RAPID Collaboration/Deliverables/`:

| Folder | What it is |
| --- | --- |
| `01_20190106_Construction` | Construction day. 59 `BLK360_*.e57` files and `20190106_sfm.las`. |
| `02_20190130_PreTest` through `11_20190212_Kobe_100pct` | Later LAS clouds around the shake program. Not counted as bare LOT-62 framing. |

Two construction-day PDFs were downloaded to read the numbers. They are not committed as PDFs. The Cyclone REGISTER 360 report (1.24 MB) is a bundle of **59 BLK360 setups**, cloud-to-cloud bundle error **0.004 m**, certified by Michael Grilliot, RAPID Facility. The Pix4D report (processed **2019-01-17**) is project **KoliouCombinedStart**: camera **FC6310**, **208 / 228** images calibrated, GSD **0.74 cm**, **10 GCPs**, mean RMS **0.003 m**. FC6310 is the Phantom 4 Pro class camera. The rank-1 PNG is page 1 of that Pix4D report, the published orthomosaic preview.

The structural description of the two buildings is the public 17WCEE paper: post-and-beam (A) and shear-wall **two-by-four** (B), three-story, same plan, on the E-Defense table. https://www.sharaku.nuac.nagoya-u.ac.jp/data/nagae/index.files/(1)%20The%202019%20Full-Scale%20Shake%20Table%20Test%20Program%20of%20Wood%20Dwellings.pdf

That is the best public whole-building wood cloud found. It is still the wrong lot, the wrong code jurisdiction, and a mix of post-and-beam with Japanese two-by-four. It is not a substitute for scanning LOT 62.

### 2. WFC

Unchanged from doc 06 (catalog D3). License gap re-checked: the GitHub README still has an empty license TODO. Do not treat the paper’s publisher license as the Dropbox license.

### 3. PRJ-2513 clouds were not published as files

Doc 11 left the file list unread. This pass listed it. The abstract is real LiDAR of 1:6 light-frame wood. The published folder is the poster, the paper, and the slides. Rank 3 is “right system, no cloud file,” which is why it sits under WFC even though a scale house is more house-shaped than one stud.

### 4 and 5

Rosenheim is the labeled wall bundle. It is generated, European prefab sheathing features, and non-commercial. Augmented Carpentry is the CC BY real timber scan that will actually open in a viewer. Neither one is a street house.

## Checked and not in the five

| Set | What this pass found | Why it is not a LOT-62 contender |
| --- | --- | --- |
| IntCDC timber scans (D9) | Still the doc 06 rank 1 for exposed timber after assembly. CC BY 4.0, LAS, on the order of 223 GB in that note. | Glulam / heavy timber members and some concrete columns. **Not** US light-frame studs. Do not train a 2×4 detector on it and call the result residential framing. |
| Rohbau3D (D1) | CC BY 4.0 masonry and concrete shells, including mid-rise apartments. | European shell. Doc 07’s line that it contains timber studs is **not** supported by doc 06 or the paper. |
| PRJ-5940, 1:2-scale three-story light-frame timber building | Publication license: Creative Commons Attribution. Listing: 16 xlsx (472.5 MB), one PDF, one DWG, one txt. **No** LAS, E57, or PLY. | The title matches light-frame. The published files are not a point cloud. Doc 07 called this a strong cloud match; that claim is withdrawn. |
| SIP, Sites in Pieces | Zenodo `10.5281/zenodo.19158662` (also 17667735 / 17667736). **CC BY-NC 4.0**. About **4.69 GB** (indoor zip ~2.37 GB, outdoor ~2.31 GB) plus a 1.4 MB overview PNG. FARO TLS, class name `opening framing`. | Real construction scans and a useful segmenter benchmark. The class name is not evidence of wood studs. Sites are not described as US platform-frame houses. NC. |
| SUM4Re `Target_RS10_woodwork.laz` | https://doi.org/10.5281/zenodo.19678608. **CC BY 4.0**. That file is **428.7 MB**. Record total about **5.89 GB**. Places: San Sebastián, Longyearbyen, The Hague. | Urban mining of **existing** buildings. “Woodwork” in a filename is not a frame-stage stud wall. The LAZ was not opened. |
| Adelaide iPhone drywall phases | Zhang et al., JCEM 2025, https://doi.org/10.1061/jcemd4.coeng-16417. Abstract says an iPhone LiDAR benchmark of framing, insulation, and plastered drywall. | No dataset URL on the pages opened. Not a public bake-off file. |
| Mid-360 multi-lidar set | arXiv:2507.04321. Livox Mid-360 with Avia and Ouster. Indoor office sequences and an outdoor sequence. | Wrong scene. Not a house frame. |
| ARKitScenes | https://github.com/apple/ARKitScenes. Apple’s repo license (non-commercial by default, with a large-MAU carve-out). 5,047 scans, furniture boxes. Paper figures are bedrooms, kitchens, and similar. | Finished interiors. Domain mismatch for bare studs. |
| ScanNet | Finished indoor reconstructions. The GitHub **code** license is MIT; that is not a finding that the scans are MIT. | Finished interiors. Not frame stage. |
| OpenTopography | Airborne lidar. Building points are a roof/envelope class (ASPRS class 6 on the tiles inspected). | Does not see studs. |
| Sketchfab “framing” models, Aalborg single-family PTS, HouseNet | CAD or synthetic envelopes (doc 11; Aalborg portal; 4TU HouseNet). | Not scans of sheathing-stage studs. |
| Figshare “Arthur’s House” | https://doi.org/10.6084/m9.figshare.21700217. **CC BY 4.0**. One **8.9 MB PDF**, not a cloud. | Historic British light timber frame, exploded axonometric. Viewer essay, not a file we can segment. |
| Schependomlaan | GitHub repo https://github.com/jakob-beetz/DataSetSchependomlaan returned HTTP 200. The release zip was HTTP 404 on the 2026-09-24 pass recorded in doc 11 and was not re-downloaded. | Dutch housing site, prefab and steel, not OSB platform frame. |
| HCIC construction VSLAM | https://github.com/Chenxy875/HCIC-Construction-VSLAM-Dataset. RealSense L515 and Ouster OS0-128 indoor construction sequences. | Indoor jobsites for SLAM. Not described as a wood stud house. |
| ResFa, vizHOME, ConSLAM, RefSite3D | Already in docs 06 and 11. | Finished facades, furnished homes, a concrete floor, or a concrete/steel/timber module. |

## PCL stud isolation (do not re-derive it here)

Draft PR #9 already maps the PCL path. It is still the right classical stack, and it is still not a one-click stud tool.

- Modules: `filters` (`VoxelGrid`, `PassThrough`), `features` (`NormalEstimation`), `sample_consensus` (`SACMODEL_PLANE` to drop floor and ceiling), `segmentation` (`EuclideanClusterExtraction` or `RegionGrowing`), then `MomentOfInertiaEstimation` or a line fit per cluster.
- PCL ships no stud tutorial. The closest shipped demo is [cylinder segmentation](https://pcl.readthedocs.io/projects/tutorials/en/latest/cylinder_segmentation.html) (plane, then an upright object).
- PCL itself is BSD.
- Full writeups, on the PR #9 branch: [14-residential-frame-cloud-and-pcl-stud-hunt.md](https://github.com/ozguvenc2/openwall-stud-frame/blob/cursor/research-residential-frame-pcl-048d/docs/research/14-residential-frame-cloud-and-pcl-stud-hunt.md) and [07-residential-frame-cloud-and-pcl-stud-hunt.md](https://github.com/ozguvenc2/openwall-stud-frame/blob/cursor/research-residential-frame-pcl-048d/docs/research/07-residential-frame-cloud-and-pcl-stud-hunt.md). Doc 07 is the earlier pass; where it disagrees with the file listing above (Rohbau as timber, PRJ-5940 as a cloud), use this note.

## What a useful own scan is

Until a local file exists, the bake-off waits. The useful file is still the one doc 11 described: ground-level, OSB and open bays both in frame, porch trusses included, a note of whether Z is gravity, stored outside git. Phone LiDAR and a Mid-360 remain the accuracy classes in [01-sensing-modalities.md](01-sensing-modalities.md). They do not become survey-TLS accurate because a Japanese BLK360 cloud exists.

## Sources

- PRJ-2180 listing and license field, fetched 2026-09-24: https://www.designsafe-ci.org/api/publications/v2/PRJ-2180/ and `https://www.designsafe-ci.org/api/datafiles/agave/public/listing/designsafe.storage.published/PRJ-2180/`
- DOI record: https://doi.org/10.17603/ds2-4rf2-bj36
- Nagoya 17WCEE paper (post-and-beam vs two-by-four): https://www.sharaku.nuac.nagoya-u.ac.jp/data/nagae/index.files/(1)%20The%202019%20Full-Scale%20Shake%20Table%20Test%20Program%20of%20Wood%20Dwellings.pdf
- PRJ-2513 and PRJ-5940 listings, same API, same day.
- WFC README: https://github.com/yigediao/wfcdataset
- Rosenheim: https://doi.org/10.5281/zenodo.16756219 and https://github.com/SchulzDaniel/wall-point-cloud-generator
- Augmented Carpentry: https://doi.org/10.5281/zenodo.14610164
- SIP: https://doi.org/10.5281/zenodo.19158662 and https://github.com/syoi92/SIP_dataset
- SUM4Re: https://doi.org/10.5281/zenodo.19678608
- Prior ranking: [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md)
