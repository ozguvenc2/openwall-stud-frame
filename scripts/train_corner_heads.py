"""Short fine-tune of ranks 4 and 5 on synthetic corner face labels.

Eight training corners. Leans, seeds, and noise are not the four eval
scenes in data/wall-corner/manifest.json. Classes are floor, face_a, and
face_b. This is not a stud head.

    .venv\\Scripts\\python.exe scripts/train_corner_heads.py --stack pointcept
    .venv-o3dml\\Scripts\\python.exe scripts/train_corner_heads.py --stack randlanet

Head-only for Pointcept (backbone frozen), three epochs. RandLA-Net keeps
the S3DIS encoder where shapes match, replaces the 13-way layer with a
3-class layer, and trains for 25 epochs. A 3-epoch pass stayed at chance
(cross-entropy near ln 3); the longer pass is still a few minutes on eight clouds.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.wall_corner import (  # noqa: E402
    CLASS_NAMES,
    histogram,
    load_manifest,
    make_corner,
    read_ply,
    repo_root,
    score_named_faces,
)

# Held out of this list: the manifest scenes (leans 0.383/0.250, seeds 23 and 29).
TRAIN_SPECS = (
    (0.20, 0.10, 11, 1.5, True),
    (0.30, 0.40, 11, 3.0, True),
    (0.50, 0.15, 17, 1.5, True),
    (0.70, 0.55, 17, 3.0, True),
    (0.15, 0.25, 41, 2.0, True),
    (0.45, 0.40, 41, 4.0, True),
    (0.10, 0.60, 53, 1.0, False),
    (0.55, 0.35, 53, 5.0, True),
)

OUT_DIR = repo_root() / "artifacts" / "scorecards" / "phase2_neural_corner"
WEIGHT_DIR = repo_root() / "artifacts" / "weights" / "corner"
POINTCEPT_EPOCHS = 3
RANDLA_EPOCHS = 25


def _train_clouds() -> list[dict]:
    rows = []
    for lean_a, lean_b, seed, noise_mm, floor in TRAIN_SPECS:
        cloud = make_corner(
            name=f"train_a{lean_a:.2f}_b{lean_b:.2f}_s{seed}",
            face_a_lean_deg=lean_a,
            face_b_lean_deg=lean_b,
            noise_std_m=noise_mm / 1000.0,
            seed=seed,
            floor=floor,
        )
        rows.append({"points": cloud.points_m, "labels": cloud.labels, "name": cloud.name})
        print(f"train cloud {cloud.name} n={cloud.points_m.shape[0]}", flush=True)
    return rows


def _class_weight(rows: list[dict]):
    import torch

    counts = np.zeros(3, dtype=np.float64)
    for row in rows:
        for class_id in range(3):
            counts[class_id] += np.sum(row["labels"] == class_id)
    counts = np.maximum(counts, 1.0)
    weight = counts.sum() / (3.0 * counts)
    return torch.tensor(weight, dtype=torch.float32, device="cuda")


def _eval_scenes(model, predict, names: list[str], stack: str, rank: int) -> list[dict]:
    manifest = load_manifest()
    cards = []
    for scene in manifest["scenes"]:
        points, labels = read_ply(repo_root() / scene["ply"])
        started = time.perf_counter()
        pred = predict(points)
        runtime_s = time.perf_counter() - started
        score = score_named_faces(
            points,
            pred,
            names,
            labels,
            np.asarray(scene["gt_normal_a"], dtype=float),
            np.asarray(scene["gt_normal_b"], dtype=float),
            gt_lean_a=float(scene["gt_face_a_lean_deg"]),
            gt_lean_b=float(scene["gt_face_b_lean_deg"]),
        )
        stem = f"r{rank}_{stack}_corner_finetune__{scene['name']}"
        card = {
            "file_stem": stem,
            "rank": rank,
            "stack": stack,
            "weights": "corner_finetune",
            "scene": scene["name"],
            "claim": "wall planes and corner lean. Not a stud detection.",
            "gt_face_a_lean_deg": scene["gt_face_a_lean_deg"],
            "gt_face_b_lean_deg": scene["gt_face_b_lean_deg"],
            "n_points": int(points.shape[0]),
            "runtime_s": round(runtime_s, 4),
            "histogram": histogram(pred, names),
            "faces_score": score,
            "note": "3-class head trained on eight other synthetic corners. Not a stud class.",
        }
        path = OUT_DIR / f"{stem}.json"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
        faces = score["faces"]
        print(
            f"{stem} both={score['both_faces_detected']} "
            f"A={faces['face_a']['measured_lean_deg']} B={faces['face_b']['measured_lean_deg']} "
            f"s={card['runtime_s']}",
            flush=True,
        )
        cards.append(card)
    return cards


def train_pointcept() -> None:
    import torch

    from openwall_stud.contenders.pointcept_ptv3 import _cache_root
    from openwall_stud.finetune_pointcept import (
        build_model,
        collate_cloud,
        load_bimstruct_backbone,
        predict_full,
        set_trainable,
        train_step,
    )

    cache = _cache_root()
    if str(cache) not in sys.path:
        sys.path.insert(0, str(cache))
    import segment_scan

    rows = _train_clouds()
    for row in rows:
        row["normals"] = segment_scan.estimate_normals(np.asarray(row["points"], dtype=np.float64))
    model = build_model("cuda", num_classes=3)
    copied = load_bimstruct_backbone(model)
    names = set_trainable(model, train_decoder=False)
    print(f"backbone copied {copied['copied']}; training {names}", flush=True)
    optimizer = torch.optim.AdamW(
        [param for param in model.parameters() if param.requires_grad],
        lr=1e-3,
        weight_decay=1e-4,
    )
    class_weight = _class_weight(rows)
    history = []
    wall_start = time.perf_counter()
    for epoch in range(1, POINTCEPT_EPOCHS + 1):
        order = torch.randperm(len(rows)).tolist()
        losses = []
        epoch_start = time.perf_counter()
        for step, index in enumerate(order, start=1):
            row = rows[index]
            batch = collate_cloud(row["points"], row["labels"], row["normals"])
            loss = train_step(model, optimizer, batch, class_weight, grad_backbone=False)
            losses.append(loss)
            print(f"pointcept epoch {epoch} step {step}/{len(order)} loss={loss:.4f}", flush=True)
        history.append(
            {
                "epoch": epoch,
                "train_loss": float(sum(losses) / len(losses)),
                "epoch_s": round(time.perf_counter() - epoch_start, 1),
            }
        )
    weight = WEIGHT_DIR / "pointcept_corner_3class.pth"
    WEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "seg_head": model.seg_head.state_dict(),
            "classes": list(CLASS_NAMES),
            "num_classes": 3,
            "epochs": POINTCEPT_EPOCHS,
            "history": history,
            "trainable_names": names,
            "wall_s": round(time.perf_counter() - wall_start, 1),
        },
        weight,
    )
    print(f"saved {weight} ({weight.stat().st_size} bytes)", flush=True)

    def predict(points: np.ndarray) -> np.ndarray:
        normals = segment_scan.estimate_normals(np.asarray(points, dtype=np.float64))
        return predict_full(model, points, normals)

    _eval_scenes(model, predict, list(CLASS_NAMES), "pointcept", 4)
    (WEIGHT_DIR / "pointcept_corner_train_log.json").write_text(
        json.dumps({"history": history, "wall_s": round(time.perf_counter() - wall_start, 1)}, indent=2) + "\n",
        encoding="utf-8",
    )


def eval_randlanet() -> None:
    import torch

    from openwall_stud.finetune_randlanet import build_model, predict_labels

    weight = WEIGHT_DIR / "randlanet_corner_3class.pth"
    blob = torch.load(weight, map_location="cpu", weights_only=False)
    model = build_model("cuda", num_classes=3)
    model.load_state_dict(blob["model_state_dict"])
    print(f"loaded {weight} epoch-end loss {blob['history'][-1]['train_loss']:.4f}", flush=True)

    def predict(points: np.ndarray) -> np.ndarray:
        pred, _runtime = predict_labels(model, points.astype(np.float32))
        return pred

    _eval_scenes(model, predict, list(CLASS_NAMES), "open3d_ml", 5)


def train_randlanet() -> None:
    import torch

    from openwall_stud.finetune_randlanet import (
        build_model,
        load_s3dis_encoder,
        predict_labels,
        s3dis_path,
        train_step,
    )

    rows = _train_clouds()
    model = build_model("cuda", num_classes=3)
    loaded = load_s3dis_encoder(model, s3dis_path())
    print(f"S3DIS copied {loaded['copied']}; skipped {loaded['skipped']}", flush=True)
    skipped = set(loaded["skipped"])
    new_params = []
    old_params = []
    for name, param in model.named_parameters():
        if name in skipped:
            new_params.append(param)
        else:
            old_params.append(param)
    if not new_params:
        raise SystemExit(f"No new 3-class parameters among skipped keys: {loaded['skipped']}")
    optimizer = torch.optim.AdamW(
        [{"params": old_params, "lr": 1e-3}, {"params": new_params, "lr": 1e-3}],
        weight_decay=1e-4,
    )
    class_weight = _class_weight(rows)
    history = []
    wall_start = time.perf_counter()
    for epoch in range(1, RANDLA_EPOCHS + 1):
        order = torch.randperm(len(rows)).tolist()
        losses = []
        epoch_start = time.perf_counter()
        for step, index in enumerate(order, start=1):
            row = rows[index]
            loss = train_step(model, optimizer, row["points"].astype(np.float32), row["labels"], class_weight)
            losses.append(loss)
        mean_loss = float(sum(losses) / len(losses))
        print(
            f"randlanet epoch {epoch}/{RANDLA_EPOCHS} loss={mean_loss:.4f} "
            f"s={time.perf_counter() - epoch_start:.1f}",
            flush=True,
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": float(sum(losses) / len(losses)),
                "epoch_s": round(time.perf_counter() - epoch_start, 1),
            }
        )
    weight = WEIGHT_DIR / "randlanet_corner_3class.pth"
    WEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "classes": list(CLASS_NAMES),
            "num_classes": 3,
            "epochs": RANDLA_EPOCHS,
            "history": history,
            "s3dis_copied": loaded["copied"],
            "s3dis_skipped": loaded["skipped"],
            "wall_s": round(time.perf_counter() - wall_start, 1),
        },
        weight,
    )
    print(f"saved {weight} ({weight.stat().st_size} bytes)", flush=True)

    def predict(points: np.ndarray) -> np.ndarray:
        pred, _runtime = predict_labels(model, points.astype(np.float32))
        return pred

    _eval_scenes(model, predict, list(CLASS_NAMES), "open3d_ml", 5)
    (WEIGHT_DIR / "randlanet_corner_train_log.json").write_text(
        json.dumps({"history": history, "wall_s": round(time.perf_counter() - wall_start, 1)}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", choices=("pointcept", "randlanet"), required=True)
    parser.add_argument("--eval-only", action="store_true")
    args = parser.parse_args()
    if args.stack == "randlanet" and args.eval_only:
        eval_randlanet()
        return
    if args.stack == "pointcept":
        train_pointcept()
    else:
        train_randlanet()


if __name__ == "__main__":
    main()
