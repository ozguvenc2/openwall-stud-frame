#!/usr/bin/env bash
set -euo pipefail
export CUDA_HOME=/home/pegassy/cudaenv
export PATH="/home/pegassy/cudaenv/bin:/home/pegassy/mlenv/bin:${PATH}"
export TORCH_CUDA_ARCH_LIST=8.9
export FORCE_CUDA=1
export CC=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-cc
export CXX=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-c++
export MAX_JOBS=4
# conda cuda-nvcc splits headers: cuda_runtime_api.h lives in include/, while
# crt/, nv/, cub/, and thrust live under targets/x86_64-linux/include/.
src_inc=/home/pegassy/cudaenv/targets/x86_64-linux/include
dst_inc=/home/pegassy/cudaenv/include
for name in "$src_inc"/*; do
  base=$(basename "$name")
  if [[ ! -e "$dst_inc/$base" ]]; then
    ln -sfn "$name" "$dst_inc/$base"
  fi
done
NVROOT=/home/pegassy/mlenv/lib/python3.11/site-packages/nvidia
export LIBRARY_PATH="$(find "$NVROOT" -type d -name lib | paste -sd: -)"
export LD_LIBRARY_PATH="${LIBRARY_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
SRC=/home/pegassy/src/sam3d-pointops
rm -rf "$SRC"
mkdir -p /home/pegassy/src
cp -a /mnt/c/Repos/openwall-stud-frame/artifacts/third_party/SegmentAnything3D/libs/pointops "$SRC"
cd "$SRC"
/home/pegassy/mlenv/bin/pip install ninja --quiet
/home/pegassy/mlenv/bin/pip install --no-build-isolation --no-deps .
/home/pegassy/mlenv/bin/python - <<'PY'
import pointops
print("POINTOPS_IMPORT_OK", pointops.__file__)
PY
echo POINTOPS_OK
