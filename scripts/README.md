# scripts

## classical_segment_obb.py

Runs the classical Open3D pipeline on a local PLY and writes heuristic oriented boxes plus matplotlib PNG views.

Windows, from the repo root, after the venv in the root README:

```bat
python scripts\classical_segment_obb.py --input data\raw\darus-intcdc\preview.ply --out-dir data\raw\darus-intcdc\seg_out
```

Full notes: [`docs/research/09-classical-seg-runbook.md`](../docs/research/09-classical-seg-runbook.md).

---

## paint_gravity_deviation.py

Reads `components.json` produced by `classical_segment_obb.py`, computes the angular deviation of each `upright` or `beam_like` member from plumb or level, and renders four orthographic views with OBB wireframes coloured by pass / warn / fail status.

```
pass  (green)  deviation <= --tolerance-deg          (default 0.12 deg)
warn  (amber)  tolerance  < deviation <= warn-factor x tolerance  (default 0.24 deg)
fail  (red)    deviation  > warn-factor x tolerance
skip  (grey)   label is not upright or beam_like
```

Default tolerance is derived from the Handbook of Construction Tolerances
1/4 in per 10 ft figure: `atan(0.25/120) ~0.12 deg`. See `docs/tolerances.md`.

Minimal run (uses default paths):

```bat
python scripts\paint_gravity_deviation.py
```

With explicit paths:

```bat
python scripts\paint_gravity_deviation.py ^
    --components data\raw\darus-intcdc\seg_out\components.json ^
    --input-ply  data\raw\darus-intcdc\preview.ply ^
    --out-dir    data\raw\darus-intcdc\dev_out ^
    --tolerance-deg 0.12 ^
    --warn-factor   2.0
```

Outputs (all under `--out-dir`, gitignored):

| File | Contents |
| --- | --- |
| `deviation_report.json` | Schema, params, per-component result (id, label, deviation_deg, status). |
| `deviation_report.md`   | Human-readable table + Wrong/Expected/Change notes for the current data gap. |
| `views/dev_front.png`   | Front orthographic view, OBBs coloured by status. |
| `views/dev_side.png`    | Side view. |
| `views/dev_top.png`     | Top-down view. |
| `views/dev_iso.png`     | Isometric view. |

The script does not need `--save-colored-ply` from the segmentation step.
It reads only `components.json` (box geometry + stored cosines) and optionally
the original PLY for a background point cloud.
