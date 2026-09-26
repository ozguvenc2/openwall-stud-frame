"""One Segment3D forward on stage0_2x4_lean0.000.

Hydra 1.3 cannot compose this repo's Hydra 1.0 defaults (the logging
group is a list, and the model group does not land in the composed
config). This smoke loads conf/model/mask3d_no_aux.yaml directly, fills
the interpolations from conf/data/indoor.yaml, and runs the network.
cuML DBSCAN in demo.py is not part of this forward.
"""
import json
import os
import sys
import types
from pathlib import Path

os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

exp = types.ModuleType("hydra.experimental")


def _unused(*_a, **_k):
    raise RuntimeError("unused shim")


exp.initialize = _unused
exp.compose = _unused
sys.modules["hydra.experimental"] = exp

repo = Path("/mnt/c/Repos/openwall-stud-frame/artifacts/third_party/Segment3D")
sys.path.insert(0, str(repo))
os.chdir(repo)

import numpy as np
import open3d as o3d
import torch
from omegaconf import OmegaConf
from demo_utils import prepare_data
import hydra

ckpt = "/mnt/c/Repos/openwall-stud-frame/data/cache/phase_neg1/segment3d/segment3d.ckpt"
model_cfg = OmegaConf.load(repo / "conf/model/mask3d_no_aux.yaml")
parent = OmegaConf.create(
    {
        "general": {"train_on_segments": False},
        "data": {
            "voxel_size": 0.02,
            "in_channels": 3,
            "num_labels": 20,
            "add_raw_coordinates": True,
        },
        "model": model_cfg,
    }
)
OmegaConf.resolve(parent)
OmegaConf.set_struct(parent.model, False)
parent.model._recursive_ = False
net = hydra.utils.instantiate(parent.model)

blob = torch.load(ckpt, map_location="cpu")
state = blob["state_dict"] if isinstance(blob, dict) and "state_dict" in blob else blob
own = net.state_dict()
stripped = {}
for key, value in state.items():
    name = key[6:] if key.startswith("model.") else key
    if name in own and own[name].shape == value.shape:
        stripped[name] = value
missing, unexpected = net.load_state_dict(stripped, strict=False)
net.eval()
device = torch.device("cuda")
net.to(device)

pts = np.load("/mnt/c/Repos/openwall-stud-frame/artifacts/phase_neg1/stage0_points.npy")
mesh = o3d.geometry.TriangleMesh()
mesh.vertices = o3d.utility.Vector3dVector(pts.astype(np.float64))
colors = np.tile(np.array([[0.7, 0.7, 0.7]], dtype=np.float64), (pts.shape[0], 1))
mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
data, point2segment, _full, raw_coordinates, inverse_map = prepare_data(
    parent, mesh, None, device
)
with torch.no_grad():
    outputs = net(data, point2segment=point2segment, raw_coordinates=raw_coordinates)

summary = {
    "tool": "Segment3D",
    "smoke": "yes",
    "n_points": int(pts.shape[0]),
    "loaded": len(stripped),
    "missing": len(missing),
    "unexpected_ckpt": len(state) - len(stripped),
    "device": torch.cuda.get_device_name(0),
    "inverse_map": int(np.asarray(inverse_map).shape[0]),
}
if isinstance(outputs, dict):
    summary["keys"] = sorted(outputs.keys())
    for key in ("pred_logits", "pred_masks"):
        if key in outputs and torch.is_tensor(outputs[key]):
            summary[key] = list(outputs[key].shape)
out = Path("/mnt/c/Repos/openwall-stud-frame/artifacts/phase_neg1/smoke_segment3d.json")
out.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary))
