"""Open3D-ML S3DIS control on the one Stage 0 stud.

Open3D 0.20 exposes ``open3d.ml`` only when the ML extra is installed. This
run imports that entry point, does not download S3DIS weights, and does not
invent a label histogram. Office beam/column classes are not studs.

Entrypoint
    python -m openwall_stud.contenders.open3d_ml_s3dis

    ``--stub`` writes the null card without loading the cloud.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from openwall_stud.contenders.common import blocked_card, emit_stub, stub_card
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

OPEN3D_ML = {
    "rank": 5,
    "algorithm_id": "A5",
    "status": "stub",
    "name": "Open3D-ML RandLA-Net or KPConv, S3DIS weights (control only)",
}


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
    except Exception as exc:  # ImportError and missing extras both land here.
        return f"{type(exc).__name__}: {exc}"
    return "open3d.ml.torch imported"


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    probe = _probe_ml()
    imported = probe.startswith("open3d.ml.torch imported")
    blocker = (
        "Open3D-ML S3DIS control did not run a forward pass. "
        f"Import probe: {probe}. "
        "S3DIS RandLA-Net and KPConv weights were not downloaded. "
        "There is no NVIDIA GPU. "
        "The open3d pin stays 0.20.0; a separate ML extra was not installed over it. "
        f"The stage 0 cloud was loaded in-process ({scene.n_points} points). "
        "No label histogram was produced, and no stud box was fit from an office class. "
        "S3DIS mIoU is not copied here. Metrics are null."
    )
    card = blocked_card(
        algorithm_id="A5",
        algorithm=OPEN3D_ML["name"],
        rank=5,
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware="GPU typical for the zoo models; no NVIDIA device in this VM",
        failure_modes=[
            "S3DIS classes are finished office scenes, not a bare 2x4.",
            "Semantic labels are not stud instances.",
            "Weights were not downloaded, so there is no histogram to record.",
            "S3DIS mIoU is not a stud score.",
        ],
        blocker=blocker,
        blocker_short="Open3D-ML weights not loaded and no forward pass. Cloud loaded. Metrics null.",
        scene=scene_record(scene),
        attempt={
            "cloud_loaded": True,
            "n_points": scene.n_points,
            "open3d_ml_torch_probe": probe,
            "ml_torch_imported": imported,
            "weights_downloaded": False,
            "forward_pass": False,
            "label_histogram": None,
        },
    )
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
        repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "05-open3d-ml.png"
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
