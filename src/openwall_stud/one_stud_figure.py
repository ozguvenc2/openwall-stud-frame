"""Screenshots of the one synthetic stud plus any OBB a finder actually fit."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

BG = "#f6f3ec"
INK = "#1f1a17"
MUTED = "#5e584f"
WOOD = "#c4844a"
BOX = "#10243f"
LINE = "#d9d2c5"


def render_finder_figure(
    path: Path,
    *,
    points: np.ndarray,
    segments: list[np.ndarray],
    title: str,
    lines: list[str],
    banner: str | None,
    point_colors: np.ndarray | None = None,
) -> Path:
    """Draw the stud. A banner is the blocked scaffold. No box is invented."""
    path.parent.mkdir(parents=True, exist_ok=True)
    shown, shown_colors = _subsample(points, 12000, seed=0, colors=point_colors)
    color = WOOD if shown_colors is None else shown_colors
    fig = plt.figure(figsize=(11.2, 6.4), dpi=130, facecolor=BG)
    ax3 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.84, bottom=0.22, wspace=0.22)

    ax3.scatter(shown[:, 0], shown[:, 1], shown[:, 2], s=0.6, c=color, alpha=0.85, linewidths=0)
    for segment in segments:
        _draw_segments(ax3, segment, BOX, 2.0)
    _style_3d(ax3)
    _equal_3d(ax3, points)
    ax3.view_init(elev=22, azim=-58)
    ax3.set_xlabel("X (m)")
    ax3.set_ylabel("Y (m)")
    ax3.set_zlabel("Z (m)")
    ax3.set_title("Points and minimal OBB" if segments else "Input cloud, no OBB", color=INK, fontsize=11)

    ax2.scatter(shown[:, 0], shown[:, 1], s=2.0, c=color, alpha=0.8, linewidths=0)
    for segment in segments:
        for edge in segment:
            ax2.plot(edge[:, 0], edge[:, 1], color=BOX, lw=1.8)
    ax2.set_aspect("equal", adjustable="box")
    ax2.set_facecolor("#fffdf8")
    ax2.set_xlabel("X (m)")
    ax2.set_ylabel("Y (m)")
    ax2.tick_params(colors=MUTED, labelsize=8)
    ax2.set_title("Section, looking along Z", color=INK, fontsize=11)
    for spine in ax2.spines.values():
        spine.set_color(LINE)

    fig.suptitle(title, color=INK, fontsize=13, x=0.04, ha="left")
    fig.text(0.04, 0.045, "\n".join(lines), color=MUTED, fontsize=8, va="bottom", family="DejaVu Sans")
    if banner:
        ax2.add_patch(
            FancyBboxPatch(
                (0.08, 0.08),
                0.84,
                0.22,
                transform=ax2.transAxes,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor="#8c2f2f",
                edgecolor="#5e1d1d",
                linewidth=0.8,
                zorder=5,
            )
        )
        ax2.text(
            0.50,
            0.19,
            banner,
            transform=ax2.transAxes,
            ha="center",
            va="center",
            color="white",
            fontsize=8,
            zorder=6,
            wrap=True,
        )
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def _subsample(
    points: np.ndarray,
    count: int,
    seed: int,
    colors: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    if len(points) <= count:
        return points, colors
    rng = np.random.default_rng(seed)
    index = rng.choice(len(points), count, replace=False)
    picked_colors = None if colors is None else colors[index]
    return points[index], picked_colors


def _draw_segments(ax, segments: np.ndarray, color: str, width: float) -> None:
    for edge in segments:
        ax.plot(edge[:, 0], edge[:, 1], edge[:, 2], color=color, lw=width, solid_capstyle="round")


def _style_3d(ax) -> None:
    ax.set_facecolor(BG)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("#efeae2")
        axis.pane.set_edgecolor(LINE)
        axis.label.set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(False)


def _equal_3d(ax, points: np.ndarray) -> None:
    lows = points.min(axis=0)
    highs = points.max(axis=0)
    center = (lows + highs) / 2.0
    radius = 0.55 * float(np.max(highs - lows))
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
