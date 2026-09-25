"""Fine-tune BIMStruct3D PTv3 for clutter vs stud.

Run with the Pointcept interpreter (torch 2.7, the BIMStruct3D pin):

    .venv\\Scripts\\python.exe scripts/train_pointcept_stud.py
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

from openwall_stud.finetune_pointcept import (  # noqa: E402
    build_model,
    collate_cloud,
    load_bimstruct_backbone,
    load_finetuned,
    predict_full,
    save_checkpoint,
    set_trainable,
    train_step,
    weight_path,
)
from openwall_stud.finetune_randlanet import point_metrics  # noqa: E402
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
            print(f"GPU memory in use: {used} MiB. Starting Pointcept.", flush=True)
            return
        print(f"GPU memory in use: {used} MiB. Waiting 60s for the other Oz_PC job.", flush=True)
        time.sleep(60)
    raise SystemExit("GPU stayed above the idle threshold. Pointcept training was not started.")


def _mean(rows: list, key: str, kind: str | None = None) -> float | None:
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
        pred = predict_full(model, cloud["points"], cloud["normals"])
        metrics = point_metrics(pred, cloud["labels"])
        scored.append((spec, metrics))
    summary = {
        "n": len(scored),
        "stud_recall_stud_scenes": _mean(scored, "recall_stud", "stud"),
        "stud_iou_floor_scenes": _mean(scored, "iou_stud", "stud_floor"),
        "clutter_iou_floor_scenes": _mean(scored, "iou_clutter", "stud_floor"),
    }
    present = [
        value
        for value in (
            summary["stud_recall_stud_scenes"],
            summary["stud_iou_floor_scenes"],
            summary["clutter_iou_floor_scenes"],
        )
        if value is not None
    ]
    summary["selection_score"] = None if not present else float(sum(present) / len(present))
    return summary


def _run_epochs(model, rows, val_rows, *, epochs: int, train_decoder: bool, history: list, best: dict) -> None:
    import torch

    names = set_trainable(model, train_decoder=train_decoder)
    head = [param for name, param in model.named_parameters() if param.requires_grad and name.startswith("seg_head")]
    other = [param for name, param in model.named_parameters() if param.requires_grad and not name.startswith("seg_head")]
    groups = [{"params": head, "lr": 1e-3}]
    if other:
        groups.append({"params": other, "lr": 1e-4})
    optimizer = torch.optim.AdamW(groups, weight_decay=1e-4)
    # Clutter is the smaller set. Upweight it so the head cannot win by
    # calling every point a stud.
    class_weight = torch.tensor([3.0, 1.0], device="cuda")
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
            if step == 1 or step % 20 == 0 or step == len(order):
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
                weight_path(),
                {
                    "selection_score": score,
                    "val": val,
                    "trained_decoder": train_decoder,
                    "torch": torch.__version__,
                    "cuda": torch.version.cuda,
                    "init": "BIMStruct3D PT-v3m1 backbone, new 2-class MLP head",
                    "classes": ["clutter", "stud"],
                    "synthetic_only": True,
                },
                names,
            )
            print(f"saved {weight_path()} score={score:.4f}", flush=True)


def main(argv: list[str] | None = None) -> int:
    import torch

    parser = argparse.ArgumentParser(description="Fine-tune PTv3 for a stud class.")
    parser.add_argument("--epochs", type=int, default=3, help="Head-only epochs.")
    parser.add_argument("--decoder-epochs", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--floor-repeat", type=int, default=2)
    args = parser.parse_args(argv)
    if not torch.__version__.startswith("2.7"):
        raise SystemExit(
            f"This script wants the .venv interpreter (torch 2.7). This one is {torch.__version__}."
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
    loaded = load_bimstruct_backbone(model)
    print(
        f"BIMStruct backbone copied {loaded['copied']} tensors "
        f"(missing {loaded['missing_count']}).",
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
    recall = last.get("stud_recall_stud_scenes") or 0.0
    floor_iou = last.get("stud_iou_floor_scenes")
    floor_iou = 1.0 if floor_iou is None else floor_iou
    if args.decoder_epochs > 0 and (recall < 0.80 or floor_iou < 0.35):
        print("Head-only val is weak. Unfreezing the PTv3 decoder.", flush=True)
        load_finetuned(model, weight_path())
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
    log = {
        "wall_s": wall_s,
        "history": history,
        "best_row": best_row,
        "trained_decoder": best["trained_decoder"],
        "best_selection_score": best["score"],
        "weight": str(weight_path()),
        "copied_backbone_tensors": loaded["copied"],
    }
    log_path = weight_path().with_name("pointcept_train_log.json")
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"Pointcept train wall_s={wall_s} log={log_path} weight={weight_path()}")
    # Touch the loader so a bad checkpoint fails before the long inference pass.
    model.cpu()
    torch.cuda.empty_cache()
    reloaded = build_model("cuda")
    load_bimstruct_backbone(reloaded)
    load_finetuned(reloaded, weight_path())
    print("reloaded fine-tuned head onto a fresh BIMStruct backbone", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
