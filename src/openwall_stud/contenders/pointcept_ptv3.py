"""Pointcept PTv3 on the one Stage 0 stud.

The finder loads that cloud and attempts one BIMStruct3D PTv3 semantic
forward pass when this interpreter has a CUDA torch and the gitignored
checkpoint cache is present (or can be fetched). BIMStruct3D weights are
CC BY-NC-SA 4.0 and are not committed. The label set has no stud class, so
stud detection, geometry, angle, and paint stay null. No PointGroup instance
checkpoint is in this repo, so that head is not run.

Entrypoint
    python -m openwall_stud.contenders.pointcept_ptv3

    ``--stub`` writes the null card without loading the cloud.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.common import (
    blocked_card,
    class_colors,
    control_card,
    emit_stub,
    gpu_probe,
    stub_card,
)
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

POINTCEPT = {
    "rank": 4,
    "algorithm_id": "A4",
    "status": "stub",
    "name": "Pointcept PTv3 / PointGroup (hook only until labeled Stage 5)",
}

BIMSTRUCT_REPO = "dfki-av/BIMStruct3D-segmentation"


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A4",
        algorithm=POINTCEPT["name"],
        rank=4,
        license_name="MIT code; some public weights are CC BY-NC-SA 4.0",
        hardware="CUDA, not used",
        failure_modes=[
            "No stud labels yet, so there is nothing to fine-tune.",
            "Zero-shot BIMStruct3D has no stud class.",
            "Commercial use of CC BY-NC-SA weights is not allowed.",
            "A GPU train was not part of this scaffold and was not started.",
        ],
        note="Scaffold hook only. Pointcept was not trained or run. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    return build_stub_card()


def _cache_root() -> Path:
    return repo_root() / "data" / "cache" / "bimstruct3d"


def _ensure_bimstruct(cache: Path) -> str | None:
    weight = cache / "weights" / "model_best.pth"
    script = cache / "segment_scan.py"
    if weight.is_file() and script.is_file() and (cache / "pointcept").is_dir():
        return None
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        return f"huggingface_hub is not importable ({type(exc).__name__}: {exc})."
    cache.mkdir(parents=True, exist_ok=True)
    try:
        snapshot_download(repo_id=BIMSTRUCT_REPO, local_dir=str(cache))
    except Exception as exc:
        return f"snapshot_download failed: {type(exc).__name__}: {exc}"
    if not weight.is_file():
        return f"Checkpoint missing after download: {weight}"
    return None


def _histogram(labels: np.ndarray, names: list[str]) -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(names):
        rows.append({"id": index, "name": str(name), "count": int(np.sum(labels == index))})
    return rows


def _forward(scene: Scene, cache: Path, device: str) -> dict[str, Any]:
    if str(cache) not in sys.path:
        sys.path.insert(0, str(cache))
    import segment_scan
    from addict import Dict as AttrDict
    from pointcept.datasets.defaults import DefaultDataset

    config_path = cache / "configs" / "model_config.py"
    weight_path = cache / "weights" / "model_best.pth"
    started = time.perf_counter()
    model, cfg = segment_scan.load_model(config_path, weight_path, device)
    names = [str(name) for name in cfg.data.names]
    num_classes = int(cfg.data.num_classes)
    coord = np.asarray(scene.points_m, dtype=np.float64)
    color = np.zeros_like(coord, dtype=np.float32)
    normal = segment_scan.estimate_normals(coord)

    work = Path(tempfile.mkdtemp(prefix="ozpc_pointcept_"))
    tiles = work / "tiles"
    tiles.mkdir(parents=True, exist_ok=True)
    tile_name = "tile_00000"
    tile_dir = tiles / tile_name
    tile_dir.mkdir()
    np.save(tile_dir / "coord.npy", coord.astype(np.float32))
    np.save(tile_dir / "color.npy", color)
    np.save(tile_dir / "normal.npy", normal)

    dataset = DefaultDataset(
        split="",
        data_root=str(tiles),
        transform=segment_scan.PREPROCESS_TRANSFORM,
        test_mode=True,
        test_cfg=AttrDict(segment_scan.TEST_CFG),
    )
    import torch
    import torch.nn.functional as F

    votes = torch.zeros((coord.shape[0], num_classes), dtype=torch.int16)
    for index in range(len(dataset)):
        tile_pred = segment_scan.infer_tile(model, dataset, index, num_classes, device)
        one_hot = F.one_hot(torch.from_numpy(tile_pred.astype(np.int64)), num_classes=num_classes)
        votes += one_hot.to(torch.int16)
    labels = votes.argmax(dim=1).numpy()
    runtime_s = round(time.perf_counter() - started, 4)
    histogram = _histogram(labels, names)
    return {
        "runtime_s": runtime_s,
        "labels": labels,
        "names": names,
        "num_classes": num_classes,
        "histogram": histogram,
        "n_uncovered": 0,
        "weight_bytes": weight_path.stat().st_size,
        "color": "zeros; the generator cloud has no RGB",
        "normals": "open3d estimate_normals on the generator coordinates",
        "tta": "segment_scan.TEST_CFG (10 scale/flip passes) and grid 0.04 m",
    }


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    probe = gpu_probe()
    cache = _cache_root()
    attempt: dict[str, Any] = {
        "cloud_loaded": True,
        "n_points": scene.n_points,
        "nvidia_smi": probe["nvidia_smi"],
        "nvidia_query": probe["nvidia_query"],
        "torch_version": probe["torch_version"],
        "torch_cuda_build": probe["torch_cuda_build"],
        "torch_cuda_available": probe["torch_cuda_available"],
        "torch_device": probe["torch_device"],
        "pointcept_importable": False,
        "weights_downloaded": False,
        "weights_committed": False,
        "forward_pass": False,
        "pointgroup_ran": False,
        "pointgroup_reason": "No stud-class PointGroup checkpoint is in this repo.",
    }
    if not probe["nvidia_present"] or not probe["torch_cuda_available"]:
        if not probe["nvidia_present"]:
            why = "nvidia-smi did not report a GPU."
            hardware = "CUDA required for PTv3; no NVIDIA device reported"
        else:
            why = (
                f"NVIDIA GPU is present ({probe['nvidia_query']}), but this interpreter "
                f"has no CUDA torch (torch={probe['torch_version']}, cuda={probe['torch_cuda_build']}, "
                f"available={probe['torch_cuda_available']})."
            )
            hardware = f"GPU present; CUDA torch not available in this interpreter ({probe['torch_version']})"
        blocker = (
            "Pointcept PTv3 was not run. "
            f"{why} "
            "No stud-class checkpoint is in this repo. "
            "BIMStruct3D weights were not used for a forward pass. "
            f"The stage 0 cloud was loaded in-process ({scene.n_points} points). "
            "Detection, geometry, angle, paint, and runtime are null."
        )
        card = blocked_card(
            algorithm_id="A4",
            algorithm=POINTCEPT["name"],
            rank=4,
            license_name="MIT code; BIMStruct3D weights are CC BY-NC-SA 4.0 and were not committed",
            hardware=hardware,
            failure_modes=[
                why,
                "No stud labels and no stud-class PointGroup checkpoint.",
                "A label histogram was not invented.",
            ],
            blocker=blocker,
            blocker_short=why,
            scene=scene_record(scene),
            attempt=attempt,
        )
        return card, []

    fetch_error = _ensure_bimstruct(cache)
    attempt["weights_cache"] = str(cache)
    attempt["weights_downloaded"] = fetch_error is None and (cache / "weights" / "model_best.pth").is_file()
    if fetch_error:
        blocker = (
            "Pointcept PTv3 was not run. "
            f"GPU: {probe['nvidia_query']}. CUDA torch {probe['torch_version']} on {probe['torch_device']}. "
            f"BIMStruct3D cache was not ready: {fetch_error} "
            f"The stage 0 cloud was loaded ({scene.n_points} points) and no forward pass ran. "
            "Detection, geometry, angle, paint, and runtime are null."
        )
        attempt["fetch_error"] = fetch_error
        card = blocked_card(
            algorithm_id="A4",
            algorithm=POINTCEPT["name"],
            rank=4,
            license_name="MIT code; BIMStruct3D weights are CC BY-NC-SA 4.0 and were not committed",
            hardware=f"{probe['torch_device']}; CUDA torch {probe['torch_version']}",
            failure_modes=[
                fetch_error,
                "No stud-class PointGroup checkpoint.",
                "A label histogram was not invented.",
            ],
            blocker=blocker,
            blocker_short="BIMStruct3D checkpoint was not available. No forward pass.",
            scene=scene_record(scene),
            attempt=attempt,
        )
        return card, []

    try:
        result = _forward(scene, cache, "cuda")
    except Exception as exc:
        detail = traceback.format_exc()
        attempt["error"] = f"{type(exc).__name__}: {exc}"
        attempt["traceback"] = detail[-4000:]
        blocker = (
            "Pointcept PTv3 forward pass failed after the GPU and checkpoint were present. "
            f"GPU: {probe['nvidia_query']}. torch {probe['torch_version']}. "
            f"{type(exc).__name__}: {exc} "
            "No label histogram was invented. Stud metrics are null."
        )
        card = blocked_card(
            algorithm_id="A4",
            algorithm=POINTCEPT["name"],
            rank=4,
            license_name="MIT code; BIMStruct3D weights are CC BY-NC-SA 4.0 and were not committed",
            hardware=f"{probe['torch_device']}; CUDA torch {probe['torch_version']}",
            failure_modes=[
                f"Forward pass raised {type(exc).__name__}: {exc}",
                "No stud-class PointGroup checkpoint.",
                "A label histogram was not invented.",
            ],
            blocker=blocker,
            blocker_short=f"Forward pass failed: {type(exc).__name__}: {exc}",
            scene=scene_record(scene),
            attempt=attempt,
        )
        return card, []

    names = result["names"]
    stud_names = [name for name in names if "stud" in name.lower()]
    histogram = result["histogram"]
    note = (
        "BIMStruct3D PTv3 semantic forward pass on this one synthetic stud. "
        f"Classes: {', '.join(names)}. "
        f"Stud-named classes: {stud_names or 'none'}. "
        "No stud box was fit and no paint color was assigned. "
        "PointGroup was not run. "
        "The generator cloud has no RGB, so color features were zeros. "
        "S3DIS or ScanNet mIoU was not copied."
    )
    control = {
        "model": "BIMStruct3D PT-v3m1 semantic segmentation",
        "repo": BIMSTRUCT_REPO,
        "license": "code MIT; weights CC BY-NC-SA 4.0; weights not committed",
        "checkpoint": "weights/model_best.pth",
        "checkpoint_bytes": result["weight_bytes"],
        "device": probe["torch_device"],
        "torch": probe["torch_version"],
        "class_names": names,
        "stud_class_names": stud_names,
        "label_histogram": histogram,
        "n_points_labeled": int(scene.n_points),
        "color_features": result["color"],
        "normals": result["normals"],
        "inference": result["tta"],
        "pointgroup_ran": False,
    }
    attempt["forward_pass"] = True
    attempt["pointcept_importable"] = True
    attempt["class_names"] = names
    short = (
        "BIMStruct3D PTv3 semantic control. "
        f"No stud class ({', '.join(names)}). "
        "Histogram recorded. No stud box and no paint."
    )
    card = control_card(
        algorithm_id="A4",
        algorithm=POINTCEPT["name"],
        rank=4,
        license_name="MIT code; BIMStruct3D weights CC BY-NC-SA 4.0, not committed",
        hardware=f"{probe['torch_device']}; CUDA torch {probe['torch_version']}",
        failure_modes=[
            "Output classes are construction/indoor labels, not studs.",
            "No PointGroup instance head was run.",
            "Zero RGB on a model that was trained with color.",
            "CC BY-NC-SA weights are not a commercial stud model.",
        ],
        note=note,
        scene=scene_record(scene),
        control=control,
        runtime_s=result["runtime_s"],
        implementation={
            "module": "openwall_stud.contenders.pointcept_ptv3",
            "entry": "BIMStruct3D segment_scan.load_model / infer_tile",
            "probe": probe,
            "attempt": attempt,
        },
        implementation_short=short,
    )
    card["_point_colors"] = class_colors(result["labels"], result["num_classes"])
    return card, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attempt Pointcept on the one synthetic stud.")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/pointcept_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"Pointcept stub scorecard written to {path}. No training was run.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_pointcept.json")
    figure = args.figure or (
        repo_root() / "docs" / "research" / "images" / "ozpc-ranks4-5" / "04-pointcept.png"
    )
    publish_attempt(
        algorithm="pointcept",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    print(f"Pointcept one-stud scorecard written to {dest}. status={card['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
