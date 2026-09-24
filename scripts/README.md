# scripts

`classical_segment_obb.py` runs the classical Open3D pipeline on a local PLY and writes heuristic oriented boxes plus matplotlib PNG views.

Windows, from the repo root, after the venv in the root README:

```bat
python scripts\classical_segment_obb.py --input data\raw\darus-intcdc\preview.ply --out-dir data\raw\darus-intcdc\seg_out
```

Full notes: [`docs/research/09-classical-seg-runbook.md`](../docs/research/09-classical-seg-runbook.md).
