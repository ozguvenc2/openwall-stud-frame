"""Short Pointcept head fine-tune for floor / wall_a / wall_b.

The backbone stays the frozen BIMStruct3D PT-v3m1. Only the new 3-class
MLP is trained. The canonical SKIL-mean corner (seed 25) is not in this
set. This is not a stud fine-tune. Budget: 8 clouds, 12 epochs. A 2-epoch
head left the two walls merged, so this pass is the longer of the two tries.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import openwall_stud.finetune_pointcept as fp  # noqa: E402
from openwall_stud.phase2_corner import CLASS_NAMES, train_variants, synthesize_corner  # noqa: E402

fp.NUM_CLASSES = 3
fp.CLASS_NAMES = CLASS_NAMES

OUT = ROOT / "artifacts" / "weights" / "finetune" / "pointcept_corner_3class.pth"
LOG = ROOT / "artifacts" / "scorecards" / "phase2_corner_neural" / "corner_pointcept_train.json"


def normals_of(points: np.ndarray) -> np.ndarray:
    import open3d as o3d

    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    cloud.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamKNN(knn=24))
    return np.asarray(cloud.normals, dtype=np.float32)


def main() -> None:
    import torch

    specs = train_variants()
    clouds = []
    for spec in specs:
        scene = synthesize_corner(
            lean_a_deg=spec["lean_a_deg"],
            lean_b_deg=spec["lean_b_deg"],
            noise_std_m=spec["noise_std_m"],
            seed=spec["seed"],
            name=spec["name"],
        )
        clouds.append(scene)
        print(spec["name"], "n", len(scene["points"]), flush=True)

    model = fp.build_model("cuda")
    copied = fp.load_bimstruct_backbone(model)
    trainable = fp.set_trainable(model, train_decoder=False)
    weight = torch.tensor([1.0, 1.5, 1.5], device="cuda")
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=1e-3, weight_decay=1e-4)
    started = time.perf_counter()
    losses = []
    for epoch in range(12):
        order = np.random.default_rng(epoch).permutation(len(clouds))
        epoch_loss = []
        for index in order:
            scene = clouds[int(index)]
            batch = fp.collate_cloud(scene["points"], scene["labels"], normals_of(scene["points"]))
            loss = fp.train_step(model, optimizer, batch, weight, grad_backbone=False)
            epoch_loss.append(loss)
            print(f"epoch {epoch} cloud {index} loss {loss:.4f}", flush=True)
        losses.append(float(np.mean(epoch_loss)))
    decoder_names = fp.set_trainable(model, train_decoder=True)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=1e-4, weight_decay=1e-4)
    decoder_losses = []
    for epoch in range(2):
        order = np.random.default_rng(100 + epoch).permutation(len(clouds))
        epoch_loss = []
        for index in order:
            scene = clouds[int(index)]
            batch = fp.collate_cloud(scene["points"], scene["labels"], normals_of(scene["points"]))
            loss = fp.train_step(model, optimizer, batch, weight, grad_backbone=True)
            epoch_loss.append(loss)
            print(f"decoder {epoch} cloud {index} loss {loss:.4f}", flush=True)
        decoder_losses.append(float(np.mean(epoch_loss)))
    runtime = round(time.perf_counter() - started, 3)
    meta = {
        "epoch": 11,
        "epochs": 12,
        "decoder_epochs": 2,
        "decoder_losses": decoder_losses,
        "decoder_trainable_count": len(decoder_names),
        "losses": losses,
        "runtime_s": runtime,
        "classes": list(CLASS_NAMES),
        "held_out": "phase2_corner_skil_means seed 25",
        "backbone_copied": copied.get("copied"),
        "trainable": trainable,
        "not_studs": True,
    }
    fp.save_checkpoint(model, OUT, meta, decoder_names)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
