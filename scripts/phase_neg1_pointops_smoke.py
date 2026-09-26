"""One pointops knn on the stage0 stud cloud. SAM3D's 3D merge uses this op."""
import json
from pathlib import Path

import numpy as np
import torch
import pointops

root = Path("/mnt/c/Repos/openwall-stud-frame/artifacts/phase_neg1")
pts = np.load(root / "stage0_points.npy").astype(np.float32)
xyz = torch.from_numpy(pts).cuda().contiguous()
offset = torch.tensor([xyz.shape[0]], device="cuda", dtype=torch.int32)
idx, dist = pointops.knn_query(8, xyz, offset)
out = {
    "tool": "SAM3D-pointops",
    "smoke": "yes",
    "n_points": int(xyz.shape[0]),
    "idx_shape": list(idx.shape),
    "dist_shape": list(dist.shape),
    "mean_dist": float(dist[:, 1:].mean().item()),
    "device": torch.cuda.get_device_name(0),
    "pointops": pointops.__file__,
}
(root / "smoke_pointops.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out))
