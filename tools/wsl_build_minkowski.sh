#!/usr/bin/env bash
# MinkowskiEngine fork that targets CUDA 12 / PyTorch 2. Official NVIDIA
# pins (torch 1.12 + CUDA 11.3) cannot compile for sm_89.
set -euo pipefail
export CUDA_HOME=/home/pegassy/cudaenv
export PATH="/home/pegassy/cudaenv/bin:/home/pegassy/mlenv/bin:${PATH}"
export TORCH_CUDA_ARCH_LIST=8.9
export ME_FORCE_CUDA=1
export ME_CUDA_HOME=/home/pegassy/cudaenv
export ME_BLAS=openblas
export ME_BLAS_INCLUDE_DIRS=/home/pegassy/blasenv/include
export ME_BLAS_LIBRARY_DIRS=/home/pegassy/blasenv/lib
export CC=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-cc
export CXX=/home/pegassy/cudaenv/bin/x86_64-conda-linux-gnu-c++
export MAX_JOBS=2
NVROOT=/home/pegassy/mlenv/lib/python3.11/site-packages/nvidia
export LIBRARY_PATH="$(find "$NVROOT" -type d -name lib | paste -sd: -):/home/pegassy/blasenv/lib:/home/pegassy/cudaenv/lib"
export LD_LIBRARY_PATH="${LIBRARY_PATH}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
src_inc=/home/pegassy/cudaenv/targets/x86_64-linux/include
dst_inc=/home/pegassy/cudaenv/include
for name in "$src_inc"/*; do
  base=$(basename "$name")
  if [[ ! -e "$dst_inc/$base" ]]; then
    ln -sfn "$name" "$dst_inc/$base"
  fi
done
# The link line only searches CUDA_HOME/lib. The pip nvidia wheels and the
# OpenBLAS prefix live elsewhere, so publish the sonames the linker asks for.
libdst=/home/pegassy/cudaenv/lib
mkdir -p "$libdst"
while IFS= read -r so; do
  ln -sfn "$so" "$libdst/$(basename "$so")"
done < <(find "$NVROOT" /home/pegassy/blasenv/lib -name 'lib*.so*' \( -type f -o -type l \) 2>/dev/null)
for so in "$libdst"/lib*.so.*; do
  [[ -e "$so" ]] || continue
  unversioned="${so%.so.*}.so"
  # libfoo.so.12.1 -> strip only the version after .so
  unversioned=$(printf '%s' "$so" | sed -E 's/\.so\..+$/.so/')
  if [[ ! -e "$unversioned" ]]; then
    ln -sfn "$so" "$unversioned"
  fi
done
cd /home/pegassy/src/MinkowskiEngine
# Keep build/ so a failed link does not recompile the CUDA objects.
rm -rf *.egg-info
/home/pegassy/mlenv/bin/pip install -v --no-build-isolation --no-deps .
/home/pegassy/mlenv/bin/python - <<'PY'
import torch
import MinkowskiEngine as ME
print("ME_IMPORT_OK", ME.__file__)
coords = torch.IntTensor([[0, 0, 0, 0], [0, 1, 0, 0]]).to("cuda")
feats = torch.ones(2, 1).to("cuda")
st = ME.SparseTensor(features=feats, coordinates=coords)
conv = ME.MinkowskiConvolution(1, 2, kernel_size=3, dimension=3).cuda()
out = conv(st)
print("ME_FORWARD_OK", tuple(out.F.shape), torch.cuda.get_device_name(0))
PY
echo MINKOWSKI_OK
