#!/usr/bin/env python3
"""Gravity-deviation pass: read components.json → paint OBB wireframes green / amber / red.

Given oriented-box records from ``classical_segment_obb.py``, this script
computes the angular deviation of each member from plumb (for ``upright``) or
from level (for ``beam_like``), then renders four orthographic views with the
boxes colour-coded by pass / warn / fail status.

Tolerance source
----------------
The default 0.12 ° comes from the **Handbook of Construction Tolerances**
figure: 1/4 inch in 10 feet → ``atan(0.25 / 120) ≈ 0.1194 °``.
See ``docs/tolerances.md`` for the full derivation and alternatives.

Status thresholds
-----------------
* ``pass``  (green)  — deviation ≤ ``--tolerance-deg``
* ``warn``  (amber)  — tolerance < deviation ≤ ``--warn-factor`` × tolerance
* ``fail``  (red)    — deviation > ``--warn-factor`` × tolerance
* ``skip``  (grey)   — label is not ``upright`` or ``beam_like``, or
  ``long_axis_abs_cos_up`` is null (box fit failed / unknown up axis)

Deviation angles
----------------
``long_axis_abs_cos_up`` (stored in components.json) is |dot(long axis, up)|.

* **upright** — long axis should be parallel to up.
  ``deviation_deg = arccos(abs_cos_up)`` in degrees.
  Perfect plumb ⟹ cos = 1.0 ⟹ deviation = 0 °.

* **beam_like** — long axis should be perpendicular to up.
  ``deviation_deg = arcsin(abs_cos_up)`` in degrees.
  Perfect level ⟹ cos = 0.0 ⟹ deviation = 0 °.

Units note
----------
The angle computation only uses the cosine stored in components.json; it does
not depend on the extent units or the PLY coordinate frame.  That means the
pass/fail decision is independent of whether the PLY is in metres, feet, or
any other unit.  The supplied ``--up`` axis is used only as a label in the
report (the segmentation script already stored the cosine against whatever
up vector was active then).

Inputs
------
* ``--components`` — components.json written by classical_segment_obb.
* ``--input-ply``  — optional PLY for a background point cloud.
  If omitted, views contain boxes only.

Outputs (all under ``--out-dir``)
----------------------------------
* ``deviation_report.json`` — per-component result + summary.
* ``deviation_report.md``   — human-readable table.
* ``views/dev_front.png``, ``dev_side.png``, ``dev_top.png``, ``dev_iso.png``
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPONENTS = (
    REPO_ROOT / "data" / "raw" / "darus-intcdc" / "seg_out" / "components.json"
)
DEFAULT_OUT = REPO_ROOT / "data" / "raw" / "darus-intcdc" / "dev_out"

STATUS_COLORS: dict[str, np.ndarray] = {
    "pass": np.array([0.09, 0.65, 0.24]),   # green
    "warn": np.array([0.85, 0.61, 0.08]),   # amber
    "fail": np.array([0.82, 0.14, 0.14]),   # red
    "skip": np.array([0.55, 0.55, 0.55]),   # grey
}

LABELS_CHECKED = frozenset({"upright", "beam_like"})

_BOX_SIGNS = np.array(
    [
        [-1, -1, -1],
        [1, -1, -1],
        [-1, 1, -1],
        [-1, -1, 1],
        [1, 1, 1],
        [-1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
    ],
    dtype=float,
)
_BOX_EDGES = (
    (0, 1), (0, 2), (0, 3),
    (1, 6), (1, 7),
    (2, 5), (2, 7),
    (3, 5), (3, 6),
    (4, 5), (4, 6), (4, 7),
)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--components",
        type=Path,
        default=DEFAULT_COMPONENTS,
        help=(
            "components.json from classical_segment_obb. "
            f"Default: {DEFAULT_COMPONENTS}"
        ),
    )
    p.add_argument(
        "--input-ply",
        type=Path,
        default=None,
        help=(
            "Optional PLY file for a background point cloud. "
            "If omitted the views show OBBs only."
        ),
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory. Default: {DEFAULT_OUT}",
    )
    p.add_argument(
        "--tolerance-deg",
        type=float,
        default=0.12,
        help=(
            "Pass / fail threshold in degrees (default 0.12). "
            "Derived from the Handbook of Construction Tolerances 1/4 in per "
            "10 ft figure — see docs/tolerances.md."
        ),
    )
    p.add_argument(
        "--warn-factor",
        type=float,
        default=2.0,
        help=(
            "Warn-zone multiplier. A component deviating more than "
            "tolerance but at most (warn-factor × tolerance) is 'warn'. "
            "Default 2.0."
        ),
    )
    p.add_argument(
        "--up",
        default="z",
        help=(
            "Up-axis label written into the report. Does not recompute "
            "deviations (those come from long_axis_abs_cos_up already stored "
            "in components.json). Default: z."
        ),
    )
    p.add_argument(
        "--plot-max-points",
        type=int,
        default=60_000,
        help="Random-subsample cap for background cloud in each PNG (default 60000).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=0,
        help="NumPy seed for PNG point subsampling (default 0).",
    )
    return p


# ---------------------------------------------------------------------------
# Deviation computation
# ---------------------------------------------------------------------------

def compute_deviation(component: dict[str, Any]) -> tuple[float | None, str]:
    """Return (deviation_deg, reason).

    ``reason`` is empty when a deviation was computed.  Otherwise it explains
    why the component was skipped.
    """
    label = component.get("label", "")
    if label not in LABELS_CHECKED:
        return None, f"label={label!r} not in checked set"

    cos_up = component.get("long_axis_abs_cos_up")
    if cos_up is None:
        return None, "long_axis_abs_cos_up is null"

    cos_up = float(cos_up)
    cos_up = max(0.0, min(1.0, cos_up))   # numerical clamp

    if label == "upright":
        # Long axis should be near-parallel to up → deviation = arccos(cos_up)
        dev = math.degrees(math.acos(cos_up))
    else:
        # beam_like: long axis should be near-perpendicular → deviation = arcsin(cos_up)
        dev = math.degrees(math.asin(cos_up))

    return dev, ""


def classify_status(
    deviation_deg: float | None,
    tolerance_deg: float,
    warn_factor: float,
) -> str:
    if deviation_deg is None:
        return "skip"
    if deviation_deg <= tolerance_deg:
        return "pass"
    if deviation_deg <= warn_factor * tolerance_deg:
        return "warn"
    return "fail"


# ---------------------------------------------------------------------------
# OBB rendering helpers (same conventions as classical_segment_obb.py)
# ---------------------------------------------------------------------------

def box_corners(center, rotation, extent) -> np.ndarray:
    local = _BOX_SIGNS * (np.asarray(extent, dtype=float) / 2.0)
    return local @ np.asarray(rotation, dtype=float).T + np.asarray(center, dtype=float)


def view_axes(up_vec: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    vertical = up_vec / np.linalg.norm(up_vec)
    helper = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(helper, vertical))) > 0.85:
        helper = np.array([0.0, 1.0, 0.0])
    horiz = helper - vertical * float(np.dot(helper, vertical))
    horiz /= np.linalg.norm(horiz)
    other = np.cross(vertical, horiz)
    other /= np.linalg.norm(other)
    look = horiz + other + vertical
    look /= np.linalg.norm(look)
    iso_y = vertical - look * float(np.dot(vertical, look))
    iso_y /= np.linalg.norm(iso_y)
    iso_x = np.cross(look, iso_y)
    iso_x /= np.linalg.norm(iso_x)
    return {
        "front": (horiz, vertical),
        "side": (other, vertical),
        "top": (horiz, other),
        "iso": (iso_x, iso_y),
    }


def project(points: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    return np.column_stack((points @ sx, points @ sy))


# ---------------------------------------------------------------------------
# View rendering
# ---------------------------------------------------------------------------

def write_views(
    out_dir: Path,
    results: list[dict[str, Any]],
    components_map: dict[int, dict[str, Any]],
    bg_points: np.ndarray | None,
    bg_colors: np.ndarray | None,
    up_vec: np.ndarray,
    up_token: str,
    tolerance_deg: float,
    warn_factor: float,
    rng: np.random.Generator,
    plot_max_points: int,
) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D

    views_dir = out_dir / "views"
    views_dir.mkdir(parents=True, exist_ok=True)

    # Subsample background cloud
    if bg_points is not None and bg_points.shape[0] > plot_max_points:
        idx = rng.choice(bg_points.shape[0], size=plot_max_points, replace=False)
        bg_points = bg_points[idx]
        bg_colors = None if bg_colors is None else bg_colors[idx]

    frames = view_axes(up_vec)

    # Legend entries
    status_labels = {
        "pass": f"pass (≤ {tolerance_deg:.4g}°)",
        "warn": f"warn (≤ {warn_factor * tolerance_deg:.4g}°)",
        "fail": f"fail (> {warn_factor * tolerance_deg:.4g}°)",
        "skip": "skip (not checked)",
    }

    written: list[Path] = []
    view_names = ("front", "side", "top", "iso")

    for name in view_names:
        sx, sy = frames[name]
        fig, ax = plt.subplots(figsize=(7.6, 7.2), dpi=140)
        fig.patch.set_facecolor("#f6f3ec")
        ax.set_facecolor("#f7f4ee")

        if bg_points is not None and bg_points.shape[0]:
            proj = project(bg_points, sx, sy)
            marker = 4.0 if bg_points.shape[0] < 4000 else (1.4 if bg_points.shape[0] < 30000 else 0.35)
            alpha = 0.85 if bg_points.shape[0] < 4000 else 0.40
            if bg_colors is not None:
                ax.scatter(proj[:, 0], proj[:, 1], c=np.clip(bg_colors, 0, 1),
                           s=marker, linewidths=0, alpha=alpha, rasterized=True, zorder=1)
            else:
                ax.scatter(proj[:, 0], proj[:, 1], color=(0.45, 0.28, 0.14),
                           s=marker, linewidths=0, alpha=alpha, rasterized=True, zorder=1)

        # Draw OBB wireframes
        segments: list[tuple[np.ndarray, np.ndarray]] = []
        seg_colors: list[tuple[float, float, float]] = []
        all_corners: list[np.ndarray] = []

        for r in results:
            comp_id = r["id"]
            status = r["status"]
            comp = components_map[comp_id]
            corners = box_corners(comp["center"], comp["R"], comp["extents_units"])
            flat = project(corners, sx, sy)
            all_corners.append(flat)
            rgb = STATUS_COLORS[status]
            lw_multiplier = 1.6 if status in ("pass", "fail") else 1.0
            for i, j in _BOX_EDGES:
                segments.append((flat[i], flat[j]))
                seg_colors.append(tuple(float(v) for v in rgb))  # type: ignore[arg-type]

        if segments:
            ax.add_collection(
                LineCollection(segments, colors=seg_colors, linewidths=1.5, zorder=3)
            )

        # Axis limits
        xs_list: list[np.ndarray] = []
        ys_list: list[np.ndarray] = []
        if bg_points is not None and bg_points.shape[0]:
            proj_bg = project(bg_points, sx, sy)
            xs_list.append(proj_bg[:, 0])
            ys_list.append(proj_bg[:, 1])
        for flat in all_corners:
            xs_list.append(flat[:, 0])
            ys_list.append(flat[:, 1])
        if xs_list:
            xs = np.concatenate(xs_list)
            ys = np.concatenate(ys_list)
            pad_x = 0.04 * (float(xs.max() - xs.min()) + 1e-6)
            pad_y = 0.04 * (float(ys.max() - ys.min()) + 1e-6)
            ax.set_xlim(float(xs.min()) - pad_x, float(xs.max()) + pad_x)
            ax.set_ylim(float(ys.min()) - pad_y, float(ys.max()) + pad_y)

        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e4ddd0", linewidth=0.4)
        ax.tick_params(labelsize=8, colors="#5c5346")
        for spine in ax.spines.values():
            spine.set_color("#d9d2c5")
        ax.set_xlabel("file units", fontsize=8, color="#5c5346")
        ax.set_ylabel("file units", fontsize=8, color="#5c5346")

        checked = sum(1 for r in results if r["status"] != "skip")
        passes = sum(1 for r in results if r["status"] == "pass")
        warns = sum(1 for r in results if r["status"] == "warn")
        fails = sum(1 for r in results if r["status"] == "fail")
        ax.set_title(
            f"{name}  ·  pass={passes}  warn={warns}  fail={fails}  "
            f"skip={len(results) - checked}  ·  tol={tolerance_deg:.4g}°",
            fontsize=10, color="#2c2822", pad=8,
        )

        present_statuses = [s for s in ("pass", "warn", "fail", "skip")
                            if any(r["status"] == s for r in results)]
        handles = [
            Line2D([0], [0], color=STATUS_COLORS[s], lw=2.0, label=status_labels[s])
            for s in present_statuses
        ]
        ax.legend(handles=handles, loc="upper right", frameon=True,
                  fontsize=7, title="gravity deviation")

        fig.text(
            0.01, 0.01,
            f"up={up_token}   tolerance={tolerance_deg:.4g}°   "
            f"warn≤{warn_factor * tolerance_deg:.4g}°   boxes: OBB wireframe",
            fontsize=7, color="#5c5346",
        )
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        path = views_dir / f"dev_{name}.png"
        fig.savefig(path, dpi=140)
        plt.close(fig)
        written.append(path)

    return written


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_json_report(
    path: Path,
    *,
    components_path: Path,
    up_token: str,
    tolerance_deg: float,
    warn_factor: float,
    results: list[dict[str, Any]],
) -> None:
    summary = {s: 0 for s in ("pass", "warn", "fail", "skip")}
    for r in results:
        summary[r["status"]] += 1

    payload = {
        "schema": "openwall.gravity_deviation.v1",
        "source_components": str(components_path),
        "up_token": up_token,
        "tolerance_deg": tolerance_deg,
        "warn_threshold_deg": warn_factor * tolerance_deg,
        "tolerance_source": (
            "Handbook of Construction Tolerances: 1/4 inch in 10 feet. "
            "Derived angle: atan(0.25/120) ≈ 0.1194°. See docs/tolerances.md."
        ),
        "summary": summary,
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _fmt(v: float | None, precision: int = 4) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    return f"{v:.{precision}g}"


def write_md_report(
    path: Path,
    *,
    components_path: Path,
    up_token: str,
    tolerance_deg: float,
    warn_factor: float,
    results: list[dict[str, Any]],
) -> None:
    summary = {s: 0 for s in ("pass", "warn", "fail", "skip")}
    for r in results:
        summary[r["status"]] += 1

    lines = [
        "# Gravity-deviation report",
        "",
        "Generated by `scripts/paint_gravity_deviation.py`.",
        "Inputs are heuristic OBBs; this is not a measured stud schedule.",
        "",
        "## Tolerance",
        "",
        f"| Parameter | Value |",
        "| --- | --- |",
        f"| Up axis (from source run) | `{up_token}` |",
        f"| Pass threshold | {tolerance_deg:.4g} ° |",
        f"| Warn threshold | {warn_factor * tolerance_deg:.4g} ° "
        f"(= {warn_factor}× tolerance) |",
        f"| Source | Handbook of Construction Tolerances 1/4 in per 10 ft |",
        "",
        "See `docs/tolerances.md` for full derivation.",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
        f"| pass (green) | {summary['pass']} |",
        f"| warn (amber) | {summary['warn']} |",
        f"| fail (red) | {summary['fail']} |",
        f"| skip (grey, label not checked) | {summary['skip']} |",
        "",
        "## Per-component results",
        "",
        ("| id | label | deviation_deg | status | "
         "long_axis_abs_cos_up | skip_reason |"),
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['label']} | {_fmt(r['deviation_deg'])} | "
            f"{r['status']} | {_fmt(r['long_axis_abs_cos_up'])} | "
            f"{r.get('skip_reason', '')} |"
        )
    lines += [
        "",
        "## What still fails vs LOT-62 residential target",
        "",
        "* **Wrong data** — these results are from the IntCDC *timber* building "
        "scan (DaRUS, exotic heavy timber, not 2×4 platform frame). "
        "The stud-schedule claim of ~12 upright and ~87 beam-like components "
        "on what is in fact a single large timber structure is not trustworthy.",
        "* **Wrong up axis** — the DaRUS PLY is not documented as Z-up / "
        "gravity-aligned. `long_axis_abs_cos_up` was computed against the "
        "stored Z axis, not a measured gravity vector. Deviations reported here "
        "are Z-axis deviations only.",
        "* **No residential data** — no public point cloud of a US residential "
        "light-frame house (LOT 62 style, exposed 2×4 studs) was found in the "
        "research pass. Until such data is acquired (Polycam capture or "
        "WFC-Dataset single stud), the pass/fail numbers here have no "
        "ground-truth anchor.",
        "* **Segmentation accuracy unknown** — the classical DBSCAN pipeline "
        "merges touching members into one cluster. On the IntCDC scan 449 "
        "clusters cover ~520K inlier points of which 109 are labelled clutter. "
        "A proper stud schedule needs per-member isolation.",
        "",
        f"Source components: `{components_path}`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_ply_background(path: Path):
    """Return (points_np, colors_np_or_None). Requires open3d."""
    try:
        import open3d as o3d
    except ImportError:
        print("open3d not available; views will show OBBs only.", file=sys.stderr)
        return None, None
    if not path.is_file():
        print(f"Background PLY not found: {path} — views will show OBBs only.",
              file=sys.stderr)
        return None, None
    cloud = o3d.io.read_point_cloud(
        str(path), remove_nan_points=True, remove_infinite_points=True,
        print_progress=False,
    )
    if cloud.is_empty():
        return None, None
    pts = np.asarray(cloud.points, dtype=float)
    cols = None
    if cloud.has_colors():
        c = np.asarray(cloud.colors)
        if c.ndim == 2 and c.shape == (pts.shape[0], 3) and float(c.max()) > 1e-8:
            cols = c
    return pts, cols


def run(args: argparse.Namespace) -> int:
    if not args.components.is_file():
        print(
            f"components.json not found: {args.components}\n"
            "Run classical_segment_obb.py first.",
            file=sys.stderr,
        )
        return 2

    raw = json.loads(args.components.read_text(encoding="utf-8"))
    raw_comps = raw.get("components", [])
    if not raw_comps:
        print("components.json has no components array.", file=sys.stderr)
        return 2

    # Determine up vector for view rendering
    stored_up = raw.get("up", [0.0, 0.0, 1.0])
    up_vec = np.array(stored_up, dtype=float)
    norm = float(np.linalg.norm(up_vec))
    if norm < 1e-12:
        up_vec = np.array([0.0, 0.0, 1.0])
    else:
        up_vec /= norm
    up_token = args.up or raw.get("up_token", "z")

    # Build id → component map
    components_map: dict[int, dict[str, Any]] = {int(c["id"]): c for c in raw_comps}

    # Compute deviations
    results: list[dict[str, Any]] = []
    for comp in raw_comps:
        dev, reason = compute_deviation(comp)
        status = classify_status(dev, args.tolerance_deg, args.warn_factor)
        results.append(
            {
                "id": int(comp["id"]),
                "label": comp.get("label", ""),
                "deviation_deg": dev,
                "status": status,
                "long_axis_abs_cos_up": comp.get("long_axis_abs_cos_up"),
                "skip_reason": reason,
            }
        )

    # Summary
    summary = {s: sum(1 for r in results if r["status"] == s)
               for s in ("pass", "warn", "fail", "skip")}
    checked = len(results) - summary["skip"]
    print(
        f"components={len(results)}  checked={checked}  "
        f"pass={summary['pass']}  warn={summary['warn']}  fail={summary['fail']}  "
        f"skip={summary['skip']}"
    )
    print(
        f"tolerance={args.tolerance_deg:.4g}deg  "
        f"warn<={args.warn_factor * args.tolerance_deg:.4g}deg"
    )

    # Load background cloud
    bg_points: np.ndarray | None = None
    bg_colors: np.ndarray | None = None
    if args.input_ply is not None:
        bg_points, bg_colors = load_ply_background(args.input_ply)
    else:
        default_ply = REPO_ROOT / "data" / "raw" / "darus-intcdc" / "preview.ply"
        if default_ply.is_file():
            bg_points, bg_colors = load_ply_background(default_ply)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)

    view_paths = write_views(
        args.out_dir,
        results,
        components_map,
        bg_points,
        bg_colors,
        up_vec,
        up_token,
        args.tolerance_deg,
        args.warn_factor,
        rng,
        args.plot_max_points,
    )

    json_path = args.out_dir / "deviation_report.json"
    md_path = args.out_dir / "deviation_report.md"

    write_json_report(
        json_path,
        components_path=args.components,
        up_token=up_token,
        tolerance_deg=args.tolerance_deg,
        warn_factor=args.warn_factor,
        results=results,
    )
    write_md_report(
        md_path,
        components_path=args.components,
        up_token=up_token,
        tolerance_deg=args.tolerance_deg,
        warn_factor=args.warn_factor,
        results=results,
    )

    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for p in view_paths:
        print(f"wrote {p}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.tolerance_deg <= 0:
        print("--tolerance-deg must be positive", file=sys.stderr)
        return 2
    if args.warn_factor < 1:
        print("--warn-factor must be >= 1", file=sys.stderr)
        return 2
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
