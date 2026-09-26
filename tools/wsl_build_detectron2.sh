#!/usr/bin/env bash
set -euo pipefail
export CUDA_HOME=/home/pegassy/cudaenv
export PATH="/home/pegassy/cudaenv/bin:/home/pegassy/mlenv/bin:${PATH}"
export TORCH_CUDA_ARCH_LIST=8.9
export FORCE_CUDA=1
export CC=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-cc
export CXX=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-c++
export MAX_JOBS=2
export LD_LIBRARY_PATH="/home/pegassy/mlenv/lib:/home/pegassy/cudaenv/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
pip install fvcore iopath yacs termcolor tabulate pycocotools cloudpickle portalocker
# Official OpenMask3D pin is detectron2 @ 710e779 (CUDA 11.3 era). Build current
# main against torch 2.14 so sm_89 is a legal target. --no-deps keeps torch.
pip install --no-build-isolation --no-deps \
  'git+https://github.com/facebookresearch/detectron2.git'
python - <<'PY'
from detectron2.projects.point_rend.point_features import point_sample
import torch
print("DETECTRON2_OK", point_sample, torch.cuda.get_device_name(0))
PY
