"""Run ranks 4 and 5 on the one Stage 0 stud, then stop.

Scene is the same call as PR #15 and PR #16: dressed 2x4, lean 0.05 degrees,
seed 2, angle versus generator +Z. Ranks 1, 2, 3, and 6 are not re-run.

    python scripts/run_ozpc_ranks45.py

Pointcept uses ``.venv`` (CUDA torch 2.7, the BIMStruct3D pin). Open3D-ML
uses ``.venv-o3dml`` (CUDA torch 2.13, the Windows Open3D 0.20 wheel).
``--report-only`` rewrites doc 18 from the scorecards without launching either stack.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCORE_PT = ROOT / "artifacts" / "scorecards" / "one_stud_pointcept.json"
SCORE_ML = ROOT / "artifacts" / "scorecards" / "one_stud_open3d_ml.json"
REPORT_MD = ROOT / "docs" / "research" / "18-ozpc-ranks4-5-run.md"
REPORT_JSON = ROOT / "docs" / "research" / "18-ozpc-ranks4-5-run.json"
PY_PT = ROOT / ".venv" / "Scripts" / "python.exe"
PY_ML = ROOT / ".venv-o3dml" / "Scripts" / "python.exe"


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        text = f"{value:.5f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _load(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _run_module(python: Path, module: str) -> int:
    if not python.is_file():
        print(f"Missing interpreter {python}")
        return 127
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [str(python), "-m", module],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return int(proc.returncode)


def _hist_table(card: dict[str, Any]) -> str:
    rows = ((card.get("control") or {}).get("label_histogram")) or []
    if not rows:
        return "No histogram was recorded.\n"
    lines = ["| Class | Count |", "| --- | --- |"]
    for item in rows:
        lines.append(f"| {item.get('name')} | {item.get('count')} |")
    return "\n".join(lines) + "\n"


def _section(card: dict[str, Any] | None, rank: int) -> str:
    if card is None:
        return f"### Rank {rank}\n\nNo scorecard was written.\n"
    figure = card.get("figure") or ""
    image = ""
    if figure.startswith("docs/research/"):
        image = f"\n\n![{card.get('algorithm')}]({figure[len('docs/research/'):]})\n"
    if card.get("status") == "ran" and card.get("stud_metrics_scored") is False:
        return (
            f"### Rank {card.get('rank')}. {card.get('algorithm')}\n\n"
            "Status: `ran`. Stud stage 0 bars: `control` (not scored). "
            "Precision, recall, section, length, angle, and paint are null on purpose.\n\n"
            f"{card.get('implementation_short') or ''}\n\n"
            f"{card.get('notes', [''])[0]}\n\n"
            f"{_hist_table(card)}"
            f"{image}"
        )
    if card.get("status") == "ran":
        return (
            f"### Rank {card.get('rank')}. {card.get('algorithm')}\n\n"
            f"Status: `ran`. Stage 0 bars: `{card.get('stage0_pass_fail')}`.\n\n"
            f"{card.get('implementation_short') or ''}\n"
            f"{image}"
        )
    return (
        f"### Rank {card.get('rank')}. {card.get('algorithm')}\n\n"
        "Status: `blocked_install`. Stud metrics were not filled.\n\n"
        f"{card.get('blocker')}\n"
        f"{image}"
    )


def _metric_cells(card: dict[str, Any] | None) -> str:
    if card is None:
        return "| — | — | — | — | — | — | — | — | — | — | — |"
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    cost = card.get("cost") or {}
    return (
        f"| {card.get('rank')} | {card.get('algorithm')} | {card.get('status')} | "
        f"{_fmt(det.get('precision'))} | {_fmt(det.get('recall'))} | "
        f"{_fmt(geom.get('max_section_error_mm'))} | {_fmt(geom.get('max_length_error_mm'))} | "
        f"{_fmt(ang.get('mae_deg'))} | — | {_fmt(cost.get('runtime_s'))} | "
        f"{card.get('stage0_pass_fail')} |"
    )


def write_report(pt: dict[str, Any] | None, ml: dict[str, Any] | None) -> None:
    scene = (pt or ml or {}).get("scene") or {}
    probe = ((pt or ml or {}).get("implementation") or {}).get("probe") or {}
    if not probe:
        probe = ((pt or ml or {}).get("attempt") or {})
    date = "2026-09-25"
    payload = {
        "doc": "docs/research/18-ozpc-ranks4-5-run.md",
        "date_america_los_angeles": date,
        "machine": "Oz_PC",
        "stopped_after": "ranks 4 and 5 on one synthetic stud",
        "not_field_accuracy": True,
        "epsilon_locked": False,
        "scene": scene,
        "gpu": {
            "nvidia_query": probe.get("nvidia_query"),
            "torch_device": probe.get("torch_device"),
        },
        "platform": platform.platform(),
        "stacks": [
            {
                "rank": 4,
                "scorecard": "artifacts/scorecards/one_stud_pointcept.json",
                "status": None if pt is None else pt.get("status"),
                "stage0_pass_fail": None if pt is None else pt.get("stage0_pass_fail"),
                "runtime_s": None if pt is None else (pt.get("cost") or {}).get("runtime_s"),
                "control": None if pt is None else pt.get("control"),
                "blocker": None if pt is None else pt.get("blocker"),
            },
            {
                "rank": 5,
                "scorecard": "artifacts/scorecards/one_stud_open3d_ml.json",
                "status": None if ml is None else ml.get("status"),
                "stage0_pass_fail": None if ml is None else ml.get("stage0_pass_fail"),
                "runtime_s": None if ml is None else (ml.get("cost") or {}).get("runtime_s"),
                "control": None if ml is None else ml.get("control"),
                "blocker": None if ml is None else ml.get("blocker"),
            },
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    gpu_line = probe.get("nvidia_query") or "not recorded"
    text = f"""# Oz_PC ranks 4 and 5 on one synthetic stud

Date (America/Los_Angeles): **{date}**. Machine: **Oz_PC**. This note records ranks 4 and 5 only, on the same Stage 0 stud as PR #15 and PR #16. It does not re-run Open3D, PCL, CloudCompare, or pyRANSAC-3D. It is not a field measurement.

Machine-readable twin: [18-ozpc-ranks4-5-run.json](18-ozpc-ranks4-5-run.json).

## Scene

One call to `stage0_single_stud` in `src/openwall_stud/synthetic.py`.

| | |
| --- | --- |
| Nominal | dressed 2×4 |
| Lean | {scene.get('lean_deg', 0.05)}° about +X |
| Seed | {scene.get('seed', 2)} |
| Scene id | `{scene.get('name', 'stage0_2x4_lean0.050')}` |
| Points | {scene.get('n_points', '—')} |
| Spacing | {scene.get('spacing_m', 0.005)} m |
| Noise | {scene.get('noise_std_m', 0.001)} m Gaussian |
| Angle reference | generator +Z (`gravity_z_no_floor_plane`). No floor was fit. The cloud was not rotated. |

## GPU

`nvidia-smi`: {gpu_line}

Pointcept ran under `.venv` with CUDA torch 2.7 (the BIMStruct3D pin). Open3D-ML ran under `.venv-o3dml` with CUDA torch 2.13, because the Windows `open3d==0.20.0` wheel refuses any other minor version (`Pytorch_VERSION` is `2.13.0+cpu` in that wheel; `BUILD_CUDA_MODULE` is false, and RandLA-Net itself is PyTorch).

## Result

Stud precision, recall, section, length, angle, and paint stay empty unless a finder actually emitted a stud box. A control histogram is not those cells. `control` means the forward pass ran and the stage 0 stud bars were not scored.

| Rank | Stack | Status | P | R | Section mm | Length mm | Angle MAE deg | Paint | Runtime s | Stage 0 bars |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{_metric_cells(pt)}
{_metric_cells(ml)}

## Versions

- `platform`: {platform.platform()}
- `python`: {sys.version.split()[0]} (this report process)

## Commands

From the repo root:

```bash
.venv\\Scripts\\python.exe -m openwall_stud.contenders.pointcept_ptv3
.venv-o3dml\\Scripts\\python.exe -m openwall_stud.contenders.open3d_ml_s3dis
python scripts/run_ozpc_ranks45.py
```

`python scripts/run_one_stud_five_finders.py` was not the command for this note. Rank 6 was not re-rolled.

## Finders

{_section(pt, 4)}
{_section(ml, 5)}

## What this run did not do

No second lean, no stage 2 floor, no stage 3 mini wall, no SAM 2, no real scan, no SKIL reading, no PointGroup instance head, no KPConv forward pass, and no claim that a synthetic control is field accuracy. S3DIS mIoU is not a stud score and is not copied into the table above. BIMStruct3D weights (CC BY-NC-SA 4.0) and the S3DIS checkpoint stay in `data/cache/`, which is gitignored.
"""
    REPORT_MD.write_text(text, encoding="utf-8")
    print(f"Wrote {REPORT_MD}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Oz_PC ranks 4 and 5, then stop.")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if not args.report_only:
        print("--- rank 4 pointcept ---")
        code_pt = _run_module(PY_PT, "openwall_stud.contenders.pointcept_ptv3")
        print(f"pointcept exit {code_pt}")
        print("--- rank 5 open3d-ml ---")
        code_ml = _run_module(PY_ML, "openwall_stud.contenders.open3d_ml_s3dis")
        print(f"open3d_ml exit {code_ml}")
    write_report(_load(SCORE_PT), _load(SCORE_ML))
    print("Stopped after ranks 4 and 5 on one stud.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
