# Stud-head checkpoints (not published semantic weights)

These files are **separate 2-class (clutter / stud) heads** trained on synthetic
one-beam / stud+floor clouds. They are **not** a rewrite of the published
BIMStruct3D or S3DIS semantic checkpoints.

| File | Stack | Notes |
| --- | --- | --- |
| `pointcept_stud_2class.pth` | Pointcept PTv3 + new MLP head | BIMStruct backbone stays in `data/cache/bimstruct3d/` (gitignored). |
| `randlanet_stud_2class.pth` | Open3D-ML RandLA-Net 2-class | S3DIS zoo file stays in `data/cache/open3d-ml/` (gitignored). |
| `*_train_log.json` | train history | Short train for stage0 inference. **Not a full bake-off train.** |

Older copies under `artifacts/weights/finetune/` are left untouched for archive.
Loaders prefer this directory, then fall back to the legacy path.
