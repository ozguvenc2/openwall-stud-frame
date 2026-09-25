"""Fine-tune Open3D-ML RandLA-Net on the synthetic stud/clutter set.

Run with the Open3D-ML interpreter (torch 2.13):

    .venv-o3dml\\Scripts\\python.exe scripts/train_randlanet_stud.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.finetune_randlanet import (  # noqa: E402
    NUM_CLASSES,
    build_model,
    load_s3dis_encoder,
    point_metrics,
    predict_labels,
    save_checkpoint,
    s3dis_path,
    train_step,
    weight_path,
)
from openwall_stud.finetune_synth import ensure_cloud, iter_split, load_manifest  # noqa: E402


def wait_until_gpu_idle(max_used_mib: int = 6000) -> None:
    nvidia = shutil.which("nvidia-smi")
    if not nvidia:
        raise SystemExit("nvidia-smi is not on PATH")
    for _ in range(30):
        proc = subprocess.run(
            [nvidia, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
        )
        used = int((proc.stdout or "0").strip().splitlines()[0])
        if used < max_used_mib:
            print(f"GPU memory in use: {used} MiB. Starting RandLA-Net.", flush=True)
            return
        print(f"GPU memory in use: {used} MiB. Waiting 60s for the other Oz_PC job.", flush=True)
        time.sleep(60)
    raise SystemExit("GPU stayed above the idle threshold. RandLA-Net training was not started.")


def _mean(rows: list[dict], key: str, kind: str | None = None) -> float | None:
    values = []
    for spec, metrics in rows:
        if kind is not None and spec["kind"] != kind:
            continue
        value = metrics.get(key)
        if value is not None:
            values.append(value)
    if not values:
        return None
    return float(sum(values) / len(values))


def evaluate(model, specs: list[dict]) -> dict:
    scored = []
    for spec in specs:
        cloud = ensure_cloud(spec)
        pred, runtime_s = predict_labels(model, cloud["points"])
        metrics = point_metrics(pred, cloud["labels"])
        metrics["runtime_s"] = runtime_s
        scored.append((spec, metrics))
    summary = {
        "n": len(scored),
        "stud_recall_stud_scenes": _mean(scored, "recall_stud", "stud"),
        "stud_iou_floor_scenes": _mean(scored, "iou_stud", "stud_floor"),
        "clutter_iou_floor_scenes": _mean(scored, "iou_clutter", "stud_floor"),
        "mean_runtime_s": float(sum(item[1]["runtime_s"] for item in scored) / max(len(scored), 1)),
    }
    parts = [
        summary["stud_recall_stud_scenes"],
        summary["stud_iou_floor_scenes"],
        summary["clutter_iou_floor_scenes"],
    ]
    present = [value for value in parts if value is not None]
    summary["selection_score"] = None if not present else float(sum(present) / len(present))
    return summary


def main(argv: list[str] | None = None) -> int:
    import torch

    parser = argparse.ArgumentParser(description="Fine-tune RandLA-Net for a stud class.")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0, help="If set, train on only this many clouds.")
    parser.add_argument("--floor-repeat", type=int, default=2)
    args = parser.parse_args(argv)
    if not torch.__version__.startswith("2.13"):
        raise SystemExit(
            f"This script wants the .venv-o3dml interpreter (torch 2.13). This one is {torch.__version__}."
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    wait_until_gpu_idle()
    manifest = load_manifest()
    train_rows = iter_split(manifest, "train", repeat_floor=args.floor_repeat)
    val_rows = list(manifest["val"])
    if args.limit:
        train_rows = train_rows[: args.limit]
        val_rows = val_rows[: min(4, len(val_rows))]
    model = build_model("cuda")
    loaded = load_s3dis_encoder(model, s3dis_path())
    print(
        f"S3DIS encoder copied {loaded['copied']} tensors; skipped {loaded['skipped']}",
        flush=True,
    )
    head = [param for name, param in model.named_parameters() if name.startswith("fc1")]
    rest = [param for name, param in model.named_parameters() if not name.startswith("fc1")]
    optimizer = torch.optim.AdamW(
        [{"params": rest, "lr": 1e-4}, {"params": head, "lr": 1e-3}],
        weight_decay=1e-4,
    )
    # Clutter is the smaller set. Upweight it so the net cannot win by
    # calling every point a stud.
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
    best = -1.0
    history = []
    wall_start = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        order = torch.randperm(len(train_rows)).tolist()
        losses = []
        epoch_start = time.perf_counter()
        for step, index in enumerate(order, start=1):
            spec = train_rows[index]
            cloud = ensure_cloud(spec)
            loss = train_step(model, optimizer, cloud["points"], cloud["labels"], class_weight)
            losses.append(loss)
            if step == 1 or step % 40 == 0 or step == len(order):
                print(
                    f"epoch {epoch} step {step}/{len(order)} loss={loss:.4f} "
                    f"id={spec['id']}",
                    flush=True,
                )
        val = evaluate(model, val_rows)
        val["epoch"] = epoch
        val["train_loss"] = float(sum(losses) / max(len(losses), 1))
        val["epoch_s"] = round(time.perf_counter() - epoch_start, 1)
        history.append(val)
        print(f"val {json.dumps(val)}", flush=True)
        score = val["selection_score"] if val["selection_score"] is not None else -1.0
        if score >= best:
            best = score
            save_checkpoint(
                model,
                weight_path(),
                {
                    "epoch": epoch,
                    "selection_score": score,
                    "val": val,
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "init": "Open3D-ML RandLA-Net S3DIS encoder, new 2-class head",
                    "classes": ["clutter", "stud"],
                    "synthetic_only": True,
                },
            )
            print(f"saved {weight_path()}", flush=True)
    wall_s = round(time.perf_counter() - wall_start, 1)
    log = {
        "wall_s": wall_s,
        "epochs": args.epochs,
        "train_presentations": len(train_rows),
        "best_selection_score": best,
        "history": history,
        "s3dis_skipped": loaded["skipped"],
        "num_classes": NUM_CLASSES,
        "weight": str(weight_path()),
    }
    log_path = weight_path().with_name("randlanet_train_log.json")
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"RandLA-Net train wall_s={wall_s} log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
