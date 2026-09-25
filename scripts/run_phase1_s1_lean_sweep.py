"""Phase 1 S1: one dressed 2x4, dense lean magnitude times axis.

Twenty-five clouds. Seed 2 on every cloud. Angle reference is generator +Z.
No floor, no plate, no multi-stud wall, no phone, no SKIL.

Ranks 1, 2, 3, and 6 are scored with the stage 0 synthetic bars.
Ranks 4 and 5 are controls: a forward pass may record a histogram, and stud
metrics stay null when the vocabulary has no stud class.

    .venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py
    .venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --check-only
    .venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --report-only

``--finder classical`` uses this interpreter. ``--finder pointcept`` expects
the BIMStruct3D ``.venv``. ``--finder open3d_ml`` expects ``.venv-o3dml``.
The default command runs those three and then writes the research note.
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

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.contenders.cloudcompare_ransac import run_one_stud as run_cloudcompare
from openwall_stud.contenders.common import gpu_probe, ran_card
from openwall_stud.contenders.open3d_ml_s3dis import OPEN3D_ML
from openwall_stud.contenders.open3d_ml_s3dis import run_one_stud as run_open3d_ml
from openwall_stud.contenders.pcl_region_grow import run_one_stud as run_pcl
from openwall_stud.contenders.pointcept_ptv3 import POINTCEPT
from openwall_stud.contenders.pointcept_ptv3 import run_one_stud as run_pointcept
from openwall_stud.contenders.pyransac3d_cuboid import run_one_stud as run_pyransac
from openwall_stud.one_stud import scene_record
from openwall_stud.one_stud_publish import publish_attempt
from openwall_stud.open3d_baseline import _angle_deg, run_baseline, score_run
from openwall_stud.paint import assert_paint_rules
from openwall_stud.results_by_day import append_day_row, repo_root, today_la
from openwall_stud.synthetic import LEAN_AXES, phase1_s1_scene_name, phase1_s1_single_stud

SCORE_DIR = ROOT / "artifacts" / "scorecards" / "phase1_s1"
FIG_DIR = ROOT / "docs" / "research" / "images" / "phase1-s1"
REPORT_MD = ROOT / "docs" / "research" / "19-phase1-s1-lean-sweep.md"
REPORT_JSON = ROOT / "docs" / "research" / "19-phase1-s1-lean-sweep.json"
PY_PT = ROOT / ".venv" / "Scripts" / "python.exe"
PY_ML = ROOT / ".venv-o3dml" / "Scripts" / "python.exe"

MAGNITUDES_DEG = (0.0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0)
SEED = 2
REFERENCE = np.array([0.0, 0.0, 1.0])

# Classical scenes that get an offline PNG when a box exists.
REPRESENTATIVE = (
    "s1_2x4_lean0.000_axnone",
    "s1_2x4_lean0.150_ax+X",
    "s1_2x4_lean4.000_ax+Y",
)

FINDERS = (
    {"key": "open3d", "rank": 1, "group": "classical", "name": "Refined Open3D stud prior"},
    {
        "key": "pcl",
        "rank": 2,
        "group": "classical",
        "name": "PCL region-grow + cuboid (Ozkan/Pochtrager, no Bassier merge)",
    },
    {"key": "cloudcompare", "rank": 3, "group": "classical", "name": "CloudCompare RANSAC-SD / CloudComPy"},
    {"key": "pointcept", "rank": 4, "group": "control", "name": POINTCEPT["name"]},
    {"key": "open3d_ml", "rank": 5, "group": "control", "name": OPEN3D_ML["name"]},
    {"key": "pyransac3d", "rank": 6, "group": "classical", "name": "pyRANSAC-3D sequential cuboid"},
)


def matrix_specs() -> list[tuple[float, str]]:
    """1 zero-lean cloud, then 6 magnitudes times 4 axes. Order is locked."""
    specs: list[tuple[float, str]] = [(0.0, "none")]
    for magnitude in MAGNITUDES_DEG:
        if magnitude == 0.0:
            continue
        for axis in LEAN_AXES:
            specs.append((float(magnitude), axis))
    return specs


def make_s1_scene(lean_deg: float, axis: str):
    return phase1_s1_single_stud(
        lean_deg=lean_deg,
        axis=axis,
        seed=SEED,
        spacing_m=0.005,
        noise_std_m=0.001,
        nominal="2x4",
    )


def assert_s1_matrix() -> list[dict[str, Any]]:
    """Fail before any finder if the locked matrix or the axis rotation is wrong."""
    specs = matrix_specs()
    if len(specs) != 25:
        raise SystemExit(f"expected 25 scenes, got {len(specs)}")
    rows: list[dict[str, Any]] = []
    names: list[str] = []
    point_counts: list[int] = []
    for lean_deg, axis in specs:
        scene = make_s1_scene(lean_deg, axis)
        expected = phase1_s1_scene_name(lean_deg, axis)
        if scene.name != expected:
            raise SystemExit(f"scene name {scene.name!r} != {expected!r}")
        if scene.seed != SEED or scene.spacing_m != 0.005 or scene.noise_std_m != 0.001:
            raise SystemExit(f"{scene.name} broke the locked noise, spacing, or seed")
        if scene.stage != 0:
            raise SystemExit(f"{scene.name} is not a stage 0 style cloud")
        if set(int(value) for value in np.unique(scene.part)) != {2}:
            raise SystemExit(f"{scene.name} is not stud-only")
        stud = scene.studs[0]
        if stud.lean_axis != axis or abs(float(stud.lean_deg) - lean_deg) > 1e-12:
            raise SystemExit(f"{scene.name} truth lean/axis mismatch")
        theta = _angle_deg(stud.long_axis, REFERENCE)
        if abs(theta - lean_deg) > 1e-8:
            raise SystemExit(f"{scene.name} long-axis angle {theta} != lean {lean_deg}")
        horizontal = np.asarray(stud.long_axis[:2], dtype=float)
        if lean_deg == 0.0:
            if float(np.linalg.norm(horizontal)) > 1e-12:
                raise SystemExit("zero lean moved the long axis off +Z")
        else:
            sine = float(np.sin(np.deg2rad(lean_deg)))
            # Right-hand rotation of +Z. The sign is the generator, checked here.
            expected_xy = {
                "+X": np.array([0.0, -sine]),
                "-X": np.array([0.0, sine]),
                "+Y": np.array([sine, 0.0]),
                "-Y": np.array([-sine, 0.0]),
            }[axis]
            if not np.allclose(horizontal, expected_xy, atol=1e-10):
                raise SystemExit(f"{scene.name} horizontal long-axis {horizontal} != {expected_xy}")
        names.append(scene.name)
        point_counts.append(scene.n_points)
        rows.append(
            {
                "name": scene.name,
                "lean_deg": lean_deg,
                "axis": axis,
                "n_points": scene.n_points,
                "long_axis": [round(float(value), 10) for value in stud.long_axis],
                "theta_from_plus_z_deg": theta,
                "seed": scene.seed,
            }
        )
    if len(set(names)) != 25:
        raise SystemExit("scene ids are not unique")
    if len(set(point_counts)) != 1:
        raise SystemExit(f"point counts differ across the matrix: {set(point_counts)}")
    return rows


def _scorecard_path(rank: int, key: str, scene_name: str) -> Path:
    return SCORE_DIR / f"r{rank}_{key}__{scene_name}.json"


def _figure_path(rank: int, key: str, scene_name: str) -> Path:
    slug = scene_name.replace("+", "p").replace("-", "m")
    return FIG_DIR / f"r{rank}_{key}__{slug}.png"


def _run_open3d(scene) -> tuple[dict, list]:
    run = run_baseline(scene)
    sections = score_run(scene, run)
    sections["detection"]["note"] = (
        "Refined Open3D stud prior on this phase 1 S1 synthetic stud. "
        "Counts are this scene, not a field accuracy."
    )
    sections["angle"]["note"] = "Truth is the generator lean against +Z. S1 has no floor. Not a SKIL reading."
    card = ran_card(
        algorithm_id="A1",
        algorithm="Refined Open3D stud prior",
        rank=1,
        scene=scene_record(scene),
        sections=sections,
        implementation={
            "module": "openwall_stud.open3d_baseline",
            "reference": run.reference,
            "floor_found": run.floor_found,
            "dbscan_eps_m": run.dbscan_eps_m,
            "dbscan_min_points": run.dbscan_min_points,
            "bbox_kind": "minimal_oriented",
        },
        implementation_short="Refined Open3D DBSCAN and minimal OBB. S1 reference is +Z.",
    )
    return card, run.detections


def _runners():
    return {
        "open3d": _run_open3d,
        "pcl": run_pcl,
        "cloudcompare": run_cloudcompare,
        "pointcept": run_pointcept,
        "open3d_ml": run_open3d_ml,
        "pyransac3d": run_pyransac,
    }


def _package_version(name: str) -> str:
    import importlib.metadata

    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def _meta(group: str) -> dict[str, Any]:
    probe = gpu_probe()
    versions: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }
    if group == "classical":
        import matplotlib
        import numpy
        import open3d

        versions.update(
            {
                "open3d": open3d.__version__,
                "numpy": numpy.__version__,
                "matplotlib": matplotlib.__version__,
                "pyransac3d": _package_version("pyransac3d"),
            }
        )
    elif group == "pointcept":
        versions["torch"] = probe.get("torch_version")
    elif group == "open3d_ml":
        versions["torch"] = probe.get("torch_version")
        try:
            import open3d

            versions["open3d"] = open3d.__version__
        except Exception as exc:
            versions["open3d"] = f"import failed: {type(exc).__name__}: {exc}"
    return {"group": group, "versions": versions, "gpu": probe}


def _write_meta(group: str) -> None:
    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    path = SCORE_DIR / f"_meta_{group}.json"
    path.write_text(json.dumps(_meta(group), indent=2) + "\n", encoding="utf-8")


def _ensure_day_row(card: dict[str, Any], scene_name: str, key: str) -> None:
    from openwall_stud.one_stud import apply_verdict, day_notes

    verdict = card.get("stage0_pass_fail") or apply_verdict(card)
    append_day_row(
        algorithm=key,
        stage=0,
        scene=scene_name,
        ground_truth_source="synthetic",
        pass_fail=verdict,
        notes=day_notes(card, card.get("scorecard_name") or _scorecard_path(int(card["rank"]), key, scene_name).name),
        card=None if verdict in {"blocked_install", "not_run"} else card,
        root=repo_root(),
    )


def run_group(group: str, *, resume: bool) -> int:
    assert_paint_rules()
    specs = assert_s1_matrix()
    print(f"Matrix ok: {len(specs)} scenes, {specs[0]['n_points']} points each, seed {SEED}")
    runners = _runners()
    if group == "classical":
        selected = [item for item in FINDERS if item["group"] == "classical"]
    else:
        selected = [item for item in FINDERS if item["key"] == group]
    if not selected:
        raise SystemExit(f"unknown group {group}")
    _write_meta(group)
    for spec in specs:
        scene = make_s1_scene(spec["lean_deg"], spec["axis"])
        for finder in selected:
            out = _scorecard_path(finder["rank"], finder["key"], scene.name)
            if resume and out.is_file():
                card = json.loads(out.read_text(encoding="utf-8"))
                _ensure_day_row(card, scene.name, finder["key"])
                print(f"resume {finder['key']} {scene.name} status={card.get('status')} bars={card.get('stage0_pass_fail')}")
                continue
            print(f"--- {finder['key']} {scene.name} ---", flush=True)
            card, detections = runners[finder["key"]](scene)
            figure = None
            if finder["group"] == "classical" and scene.name in REPRESENTATIVE and detections:
                figure = _figure_path(finder["rank"], finder["key"], scene.name)
            publish_attempt(
                algorithm=finder["key"],
                card=card,
                detections=detections,
                scene=scene,
                out=out,
                figure=figure,
                write_day_row=True,
            )
            print(
                f"{finder['key']} {scene.name}: status={card.get('status')} "
                f"bars={card.get('stage0_pass_fail')} runtime={(card.get('cost') or {}).get('runtime_s')}",
                flush=True,
            )
    return 0


def _fmt(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        text = f"{value:.5f}".rstrip("0").rstrip(".")
        return text or "0"
    if isinstance(value, list):
        if not value:
            return "—"
        if all(item == value[0] for item in value):
            return f"{value[0]} x{len(value)}"
        return ",".join(str(item) for item in value)
    return str(value)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _row_from_card(finder: dict[str, Any], spec: dict[str, Any], card: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "rank": finder["rank"],
        "algorithm_key": finder["key"],
        "algorithm": finder["name"],
        "group": finder["group"],
        "scene": spec["name"],
        "lean_deg": spec["lean_deg"],
        "axis": spec["axis"],
        "status": "not_run",
        "precision": None,
        "recall": None,
        "section_mm": None,
        "length_mm": None,
        "angle_mae_deg": None,
        "angle_max_abs_deg": None,
        "paint": None,
        "runtime_s": None,
        "stage0_pass_fail": "not_run",
        "scorecard": None,
        "figure": None,
        "stud_metrics_scored": None,
        "blocker_short": None,
        "implementation_short": None,
    }
    if card is None:
        return row
    row["algorithm"] = card.get("algorithm") or finder["name"]
    row["status"] = card.get("status")
    row["stage0_pass_fail"] = card.get("stage0_pass_fail")
    row["stud_metrics_scored"] = card.get("stud_metrics_scored", card.get("status") == "ran")
    row["scorecard"] = f"artifacts/scorecards/phase1_s1/{_scorecard_path(finder['rank'], finder['key'], spec['name']).name}"
    row["figure"] = card.get("figure")
    row["blocker_short"] = card.get("blocker_short")
    row["implementation_short"] = card.get("implementation_short")
    if card.get("status") == "blocked_install" or card.get("stud_metrics_scored") is False:
        cost = card.get("cost") or {}
        if card.get("stud_metrics_scored") is False:
            row["runtime_s"] = cost.get("runtime_s")
        return row
    if card.get("status") != "ran":
        return row
    det = card.get("detection") or {}
    geom = card.get("geometry") or {}
    ang = card.get("angle") or {}
    paint = card.get("paint") or {}
    cost = card.get("cost") or {}
    row.update(
        {
            "precision": det.get("precision"),
            "recall": det.get("recall"),
            "section_mm": geom.get("max_section_error_mm"),
            "length_mm": geom.get("max_length_error_mm"),
            "angle_mae_deg": ang.get("mae_deg"),
            "angle_max_abs_deg": ang.get("max_abs_error_deg"),
            "paint": paint.get("production_colors") or None,
            "runtime_s": cost.get("runtime_s"),
        }
    )
    return row


def _hist_fingerprint(card: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if not card:
        return None
    return ((card.get("control") or {}).get("label_histogram")) or None


def _histogram_span(histograms: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    names = [str(item.get("name")) for item in histograms[0]]
    spans = []
    for name in names:
        counts = []
        for hist in histograms:
            match = next(item for item in hist if str(item.get("name")) == name)
            counts.append(int(match.get("count") or 0))
        spans.append({"name": name, "min": min(counts), "max": max(counts)})
    return spans


def _control_summary(finder: dict[str, Any], specs: list[dict[str, Any]]) -> dict[str, Any]:
    histograms = []
    statuses = []
    labeled = []
    stud_names: list[str] = []
    for spec in specs:
        card = _load_json(_scorecard_path(finder["rank"], finder["key"], spec["name"]))
        statuses.append(None if card is None else card.get("status"))
        hist = _hist_fingerprint(card)
        histograms.append(hist)
        control = (card or {}).get("control") or {}
        if control.get("stud_class_names") is not None and not stud_names:
            stud_names = list(control.get("stud_class_names") or [])
        if control.get("n_points_labeled") is not None:
            labeled.append(int(control["n_points_labeled"]))
        elif control.get("n_points_in") is not None and hist:
            labeled.append(int(control["n_points_in"]))
    present = [item for item in histograms if item is not None]
    unique = []
    for item in present:
        if item not in unique:
            unique.append(item)
    identical = len(unique) == 1 and len(present) == len(specs)
    span = _histogram_span(present) if present else []
    stud_positive = [
        item["name"]
        for item in span
        if "stud" in item["name"].lower() and item["max"] > 0
    ]
    return {
        "rank": finder["rank"],
        "algorithm": finder["name"],
        "n_scorecards": sum(status is not None for status in statuses),
        "statuses": sorted({str(status) for status in statuses}),
        "n_histograms": len(present),
        "histograms_identical": identical,
        "unique_histogram_count": len(unique),
        "label_histogram": unique[0] if identical else None,
        "label_count_span": span,
        "n_points_labeled_min": min(labeled) if labeled else None,
        "n_points_labeled_max": max(labeled) if labeled else None,
        "stud_class_names": stud_names,
        "stud_named_classes_with_points": stud_positive,
        "stud_metrics": "null on every scene in this control unless a scorecard says a stud class was scored",
    }


def _count_bars(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = []
    for finder in FINDERS:
        subset = [row for row in rows if row["rank"] == finder["rank"]]
        tally: dict[str, int] = {}
        for row in subset:
            key = str(row.get("stage0_pass_fail") or "missing")
            tally[key] = tally.get(key, 0) + 1
        counts.append(
            {
                "rank": finder["rank"],
                "algorithm": finder["name"],
                "group": finder["group"],
                "n_rows": len(subset),
                "bars": tally,
            }
        )
    return counts


def _table(rows: list[dict[str, Any]]) -> str:
    header = (
        "| Rank | Scene | Lean deg | Axis | Status | P | R | Section mm | Length mm | "
        "Angle MAE deg | Angle max abs deg | Paint | Runtime s | Stage 0 bars |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    )
    lines = []
    for row in rows:
        lines.append(
            "| {rank} | `{scene}` | {lean} | {axis} | {status} | {p} | {r} | {section} | {length} | "
            "{mae} | {amax} | {paint} | {runtime} | {bars} |".format(
                rank=row["rank"],
                scene=row["scene"],
                lean=_fmt(row["lean_deg"]),
                axis=row["axis"],
                status=row["status"],
                p=_fmt(row["precision"]),
                r=_fmt(row["recall"]),
                section=_fmt(row["section_mm"]),
                length=_fmt(row["length_mm"]),
                mae=_fmt(row["angle_mae_deg"]),
                amax=_fmt(row["angle_max_abs_deg"]),
                paint=_fmt(row["paint"]),
                runtime=_fmt(row["runtime_s"]),
                bars=row["stage0_pass_fail"],
            )
        )
    return header + "\n".join(lines)


def _count_table(counts: list[dict[str, Any]]) -> str:
    header = "| Rank | Stack | Role | Scenes | pass | fail | control | blocked_install | not_run |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    lines = []
    for item in counts:
        bars = item["bars"]
        lines.append(
            f"| {item['rank']} | {item['algorithm']} | {item['group']} | {item['n_rows']} | "
            f"{bars.get('pass', 0)} | {bars.get('fail', 0)} | {bars.get('control', 0)} | "
            f"{bars.get('blocked_install', 0)} | {bars.get('not_run', 0)} |"
        )
    return header + "\n".join(lines)


def _hist_table(histogram: list[dict[str, Any]] | None) -> str:
    if not histogram:
        return "No histogram was recorded.\n"
    lines = ["| Class | Count |", "| --- | --- |"]
    for item in histogram:
        lines.append(f"| {item.get('name')} | {item.get('count')} |")
    return "\n".join(lines) + "\n"


def _span_table(span: list[dict[str, Any]] | None) -> str:
    if not span:
        return "No histogram was recorded.\n"
    lines = ["| Class | Min count | Max count |", "| --- | --- | --- |"]
    for item in span:
        lines.append(f"| {item.get('name')} | {item.get('min')} | {item.get('max')} |")
    return "\n".join(lines) + "\n"


def _same_text(finder: dict[str, Any], specs: list[dict[str, Any]], field: str) -> list[str]:
    values: list[str] = []
    for spec in specs:
        card = _load_json(_scorecard_path(finder["rank"], finder["key"], spec["name"])) or {}
        text = card.get(field)
        if text and text not in values:
            values.append(str(text))
    return values


def _figure_section(rows: list[dict[str, Any]]) -> str:
    shown = [row for row in rows if row.get("figure") and str(row["figure"]).startswith("docs/research/")]
    if not shown:
        return "No representative box was written. A finder with no detection does not get a painted box in this note.\n"
    blocks = []
    for row in shown:
        rel = str(row["figure"])[len("docs/research/") :]
        blocks.append(
            f"### Rank {row['rank']} `{row['scene']}`\n\n"
            f"Stage 0 bars: `{row['stage0_pass_fail']}`. Paint: {_fmt(row['paint'])}.\n\n"
            f"![{row['algorithm']} {row['scene']}]({rel})\n"
        )
    return "\n".join(blocks)


def write_report() -> None:
    specs = assert_s1_matrix()
    rows = []
    for finder in FINDERS:
        for spec in specs:
            card = _load_json(_scorecard_path(finder["rank"], finder["key"], spec["name"]))
            rows.append(_row_from_card(finder, spec, card))
    counts = _count_bars(rows)
    controls = [
        _control_summary(finder, specs)
        for finder in FINDERS
        if finder["group"] == "control"
    ]
    metas = {
        name: _load_json(SCORE_DIR / f"_meta_{name}.json")
        for name in ("classical", "pointcept", "open3d_ml")
    }
    date = today_la()
    n_cards = sum(1 for row in rows if row["scorecard"])
    gpu = {}
    for meta in metas.values():
        if meta and (meta.get("gpu") or {}).get("nvidia_query"):
            gpu = meta["gpu"]
            break
    payload = {
        "doc": "docs/research/19-phase1-s1-lean-sweep.md",
        "date_america_los_angeles": date,
        "machine": "Oz_PC",
        "experiment": "phase1_s1_single_rigid_lean",
        "not_field_accuracy": True,
        "epsilon_locked": False,
        "not_s1b": True,
        "not_field_phone_or_skil": True,
        "scene_count_expected": 25,
        "scene_count_generated": len(specs),
        "scorecards_written": n_cards,
        "matrix": {
            "nominal": "dressed 2x4",
            "length": "8 ft",
            "spacing_m": 0.005,
            "noise_std_m": 0.001,
            "noise": "Gaussian",
            "seed": SEED,
            "seed_note": "The same seed is passed to every scene. Noise is drawn after the lean, in generator coordinates.",
            "reference": "gravity_z_no_floor_plane",
            "floor": False,
            "cloud_rotated_onto_another_frame": False,
            "long_axis_before_lean": "+Z",
            "lean_magnitudes_deg": list(MAGNITUDES_DEG),
            "axes_when_lean_nonzero": list(LEAN_AXES),
            "axis_when_lean_zero": "none",
            "rotation": "right-hand about the named axis",
            "scenes": specs,
        },
        "stage0_bars": {
            "detection": "precision = 1 and recall = 1",
            "section_mm_max": 10.0,
            "length_mm_max": 25.0,
            "angle_deg_max_abs": 0.05,
            "paint": "yellow",
            "scope": "synthetic bring-up only, not field accuracy",
        },
        "ranks_4_and_5": "controls. Stud metrics stay null when the forward pass has no stud class.",
        "summary_counts": counts,
        "rows": rows,
        "controls": controls,
        "versions_by_group": metas,
        "gpu": {
            "nvidia_query": gpu.get("nvidia_query"),
            "torch_device": gpu.get("torch_device"),
        },
        "commands": [
            ".venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py",
            ".venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --finder classical",
            ".venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --finder pointcept",
            ".venv-o3dml\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --finder open3d_ml",
            ".venv\\Scripts\\python.exe scripts/run_phase1_s1_lean_sweep.py --report-only",
        ],
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    version_lines = []
    for name, meta in metas.items():
        if not meta:
            version_lines.append(f"- `{name}`: meta file was not written")
            continue
        version_lines.append(f"- `{name}` python: {meta.get('versions', {}).get('python')} ({meta.get('versions', {}).get('executable')})")
        for key, value in (meta.get("versions") or {}).items():
            if key in {"python", "executable"}:
                continue
            version_lines.append(f"  - `{key}`: {value}")
        probe = meta.get("gpu") or {}
        if probe.get("nvidia_query") or probe.get("torch_version"):
            version_lines.append(
                f"  - gpu: {probe.get('nvidia_query') or 'not reported'}; "
                f"torch {probe.get('torch_version')}; cuda_available={probe.get('torch_cuda_available')}; "
                f"device {probe.get('torch_device')}"
            )
    control_blocks = []
    for item in controls:
        identical = item["histograms_identical"]
        stud_named = ", ".join(item["stud_class_names"]) if item["stud_class_names"] else "none"
        positive = item.get("stud_named_classes_with_points") or []
        positive_text = ", ".join(positive) if positive else "none"
        labeled = ""
        if item.get("n_points_labeled_min") is not None:
            labeled = (
                f" Labeled-point count min/max: {item['n_points_labeled_min']} / {item['n_points_labeled_max']}."
            )
        if item["n_histograms"] == 0:
            hist_note = "No histogram was recorded. Stud metrics were not filled."
            table = "No histogram was recorded.\n"
        elif identical:
            hist_note = (
                f"All {item['n_histograms']} recorded histograms on this matrix were identical. "
                f"Stud-named classes: {stud_named}. "
                f"Stud-named classes with a nonzero count: {positive_text}. "
                "Stud precision, recall, section, length, angle, and paint stay null."
                f"{labeled}"
            )
            table = _hist_table(item["label_histogram"])
        else:
            hist_note = (
                f"{item['unique_histogram_count']} distinct histograms across {item['n_histograms']} scorecards. "
                "The table is the min and max count of each class on those scorecards. "
                "Per-scene histograms stay on the scorecards and are not replaced by one invented histogram. "
                f"Stud-named classes: {stud_named}. "
                f"Stud-named classes with a nonzero count: {positive_text}. "
                "Stud precision, recall, section, length, angle, and paint stay null."
                f"{labeled}"
            )
            table = _span_table(item.get("label_count_span"))
        control_blocks.append(
            f"### Rank {item['rank']}. {item['algorithm']}\n\n"
            f"Role: control. Scorecards: {item['n_scorecards']} of 25. Statuses: {', '.join(item['statuses']) or 'none'}.\n\n"
            f"{hist_note}\n\n"
            f"{table}"
        )
    finder_notes = []
    for finder in FINDERS:
        if finder["key"] == "pcl":
            shorts = _same_text(finder, specs, "implementation_short")
            native_flags = []
            for spec in specs:
                card = _load_json(_scorecard_path(finder["rank"], finder["key"], spec["name"])) or {}
                flag = (card.get("implementation") or {}).get("native_pcl_region_growing")
                if flag not in native_flags:
                    native_flags.append(flag)
            finder_notes.append(
                "Rank 2 `native_pcl_region_growing` values on these scorecards: "
                + ", ".join(str(flag) for flag in native_flags)
                + ". "
                + " ".join(shorts)
            )
        if finder["key"] == "cloudcompare":
            shorts = _same_text(finder, specs, "blocker_short")
            finder_notes.append("Rank 3 blocker: " + " ".join(shorts))
    text = f"""# Phase 1 S1 lean sweep

Date (America/Los_Angeles): **{date}**. Machine: **Oz_PC**. This note is one rigid lean on one synthetic dressed 2×4. It is the stage 0 style bring-up (S1). It is not a multi-stud wall, not a plate-fixed bow (S1b), and not a field, phone, or SKIL measurement.

Machine-readable twin: [19-phase1-s1-lean-sweep.json](19-phase1-s1-lean-sweep.json).

Ranks 4 and 5 are controls. A histogram is not a stud score. Device ε is unlocked, so a production color is yellow when a box exists. This note does not paint green or red as the production call.

## Matrix

Generated by `phase1_s1_single_stud` in `src/openwall_stud/synthetic.py`. The long axis is +Z before a right-hand lean. The cloud is not rotated onto a floor or any other frame. Lean 0 runs once, with axis label `none`.

| | |
| --- | --- |
| Nominal | dressed 2×4, length 8 ft |
| Surface spacing | 0.005 m |
| Noise | Gaussian, 0.001 m, seed **{SEED}** on every scene |
| Angle reference | generator +Z (`gravity_z_no_floor_plane`) |
| Floor | none |
| Magnitudes (deg) | 0, 0.05, 0.12, 0.15, 0.30, 1.0, 4.0 |
| Axes when lean ≠ 0 | +X, −X, +Y, −Y |
| Scene count | {len(specs)} generated, {n_cards} scorecards written of {len(specs) * 6} finder-scene pairs |
| Points per cloud | {specs[0]["n_points"]} |

Scene ids use `s1_2x4_lean{{magnitude:.3f}}_ax{{axis}}`. The zero cloud is `s1_2x4_lean0.000_axnone`. The generator check in the JSON twin records each long axis and its angle from +Z. That check refuses to start the sweep if the angle disagrees with the requested magnitude.

## Stage 0 bars

These bars are the synthetic bring-up checks. They are not a field acceptance test.

| Check | Bar |
| --- | --- |
| Detection | precision = 1 and recall = 1 |
| Section | max absolute error ≤ 10 mm |
| Length | max absolute error ≤ 25 mm |
| Angle | max absolute error ≤ 0.05° |
| Paint | yellow |

`control` means the forward pass ran and the stud bars were not scored. `blocked_install` means the cloud was built and the stack did not segment it. Both leave stud cells empty.

## Counts

{_count_table(counts)}

## Scorecard

One row is one finder on one scene. Empty cells were not measured.

{_table(rows)}

## Versions and hardware

`nvidia-smi`: {gpu.get("nvidia_query") or "not recorded on a meta file"}

Pointcept is rank 4 and uses `.venv` (the BIMStruct3D CUDA torch pin). Open3D-ML is rank 5 and uses `.venv-o3dml`. Ranks 1, 2, 3, and 6 use `.venv`. Rank 4 `runtime_s` includes checkpoint load, normal estimation, and the 10-pass test-time augmentation on that scene, because each scene calls the existing `run_one_stud` path. Rank 5 `runtime_s` is `run_inference` after that scene's checkpoint load.

{chr(10).join(version_lines)}

## What the scorecards say about ranks 2 and 3

{"\n\n".join(finder_notes) if finder_notes else "No rank 2 or rank 3 note was on the scorecards."}

Rank 2 metrics are the run that the scorecard names. They are not a libpcl measurement when `native_pcl_region_growing` is false. Rank 3 stud cells stay empty when the binary was not on PATH.

## Controls

{chr(10).join(control_blocks)}

## Representative renders

Offline PNGs for the classical finders on lean 0°, 0.15° about +X, and 4° about +Y, and only when that finder returned a box. The section view looks along generator Z. Production paint on a box is yellow because ε is unlocked.

{_figure_section(rows)}

## What this run did not do

No second stud, no plate, no bow (S1b), no stage 2 floor, no stage 3 mini wall, no SAM 2, no YOLO, no RoomPlan, no phone capture, no SKIL reading, and no claim that a synthetic pass is field accuracy. S3DIS mIoU and BIMStruct3D class counts are not stud scores.
"""
    REPORT_MD.write_text(text, encoding="utf-8")
    print(f"Wrote {REPORT_MD} ({n_cards} scorecards)")


def _spawn(python: Path, finder: str, resume: bool) -> int:
    if not python.is_file():
        print(f"Missing interpreter {python}")
        return 127
    command = [str(python), str(Path(__file__).resolve()), "--finder", finder]
    if resume:
        command.append("--resume")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    print(f"=== spawn {finder} via {python} ===", flush=True)
    proc = subprocess.run(command, cwd=ROOT, env=env, check=False)
    print(f"=== {finder} exit {proc.returncode} ===", flush=True)
    return int(proc.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 S1 lean magnitude x axis sweep.")
    parser.add_argument("--check-only", action="store_true", help="Check the 25-scene matrix and exit.")
    parser.add_argument("--report-only", action="store_true", help="Rewrite doc 19 from scorecards.")
    parser.add_argument(
        "--finder",
        choices=("classical", "pointcept", "open3d_ml"),
        default=None,
        help="Run one group in this interpreter. Default runs all three, then the report.",
    )
    parser.add_argument("--resume", action="store_true", help="Keep an existing scorecard and only upsert its day row.")
    args = parser.parse_args(argv)
    if args.check_only:
        rows = assert_s1_matrix()
        print(f"OK {len(rows)} scenes, {rows[0]['n_points']} points, seed {SEED}")
        for row in rows:
            print(f"{row['name']} theta={row['theta_from_plus_z_deg']:.6f} axis={row['long_axis']}")
        return 0
    if args.report_only:
        write_report()
        return 0
    if args.finder:
        return run_group(args.finder, resume=args.resume)
    assert_s1_matrix()
    codes = [
        _spawn(PY_PT, "classical", args.resume),
        _spawn(PY_PT, "pointcept", args.resume),
        _spawn(PY_ML, "open3d_ml", args.resume),
    ]
    write_report()
    return 0 if all(code == 0 for code in codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
