"""CloudCompare RANSAC Shape Detection on the one Stage 0 stud.

Install
    Invoked as a separate process. This repo does not copy or link the GPL
    sources. The command is ``CloudCompare -RANSAC`` with the RANSAC Shape
    Detection plugin (Schnabel, Wahl, and Klein 2007).

    Discovery order for the binary:

    1. ``CLOUDCOMPARE_EXE`` (absolute path to ``CloudCompare`` or
       ``CloudCompare.exe``).
    2. The Oz_PC default ``C:\\Program Files\\CloudCompare\\CloudCompare.exe``
       when that file exists.
    3. ``CloudCompare`` or ``cloudcompare`` on ``PATH``.

    On Linux the plugin file is ``libQRANSAC_SD_PLUGIN.so``. On Windows it is
    ``QRANSAC_SD_PLUGIN.dll`` next to the executable.

    QRANSAC-SD has no cuboid. Its shapes are plane, sphere, cylinder, cone,
    and torus. This module asks for planes only, then merges the faces of one
    dressed 2x4 into a single minimal OBB. A cylinder on a 2x4 is not a stud.

Entrypoint
    python -m openwall_stud.contenders.cloudcompare_ransac

    ``--stub`` writes the null card and does not launch CloudCompare.
    ``--smoke`` launches ``CloudCompare -SILENT -NO_TIMESTAMP`` once and writes
    ``artifacts/scorecards/cloudcompare_smoke.json``.

    This 2.14.beta build has no ``-H`` switch. That token is
    ``Unknown or misplaced command: '-H'`` and opens the command-line window.
    The stud command always starts with ``-SILENT -NO_TIMESTAMP``. Listing
    commands, when needed, is ``-SILENT -NO_TIMESTAMP -HELP``.

Do not
    Do not link CloudComPy into a closed-source app.
    Do not treat a cylinder fit on a 2x4 as a stud instance.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from openwall_stud.contenders.common import blocked_card, emit_stub, ran_card, stub_card
from openwall_stud.lumber import DRESSED_SECTION_M, STUD_LENGTH_8FT_M
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.open3d_baseline import _point_cloud
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

CLOUDCOMPARE = {
    "rank": 3,
    "algorithm_id": "A3",
    "status": "stub",
    "name": "CloudCompare RANSAC-SD / CloudComPy",
}

# Env override, then the Oz_PC install, then PATH. See resolve_cloudcompare_binary.
CLOUDCOMPARE_ENV = "CLOUDCOMPARE_EXE"
DEFAULT_WINDOWS_CLOUDCOMPARE = Path(r"C:\Program Files\CloudCompare\CloudCompare.exe")
_ABOUT_VERSION = re.compile(rb"(\d+\.\d+\.(?:alpha|beta|stable|\d+)) \(%1\)")
_BUILD_DATE = re.compile(
    rb"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4})"
)

# Plugin shapes, from the CloudCompare -RANSAC command (2.11+). No cuboid.
RANSAC_SHAPES = ("PLANE", "SPHERE", "CYLINDER", "CONE", "TORUS")
_PRIMITIVE_KIND = re.compile(r"_(PLANE|SPHERE|CYLINDER|CONE|TORUS)_", re.IGNORECASE)
_UP = np.array([0.0, 0.0, 1.0])

# Dressed 2x4 face gates. Long faces are ~2.44 m by 38 mm or 89 mm.
# End caps are the section, with a normal near +Z. S1 leans are at most 4°.
_LONG_FACE_MIN_M = 0.80
_FACE_WIDTH_MIN_M = 0.020
_FACE_WIDTH_MAX_M = 0.120
_PLANE_THICKNESS_MAX_M = 0.025
_END_CAP_MAX_M = 0.160
_END_NORMAL_MIN_COS = 0.90
_ADJACENT_CENTER_M = 0.12
_COPLANAR_COS = 0.985
_COPLANAR_OFFSET_M = 0.012
_COPLANAR_ALONG_M = 1.6
# Shards of one face line up across the face width. The next stud on a
# coplanar narrow face is a bay away (~406 mm), so 30 mm does not reach it.
_COPLANAR_ACROSS_M = 0.030
_END_XY_M = 0.08
_END_ALONG_M = 1.5
_VERTICAL_MAX_DEG = 15.0


@dataclass(frozen=True)
class RansacStudParams:
    """Knobs for one stud-sized box. See knob_notes and doc 21.

    Chosen on the three-scene grid in ``scripts/tune_cloudcompare_stud.py``
    (0°, 0.15° about +X, 4° about +Y). Several plane-only rows tied on
    section. This row also tied the best angle and returned four planes,
    one per long face. See docs/research/21-cloudcompare-stud-param-tune.md.

    - epsilon 6 mm: above the 1 mm noise, below half the 38 mm thickness,
      so the opposite face stays a separate plane.
    - bitmap epsilon 12 mm: just above the 5 mm surface spacing. 20 mm tied
      on the grid; 12 mm is the tighter cell that still kept one face intact.
    - support 800: above an end cap (~135 points at 5 mm) and below half of
      a narrow face (~3700). The grid's support-400 rows kept extra fragments.
    - max normal deviation 25°: the faces are flat, and 25° beat 15° on the
      upright scene's long-axis angle (0.0056° versus 0.0077°).
    - probability 0.01: the plugin default overlooking probability.
    - PLANE only: a dressed 2x4 is not a cylinder, sphere, cone, or torus.
      Leaving the cylinder on dropped two long faces on the upright stud
      and failed the 0.05° angle bar.
    """

    epsilon_absolute_m: float = 0.006
    bitmap_epsilon_absolute_m: float = 0.012
    support_points: int = 800
    max_normal_dev_deg: float = 25.0
    probability: float = 0.01
    primitives: tuple[str, ...] = ("PLANE",)


DEFAULT_RANSAC_STUD = RansacStudParams()


def _fmt_num(value: float) -> str:
    return f"{float(value):.6g}"


def ransac_arg_tokens(params: RansacStudParams | None = None) -> list[str]:
    """CloudCompare ``-RANSAC`` tokens for these knobs."""
    chosen = params or DEFAULT_RANSAC_STUD
    unknown = [name for name in chosen.primitives if name not in RANSAC_SHAPES]
    if unknown:
        raise ValueError(f"RANSAC-SD has no primitive {unknown}. Shapes: {RANSAC_SHAPES}")
    if not chosen.primitives:
        raise ValueError("at least one RANSAC primitive is required")
    return [
        "EPSILON_ABSOLUTE",
        _fmt_num(chosen.epsilon_absolute_m),
        "BITMAP_EPSILON_ABSOLUTE",
        _fmt_num(chosen.bitmap_epsilon_absolute_m),
        "SUPPORT_POINTS",
        str(int(chosen.support_points)),
        "MAX_NORMAL_DEV",
        _fmt_num(chosen.max_normal_dev_deg),
        "PROBABILITY",
        _fmt_num(chosen.probability),
        "ENABLE_PRIMITIVE",
        *chosen.primitives,
        "OUTPUT_INDIVIDUAL_SUBCLOUDS",
    ]


def knob_notes(params: RansacStudParams | None = None) -> dict[str, str]:
    """Plain-language record of each knob. Written onto the scorecard."""
    chosen = params or DEFAULT_RANSAC_STUD
    shapes = ", ".join(chosen.primitives)
    return {
        "primitives": (
            "QRANSAC-SD shapes are PLANE, SPHERE, CYLINDER, CONE, and TORUS. "
            f"There is no cuboid primitive. This run enables {shapes}. "
            "CYLINDER stays off when it is not listed: a dressed 2x4 is not a cylinder, "
            "and a cylinder inlier set was an extra detection on the untuned pass."
        ),
        "epsilon_absolute_m": (
            f"{chosen.epsilon_absolute_m} m max distance from a point to the primitive. "
            "Generator noise is 1 mm and the surface spacing is 5 mm. "
            "The value stays under half of the 38 mm dressed thickness so the opposite face "
            "is not swallowed into the same plane."
        ),
        "bitmap_epsilon_absolute_m": (
            f"{chosen.bitmap_epsilon_absolute_m} m in-plane bitmap cell "
            "(Schnabel bitmap epsilon). Larger than the 5 mm spacing so one face "
            "stays one primitive instead of splitting into shards."
        ),
        "support_points": (
            f"{chosen.support_points} minimum inliers. "
            "At 5 mm spacing a narrow 2x4 face is about 3700 points and an end cap is about 135. "
            "A threshold in the hundreds keeps the long faces and drops end-grain crumbs."
        ),
        "max_normal_dev_deg": (
            f"{chosen.max_normal_dev_deg} degrees. Points whose normals leave the primitive "
            "by more than this are not inliers. Stud faces are planar."
        ),
        "probability": (
            f"{chosen.probability} is the probability that a better candidate was overlooked. "
            "Lower is a longer search. 0.01 is the plugin's usual setting."
        ),
        "merge": (
            "Planes that match a dressed 2x4 face (long face ~2.44 m by 38 or 89 mm, "
            "or an end cap with a normal near +Z) are grouped. Adjacent face centers "
            "within 120 mm are one stud. Coplanar shards of one face are one face. "
            "The group is one point set and one minimal OBB. "
            "If several groups exist, the best section, length, and Z-up score is kept. "
            "This pass keeps one box. It is not a multi-stud segmenter."
        ),
    }


def _plane_frame(points: np.ndarray) -> dict[str, Any]:
    """PCA frame. Extents are ordered thickness, mid, long."""
    center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - center, full_matrices=False)
    axes = vh.T
    local = (points - center) @ axes
    extents = local.max(axis=0) - local.min(axis=0)
    order = np.argsort(extents)
    return {
        "points": points,
        "center": center,
        "normal": axes[:, int(order[0])],
        "mid_axis": axes[:, int(order[1])],
        "long_axis": axes[:, int(order[2])],
        "extents": extents[order],
        "n": int(len(points)),
    }


def _is_long_face(frame: dict[str, Any]) -> bool:
    thickness, width, length = (float(value) for value in frame["extents"])
    return (
        length >= _LONG_FACE_MIN_M
        and _FACE_WIDTH_MIN_M <= width <= _FACE_WIDTH_MAX_M
        and thickness <= _PLANE_THICKNESS_MAX_M
    )


def _is_end_cap(frame: dict[str, Any]) -> bool:
    _thickness, mid, length = (float(value) for value in frame["extents"])
    normal = frame["normal"]
    cosine = abs(float(np.dot(normal, _UP)))
    return length <= _END_CAP_MAX_M and mid <= _END_CAP_MAX_M and cosine >= _END_NORMAL_MIN_COS


def _coplanar(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True for shards of one face, false for the next stud's coplanar face.

    Neighboring studs in a wall share a narrow-face plane. Their centers are
    a bay apart across that face. A split of one face is apart along the stud
    and lines up across the face width.
    """
    align = abs(float(np.dot(a["normal"], b["normal"])))
    if align < _COPLANAR_COS:
        return False
    normal = a["normal"]
    if float(np.dot(normal, b["normal"])) < 0.0:
        normal = -normal
    delta = b["center"] - a["center"]
    offset = abs(float(np.dot(delta, normal)))
    along = abs(float(np.dot(delta, a["long_axis"])))
    across = abs(float(np.dot(delta, a["mid_axis"])))
    return offset <= _COPLANAR_OFFSET_M and across <= _COPLANAR_ACROSS_M and along <= _COPLANAR_ALONG_M


def _give_flat_cloud_a_span(points: np.ndarray) -> np.ndarray:
    """Give a perfectly flat face a 0.1 mm span so the minimal OBB can be built.

    RANSAC inliers already have thickness. A synthetic face does not, and
    Qhull refuses a cloud that is one plane. The bump is far below the
    10 mm section bar, so a lone face still fails that bar.
    """
    centered = points - points.mean(axis=0)
    singular = np.linalg.svd(centered, compute_uv=False)
    scale = max(float(singular[0]), 1.0e-9)
    if len(singular) < 3 or float(singular[-1]) >= 1.0e-6 * scale:
        return points
    bumped = np.array(points, dtype=float, copy=True)
    bumped[0] = bumped[0] + _plane_frame(points)["normal"] * 1.0e-4
    return bumped


def _stud_cost(points: np.ndarray) -> tuple[float, dict[str, float]]:
    """Lower is a closer dressed 2x4 with a long axis near +Z."""
    from openwall_stud.poststep import detections_from_clusters

    detections = detections_from_clusters([_give_flat_cloud_a_span(points)])
    if not detections:
        return 1.0e9, {}
    det = detections[0]
    section = np.sort(det.extent_sorted_m[:2])
    target = np.sort(np.asarray(DRESSED_SECTION_M["2x4"], dtype=float))
    section_mm = float(np.max(np.abs(section - target)) * 1000.0)
    length_mm = abs(float(det.extent_sorted_m[2]) - STUD_LENGTH_8FT_M) * 1000.0
    angle = float(det.theta_deg)
    penalty = 0.0 if angle <= _VERTICAL_MAX_DEG else 1000.0
    cost = section_mm + 0.2 * length_mm + penalty
    return cost, {
        "section_error_mm": round(section_mm, 2),
        "length_error_mm": round(length_mm, 2),
        "angle_from_plus_z_deg": round(angle, 5),
        "n_points": float(len(points)),
        "cost": round(cost, 3),
    }


class _UnionFind:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count))

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[self.parent[index]]
            index = self.parent[index]
        return index

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def merge_plane_faces_to_one_stud(
    labeled: list[tuple[str, np.ndarray]],
) -> tuple[list[np.ndarray], dict[str, Any]]:
    """Collapse stud-sized planes into one point set.

    Returns a list of length 0 or 1. One scene keeps the single best box
    by the dressed 2x4 size prior and a long axis within 15° of +Z.
    """
    planes: list[dict[str, Any]] = []
    rejected_non_plane = 0
    for kind, points in labeled:
        if len(points) < 10:
            continue
        if kind not in {"PLANE", "UNKNOWN"}:
            rejected_non_plane += 1
            continue
        frame = _plane_frame(np.asarray(points, dtype=float))
        frame["kind"] = kind
        planes.append(frame)

    long_faces = [frame for frame in planes if _is_long_face(frame)]
    end_caps = [frame for frame in planes if not _is_long_face(frame) and _is_end_cap(frame)]
    groups = _group_faces(long_faces, end_caps)

    candidates: list[tuple[str, np.ndarray, int]] = []
    for members in groups:
        chunks = [frame["points"] for frame in members]
        candidates.append(("stud_face_group", np.vstack(chunks), len(members)))
    accepted = long_faces + end_caps
    if accepted:
        chunks = [frame["points"] for frame in accepted]
        candidates.append(("all_accepted_faces", np.vstack(chunks), len(accepted)))
    if not candidates:
        for kind, points in labeled:
            if len(points) >= 10:
                candidates.append(("best_single_primitive", np.asarray(points, dtype=float), 1))

    report: dict[str, Any] = {
        "n_input_primitives": len(labeled),
        "n_planes_considered": len(planes),
        "n_rejected_non_plane": rejected_non_plane,
        "n_long_faces": len(long_faces),
        "n_end_caps": len(end_caps),
        "n_groups": len(groups),
        "chosen": None,
        "chosen_faces": 0,
        "chosen_score": None,
    }
    if not candidates:
        return [], report

    best_cost = 1.0e9
    best: tuple[str, np.ndarray, int, dict[str, float]] | None = None
    for name, points, n_faces in candidates:
        cost, score = _stud_cost(points)
        if cost < best_cost:
            best_cost = cost
            best = (name, points, n_faces, score)
    assert best is not None
    name, points, n_faces, score = best
    report["chosen"] = name
    report["chosen_faces"] = n_faces
    report["chosen_score"] = score
    return [points], report


def _group_faces(
    long_faces: list[dict[str, Any]],
    end_caps: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    if not long_faces:
        if not end_caps:
            return []
        # Two end caps of one stud are about a stud length apart.
        return [end_caps]

    union = _UnionFind(len(long_faces))
    for i, left in enumerate(long_faces):
        for j in range(i + 1, len(long_faces)):
            right = long_faces[j]
            gap = float(np.linalg.norm(left["center"] - right["center"]))
            if gap <= _ADJACENT_CENTER_M or _coplanar(left, right):
                union.union(i, j)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for index, frame in enumerate(long_faces):
        grouped.setdefault(union.find(index), []).append(frame)

    attached: dict[int, list[dict[str, Any]]] = {root: [] for root in grouped}
    for cap in end_caps:
        best_root = None
        best_gap = 1.0e9
        for root, members in grouped.items():
            center = np.mean([member["center"] for member in members], axis=0)
            gap_xy = float(np.linalg.norm(cap["center"][:2] - center[:2]))
            gap_z = abs(float(cap["center"][2] - center[2]))
            if gap_xy <= _END_XY_M and gap_z <= _END_ALONG_M and gap_xy < best_gap:
                best_root = root
                best_gap = gap_xy
        if best_root is not None:
            attached[best_root].append(cap)
    return [members + attached[root] for root, members in grouped.items()]


def self_check_stud_merge() -> None:
    """Check the face merge on a synthetic dressed 2x4, with no CloudCompare."""
    one = _synthetic_stud_planes(np.zeros(3))
    clusters, report = merge_plane_faces_to_one_stud(one + [("CYLINDER", np.zeros((40, 3)))])
    if len(clusters) != 1:
        raise AssertionError(f"expected one stud box, got {len(clusters)}")
    if report["n_rejected_non_plane"] < 1:
        raise AssertionError("cylinder points were not rejected")
    _cost, score = _stud_cost(clusters[0])
    if score["section_error_mm"] > 5.0 or score["length_error_mm"] > 5.0:
        raise AssertionError(f"single-stud merge missed the dressed size: {score}")
    if score["angle_from_plus_z_deg"] > 0.05:
        raise AssertionError(f"single-stud long axis left +Z: {score}")

    # A face split along the stud must still come back as one box.
    split_source = one[0][1]
    midpoint = float(np.median(split_source[:, 2]))
    low = split_source[split_source[:, 2] <= midpoint]
    high = split_source[split_source[:, 2] > midpoint]
    split = [("PLANE", low), ("PLANE", high), *one[1:]]
    clusters, _report = merge_plane_faces_to_one_stud(split)
    _cost, score = _stud_cost(clusters[0])
    if score["section_error_mm"] > 5.0:
        raise AssertionError(f"a split face was dropped from the stud: {score}")

    # A second stud one bay away must not win by being glued to the first.
    other = _synthetic_stud_planes(np.array([0.4064, 0.0, 0.0]))
    clusters, report = merge_plane_faces_to_one_stud(one + other)
    if len(clusters) != 1:
        raise AssertionError("selector should keep one box")
    _cost, score = _stud_cost(clusters[0])
    if score["section_error_mm"] > 10.0:
        raise AssertionError(f"two studs were merged into one fat box: {score}")
    if report["n_groups"] < 2:
        raise AssertionError(f"expected two stud groups, got {report}")


def _synthetic_stud_planes(center: np.ndarray, step: float = 0.005) -> list[tuple[str, np.ndarray]]:
    thickness, width = DRESSED_SECTION_M["2x4"]
    length = STUD_LENGTH_8FT_M
    x_axis = np.array([1.0, 0.0, 0.0])
    y_axis = np.array([0.0, 1.0, 0.0])
    z_axis = np.array([0.0, 0.0, 1.0])
    faces: list[np.ndarray] = []
    for sign in (-1.0, 1.0):
        origin = center + np.array([sign * thickness / 2.0, -width / 2.0, -length / 2.0])
        faces.append(_grid_face(origin, y_axis, z_axis, width, length, step))
    for sign in (-1.0, 1.0):
        origin = center + np.array([-thickness / 2.0, sign * width / 2.0, -length / 2.0])
        faces.append(_grid_face(origin, x_axis, z_axis, thickness, length, step))
    for sign in (-1.0, 1.0):
        origin = center + np.array([-thickness / 2.0, -width / 2.0, sign * length / 2.0])
        faces.append(_grid_face(origin, x_axis, y_axis, thickness, width, step))
    return [("PLANE", face) for face in faces]


def _grid_face(
    origin: np.ndarray,
    axis_u: np.ndarray,
    axis_v: np.ndarray,
    span_u: float,
    span_v: float,
    step: float,
) -> np.ndarray:
    count_u = int(round(span_u / step)) + 1
    count_v = int(round(span_v / step)) + 1
    grid_u, grid_v = np.meshgrid(np.arange(count_u), np.arange(count_v), indexing="ij")
    points = (
        origin
        + grid_u[..., None] * (step * axis_u)
        + grid_v[..., None] * (step * axis_v)
    )
    return points.reshape(-1, 3)


def resolve_cloudcompare_binary() -> tuple[str | None, str]:
    """Return ``(path, source)`` for the CloudCompare executable.

    ``source`` is ``env``, ``default_windows_path``, ``path``, or ``missing``.
    A set but missing ``CLOUDCOMPARE_EXE`` is skipped so the default path and
    PATH can still resolve.
    """
    env_value = os.environ.get(CLOUDCOMPARE_ENV, "").strip().strip('"')
    if env_value and Path(env_value).is_file():
        return str(Path(env_value)), "env"
    if DEFAULT_WINDOWS_CLOUDCOMPARE.is_file():
        return str(DEFAULT_WINDOWS_CLOUDCOMPARE), "default_windows_path"
    which = shutil.which("CloudCompare") or shutil.which("cloudcompare")
    if which:
        return which, "path"
    return None, "missing"


def _plugin_file() -> str:
    if os.name == "nt":
        return "QRANSAC_SD_PLUGIN.dll"
    return "libQRANSAC_SD_PLUGIN.so"


def _process_env() -> dict[str, str]:
    env = os.environ.copy()
    # The Windows build ships qwindows.dll, not an offscreen Qt platform.
    if os.name != "nt":
        env["QT_QPA_PLATFORM"] = "offscreen"
        env.setdefault("XDG_RUNTIME_DIR", "/tmp/runtime-ubuntu")
    return env


def _subprocess_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


# Exact tokens. -HELP and -H_EXPORT_FMT are real commands and are not this set.
# -H is not a command on CloudCompare 2.14.beta. It opens an error dialog.
_REJECTED_COMMANDS = {"-H", "-h"}


def _guard_cloudcompare_command(command: list[str]) -> None:
    """Refuse flags that pop a dialog on this build, and require silent mode.

    ``-SILENT`` has to be the first argument. If it comes later, an unknown
    token is reported in the command-line window before silent mode is on.
    """
    rejected = [token for token in command if token in _REJECTED_COMMANDS]
    if rejected:
        raise ValueError(
            f"{rejected[0]} is not a CloudCompare 2.14.beta command. "
            "The build reports Unknown or misplaced command and opens a dialog. "
            "Start with -SILENT -NO_TIMESTAMP. List commands with -HELP after that."
        )
    if len(command) < 2 or command[1] != "-SILENT":
        raise ValueError(
            "CloudCompare must be started with -SILENT so command-line errors "
            "stay off the desktop. -H is not a help flag on this build."
        )


def _run_cloudcompare(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    _guard_cloudcompare_command(command)
    return subprocess.run(command, **kwargs)


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A3",
        algorithm=CLOUDCOMPARE["name"],
        rank=3,
        license_name="GPL-3.0",
        hardware="CPU desktop",
        failure_modes=[
            "CloudCompare and CloudComPy are not installed here, so no primitive was fit.",
            "A 2x4 is not a cylinder. A wall of studs is not one plane.",
            "GPL-3.0 if the library is linked into a shipped app.",
        ],
        note="Stub only. RANSAC Shape Detection was not executed. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    return build_stub_card()


def run_one_stud(
    scene: Scene | None = None,
    *,
    params: RansacStudParams | None = None,
    work: Path | None = None,
) -> tuple[dict[str, Any], list]:
    scene = scene or make_scene()
    record = scene_record(scene)
    chosen = params or DEFAULT_RANSAC_STUD
    binary, binary_source = resolve_cloudcompare_binary()
    work = work or (repo_root() / "artifacts" / "one_stud" / "cloudcompare")
    work.mkdir(parents=True, exist_ok=True)
    if binary is None:
        card = blocked_card(
            algorithm_id="A3",
            algorithm=CLOUDCOMPARE["name"],
            rank=3,
            license_name="GPL-3.0",
            hardware="CPU",
            failure_modes=[
                "CloudCompare was not found via CLOUDCOMPARE_EXE, "
                "the default Windows path, or PATH, so RANSAC-SD was not executed."
            ],
            blocker=(
                "CloudCompare was not found. Discovery checks CLOUDCOMPARE_EXE, then "
                f"{DEFAULT_WINDOWS_CLOUDCOMPARE}, then PATH. The stage 0 cloud was generated "
                f"in-process ({scene.n_points} points) and no primitive was fit. "
                "GPL sources were not copied into this repo. Metrics are null."
            ),
            blocker_short=(
                "CloudCompare binary not found "
                "(CLOUDCOMPARE_EXE, default Windows path, or PATH). "
                "Cloud was generated and not segmented."
            ),
            scene=record,
            attempt={
                "cloud_loaded": True,
                "n_points": scene.n_points,
                "binary": None,
                "binary_source": binary_source,
                "env": CLOUDCOMPARE_ENV,
            },
        )
        return card, []

    ply_path = work / "stud.ply"
    out_dir = work / "primitives"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*"):
        if old.is_file():
            old.unlink()
    _write_ply(ply_path, scene.points_m)
    command = [
        binary,
        "-SILENT",
        "-NO_TIMESTAMP",
        "-AUTO_SAVE",
        "OFF",
        "-C_EXPORT_FMT",
        "PLY",
        "-PLY_EXPORT_FMT",
        "ASCII",
        "-O",
        str(ply_path),
        "-RANSAC",
        *ransac_arg_tokens(chosen),
        "OUT_CLOUD_DIR",
        str(out_dir),
    ]
    env = _process_env()
    started = time.perf_counter()
    proc = _run_cloudcompare(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
        cwd=work,
        **_subprocess_kwargs(),
    )
    runtime_s = time.perf_counter() - started
    log = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-6000:]
    labeled = _load_primitive_clouds(out_dir, ply_path)
    if not labeled:
        labeled = _load_primitive_clouds(work, ply_path)
    attempt = {
        "cloud_loaded": True,
        "n_points": scene.n_points,
        "binary": binary,
        "binary_source": binary_source,
        "command": command,
        "ransac_params": asdict(chosen),
        "returncode": proc.returncode,
        "n_primitive_clouds": len(labeled),
        "primitive_kinds": [kind for kind, _points in labeled],
        "output_files": sorted(path.name for path in out_dir.iterdir() if path.is_file()),
        "log_tail": log,
        "gpl": "Separate process. GPL sources were not copied into this repository.",
    }
    failed = proc.returncode != 0 or "Unknown or misplaced command" in log or "No point cloud to attempt RANSAC" in log
    if failed or (not labeled and "RANSAC" not in log):
        reason = _failure_reason(proc.returncode, log, labeled)
        card = blocked_card(
            algorithm_id="A3",
            algorithm=CLOUDCOMPARE["name"],
            rank=3,
            license_name="GPL-3.0",
            hardware="CPU",
            failure_modes=[
                "The CloudCompare process did not return primitive point sets.",
                "A 2x4 is not a cylinder. Coplanar faces are planes, not one stud instance.",
                "GPL-3.0 if this library is linked into a shipped app. It was not linked here.",
            ],
            blocker=reason,
            blocker_short="CloudCompare RANSAC-SD did not return primitive clouds. Metrics null.",
            scene=record,
            attempt=attempt,
        )
        return card, []

    from openwall_stud.poststep import score_clusters

    stud_clouds, merge_report = merge_plane_faces_to_one_stud(labeled)
    if not stud_clouds:
        reason = _failure_reason(proc.returncode, log, labeled)
        card = blocked_card(
            algorithm_id="A3",
            algorithm=CLOUDCOMPARE["name"],
            rank=3,
            license_name="GPL-3.0",
            hardware="CPU",
            failure_modes=[
                "RANSAC-SD returned primitives, and none survived the stud-face merge.",
                "A 2x4 is not a cylinder. Coplanar faces are planes, not one stud instance, until they are merged.",
                "GPL-3.0 if this library is linked into a shipped app. It was not linked here.",
            ],
            blocker=reason,
            blocker_short="CloudCompare primitives did not yield a stud box. Metrics null.",
            scene=record,
            attempt={**attempt, "merge": merge_report},
        )
        return card, []

    sections, detections = score_clusters(
        scene,
        [_give_flat_cloud_a_span(cloud) for cloud in stud_clouds],
        runtime_s=runtime_s,
        detection_note=(
            "RANSAC-SD plane faces that match a dressed 2x4 are merged into one stud box. "
            "One scene keeps the best box by section, length, and a long axis near +Z. "
            "Counts are this synthetic stud, not a field accuracy."
        ),
        geometry_note=(
            "Section and length are the minimal OBB of the merged stud points versus the dressed 2x4. "
            "The plugin has no cuboid. The box is the union of accepted face planes."
        ),
        angle_note=(
            "Truth is the generator lean against +Z. Not a SKIL reading. "
            "The long axis is the longest side of the merged minimal OBB."
        ),
        cost={
            "runtime_s": round(runtime_s, 4),
            "license": "GPL-3.0",
            "license_note": "CloudCompare was executed as a separate process. Its sources were not vendored or linked.",
            "hardware": "CPU",
            "n_points_in": scene.n_points,
            "failure_modes": [
                "QRANSAC-SD has no cuboid. A missed face leaves the section short.",
                "The merge keeps one box. A second stud in the same cloud would be dropped.",
                "A cylinder on a 2x4 is the wrong section and is not enabled in the tuned command.",
                "GPL-3.0 blocks shipping a closed app linked to CloudCompare. This run does not link it.",
            ],
            "note": "Runtime includes the CloudCompare process on this one stud. It is not a field budget.",
            "command": command,
            "n_primitive_clouds": len(labeled),
            "n_stud_boxes": len(stud_clouds),
        },
    )
    version = _package_version(binary)
    card = ran_card(
        algorithm_id="A3",
        algorithm=CLOUDCOMPARE["name"],
        rank=3,
        scene=record,
        sections=sections,
        implementation={
            "tool": "CloudCompare RANSAC Shape Detection",
            "package": version,
            "plugin": _plugin_file(),
            "primitives": list(chosen.primitives),
            "plugin_shapes": list(RANSAC_SHAPES),
            "cuboid_primitive": False,
            "merged_primitives_into_stud": True,
            "ransac_params": asdict(chosen),
            "knob_notes": knob_notes(chosen),
            "merge": merge_report,
            "attempt": {key: value for key, value in attempt.items() if key != "log_tail"},
            "log_tail": log,
        },
        implementation_short=(
            f"CloudCompare {version} RANSAC-SD, planes merged into one dressed-2x4 OBB. "
            f"epsilon {_fmt_num(chosen.epsilon_absolute_m)} m, "
            f"support {chosen.support_points}, "
            f"primitives {', '.join(chosen.primitives)}."
        ),
    )
    return card, detections


def _failure_reason(code: int, log: str, labeled: list[tuple[str, np.ndarray]]) -> str:
    tail = " ".join(log.split())[-500:]
    return (
        f"CloudCompare exited {code} and returned {len(labeled)} primitive clouds. "
        f"The stage 0 stud was written to PLY and passed to -RANSAC. "
        f"No stud metric was filled. Log tail: {tail}"
    )


def _version_from_executable(binary: str) -> str | None:
    """Read the about-dialog version baked into the CloudCompare binary.

    The Windows build stores ``2.14.beta (%1)`` next to the compile date.
    This does not launch the GUI.
    """
    try:
        data = Path(binary).read_bytes()
    except OSError:
        return None
    match = _ABOUT_VERSION.search(data)
    if match is None:
        return None
    version = match.group(1).decode("ascii")
    window = data[match.end() : match.end() + 80]
    dated = _BUILD_DATE.search(window)
    if dated is not None:
        return f"{version} ({dated.group(1).decode('ascii')})"
    return version


def _package_version(binary: str | None = None) -> str:
    dpkg = shutil.which("dpkg-query")
    if dpkg:
        proc = subprocess.run(
            [dpkg, "-W", "-f", "${Version}", "cloudcompare"],
            check=False,
            capture_output=True,
            text=True,
        )
        text = (proc.stdout or "").strip()
        if text:
            return text
    if binary:
        found = _version_from_executable(binary)
        if found:
            return found
    return "unknown"


def smoke_test() -> dict[str, Any]:
    """Launch CloudCompare once with ``-SILENT`` and record whether it exits.

    This does not fit a stud. A later ``run_one_stud`` call is the measurement.
    """
    binary, source = resolve_cloudcompare_binary()
    record: dict[str, Any] = {
        "ok": False,
        "binary": binary,
        "binary_source": source,
        "env": CLOUDCOMPARE_ENV,
        "default_windows_path": str(DEFAULT_WINDOWS_CLOUDCOMPARE),
        "version": _package_version(binary) if binary else None,
        "returncode": None,
        "plugin_seen": False,
        "processed_finished": False,
        "evidence_lines": [],
    }
    if binary is None:
        record["error"] = (
            "CloudCompare was not found via CLOUDCOMPARE_EXE, "
            f"{DEFAULT_WINDOWS_CLOUDCOMPARE}, or PATH."
        )
        return record
    command = [binary, "-SILENT", "-NO_TIMESTAMP"]
    record["command"] = command
    record["help_command"] = [binary, "-SILENT", "-NO_TIMESTAMP", "-HELP"]
    record["rejected_flag"] = "-H"
    proc = _run_cloudcompare(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=_process_env(),
        timeout=90,
        cwd=str(Path(binary).parent),
        **_subprocess_kwargs(),
    )
    log = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    evidence = [
        line.strip()
        for line in log.splitlines()
        if "RANSAC Shape Detection" in line or "Processed finished" in line
    ]
    record["returncode"] = proc.returncode
    record["plugin_seen"] = any("RANSAC Shape Detection" in line for line in evidence)
    record["processed_finished"] = "Processed finished" in log
    record["evidence_lines"] = evidence
    record["ok"] = proc.returncode == 0 and record["processed_finished"] and record["plugin_seen"]
    return record


def _write_ply(path: Path, points: np.ndarray) -> None:
    import open3d as o3d

    cloud = _point_cloud(points)
    ok = o3d.io.write_point_cloud(str(path), cloud, write_ascii=True)
    if not ok:
        raise RuntimeError(f"failed to write {path}")


def _load_primitive_clouds(out_dir: Path, source_ply: Path) -> list[tuple[str, np.ndarray]]:
    import open3d as o3d

    labeled: list[tuple[str, np.ndarray]] = []
    for path in sorted(out_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".ply", ".pcd", ".bin"}:
            continue
        if path.resolve() == source_ply.resolve():
            continue
        cloud = o3d.io.read_point_cloud(str(path))
        points = np.asarray(cloud.points)
        if len(points) >= 10:
            labeled.append((_primitive_kind(path), points))
    return labeled


def _primitive_kind(path: Path) -> str:
    match = _PRIMITIVE_KIND.search(path.stem)
    if match is None:
        return "UNKNOWN"
    return match.group(1).upper()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CloudCompare RANSAC-SD on the one synthetic stud, or a stub card.")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Launch CloudCompare -SILENT once and write cloudcompare_smoke.json.",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.smoke and args.stub:
        parser.error("--smoke and --stub cannot be combined")
    if args.smoke:
        dest = args.out or (repo_root() / "artifacts" / "scorecards" / "cloudcompare_smoke.json")
        record = smoke_test()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(
            f"CloudCompare smoke written to {dest}. "
            f"ok={record['ok']} source={record['binary_source']} version={record['version']}"
        )
        return 0 if record["ok"] else 1
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/cloudcompare_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"CloudCompare stub scorecard written to {path}. RANSAC-SD was not executed.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_cloudcompare.json")
    figure = args.figure or (
        repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "03-cloudcompare.png"
    )
    publish_attempt(
        algorithm="cloudcompare",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    print(
        f"CloudCompare one-stud scorecard written to {dest}. "
        f"status={card['status']} bars={card.get('stage0_pass_fail')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
