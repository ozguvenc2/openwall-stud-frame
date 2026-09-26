#!/usr/bin/env bash
set -euo pipefail
export PATH="/home/pegassy/mlenv/bin:${PATH}"
export CUDA_HOME=/home/pegassy/cudaenv
export PATH="/home/pegassy/cudaenv/bin:${PATH}"
export TORCH_CUDA_ARCH_LIST=8.9
export FORCE_CUDA=1
export CC=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-cc
export CXX=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-c++
export MAX_JOBS=2
NVROOT=/home/pegassy/mlenv/lib/python3.11/site-packages/nvidia
export LIBRARY_PATH="$(find "$NVROOT" -type d -name lib | paste -sd: -):/home/pegassy/cudaenv/lib"
export LD_LIBRARY_PATH="${LIBRARY_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
pip install \
  pytorch-lightning python-dotenv pyviz3d scikit-learn loguru open3d \
  h5py torchmetrics gdown plyfile trimesh scipy
# Do not pin an old torch. Build scatter against the installed 2.14 wheel.
if ! python -c "import torch_scatter" 2>/dev/null; then
  pip install --no-build-isolation torch-scatter
fi
python - <<'PY'
import torch, pytorch_lightning, torch_scatter, open3d
print("mask_py", torch.__version__, pytorch_lightning.__version__, torch_scatter.__file__)
PY
echo MASK_PY_OK
