# openwall-stud-frame

Residential framing point-cloud work for OpenWall: sample frame-stage homes → semantic stud/frame segmentation → angle vs gravity with industry margins and measurement tolerance (red/green paint).

Temporary GitHub name: `openwall-stud-public-try` (rename later once private-repo + token access is fixed).

## Start here (2026-09-24)

Four notes for the sheathing-stage house in the site photos, and for the “colors and boxes” editor:

1. **Editor.** Open3D `draw_geometries` is the interactive view (colored points + oriented wire boxes). CloudCompare is the LAS/E57 browser. Unity is later, for a baked-color review, and no Asset Store package found draws per-member boxes. [13](docs/research/13-open3d-interactive-obb-viewer.md) · [12](docs/research/12-unity-pointcloud-viz-summary.md)
2. **Drone + wood segmentation.** No LinkedIn post found that is both aerial photogrammetry and residential stud segmentation. Named stacks are Metashape → CloudCompare / PointNet++ / PyVista, DroneDeploy’s closed trade tag, and forestry models that segment trees. [10](docs/research/10-drone-wood-photogrammetry-seg.md)
3. **Residential frame scans.** A public cloud of a US light-frame house at sheathing stage (OSB, open studs, porch trusses) was not found. New near-misses: a 1:6-scale NHERI light-frame lidar set, synthetic Rosenheim wall clouds, and carpentry mock-ups. IntCDC remains the closest real timber building scan, and it is not this house. [11](docs/research/11-residential-light-frame-scans.md)
4. **Unity summary.** PR #4 (branch `cursor/blender-unity-pointcloud-1ad9`, not merged) already picked Point Cloud Viewer and Tools 3 for viewing and found no Unity segmenter. [12](docs/research/12-unity-pointcloud-viz-summary.md)

## Roadmap status (2026-09-23)

| Step | Goal | Where we are |
|------|------|----------------|
| 1 | Sample point clouds of residential homes in **frame stage** | Dataset survey is in [`docs/research/03-sample-datasets.md`](docs/research/03-sample-datasets.md). Ranked shortlist: [`docs/research/06-top5-frame-pointclouds.md`](docs/research/06-top5-frame-pointclouds.md). A 2026-09-24 hunt for a US sheathing-stage house is in [`docs/research/11-residential-light-frame-scans.md`](docs/research/11-residential-light-frame-scans.md). No full light-frame house cloud was found. Clouds are linked only. Download scripts are not in this tree. `data/` is empty. |
| 2 | Apps that **semantically segment** studs and frame members | Tool survey is in [`docs/research/02-software-segmentation-angles.md`](docs/research/02-software-segmentation-angles.md). No segmenter shipped here. Prior Pointcept notes lived on Origin. |
| 3 | **Angle estimation** + red/green vs industry margins + **error tolerance** | Open3D can fit an OBB; gravity comparison is not coded yet. Plumb guidelines are in [`docs/tolerances.md`](docs/tolerances.md). No pass/fail paint yet. |

Prior Cursor agents (finished, Origin-backed): `bc-d567e2f1`, `bc-c355a90c`. `bc-63a01dad` errored on Origin auth. This repo is the GitHub home going forward.

## Python setup (Open3D)

Near-term segmentation and angle code uses Open3D. `requirements.txt` pins `open3d==0.20.0` (PyPI, 16 Sep 2026). That wheel supports Python 3.10–3.14. On Windows it is the standard PyPI wheel, not the separate Windows CUDA preview posted on GitHub.

From the repo root in **PowerShell** or **cmd**:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python src\open3d_smoke.py
```

The smoke script imports Open3D and prints the version. It does not download a point cloud. `.venv/` is gitignored.

`pyproject.toml` lists the same pin. The documented install on Windows is `pip install -r requirements.txt`.

## Layout (planned)

```
data/           # sample clouds + manifests (git-lfs or external)
docs/           # datasets, margins, handoff notes
src/            # Open3D / segmentation / angle paint
scripts/        # download + eval helpers
```

## Industry margins

Sourced plumb guidelines and the derived ~0.12° conversion are in [`docs/tolerances.md`](docs/tolerances.md). A measured sensor error bar is still open. Do not paint pass/fail until that bar exists.

## Research docs

Literature and vendor survey (2026-09-23). Numbers are cited or marked unknown. Large datasets are linked, not stored in git.

- [Index and status-column legend](docs/research/README.md)
- [Table 1 — Sensing modalities](docs/research/01-sensing-modalities.md) (LiDAR classes vs ~0.12° plumb; survey TLS is the viable class)
- [Table 2 — Segmentation and angles](docs/research/02-software-segmentation-angles.md) (gravity-up, then Open3D angle paint)
- [Table 3 — Sample datasets](docs/research/03-sample-datasets.md)
- [Top 5 frame-stage point clouds](docs/research/06-top5-frame-pointclouds.md)
- [Table 4 — Seed / grant paths](docs/research/04-seed-funds.md)
- [Misc resources](docs/research/05-misc-resources.md)
- [Drone photogrammetry and wood segmentation](docs/research/10-drone-wood-photogrammetry-seg.md)
- [Residential light-frame scans](docs/research/11-residential-light-frame-scans.md)
- [Unity point-cloud viz summary](docs/research/12-unity-pointcloud-viz-summary.md)
- [Open3D interactive boxes](docs/research/13-open3d-interactive-obb-viewer.md)
- [catalog.json](docs/research/catalog.json)

## Related

- OpenWall product (separate Unity track): https://github.com/ozguvenc2/openWall
