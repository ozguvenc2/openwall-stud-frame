"""Shared stub scorecard for contenders that are not executed here."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Any

from openwall_stud.scorecard import empty_sections, write_scorecard


def stub_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    note: str,
) -> dict[str, Any]:
    sections = empty_sections()
    sections["detection"]["note"] = note
    sections["geometry"]["note"] = note
    sections["angle"]["note"] = note
    sections["paint"]["note"] = note
    sections["paint"]["epsilon_locked"] = False
    sections["cost"]["license"] = license_name
    sections["cost"]["hardware"] = hardware
    sections["cost"]["failure_modes"] = failure_modes
    sections["cost"]["note"] = note
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": None,
        "status": "stub_not_run",
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        **sections,
        "notes": [note],
    }


def emit_stub(path: Path, card: dict[str, Any]) -> Path:
    return write_scorecard(path, card)


def blocked_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    blocker: str,
    blocker_short: str,
    scene: dict[str, Any],
    attempt: dict[str, Any],
) -> dict[str, Any]:
    """Scorecard for a finder that loaded the cloud and could not run.

    Detection, geometry, angle, paint colors, and runtime stay null.
    """
    sections = empty_sections()
    for key in ("detection", "geometry", "angle", "paint", "cost"):
        sections[key]["note"] = blocker
    sections["paint"]["epsilon_locked"] = False
    sections["cost"]["license"] = license_name
    sections["cost"]["hardware"] = hardware
    sections["cost"]["failure_modes"] = failure_modes
    sections["cost"]["runtime_s"] = None
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": 0,
        "status": "blocked_install",
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        "measurement_scope": "not measured; the stack did not segment this cloud",
        "scene": scene,
        "attempt": attempt,
        "blocker": blocker,
        "blocker_short": blocker_short,
        **sections,
        "notes": [blocker],
    }


_CLASS_PALETTE = (
    (0.75, 0.22, 0.17),
    (0.20, 0.45, 0.72),
    (0.85, 0.55, 0.20),
    (0.30, 0.55, 0.32),
    (0.55, 0.32, 0.62),
    (0.15, 0.60, 0.62),
    (0.70, 0.40, 0.55),
    (0.45, 0.40, 0.22),
    (0.25, 0.25, 0.28),
    (0.62, 0.62, 0.20),
    (0.40, 0.55, 0.75),
    (0.72, 0.30, 0.30),
    (0.35, 0.35, 0.35),
    (0.55, 0.55, 0.55),
    (0.80, 0.75, 0.40),
    (0.25, 0.40, 0.55),
)


def class_colors(labels: Any, n_classes: int) -> Any:
    """RGB colors in 0–1 for a per-point class id. Ids outside the palette stay gray."""
    import numpy as np

    ids = np.asarray(labels).reshape(-1)
    palette = np.array(_CLASS_PALETTE, dtype=np.float32)
    colors = np.full((len(ids), 3), 0.65, dtype=np.float32)
    for class_id in range(max(n_classes, 0)):
        colors[ids == class_id] = palette[class_id % len(palette)]
    return colors


def gpu_probe() -> dict[str, Any]:
    """Read nvidia-smi and the torch build in this interpreter.

    A CPU torch wheel on a machine that has a GPU is reported as such.
    This does not invent a device.
    """
    nvidia = shutil.which("nvidia-smi")
    query = None
    if nvidia:
        proc = subprocess.run(
            [
                nvidia,
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        query = (proc.stdout or "").strip() or (proc.stderr or "").strip() or None
    torch_version = None
    cuda_build = None
    cuda_available = False
    device_name = None
    torch_error = None
    if importlib.util.find_spec("torch") is not None:
        try:
            import torch

            torch_version = torch.__version__
            cuda_build = torch.version.cuda
            cuda_available = bool(torch.cuda.is_available())
            if cuda_available:
                device_name = torch.cuda.get_device_name(0)
        except Exception as exc:
            torch_error = f"{type(exc).__name__}: {exc}"
    return {
        "nvidia_smi": nvidia,
        "nvidia_query": query,
        "nvidia_present": bool(query),
        "torch_importable": torch_version is not None,
        "torch_version": torch_version,
        "torch_cuda_build": cuda_build,
        "torch_cuda_available": cuda_available,
        "torch_device": device_name,
        "torch_error": torch_error,
    }


def control_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    license_name: str,
    hardware: str,
    failure_modes: list[str],
    note: str,
    scene: dict[str, Any],
    control: dict[str, Any],
    runtime_s: float,
    implementation: dict[str, Any],
    implementation_short: str,
) -> dict[str, Any]:
    """A forward pass ran. Stud detection, geometry, angle, and paint stay null.

    The label histogram in ``control`` is the measurement. No stud box is fit
    from a class that is not a stud, and no paint color is invented.
    """
    sections = empty_sections()
    for key in ("detection", "geometry", "angle", "paint", "cost"):
        sections[key]["note"] = note
    sections["paint"]["epsilon_locked"] = False
    sections["cost"]["license"] = license_name
    sections["cost"]["hardware"] = hardware
    sections["cost"]["failure_modes"] = failure_modes
    sections["cost"]["runtime_s"] = runtime_s
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": 0,
        "status": "ran",
        "stud_metrics_scored": False,
        "epsilon_locked": False,
        "metrics_are_measurements": False,
        "measurement_scope": (
            "label histogram from one forward pass on this synthetic cloud; "
            "stud detection, geometry, angle, and paint were not scored"
        ),
        "scene": scene,
        "control": control,
        "implementation": implementation,
        "implementation_short": implementation_short,
        **sections,
        "notes": [note],
    }


def ran_card(
    *,
    algorithm_id: str,
    algorithm: str,
    rank: int,
    scene: dict[str, Any],
    sections: dict[str, Any],
    implementation: dict[str, Any],
    implementation_short: str,
) -> dict[str, Any]:
    return {
        "schema": "openwall.stud_scorecard.v1",
        "algorithm_id": algorithm_id,
        "algorithm": algorithm,
        "rank": rank,
        "stage": 0,
        "status": "ran",
        "epsilon_locked": False,
        "metrics_are_measurements": True,
        "measurement_scope": "synthetic generator, this process, one stud",
        "scene": scene,
        "implementation": implementation,
        "implementation_short": implementation_short,
        **sections,
        "notes": [
            "Synthetic stage 0 only. Not a field measurement. "
            "Device epsilon is unlocked, so production paint is yellow."
        ],
    }
