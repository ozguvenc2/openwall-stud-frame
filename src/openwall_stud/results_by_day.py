"""Day-by-day bake-off table.

The CSV is the source of truth. The JSON mirrors it. The markdown is
regenerated from those rows. A same-day re-run of the same stage, scene, and
algorithm updates that row. A new America/Los_Angeles date appends.

Null metrics stay null. This module does not invent field measurements.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

LA = ZoneInfo("America/Los_Angeles")

COLUMNS = (
    "date",
    "stage",
    "scene",
    "algorithm",
    "ground_truth_source",
    "detection_precision",
    "detection_recall",
    "detection_tp",
    "detection_fp",
    "detection_fn",
    "geometry_section_err_mm",
    "geometry_length_err_mm",
    "angle_mae_deg",
    "angle_pct_in_band",
    "paint_correct_pct",
    "device_eps_deg",
    "runtime_s",
    "notes",
    "pass_fail",
)

METRIC_COLUMNS = (
    "detection_precision",
    "detection_recall",
    "detection_tp",
    "detection_fp",
    "detection_fn",
    "geometry_section_err_mm",
    "geometry_length_err_mm",
    "angle_mae_deg",
    "angle_pct_in_band",
    "paint_correct_pct",
    "device_eps_deg",
    "runtime_s",
)

ALGORITHMS = ("open3d", "pcl", "cloudcompare", "pointcept", "open3d_ml")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def today_la(now: datetime | None = None) -> str:
    moment = now or datetime.now(LA)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=LA)
    return moment.astimezone(LA).date().isoformat()


def results_paths(root: Path | None = None) -> dict[str, Path]:
    base = root or repo_root()
    return {
        "csv": base / "artifacts" / "scorecards" / "results_by_day.csv",
        "json": base / "artifacts" / "scorecards" / "results_by_day.json",
        "markdown": base / "docs" / "research" / "13-stud-seg-results-by-day.md",
    }


def _blank_metrics() -> dict[str, Any]:
    return {key: None for key in METRIC_COLUMNS}


def paint_agreement_pct(card: dict[str, Any]) -> float | None:
    """Percent of studs whose production color matches the paint rule.

    While epsilon is unlocked the rule requires yellow on every stud. That
    percentage is not a green/red agreement with a level.
    """
    paint = card.get("paint") or {}
    colors = list(paint.get("production_colors") or [])
    if not colors:
        return None
    if not paint.get("epsilon_locked"):
        matched = sum(1 for color in colors if color == "yellow")
        return round(100.0 * matched / len(colors), 2)
    return None


def row_from_card(
    card: dict[str, Any] | None,
    *,
    date: str,
    stage: int,
    scene: str,
    algorithm: str,
    ground_truth_source: str,
    pass_fail: str,
    notes: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "date": date,
        "stage": int(stage),
        "scene": scene,
        "algorithm": algorithm,
        "ground_truth_source": ground_truth_source,
        "notes": notes,
        "pass_fail": pass_fail,
    }
    row.update(_blank_metrics())
    if pass_fail == "not_run" or card is None:
        return row
    detection = card.get("detection") or {}
    geometry = card.get("geometry") or {}
    angle = card.get("angle") or {}
    paint = card.get("paint") or {}
    cost = card.get("cost") or {}
    row.update(
        {
            "detection_precision": detection.get("precision"),
            "detection_recall": detection.get("recall"),
            "detection_tp": detection.get("true_positives"),
            "detection_fp": detection.get("false_positives"),
            "detection_fn": detection.get("false_negatives"),
            "geometry_section_err_mm": geometry.get("max_section_error_mm"),
            "geometry_length_err_mm": geometry.get("max_length_error_mm"),
            "angle_mae_deg": angle.get("mae_deg"),
            "angle_pct_in_band": angle.get("pct_in_band"),
            "paint_correct_pct": paint_agreement_pct(card),
            "device_eps_deg": paint.get("epsilon_deg") if paint.get("epsilon_locked") else None,
            "runtime_s": cost.get("runtime_s"),
        }
    )
    return row


def _key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (str(row["date"]), str(row["stage"]), str(row["scene"]), str(row["algorithm"]))


def _algo_index(name: str) -> int:
    try:
        return ALGORITHMS.index(name)
    except ValueError:
        return len(ALGORITHMS)


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (str(row["date"]), int(row["stage"]), str(row["scene"]), _algo_index(str(row["algorithm"])), str(row["algorithm"])))


def load_rows(root: Path | None = None) -> list[dict[str, Any]]:
    path = results_paths(root)["csv"]
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            row = {column: raw.get(column, "") for column in COLUMNS}
            row["stage"] = int(row["stage"]) if str(row["stage"]).strip() != "" else None
            for column in METRIC_COLUMNS:
                text = str(row.get(column, "")).strip()
                if text == "":
                    row[column] = None
                else:
                    number = float(text)
                    row[column] = int(number) if number.is_integer() and column.startswith("detection_") and column not in ("detection_precision", "detection_recall") else number
            rows.append(row)
    return rows


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        text = f"{value:.5f}".rstrip("0").rstrip(".")
        return text if text else "0"
    return str(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _cell(row.get(column)) for column in COLUMNS})


def _write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = {
        "schema": "openwall.results_by_day.v1",
        "timezone": "America/Los_Angeles",
        "source": "artifacts/scorecards/results_by_day.csv",
        "note": "Null metrics were not measured. Stub rows are not_run. Synthetic rows are generator comparisons, not field accuracy.",
        "rows": rows,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _md_cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(_cell(value)).replace("|", "/")


def render_markdown(rows: list[dict[str, Any]]) -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    rule = "| " + " | ".join("---" for _ in COLUMNS) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_md_cell(row.get(column)) for column in COLUMNS) + " |")
    table = "\n".join([header, rule, *body]) if body else "\n".join([header, rule, "| " + " | ".join("—" for _ in COLUMNS) + " |"])
    return f"""# Stud segmentation results by day

Dates are **America/Los_Angeles**. This page is regenerated from [`../../artifacts/scorecards/results_by_day.csv`](../../artifacts/scorecards/results_by_day.csv). The JSON mirror is [`../../artifacts/scorecards/results_by_day.json`](../../artifacts/scorecards/results_by_day.json).

One row is one algorithm on one scene that day, compared with that scene’s ground truth. `python scripts/run_stage0_baseline.py` upserts rows when a run finishes: the same date, stage, scene, and algorithm is updated; a later date is appended. Hand-added CSV rows are kept. Refresh this page with `python -m openwall_stud.results_by_day` from the repo root (`PYTHONPATH=src`).

`paint_correct_pct` is the share of studs whose production color matches the paint rule. While `device_eps_deg` is empty, the rule is yellow on every stud, so the percentage is that check only. It is not a green/red score against a level. `pass_fail` is `not_run` when the stack did not execute. Empty cells were not measured.

Ground-truth sources intended for later rows: `synthetic`, `skil`, `total_station`, `hand_label`. Do not type a field number that was not measured.

{table}
"""


def write_all(rows: list[dict[str, Any]], root: Path | None = None) -> None:
    paths = results_paths(root)
    ordered = _sort_rows(rows)
    _write_csv(paths["csv"], ordered)
    _write_json(paths["json"], ordered)
    paths["markdown"].write_text(render_markdown(ordered), encoding="utf-8")


def append_day_row(
    *,
    algorithm: str,
    stage: int,
    scene: str,
    ground_truth_source: str,
    pass_fail: str,
    notes: str,
    card: dict[str, Any] | None = None,
    date: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Insert or replace one day-row and rewrite CSV, JSON, and markdown."""
    if pass_fail not in {"pass", "fail", "not_run"}:
        raise ValueError(f"pass_fail must be pass, fail, or not_run, got {pass_fail!r}")
    if pass_fail != "not_run" and card is None:
        raise ValueError("a measured row needs the scorecard that produced it")
    row = row_from_card(
        card,
        date=date or today_la(),
        stage=stage,
        scene=scene,
        algorithm=algorithm,
        ground_truth_source=ground_truth_source,
        pass_fail=pass_fail,
        notes=notes,
    )
    rows = load_rows(root)
    key = _key(row)
    replaced = False
    for index, existing in enumerate(rows):
        if _key(existing) == key:
            rows[index] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)
    write_all(rows, root)
    return row


def main() -> int:
    """Regenerate the markdown and JSON from the CSV. Does not add rows."""
    rows = load_rows()
    write_all(rows)
    print(f"Rewrote results table from {len(rows)} CSV rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
