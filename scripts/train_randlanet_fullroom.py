"""Train the Open3D-ML RandLA-Net stud head on 28-stud rooms.

Run with the Open3D-ML interpreter (torch 2.13):

    C:\\Repos\\openwall-stud-frame-ranks45\\.venv-o3dml\\Scripts\\python.exe scripts/train_randlanet_fullroom.py

Writes artifacts/checkpoints/stud-heads/fullroom/ only.
Does not overwrite the Experiment 1 randlanet_stud_2class.pth.
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

from openwall_stud.finetune_fullroom import (  # noqa: E402
    WEIGHT_DIR,
    assert_safe_weight_path,
    ensure_cloud,
    load_manifest,
)
from openwall_stud.finetune_randlanet import (  # noqa: E402
    NUM_CLASSES,
    build_model,
    load_s3dis_encoder,
    point_metrics,
    predict_labels,
    s3dis_path,
    save_checkpoint,
    train_step,
)


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
            print(f"GPU memory in use: {used} MiB. Starting RandLA-Net full-room train.", flush=True)
            return
        print(f"GPU memory in use: {used} MiB. Waiting 60s.", flush=True)
        time.sleep(60)
    raise SystemExit("GPU stayed above the idle threshold. RandLA-Net training was not started.")


def _mean(rows: list, key: str) -> float | None:
    values = [metrics[key] for _spec, metrics in rows if metrics.get(key) is not None]
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
        both = int(len(set(pred.tolist()))) >= 2
        metrics["both_classes"] = both
        scored.append((spec, metrics))
    summary = {
        "n": len(scored),
        "stud_iou": _mean(scored, "iou_stud"),
        "clutter_iou": _mean(scored, "iou_clutter"),
        "stud_recall": _mean(scored, "recall_stud"),
        "mean_runtime_s": float(sum(item[1]["runtime_s"] for item in scored) / max(len(scored), 1)),
        "rooms_with_both_classes": int(sum(1 for _spec, metrics in scored if metrics["both_classes"])),
    }
    parts = [summary["stud_iou"], summary["clutter_iou"]]
    present = [value for value in parts if value is not None]
    summary["selection_score"] = None if len(present) < 2 else float(sum(present) / len(present))
    return summary


def weight_file() -> Path:
    WEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    return assert_safe_weight_path(WEIGHT_DIR / "randlanet_stud_2class_fullroom.pth")


def main(argv: list[str] | None = None) -> int:
    import torch

    parser = argparse.ArgumentParser(description="Fine-tune RandLA-Net on 28-stud rooms.")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="If set, train on only this many rooms.")
    args = parser.parse_args(argv)
    if not torch.__version__.startswith("2.13"):
        raise SystemExit(
            f"This script wants the .venv-o3dml interpreter (torch 2.13). This one is {torch.__version__}."
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available.")
    wait_until_gpu_idle()
    manifest = load_manifest()
    train_rows = list(manifest["train"])
    val_rows = list(manifest["val"])
    if args.limit:
        train_rows = train_rows[: args.limit]
        val_rows = val_rows[: min(2, len(val_rows))]
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
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
    best = -1.0
    history = []
    wall_start = time.perf_counter()
    dest = weight_file()
    for epoch in range(1, args.epochs + 1):
        order = torch.randperm(len(train_rows)).tolist()
        losses = []
        epoch_start = time.perf_counter()
        for step, index in enumerate(order, start=1):
            spec = train_rows[index]
            cloud = ensure_cloud(spec)
            loss = train_step(model, optimizer, cloud["points"], cloud["labels"], class_weight)
            losses.append(loss)
            if step == 1 or step % 8 == 0 or step == len(order):
                print(
                    f"epoch {epoch} step {step}/{len(order)} loss={loss:.4f} id={spec['id']}",
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
                dest,
                {
                    "epoch": epoch,
                    "selection_score": score,
                    "val": val,
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "init": "Open3D-ML RandLA-Net S3DIS encoder, new 2-class head",
                    "classes": ["clutter", "stud"],
                    "synthetic_only": True,
                    "recipe": "fullroom_28",
                    "decision": "docs/research/37-fullroom-training-decision.md",
                },
            )
            print(f"saved {dest}", flush=True)
    wall_s = round(time.perf_counter() - wall_start, 1)
    log = {
        "wall_s": wall_s,
        "epochs": args.epochs,
        "train_rooms": len(train_rows),
        "best_selection_score": best,
        "history": history,
        "s3dis_skipped": loaded["skipped"],
        "num_classes": NUM_CLASSES,
        "weight": str(dest.relative_to(ROOT)),
        "recipe": "fullroom_28",
    }
    log_path = dest.with_name("randlanet_fullroom_train_log.json")
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"RandLA-Net full-room train wall_s={wall_s} log={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
