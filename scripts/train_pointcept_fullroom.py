"""Train the Pointcept PTv3 stud head on 28-stud rooms.

Run with the Pointcept interpreter (torch 2.7):

    C:\\Repos\\openwall-stud-frame-ranks45\\.venv\\Scripts\\python.exe scripts/train_pointcept_fullroom.py

Writes artifacts/checkpoints/stud-heads/fullroom/ only.
Does not overwrite the Experiment 1 pointcept_stud_2class.pth.
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
from openwall_stud.finetune_pointcept import (  # noqa: E402
    build_model,
    collate_cloud,
    load_bimstruct_backbone,
    load_finetuned,
    predict_full,
    save_checkpoint,
    set_trainable,
    train_step,
)
from openwall_stud.finetune_randlanet import point_metrics  # noqa: E402


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
            print(f"GPU memory in use: {used} MiB. Starting Pointcept full-room train.", flush=True)
            return
        print(f"GPU memory in use: {used} MiB. Waiting 60s.", flush=True)
        time.sleep(60)
    raise SystemExit("GPU stayed above the idle threshold. Pointcept training was not started.")


def _mean(rows: list, key: str) -> float | None:
    values = [metrics[key] for _spec, metrics in rows if metrics.get(key) is not None]
    if not values:
        return None
    return float(sum(values) / len(values))


def evaluate(model, specs: list[dict]) -> dict:
    scored = []
    for spec in specs:
        cloud = ensure_cloud(spec)
        pred = predict_full(model, cloud["points"], cloud["normals"])
        metrics = point_metrics(pred, cloud["labels"])
        metrics["both_classes"] = int(len(set(pred.tolist()))) >= 2
        scored.append((spec, metrics))
    summary = {
        "n": len(scored),
        "stud_iou": _mean(scored, "iou_stud"),
        "clutter_iou": _mean(scored, "iou_clutter"),
        "stud_recall": _mean(scored, "recall_stud"),
        "rooms_with_both_classes": int(sum(1 for _spec, metrics in scored if metrics["both_classes"])),
    }
    parts = [summary["stud_iou"], summary["clutter_iou"]]
    present = [value for value in parts if value is not None]
    summary["selection_score"] = None if len(present) < 2 else float(sum(present) / len(present))
    return summary


def weight_file() -> Path:
    WEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    return assert_safe_weight_path(WEIGHT_DIR / "pointcept_stud_2class_fullroom.pth")


def _run_epochs(model, rows, val_rows, *, epochs: int, train_decoder: bool, history: list, best: dict) -> None:
    import torch

    names = set_trainable(model, train_decoder=train_decoder)
    head = [param for name, param in model.named_parameters() if param.requires_grad and name.startswith("seg_head")]
    other = [param for name, param in model.named_parameters() if param.requires_grad and not name.startswith("seg_head")]
    groups = [{"params": head, "lr": 1e-3}]
    if other:
        groups.append({"params": other, "lr": 1e-4})
    optimizer = torch.optim.AdamW(groups, weight_decay=1e-4)
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
    dest = weight_file()
    for epoch in range(1, epochs + 1):
        order = torch.randperm(len(rows)).tolist()
        losses = []
        epoch_start = time.perf_counter()
        for step, index in enumerate(order, start=1):
            spec = rows[index]
            cloud = ensure_cloud(spec)
            batch = collate_cloud(cloud["points"], cloud["labels"], cloud["normals"])
            loss = train_step(
                model,
                optimizer,
                batch,
                class_weight,
                grad_backbone=train_decoder,
            )
            losses.append(loss)
            if step == 1 or step % 8 == 0 or step == len(order):
                print(
                    f"decoder={train_decoder} epoch {epoch} step {step}/{len(order)} "
                    f"loss={loss:.4f} id={spec['id']}",
                    flush=True,
                )
        val = evaluate(model, val_rows)
        val["epoch"] = epoch
        val["train_decoder"] = train_decoder
        val["train_loss"] = float(sum(losses) / max(len(losses), 1))
        val["epoch_s"] = round(time.perf_counter() - epoch_start, 1)
        val["n_trainable"] = len(names)
        history.append(val)
        print(f"val {json.dumps(val)}", flush=True)
        score = val["selection_score"] if val["selection_score"] is not None else -1.0
        if score >= best["score"]:
            best["score"] = score
            best["trained_decoder"] = train_decoder
            save_checkpoint(
                model,
                dest,
                {
                    "selection_score": score,
                    "val": val,
                    "trained_decoder": train_decoder,
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "init": "BIMStruct3D PT-v3m1 backbone, new 2-class MLP head",
                    "classes": ["clutter", "stud"],
                    "synthetic_only": True,
                    "recipe": "fullroom_28",
                    "decision": "docs/research/37-fullroom-training-decision.md",
                },
                names,
            )
            print(f"saved {dest} score={score:.4f}", flush=True)


def main(argv: list[str] | None = None) -> int:
    import torch

    parser = argparse.ArgumentParser(description="Fine-tune PTv3 on 28-stud rooms.")
    parser.add_argument("--epochs", type=int, default=4, help="Head-only epochs.")
    parser.add_argument("--decoder-epochs", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)
    if not torch.__version__.startswith("2.7"):
        raise SystemExit(
            f"This script wants the .venv interpreter (torch 2.7). This one is {torch.__version__}."
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
    loaded = load_bimstruct_backbone(model)
    print(
        f"BIMStruct backbone copied {loaded['copied']} tensors (missing {loaded['missing_count']}).",
        flush=True,
    )
    history: list[dict] = []
    best = {"score": -1.0, "trained_decoder": False}
    wall_start = time.perf_counter()
    _run_epochs(
        model,
        train_rows,
        val_rows,
        epochs=args.epochs,
        train_decoder=False,
        history=history,
        best=best,
    )
    last = history[-1]
    recall = last.get("stud_recall") or 0.0
    stud_iou = last.get("stud_iou")
    stud_iou = 1.0 if stud_iou is None else stud_iou
    if args.decoder_epochs > 0 and (recall < 0.80 or stud_iou < 0.35):
        print("Head-only val is weak. Unfreezing the PTv3 decoder.", flush=True)
        load_finetuned(model, weight_file())
        _run_epochs(
            model,
            train_rows,
            val_rows,
            epochs=args.decoder_epochs,
            train_decoder=True,
            history=history,
            best=best,
        )
    best_row = max(history, key=lambda row: row["selection_score"] or -1.0)
    wall_s = round(time.perf_counter() - wall_start, 1)
    dest = weight_file()
    log = {
        "wall_s": wall_s,
        "history": history,
        "best_row": best_row,
        "trained_decoder": best["trained_decoder"],
        "best_selection_score": best["score"],
        "weight": str(dest.relative_to(ROOT)),
        "copied_backbone_tensors": loaded["copied"],
        "recipe": "fullroom_28",
    }
    log_path = dest.with_name("pointcept_fullroom_train_log.json")
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"Pointcept full-room train wall_s={wall_s} log={log_path} weight={dest}")
    model.cpu()
    torch.cuda.empty_cache()
    reloaded = build_model("cuda")
    load_bimstruct_backbone(reloaded)
    load_finetuned(reloaded, dest)
    print("reloaded fine-tuned full-room head onto a fresh BIMStruct backbone", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
