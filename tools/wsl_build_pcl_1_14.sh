#!/usr/bin/env bash
# Build PCL 1.14.1 and tools/pcl_region_grow.cpp inside WSL, without sudo.
# Ubuntu on Oz_PC is 26.04 and apt needs a password, so the compiler, Boost,
# FLANN, and Eigen 3.4 come from a user micromamba prefix.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# This script is stored in the Windows repo. When invoked from WSL, ROOT is
# /mnt/c/... and the compiler should not write the ELF onto the 9p mount.
HOME_DIR="${HOME}"
MM="${HOME_DIR}/.local/bin/micromamba"
ENV_PREFIX="${HOME_DIR}/pclenv"
SRC="${HOME_DIR}/src/pcl-pcl-1.14.1"
EIGEN="${HOME_DIR}/src/eigen-3.4.0"
INSTALL="${HOME_DIR}/pcl-1.14.1-install"
BUILD="${HOME_DIR}/src/pcl-1.14.1-build"
OUT_LINUX="${HOME_DIR}/bin/pcl_region_grow"

if [[ ! -x "$MM" ]]; then
  echo "micromamba missing at $MM" >&2
  exit 1
fi

mkdir -p "${HOME_DIR}/src" "${HOME_DIR}/bin"
if [[ ! -f "${SRC}/CMakeLists.txt" ]]; then
  curl -L --fail -o "${HOME_DIR}/src/pcl-1.14.1.tar.gz" \
    https://github.com/PointCloudLibrary/pcl/archive/refs/tags/pcl-1.14.1.tar.gz
  tar -xzf "${HOME_DIR}/src/pcl-1.14.1.tar.gz" -C "${HOME_DIR}/src"
fi
if [[ ! -d "$SRC" && -d "${HOME_DIR}/src/pcl-1.14.1" ]]; then
  SRC="${HOME_DIR}/src/pcl-1.14.1"
fi
if [[ ! -f "${EIGEN}/Eigen/Core" ]]; then
  curl -L --fail -o "${HOME_DIR}/src/eigen-3.4.0.tar.gz" \
    https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
  tar -xzf "${HOME_DIR}/src/eigen-3.4.0.tar.gz" -C "${HOME_DIR}/src"
fi

export PATH="${ENV_PREFIX}/bin:${PATH}"
export LD_LIBRARY_PATH="${ENV_PREFIX}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

EIGEN_INSTALL="${HOME_DIR}/eigen-3.4-install"
if [[ ! -f "${EIGEN_INSTALL}/share/eigen3/cmake/Eigen3Config.cmake" ]]; then
  cmake -S "$EIGEN" -B "${HOME_DIR}/src/eigen-3.4-build" \
    -DCMAKE_INSTALL_PREFIX="$EIGEN_INSTALL" -G Ninja
  cmake --install "${HOME_DIR}/src/eigen-3.4-build"
fi

cmake -S "$SRC" -B "$BUILD" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$INSTALL" \
  -DEigen3_DIR="${EIGEN_INSTALL}/share/eigen3/cmake" \
  -DBoost_NO_BOOST_CMAKE=ON \
  -DBoost_INCLUDE_DIR="${ENV_PREFIX}/include" \
  -DBOOST_LIBRARYDIR="${ENV_PREFIX}/lib" \
  -DFLANN_ROOT="${ENV_PREFIX}" \
  -DBUILD_visualization=OFF \
  -DBUILD_tools=OFF \
  -DBUILD_apps=OFF \
  -DBUILD_examples=OFF \
  -DBUILD_global_tests=OFF \
  -DBUILD_simulation=OFF \
  -DWITH_VTK=OFF \
  -DWITH_QT=OFF \
  -DWITH_OPENGL=OFF \
  -DWITH_OPENNI=OFF \
  -DWITH_OPENNI2=OFF \
  -DWITH_PCAP=OFF \
  -DWITH_PNG=OFF \
  -DWITH_QHULL=OFF \
  -DWITH_LIBUSB=OFF \
  -DWITH_CUDA=OFF \
  -DWITH_OPENGL=OFF

# gcc 15 fails in pcl_registration (getClassName). Region growing does not need it.
# -j4 stays inside 32 GB. A full nproc build swaps.
cmake --build "$BUILD" --target pcl_ml pcl_segmentation -j4

g++ -O2 -std=c++17 "$ROOT/tools/pcl_region_grow.cpp" -o "$OUT_LINUX" \
  -I"$BUILD/include" \
  -I"$SRC/common/include" \
  -I"$SRC/search/include" \
  -I"$SRC/kdtree/include" \
  -I"$SRC/octree/include" \
  -I"$SRC/sample_consensus/include" \
  -I"$SRC/filters/include" \
  -I"$SRC/features/include" \
  -I"$SRC/segmentation/include" \
  -I"${EIGEN_INSTALL}/include/eigen3" \
  -I"${ENV_PREFIX}/include" \
  -Wl,-rpath,"$BUILD/lib" \
  -Wl,-rpath,"${ENV_PREFIX}/lib" \
  -L"$BUILD/lib" \
  -L"${ENV_PREFIX}/lib" \
  -lpcl_segmentation -lpcl_ml -lpcl_features -lpcl_search -lpcl_kdtree \
  -lpcl_sample_consensus -lpcl_filters -lpcl_octree -lpcl_common \
  -lboost_system \
  -fopenmp

echo "PCL_VERSION_HEADER $(grep -m1 PCL_VERSION_PRETTY "$BUILD/include/pcl/pcl_config.h" || true)"
echo "BUILT $OUT_LINUX"
"$OUT_LINUX" 2>&1 | head -n 1 || true
