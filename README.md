# openwall-stud-frame

Residential framing point-cloud work for OpenWall: sample frame-stage homes → semantic stud/frame segmentation → angle vs gravity with industry margins and measurement tolerance (red/green paint).

Temporary GitHub name: `openwall-stud-public-try` (rename later once private-repo + token access is fixed).

## Roadmap status (2026-09-23)

| Step | Goal | Where we are |
|------|------|----------------|
| 1 | Sample point clouds of residential homes in **frame stage** | Research + download scripts/manifests for **WFC-Dataset** and **Rohbau3D**. Full PC downloads were incomplete (worker/auth). Need reproducible local data under `data/`. |
| 2 | Apps that **semantically segment** studs and frame members | Surveyed Pointcept / Rohbau labels. No shipped segmenter in this repo yet; prior sketches lived on Cursor Origin (`oz-stud` / tmp). |
| 3 | **Angle estimation** + red/green vs industry margins + **error tolerance** | Open3D stud-vs-gravity pipeline sketched on Origin. No tolerance UI or pass/fail paint shipped here yet. |

Prior Cursor agents (finished, Origin-backed): `bc-d567e2f1`, `bc-c355a90c`. `bc-63a01dad` errored on Origin auth. This repo is the GitHub home going forward.

## Layout (planned)

```
data/           # sample clouds + manifests (git-lfs or external)
docs/           # datasets, margins, handoff notes
src/            # Open3D / segmentation / angle paint
scripts/        # download + eval helpers
```

## Industry margins

Document exact plumb/level tolerances (and sensor error bars) in `docs/tolerances.md` before painting pass/fail.

## Related

- OpenWall product: https://github.com/ozguvenc2/openWall
