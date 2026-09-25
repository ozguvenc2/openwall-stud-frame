"""Fine-tune Open3D-ML RandLA-Net (S3DIS layout) for clutter vs stud.

The encoder matches ``randlanet_s3dis.yml`` so the published S3DIS checkpoint
can initialize it. The last convolution is a new 2-class layer. RGB channels
stay zero, the same way the rank-5 control ran.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.finetune_synth import CLASS_NAMES, repo_root

WEIGHT_DIR = repo_root() / "artifacts" / "weights" / "finetune"
WEIGHT_NAME = "randlanet_stud_2class.pth"
S3DIS_NAME = "randlanet_s3dis_202201071330utc.pth"

NUM_POINTS = 16384
GRID_SIZE = 0.02
NUM_CLASSES = 2


def weight_path() -> Path:
    return WEIGHT_DIR / WEIGHT_NAME


def s3dis_path() -> Path:
    return repo_root() / "data" / "cache" / "open3d-ml" / S3DIS_NAME


def build_model(device: str = "cuda"):
    import open3d.ml.torch as ml3d

    model = ml3d.models.RandLANet(
        name="RandLANet",
        num_neighbors=16,
        num_layers=5,
        num_points=NUM_POINTS,
        num_classes=NUM_CLASSES,
        ignored_label_inds=[],
        sub_sampling_ratio=[4, 4, 4, 4, 2],
        in_channels=6,
        dim_features=8,
        dim_output=[16, 64, 128, 256, 512],
        grid_size=GRID_SIZE,
        batcher="DefaultBatcher",
        augment={
            "recenter": {"dim": [0, 1]},
            "noise": {"noise_std": 0.001},
        },
    )
    model.device = device
    model.to(device)
    return model


def load_s3dis_encoder(model, path: Path | None = None) -> dict[str, Any]:
    """Copy S3DIS tensors whose shapes still match. The 13-way head is left new."""
    import torch

    ckpt_path = path or s3dis_path()
    blob = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    source = blob["model_state_dict"] if isinstance(blob, dict) and "model_state_dict" in blob else blob
    own = model.state_dict()
    copied = []
    skipped = []
    filtered = {}
    for key, value in source.items():
        if key in own and tuple(own[key].shape) == tuple(value.shape):
            filtered[key] = value
            copied.append(key)
        else:
            skipped.append(key)
    missing, unexpected = model.load_state_dict(filtered, strict=False)
    return {
        "copied": len(copied),
        "skipped": skipped,
        "missing": list(missing),
        "unexpected": list(unexpected),
        "s3dis_path": str(ckpt_path),
    }


def save_checkpoint(model, path: Path, meta: dict[str, Any]) -> None:
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "meta": meta,
            "classes": list(CLASS_NAMES),
            "num_points": NUM_POINTS,
            "grid_size": GRID_SIZE,
            "num_classes": NUM_CLASSES,
        },
        path,
    )


def load_checkpoint(model, path: Path) -> dict[str, Any]:
    import torch

    blob = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(blob["model_state_dict"], strict=True)
    return blob.get("meta", {})


def _batch_from_cloud(model, points: np.ndarray, labels: np.ndarray, split: str) -> dict:
    from open3d._ml3d.torch.dataloaders import DefaultBatcher

    feat = np.zeros((points.shape[0], 3), dtype=np.float32)
    data = {
        "point": np.asarray(points, dtype=np.float32),
        "feat": feat,
        "label": np.asarray(labels, dtype=np.int32),
    }
    pre = model.preprocess(data, {"split": split})
    sample = model.transform(pre, {"split": split})
    batched = DefaultBatcher().collate_fn([{"data": sample, "attr": {"split": split}}])
    return batched["data"]


def train_step(model, optimizer, points: np.ndarray, labels: np.ndarray, class_weight) -> float:
    import torch
    import torch.nn.functional as F

    model.train()
    batch = _batch_from_cloud(model, points, labels, "train")
    optimizer.zero_grad(set_to_none=True)
    logits = model(batch)
    target = batch["labels"].to(logits.device).long()
    loss = F.cross_entropy(logits.reshape(-1, NUM_CLASSES), target.reshape(-1), weight=class_weight)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
    return float(loss.detach().cpu())


_PIPELINE = None


def _pipeline(model):
    global _PIPELINE
    import open3d.ml.torch as ml3d

    if _PIPELINE is None or _PIPELINE.model is not model:
        log_dir = repo_root() / "data" / "cache" / "open3d-ml" / "logs" / "finetune"
        log_dir.mkdir(parents=True, exist_ok=True)
        _PIPELINE = ml3d.pipelines.SemanticSegmentation(
            model,
            dataset=None,
            batch_size=1,
            val_batch_size=1,
            test_batch_size=1,
            main_log_dir=str(log_dir),
            device="cuda",
            max_epoch=1,
        )
    model.device = "cuda"
    return _PIPELINE


def use_batch_norm_stats(model) -> None:
    """Dropout off, BatchNorm on this cloud's statistics.

    Training steps are batch size 1. The running averages stay close to the
    S3DIS checkpoint, so ``model.eval()`` labels every point as stud. Matching
    the training step means normalizing with the cloud in front of the model.
    """
    import torch.nn as nn

    nn.Module.eval(model)
    for module in model.modules():
        if isinstance(module, nn.modules.batchnorm._BatchNorm):
            module.train()


def predict_labels(model, points: np.ndarray) -> tuple[np.ndarray, float]:
    """One S3DIS-style inference. Returned labels cover the input points."""
    dummy = np.zeros((points.shape[0],), dtype=np.int32)
    data = {
        "point": np.asarray(points, dtype=np.float32),
        "feat": np.zeros((points.shape[0], 3), dtype=np.float32),
        "label": dummy,
    }
    # run_inference swaps in a spatial sampler sized to that cloud.
    # Put the training sampler back or the next step indexes off the end.
    training_sampler = model.trans_point_sampler
    pipeline = _pipeline(model)

    def _eval_with_batch_stats(*_args, **_kwargs):
        use_batch_norm_stats(model)
        return model

    model.eval = _eval_with_batch_stats  # type: ignore[method-assign]
    started = time.perf_counter()
    try:
        result = pipeline.run_inference(data)
    finally:
        model.trans_point_sampler = training_sampler
        del model.eval
    runtime_s = time.perf_counter() - started
    pred = np.asarray(result["predict_labels"]).reshape(-1)
    if pred.shape[0] != points.shape[0]:
        raise RuntimeError(f"predict_labels {pred.shape[0]} != points {points.shape[0]}")
    return pred, runtime_s


def point_metrics(pred: np.ndarray, labels: np.ndarray) -> dict[str, float | None]:
    pred = np.asarray(pred).reshape(-1)
    labels = np.asarray(labels).reshape(-1)
    out: dict[str, float | None] = {}
    for class_id, name in enumerate(CLASS_NAMES):
        tp = int(np.sum((pred == class_id) & (labels == class_id)))
        fp = int(np.sum((pred == class_id) & (labels != class_id)))
        fn = int(np.sum((pred != class_id) & (labels == class_id)))
        denom = tp + fp + fn
        out[f"iou_{name}"] = None if denom == 0 else tp / denom
        support = tp + fn
        out[f"recall_{name}"] = None if support == 0 else tp / support
    return out
