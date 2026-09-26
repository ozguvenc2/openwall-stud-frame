"""One coherent stage0_2x4_lean0.000 pass across all nine bake-off tools.

Shells into the env each tool already uses on Oz_PC. CloudCompare stays out.

    .venv\\Scripts\\python.exe scripts/phase_neg1_all_nine_stage0.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "artifacts" / "phase_neg1"
OUT_TABLE = PHASE / "all_nine_stage0.json"

WIN_GEO = ROOT / ".venv" / "Scripts" / "python.exe"
WIN_PC = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe")
WIN_O3DML = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml\Scripts\python.exe")
WSL_PY = "/home/pegassy/mlenv/bin/python"
ROOT_WSL = "/mnt/c/Repos/openwall-stud-frame"


def _run(cmd: list[str], *, cwd: Path | None = None) -> dict:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    wall_s = round(time.perf_counter() - started, 3)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "wall_s": wall_s,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }


def _load_rows(name: str) -> list[dict]:
    path = PHASE / name
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main() -> int:
    PHASE.mkdir(parents=True, exist_ok=True)
    steps = []

    # 1) Geometry: Open3D, PCL, pyRANSAC-3D
    steps.append(
        (
            "geometry",
            _run([str(WIN_GEO), str(ROOT / "scripts" / "phase_neg1_stage0_round.py"), "--role", "geometry"]),
        )
    )
    # 2) Pointcept control + stud head
    steps.append(
        (
            "pointcept",
            _run([str(WIN_PC), str(ROOT / "scripts" / "phase_neg1_stage0_round.py"), "--role", "pointcept"]),
        )
    )
    # 3) Open3D-ML control + stud head
    steps.append(
        (
            "o3dml",
            _run([str(WIN_O3DML), str(ROOT / "scripts" / "phase_neg1_stage0_round.py"), "--role", "o3dml"]),
        )
    )
    # 4) Foundation — SAM3D on Windows ranks45
    steps.append(
        (
            "sam3d",
            _run(
                [
                    str(WIN_PC),
                    str(ROOT / "scripts" / "phase_neg1_stage0_foundation.py"),
                    "--tool",
                    "sam3d",
                ]
            ),
        )
    )
    # 5–7) Foundation on WSL mlenv
    for tool in ("pointsam", "openmask3d", "segment3d"):
        steps.append(
            (
                tool,
                _run(
                    [
                        "wsl",
                        "-e",
                        WSL_PY,
                        f"{ROOT_WSL}/scripts/phase_neg1_stage0_foundation.py",
                        "--tool",
                        tool,
                    ]
                ),
            )
        )

    rows: list[dict] = []
    for name in (
        "stage0_round_geometry.json",
        "stage0_round_pointcept.json",
        "stage0_round_o3dml.json",
        "stage0_round_pointsam.json",
        "stage0_round_sam3d.json",
        "stage0_round_openmask3d.json",
        "stage0_round_segment3d.json",
    ):
        rows.extend(_load_rows(name))

    # Canonical nine: supervised slots use the separate 2-class stud heads.
    # Published BIMStruct / S3DIS controls stay listed under controls.
    nine_spec = (
        ("open3d", "open3d", "geometry-first"),
        ("pcl", "pcl", "geometry-first"),
        ("pyransac3d", "pyransac3d", "geometry-first"),
        ("pointcept_stud_head", "pointcept_finetune", "supervised"),
        ("open3d_ml_stud_head", "open3d_ml_finetune", "supervised"),
        ("pointsam", "pointsam", "promptable-foundation"),
        ("sam3d", "sam3d", "promptable-foundation"),
        ("openmask3d", "openmask3d", "promptable-foundation"),
        ("segment3d", "segment3d", "promptable-foundation"),
    )
    by_alg = {row.get("algorithm"): row for row in rows}
    table = []
    for label, key, bucket in nine_spec:
        row = by_alg.get(key)
        if row is None:
            table.append(
                {
                    "algorithm": label,
                    "bucket": bucket,
                    "pass_fail": "fail",
                    "reason": "no stage0 row produced",
                }
            )
            continue
        entry = {
            "algorithm": label,
            "bucket": bucket,
            "pass_fail": row.get("pass_fail") or row.get("status"),
            "scorecard": row.get("scorecard"),
            "runtime_s": row.get("runtime_s"),
            "precision": row.get("precision"),
            "recall": row.get("recall"),
            "section_mm": row.get("section_mm"),
            "length_mm": row.get("length_mm"),
            "angle_mae_deg": row.get("angle_mae_deg"),
            "reason": row.get("reason")
            or (
                "published control vocabulary; stud cells null"
                if row.get("pass_fail") == "control"
                else str(row.get("pass_fail"))
            ),
        }
        table.append(entry)

    extras = [row for row in rows if row.get("algorithm") in ("pointcept", "open3d_ml")]
    report = {
        "scene": "stage0_2x4_lean0.000",
        "n_points": 25666,
        "cloudcompare": "OUT of bake-off",
        "nine": table,
        "supervised_stud_heads": extras,
        "step_logs": [
            {"step": name, "returncode": log["returncode"], "wall_s": log["wall_s"], "stderr_tail": log["stderr_tail"]}
            for name, log in steps
        ],
    }
    OUT_TABLE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    failed_steps = [name for name, log in steps if log["returncode"] != 0]
    if failed_steps:
        print(f"steps with non-zero exit: {failed_steps}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
