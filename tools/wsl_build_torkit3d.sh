#!/usr/bin/env bash
set -euo pipefail
export CUDA_HOME=/home/pegassy/cudaenv
export PATH="/home/pegassy/cudaenv/bin:${PATH}"
export TORCH_CUDA_ARCH_LIST=8.9
export FORCE_CUDA=1
export CC=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-cc
export CXX=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-c++
NVROOT=/home/pegassy/mlenv/lib/python3.11/site-packages/nvidia
for name in cublas cudnn cusparse cusolver curand cufft nvtx cuda_runtime; do
  inc="${NVROOT}/${name}/include"
  if [[ -d "$inc" ]]; then
    find "$inc" -maxdepth 1 -type f -exec ln -sfn {} /home/pegassy/cudaenv/include/ \;
  fi
done
export LIBRARY_PATH="$(find "$NVROOT" -type d -name lib | paste -sd: -)"
export LD_LIBRARY_PATH="${LIBRARY_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
nvcc --version
"$CXX" --version
cd /mnt/c/Repos/openwall-stud-frame/artifacts/third_party/Point-SAM/third_party/torkit3d
/home/pegassy/mlenv/bin/pip install --no-build-isolation --no-deps .
echo TORKIT_OK
