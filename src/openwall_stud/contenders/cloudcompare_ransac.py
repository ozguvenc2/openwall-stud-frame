"""CloudCompare RANSAC Shape Detection on the one Stage 0 stud.

Install
    Ubuntu package ``cloudcompare`` (GPL-3.0), invoked as a separate process.
    This repo does not copy or link the GPL sources. The command is
    ``CloudCompare -RANSAC`` with the RANSAC Shape Detection plugin
    (``libQRANSAC_SD_PLUGIN.so``), which is Schnabel, Wahl, and Klein 2007.

    Each primitive inlier set gets its own minimal OBB. Primitives are not
    merged into a stud. A 2x4 is not a cylinder, and coplanar faces are planes.

Entrypoint
    python -m openwall_stud.contenders.cloudcompare_ransac

    ``--stub`` writes the null card and does not launch CloudCompare.

Do not
    Do not link CloudComPy into a closed-source app.
    Do not treat a cylinder fit on a 2x4 as a stud instance.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.common import blocked_card, emit_stub, ran_card, stub_card
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.open3d_baseline import _point_cloud
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

CLOUDCOMPARE = {
    "rank": 3,
    "algorithm_id": "A3",
    "status": "stub",
    "name": "CloudCompare RANSAC-SD / CloudComPy",
}

# Epsilon is a few times the 1 mm generator noise and the 5 mm surface spacing.
# Support is below one stud face and above a handful of noisy points.
RANSAC_ARGS = [
    "EPSILON_ABSOLUTE",
    "0.008",
    "BITMAP_EPSILON_ABSOLUTE",
    "0.020",
    "SUPPORT_POINTS",
    "400",
    "MAX_NORMAL_DEV",
    "25",
    "PROBABILITY",
    "0.01",
    "ENABLE_PRIMITIVE",
    "PLANE",
    "CYLINDER",
    "OUTPUT_INDIVIDUAL_SUBCLOUDS",
]


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A3",
        algorithm=CLOUDCOMPARE["name"],
        rank=3,
        license_name="GPL-3.0",
        hardware="CPU desktop",
        failure_modes=[
            "CloudCompare and CloudComPy are not installed here, so no primitive was fit.",
            "A 2x4 is not a cylinder. A wall of studs is not one plane.",
            "GPL-3.0 if the library is linked into a shipped app.",
        ],
        note="Stub only. RANSAC Shape Detection was not executed. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    return build_stub_card()


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    record = scene_record(scene)
    binary = shutil.which("CloudCompare") or shutil.which("cloudcompare")
    work = repo_root() / "artifacts" / "one_stud" / "cloudcompare"
    work.mkdir(parents=True, exist_ok=True)
    if binary is None:
        card = blocked_card(
            algorithm_id="A3",
            algorithm=CLOUDCOMPARE["name"],
            rank=3,
            license_name="GPL-3.0",
            hardware="CPU",
            failure_modes=["CloudCompare is not on PATH, so RANSAC-SD was not executed."],
            blocker=(
                f"CloudCompare is not on PATH. The stage 0 cloud was generated in-process "
                f"({scene.n_points} points) and no primitive was fit. "
                "GPL sources were not copied into this repo. Metrics are null."
            ),
            blocker_short="CloudCompare binary not on PATH. Cloud was generated and not segmented.",
            scene=record,
            attempt={"cloud_loaded": True, "n_points": scene.n_points, "binary": None},
        )
        return card, []

    ply_path = work / "stud.ply"
    out_dir = work / "primitives"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*"):
        if old.is_file():
            old.unlink()
    _write_ply(ply_path, scene.points_m)
    command = [
        binary,
        "-SILENT",
        "-NO_TIMESTAMP",
        "-AUTO_SAVE",
        "OFF",
        "-C_EXPORT_FMT",
        "PLY",
        "-PLY_EXPORT_FMT",
        "ASCII",
        "-O",
        str(ply_path),
        "-RANSAC",
        *RANSAC_ARGS,
        "OUT_CLOUD_DIR",
        str(out_dir),
    ]
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env.setdefault("XDG_RUNTIME_DIR", "/tmp/runtime-ubuntu")
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        cwd=work,
    )
    runtime_s = time.perf_counter() - started
    log = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-6000:]
    clouds = _load_primitive_clouds(out_dir, ply_path)
    if not clouds:
        clouds = _load_primitive_clouds(work, ply_path)
    attempt = {
        "cloud_loaded": True,
        "n_points": scene.n_points,
        "binary": binary,
        "command": command,
        "returncode": proc.returncode,
        "n_primitive_clouds": len(clouds),
        "output_files": sorted(path.name for path in out_dir.iterdir() if path.is_file()),
        "log_tail": log,
        "gpl": "Separate process. GPL sources were not copied into this repository.",
    }
    failed = proc.returncode != 0 or "Unknown or misplaced command" in log or "No point cloud to attempt RANSAC" in log
    if failed or not clouds and "RANSAC" not in log:
        reason = _failure_reason(proc.returncode, log, clouds)
        card = blocked_card(
            algorithm_id="A3",
            algorithm=CLOUDCOMPARE["name"],
            rank=3,
            license_name="GPL-3.0",
            hardware="CPU",
            failure_modes=[
                "The CloudCompare process did not return primitive point sets.",
                "A 2x4 is not a cylinder. Coplanar faces are planes, not one stud instance.",
                "GPL-3.0 if this library is linked into a shipped app. It was not linked here.",
            ],
            blocker=reason,
            blocker_short="CloudCompare RANSAC-SD did not return primitive clouds. Metrics null.",
            scene=record,
            attempt=attempt,
        )
        return card, []

    from openwall_stud.poststep import score_clusters

    sections, detections = score_clusters(
        scene,
        clouds,
        runtime_s=runtime_s,
        detection_note=(
            "Each CloudCompare RANSAC-SD primitive inlier set is one detection. "
            "Primitives were not merged into a stud. "
            "Counts are this synthetic stud, not a field accuracy."
        ),
        geometry_note=(
            "Section and length are the minimal OBB of one primitive's points versus the dressed stud. "
            "A plane on one face is expected to miss the stud section."
        ),
        angle_note="Truth is the generator lean against +Z. Not a SKIL reading. A face plane's long axis may still lie along the stud.",
        cost={
            "runtime_s": round(runtime_s, 4),
            "license": "GPL-3.0",
            "license_note": "CloudCompare was executed as a separate process. Its sources were not vendored or linked.",
            "hardware": "CPU",
            "n_points_in": scene.n_points,
            "failure_modes": [
                "A rectangular stud is not one Schnabel primitive. Planes describe faces.",
                "A cylinder on a 2x4 is the wrong section.",
                "Enabling both planes and cylinders can emit more than one detection for one stud.",
                "GPL-3.0 blocks shipping a closed app linked to CloudCompare. This run does not link it.",
            ],
            "note": "Runtime includes the CloudCompare process on this one stud. It is not a field budget.",
            "command": command,
            "n_primitive_clouds": len(clouds),
        },
    )
    version = _package_version()
    card = ran_card(
        algorithm_id="A3",
        algorithm=CLOUDCOMPARE["name"],
        rank=3,
        scene=record,
        sections=sections,
        implementation={
            "tool": "CloudCompare RANSAC Shape Detection",
            "package": version,
            "plugin": "libQRANSAC_SD_PLUGIN.so",
            "primitives": ["PLANE", "CYLINDER"],
            "merged_primitives_into_stud": False,
            "attempt": {key: value for key, value in attempt.items() if key != "log_tail"},
            "log_tail": log,
        },
        implementation_short=(
            f"CloudCompare {version} RANSAC-SD, one OBB per plane or cylinder primitive, primitives not merged."
        ),
    )
    return card, detections


def _failure_reason(code: int, log: str, clouds: list[np.ndarray]) -> str:
    tail = " ".join(log.split())[-500:]
    return (
        f"CloudCompare exited {code} and returned {len(clouds)} primitive clouds. "
        f"The stage 0 stud was written to PLY and passed to -RANSAC. "
        f"No stud metric was filled. Log tail: {tail}"
    )


def _package_version() -> str:
    proc = subprocess.run(
        ["dpkg-query", "-W", "-f", "${Version}", "cloudcompare"],
        check=False,
        capture_output=True,
        text=True,
    )
    text = (proc.stdout or "").strip()
    return text or "unknown"


def _write_ply(path: Path, points: np.ndarray) -> None:
    import open3d as o3d

    cloud = _point_cloud(points)
    ok = o3d.io.write_point_cloud(str(path), cloud, write_ascii=True)
    if not ok:
        raise RuntimeError(f"failed to write {path}")


def _load_primitive_clouds(out_dir: Path, source_ply: Path) -> list[np.ndarray]:
    import open3d as o3d

    clouds: list[np.ndarray] = []
    for path in sorted(out_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".ply", ".pcd", ".bin"}:
            continue
        if path.resolve() == source_ply.resolve():
            continue
        cloud = o3d.io.read_point_cloud(str(path))
        points = np.asarray(cloud.points)
        if len(points) >= 10:
            clouds.append(points)
    return clouds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CloudCompare RANSAC-SD on the one synthetic stud, or a stub card.")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/cloudcompare_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"CloudCompare stub scorecard written to {path}. RANSAC-SD was not executed.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_cloudcompare.json")
    figure = args.figure or (
        repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "03-cloudcompare.png"
    )
    publish_attempt(
        algorithm="cloudcompare",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    print(
        f"CloudCompare one-stud scorecard written to {dest}. "
        f"status={card['status']} bars={card.get('stage0_pass_fail')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
