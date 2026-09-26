"""Color Experiment 1 from stored stage0 lean errors. Does not retrain.

Experiment 1 is the all-nine stage0 one-beam scene: one synthetic stud, no
floor, no ceiling, planted lean 0°. Inputs are the published
``angle_mae_deg`` cells in ``artifacts/phase_neg1/all_nine_stage0.json``.
Each model's scorecard ``abs_error_deg`` must match that cell.

Writes ``artifacts/phase_neg1/experiment1_dual_pass.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.paint import DUAL_PASS_RULE, assert_paint_rules, dual_standard_passes

SUMMARY = ROOT / "artifacts" / "phase_neg1" / "all_nine_stage0.json"
SCORECARDS = ROOT / "artifacts" / "scorecards"
OUT = ROOT / "artifacts" / "phase_neg1" / "experiment1_dual_pass.json"


def _threshold(report: dict, key: str) -> float:
    for spec in report["standards"]:
        if spec["key"] == key:
            return float(spec["threshold_deg"])
    raise KeyError(key)


def _colors(report: dict, key: str) -> tuple[str, str]:
    for spec in report["standards"]:
        if spec["key"] == key:
            return spec["absolute"]["color"], spec["sensor"]["color"]
    raise KeyError(key)


def load_rows() -> list[dict]:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = []
    for item in summary["nine"]:
        mae = item.get("angle_mae_deg")
        if mae is None:
            raise ValueError(f"{item['algorithm']} has no stored angle_mae_deg")
        card_path = SCORECARDS / item["scorecard"]
        card = json.loads(card_path.read_text(encoding="utf-8"))
        per_stud = card["angle"]["per_stud"]
        if len(per_stud) != 1:
            raise ValueError(f"{item['algorithm']} expected one stud, got {len(per_stud)}")
        stored = float(per_stud[0]["abs_error_deg"])
        if stored != float(mae):
            raise ValueError(
                f"{item['algorithm']} summary MAE {mae} != scorecard abs_error {stored}"
            )
        if float(per_stud[0]["true_deg"]) != 0.0:
            raise ValueError(f"{item['algorithm']} truth lean is not the stage0 0° lock")
        report = dual_standard_passes(float(mae))
        rows.append(
            {
                "algorithm": item["algorithm"],
                "bucket": item["bucket"],
                "mean_abs_error_deg": float(mae),
                "true_lean_deg": 0.0,
                "standards": report["standards"],
            }
        )
    return rows


def render_markdown(rows: list[dict]) -> str:
    handbook_tau = _threshold(dual_standard_passes(0.0), "handbook_finish_plumb")
    nahb_tau = _threshold(dual_standard_passes(0.0), "nahb_warranty_gauge")
    lines = [
        "| Model | Standard | Threshold (°) | Mean \\|err\\| (°) | Absolute | With sensor ε 0.05° |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    labels = (
        (
            "handbook_finish_plumb",
            "Handbook finish plumb (1/4 in in 10 ft)",
            handbook_tau,
        ),
        (
            "nahb_warranty_gauge",
            "NAHB warranty gauge (3/8 in in 32 in)",
            nahb_tau,
        ),
    )
    for row in rows:
        for key, label, tau in labels:
            absolute, sensor = _colors({"standards": row["standards"]}, key)
            lines.append(
                f"| {row['algorithm']} | {label} | {tau:.5f} | "
                f"{row['mean_abs_error_deg']:.5f} | {absolute} | {sensor} |"
            )
    return "\n".join(lines)


def main() -> None:
    assert_paint_rules()
    rows = load_rows()
    payload = {
        "experiment": "1",
        "scene": "stage0_2x4_lean0.000",
        "description": (
            "Single synthetic stud, no floor, no ceiling. Planted lean 0°. "
            "Colors recomputed from stored angle_mae_deg. Models were not re-run."
        ),
        "rule": DUAL_PASS_RULE,
        "source": "artifacts/phase_neg1/all_nine_stage0.json",
        "rows": rows,
        "markdown": render_markdown(rows),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(payload["markdown"])
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
