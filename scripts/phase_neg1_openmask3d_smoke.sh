#!/usr/bin/env bash
set -euo pipefail
export LD_LIBRARY_PATH="/home/pegassy/mlenv/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OMP_NUM_THREADS=8
# Torch 2.6+ defaults torch.load to weights_only=True. The OpenMask3D
# checkpoint is the authors' Drive file and the loader does not pass the flag.
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
PY=/home/pegassy/mlenv/bin/python
ROOT=/mnt/c/Repos/openwall-stud-frame
PLY="$ROOT/artifacts/phase_neg1/stage0_2x4_lean0.ply"
"$PY" - <<PY
import numpy as np
pts = np.load("$ROOT/artifacts/phase_neg1/stage0_points.npy").astype(np.float32)
path = "$PLY"
with open(path, "w", encoding="ascii") as f:
    f.write("ply\\nformat ascii 1.0\\n")
    f.write(f"element vertex {pts.shape[0]}\\n")
    f.write("property float x\\nproperty float y\\nproperty float z\\n")
    f.write("property uchar red\\nproperty uchar green\\nproperty uchar blue\\nend_header\\n")
    for p in pts:
        f.write(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f} 180 180 180\\n")
print("ply", pts.shape[0])
PY
cd "$ROOT/artifacts/third_party/openmask3d/openmask3d/class_agnostic_mask_computation"
"$PY" get_masks_single_scene.py \
  general.scene_path="$PLY" \
  general.checkpoint="$ROOT/data/cache/phase_neg1/openmask3d/mask_module_arbitrary.ckpt" \
  general.mask_save_dir="$ROOT/artifacts/phase_neg1/openmask3d_masks" \
  general.train_mode=false \
  general.experiment_name=phase_neg1_stud \
  +model._recursive_=false \
  data.test_mode=test
