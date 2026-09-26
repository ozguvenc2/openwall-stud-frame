# Curriculum ladder figures

Added **2026-09-26**. One iso (or iso plus a front, plan, or bow profile) per step from a single stud to the synthetic room. Rank 1 boxes are the Open3D baseline. Yellow is production paint, because ε is unlocked.

The table, including pass/fail, is in [24-sam2-rank7-and-curriculum.md](../../24-sam2-rank7-and-curriculum.md). Stages 6 and 7 stay stubs. This folder has no picture for them.

Regenerate from the repo root with `python scripts/render_curriculum_figures.py`.

| Level | Studs | Image path | Pass/fail (rank 1) |
| --- | ---: | --- | --- |
| Stage 0 one-stud | 1 | [01-stage0-one-stud.png](01-stage0-one-stud.png) | pass |
| Stage 2 one-stud harder | 1 | [02-stage2-one-stud-harder.png](02-stage2-one-stud-harder.png) | pass |
| Stage 3 mini wall 3 | 3 | [03-stage3-mini-wall-3.png](03-stage3-mini-wall-3.png) | pass |
| Stage 3 mini wall 4 | 4 | [04-stage3-mini-wall-4.png](04-stage3-mini-wall-4.png) | pass |
| Stage 3 mini wall 5 | 5 | [05-stage3-mini-wall-5.png](05-stage3-mini-wall-5.png) | pass |
| Stage 3 probe 2 mm noise | 4 | [06-stage3-probe-2mm-noise.png](06-stage3-probe-2mm-noise.png) | fail |
| S1b bow single | 1 | [07-s1b-bow-single.png](07-s1b-bow-single.png) | fail |
| S1b bow wall | 3 | [08-s1b-bow-wall.png](08-s1b-bow-wall.png) | fail |
| Stage 5 room bay lot62 look | 26 | [09-stage5-room-bay-lot62-look.png](09-stage5-room-bay-lot62-look.png) | pass |
