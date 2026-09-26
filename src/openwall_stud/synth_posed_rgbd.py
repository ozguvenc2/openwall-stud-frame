"""Synthetic posed RGB-D for OpenMask3D-style CLIP / open-vocab on stage0.

Writes a ScanNet-style scene folder (color / depth / pose / intrinsic / ply)
from the generator cloud and the full-stud pinholes. Poses are camera-to-world
4×4 in OpenCV axes (X right, Y down, Z forward) so OpenMask3D's
``np.linalg.inv(pose)`` world-to-camera path matches the rasters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

from openwall_stud.contenders.sam2_mask import (
    Pinhole,
    _basis,
    _rgb_from_occupied,
    full_stud_cameras,
    project_points,
    raster_nearest,
)
from openwall_stud.synthetic import Scene


DEPTH_SCALE = 1000.0


def pinhole_c2w_opencv(camera: Pinhole) -> np.ndarray:
    """4×4 camera-to-world with OpenCV axes (right, down, forward)."""
    right, cam_up, forward = _basis(camera)
    down = -cam_up
    eye = np.asarray(camera.eye_m, dtype=float)
    c2w = np.eye(4, dtype=float)
    c2w[:3, 0] = right
    c2w[:3, 1] = down
    c2w[:3, 2] = forward
    c2w[:3, 3] = eye
    return c2w


def pinhole_intrinsics_4x4(camera: Pinhole) -> np.ndarray:
    """4×4 intrinsic matrix matching ``project_points`` (OpenCV image axes)."""
    fy = (camera.height / 2.0) / np.tan(np.deg2rad(camera.fov_y_deg) / 2.0)
    fx = fy
    cx = (camera.width - 1) / 2.0
    cy = (camera.height - 1) / 2.0
    mat = np.eye(4, dtype=float)
    mat[0, 0] = fx
    mat[1, 1] = fy
    mat[0, 2] = cx
    mat[1, 2] = cy
    return mat


def depth_image_m(points_m: np.ndarray, camera: Pinhole) -> np.ndarray:
    """Z-buffer depth (metres) for every pixel; 0 where empty."""
    projected = project_points(points_m, camera)
    u = projected["u"]
    v = projected["v"]
    z_cam = projected["z_m"]
    valid = projected["valid"]
    ui = np.rint(u).astype(np.int32)
    vi = np.rint(v).astype(np.int32)
    inside = (
        valid
        & (ui >= 0)
        & (ui < camera.width)
        & (vi >= 0)
        & (vi < camera.height)
    )
    depth = np.zeros((camera.height, camera.width), dtype=np.float64)
    order = np.flatnonzero(inside)
    if order.size == 0:
        return depth
    order = order[np.argsort(-z_cam[order])]
    depth[vi[order], ui[order]] = z_cam[order]
    return depth


def write_ascii_ply(path: Path, points_m: np.ndarray, rgb: tuple[int, int, int] = (180, 180, 180)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pts = np.asarray(points_m, dtype=np.float64)
    r, g, b = rgb
    with path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("ply\nformat ascii 1.0\n")
        handle.write(f"element vertex {pts.shape[0]}\n")
        handle.write("property float x\nproperty float y\nproperty float z\n")
        handle.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        handle.write("end_header\n")
        for row in pts:
            handle.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f} {r} {g} {b}\n")


def write_posed_rgbd_scene(
    scene: Scene,
    dest: Path,
    *,
    cameras: Iterable[Pinhole] | None = None,
    ply_name: str = "stage0_2x4_lean0.ply",
) -> dict:
    """Write OpenMask3D single-scene layout under ``dest``."""
    cameras = tuple(cameras) if cameras is not None else full_stud_cameras()
    if not cameras:
        raise ValueError("need at least one camera")
    dest = Path(dest)
    color_dir = dest / "color"
    depth_dir = dest / "depth"
    pose_dir = dest / "pose"
    intrinsic_dir = dest / "intrinsic"
    for folder in (color_dir, depth_dir, pose_dir, intrinsic_dir):
        folder.mkdir(parents=True, exist_ok=True)

    from PIL import Image

    records = []
    for index, camera in enumerate(cameras):
        raster = raster_nearest(scene.points_m, scene.part, camera)
        rgb, _ = _rgb_from_occupied(raster["part_image"])
        depth_m = depth_image_m(scene.points_m, camera)
        depth_u16 = np.clip(np.rint(depth_m * DEPTH_SCALE), 0, 65535).astype(np.uint16)
        Image.fromarray(rgb, mode="RGB").save(color_dir / f"{index}.jpg", quality=95)
        Image.fromarray(depth_u16, mode="I;16").save(depth_dir / f"{index}.png")
        c2w = pinhole_c2w_opencv(camera)
        np.savetxt(pose_dir / f"{index}.txt", c2w, fmt="%.8f")
        records.append(
            {
                "index": index,
                "eye_m": list(camera.eye_m),
                "target_m": list(camera.target_m),
                "fov_y_deg": camera.fov_y_deg,
                "width": camera.width,
                "height": camera.height,
                "n_occupied": int(np.count_nonzero(raster["part_image"] >= 0)),
            }
        )

    first = cameras[0]
    intrinsic = pinhole_intrinsics_4x4(first)
    np.savetxt(intrinsic_dir / "intrinsic_color.txt", intrinsic, fmt="%.8f")
    ply_path = dest / ply_name
    write_ascii_ply(ply_path, scene.points_m)

    meta = {
        "scene": scene.name,
        "n_points": int(scene.n_points),
        "n_views": len(cameras),
        "depth_scale": DEPTH_SCALE,
        "intrinsic_resolution": [first.height, first.width],
        "images_ext": ".jpg",
        "depths_ext": ".png",
        "ply": str(ply_path),
        "views": records,
        "note": (
            "Synthetic posed RGB-D for OpenMask3D CLIP. Wood-colored silhouette "
            "renders; not a real capture. OpenCV c2w poses."
        ),
    }
    (dest / "synth_posed_rgbd.json").write_text(
        __import__("json").dumps(meta, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta
