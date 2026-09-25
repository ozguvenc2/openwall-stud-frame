"""Write one finder scorecard, its figure, and its day-table row."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openwall_stud.one_stud import apply_verdict, day_notes, figure_lines
from openwall_stud.one_stud_figure import render_finder_figure
from openwall_stud.results_by_day import append_day_row
from openwall_stud.scorecard import write_scorecard
from openwall_stud.synthetic import Scene


def publish_attempt(
    *,
    algorithm: str,
    card: dict[str, Any],
    detections: list,
    scene: Scene,
    out: Path,
    figure: Path | None,
    write_day_row: bool = True,
) -> dict[str, Any]:
    point_colors = card.pop("_point_colors", None)
    verdict = apply_verdict(card)
    card["scorecard_name"] = out.name
    write_scorecard(out, card)
    if figure is not None:
        from openwall_stud.results_by_day import repo_root

        segments = [item.segments_m for item in detections]
        if card.get("status") != "ran":
            banner = "BLOCKED INSTALL"
        elif card.get("stud_metrics_scored") is False:
            banner = "CONTROL — NO STUD BOX"
        elif not segments:
            banner = "RAN, NO BOX"
        else:
            banner = None
        title = f"Rank {card.get('rank')}  {card.get('algorithm')}  [{card.get('status')}]"
        render_finder_figure(
            figure,
            points=scene.points_m,
            segments=segments,
            title=title,
            lines=figure_lines(card),
            banner=banner,
            point_colors=point_colors,
        )
        try:
            card["figure"] = str(figure.resolve().relative_to(repo_root())).replace("\\", "/")
        except ValueError:
            card["figure"] = str(figure).replace("\\", "/")
        write_scorecard(out, card)
    if write_day_row:
        from openwall_stud.results_by_day import repo_root

        append_day_row(
            algorithm=algorithm,
            stage=0,
            scene=scene.name,
            ground_truth_source="synthetic",
            pass_fail=verdict,
            notes=day_notes(card, out.name),
            card=None if verdict in {"blocked_install", "not_run"} else card,
            root=repo_root(),
        )
    return card
