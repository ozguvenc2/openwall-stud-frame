# OpenWall stud-frame research

Research date: **2026-09-23**. Scope: residential frame-stage QA — sample point clouds, semantic stud/beam segmentation, angle versus gravity, red/green against industry margins, with measurement-error tolerance. Near-term stack is Python + Open3D. Unity is optional later for visualization or XR. XREAL Aura is an AR display, not the capture scanner.

No multi-gigabyte datasets were downloaded into this repo. Large clouds stay behind the access URLs in [03-sample-datasets.md](03-sample-datasets.md).

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
| [01-sensing-modalities.md](01-sensing-modalities.md) | Phone LiDAR, TLS, photogrammetry, stereo/VIO (Aura-class), UWB, TI mmWave, and related sensors versus ~0.1–0.12° stud plumb. |
| [02-software-segmentation-angles.md](02-software-segmentation-angles.md) | Tools that segment structure, fit oriented boxes, or report angles. Includes Open3D, Unity point-cloud plugins, and Blender point-cloud support. |
| [03-sample-datasets.md](03-sample-datasets.md) | Frame/shell clouds and nearby samples: Rohbau3D, BIMNet, WFC-Dataset, ScanNet++, openBIM, FARO/Leica libs, Polycam self-capture. |
| [04-seed-funds.md](04-seed-funds.md) | NSF America’s Seed Fund AR/VR topic and nearby SBIR / construction awards. |
| [05-misc-resources.md](05-misc-resources.md) | Gaussian splats versus clouds, MIT VNAV, the brief’s video and Gemini links, LinkedIn posts, aerial-LiDAR tools. |
| [catalog.json](catalog.json) | Same rows in one JSON file for later tooling. Each table also has a sibling `.json`. |

Industry margin sources and the derived degree conversion are summarized in [../tolerances.md](../tolerances.md).

## What we already know

| Item | Status |
| --- | --- |
| This GitHub repo is a scaffold. `src/` and `scripts/` have no pipeline yet. `data/` has no clouds. `.gitignore` ignores `*.ply`, `*.las`, `*.laz`. | `known; surveyed` |
| Prior Origin work sketched WFC-Dataset and Rohbau3D download hooks (incomplete), a Pointcept/Rohbau segmentation survey, and an Open3D stud-versus-gravity sketch. Agents named in the root README: `bc-d567e2f1`, `bc-c355a90c` (finished on Origin); `bc-63a01dad` (Origin auth error). Those transcripts were not re-fetched here. | `known; not-in-repo` |
| Capture path of interest: Polycam on iPhone 12 Pro or later Pro/Pro Max LiDAR, export PLY or LAS. Official help (this pass) puts point-cloud export on **Business and Enterprise**, not on the Pro/Basic tiers the earlier note called “Pro tier”. | `known; surveyed` (tier corrected) |
| Earlier note: prefer a Polycam Photo/Detail hybrid for edges. Polycam’s current help distinguishes Space Mode (LiDAR) from non-LiDAR photogrammetry, plus Default / Custom / Cloud processing. A mode literally named “Photo/Detail hybrid” was not found. | `known; unverified` as a product name |
| Earlier note: iPhone alone is not enough for reliable 0.1° on an 8 ft stud, because a ~4.25 mm tip offset is smaller than a ±3–10 mm RMSE at 1.5–2 m. The millimeter offset is **derived** (see tolerances). The ±3–10 mm RMSE figure was **not** found on a primary page in this pass. Peer-reviewed phone-LiDAR errors located here are centimeter-class. Direction (phone LiDAR is coarser than the angle budget) stands; the specific RMSE band does not. | `known` claim; RMSE `unverified` |
| PLY is the practical Open3D input. LAS/LAZ is the interchange/CAD/BIM path. Open3D’s file I/O table does not list LAS/LAZ. Meshes are a different representation; this project wants points for ML isolation. “PSY” is not a Polycam or point-cloud format. | `known; surveyed` |
| Point cloud for measurement and ML; Gaussian splat for view synthesis; mesh for game/CAD engines. Do not treat a splat as a stud metrology cloud. | `known; surveyed` |
| MultiSet / openWall Unity work is a separate track: [openWall](https://github.com/ozguvenc2/openWall). | `known; separate-track` |

## Source rule

Prefer the vendor, paper, or dataset page linked on the row. If a page failed to load, the row says so. Duplicate brief links (Qorvo, TI, the Smart Health article) are cited once.
