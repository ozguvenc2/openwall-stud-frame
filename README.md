# openwall-stud-frame

Residential framing point-cloud work for OpenWall: sample frame-stage homes → semantic stud/frame segmentation → angle vs gravity with industry margins and measurement tolerance (red/green paint).

Temporary GitHub name: `openwall-stud-public-try` (rename later once private-repo + token access is fixed).

## Roadmap status (2026-09-23)

| Step | Goal | Where we are |
|------|------|----------------|
| 1 | Sample point clouds of residential homes in **frame stage** | Dataset survey is in [`docs/research/03-sample-datasets.md`](docs/research/03-sample-datasets.md). Ranked shortlist: [`docs/research/06-top5-frame-pointclouds.md`](docs/research/06-top5-frame-pointclouds.md). No full light-frame house cloud was found. Clouds are linked only. Download scripts are not in this tree. `data/` is empty. |
| 2 | Apps that **semantically segment** studs and frame members | Tool survey is in [`docs/research/02-software-segmentation-angles.md`](docs/research/02-software-segmentation-angles.md). Algorithm ranking for vertical studs is in [`docs/research/11-stud-segmentation-algorithm-ranking.md`](docs/research/11-stud-segmentation-algorithm-ranking.md). No segmenter shipped here. |
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
- [Stud segmentation algorithm ranking](docs/research/11-stud-segmentation-algorithm-ranking.md) (vertical studs, floor-relative angle, green/yellow/red)
- [Table 4 — Seed / grant paths](docs/research/04-seed-funds.md)
- [Misc resources](docs/research/05-misc-resources.md)
- [catalog.json](docs/research/catalog.json)

## Related

- OpenWall product (separate Unity track): https://github.com/ozguvenc2/openWall
