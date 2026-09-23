# openwall-stud-frame

Residential framing point-cloud work for OpenWall: sample frame-stage homes → semantic stud/frame segmentation → angle vs gravity with industry margins and measurement tolerance (red/green paint).

Temporary GitHub name: `openwall-stud-public-try` (rename later once private-repo + token access is fixed).

## Roadmap status (2026-09-23)

| Step | Goal | Where we are |
|------|------|----------------|
| 1 | Sample point clouds of residential homes in **frame stage** | Dataset survey is in [`docs/research/03-sample-datasets.md`](docs/research/03-sample-datasets.md). WFC and Rohbau3D are linked only. Download scripts are not in this tree. `data/` is empty. |
| 2 | Apps that **semantically segment** studs and frame members | Tool survey is in [`docs/research/02-software-segmentation-angles.md`](docs/research/02-software-segmentation-angles.md). No segmenter shipped here. Prior Pointcept notes lived on Origin. |
| 3 | **Angle estimation** + red/green vs industry margins + **error tolerance** | Open3D can fit an OBB; gravity comparison is not coded yet. Plumb guidelines are in [`docs/tolerances.md`](docs/tolerances.md). No pass/fail paint yet. |

Prior Cursor agents (finished, Origin-backed): `bc-d567e2f1`, `bc-c355a90c`. `bc-63a01dad` errored on Origin auth. This repo is the GitHub home going forward.

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
- [Table 4 — Seed / grant paths](docs/research/04-seed-funds.md)
- [Misc resources](docs/research/05-misc-resources.md)
- [catalog.json](docs/research/catalog.json)

## Related

- OpenWall product (separate Unity track): https://github.com/ozguvenc2/openWall
