"""SAM3D smoke: Yang et al. Pointcept/SegmentAnything3D, not Meta SAM 3D Bodies.

The published entry point lifts 2D SAM masks into a cloud. This scene is a
bare stud, so the image is the repo's existing stud pinhole
(openwall_stud.contenders.sam2_mask.default_stud_camera). One SAM ViT-H
forward runs on that raster. The 3D neighbor op is pointops, built in WSL
by tools/wsl_build_sam3d_pointops.sh and smoked by
scripts/phase_neg1_pointops_smoke.py. This Windows script is only the 2D half.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.sam2_mask import (  # noqa: E402
    _prompt_on_stud_pixels,
    _rgb_from_occupied,
    default_stud_camera,
    raster_nearest,
)
from openwall_stud.synthetic import stage0_single_stud  # noqa: E402


def main() -> int:
    import torch
    from segment_anything import SamPredictor, sam_model_registry

    cloud = stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)
    camera = default_stud_camera()
    raster = raster_nearest(cloud.points_m, cloud.part, camera)
    rgb, _occupied = _rgb_from_occupied(raster["part_image"])
    prompt = _prompt_on_stud_pixels(raster["part_image"])
    if prompt is None:
        raise SystemExit("stud pixels did not project")
    weight = ROOT / "data" / "cache" / "phase_neg1" / "sam" / "sam_vit_h_4b8939.pth"
    sam = sam_model_registry["vit_h"](checkpoint=str(weight))
    sam.to(device="cuda")
    predictor = SamPredictor(sam)
    predictor.set_image(rgb)
    x_px, y_px = prompt
    masks, scores, _logits = predictor.predict(
        point_coords=np.array([[x_px, y_px]], dtype=np.float32),
        point_labels=np.array([1], dtype=np.int32),
        multimask_output=True,
    )
    row = {
        "tool": "SAM3D",
        "identity": "Pointcept/SegmentAnything3D yang2023sam3d",
        "installed": True,
        "version": f"segment-anything 1.0; torch {torch.__version__}; checkpoint sam_vit_h_4b8939.pth",
        "smoke": "yes",
        "detail": (
            f"n_points={cloud.n_points} image={rgb.shape} prompt_px=({x_px:.1f},{y_px:.1f}) "
            f"masks={int(masks.shape[0])} best_score={float(scores.max()):.4f} "
            f"device={torch.cuda.get_device_name(0)}. "
            "2D SAM ViT-H forward on the existing stud pinhole. "
            "3D pointops knn is the WSL smoke, not this process."
        ),
        "error": "",
        "needs_user_at_keyboard": "no",
    }
    out = ROOT / "artifacts" / "phase_neg1"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "smoke_sam3d.json"
    dest.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
