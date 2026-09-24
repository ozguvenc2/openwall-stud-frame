"""Render the five contender figures Oz can open.

Rank 1 images are matplotlib drawings of the Open3D baseline on synthetic
stages 0 and 3. Ranks 2–5 are labeled scaffold diagrams. They are not outputs
of PCL, CloudCompare, Pointcept, or Open3D-ML.

    python scripts/render_algo_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.open3d_baseline import run_baseline
from openwall_stud.synthetic import stage0_single_stud, stage3_mini_wall

OUT = ROOT / "docs" / "research" / "images" / "algo-contenders"
SCORE = ROOT / "artifacts" / "scorecards"

BG = "#f6f3ec"
INK = "#1f1a17"
MUTED = "#5e584f"
WOOD = "#c4844a"
NAVY = "#1e4d7b"
GREEN = "#2e7d32"
YELLOW = "#e0a106"
RED = "#c0392b"
SLAB = "#c9c2b6"
CARD = "#fffdf8"
LINE = "#d9d2c5"

STUD_COLORS = ["#c4844a", "#2a6f8f", "#6b4c9a", "#3d6b4f"]
PAINT = {"green": GREEN, "yellow": YELLOW, "red": RED}


def _subsample(points: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(points) <= n:
        return points
    rng = np.random.default_rng(seed)
    return points[rng.choice(len(points), n, replace=False)]


def _load(name: str) -> dict:
    return json.loads((SCORE / name).read_text(encoding="utf-8"))


def _style_3d(ax) -> None:
    ax.set_facecolor(BG)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("#efeae2")
        axis.pane.set_edgecolor(LINE)
        axis.label.set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(False)


def _draw_segments(ax, segments: np.ndarray, color: str, lw: float = 1.3) -> None:
    for seg in segments:
        ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color, lw=lw, solid_capstyle="round")


def _equal_3d(ax, points: np.ndarray) -> None:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    center = (mins + maxs) / 2.0
    radius = 0.5 * float(np.max(maxs - mins))
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)


def render_stage0(path: Path) -> None:
    scene = stage0_single_stud(nominal="2x4", lean_deg=4.0, seed=4)
    run = run_baseline(scene)
    det = run.detections[0]
    card = _load("open3d_stage0_stage0_2x4_lean4.000.json")
    measured = card["angle"]["per_stud"][0]["measured_deg"]
    rows = []
    for filename in [
        "open3d_stage0_stage0_2x4_lean0.000.json",
        "open3d_stage0_stage0_2x4_lean0.050.json",
        "open3d_stage0_stage0_2x4_lean0.120.json",
        "open3d_stage0_stage0_2x4_lean4.000.json",
        "open3d_stage0_stage0_2x6_lean0.300.json",
    ]:
        item = _load(filename)
        stud = item["angle"]["per_stud"][0]
        geom = item["geometry"]["per_stud"][0]
        rows.append(
            [
                geom["nominal"],
                f"{stud['true_deg']:.3f}",
                f"{stud['measured_deg']:.3f}",
                f"{stud['abs_error_deg']:.3f}",
                f"{item['geometry']['max_section_error_mm']:.2f}",
                stud["production_color"],
                stud["hypothetical_color"],
            ]
        )

    fig = plt.figure(figsize=(13.4, 7.5), dpi=150)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Rank 1 — Open3D baseline on synthetic Stage 0",
        fontsize=16,
        color=INK,
        fontweight="bold",
        x=0.04,
        ha="left",
    )
    fig.text(
        0.04,
        0.91,
        "Real run of this repo. One 2×4, generator gravity +Z, 1 mm noise. Production paint is yellow because ε is unlocked.",
        fontsize=10,
        color=MUTED,
        ha="left",
    )

    ax = fig.add_axes([0.04, 0.14, 0.46, 0.72], projection="3d")
    _style_3d(ax)
    pts = _subsample(scene.points_m, 5000, 4)
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=WOOD, s=1.6, depthshade=False, linewidths=0, alpha=0.9)
    _draw_segments(ax, det.segments_m, NAVY, lw=1.5)
    half = float(det.extent_sorted_m[2]) / 2.0
    axis = det.long_axis
    if axis[2] < 0:
        axis = -axis
    p0 = det.center_m - axis * half
    p1 = det.center_m + axis * half
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], [p0[2], p1[2]], color=RED, lw=2.0)
    base = scene.points_m[np.argmin(scene.points_m[:, 2])]
    ax.plot(
        [base[0], base[0]],
        [base[1], base[1]],
        [0.0, 2.5],
        color=MUTED,
        lw=1.0,
        ls="--",
    )
    _equal_3d(ax, scene.points_m)
    ax.view_init(elev=16, azim=-58)
    ax.set_xlabel("X m", fontsize=8)
    ax.set_ylabel("Y m", fontsize=8)
    ax.set_zlabel("Z m (gravity)", fontsize=8)
    ax.set_title(
        f"4.00° generator lean    measured {measured:.3f}°\nminimal OBB in blue, long axis in red, plumb dashed",
        fontsize=10,
        color=INK,
        pad=8,
    )

    table_ax = fig.add_axes([0.54, 0.16, 0.43, 0.68])
    table_ax.set_axis_off()
    table_ax.set_title(
        "Same pipeline, five Stage 0 clouds (from the scorecards)",
        fontsize=11,
        color=INK,
        loc="left",
        pad=8,
    )
    columns = ["Nominal", "True °", "Measured °", "|err| °", "Section mm", "Paint", "If ε=0.05°"]
    table = table_ax.table(
        cellText=rows,
        colLabels=columns,
        loc="upper center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 1.7)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor("#efe6d6")
            cell.set_text_props(color=INK, fontweight="bold")
        else:
            cell.set_facecolor(CARD)
            if c == 5:
                cell.set_facecolor(PAINT[rows[r - 1][5]])
                cell.set_text_props(color="white" if rows[r - 1][5] != "yellow" else INK, fontweight="bold")
            if c == 6:
                cell.set_facecolor(PAINT[rows[r - 1][6]])
                cell.set_text_props(color="white" if rows[r - 1][6] != "yellow" else INK, fontweight="bold")
    table_ax.text(
        0.0,
        0.08,
        "Paint column is the production color (all yellow).\n"
        "The last column reapplies the rule with a placeholder ε of 0.05°.\n"
        "That 0.05° is not a measured device band.\n"
        "Section error is the minimal box versus dressed 38.1 × 88.9 mm\n"
        "(or 38.1 × 139.7 mm for the 2×6). Noise tails widen the box.",
        transform=table_ax.transAxes,
        fontsize=9,
        color=MUTED,
        va="bottom",
    )
    fig.text(
        0.04,
        0.04,
        "Stage 0 pass on this run: precision 1, recall 1, section error under 10 mm, angle error under 0.05°. Not a field result.",
        fontsize=9,
        color=MUTED,
    )
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_stage3(path: Path) -> None:
    scene = stage3_mini_wall(n_studs=4, seed=7)
    run = run_baseline(scene)
    card = _load("open3d_stage3_stage3_mini_wall_4.json")
    fig = plt.figure(figsize=(13.4, 7.6), dpi=150)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Rank 1 — Open3D baseline on synthetic Stage 3 mini wall",
        fontsize=16,
        color=INK,
        fontweight="bold",
        x=0.04,
        ha="left",
    )
    fig.text(
        0.04,
        0.91,
        "Real run. Four 2×4s at 16 inch centers, plates and floor peeled, then DBSCAN. "
        f"Precision {card['detection']['precision']}, recall {card['detection']['recall']}, "
        f"angle MAE {card['angle']['mae_deg']:.5f}°.",
        fontsize=10,
        color=MUTED,
        ha="left",
    )

    ax = fig.add_axes([0.05, 0.12, 0.52, 0.74])
    ax.set_facecolor("#fbf9f4")
    removed = scene.points_m[~run.keep_mask]
    removed = _subsample(removed, 4000, 1)
    ax.scatter(removed[:, 0], removed[:, 2], c=SLAB, s=2, linewidths=0, alpha=0.45, label="Peeled floor and plates")
    for index, det in enumerate(run.detections):
        member = scene.points_m[run.cluster_labels == det.cluster_id]
        member = _subsample(member, 2500, 10 + index)
        ax.scatter(
            member[:, 0],
            member[:, 2],
            c=STUD_COLORS[index % len(STUD_COLORS)],
            s=2,
            linewidths=0,
            alpha=0.85,
        )
        for seg in det.segments_m:
            ax.plot(seg[:, 0], seg[:, 2], color=NAVY, lw=1.0)
        ax.text(
            det.center_m[0],
            det.center_m[2] + float(det.extent_sorted_m[2]) / 2.0 + 0.06,
            f"{det.theta_deg:.3f}°",
            ha="center",
            va="bottom",
            fontsize=9,
            color=INK,
        )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X along the wall (m)", color=MUTED)
    ax.set_ylabel("Z (m)", color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.spines[:].set_color(LINE)
    ax.set_title("Elevation of the wall face. Four boxes, no merged bay.", fontsize=11, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    side = fig.add_axes([0.62, 0.16, 0.34, 0.68])
    side.set_axis_off()
    lines = [
        "What this picture is",
        "",
        "Gray points were removed as horizontal slabs",
        "(floor, bottom plate, top plate).",
        "Each color is one DBSCAN cluster that passed",
        "the 2×4 section prior.",
        "Navy outlines are minimal oriented boxes,",
        "drawn in this elevation.",
        "",
        f"Studs found: {card['detection']['n_pred']} of {card['detection']['n_true']}",
        f"Max section error: {card['geometry']['max_section_error_mm']:.2f} mm",
        f"Max length error: {card['geometry']['max_length_error_mm']:.2f} mm",
        "  (plate slab eats the stud ends)",
        f"Angle MAE vs generator: {card['angle']['mae_deg']:.5f}°",
        f"Runtime: {card['cost']['runtime_s']:.3f} s on CPU",
        "",
        "Labels above the studs are measured θ",
        "versus the floor normal.",
        "Production color of every stud: yellow.",
        "ε is not locked. Placeholder colors are",
        "in the scorecard, not on this elevation.",
    ]
    side.text(0.0, 1.0, "\n".join(lines), va="top", ha="left", fontsize=11, color=INK, linespacing=1.35)
    fig.text(
        0.04,
        0.035,
        "Stage 3 is the first product-shaped milestone. These numbers are this synthetic cloud only.",
        fontsize=9,
        color=MUTED,
    )
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def _panel_cloud(ax) -> None:
    scene = stage3_mini_wall(n_studs=4, seed=7)
    stud = scene.points_m[scene.part == 2]
    other = scene.points_m[scene.part != 2]
    other = _subsample(other, 2500, 2)
    stud = _subsample(stud, 6000, 3)
    ax.scatter(other[:, 0], other[:, 2], c=SLAB, s=2, linewidths=0, alpha=0.5)
    ax.scatter(stud[:, 0], stud[:, 2], c=WOOD, s=2, linewidths=0, alpha=0.8)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("X (m)", color=MUTED, fontsize=8)
    ax.set_ylabel("Z (m)", color=MUTED, fontsize=8)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.set_facecolor("#fbf9f4")
    for spine in ax.spines.values():
        spine.set_color(LINE)
    ax.set_title("Synthetic Stage 3 input\n(not this stack’s output)", fontsize=10, color=INK, loc="left")


def render_scaffold(
    path: Path,
    *,
    rank: int,
    title: str,
    status: str,
    steps: list[str],
    callout: str,
    citation: str,
) -> None:
    fig = plt.figure(figsize=(13.4, 7.6), dpi=150)
    fig.patch.set_facecolor(BG)
    fig.text(0.04, 0.94, f"Rank {rank}", fontsize=11, color=MUTED, fontweight="bold")
    fig.text(0.04, 0.885, title, fontsize=16, color=INK, fontweight="bold")
    fig.text(
        0.04,
        0.835,
        status,
        fontsize=10,
        color="#7a1f16",
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.35", "fc": "#fde8e4", "ec": "#e0b2aa"},
    )
    ax = fig.add_axes([0.04, 0.12, 0.36, 0.64])
    _panel_cloud(ax)
    y = 0.70
    for index, step in enumerate(steps, start=1):
        fig.patches.append(
            FancyBboxPatch(
                (0.44, y),
                0.52,
                0.075,
                transform=fig.transFigure,
                boxstyle="round,pad=0.004,rounding_size=0.008",
                facecolor=CARD,
                edgecolor=LINE,
                linewidth=1.1,
            )
        )
        fig.text(0.455, y + 0.038, f"{index}.  {step}", va="center", ha="left", fontsize=10.5, color=INK)
        y -= 0.09
    fig.patches.append(
        FancyBboxPatch(
            (0.44, 0.12),
            0.52,
            0.14,
            transform=fig.transFigure,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            facecolor="#fde8e4",
            edgecolor="#e0b2aa",
            linewidth=1.1,
        )
    )
    fig.text(0.455, 0.19, callout, va="center", ha="left", fontsize=10, color="#7a1f16")
    fig.text(0.04, 0.04, citation, fontsize=8.5, color=MUTED)
    # Mark the figure type in the corner so a thumbnail cannot be mistaken for a fit.
    fig.patches.append(
        Rectangle((0.44, 0.78), 0.18, 0.035, transform=fig.transFigure, facecolor=NAVY, edgecolor="none")
    )
    fig.text(0.45, 0.797, "SCAFFOLD", color="white", fontsize=8, fontweight="bold", va="center")
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    render_stage0(OUT / "01-open3d-stage0.png")
    render_stage3(OUT / "01-open3d-stage3-miniwall.png")
    render_scaffold(
        OUT / "02-pcl-region-grow-scaffold.png",
        rank=2,
        title="PCL region growing, then a timber cuboid",
        status="SCAFFOLD / ILLUSTRATIVE — PCL was not executed. No metric in the scorecard.",
        steps=[
            "Estimate normals on the bare-frame cloud.",
            "Grow smooth regions (pcl::RegionGrowing).",
            "Split non-linear segments (Özkan / Pöchtrager).",
            "Fit one cuboid per member. Do not force the axis to Z.",
            "Hand that cuboid to the shared OBB and paint scorecard.",
        ],
        callout="Do not port Bassier remote coplanar merge.\nJoining coplanar patches glues the studs in one wall.",
        citation="Özkan et al. 2022, J. Imaging (one historic roof, not a 2×4 score).  Pöchtrager et al. 2018.  PCL RegionGrowing class.",
    )
    render_scaffold(
        OUT / "03-cloudcompare-ransac-scaffold.png",
        rank=3,
        title="CloudCompare RANSAC Shape Detection / CloudComPy",
        status="SCAFFOLD / ILLUSTRATIVE — the plugin was not run. Inspector, not the stud model.",
        steps=[
            "Open the same cloud in CloudCompare, or call CloudComPy.",
            "Run RANSAC Shape Detection (Schnabel, Wahl, Klein 2007).",
            "Primitives are plane, sphere, cylinder, cone, torus.",
            "A 2×4 is not a cylinder. Count primitives against stud count.",
            "Optional: one primitive’s points → shared OBB post-step.",
        ],
        callout="Coplanar stud faces become one plane.\nThat is the merge rank 1 is written to avoid. GPL-3.0 if linked.",
        citation="Schnabel, Wahl, Klein 2007, Eurographics.  CloudCompare RANSAC Shape Detection plugin.  CloudComPy computeRANSAC_SD.",
    )
    render_scaffold(
        OUT / "04-pointcept-ptv3-scaffold.png",
        rank=4,
        title="Pointcept PTv3 / PointGroup — hook only",
        status="SCAFFOLD / ILLUSTRATIVE — no training, no weights, no stud score.",
        steps=[
            "Wait for labeled Stage 5 (one room). Labels do not exist yet.",
            "Fine-tune a PTv3 backbone in Pointcept. Not started.",
            "Instance head in the PointGroup line. Not started.",
            "Stud points then use the same OBB and yellow paint.",
            "BIMStruct3D zero-shot is a control only: no stud class.",
        ],
        callout="Do not paint QA from ScanNet or BIMStruct3D labels.\nThose weights are the wrong classes, and some are CC BY-NC-SA.",
        citation="Pointcept (MIT code).  BIMStruct3D model card: wall and column, not stud.  No checkpoint was downloaded.",
    )
    render_scaffold(
        OUT / "05-open3d-ml-s3dis-scaffold.png",
        rank=5,
        title="Open3D-ML S3DIS — control baseline only",
        status="SCAFFOLD / ILLUSTRATIVE — no weights loaded, no forward pass.",
        steps=[
            "Later, one pass of RandLA-Net or KPConv on a Stage 5 cloud.",
            "Use the published S3DIS weights. They are office classes.",
            "Record the label histogram. Stop there.",
            "Do not fit a stud box from “beam” or “column”.",
            "Do not copy S3DIS mIoU into the stud scorecard.",
        ],
        callout="Office beam/column is not a 2×4.\nS3DIS mIoU stays on S3DIS. This rank exists to retire that mix-up.",
        citation="Open3D-ML model zoo.  Upstream RandLA-Net repo is CC BY-NC-SA 4.0; confirm the in-tree header before shipping.",
    )
    print(f"Wrote figures under {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
