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
SRC=/home/pegassy/src/openmask3d-pointnet2
rm -rf "$SRC"
mkdir -p /home/pegassy/src
cp -a /mnt/c/Repos/openwall-stud-frame/artifacts/third_party/openmask3d/openmask3d/class_agnostic_mask_computation/third_party/pointnet2 "$SRC"
cd "$SRC"
pip install --no-build-isolation --no-deps .
python -c "import pointnet2; print('POINTNET2_OK', pointnet2.__file__)"
