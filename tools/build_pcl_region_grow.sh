#!/usr/bin/env bash
# Build tools/pcl_region_grow.cpp against the system PCL 1.14 shared libraries.
# Headers come from /usr/include or from the libpcl-dev .deb extracted locally.
# The extracted tree is not committed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/tools/pcl_region_grow.cpp"
OUT="$ROOT/artifacts/bin/pcl_region_grow"
INC=""

find_inc() {
  local candidate="$1"
  if [[ -f "$candidate/pcl/segmentation/region_growing.h" ]]; then
    INC="$candidate"
  fi
}

find_inc /usr/include/pcl-1.14
find_inc "$ROOT/artifacts/third_party/pcl/usr/include/pcl-1.14"

if [[ -z "$INC" ]]; then
  echo "PCL headers not installed. Downloading the libpcl-dev deb for headers only."
  STAGE="$ROOT/artifacts/third_party/pcl"
  mkdir -p "$STAGE"
  TMP="$(mktemp -d)"
  (
    cd "$TMP"
    apt-get download libpcl-dev
    dpkg-deb -x libpcl-dev_*.deb "$STAGE"
  )
  rm -rf "$TMP"
  find_inc "$STAGE/usr/include/pcl-1.14"
fi

if [[ -z "$INC" ]]; then
  echo "Could not find pcl/segmentation/region_growing.h" >&2
  exit 1
fi

PCL_LIB=/usr/lib/x86_64-linux-gnu
if [[ ! -e "$PCL_LIB/libpcl_segmentation.so.1.14" ]]; then
  echo "libpcl_segmentation.so.1.14 is not installed." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
# Link the SONAMEs directly. The libpcl-dev linker symlinks are relative and
# do not resolve from an extracted header tree.
g++ -O2 -std=c++17 "$SRC" -o "$OUT" \
  -I"$INC" \
  -I/usr/include/eigen3 \
  -Wl,-rpath,"$PCL_LIB" \
  "$PCL_LIB/libpcl_segmentation.so.1.14" \
  "$PCL_LIB/libpcl_features.so.1.14" \
  "$PCL_LIB/libpcl_search.so.1.14" \
  "$PCL_LIB/libpcl_kdtree.so.1.14" \
  "$PCL_LIB/libpcl_sample_consensus.so.1.14" \
  "$PCL_LIB/libpcl_filters.so.1.14" \
  "$PCL_LIB/libpcl_octree.so.1.14" \
  "$PCL_LIB/libpcl_common.so.1.14" \
  -fopenmp

echo "Built $OUT"
"$OUT" 2>&1 | head -n 1 || true
