"""SAM 2 as bake-off rank 7. Scaffold only unless the weights actually run.

SAM 2 segments images and video. It does not read a stud cloud. The path
this module records is:

1. Project the cloud through a known pinhole (a stand-in for a registered
   RGB or depth view). A pure LAS or PLY with no camera is not this input.
2. A mask on that image, if a model produced one, lifts back to the points
   that own those pixels.
3. Those points go to the shared box, angle, and yellow paint.

This process does not download SAM 2 weights and does not invent a mask.
If ``sam2`` or a checkpoint is missing, the rank-7 scorecard stays
``blocked_install`` and the stud metrics stay null.

A separate control projects the generator's own stud labels into the same
camera and lifts that mask. That control is not a SAM 2 result. It only
shows that the projection can hand points to the shared box.

Entrypoint
    python -m openwall_stud.contenders.sam2_mask
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.common import blocked_card
from openwall_stud.lumber import TOLERANCE_DEG
from openwall_stud.open3d_baseline import run_baseline, score_run
from openwall_stud.scorecard import write_scorecard
from openwall_stud.synthetic import Scene, stage0_single_stud

SAM2 = {
    "rank": 7,
    "algorithm_id": "B7",
    "status": "blocked_install",
    "name": "SAM 2 image/video mask, lifted onto points",
}

LICENSE_NAME = "Apache-2.0 (SAM 2 code and checkpoint license; not linked here)"
LICENSE_URL = "https://github.com/facebookresearch/sam2"
PAPER_URL = "https://arxiv.org/abs/2408.00714"


@dataclass(frozen=True)
class Pinhole:
    """Camera in the generator frame. +Z is up. The image y axis points down."""

    eye_m: tuple[float, float, float]
    target_m: tuple[float, float, float]
    up: tuple[float, float, float]
    fov_y_deg: float
    width: int
    height: int


def default_stud_camera() -> Pinhole:
    """Three-quarter view of a stud at the origin, 8 ft tall.

    FOV crops the 8 ft stud to roughly the middle metre. Keep this camera for
    the SAM 2 rank-7 scaffold and for controls that document the crop. Stage0
    SAM3D stud-bar scoring uses ``full_stud_camera`` / ``full_stud_cameras``.
    """
    return Pinhole(
        eye_m=(0.55, -1.15, 1.15),
        target_m=(0.0, 0.0, 1.22),
        up=(0.0, 0.0, 1.0),
        fov_y_deg=42.0,
        width=640,
        height=480,
    )


def full_stud_camera() -> Pinhole:
    """Pulled-back pinhole that keeps the full 8 ft stud inside a 640×480 frame.

    The default scaffold camera crops length to ~1.0 m and fails the stage0
    length bar (≤ 25 mm). This view is the SAM3D / posed-RGB-D stage0 camera.
    """
    return Pinhole(
        eye_m=(1.6, -3.4, 1.22),
        target_m=(0.0, 0.0, 1.22),
        up=(0.0, 0.0, 1.0),
        fov_y_deg=50.0,
        width=640,
        height=480,
    )


def full_stud_cameras() -> tuple[Pinhole, ...]:
    """Front and back full-stud pinholes for multi-view lift / posed RGB-D."""
    front = full_stud_camera()
    back = Pinhole(
        eye_m=(-1.6, 3.4, 1.22),
        target_m=(0.0, 0.0, 1.22),
        up=(0.0, 0.0, 1.0),
        fov_y_deg=50.0,
        width=640,
        height=480,
    )
    return (front, back)


def _basis(camera: Pinhole) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    eye = np.asarray(camera.eye_m, dtype=float)
    target = np.asarray(camera.target_m, dtype=float)
    up = np.asarray(camera.up, dtype=float)
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    cam_up = np.cross(right, forward)
    cam_up = cam_up / np.linalg.norm(cam_up)
    return right, cam_up, forward


def project_points(points: np.ndarray, camera: Pinhole) -> dict[str, np.ndarray]:
    """Pinhole projection. ``z_m`` is depth along the optical axis."""
    right, cam_up, forward = _basis(camera)
    eye = np.asarray(camera.eye_m, dtype=float)
    relative = np.asarray(points, dtype=float) - eye
    x_cam = relative @ right
    y_cam = relative @ cam_up
    z_cam = relative @ forward
    fy = (camera.height / 2.0) / np.tan(np.deg2rad(camera.fov_y_deg) / 2.0)
    fx = fy
    cx = (camera.width - 1) / 2.0
    cy = (camera.height - 1) / 2.0
    valid = z_cam > 1.0e-4
    u = np.full(len(points), np.nan)
    v = np.full(len(points), np.nan)
    u[valid] = fx * (x_cam[valid] / z_cam[valid]) + cx
    v[valid] = cy - fy * (y_cam[valid] / z_cam[valid])
    return {"u": u, "v": v, "z_m": z_cam, "valid": valid, "fx": fx, "fy": fy, "cx": cx, "cy": cy}


def raster_nearest(
    points: np.ndarray,
    part: np.ndarray,
    camera: Pinhole,
) -> dict[str, Any]:
    """Z-buffer. Each pixel keeps the nearest point that lands on it."""
    projected = project_points(points, camera)
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
    depth = np.full(camera.height * camera.width, np.inf)
    winner = np.full(camera.height * camera.width, -1, dtype=np.int32)
    order = np.flatnonzero(inside)
    # Farther points first so a nearer point overwrites the pixel.
    order = order[np.argsort(-z_cam[order])]
    flat = vi[order] * camera.width + ui[order]
    depth[flat] = z_cam[order]
    winner[flat] = order
    occupied = winner >= 0
    part_image = np.full(camera.height * camera.width, -1, dtype=np.int32)
    part_image[occupied] = part[winner[occupied]]
    stud_pixels = int(np.count_nonzero(part_image == 2))
    return {
        "projected": projected,
        "winner": winner,
        "part_image": part_image.reshape(camera.height, camera.width),
        "n_points": int(len(points)),
        "n_projected_inside": int(np.count_nonzero(inside)),
        "n_occupied_pixels": int(np.count_nonzero(occupied)),
        "n_stud_pixels": stud_pixels,
        "n_stud_points": int(np.count_nonzero(part == 2)),
        "intrinsics": {
            "fx": float(projected["fx"]),
            "fy": float(projected["fy"]),
            "cx": float(projected["cx"]),
            "cy": float(projected["cy"]),
            "width": camera.width,
            "height": camera.height,
            "fov_y_deg": camera.fov_y_deg,
        },
    }


def lift_visible_stud_points(raster: dict[str, Any]) -> np.ndarray:
    """Indices of z-buffer winners whose generator part is stud.

    This is the generator mask, not a SAM 2 mask. Occluded points stay out.
    """
    winner = raster["winner"]
    part_flat = raster["part_image"].reshape(-1)
    chosen = winner[part_flat == 2]
    return chosen[chosen >= 0]


def probe_install() -> dict[str, Any]:
    """Record whether this process can run SAM 2. Does not download weights."""
    torch_spec = importlib.util.find_spec("torch")
    sam_spec = importlib.util.find_spec("sam2")
    checkpoint = os.environ.get("SAM2_CHECKPOINT") or ""
    cuda = None
    torch_version = None
    if torch_spec is not None:
        import torch

        torch_version = torch.__version__
        cuda = bool(torch.cuda.is_available())
    ready = bool(sam_spec is not None and checkpoint and Path(checkpoint).is_file() and cuda)
    if sam_spec is None:
        blocker = (
            "SAM 2 is not installed in this process. No mask was produced. "
            "Stud metrics are null."
        )
        short = "sam2 not installed"
    elif not checkpoint or not Path(checkpoint).is_file():
        blocker = (
            "SAM 2 imports, but SAM2_CHECKPOINT is missing or not a file. "
            "No mask was produced. Stud metrics are null."
        )
        short = "SAM2_CHECKPOINT missing"
    elif not cuda:
        blocker = (
            "SAM 2 imports and a checkpoint path is set, but CUDA is not "
            "available. This pass does not run the model on CPU and does not "
            "invent a mask. Stud metrics are null."
        )
        short = "no CUDA for SAM 2"
    else:
        blocker = ""
        short = "ready"
    return {
        "torch_installed": torch_spec is not None,
        "torch_version": torch_version,
        "cuda": cuda,
        "sam2_installed": sam_spec is not None,
        "checkpoint_env": "SAM2_CHECKPOINT",
        "checkpoint_set": bool(checkpoint),
        "checkpoint_is_file": bool(checkpoint) and Path(checkpoint).is_file(),
        "ready": ready,
        "blocker": blocker,
        "blocker_short": short,
    }


def save_part_png(path: Path, part_image: np.ndarray) -> None:
    """False-color part ids. These colors are not the green/yellow/red paint."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 0 floor, 1 plate, 2 stud. Anything else stays dark.
    palette = np.array(
        [
            [0.45, 0.45, 0.48],
            [0.55, 0.42, 0.28],
            [0.20, 0.45, 0.75],
        ],
        dtype=float,
    )
    rgb = np.zeros((*part_image.shape, 3), dtype=float)
    for part_id in range(len(palette)):
        rgb[part_image == part_id] = palette[part_id]
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=100)
    ax.imshow(rgb, interpolation="nearest")
    ax.set_title("Generator part ids through a pinhole. Not a SAM 2 mask. Not QA paint.")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generator_mask_control(scene: Scene, camera: Pinhole | None = None) -> dict[str, Any]:
    """Lift the generator stud pixels and score the shared box.

    Status is a control. The mask is the generator part id, not SAM 2.
    """
    camera = camera or default_stud_camera()
    raster = raster_nearest(scene.points_m, scene.part, camera)
    indices = lift_visible_stud_points(raster)
    lifted = scene.points_m[indices]
    control_scene = Scene(
        name=f"{scene.name}_generator_mask",
        stage=scene.stage,
        points_m=lifted if len(lifted) else np.zeros((0, 3)),
        part=np.full(len(lifted), 2, dtype=np.int32),
        stud_slot=np.zeros(len(lifted), dtype=np.int32),
        studs=list(scene.studs),
        seed=scene.seed,
        spacing_m=scene.spacing_m,
        noise_std_m=scene.noise_std_m,
        description=(
            "Visible stud points from the generator z-buffer. Not a SAM 2 mask. "
            + scene.description
        ),
        meta={"mask_source": "generator_part_id", "not_sam2": True},
    )
    run = run_baseline(control_scene) if len(lifted) else None
    sections = score_run(control_scene, run) if run is not None else None
    return {
        "camera": camera,
        "raster": raster,
        "n_lifted": int(len(indices)),
        "run": run,
        "sections": sections,
        "control_scene": control_scene,
    }


def _camera_record(camera: Pinhole) -> dict[str, Any]:
    return {
        "eye_m": list(camera.eye_m),
        "target_m": list(camera.target_m),
        "up": list(camera.up),
        "fov_y_deg": camera.fov_y_deg,
        "width": camera.width,
        "height": camera.height,
        "frame": "generator Z-up",
    }


def blocked_sam2_card(scene: Scene, raster: dict[str, Any], install: dict[str, Any], camera: Pinhole) -> dict[str, Any]:
    card = blocked_card(
        algorithm_id=SAM2["algorithm_id"],
        algorithm=SAM2["name"],
        rank=7,
        license_name=LICENSE_NAME,
        hardware="not run; no SAM 2 mask on this process",
        failure_modes=[
            "SAM 2 needs an image. A bare LAS or PLY has no mask.",
            "A single view hides the far faces of a stud.",
            "Lifting a mask still needs the shared box. The network does not emit theta or epsilon.",
            "Corner studs that touch in a real bay are not separated by an image mask alone.",
        ],
        blocker=install["blocker"],
        blocker_short=install["blocker_short"],
        scene={
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "n_points": scene.n_points,
            "stage": scene.stage,
        },
        attempt={
            "model": "not executed",
            "paper": PAPER_URL,
            "license_url": LICENSE_URL,
            "install": {key: install[key] for key in install if key not in {"blocker"}},
            "projection": {
                "camera": _camera_record(camera),
                "intrinsics": raster["intrinsics"],
                "n_points": raster["n_points"],
                "n_projected_inside": raster["n_projected_inside"],
                "n_occupied_pixels": raster["n_occupied_pixels"],
                "n_stud_pixels_generator": raster["n_stud_pixels"],
                "n_stud_points": raster["n_stud_points"],
                "note": (
                    "These counts are the pinhole raster of this synthetic cloud. "
                    "They are not a SAM 2 mask IoU and not a stud score."
                ),
            },
        },
    )
    card["stage"] = scene.stage
    card["notes"] = [
        install["blocker"],
        "Bake-off rank 7. The master-table row numbered 7 remains ClearEdge3D EdgeWise and is not this stack.",
        "Device epsilon is unlocked. No production color was painted because no stud box was fit from a SAM 2 mask.",
    ]
    return card


def visible_box_record(points: np.ndarray) -> dict[str, Any] | None:
    """Minimal box of the lifted points, including a box the stud gate drops.

    The scorecard detection stays empty when the length or the section gate
    rejects the cluster. This record is that measurement, not a SAM 2 score.
    ``theta_vs_plus_z_deg`` is a generator-+Z diagnostic of the visible span.
    It is not the scorecard angle reference. A scene with a floor uses the
    fitted floor normal for that reference.
    """
    if len(points) < 20:
        return None
    from openwall_stud.open3d_baseline import (
        MAX_LENGTH_M,
        MAX_UPRIGHT_DEG,
        MIN_LENGTH_M,
        _angle_deg,
        _guess_nominal,
        _obb_segments,
        _point_cloud,
    )

    _, extent, rotation, _ = _obb_segments(_point_cloud(points))
    order = np.argsort(extent)
    ordered = extent[order]
    axis = rotation[:, int(order[-1])]
    theta = _angle_deg(axis, np.array([0.0, 0.0, 1.0]))
    length = float(ordered[2])
    nominal = _guess_nominal(ordered[:2])
    reasons: list[str] = []
    if nominal is None:
        reasons.append("section outside the 15 mm nominal gate")
    if not (MIN_LENGTH_M <= length <= MAX_LENGTH_M):
        reasons.append(f"length {length:.3f} m outside {MIN_LENGTH_M:.1f}–{MAX_LENGTH_M:.1f} m")
    if theta > MAX_UPRIGHT_DEG:
        reasons.append(f"angle {theta:.3f} deg above {MAX_UPRIGHT_DEG:.0f} deg")
    return {
        "extent_sorted_mm": [round(float(value) * 1000.0, 2) for value in ordered],
        "theta_vs_plus_z_deg": round(float(theta), 5),
        "z_min_m": round(float(points[:, 2].min()), 4),
        "z_max_m": round(float(points[:, 2].max()), 4),
        "nominal_guess": nominal,
        "kept_by_stud_gate": not reasons,
        "drop_reasons": reasons,
        "note": (
            "Minimal oriented box of the lifted visible points. "
            "Not a SAM 2 output. A failed gate leaves detection null on this card."
        ),
    }


def control_card(scene: Scene, control: dict[str, Any], png_name: str | None) -> dict[str, Any]:
    sections = control["sections"]
    raster = control["raster"]
    camera = control["camera"]
    visible = visible_box_record(control["control_scene"].points_m)
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": "B7-control",
        "algorithm": "Generator-mask round trip (not SAM 2)",
        "rank": 7,
        "stage": scene.stage,
        "status": "control",
        "epsilon_locked": False,
        "metrics_are_measurements": True,
        "measurement_scope": (
            "synthetic generator mask through one pinhole, then the shared Open3D box. Not SAM 2."
        ),
        "scene": {
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "n_points": scene.n_points,
            "tolerance_deg": round(TOLERANCE_DEG, 5),
        },
        "projection": {
            "camera": _camera_record(camera),
            "intrinsics": raster["intrinsics"],
            "n_stud_pixels": raster["n_stud_pixels"],
            "n_occupied_pixels": raster["n_occupied_pixels"],
            "n_lifted_points": control["n_lifted"],
            "n_stud_points": raster["n_stud_points"],
            "png": png_name,
            "png_colors": "part ids (floor, plate, stud). Not green/yellow/red paint.",
        },
        "visible_box": visible,
        **sections,
        "notes": [
            "The mask is the generator part id on the z-buffer. SAM 2 did not produce it.",
            "Occluded points are not lifted. On this camera the visible length is below the 1.2 m keep gate, so detection stays empty. See visible_box.",
            "Device epsilon is unlocked. Production paint on any box from this control is yellow.",
        ],
    }


def _rgb_from_occupied(part_image: np.ndarray, *, dilate_px: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Wood-colored silhouette. Part ids are not colors.

    Dilation fills single-pixel holes in the z-buffer so the network sees a
    surface. The lift still uses only pixels that own a point.
    """
    occupied = part_image >= 0
    if dilate_px > 0:
        ys, xs = np.nonzero(occupied)
        grown = occupied.copy()
        height, width = occupied.shape
        for dy in range(-dilate_px, dilate_px + 1):
            for dx in range(-dilate_px, dilate_px + 1):
                if dy * dy + dx * dx > dilate_px * dilate_px:
                    continue
                yy = np.clip(ys + dy, 0, height - 1)
                xx = np.clip(xs + dx, 0, width - 1)
                grown[yy, xx] = True
        occupied_draw = grown
    else:
        occupied_draw = occupied
    rgb = np.zeros((*part_image.shape, 3), dtype=np.uint8)
    rgb[:] = (24, 24, 28)
    rgb[occupied_draw] = (186, 140, 90)
    return rgb, occupied_draw


def _prompt_on_stud_pixels(part_image: np.ndarray) -> tuple[float, float] | None:
    """Oracle click: centroid of generator stud pixels. Not a field click."""
    ys, xs = np.nonzero(part_image == 2)
    if ys.size == 0:
        return None
    return float(xs.mean()), float(ys.mean())


def lift_mask_winners(raster: dict[str, Any], mask: np.ndarray) -> np.ndarray:
    """Point indices for z-buffer winners whose pixel is inside ``mask``.

    Empty pixels the mask fills do not invent points. Generator part ids are
    not used as a filter.
    """
    if mask.shape != raster["part_image"].shape:
        raise ValueError(f"mask shape {mask.shape} != {raster['part_image'].shape}")
    winner = raster["winner"]
    chosen = winner[mask.reshape(-1) & (winner >= 0)]
    if chosen.size == 0:
        return chosen
    return np.unique(chosen)


def _load_transformers_sam2(device: str) -> tuple[Any, Any, dict[str, Any]]:
    """Load the tiny image checkpoint already cached, or download it.

    ``facebook/sam2.1-hiera-tiny`` is published as a ``sam2_video`` config.
    Transformers still builds ``Sam2Model`` from it. The load warning is stored.
    """
    import warnings

    from transformers import Sam2Model, Sam2Processor

    model_id = "facebook/sam2.1-hiera-tiny"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        processor = Sam2Processor.from_pretrained(model_id)
        model = Sam2Model.from_pretrained(model_id)
    model = model.to(device)
    model.eval()
    warning_text = [str(item.message) for item in caught if "sam2" in str(item.message).lower()]
    return processor, model, {"model_id": model_id, "load_warnings": warning_text}


def _predict_mask(processor: Any, model: Any, rgb: np.ndarray, column: float, row: float) -> tuple[np.ndarray, dict[str, Any]]:
    import torch
    from PIL import Image

    image = Image.fromarray(rgb, mode="RGB")
    inputs = processor(images=image, input_points=[[[[column, row]]]], return_tensors="pt")
    allowed = {"pixel_values", "input_points", "input_labels", "input_boxes"}
    device = next(model.parameters()).device
    tensors = {key: value.to(device) for key, value in inputs.items() if key in allowed and hasattr(value, "to")}
    with torch.inference_mode():
        outputs = model(**tensors)
    scores = outputs.iou_scores.detach().float().cpu().numpy().reshape(-1)
    choice = int(np.nanargmax(scores))
    pred = outputs.pred_masks.detach().float().cpu().numpy()
    flat = pred.reshape((-1,) + pred.shape[-2:])
    chosen = flat[choice]
    height, width = rgb.shape[:2]
    info: dict[str, Any] = {
        "iou_scores": [round(float(value), 5) for value in scores],
        "chosen_index": choice,
        "chosen_iou": round(float(scores[choice]), 5),
        "low_res_shape": list(chosen.shape),
    }
    try:
        taken = outputs.pred_masks[:, :, choice : choice + 1, ...]
        processed = processor.post_process_masks(taken, inputs["original_sizes"])
        array = processed[0] if isinstance(processed, (list, tuple)) else processed
        if hasattr(array, "detach"):
            array = array.detach().cpu().numpy()
        array = np.squeeze(np.asarray(array))
        if array.shape == (height, width):
            info["resize"] = "post_process_masks"
            return array.astype(bool), info
        info["post_process_shape"] = list(array.shape)
    except Exception as exc:
        info["post_process_error"] = f"{type(exc).__name__}: {exc}"
    ys = np.linspace(0, chosen.shape[0] - 1, height)
    xs = np.linspace(0, chosen.shape[1] - 1, width)
    resized = chosen[np.rint(ys).astype(int)][:, np.rint(xs).astype(int)]
    info["resize"] = "nearest_logits_threshold_0"
    return resized > 0.0, info


def measure_rank7(
    scene: Scene | None = None,
    camera: Pinhole | None = None,
) -> dict[str, Any]:
    """One SAM 2 forward pass on the scaffold camera. Metrics stay null on failure."""
    import time

    scene = scene or stage0_single_stud(nominal="2x4", lean_deg=0.05, seed=2)
    camera = camera or default_stud_camera()
    raster = raster_nearest(scene.points_m, scene.part, camera)
    install = probe_install()
    attempt: dict[str, Any] = {
        "paper": PAPER_URL,
        "license_url": LICENSE_URL,
        "install_probe": {key: install[key] for key in install if key != "blocker"},
        "backend": "transformers.Sam2Model",
        "prompt_source": "centroid of generator stud pixels on this render",
        "image": "occupied z-buffer pixels, one wood color, dilated 1 px. Part ids are not colors.",
    }
    try:
        import torch
    except Exception as exc:
        card = blocked_sam2_card(scene, raster, {
            **install,
            "blocker": f"torch did not import, so SAM 2 was not run. {type(exc).__name__}: {exc}",
            "blocker_short": "torch missing",
            "ready": False,
        }, camera)
        card["attempt"]["ozpc"] = attempt
        return {"card": card, "raster": raster, "rgb": None, "mask": None}

    if not torch.cuda.is_available():
        card = blocked_sam2_card(scene, raster, {
            **install,
            "blocker": (
                f"CUDA is not available (torch {torch.__version__}). "
                "SAM 2 was not run on CPU. Stud metrics are null."
            ),
            "blocker_short": "no CUDA for SAM 2",
            "ready": False,
            "cuda": False,
            "torch_version": torch.__version__,
        }, camera)
        card["attempt"]["ozpc"] = attempt
        return {"card": card, "raster": raster, "rgb": None, "mask": None}

    rgb, _drawn = _rgb_from_occupied(raster["part_image"])
    prompt = _prompt_on_stud_pixels(raster["part_image"])
    if prompt is None:
        card = blocked_sam2_card(scene, raster, {
            **install,
            "blocker": "No generator stud pixel fell in the image, so SAM 2 was not prompted. Metrics are null.",
            "blocker_short": "prompt missed the image",
            "ready": False,
        }, camera)
        return {"card": card, "raster": raster, "rgb": rgb, "mask": None}

    started = time.perf_counter()
    try:
        processor, model, loaded = _load_transformers_sam2("cuda")
        mask, mask_info = _predict_mask(processor, model, rgb, prompt[0], prompt[1])
    except Exception as exc:
        card = blocked_sam2_card(scene, raster, {
            **install,
            "blocker": (
                "SAM 2 weights did not complete a forward pass. "
                f"{type(exc).__name__}: {exc}. Stud metrics are null."
            ),
            "blocker_short": "SAM 2 forward failed",
            "ready": False,
        }, camera)
        card["attempt"]["ozpc"] = attempt | {"error": f"{type(exc).__name__}: {exc}"}
        return {"card": card, "raster": raster, "rgb": rgb, "mask": None}
    runtime_s = time.perf_counter() - started
    indices = lift_mask_winners(raster, mask)
    lifted = scene.points_m[indices] if len(indices) else np.zeros((0, 3))
    control_scene = Scene(
        name=f"{scene.name}_sam2_mask",
        stage=scene.stage,
        points_m=lifted,
        part=np.full(len(lifted), 2, dtype=np.int32),
        stud_slot=np.zeros(len(lifted), dtype=np.int32),
        studs=list(scene.studs),
        seed=scene.seed,
        spacing_m=scene.spacing_m,
        noise_std_m=scene.noise_std_m,
        description="Points lifted from a SAM 2 mask on one synthetic render. " + scene.description,
        meta={"mask_source": "sam2", "not_generator_mask": True},
    )
    run = run_baseline(control_scene) if len(lifted) >= 20 else None
    sections = score_run(control_scene, run) if run is not None else None
    if sections is None:
        from openwall_stud.scorecard import empty_sections

        sections = empty_sections()
        for key in sections:
            sections[key]["note"] = "SAM 2 ran. The lift had fewer than 20 points, so no box was scored."
        sections["paint"]["epsilon_locked"] = False
        sections["cost"]["runtime_s"] = round(runtime_s, 4)
    else:
        sections["cost"]["runtime_s"] = round(runtime_s, 4)
        sections["cost"]["hardware"] = f"CUDA {torch.cuda.get_device_name(0)}"
        sections["cost"]["license"] = "Apache-2.0"
        sections["detection"]["note"] = (
            "One SAM 2 mask on the scaffold camera, lifted through the z-buffer. "
            "Counts are this synthetic render, not a field accuracy."
        )
        from openwall_stud.angle_reference import synthetic_angle_note

        sections["angle"]["note"] = synthetic_angle_note(
            sections["angle"]["reference"],
            extra="The network does not emit the angle. The shared box does.",
        )
    generator_stud = raster["part_image"] == 2
    intersection = int(np.count_nonzero(generator_stud & mask))
    union = int(np.count_nonzero(generator_stud | mask))
    part = scene.part[indices] if len(indices) else np.zeros(0, dtype=np.int32)
    visible = visible_box_record(lifted)
    if visible is not None:
        visible["note"] = (
            "Minimal oriented box of the points lifted from this SAM 2 mask. "
            "The stud-length gate may still drop it, which leaves detection null. "
            "The network does not emit the box."
        )
    card = {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": SAM2["algorithm_id"],
        "algorithm": SAM2["name"],
        "rank": 7,
        "stage": scene.stage,
        "status": "ran",
        "epsilon_locked": False,
        "metrics_are_measurements": True,
        "measurement_scope": (
            "One synthetic pinhole, SAM 2 tiny, z-buffer lift, shared Open3D box. "
            "Not a field image. The prompt is the generator stud centroid."
        ),
        "scene": {
            "name": scene.name,
            "description": scene.description,
            "seed": scene.seed,
            "n_points": scene.n_points,
            "stage": scene.stage,
        },
        "implementation": {
            **loaded,
            "torch": torch.__version__,
            "device": torch.cuda.get_device_name(0),
            "prompt_px": [round(prompt[0], 2), round(prompt[1], 2)],
            "mask": mask_info,
            "pixel_agreement_with_generator_stud": {
                "intersection_px": intersection,
                "union_px": union,
                "ratio": None if union == 0 else round(intersection / union, 4),
                "note": (
                    "Ratio of this mask against generator stud pixels on this render. "
                    "The generator raster is not a field label."
                ),
            },
            "n_mask_pixels": int(mask.sum()),
            "n_generator_stud_pixels": int(generator_stud.sum()),
            "n_lifted_points": int(len(indices)),
            "lifted_part_counts": {
                "floor": int(np.sum(part == 0)),
                "plate": int(np.sum(part == 1)),
                "stud": int(np.sum(part == 2)),
            },
            "camera": _camera_record(camera),
        },
        "visible_box": visible,
        **sections,
        "notes": [
            "Bake-off rank 7. Master-table row 7 remains ClearEdge3D EdgeWise.",
            "Device epsilon is unlocked. Production paint is yellow when a box is kept.",
            "The prompt is the centroid of generator stud pixels. It is not a field click.",
            "facebook/sam2.1-hiera-tiny is a sam2_video config loaded here as Sam2Model. Captured Python warnings are in implementation.load_warnings.",
        ],
    }
    return {"card": card, "raster": raster, "rgb": rgb, "mask": mask, "runtime_s": runtime_s}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SAM 2 rank-7 scaffold on one synthetic stud.")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--stub", action="store_true", help="Write a null card and skip the projection.")
    parser.add_argument(
        "--measure",
        action="store_true",
        help="Run SAM 2 tiny on CUDA if this interpreter can. Writes sam2_rank7_ozpc.json.",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    out_dir = args.out_dir or (root / "artifacts" / "scorecards" / "curriculum")
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.measure:
        measured = measure_rank7()
        card = measured["card"]
        dest = out_dir / "sam2_rank7_ozpc.json"
        write_scorecard(dest, card)
        rgb = measured.get("rgb")
        mask = measured.get("mask")
        if rgb is not None and mask is not None:
            import open3d as o3d

            overlay = rgb.copy()
            overlay[mask] = (0.55 * overlay[mask] + 0.45 * np.array([40, 210, 90])).astype(np.uint8)
            png = out_dir / "sam2_rank7_ozpc_overlay.png"
            o3d.io.write_image(str(png), o3d.geometry.Image(np.ascontiguousarray(overlay)))
        from openwall_stud.results_by_day import append_day_row

        status = card.get("status")
        det = card.get("detection") or {}
        if status == "blocked_install":
            verdict = "blocked_install"
            stored = None
        elif det.get("recall") == 1.0 and det.get("precision") == 1.0:
            verdict = "pass"
            stored = card
        else:
            verdict = "fail"
            stored = card if status == "ran" else None
        append_day_row(
            algorithm="sam2",
            stage=int(card.get("stage") or 0),
            scene=(card.get("scene") or {}).get("name") or "stage0_2x4_lean0.050",
            ground_truth_source="synthetic",
            pass_fail=verdict,
            notes=(
                "Oz_PC SAM 2 tiny on the scaffold camera. "
                "Prompt is the generator stud centroid. "
                f"Day-table bars: {verdict}. Device epsilon unlocked. "
                f"Scorecard: curriculum/{dest.name}."
            ),
            card=stored,
        )
        print(f"sam2 measure status={card.get('status')} -> {dest}")
        return 0 if card.get("status") in {"ran", "blocked_install"} else 1
    if args.stub:
        from openwall_stud.contenders.common import emit_stub, stub_card

        card = stub_card(
            algorithm_id=SAM2["algorithm_id"],
            algorithm=SAM2["name"],
            rank=7,
            license_name=LICENSE_NAME,
            hardware="not run",
            failure_modes=["stub does not project and does not mask"],
            note="Stub. SAM 2 was not imported and the cloud was not projected. Metrics left null.",
        )
        emit_stub(out_dir / "sam2_stub.json", card)
        print(f"sam2 stub -> {out_dir / 'sam2_stub.json'}")
        return 0

    scene = stage0_single_stud(nominal="2x4", lean_deg=0.05, seed=2)
    camera = default_stud_camera()
    raster = raster_nearest(scene.points_m, scene.part, camera)
    install = probe_install()
    png_path = out_dir / "sam2_projection_stage0_partids.png"
    save_part_png(png_path, raster["part_image"])
    blocked = blocked_sam2_card(scene, raster, install, camera)
    write_scorecard(out_dir / "sam2_rank7_blocked.json", blocked)
    control = generator_mask_control(scene, camera)
    write_scorecard(
        out_dir / "sam2_generator_mask_control.json",
        control_card(scene, control, png_path.name),
    )
    print(
        f"sam2 blocked ({install['blocker_short']}); "
        f"generator-mask lifted {control['n_lifted']} points; png {png_path.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
