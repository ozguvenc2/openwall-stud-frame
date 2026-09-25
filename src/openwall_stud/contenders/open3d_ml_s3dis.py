"""Open3D-ML S3DIS control on the one Stage 0 stud.

Open3D 0.20 exposes ``open3d.ml.torch`` when torch matches the wheel
(Windows wheel: torch 2.13) and the ML extra packages are installed. This
module runs RandLA-Net with the published S3DIS torch checkpoint when that
import succeeds. Office classes are not studs, so stud detection, geometry,
angle, and paint stay null. S3DIS mIoU is not copied. KPConv is not the
checkpoint this pass loads.

Entrypoint
    python -m openwall_stud.contenders.open3d_ml_s3dis

    ``--stub`` writes the null card without loading the cloud.
"""

from __future__ import annotations

import argparse
import random
import time
import traceback
import urllib.request
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

OPEN3D_ML = {
    "rank": 5,
    "algorithm_id": "A5",
    "status": "stub",
    "name": "Open3D-ML RandLA-Net or KPConv, S3DIS weights (control only)",
}

WEIGHT_URL = (
    "https://storage.googleapis.com/open3d-releases/model-zoo/"
    "randlanet_s3dis_202201071330utc.pth"
)
WEIGHT_NAME = "randlanet_s3dis_202201071330utc.pth"


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A5",
        algorithm=OPEN3D_ML["name"],
        rank=5,
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware="GPU typical for the zoo models; not used",
        failure_modes=[
            "S3DIS classes are finished office scenes, not a bare 2x4 wall.",
            "Semantic labels are not stud instances.",
            "Publishing S3DIS mIoU as stud accuracy would be a false claim.",
            "Open3D-ML weights were not downloaded and no forward pass was run.",
        ],
        note="Control-baseline stub. Open3D-ML was not executed. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    return build_stub_card()


def _probe_ml() -> str:
    try:
        import open3d.ml.torch as ml_torch  # noqa: F401
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return "open3d.ml.torch imported"


def _weight_path() -> Path:
    return repo_root() / "data" / "cache" / "open3d-ml" / WEIGHT_NAME


def _ensure_weight(path: Path) -> str | None:
    if path.is_file() and path.stat().st_size > 0:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(WEIGHT_URL, path)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    if not path.is_file() or path.stat().st_size == 0:
        return "download finished without a checkpoint file"
    return None


def _class_names() -> list[str]:
    from open3d._ml3d.datasets.s3dis import S3DIS

    mapping = S3DIS.get_label_to_names()
    return [str(mapping[index]) for index in range(len(mapping))]


def _histogram(labels: np.ndarray, names: list[str]) -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(names):
        rows.append({"id": index, "name": name, "count": int(np.sum(labels == index))})
    return rows


def _forward(scene: Scene, weight: Path, probe: dict[str, Any]) -> dict[str, Any]:
    import open3d.ml as ml3d_root
    import open3d.ml.torch as ml3d

    config_path = Path(ml3d_root.__file__).resolve().parent.parent / "_ml3d" / "configs" / "randlanet_s3dis.yml"
    if not config_path.is_file():
        # open3d.ml lives in open3d/ml/__init__.py; configs are open3d/_ml3d/configs.
        config_path = Path(ml3d_root.__file__).resolve().parents[1] / "_ml3d" / "configs" / "randlanet_s3dis.yml"
    cfg = ml3d_root.utils.Config.load_from_file(str(config_path))
    model = ml3d.models.RandLANet(**cfg.model)
    log_dir = weight.parent / "logs"
    pipe_kwargs = dict(cfg.pipeline)
    pipe_kwargs["batch_size"] = 1
    pipe_kwargs["main_log_dir"] = str(log_dir)
    pipe_kwargs["device"] = "cuda"
    pipeline = ml3d.pipelines.SemanticSegmentation(model, dataset=None, **pipe_kwargs)
    pipeline.load_ckpt(ckpt_path=str(weight), is_resume=False)

    points = np.asarray(scene.points_m, dtype=np.float32)
    # S3DIS feat is RGB. This generator has none, so the three channels are zero.
    feat = np.zeros((points.shape[0], 3), dtype=np.float32)
    labels_placeholder = np.zeros((points.shape[0],), dtype=np.int32)
    data = {"point": points, "feat": feat, "label": labels_placeholder}

    random.seed(scene.seed)
    np.random.seed(scene.seed)
    import torch

    torch.manual_seed(scene.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(scene.seed)

    started = time.perf_counter()
    result = pipeline.run_inference(data)
    runtime_s = round(time.perf_counter() - started, 4)
    pred = np.asarray(result["predict_labels"]).reshape(-1)
    names = _class_names()
    return {
        "runtime_s": runtime_s,
        "labels": pred,
        "names": names,
        "histogram": _histogram(pred, names),
        "n_pred": int(pred.shape[0]),
        "config": str(config_path),
        "weight_bytes": weight.stat().st_size,
        "torch": probe["torch_version"],
        "device": probe["torch_device"],
    }


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    probe = gpu_probe()
    ml_probe = _probe_ml()
    imported = ml_probe.startswith("open3d.ml.torch imported")
    weight = _weight_path()
    attempt: dict[str, Any] = {
        "cloud_loaded": True,
        "n_points": scene.n_points,
        "nvidia_smi": probe["nvidia_smi"],
        "nvidia_query": probe["nvidia_query"],
        "torch_version": probe["torch_version"],
        "torch_cuda_build": probe["torch_cuda_build"],
        "torch_cuda_available": probe["torch_cuda_available"],
        "torch_device": probe["torch_device"],
        "open3d_ml_torch_probe": ml_probe,
        "ml_torch_imported": imported,
        "weights_downloaded": False,
        "weights_committed": False,
        "forward_pass": False,
        "label_histogram": None,
        "model": "RandLANet",
        "dataset_weights": "S3DIS",
        "kpconv_ran": False,
    }
    hardware = probe["torch_device"] or probe["nvidia_query"] or "no CUDA torch in this interpreter"

    def _blocked(short: str, blocker: str, modes: list[str]) -> tuple[dict[str, Any], list]:
        card = blocked_card(
            algorithm_id="A5",
            algorithm=OPEN3D_ML["name"],
            rank=5,
            license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
            hardware=str(hardware),
            failure_modes=modes,
            blocker=blocker,
            blocker_short=short,
            scene=scene_record(scene),
            attempt=attempt,
        )
        return card, []

    if not probe["nvidia_present"] and not probe["torch_cuda_available"]:
        return _blocked(
            "No NVIDIA GPU reported and no CUDA torch. No forward pass.",
            (
                "Open3D-ML S3DIS control did not run a forward pass. "
                f"nvidia-smi query: {probe['nvidia_query'] or 'absent'}. "
                f"Import probe: {ml_probe}. "
                "S3DIS weights were not loaded. Metrics are null."
            ),
            [
                "No NVIDIA GPU reported in this process.",
                "S3DIS classes are finished office scenes, not a bare 2x4.",
                "A label histogram was not invented.",
            ],
        )
    if not imported:
        return _blocked(
            f"open3d.ml.torch did not import. {ml_probe}",
            (
                "Open3D-ML S3DIS control did not run a forward pass. "
                f"GPU: {probe['nvidia_query']}. torch {probe['torch_version']} "
                f"cuda_available={probe['torch_cuda_available']}. "
                f"Import probe: {ml_probe}. "
                "The Windows Open3D 0.20 wheel asks for torch 2.13. "
                "No label histogram was produced. S3DIS mIoU was not copied. Metrics are null."
            ),
            [
                ml_probe,
                "S3DIS classes are finished office scenes, not a bare 2x4.",
                "A label histogram was not invented.",
                "S3DIS mIoU is not a stud score.",
            ],
        )

    fetch_error = _ensure_weight(weight)
    attempt["weights_downloaded"] = fetch_error is None and weight.is_file()
    attempt["weight_path"] = str(weight)
    if fetch_error:
        return _blocked(
            f"S3DIS RandLA-Net checkpoint was not downloaded. {fetch_error}",
            (
                "Open3D-ML imported, and the GPU is present, but the S3DIS checkpoint "
                f"did not download ({fetch_error}). No forward pass. Metrics are null."
            ),
            [
                fetch_error,
                "S3DIS classes are finished office scenes, not a bare 2x4.",
                "A label histogram was not invented.",
            ],
        )

    try:
        result = _forward(scene, weight, probe)
    except Exception as exc:
        attempt["error"] = f"{type(exc).__name__}: {exc}"
        attempt["traceback"] = traceback.format_exc()[-4000:]
        return _blocked(
            f"Forward pass failed: {type(exc).__name__}: {exc}",
            (
                "Open3D-ML RandLA-Net S3DIS forward pass failed. "
                f"GPU: {probe['nvidia_query']}. torch {probe['torch_version']}. "
                f"{type(exc).__name__}: {exc} "
                "No label histogram was invented. Stud metrics are null. S3DIS mIoU was not copied."
            ),
            [
                f"Forward pass raised {type(exc).__name__}: {exc}",
                "S3DIS classes are finished office scenes, not a bare 2x4.",
                "A label histogram was not invented.",
            ],
        )

    names = result["names"]
    stud_names = [name for name in names if "stud" in name.lower()]
    note = (
        "Open3D-ML RandLA-Net S3DIS forward pass on this one synthetic stud. "
        f"Classes: {', '.join(names)}. "
        f"Stud-named classes: {stud_names or 'none'}. "
        "RGB features were zeros because the generator cloud has no color. "
        "The library's own sampler pads when the subsampled cloud is shorter than 40960 points. "
        f"predict_labels length {result['n_pred']} on {scene.n_points} input points. "
        "Placeholder API labels were zeros and were not treated as ground truth. "
        "No stud box was fit and no paint color was assigned. "
        "KPConv was not run. S3DIS mIoU was not copied."
    )
    control = {
        "model": "RandLANet",
        "dataset_weights": "S3DIS",
        "checkpoint": WEIGHT_NAME,
        "checkpoint_url": WEIGHT_URL,
        "checkpoint_bytes": result["weight_bytes"],
        "config": result["config"],
        "device": result["device"],
        "torch": result["torch"],
        "class_names": names,
        "stud_class_names": stud_names,
        "label_histogram": result["histogram"],
        "n_points_in": scene.n_points,
        "n_points_labeled": result["n_pred"],
        "color_features": "zeros; the generator cloud has no RGB",
        "sampler_seed": scene.seed,
        "kpconv_ran": False,
        "s3dis_miou_copied": False,
    }
    attempt["forward_pass"] = True
    attempt["label_histogram"] = result["histogram"]
    short = (
        "RandLA-Net S3DIS control. "
        f"No stud class ({', '.join(names)}). "
        "Histogram recorded. No stud box and no paint."
    )
    card = control_card(
        algorithm_id="A5",
        algorithm=OPEN3D_ML["name"],
        rank=5,
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware=f"{probe['torch_device']}; CUDA torch {probe['torch_version']}",
        failure_modes=[
            "S3DIS classes are finished office scenes, not a bare 2x4.",
            "Semantic labels are not stud instances.",
            "Zero RGB on a model trained with office color.",
            "S3DIS mIoU is not a stud score and was not copied.",
        ],
        note=note,
        scene=scene_record(scene),
        control=control,
        runtime_s=result["runtime_s"],
        implementation={
            "module": "openwall_stud.contenders.open3d_ml_s3dis",
            "entry": "open3d.ml.torch RandLANet + SemanticSegmentation.run_inference",
            "probe": probe,
            "attempt": attempt,
        },
        implementation_short=short,
    )
    card["_point_colors"] = class_colors(result["labels"], len(names))
    return card, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attempt the Open3D-ML S3DIS control on the one synthetic stud.")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/open3d_ml_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"Open3D-ML stub scorecard written to {path}. No forward pass was run.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_open3d_ml.json")
    figure = args.figure or (
        repo_root() / "docs" / "research" / "images" / "ozpc-ranks4-5" / "05-open3d-ml.png"
    )
    publish_attempt(
        algorithm="open3d_ml",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    print(f"Open3D-ML one-stud scorecard written to {dest}. status={card['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
