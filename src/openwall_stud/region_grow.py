"""Face region growing, then a cuboid from faces that actually touch.

The grow step prefers the system PCL 1.14 ``RegionGrowing`` binary. If that
binary cannot be built or run, a NumPy/Open3D-KDTree port of the same
smoothness test is the fallback and is labeled as such.

Cuboid assembly is local adjacency only. Patches farther apart than the gap
stay separate, including coplanar faces across a bay. The member axis is the
minimal OBB axis from the shared post-step. It is not forced to Z.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import open3d as o3d

from openwall_stud.open3d_baseline import _point_cloud
from openwall_stud.results_by_day import repo_root

SMOOTHNESS_DEG = 10.0
CURVATURE_THRESHOLD = 1.0
NEIGHBOURS = 30
MIN_CLUSTER = 50
ADJACENCY_GAP_M = 0.020
VOXEL_M = 0.008
MIN_MEMBER_POINTS = 100


def grow_labels(points: np.ndarray, work: Path) -> tuple[np.ndarray, dict]:
    """Return a label per point (-1 = unassigned) and a provenance record."""
    work.mkdir(parents=True, exist_ok=True)
    native_labels, native_info = _native_labels(points, work)
    if native_labels is not None:
        return native_labels, native_info
    if sys.platform == "win32" and shutil.which("wsl"):
        wsl_labels, wsl_info = _wsl_labels(points, work, native_info)
        if wsl_labels is not None:
            return wsl_labels, wsl_info
        native_info = wsl_info
    labels = _numpy_labels(points)
    native_info["implementation"] = "numpy_smoothness_region_grow"
    native_info["native_pcl_region_growing"] = False
    native_info["fallback_reason"] = native_info.get("error") or "native PCL binary did not return labels"
    return labels, native_info


def members_from_labels(points: np.ndarray, labels: np.ndarray) -> tuple[list[np.ndarray], dict]:
    """Union clusters whose voxels are within the adjacency gap."""
    ids = sorted(int(value) for value in np.unique(labels) if int(value) >= 0)
    parent = {cluster_id: cluster_id for cluster_id in ids}

    def find(cluster_id: int) -> int:
        while parent[cluster_id] != cluster_id:
            parent[cluster_id] = parent[parent[cluster_id]]
            cluster_id = parent[cluster_id]
        return cluster_id

    clouds: dict[int, np.ndarray] = {}
    for cluster_id in ids:
        selected = points[labels == cluster_id]
        cloud = _point_cloud(selected)
        coarse = cloud.voxel_down_sample(VOXEL_M)
        clouds[cluster_id] = np.asarray(coarse.points) if len(coarse.points) else selected

    print(f"region-grow adjacency: {len(ids)} face clusters", flush=True)
    merges = 0
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            if find(left) == find(right):
                continue
            if _within_gap(clouds[left], clouds[right], ADJACENCY_GAP_M):
                parent[find(right)] = find(left)
                merges += 1

    grouped: dict[int, list[np.ndarray]] = {}
    for cluster_id in ids:
        grouped.setdefault(find(cluster_id), []).append(points[labels == cluster_id])

    members: list[np.ndarray] = []
    dropped = 0
    for chunks in grouped.values():
        stacked = np.vstack(chunks)
        if len(stacked) < MIN_MEMBER_POINTS:
            dropped += 1
            continue
        members.append(stacked)
    info = {
        "n_face_clusters": len(ids),
        "n_unassigned": int(np.count_nonzero(labels < 0)),
        "adjacency_merges": merges,
        "adjacency_gap_m": ADJACENCY_GAP_M,
        "voxel_m": VOXEL_M,
        "min_member_points": MIN_MEMBER_POINTS,
        "n_members": len(members),
        "n_dropped_small_members": dropped,
        "remote_coplanar_merge": False,
        "axis_forced_to_z": False,
    }
    return members, info


def _within_gap(left: np.ndarray, right: np.ndarray, gap_m: float) -> bool:
    if len(left) == 0 or len(right) == 0:
        return False
    query, base = (left, right) if len(left) <= len(right) else (right, left)
    tree = o3d.geometry.KDTreeFlann(_point_cloud(base))
    limit = gap_m * gap_m
    for point in query:
        _, _, dist2 = tree.search_knn_vector_3d(point, 1)
        if dist2 and float(dist2[0]) <= limit:
            return True
    return False


def _native_labels(points: np.ndarray, work: Path) -> tuple[np.ndarray | None, dict]:
    info: dict = {
        "implementation": "pcl::RegionGrowing",
        "native_pcl_region_growing": False,
        "smoothness_deg": SMOOTHNESS_DEG,
        "curvature_threshold": CURVATURE_THRESHOLD,
        "neighbours": NEIGHBOURS,
        "min_cluster": MIN_CLUSTER,
        "viewpoint": [0.0, 0.0, 0.0],
        "viewpoint_note": "Origin is inside this stud, so normals point inward and stay consistent on a face.",
    }
    binary = _ensure_binary(info)
    if binary is None:
        return None, info
    xyz_path = work / "stud.xyz"
    label_path = work / "stud.labels"
    _write_xyz(xyz_path, points)
    proc = subprocess.run(
        [
            str(binary),
            str(xyz_path),
            str(label_path),
            str(SMOOTHNESS_DEG),
            str(CURVATURE_THRESHOLD),
            str(NEIGHBOURS),
            str(MIN_CLUSTER),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    info["binary"] = str(binary)
    info["returncode"] = proc.returncode
    info["stderr"] = (proc.stderr or "")[-2000:]
    if proc.returncode != 0 or not label_path.exists():
        info["error"] = f"pcl_region_grow exited {proc.returncode}"
        return None, info
    labels = np.loadtxt(label_path, dtype=np.int32)
    if labels.ndim == 0:
        labels = np.array([int(labels)], dtype=np.int32)
    if len(labels) != len(points):
        info["error"] = f"label count {len(labels)} != point count {len(points)}"
        return None, info
    info["native_pcl_region_growing"] = True
    info["library"] = "libpcl_segmentation.so.1.14"
    return labels, info


def _ensure_binary(info: dict) -> Path | None:
    binary = repo_root() / "artifacts" / "bin" / "pcl_region_grow"
    if binary.exists():
        return binary
    script = repo_root() / "tools" / "build_pcl_region_grow.sh"
    if not script.exists():
        info["error"] = f"missing build script {script}"
        return None
    proc = subprocess.run(["bash", str(script)], check=False, capture_output=True, text=True)
    info["build_returncode"] = proc.returncode
    info["build_log"] = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-2000:]
    if proc.returncode != 0 or not binary.exists():
        info["error"] = "could not build artifacts/bin/pcl_region_grow"
        return None
    return binary


def _windows_to_wsl(path: Path) -> str:
    text = str(path.resolve())
    if len(text) >= 2 and text[1] == ":":
        return "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return text.replace("\\", "/")


def _wsl_labels(points: np.ndarray, work: Path, info: dict) -> tuple[np.ndarray | None, dict]:
    """Run the user-space PCL 1.14 binary built by tools/wsl_build_pcl_1_14.sh."""
    info = dict(info)
    info["implementation"] = "pcl::RegionGrowing"
    xyz_path = work / "stud.xyz"
    label_path = work / "stud.labels"
    _write_xyz(xyz_path, points)
    xyz_wsl = _windows_to_wsl(xyz_path)
    label_wsl = _windows_to_wsl(label_path)
    command = (
        'export LD_LIBRARY_PATH="$HOME/src/pcl-1.14.1-build/lib:$HOME/pclenv/lib'
        '${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; '
        'BIN="$HOME/bin/pcl_region_grow"; '
        'test -x "$BIN" || exit 127; '
        f'"$BIN" "{xyz_wsl}" "{label_wsl}" '
        f"{SMOOTHNESS_DEG} {CURVATURE_THRESHOLD} {NEIGHBOURS} {MIN_CLUSTER}"
    )
    proc = subprocess.run(
        ["wsl", "-e", "bash", "-lc", command],
        check=False,
        capture_output=True,
        text=True,
    )
    info["binary"] = "wsl:$HOME/bin/pcl_region_grow"
    info["returncode"] = proc.returncode
    info["stdout"] = (proc.stdout or "")[-500:]
    info["stderr"] = (proc.stderr or "")[-2000:]
    if proc.returncode != 0 or not label_path.exists():
        info["error"] = f"wsl pcl_region_grow exited {proc.returncode}"
        return None, info
    labels = np.loadtxt(label_path, dtype=np.int32)
    if labels.ndim == 0:
        labels = np.array([int(labels)], dtype=np.int32)
    if len(labels) != len(points):
        info["error"] = f"label count {len(labels)} != point count {len(points)}"
        return None, info
    info["native_pcl_region_growing"] = True
    info["library"] = "libpcl_segmentation.so.1.14"
    info.pop("error", None)
    return labels, info


def _write_xyz(path: Path, points: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for x_coord, y_coord, z_coord in points:
            handle.write(f"{x_coord:.8f} {y_coord:.8f} {z_coord:.8f}\n")


def _numpy_labels(points: np.ndarray) -> np.ndarray:
    """Smoothness region growing. Curvature is unused because the threshold is 1."""
    cloud = _point_cloud(points)
    tree = o3d.geometry.KDTreeFlann(cloud)
    normals = _oriented_normals(cloud)
    count = len(points)
    knn = np.empty((count, NEIGHBOURS), dtype=np.int32)
    for index in range(count):
        _, indices, _ = tree.search_knn_vector_3d(points[index], NEIGHBOURS)
        row = np.full(NEIGHBOURS, index, dtype=np.int32)
        usable = min(len(indices), NEIGHBOURS)
        row[:usable] = np.asarray(indices[:usable], dtype=np.int32)
        knn[index] = row

    cosine_limit = float(np.cos(np.deg2rad(SMOOTHNESS_DEG)))
    labels = np.full(count, -1, dtype=np.int32)
    cluster_id = 0
    for seed in range(count):
        if labels[seed] != -1:
            continue
        stack = [seed]
        labels[seed] = cluster_id
        size = 1
        while stack:
            current = stack.pop()
            current_normal = normals[current]
            for neighbor in knn[current]:
                if labels[neighbor] != -1:
                    continue
                if float(np.dot(current_normal, normals[neighbor])) < cosine_limit:
                    continue
                labels[neighbor] = cluster_id
                size += 1
                stack.append(int(neighbor))
        if size < MIN_CLUSTER:
            labels[labels == cluster_id] = -1
        else:
            cluster_id += 1
    return labels


def _oriented_normals(cloud: o3d.geometry.PointCloud) -> np.ndarray:
    cloud.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=NEIGHBOURS))
    cloud.orient_normals_towards_camera_location(np.array([0.0, 0.0, 0.0]))
    normals = np.asarray(cloud.normals)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0.0] = 1.0
    return normals / lengths
