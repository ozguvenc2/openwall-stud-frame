"""Fine-tune the BIMStruct3D PTv3 checkpoint for clutter vs stud.

The backbone is the rank-4 PT-v3m1 (``in_channels=6``, color + normal).
The 10-class head is replaced by a 2-class MLP. Training starts with that
head only. If val stud recall stays weak, the decoder is unfrozen for a
second pass. Base BIMStruct3D weights stay in the gitignored cache.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.finetune_synth import CLASS_NAMES, repo_root

WEIGHT_DIR = repo_root() / "artifacts" / "weights" / "finetune"
WEIGHT_NAME = "pointcept_stud_2class.pth"
GRID_SIZE = 0.02
NUM_CLASSES = 2
BACKBONE_OUT = 64


def cache_root() -> Path:
    return repo_root() / "data" / "cache" / "bimstruct3d"


def weight_path() -> Path:
    return WEIGHT_DIR / WEIGHT_NAME


def _import_pointcept():
    root = cache_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from pointcept.datasets.transform import Compose
    from pointcept.datasets.utils import collate_fn
    from pointcept.models import build_model
    from pointcept.models.utils.structure import Point
    from pointcept.utils.config import Config

    return Compose, collate_fn, build_model, Point, Config


def _transform():
    Compose, _, _, _, _ = _import_pointcept()
    return Compose(
        [
            dict(type="CenterShift", apply_z=True),
            dict(
                type="GridSample",
                grid_size=GRID_SIZE,
                hash_type="fnv",
                mode="train",
                return_grid_coord=True,
            ),
            dict(type="CenterShift", apply_z=False),
            dict(type="NormalizeColor"),
            dict(type="ToTensor"),
            dict(
                type="Collect",
                keys=("coord", "grid_coord", "segment", "index"),
                feat_keys=("color", "normal"),
            ),
        ]
    )


def _replace_head(model):
    import torch.nn as nn

    model.seg_head = nn.Sequential(
        nn.Linear(BACKBONE_OUT, BACKBONE_OUT),
        nn.ReLU(inplace=True),
        nn.Dropout(0.1),
        nn.Linear(BACKBONE_OUT, NUM_CLASSES),
    )
    return model


def build_model(device: str = "cuda"):
    _, _, build_model_fn, _, Config = _import_pointcept()
    cfg = Config.fromfile(str(cache_root() / "configs" / "model_config.py"))
    cfg.model.num_classes = NUM_CLASSES
    cfg.model.criteria = [
        dict(type="CrossEntropyLoss", loss_weight=1.0, ignore_index=-1),
    ]
    model = build_model_fn(cfg.model)
    _replace_head(model)
    model.to(device)
    return model


def load_bimstruct_backbone(model) -> dict[str, Any]:
    import torch

    weight_path = cache_root() / "weights" / "model_best.pth"
    blob = torch.load(weight_path, map_location="cpu", weights_only=False)
    source = blob["state_dict"]
    own = model.state_dict()
    filtered = {}
    skipped = []
    for key, value in source.items():
        name = key[7:] if key.startswith("module.") else key
        if name.startswith("seg_head"):
            skipped.append(name)
            continue
        if name in own and tuple(own[name].shape) == tuple(value.shape):
            filtered[name] = value
        else:
            skipped.append(name)
    missing, unexpected = model.load_state_dict(filtered, strict=False)
    return {
        "copied": len(filtered),
        "skipped_head_or_mismatch": skipped,
        "missing_count": len(list(missing)),
        "unexpected_count": len(list(unexpected)),
        "base_checkpoint": str(weight_path),
    }


def set_trainable(model, *, train_decoder: bool) -> list[str]:
    names = []
    for name, param in model.named_parameters():
        train = name.startswith("seg_head") or (train_decoder and name.startswith("backbone.dec"))
        param.requires_grad = train
        if train:
            names.append(name)
    return names


def save_checkpoint(model, path: Path, meta: dict[str, Any], trainable_names: list[str]) -> None:
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    full = model.state_dict()
    torch.save(
        {
            "seg_head": model.seg_head.state_dict(),
            "trainable": {
                name: full[name].detach().cpu()
                for name in trainable_names
                if name in full
            },
            "trainable_names": list(trainable_names),
            "meta": meta,
            "classes": list(CLASS_NAMES),
            "grid_size": GRID_SIZE,
            "num_classes": NUM_CLASSES,
            "head": "mlp-64-64-2",
        },
        path,
    )


def load_finetuned(model, path: Path) -> dict[str, Any]:
    import torch

    blob = torch.load(path, map_location="cpu", weights_only=False)
    model.seg_head.load_state_dict(blob["seg_head"])
    own = model.state_dict()
    extra = blob.get("trainable") or {}
    copied = {}
    for name, value in extra.items():
        if name.startswith("seg_head"):
            continue
        if name in own and tuple(own[name].shape) == tuple(value.shape):
            copied[name] = value
    if copied:
        model.load_state_dict(copied, strict=False)
    if hasattr(model.backbone, "shuffle_orders"):
        model.backbone.shuffle_orders = False
    return blob.get("meta", {})


def collate_cloud(points: np.ndarray, labels: np.ndarray, normals: np.ndarray):
    _, collate_fn, _, _, _ = _import_pointcept()
    import torch

    xyz = np.asarray(points, dtype=np.float32)
    data = {
        "coord": xyz.copy(),
        "color": np.zeros_like(xyz, dtype=np.float32),
        "normal": np.asarray(normals, dtype=np.float32),
        "segment": np.asarray(labels, dtype=np.int64),
        "index": np.arange(xyz.shape[0], dtype=np.int64),
        "index_valid_keys": ["coord", "color", "normal", "segment", "index"],
    }
    sample = _transform()(data)
    batch = collate_fn([sample])
    device = "cuda"
    for key, value in list(batch.items()):
        if torch.is_tensor(value):
            batch[key] = value.to(device, non_blocking=True)
    if "grid_coord" in batch:
        batch["grid_coord"] = batch["grid_coord"].int()
    return batch


def _unpool(point):
    if not hasattr(point, "keys"):
        return point
    while "pooling_parent" in point.keys():
        parent = point.pop("pooling_parent")
        inverse = point.pop("pooling_inverse")
        parent.feat = __import__("torch").cat([parent.feat, point.feat[inverse]], dim=-1)
        point = parent
    return point


def logits_of(model, batch, *, grad_backbone: bool):
    import torch

    _, _, _, Point, _ = _import_pointcept()
    point = Point(batch)
    if grad_backbone:
        point = model.backbone(point)
        point = _unpool(point)
        feat = point.feat if hasattr(point, "feat") else point
    else:
        with torch.no_grad():
            point = model.backbone(point)
            point = _unpool(point)
            feat = point.feat.detach() if hasattr(point, "feat") else point
    return model.seg_head(feat)


def train_step(model, optimizer, batch, class_weight, *, grad_backbone: bool) -> float:
    import torch
    import torch.nn.functional as F

    model.train()
    if not grad_backbone:
        model.backbone.eval()
    optimizer.zero_grad(set_to_none=True)
    logits = logits_of(model, batch, grad_backbone=grad_backbone)
    target = batch["segment"].to(logits.device).long()
    loss = F.cross_entropy(logits, target, weight=class_weight)
    loss.backward()
    torch.nn.utils.clip_grad_norm_((param for param in model.parameters() if param.requires_grad), 1.0)
    optimizer.step()
    return float(loss.detach().cpu())


def predict_full(model, points: np.ndarray, normals: np.ndarray) -> np.ndarray:
    """Label every input point. Voxel reps are predicted, then nearest-neighbor copied."""
    import torch
    from scipy.spatial import cKDTree

    dummy = np.zeros((points.shape[0],), dtype=np.int64)
    batch = collate_cloud(points, dummy, normals)
    model.eval()
    with torch.no_grad():
        logits = logits_of(model, batch, grad_backbone=False)
        pred_voxel = logits.argmax(dim=1).detach().cpu().numpy()
    index = batch["index"].detach().cpu().numpy().reshape(-1)
    chosen = np.asarray(points, dtype=np.float64)[index]
    tree = cKDTree(chosen)
    _, nearest = tree.query(np.asarray(points, dtype=np.float64), k=1)
    return pred_voxel[nearest].astype(np.int64)
