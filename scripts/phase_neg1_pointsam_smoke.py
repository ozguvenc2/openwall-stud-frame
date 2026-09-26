"""Point-SAM smoke on stage0_2x4_lean0.000. Run with the WSL mlenv Python."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from safetensors.torch import load_model

ROOT = Path("/mnt/c/Repos/openwall-stud-frame")
POINT_SAM = ROOT / "artifacts" / "third_party" / "Point-SAM"
sys.path.insert(0, str(POINT_SAM))

points = np.load(ROOT / "artifacts" / "phase_neg1" / "stage0_points.npy")
coords = torch.from_numpy(points).float().cuda().unsqueeze(0)
coords = coords - coords.mean(dim=1, keepdim=True)
coords = coords / coords.norm(dim=2, keepdim=True).max()
features = torch.zeros(coords.shape, device=coords.device, dtype=coords.dtype)
gt = torch.ones((1, 1, coords.shape[1]), device=coords.device, dtype=torch.bool)

import os

os.chdir(POINT_SAM)
with initialize_config_dir(config_dir=str(POINT_SAM / "configs"), version_base=None):
    cfg = compose(config_name="large")
model = instantiate(cfg.model)
weight = ROOT / "data" / "cache" / "phase_neg1" / "pointsam" / "model.safetensors"
loaded = load_model(model, str(weight), strict=False)
if isinstance(loaded, tuple):
    missing, unexpected = loaded
else:
    missing, unexpected = loaded.missing_keys, loaded.unexpected_keys
model.cuda().eval()
prompt = coords[:, :1, :]
prompt_labels = torch.ones((1, 1), device=coords.device, dtype=torch.int64)
with torch.no_grad():
    masks, iou_preds = model.predict_masks(coords, features, prompt, prompt_labels)
row = {
    "tool": "Point-SAM",
    "installed": True,
    "version": f"commit 25f4fd9; torch {torch.__version__}; torkit3d CUDA sm_89; weights yuchen0187/Point-SAM model.safetensors",
    "smoke": "yes",
    "detail": (
        f"n_points={int(points.shape[0])} device={torch.cuda.get_device_name(0)} "
        f"mask_shape={tuple(masks.shape)} iou={float(iou_preds.detach().float().max()):.4f} "
        f"missing={len(missing)} unexpected={len(unexpected)}"
    ),
    "error": "",
    "needs_user_at_keyboard": "no",
}
dest = ROOT / "artifacts" / "phase_neg1" / "smoke_pointsam.json"
dest.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
print(json.dumps(row))
