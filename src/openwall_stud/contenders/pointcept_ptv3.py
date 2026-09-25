"""Pointcept PTv3 / PointGroup on the one Stage 0 stud.

The finder loads that cloud and then tries to import a CUDA Pointcept stack.
This VM has no NVIDIA device. BIMStruct3D weights are not downloaded: they are
CC BY-NC-SA 4.0 and have no stud class. No forward pass is invented.

Entrypoint
    python -m openwall_stud.contenders.pointcept_ptv3

    ``--stub`` writes the null card without loading the cloud.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path
from typing import Any

from openwall_stud.contenders.common import blocked_card, emit_stub, stub_card
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

POINTCEPT = {
    "rank": 4,
    "algorithm_id": "A4",
    "status": "stub",
    "name": "Pointcept PTv3 / PointGroup (hook only until labeled Stage 5)",
}


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


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    torch_spec = importlib.util.find_spec("torch")
    pointcept_spec = importlib.util.find_spec("pointcept")
    nvidia = shutil.which("nvidia-smi")
    blocker = (
        "Pointcept PTv3 was not run. "
        f"nvidia-smi: {nvidia or 'absent'}. "
        f"torch importable: {torch_spec is not None}. "
        f"pointcept importable: {pointcept_spec is not None}. "
        "There is no NVIDIA device in this VM, so a CUDA PTv3 / PointGroup forward pass cannot execute. "
        "Torch and Pointcept were not installed for a CPU-only import that still cannot segment. "
        "No stud-class checkpoint is in this repo. "
        "BIMStruct3D weights were not downloaded (CC BY-NC-SA 4.0; classes are wall, column, clutter, and similar, not stud). "
        f"The stage 0 cloud was loaded in-process ({scene.n_points} points) and no forward pass ran. "
        "Detection, geometry, angle, paint, and runtime are null."
    )
    card = blocked_card(
        algorithm_id="A4",
        algorithm=POINTCEPT["name"],
        rank=4,
        license_name="MIT code; BIMStruct3D weights are CC BY-NC-SA 4.0 and were not downloaded",
        hardware="CUDA required for PTv3; no NVIDIA device",
        failure_modes=[
            "No NVIDIA GPU, so the CUDA stack was not installed and was not run.",
            "No stud labels and no stud-class checkpoint.",
            "BIMStruct3D has no stud class and its weights were not fetched.",
            "A label histogram was not invented.",
        ],
        blocker=blocker,
        blocker_short="No NVIDIA GPU and no stud checkpoint. Cloud loaded, no forward pass.",
        scene=scene_record(scene),
        attempt={
            "cloud_loaded": True,
            "n_points": scene.n_points,
            "nvidia_smi": nvidia,
            "torch_importable": torch_spec is not None,
            "pointcept_importable": pointcept_spec is not None,
            "weights_downloaded": False,
            "forward_pass": False,
        },
    )
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
        repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "04-pointcept.png"
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
