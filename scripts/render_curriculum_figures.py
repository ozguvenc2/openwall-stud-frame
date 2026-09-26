"""Iso figures for the curriculum ladder, one stud through the synthetic room.

Rank 1 boxes are the Open3D baseline on the existing generators. Production
paint is yellow because device epsilon is unlocked. Stages 6 and 7 stay
stubs: this script does not draw them.

    python scripts/render_curriculum_figures.py

Images land in ``docs/research/images/curriculum/``. A manifest next to them
records the stud count and the rank-1 pass/fail from this process. Pass/fail
uses the same bars as ``scripts/run_curriculum_through_room.py``. It does not
publish a new angle, section, or length.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.open3d_baseline import (
    _obb_segments,
    _point_cloud,
    match_detections,
    run_baseline,
    score_run,
)
from openwall_stud.synthetic import (
    s1b_bow_wall,
    s1b_bowed_stud,
    stage0_single_stud,
    stage2_stud_and_floor,
    stage3_mini_wall,
    stage5_room_bay,
)

OUT = ROOT / "docs" / "research" / "images" / "curriculum"

BG = "#f6f3ec"
INK = "#1f1a17"
MUTED = "#5e584f"
WOOD = "#c4844a"
YELLOW = "#c48a00"
DROPPED = "#a33b32"
SLAB = "#c9c2b6"
LINE = "#d9d2c5"
FAIL_INK = "#7a1f16"
FAIL_BG = "#fde8e4"

STUD_COLORS = ["#c4844a", "#2a6f8f", "#6b4c9a", "#3d6b4f", "#8a5a2a"]
WALL_COLORS = {
    "south": "#c4844a",
    "west": "#2a6f8f",
    "north": "#6b4c9a",
    "east": "#3d6b4f",
}

# Same bring-up bars as scripts/run_curriculum_through_room.py.
# Stage 5 has no numeric bar. A pass there is one box per stud and yellow paint.
BARS = {
    0: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    2: {"section_mm": 10.0, "length_mm": 25.0, "angle_deg": 0.05},
    3: {"section_mm": 10.0, "length_mm": 30.0, "angle_deg": 0.10},
}

# Day-table outcomes for the scenes this script rebuilds. Stage 0 at 0.15°
# is not one of those cards; its verdict is this process only.
KNOWN_VERDICT = {
    "stage2_2x4_lean1.000": "pass",
    "stage3_mini_wall_3": "pass",
    "stage3_mini_wall_4_leanmild": "pass",
    "stage3_mini_wall_5": "pass",
    "stage3_mini_wall_4_noise2mm": "fail",
    "s1b_bow_2x4_amp6.35mm_lean0.000": "fail",
    "s1b_bow_wall_3": "fail",
    "stage5_room_bay_lot62_look": "pass",
}


def _subsample(points: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(points) <= n:
        return points
    rng = np.random.default_rng(seed)
    return points[rng.choice(len(points), n, replace=False)]


def _style_3d(ax) -> None:
    ax.set_facecolor(BG)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor("#efeae2")
        axis.pane.set_edgecolor(LINE)
        axis.label.set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(False)


def _style_2d(ax, *, equal: bool) -> None:
    ax.set_facecolor("#fbf9f4")
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.spines[:].set_color(LINE)
    if equal:
        ax.set_aspect("equal", adjustable="box")


def _equal_3d(ax, points: np.ndarray) -> None:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    center = (mins + maxs) / 2.0
    radius = 0.55 * float(np.max(maxs - mins))
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)


def _draw_segments(ax, segments: np.ndarray, color: str, *, lw: float, ls: str, project: str | None) -> None:
    for seg in segments:
        if project == "xz":
            ax.plot(seg[:, 0], seg[:, 2], color=color, lw=lw, ls=ls, solid_capstyle="round")
        elif project == "xy":
            ax.plot(seg[:, 0], seg[:, 1], color=color, lw=lw, ls=ls, solid_capstyle="round")
        else:
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color, lw=lw, ls=ls, solid_capstyle="round")


def _rank1_verdict(scene, sections) -> tuple[str, list[str]]:
    """Same day-row rule as the curriculum script. No new numeric bar."""
    det = sections["detection"]
    geom = sections["geometry"]
    ang = sections["angle"]
    colors = list(sections["paint"]["production_colors"] or [])
    failures: list[str] = []
    if det["precision"] != 1.0 or det["recall"] != 1.0:
        failures.append(f"detection P={det['precision']} R={det['recall']}")
    if scene.stage in BARS:
        bar = BARS[scene.stage]
        if geom["max_section_error_mm"] is None or geom["max_section_error_mm"] > bar["section_mm"]:
            failures.append("section")
        if geom["max_length_error_mm"] is None or geom["max_length_error_mm"] > bar["length_mm"]:
            failures.append("length")
        if ang["max_abs_error_deg"] is None or ang["max_abs_error_deg"] > bar["angle_deg"]:
            failures.append("angle")
    if not colors or any(color != "yellow" for color in colors):
        failures.append("paint")
    return ("fail" if failures else "pass"), failures


def _kept_slots(scene, run) -> set[int]:
    return {truth_i for truth_i, _det_i in match_detections(scene, run)}


def _rejected_segments(scene, run) -> list[np.ndarray]:
    """Minimal boxes for DBSCAN clusters the baseline did not keep.

    These wires are the same fitter the baseline uses before the section and
    length gates. They are not a second score.
    """
    kept = {det.cluster_id for det in run.detections}
    labels = run.cluster_labels
    rejected = []
    for cluster_id in sorted(int(value) for value in np.unique(labels) if int(value) >= 0):
        if cluster_id in kept:
            continue
        member = scene.points_m[labels == cluster_id]
        if member.shape[0] < run.dbscan_min_points:
            continue
        _center, _extent, _rotation, segments = _obb_segments(_point_cloud(member))
        rejected.append(segments)
    return rejected


def _scatter_scene(
    ax,
    scene,
    kept: set[int],
    *,
    per_stud: int,
    context: int,
    seed: int,
    project: str | None,
    walls: dict[int, str] | None,
) -> None:
    context_idx = np.flatnonzero(scene.part != 2)
    context_pts = _subsample(scene.points_m[context_idx], context, seed) if context_idx.size else np.empty((0, 3))
    if context_pts.size:
        if project == "xz":
            ax.scatter(context_pts[:, 0], context_pts[:, 2], c=SLAB, s=2, linewidths=0, alpha=0.45)
        elif project == "xy":
            ax.scatter(context_pts[:, 0], context_pts[:, 1], c=SLAB, s=2, linewidths=0, alpha=0.4)
        else:
            ax.scatter(
                context_pts[:, 0],
                context_pts[:, 1],
                context_pts[:, 2],
                c=SLAB,
                s=1.4,
                depthshade=False,
                linewidths=0,
                alpha=0.45,
            )
    for slot in range(len(scene.studs)):
        idx = np.flatnonzero((scene.part == 2) & (scene.stud_slot == slot))
        pts = _subsample(scene.points_m[idx], per_stud, seed + 1 + slot)
        if walls is not None:
            color = WALL_COLORS[walls[slot]]
        elif slot in kept:
            color = STUD_COLORS[slot % len(STUD_COLORS)]
        else:
            color = DROPPED
        if project == "xz":
            ax.scatter(pts[:, 0], pts[:, 2], c=color, s=3, linewidths=0, alpha=0.9)
        elif project == "xy":
            ax.scatter(pts[:, 0], pts[:, 1], c=color, s=3, linewidths=0, alpha=0.9)
        else:
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=color, s=1.8, depthshade=False, linewidths=0, alpha=0.9)


def _draw_boxes(ax, run, rejected: list[np.ndarray], *, project: str | None, lw: float) -> None:
    for det in run.detections:
        _draw_segments(ax, det.segments_m, YELLOW, lw=lw, ls="-", project=project)
    for segments in rejected:
        _draw_segments(ax, segments, DROPPED, lw=lw * 0.85, ls="--", project=project)


def _legend(ax, *, show_dropped: bool, walls: bool) -> None:
    handles = [
        Line2D([0], [0], color=SLAB, lw=6, label="Floor and plates"),
        Line2D([0], [0], color=YELLOW, lw=2, label="Kept box, yellow paint"),
    ]
    if show_dropped:
        handles.append(Line2D([0], [0], color=DROPPED, lw=1.6, ls="--", label="Dropped cluster"))
    if walls:
        handles = [
            Line2D([0], [0], color=WALL_COLORS[name], lw=6, label=name.capitalize())
            for name in ("south", "west", "north", "east")
        ] + [handles[1]]
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="upper left")


def _room_walls(scene) -> dict[int, str]:
    """Nearest extreme plan line. Corner studs are not shared, so one wall wins."""
    centers = np.vstack([stud.center_m[:2] for stud in scene.studs])
    x_west = float(centers[:, 0].min())
    x_east = float(centers[:, 0].max())
    y_south = float(centers[:, 1].min())
    y_north = float(centers[:, 1].max())
    walls: dict[int, str] = {}
    for slot, (x_m, y_m) in enumerate(centers):
        distance = {
            "south": abs(float(y_m) - y_south),
            "north": abs(float(y_m) - y_north),
            "west": abs(float(x_m) - x_west),
            "east": abs(float(x_m) - x_east),
        }
        walls[slot] = min(distance, key=distance.get)
    return walls


def _bow_profile(ax, scene, slot: int) -> None:
    """Median lateral offset of one generator stud. The bow is the scene, not a score."""
    stud = scene.studs[slot]
    mask = (scene.part == 2) & (scene.stud_slot == slot)
    pts = scene.points_m[mask]
    z = pts[:, 2]
    lateral_mm = (pts[:, 1] - float(stud.center_m[1])) * 1000.0
    edges = np.linspace(float(z.min()), float(z.max()), 36)
    centers = []
    medians = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        chosen = (z >= lo) & (z < hi if hi < edges[-1] else z <= hi)
        if int(chosen.sum()) < 8:
            continue
        centers.append(0.5 * (lo + hi))
        medians.append(float(np.median(lateral_mm[chosen])))
    ax.axvline(0.0, color=MUTED, lw=0.8, ls=":")
    ax.plot(medians, centers, color=WOOD, lw=2.0)
    ax.scatter(medians, centers, c=WOOD, s=12, linewidths=0)
    bow_mm = float(stud.bow_m) * 1000.0
    ax.axvline(bow_mm, color=YELLOW, lw=1.0, ls="--")
    ax.set_xlim(-2.0, max(12.0, bow_mm + 4.0))
    ax.set_xlabel("Median Y − chord (mm)", color=MUTED)
    ax.set_ylabel("Z (m)", color=MUTED)
    ax.set_title(
        f"Generator bow {bow_mm:.2f} mm on stud {slot + 1}. Not a detector offset.",
        fontsize=10,
        color=INK,
        loc="left",
    )


def _new_figure(title: str, subtitle: str) -> plt.Figure:
    fig = plt.figure(figsize=(13.6, 7.7), dpi=140)
    fig.patch.set_facecolor(BG)
    fig.suptitle(title, fontsize=16, color=INK, fontweight="bold", x=0.04, ha="left", y=0.98)
    fig.text(0.04, 0.925, subtitle, fontsize=10, color=MUTED, ha="left")
    return fig


def _footer(fig, verdict: str, note: str) -> None:
    fig.text(0.04, 0.028, note, fontsize=9, color=FAIL_INK if verdict == "fail" else MUTED)


def _label_studs(ax, scene, kept: set[int]) -> None:
    for slot, stud in enumerate(scene.studs):
        word = "kept" if slot in kept else "dropped"
        color = INK if slot in kept else DROPPED
        top = float(stud.center_m[2] + stud.length_m / 2.0 + 0.05)
        ax.text(float(stud.center_m[0]), top, f"{slot + 1} {word}", ha="center", va="bottom", fontsize=8, color=color)


def render_record(spec: dict) -> dict:
    scene = spec["build"]()
    n_studs = len(scene.studs)
    if n_studs != spec["studs"]:
        raise SystemExit(f"{spec['level']}: generator studs {n_studs}, expected {spec['studs']}")
    print(f"running {scene.name} points {scene.n_points} studs {n_studs}", flush=True)
    run = run_baseline(scene)
    sections = score_run(scene, run)
    verdict, reasons = _rank1_verdict(scene, sections)
    known = KNOWN_VERDICT.get(scene.name)
    if known is not None and verdict != known:
        raise SystemExit(
            f"{scene.name}: this run is {verdict} ({reasons}), day table is {known}. "
            "Refusing to label the figure against the published rank-1 row."
        )
    kept = _kept_slots(scene, run)
    rejected = _rejected_segments(scene, run) if spec["show_dropped"] else []
    det = sections["detection"]
    noun = "stud" if n_studs == 1 else "studs"
    title = f"{spec['level']} — {n_studs} {noun}"
    subtitle = spec["subtitle"]
    if spec["show_dropped"]:
        subtitle = (
            f"{subtitle} Rank 1 kept {det['n_pred']} of {det['n_true']}. "
            f"{len(rejected)} cluster{'s' if len(rejected) != 1 else ''} drawn dashed."
        )
    subtitle = f"{subtitle} Rank 1 {verdict}."
    fig = _new_figure(title, subtitle)
    walls = _room_walls(scene) if spec["walls"] else None
    if walls is not None:
        counts = {name: sum(1 for wall in walls.values() if wall == name) for name in WALL_COLORS}
        if counts != {"south": 5, "west": 7, "north": 7, "east": 7}:
            raise SystemExit(f"{scene.name}: wall counts {counts}, expected south 5 and 7 on the other three")
    project = spec["project"]

    if project is None and spec["profile_slot"] is None:
        ax = fig.add_axes([0.05, 0.10, 0.90, 0.78], projection="3d")
        _style_3d(ax)
        _scatter_scene(
            ax,
            scene,
            kept,
            per_stud=spec["per_stud"],
            context=spec["context"],
            seed=scene.seed,
            project=None,
            walls=walls,
        )
        _draw_boxes(ax, run, rejected, project=None, lw=1.6)
        _equal_3d(ax, scene.points_m)
        ax.view_init(elev=spec["elev"], azim=spec["azim"])
        ax.set_xlabel("X m", fontsize=8)
        ax.set_ylabel("Y m", fontsize=8)
        ax.set_zlabel("Z m", fontsize=8)
        ax.set_title(title, fontsize=11, color=INK, pad=8)
        _legend(ax, show_dropped=spec["show_dropped"], walls=spec["walls"])
    else:
        ax = fig.add_axes([0.02, 0.10, 0.48, 0.76], projection="3d")
        _style_3d(ax)
        _scatter_scene(
            ax,
            scene,
            kept,
            per_stud=spec["per_stud"],
            context=spec["context"],
            seed=scene.seed,
            project=None,
            walls=walls,
        )
        _draw_boxes(ax, run, rejected, project=None, lw=1.35)
        _equal_3d(ax, scene.points_m)
        ax.view_init(elev=spec["elev"], azim=spec["azim"])
        ax.set_xlabel("X m", fontsize=8)
        ax.set_ylabel("Y m", fontsize=8)
        ax.set_zlabel("Z m", fontsize=8)
        ax.set_title(f"Iso — {title}", fontsize=11, color=INK, pad=6)

        panels = []
        if project is not None and spec["profile_slot"] is not None:
            panels.append((fig.add_axes([0.54, 0.52, 0.42, 0.34]), "project"))
            panels.append((fig.add_axes([0.54, 0.12, 0.42, 0.32]), "profile"))
        elif spec["profile_slot"] is not None:
            panels.append((fig.add_axes([0.54, 0.16, 0.42, 0.68]), "profile"))
        else:
            panels.append((fig.add_axes([0.54, 0.16, 0.42, 0.68]), "project"))
        for side, kind in panels:
            if kind == "profile":
                _style_2d(side, equal=False)
                _bow_profile(side, scene, spec["profile_slot"])
                continue
            _style_2d(side, equal=True)
            _scatter_scene(
                side,
                scene,
                kept,
                per_stud=spec["per_stud"],
                context=min(spec["context"], 5000),
                seed=scene.seed + 17,
                project=project,
                walls=walls,
            )
            _draw_boxes(side, run, rejected, project=project, lw=1.15)
            if spec["label_studs"]:
                _label_studs(side, scene, kept)
            if project == "xz":
                side.set_xlabel("X along the wall (m)", color=MUTED)
                side.set_ylabel("Z (m)", color=MUTED)
                side.set_title(f"Front — {title}", fontsize=11, color=INK, loc="left")
            else:
                side.set_xlabel("X (m)", color=MUTED)
                side.set_ylabel("Y (m)", color=MUTED)
                side.set_title(f"Plan — {title}", fontsize=11, color=INK, loc="left")
            _legend(side, show_dropped=spec["show_dropped"], walls=spec["walls"])

    _footer(fig, verdict, spec["footer"])
    path = OUT / spec["filename"]
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  wrote {path.name} verdict {verdict} kept {det['n_pred']}/{det['n_true']}", flush=True)
    return {
        "level": spec["level"],
        "studs": n_studs,
        "image": f"docs/research/images/curriculum/{spec['filename']}",
        "pass_fail": verdict,
        "scene": scene.name,
        "n_pred": det["n_pred"],
        "n_true": det["n_true"],
        "reasons": reasons,
        "title": title,
    }


def _specs() -> list[dict]:
    common = {
        "show_dropped": False,
        "walls": False,
        "project": None,
        "profile_slot": None,
        "label_studs": False,
        "per_stud": 4000,
        "context": 4000,
        "elev": 16,
        "azim": -58,
    }

    def spec(**overrides):
        row = dict(common)
        row.update(overrides)
        return row

    return [
        spec(
            level="Stage 0 one-stud",
            studs=1,
            filename="01-stage0-one-stud.png",
            build=lambda: stage0_single_stud(nominal="2x4", lean_deg=0.15, seed=8),
            subtitle="One dressed 2×4, lean 0.15° about +X, no floor. Generator gravity is +Z.",
            footer="Stage 0. Rank 1 Open3D on this cloud. Yellow is production paint. ε is unlocked. Not a field result.",
        ),
        spec(
            level="Stage 2 one-stud harder",
            studs=1,
            filename="02-stage2-one-stud-harder.png",
            build=lambda: stage2_stud_and_floor(nominal="2x4", lean_deg=1.0, seed=22),
            subtitle="One dressed 2×4, lean 1.0° about +X, on a floor slab. Reference is the fitted floor normal.",
            footer="Stage 2 gate scene from the curriculum script. Yellow is production paint. ε is unlocked.",
            context=6000,
        ),
        spec(
            level="Stage 3 mini wall 3",
            studs=3,
            filename="03-stage3-mini-wall-3.png",
            build=lambda: stage3_mini_wall(n_studs=3, leans_deg=(0.0, 0.12, 4.0), seed=30),
            subtitle="Three 2×4s at 16 inch centers, leans 0 / 0.12 / 4°. Plates and floor peeled before the boxes.",
            footer="Stage 3 gate. Yellow wires are kept boxes. ε is unlocked.",
            project="xz",
            label_studs=True,
            elev=18,
            azim=-62,
        ),
        spec(
            level="Stage 3 mini wall 4",
            studs=4,
            filename="04-stage3-mini-wall-4.png",
            build=lambda: stage3_mini_wall(
                n_studs=4,
                leans_deg=(0.05, 0.15, 0.30, 1.0),
                seed=33,
                scene_name="stage3_mini_wall_4_leanmild",
            ),
            subtitle="Four 2×4s, mild leans 0.05 / 0.15 / 0.30 / 1.0°. Same gate as the other 1 mm walls.",
            footer="Stage 3 gate, mild-lean wall. Yellow wires are kept boxes. ε is unlocked.",
            project="xz",
            label_studs=True,
            elev=18,
            azim=-62,
        ),
        spec(
            level="Stage 3 mini wall 5",
            studs=5,
            filename="05-stage3-mini-wall-5.png",
            build=lambda: stage3_mini_wall(n_studs=5, seed=31),
            subtitle="Five 2×4s, default leans 0 / 0.30 / 0.80 / 1.50 / 0.15°. 1 mm noise.",
            footer="Stage 3 gate. Yellow wires are kept boxes. ε is unlocked.",
            project="xz",
            label_studs=True,
            elev=18,
            azim=-62,
            per_stud=3000,
        ),
        spec(
            level="Stage 3 probe 2 mm noise",
            studs=4,
            filename="06-stage3-probe-2mm-noise.png",
            build=lambda: stage3_mini_wall(
                n_studs=4,
                leans_deg=(0.0, 0.30, 0.80, 1.50),
                seed=32,
                noise_std_m=0.002,
                scene_name="stage3_mini_wall_4_noise2mm",
            ),
            subtitle="Four studs, 2 mm noise. Dashed wires are clusters the section gate dropped.",
            footer="Probe, not a stage gate. A dashed wire is a cluster rank 1 refused. It is not red paint.",
            project="xz",
            label_studs=True,
            show_dropped=True,
            elev=18,
            azim=-62,
        ),
        spec(
            level="S1b bow single",
            studs=1,
            filename="07-s1b-bow-single.png",
            build=lambda: s1b_bowed_stud(bow_m=0.00635, lean_deg=0.0, seed=40),
            subtitle="One 2×4, parabolic bow 6.35 mm along local Y, chord lean 0°. Ends stay on the chord.",
            footer="S1b probe. The right panel is the generator shape. Rank 1 still fits a straight box.",
            profile_slot=0,
            elev=16,
            azim=-70,
        ),
        spec(
            level="S1b bow wall",
            studs=3,
            filename="08-s1b-bow-wall.png",
            build=lambda: s1b_bow_wall(n_studs=3, bow_slot=1, bow_m=0.00635, leans_deg=(0.0, 0.0, 0.20), seed=41),
            subtitle="Three studs. The middle stud bows 6.35 mm. The outer studs are rigid.",
            footer="S1b probe. Front view counts the studs. The lower curve is the middle stud's generator bow, not a measured offset.",
            project="xz",
            label_studs=True,
            profile_slot=1,
            elev=18,
            azim=-62,
        ),
        spec(
            level="Stage 5 room bay lot62 look",
            studs=26,
            filename="09-stage5-room-bay-lot62-look.png",
            build=stage5_room_bay,
            subtitle="stage5_room_bay_lot62_look. Four walls, 16 inch centers, south door gap, 26 studs. Not the Lot 62 scan.",
            footer="Stage 5 has no numeric bar. Pass here means one yellow box per generator stud. Not stages 6 or 7.",
            project="xy",
            walls=True,
            elev=28,
            azim=-58,
            per_stud=450,
            context=5000,
        ),
    ]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [render_record(spec) for spec in _specs()]
    manifest = {
        "epsilon_locked": False,
        "paint": "yellow",
        "rank": 1,
        "stages_6_and_7": "stub_not_run_no_figure",
        "rows": rows,
    }
    dest = OUT / "manifest.json"
    dest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest -> {dest}", flush=True)
    for row in rows:
        print(f"{row['level']}\t{row['studs']}\t{row['image']}\t{row['pass_fail']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
