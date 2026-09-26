"""Write the full-room catch summary from scenario JSON already on disk.

Missing models stay blank. This does not re-run a finder and does not edit
Experiment 1.

    .venv\\Scripts\\python.exe scripts/aggregate_fullroom_catch.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "artifacts" / "fullroom" / "results"
SUMMARY = ROOT / "artifacts" / "fullroom" / "catch_summary.json"
DOC = ROOT / "docs" / "research" / "41-fullroom-catch-tables.md"

LETTERS = tuple("ABCDEFGHIJ")
MODELS = (
    "open3d",
    "pointcept",
    "open3d_ml",
    "pcl",
    "pyransac3d",
    "pointsam",
    "sam3d",
    "openmask3d",
    "segment3d",
)
GAUGES = (
    ("handbook_finish_plumb", "Handbook"),
    ("nahb_warranty_gauge", "NAHB"),
)
COLUMNS = ("absolute", "sensor")


def _load(letter: str, model: str) -> dict | None:
    path = RESULTS / f"{letter}_{model}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _cell(row: dict | None, gauge: str, column: str) -> str:
    if row is None:
        return "not run"
    if row.get("status") == "not_adapted":
        return "not adapted"
    if row.get("status") != "ok":
        return row.get("status") or "unknown"
    tally = row["catch"]["tallies"][gauge][column]
    expected = tally["n_expected_red"]
    caught = tally["n_caught_red"]
    if expected == 0:
        return f"0 expected ({tally['n_matched']}/28 matched)"
    rate = tally["catch_rate_red"]
    return f"{caught}/{expected} ({rate})"


def _yellow_cell(row: dict | None, gauge: str, column: str) -> str:
    if row is None or row.get("status") != "ok":
        return "—"
    tally = row["catch"]["tallies"][gauge][column]
    expected = tally["n_expected_yellow"]
    if expected == 0:
        return "0 expected"
    return f"{tally['n_caught_yellow']}/{expected}"


def build_summary() -> dict:
    scenes = []
    calibration_deltas = []
    for letter in LETTERS:
        models = {}
        for model in MODELS:
            row = _load(letter, model)
            models[model] = None if row is None else {
                "status": row.get("status"),
                "catch": None if row.get("status") != "ok" else row.get("catch", {}).get("tallies"),
                "n_matched": None if row.get("status") != "ok" else row.get("catch", {}).get("n_matched"),
                "runtime_s": None if row.get("status") != "ok" else (row.get("model_extra") or {}).get("runtime_s"),
            }
            if row and row.get("calibration"):
                cal = row["calibration"]
                calibration_deltas.append(
                    {
                        "letter": letter,
                        "model": model,
                        "display_rounding_delta_handbook_deg": cal.get("display_rounding_delta_handbook_deg"),
                        "display_rounding_delta_nahb_deg": cal.get("display_rounding_delta_nahb_deg"),
                        "improvement": cal.get("improvement"),
                    }
                )
        scenes.append({"letter": letter, "models": models})
    improvements = sorted({item.get("improvement") for item in calibration_deltas})
    return {
        "status": "ok",
        "experiment": "fullroom_phase4",
        "catch_definition": (
            "Caught red means the stud was matched within 0.15 m and the measured "
            "lean from the floor normal colors red on that gauge and column. "
            "Expected red is the planted-lean plumb call. The error call is stored "
            "on each result JSON and is not this rate."
        ),
        "scenes": scenes,
        "calibration_deltas": calibration_deltas,
        "calibration_improvement": improvements,
        "n_result_files": len(list(RESULTS.glob("*.json"))) if RESULTS.is_dir() else 0,
    }


def _zero_note() -> str:
    """Explain measured zeros. Missing files stay a short sentence."""
    pcl = _load("A", "pcl")
    ransac = _load("A", "pyransac3d")
    parts = []
    if pcl and pcl.get("status") == "ok":
        extra = pcl.get("model_extra") or {}
        parts.append(
            f"PCL on scene A: native region growing "
            f"{extra.get('native_pcl_region_growing')}, "
            f"{extra.get('n_members')} member after adjacency, "
            f"{pcl['catch']['n_detections']} detections after the existing stud gate "
            f"(section, length, upright). Catch stays 0 because nothing matched."
        )
    if ransac and ransac.get("status") == "ok":
        extra = ransac.get("model_extra") or {}
        parts.append(
            f"pyRANSAC-3D on scene A: stopped `{extra.get('stopped')}`, "
            f"accepted {extra.get('n_accepted')} cuboids, "
            f"MAX_CUBOIDS {extra.get('max_cuboids')}. "
            "Those existing limits were not raised."
        )
    if not parts:
        return "No geometry extra was on disk for scene A."
    return " ".join(parts)


def _markdown(summary: dict) -> str:
    lines = [
        "# Full-room catch tables",
        "",
        "Date (America/Los_Angeles): **2026-09-26**. Numbers are read from `artifacts/fullroom/results/`. A blank model is `not run`. A foundation tool whose stage-0 writer cannot take a 28-stud room is `not adapted` and has no invented rate.",
        "",
        "Catch rate is the plumb call: measured lean from the floor normal, colored with the locked dual gauges, compared with the planted lean. |measured − planted| is the error call on each result file and is not the supposed-red count. Production paint stays yellow. Experiment 1 tables are unchanged.",
        "",
        "Calibration ran `assert_paint_rules()` before each scenario. Display rounding of the Handbook and NAHB atan values is the only delta. No threshold was edited (`improvement: none`).",
        "",
        "## Handbook absolute red catch",
        "",
        "| Scene | " + " | ".join(MODELS) + " |",
        "| --- | " + " | ".join("---:" for _ in MODELS) + " |",
    ]
    for letter in LETTERS:
        cells = []
        for model in MODELS:
            loaded = _load(letter, model)
            cells.append(_cell(loaded, "handbook_finish_plumb", "absolute"))
        lines.append(f"| {letter} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## NAHB absolute red catch",
            "",
            "| Scene | " + " | ".join(MODELS) + " |",
            "| --- | " + " | ".join("---:" for _ in MODELS) + " |",
        ]
    )
    for letter in LETTERS:
        cells = []
        for model in MODELS:
            cells.append(_cell(_load(letter, model), "nahb_warranty_gauge", "absolute"))
        lines.append(f"| {letter} | " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## Sensor-column red catch (ε = 0.05°)",
            "",
            "Same catch rule. Yellow catches for scenes that plant a sensor yellow are in the result JSON (`n_caught_yellow`).",
            "",
            "| Scene | Model | Handbook sensor red | NAHB sensor red | Handbook sensor yellow | NAHB sensor yellow |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for letter in LETTERS:
        for model in MODELS:
            loaded = _load(letter, model)
            if loaded is None or loaded.get("status") != "ok":
                continue
            lines.append(
                "| {letter} | {model} | {hs} | {ns} | {hy} | {ny} |".format(
                    letter=letter,
                    model=model,
                    hs=_cell(loaded, "handbook_finish_plumb", "sensor"),
                    ns=_cell(loaded, "nahb_warranty_gauge", "sensor"),
                    hy=_yellow_cell(loaded, "handbook_finish_plumb", "sensor"),
                    ny=_yellow_cell(loaded, "nahb_warranty_gauge", "sensor"),
                )
            )
    ran = summary["n_result_files"]
    lines.extend(
        [
            "",
            "## What the zeros are",
            "",
            _zero_note(),
            "",
            f"Result files on disk when this note was written: {ran}.",
            "",
            "Self-healing queue: `scripts/experiment_queue_runner.py`. Invoke note: [40-experiment-queue-runner.md](40-experiment-queue-runner.md). Scenes: [39-fullroom-scenes.md](39-fullroom-scenes.md).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    summary = build_summary()
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    DOC.write_text(_markdown(summary), encoding="utf-8")
    print(f"wrote {SUMMARY.relative_to(ROOT)}", flush=True)
    print(f"wrote {DOC.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
