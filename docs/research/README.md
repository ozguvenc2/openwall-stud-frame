# OpenWall stud-frame research

Research date: **2026-09-23**. Scope: residential frame-stage QA — sample point clouds, semantic stud/beam segmentation, angle versus gravity, red/green against industry margins, with measurement-error tolerance. Near-term stack is Python + Open3D. Unity is optional later for visualization or XR. XREAL Aura is an AR display, not the capture scanner.

No multi-gigabyte datasets were downloaded into this repo. Large clouds stay behind the access URLs in [03-sample-datasets.md](03-sample-datasets.md). The frame-stage shortlist is [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md). The stud-segmentation ranking is [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md). The stage ladder and the synthetic Open3D path are [12-stud-seg-design-plan.md](12-stud-seg-design-plan.md).

## How to read these docs

Each primary table has a **status** column. Status is about *this repository and this research pass*, not about whether a vendor product works.

| Status | Meaning |
| --- | --- |
| `known` | Already stated in the repo README or the 2026-09-23 research brief. |
| `surveyed` | Checked against a primary page (vendor, paper, official docs, or dataset repo) on this pass. |
| `unverified` | Mentioned in prior notes, a secondary write-up, or a page this pass could not open. Do not treat numbers under this status as measurements. |
| `not-downloaded` | Dataset is linked only. Bytes are not in `data/`. |
| `not-in-repo` | Code, hook, or pipeline is not in this GitHub tree (some earlier sketches lived on Cursor Origin). |
| `separate-track` | Related OpenWall / Unity work that is intentionally not this repo. |

A cell can carry more than one status, for example `known; surveyed; not-downloaded`.

Numbers are copied from the cited page or marked **unknown**. Vendor brochure figures are labeled **vendor claim**. A degree converted from a linear tolerance (for example 1/4 inch in 10 feet) is labeled **derived**, not a published angular spec. Nothing here is a calibrated stud-plumb error budget for a specific phone, scanner, or site.

## Documents

| Doc | What it answers |
| --- | --- |
| [01-sensing-modalities.md](01-sensing-modalities.md) | LiDAR classes versus ~0.12° stud plumb and price. Survey TLS (Focus / RTC360) is the class whose published specs sit inside that angle. Phone, Livox, mapping lidars, BLK360 tilt, and handheld SLAM do not. Also phone, photo, Aura, UWB, and mmWave. |
| [02-software-segmentation-angles.md](02-software-segmentation-angles.md) | Segmentation and viewers, plus a finalized gravity-up stack: scanner inclinometer or DAC, else ARKit or a static IMU, then Open3D angle paint. Floor-plane “level” tools are not the plumb reference. |
| [03-sample-datasets.md](03-sample-datasets.md) | Frame/shell clouds and nearby samples: Rohbau3D, BIMNet, WFC-Dataset, ScanNet++, openBIM, FARO/Leica libs, Polycam self-capture, RefSite3D, ConSLAM. |
| [06-top5-frame-pointclouds.md](06-top5-frame-pointclouds.md) | Ranked five closest public clouds to a residential frame stage, with a still for each. No full light-frame house cloud was found. |
| [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md) | Engineering order for vertical studs on a bare frame: tight boxes, angle versus the floor, then green/yellow/red once a device error band exists. Floor is not gravity. Live buckets are doc 27. The master table is the 2026-09-24 order. |
| [12-stud-seg-design-plan.md](12-stud-seg-design-plan.md) | Curriculum stages 0–7, scorecard, pass bars, capture protocol (iPhone, Mid-360, SKIL BOT/MID/TOP), and what this repo runs. Figures: [images/algo-contenders/INDEX.md](images/algo-contenders/INDEX.md). |
| [13-stud-seg-results-by-day.md](13-stud-seg-results-by-day.md) | Day-by-day algorithm outcome versus ground truth. Seeded with the 2026-09-24 synthetic Open3D runs. Later rows record the one-stud five-finder attempt. |
| [16-one-stud-five-finder-run.md](16-one-stud-five-finder-run.md) | One synthetic 2×4 at 0.05° lean through the five finders, plus rank 6 (pyRANSAC-3D, the doc 17 add). What ran, what was blocked, and the stage 0 bar result. Not a field score. |
| [18-ozpc-ranks4-5-run.md](18-ozpc-ranks4-5-run.md) | Oz_PC re-run of ranks 4 and 5 only, on that same stud. GPU forward passes or an honest block. Stud cells stay empty when the vocabulary has no stud class. |
| [19-phase1-s1-lean-sweep.md](19-phase1-s1-lean-sweep.md) | Phase 1 S1: 25 synthetic dressed 2×4 leans through all six finders. Ranks 1, 2, and 6 pass the stage-0 bars on 25/25. Former rank 3 (CloudCompare), after `CLOUDCOMPARE_EXE` discovery, returns a lean on 25/25 and fails the bars on 25/25 (several faces per stud). That row is now the interactive GUI bucket (doc 27), not a geometry-first finder. Ranks 4 and 5 are controls. Not a field score. |
| [20-synthetic-stud-finetune.md](20-synthetic-stud-finetune.md) | Synthetic stud/clutter fine-tune of rank 4 (PTv3) and rank 5 (RandLA-Net). Not a field score. The 25 phase-1 cards are held out. |
| [24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md) | Bake-off rank 7 is SAM 2 (weights not run on the curriculum VM; Oz_PC tiny pass is doc 25). Rank 1 through a synthetic room. S1b bow and a 2 mm probe recorded as misses. Ladder figures with stud counts: [images/curriculum/INDEX.md](images/curriculum/INDEX.md). PRs #23 and #24 stay parallel. |
| [26-point-sam-and-3d-peers.md](26-point-sam-and-3d-peers.md) | Point-SAM, SAM3D, OpenMask3D, and Segment3D, plus closed-set indoor peers. Input, prompt, and license. Not a measured ranking. |
| [27-four-way-tool-classification.md](27-four-way-tool-classification.md) | Live lock: three geometry-first automated tools, two supervised nets, four foundation models, one interactive viewer (CloudCompare). Former ranks stay as archive labels. |
| [TruePlank paper space](../../papers/trueplank-stud-lean-qa/README.md) | Draft: instance detection and lean assessment of light-frame wood studs from point clouds (BeamWeaver / TruePlank / OpenWall). Class S only. Not a submission. |
| [04-seed-funds.md](04-seed-funds.md) | NSF America’s Seed Fund AR/VR topic and nearby SBIR / construction awards. |
| [05-misc-resources.md](05-misc-resources.md) | Gaussian splats versus clouds, MIT VNAV, the brief’s video and Gemini links, LinkedIn posts, aerial-LiDAR tools. |
| [catalog.json](catalog.json) | Same rows in one JSON file for later tooling. Each table also has a sibling `.json`. |

Industry margin sources and the derived degree conversion are summarized in [../tolerances.md](../tolerances.md).

## What we already know

| Item | Status |
| --- | --- |
| This GitHub repo started as a scaffold. `src/open3d_smoke.py` only prints the Open3D version. `scripts/` has no dataset download helper. `data/` has no clouds. `.gitignore` ignores `*.ply`, `*.las`, `*.laz`. | `known; surveyed` |
| 2026-09-24: `src/openwall_stud/` runs the Open3D baseline on synthetic stages 0, 2, and 3, writes a scorecard, and paints yellow while device ε is unlocked. Figures for that plan are in `docs/research/images/algo-contenders/`. | `known` |
| 2026-09-25: one synthetic 2×4 at 0.05° lean was passed through all five finders. Open3D and PCL ran. CloudCompare RANSAC-SD ran and missed the stage 0 bars. Pointcept and Open3D-ML were blocked on the Linux VM (no GPU, no weights). Rank 6 is pyRANSAC-3D v0.7.0 sequential cuboid, the add Oz approved from doc 17, on that same stud. Write-up: `docs/research/16-one-stud-five-finder-run.md`. Not a field segmenter. | `known` |
| 2026-09-25, Oz_PC: ranks 4 and 5 only, same stud. Write-up: `docs/research/18-ozpc-ranks4-5-run.md`. | `known` |
| 2026-09-25, Oz_PC: phase 1 S1 lean sweep, 25 synthetic clouds, six finders. Write-up: `docs/research/19-phase1-s1-lean-sweep.md`. Ranks 4 and 5 stay controls. CloudCompare RANSAC-SD ran on all 25 scenes from `CLOUDCOMPARE_EXE` / `C:\Program Files\CloudCompare\CloudCompare.exe` and missed the stage 0 bars (several primitives per stud, not one box). The PCL row is the in-process port when the scorecard says the native binary did not run. Not a field segmenter. | `known` |
| 2026-09-25, Oz_PC: ranks 4 and 5 fine-tuned on a larger synthetic stud/clutter set. The 25 phase-1 cards are not the training set. Write-up: `docs/research/20-synthetic-stud-finetune.md`. Synthetic only. | `known` |
| 2026-09-25: SAM 2 added as bake-off rank 7. Weights not installed; stud metrics null. Rank 1 scored on a synthetic 26-stud room (recall 1, yellow). Write-up: `docs/research/24-sam2-rank7-and-curriculum.md`. The corner PRs #23 and #24 are parallel and are not this ladder. | `known` |
| 2026-09-26: four-way lock. Geometry-first automated is Open3D, PCL / NumPy region-grow cuboid, and pyRANSAC-3D. Supervised is Pointcept / PTv3 and Open3D-ML RandLA-Net. Promptable foundation models are Point-SAM, SAM3D, OpenMask3D, and Segment3D. CloudCompare is the interactive GUI (former bake-off rank 3), not a geometry-first automated finder. SAM 2 stays the image-prompted lift. Day-table rows and scorecards are not rewritten. Write-up: `docs/research/27-four-way-tool-classification.md`. | `known` |
| Prior Origin work sketched WFC-Dataset and Rohbau3D download hooks (incomplete), a Pointcept/Rohbau segmentation survey, and an Open3D stud-versus-gravity sketch. Agents named in the root README: `bc-d567e2f1`, `bc-c355a90c` (finished on Origin); `bc-63a01dad` (Origin auth error). Those transcripts were not re-fetched here. | `known; not-in-repo` |
| Capture path of interest: Polycam on iPhone 12 Pro or later Pro/Pro Max LiDAR, export PLY or LAS. Official help (this pass) puts point-cloud export on **Business and Enterprise**, not on the Pro/Basic tiers the earlier note called “Pro tier”. | `known; surveyed` (tier corrected) |
| Earlier note: prefer a Polycam Photo/Detail hybrid for edges. Polycam’s current help distinguishes Space Mode (LiDAR) from non-LiDAR photogrammetry, plus Default / Custom / Cloud processing. A mode literally named “Photo/Detail hybrid” was not found. | `known; unverified` as a product name |
| Earlier note: iPhone alone is not enough for reliable 0.1° on an 8 ft stud, because a ~4.25 mm tip offset is smaller than a ±3–10 mm RMSE at 1.5–2 m. The millimeter offset is **derived** (see tolerances). The ±3–10 mm RMSE figure was **not** found on a primary page in this pass. Peer-reviewed phone-LiDAR errors located here are centimeter-class. Direction (phone LiDAR is coarser than the angle budget) stands; the specific RMSE band does not. | `known` claim; RMSE `unverified` |
| PLY is the practical Open3D input. LAS/LAZ is the interchange/CAD/BIM path. Open3D’s file I/O table does not list LAS/LAZ. Meshes are a different representation; this project wants points for ML isolation. “PSY” is not a Polycam or point-cloud format. | `known; surveyed` |
| LiDAR class for a ~0.12° plumb call is survey TLS (Focus / RTC360). Phone, Livox, mapping spinning lidars, BLK360 G2 tilt (8 arcmin), and handheld SLAM do not clear that spec on the pages read. Current street prices for Focus are unverified. | `surveyed` |
| Gravity-up is the scanner inclinometer or DAC, an ARKit gravity session, or a static IMU. A floor-plane “level” is not the plumb reference. Angle paint is Open3D once Z is up. | `surveyed` |
| Point cloud for measurement and ML; Gaussian splat for view synthesis; mesh for game/CAD engines. Do not treat a splat as a stud metrology cloud. | `known; surveyed` |
| MultiSet / openWall Unity work is a separate track: [openWall](https://github.com/ozguvenc2/openWall). | `known; separate-track` |

## Source rule

Prefer the vendor, paper, or dataset page linked on the row. If a page failed to load, the row says so. Duplicate brief links (Qorvo, TI, the Smart Health article) are cited once.
