"""Synthetic stud scenes for the TruePlank curriculum, plus phase-1 S1.

Stage 0 is one dressed stud. Gravity in the generator is +Z. The stud long
axis is +Z before lean. Lean is a right-hand rotation about a named axis
through the base center. The historical default is +X, so the long-axis angle
from +Z equals the requested lean. Phase 1 S1 also allows −X, +Y, and −Y.
A zero lean is labeled axis ``none`` and is not rotated.

Stage 2 adds a floor slab in the same frame. Stage 3 is a 3–5 stud mini wall
(default 4) at 16 inch centers, with a bottom plate, a top plate, and a floor.
Plates are context for the peeler. They are not a QA class.

S1b is a bowed stud: ends stay on the chord, the midspan moves. It is not a
stage gate. Stage 5 is a synthetic room or bay with a LOT-62 look (a framed
bay you can walk). It is not the Polycam loft on the parallel corner track,
and it is not a real capture. Stages 6 and 7 are not generated here.

``full_room_28`` is the 28-stud train and experiment room: the same four-wall
layout with the south door left in place so all 28 centers stay. It does not
replace ``stage5_room_bay``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from openwall_stud.lumber import DRESSED_SECTION_M, OC_16_IN_M, STUD_LENGTH_8FT_M


LEAN_AXES = ("+X", "-X", "+Y", "-Y")
# Right-hand unit axes. +Z stays the stud long axis before the lean rotation.
_LEAN_AXIS_VECTORS = {
    "+X": np.array([1.0, 0.0, 0.0]),
    "-X": np.array([-1.0, 0.0, 0.0]),
    "+Y": np.array([0.0, 1.0, 0.0]),
    "-Y": np.array([0.0, -1.0, 0.0]),
}


@dataclass(frozen=True)
class StudTruth:
    stud_id: str
    nominal: str
    lean_deg: float
    length_m: float
    section_m: tuple[float, float]
    center_m: np.ndarray
    long_axis: np.ndarray
    lean_axis: str = "+X"
    # Midspan offset of a parabolic bow. Zero is a rigid stud. Ends stay on the chord.
    bow_m: float = 0.0


@dataclass
class Scene:
    name: str
    stage: int
    points_m: np.ndarray
    part: np.ndarray
    stud_slot: np.ndarray
    studs: list[StudTruth] = field(default_factory=list)
    seed: int = 0
    spacing_m: float = 0.005
    noise_std_m: float = 0.001
    description: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return int(self.points_m.shape[0])


def _face_grid(origin: np.ndarray, axis_u: np.ndarray, axis_v: np.ndarray, spacing: float) -> np.ndarray:
    len_u = float(np.linalg.norm(axis_u))
    len_v = float(np.linalg.norm(axis_v))
    nu = max(2, int(round(len_u / spacing)) + 1)
    nv = max(2, int(round(len_v / spacing)) + 1)
    u = np.linspace(0.0, 1.0, nu)
    v = np.linspace(0.0, 1.0, nv)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    return (
        origin
        + uu[..., None] * axis_u
        + vv[..., None] * axis_v
    ).reshape(-1, 3)


def _box_surface(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, spacing: float) -> np.ndarray:
    corners = {
        "x0y0z0": np.array([x0, y0, z0]),
        "x1y0z0": np.array([x1, y0, z0]),
        "x0y1z0": np.array([x0, y1, z0]),
        "x0y0z1": np.array([x0, y0, z1]),
    }
    spans = {
        "x": np.array([x1 - x0, 0.0, 0.0]),
        "y": np.array([0.0, y1 - y0, 0.0]),
        "z": np.array([0.0, 0.0, z1 - z0]),
    }
    faces = [
        _face_grid(corners["x0y0z0"], spans["x"], spans["y"], spacing),
        _face_grid(corners["x0y0z1"], spans["x"], spans["y"], spacing),
        _face_grid(corners["x0y0z0"], spans["x"], spans["z"], spacing),
        _face_grid(corners["x0y1z0"], spans["x"], spans["z"], spacing),
        _face_grid(corners["x0y0z0"], spans["y"], spans["z"], spacing),
        _face_grid(corners["x1y0z0"], spans["y"], spans["z"], spacing),
    ]
    stacked = np.vstack(faces)
    rounded = np.round(stacked, 4)
    _, index = np.unique(rounded, axis=0, return_index=True)
    return stacked[np.sort(index)]


def _yaw_about_z(yaw_deg: float) -> np.ndarray:
    """Right-hand rotation about +Z. Zero keeps the historical stud frame."""
    angle = np.deg2rad(yaw_deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    return np.array(
        [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )


def _apply_bow(local: np.ndarray, length_m: float, amplitude_m: float, bow_axis: str) -> np.ndarray:
    """Parabolic bow. z = 0 and z = length stay put. Midspan moves by ``amplitude_m``.

    The chord from the base center to the top center is unchanged, so a later
    lean still names that chord. This is not a second rigid rotation.
    """
    if amplitude_m == 0.0:
        return local
    if bow_axis not in {"X", "Y"}:
        raise ValueError("bow axis must be 'X' or 'Y'")
    if length_m <= 0.0:
        raise ValueError("length_m must be positive")
    out = np.array(local, dtype=float, copy=True)
    shape = 4.0 * (out[:, 2] / length_m) * (1.0 - out[:, 2] / length_m)
    column = 0 if bow_axis == "X" else 1
    out[:, column] = out[:, column] + float(amplitude_m) * shape
    return out


def _legacy_plus_x_rotation(lean_deg: float) -> np.ndarray:
    """The historical stage 0 matrix: right-hand rotation about +X."""
    angle = np.deg2rad(lean_deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    return np.array(
        [[1.0, 0.0, 0.0], [0.0, cosine, -sine], [0.0, sine, cosine]],
        dtype=float,
    )


def _lean_rotation(lean_deg: float, axis: str = "+X") -> np.ndarray:
    """Right-hand rotation by ``lean_deg`` about ``axis``.

    ``axis`` is one of ``+X``, ``-X``, ``+Y``, ``-Y``. The stud long axis
    before this rotation is +Z. ``+X`` matches ``_legacy_plus_x_rotation``.
    """
    if axis not in _LEAN_AXIS_VECTORS:
        raise ValueError(f"lean axis must be one of {LEAN_AXES}, got {axis!r}")
    angle = float(np.deg2rad(lean_deg))
    axis_u = _LEAN_AXIS_VECTORS[axis]
    skew = np.array(
        [
            [0.0, -axis_u[2], axis_u[1]],
            [axis_u[2], 0.0, -axis_u[0]],
            [-axis_u[1], axis_u[0], 0.0],
        ],
        dtype=float,
    )
    rotation = np.eye(3) + np.sin(angle) * skew + (1.0 - np.cos(angle)) * (skew @ skew)
    if axis == "+X":
        legacy = _legacy_plus_x_rotation(lean_deg)
        if not np.allclose(rotation, legacy, atol=1e-12):
            raise RuntimeError("+X lean rotation drifted from the historical matrix")
    return rotation


def _sample_stud(
    *,
    nominal: str,
    lean_deg: float,
    origin_xy: tuple[float, float],
    z_base: float,
    length_m: float,
    spacing_m: float,
    lean_axis: str = "+X",
    yaw_deg: float = 0.0,
    bow_m: float = 0.0,
    bow_axis: str = "Y",
) -> tuple[np.ndarray, StudTruth, str]:
    thickness, width = DRESSED_SECTION_M[nominal]
    local = _box_surface(
        -thickness / 2.0,
        thickness / 2.0,
        -width / 2.0,
        width / 2.0,
        0.0,
        length_m,
        spacing_m,
    )
    local = _apply_bow(local, length_m, bow_m, bow_axis)
    rotation = _lean_rotation(lean_deg, lean_axis)
    yaw = _yaw_about_z(yaw_deg)
    # Row-vector form of yaw @ rotation @ point. Yaw 0 and bow 0 match the
    # historical stage-0 cloud.
    world = local @ rotation.T @ yaw.T
    world[:, 0] += origin_xy[0]
    world[:, 1] += origin_xy[1]
    world[:, 2] += z_base
    axis = yaw @ (rotation @ np.array([0.0, 0.0, 1.0]))
    center = np.array([origin_xy[0], origin_xy[1], z_base]) + yaw @ (
        rotation @ np.array([0.0, 0.0, length_m / 2.0])
    )
    truth = StudTruth(
        stud_id="",
        nominal=nominal,
        lean_deg=float(lean_deg),
        length_m=float(length_m),
        section_m=(float(thickness), float(width)),
        center_m=center,
        long_axis=axis,
        lean_axis=lean_axis,
        bow_m=float(bow_m),
    )
    return world, truth, nominal


def _add_noise(points: np.ndarray, rng: np.random.Generator, noise_std_m: float) -> np.ndarray:
    if noise_std_m <= 0:
        return points
    return points + rng.normal(0.0, noise_std_m, size=points.shape)


def _floor_points(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    spacing_m: float,
) -> np.ndarray:
    xs = np.arange(x_min, x_max + spacing_m * 0.5, spacing_m)
    ys = np.arange(y_min, y_max + spacing_m * 0.5, spacing_m)
    xx, yy = np.meshgrid(xs, ys, indexing="ij")
    zz = np.zeros_like(xx)
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def _pack(
    *,
    name: str,
    stage: int,
    chunks: list[tuple[np.ndarray, int, int]],
    studs: list[StudTruth],
    seed: int,
    spacing_m: float,
    noise_std_m: float,
    description: str,
    rng: np.random.Generator,
    meta: dict | None = None,
) -> Scene:
    points = []
    parts = []
    slots = []
    for xyz, part, slot in chunks:
        noisy = _add_noise(xyz, rng, noise_std_m)
        points.append(noisy)
        parts.append(np.full(noisy.shape[0], part, dtype=np.int32))
        slots.append(np.full(noisy.shape[0], slot, dtype=np.int32))
    for index, stud in enumerate(studs, start=1):
        stud_id = f"S{index}"
        # dataclasses are frozen; rebuild with the id.
        studs[index - 1] = StudTruth(
            stud_id=stud_id,
            nominal=stud.nominal,
            lean_deg=stud.lean_deg,
            length_m=stud.length_m,
            section_m=stud.section_m,
            center_m=stud.center_m,
            long_axis=stud.long_axis,
            lean_axis=stud.lean_axis,
            bow_m=stud.bow_m,
        )
    return Scene(
        name=name,
        stage=stage,
        points_m=np.vstack(points),
        part=np.concatenate(parts),
        stud_slot=np.concatenate(slots),
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=description,
        meta=dict(meta or {}),
    )


def phase1_s1_scene_name(lean_deg: float, axis: str) -> str:
    """Scene id for one phase-1 S1 cloud.

    Zero lean is ``s1_2x4_lean0.000_axnone``. A non-zero lean encodes the
    absolute magnitude and the rotation axis, for example
    ``s1_2x4_lean0.050_ax+X``.
    """
    magnitude = abs(float(lean_deg))
    if magnitude == 0.0:
        if axis != "none":
            raise ValueError("a zero lean uses axis 'none'")
        return "s1_2x4_lean0.000_axnone"
    if axis not in LEAN_AXES:
        raise ValueError(f"lean axis must be one of {LEAN_AXES}, got {axis!r}")
    return f"s1_2x4_lean{magnitude:.3f}_ax{axis}"


def phase1_s1_single_stud(
    *,
    lean_deg: float,
    axis: str,
    seed: int = 2,
    spacing_m: float = 0.005,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    nominal: str = "2x4",
) -> Scene:
    """One dressed stud for phase-1 S1. No floor. The cloud is not rotated onto a plane.

    ``lean_deg`` is the magnitude. ``axis`` is ``none`` at 0°, otherwise
    ``+X``, ``-X``, ``+Y``, or ``-Y``. The long axis is +Z before that
    right-hand rotation. Gravity in the generator stays +Z.
    """
    if nominal not in DRESSED_SECTION_M:
        raise ValueError(f"nominal must be one of {sorted(DRESSED_SECTION_M)}")
    magnitude = abs(float(lean_deg))
    name = phase1_s1_scene_name(magnitude, axis)
    # Axis ``none`` is the zero-lean label. The rotation itself is the identity
    # about +X, then the stored label is set back to ``none``.
    rotation_axis = "+X" if axis == "none" else axis
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=magnitude,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
        lean_axis=rotation_axis,
    )
    if axis == "none":
        truth = StudTruth(
            stud_id=truth.stud_id,
            nominal=truth.nominal,
            lean_deg=0.0,
            length_m=truth.length_m,
            section_m=truth.section_m,
            center_m=truth.center_m,
            long_axis=truth.long_axis,
            lean_axis="none",
        )
        description = (
            "Phase 1 S1 synthetic dressed stud. Lean 0, axis none. "
            "Generator gravity is +Z. No floor. The cloud is not rotated."
        )
    else:
        description = (
            f"Phase 1 S1 synthetic dressed stud. Lean {magnitude:.3f} deg about {axis}. "
            "Long axis is +Z before the right-hand rotation. "
            "Generator gravity is +Z. No floor. The cloud is not rotated."
        )
    return _pack(
        name=name,
        stage=0,
        chunks=[(points, 2, 0)],
        studs=[truth],
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=description,
        rng=rng,
    )


def stage0_single_stud(
    *,
    nominal: str = "2x4",
    lean_deg: float = 0.0,
    seed: int = 0,
    spacing_m: float = 0.005,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    lean_axis: str = "+X",
) -> Scene:
    """One stud standing on z = 0. No floor and no plate.

    ``lean_axis`` defaults to ``+X``, and that default keeps the historical
    scene name. Any other axis is appended so the name encodes the rotation.
    """
    if nominal not in DRESSED_SECTION_M:
        raise ValueError(f"nominal must be one of {sorted(DRESSED_SECTION_M)}")
    if lean_axis not in LEAN_AXES:
        raise ValueError(f"lean axis must be one of {LEAN_AXES}, got {lean_axis!r}")
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=lean_deg,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
        lean_axis=lean_axis,
    )
    name = f"stage0_{nominal}_lean{lean_deg:.3f}"
    if lean_axis != "+X":
        name = f"{name}_ax{lean_axis}"
    return _pack(
        name=name,
        stage=0,
        chunks=[(points, 2, 0)],
        studs=[truth],
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description="Synthetic single stud. Generator gravity is +Z.",
        rng=rng,
    )


def stage2_stud_and_floor(
    *,
    nominal: str = "2x4",
    lean_deg: float = 0.0,
    seed: int = 0,
    spacing_m: float = 0.005,
    floor_spacing_m: float = 0.01,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    lean_axis: str = "+X",
) -> Scene:
    """One stud plus a horizontal floor slab at z = 0.

    ``lean_axis`` defaults to ``+X``. That default keeps the historical scene
    name. Any other axis is appended so the name encodes the rotation.
    """
    if lean_axis not in LEAN_AXES:
        raise ValueError(f"lean axis must be one of {LEAN_AXES}, got {lean_axis!r}")
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=lean_deg,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
        lean_axis=lean_axis,
    )
    floor = _floor_points(-0.7, 0.7, -0.7, 0.7, floor_spacing_m)
    name = f"stage2_{nominal}_lean{lean_deg:.3f}"
    if lean_axis != "+X":
        name = f"{name}_ax{lean_axis}"
    return _pack(
        name=name,
        stage=2,
        chunks=[(floor, 0, -1), (points, 2, 0)],
        studs=[truth],
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            "Synthetic stud on a floor slab. Lean is measured against the fitted floor normal. "
            "The cloud is not rotated. The floor normal is not a gravity or level reading."
        ),
        rng=rng,
    )


def stage3_mini_wall(
    *,
    n_studs: int = 4,
    leans_deg: tuple[float, ...] | None = None,
    nominal: str = "2x4",
    seed: int = 0,
    spacing_m: float = 0.005,
    floor_spacing_m: float = 0.012,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    scene_name: str | None = None,
) -> Scene:
    """Mini wall: 3–5 studs, bottom plate, top plate, and a floor. Little noise."""
    if not 3 <= n_studs <= 5:
        raise ValueError("stage 3 mini wall is 3 to 5 studs")
    if leans_deg is None:
        leans_deg = (0.0, 0.30, 0.80, 1.50, 0.15)[:n_studs]
    if len(leans_deg) != n_studs:
        raise ValueError("leans_deg must have one value per stud")
    rng = np.random.default_rng(seed)
    thickness, width = DRESSED_SECTION_M[nominal]
    plate_h = thickness  # a plate standing on its 1.5 in face
    chunks: list[tuple[np.ndarray, int, int]] = []
    studs: list[StudTruth] = []
    x_centers = [index * OC_16_IN_M for index in range(n_studs)]
    x_min = x_centers[0] - thickness / 2.0 - 0.02
    x_max = x_centers[-1] + thickness / 2.0 + 0.02
    y_min, y_max = -width / 2.0, width / 2.0
    bottom = _box_surface(x_min, x_max, y_min, y_max, 0.0, plate_h, spacing_m)
    top_z = plate_h + length_m
    top = _box_surface(x_min, x_max, y_min, y_max, top_z, top_z + plate_h, spacing_m)
    floor = _floor_points(x_min - 0.35, x_max + 0.35, -0.45, 0.45, floor_spacing_m)
    chunks.append((floor, 0, -1))
    chunks.append((bottom, 1, -1))
    chunks.append((top, 1, -1))
    for slot, (x_center, lean) in enumerate(zip(x_centers, leans_deg)):
        points, truth, _ = _sample_stud(
            nominal=nominal,
            lean_deg=lean,
            origin_xy=(x_center, 0.0),
            z_base=plate_h,
            length_m=length_m,
            spacing_m=spacing_m,
        )
        chunks.append((points, 2, slot))
        studs.append(truth)
    lean_text = ", ".join(f"{value:.3f}" for value in leans_deg)
    return _pack(
        name=scene_name or f"stage3_mini_wall_{n_studs}",
        stage=3,
        chunks=chunks,
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            f"Synthetic mini wall, {n_studs} {nominal} studs at 16 inch centers, "
            f"leans {lean_text} deg about +X, bottom and top plates, floor slab, "
            f"{noise_std_m * 1000:.1f} mm noise. First product-shaped scene."
        ),
        rng=rng,
    )


def _section_aabb_xy(
    center_xy: tuple[float, float],
    yaw_deg: float,
    thickness: float,
    width: float,
    inflate_m: float = 0.0,
) -> tuple[float, float, float, float]:
    """Axis-aligned plan box of the stud section, optionally inflated by a lean tip."""
    corners = np.array(
        [
            [-thickness / 2.0, -width / 2.0],
            [-thickness / 2.0, width / 2.0],
            [thickness / 2.0, -width / 2.0],
            [thickness / 2.0, width / 2.0],
        ],
        dtype=float,
    )
    angle = np.deg2rad(yaw_deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    rotation = np.array([[cosine, -sine], [sine, cosine]], dtype=float)
    world = corners @ rotation.T
    world[:, 0] += center_xy[0]
    world[:, 1] += center_xy[1]
    pad = float(inflate_m)
    return (
        float(world[:, 0].min()) - pad,
        float(world[:, 0].max()) + pad,
        float(world[:, 1].min()) - pad,
        float(world[:, 1].max()) + pad,
    )


def _plan_gap_m(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    """Separation of two plan AABBs. Zero means they overlap."""
    dx = max(0.0, first[0] - second[1], second[0] - first[1])
    dy = max(0.0, first[2] - second[3], second[2] - first[3])
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return float(np.hypot(dx, dy))


def s1b_bowed_stud(
    *,
    bow_m: float,
    lean_deg: float = 0.0,
    lean_axis: str = "+X",
    bow_axis: str = "Y",
    nominal: str = "2x4",
    seed: int = 40,
    spacing_m: float = 0.005,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
) -> Scene:
    """One dressed stud with a parabolic bow. Ends stay on the chord. No floor.

    S1b is a class of scene, not a curriculum stage gate. The stored long axis
    is the chord. A straight oriented box is not a bow measurement.
    """
    if bow_m <= 0.0:
        raise ValueError("s1b bow amplitude must be positive")
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=lean_deg,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
        lean_axis=lean_axis,
        bow_m=bow_m,
        bow_axis=bow_axis,
    )
    # Ends of the chord are the unbowed base and top. A sample at z=0 and z=L
    # in the local frame is not shifted before the lean.
    name = f"s1b_bow_{nominal}_amp{bow_m * 1000:.2f}mm_lean{lean_deg:.3f}"
    return _pack(
        name=name,
        stage=0,
        chunks=[(points, 2, 0)],
        studs=[truth],
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            f"S1b synthetic bowed {nominal}. Midspan bow {bow_m * 1000:.2f} mm along local {bow_axis}. "
            f"Chord lean {lean_deg:.3f} deg about {lean_axis}. Ends held. No floor. "
            "Not a stage-0 gate and not a field bow."
        ),
        rng=rng,
        meta={
            "curriculum_class": "S1b",
            "bow_m": float(bow_m),
            "bow_axis": bow_axis,
            "chord_is_long_axis": True,
            "stage_gate": False,
        },
    )


def s1b_bow_wall(
    *,
    n_studs: int = 3,
    bow_slot: int = 1,
    bow_m: float = 0.00635,
    leans_deg: tuple[float, ...] | None = None,
    nominal: str = "2x4",
    seed: int = 41,
    spacing_m: float = 0.005,
    floor_spacing_m: float = 0.012,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
) -> Scene:
    """Mini wall with one bowed stud. Other studs are rigid. Plates and a floor stay."""
    if not 3 <= n_studs <= 5:
        raise ValueError("S1b bow wall is 3 to 5 studs")
    if not 0 <= bow_slot < n_studs:
        raise ValueError("bow_slot is out of range")
    if leans_deg is None:
        leans_deg = tuple(0.0 for _ in range(n_studs))
    if len(leans_deg) != n_studs:
        raise ValueError("leans_deg must have one value per stud")
    rng = np.random.default_rng(seed)
    thickness, width = DRESSED_SECTION_M[nominal]
    plate_h = thickness
    chunks: list[tuple[np.ndarray, int, int]] = []
    studs: list[StudTruth] = []
    x_centers = [index * OC_16_IN_M for index in range(n_studs)]
    x_min = x_centers[0] - thickness / 2.0 - 0.02
    x_max = x_centers[-1] + thickness / 2.0 + 0.02
    y_min, y_max = -width / 2.0, width / 2.0
    bottom = _box_surface(x_min, x_max, y_min, y_max, 0.0, plate_h, spacing_m)
    top_z = plate_h + length_m
    top = _box_surface(x_min, x_max, y_min, y_max, top_z, top_z + plate_h, spacing_m)
    floor = _floor_points(x_min - 0.35, x_max + 0.35, -0.45, 0.45, floor_spacing_m)
    chunks.append((floor, 0, -1))
    chunks.append((bottom, 1, -1))
    chunks.append((top, 1, -1))
    for slot, (x_center, lean) in enumerate(zip(x_centers, leans_deg)):
        amplitude = bow_m if slot == bow_slot else 0.0
        points, truth, _ = _sample_stud(
            nominal=nominal,
            lean_deg=lean,
            origin_xy=(x_center, 0.0),
            z_base=plate_h,
            length_m=length_m,
            spacing_m=spacing_m,
            bow_m=amplitude,
            bow_axis="Y",
        )
        chunks.append((points, 2, slot))
        studs.append(truth)
    return _pack(
        name=f"s1b_bow_wall_{n_studs}",
        stage=3,
        chunks=chunks,
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            f"S1b synthetic wall, {n_studs} {nominal} studs. Stud slot {bow_slot} bows "
            f"{bow_m * 1000:.2f} mm at midspan along local Y. Ends held. "
            "Plates and floor are context. Not a stage-3 gate."
        ),
        rng=rng,
        meta={
            "curriculum_class": "S1b",
            "bow_m": float(bow_m),
            "bow_slot": int(bow_slot),
            "bow_axis": "Y",
            "stage_gate": False,
        },
    )


def stage5_room_bay(
    *,
    nominal: str = "2x4",
    seed: int = 62,
    spacing_m: float = 0.006,
    plate_spacing_m: float = 0.01,
    floor_spacing_m: float = 0.02,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    corner_gap_m: float = 0.10,
) -> Scene:
    """Synthetic room or bay with a LOT-62 look: one framed bay you can walk.

    Four stud walls at 16 inch centers, bottom and top plates, and a floor.
    One wall has a door-width gap and no studs in that span. A header is not
    generated: rank 1 peels a global Z slab, and a header band would slice
    every stud in the room.

    Corner studs do not touch. ``corner_gap_m`` is clear air between section
    boxes after a lean-tip inflation, and it stays above the rank-1 DBSCAN
    ``eps`` of 25 mm. A real corner is tight. This generator does not claim
    that joint.

    This cloud is not the Lot 62 Polycam capture. That field file stays on the
    parallel corner track (PRs #23 and #24). Stages 6 and 7 are not this scene.
    """
    if nominal not in DRESSED_SECTION_M:
        raise ValueError(f"nominal must be one of {sorted(DRESSED_SECTION_M)}")
    if corner_gap_m < 0.05:
        raise ValueError("corner gap must stay above the 25 mm DBSCAN eps with margin")
    thickness, width = DRESSED_SECTION_M[nominal]
    plate_h = thickness
    rng = np.random.default_rng(seed)
    # Seven centers span 6 * 16 in = 8 ft along each wall line.
    n_along = 7
    along = [index * OC_16_IN_M for index in range(n_along)]
    x_w = -thickness / 2.0 - corner_gap_m - width / 2.0
    y0 = width / 2.0 + corner_gap_m + thickness / 2.0
    y_along = [y0 + index * OC_16_IN_M for index in range(n_along)]
    y_n = y_along[-1] + thickness / 2.0 + corner_gap_m + width / 2.0
    x_e = along[-1] + thickness / 2.0 + corner_gap_m + width / 2.0
    # Door on the south wall removes two studs. No header. See the docstring.
    door_lo, door_hi = 0.60, 1.55

    # (origin_xy, yaw_deg, lean_deg, keep)
    placements: list[tuple[tuple[float, float], float, float]] = []
    south_leans = (0.20, 0.0, 0.0, 0.0, 0.0, 0.12, 0.0)
    for x_center, lean in zip(along, south_leans):
        if door_lo < x_center < door_hi:
            continue
        placements.append(((x_center, 0.0), 0.0, lean))
    west_leans = (0.0, 0.0, 0.12, 0.0, 0.0, 0.0, 0.30)
    for y_center, lean in zip(y_along, west_leans):
        placements.append(((x_w, y_center), 90.0, lean))
    north_leans = (0.0, 0.30, 0.0, 0.0, 0.0, 0.0, 0.0)
    for x_center, lean in zip(along, north_leans):
        placements.append(((x_center, y_n), 0.0, lean))
    east_leans = (0.0, 0.0, 0.0, 0.0, 0.30, 0.0, 0.0)
    for y_center, lean in zip(y_along, east_leans):
        placements.append(((x_e, y_center), 90.0, lean))

    boxes = []
    for origin_xy, yaw_deg, lean in placements:
        tip = float(length_m * np.tan(np.deg2rad(abs(lean))))
        boxes.append(_section_aabb_xy(origin_xy, yaw_deg, thickness, width, inflate_m=tip))
    min_gap = None
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            gap = _plan_gap_m(boxes[i], boxes[j])
            min_gap = gap if min_gap is None else min(min_gap, gap)
    if min_gap is None or min_gap < 0.04:
        raise RuntimeError(f"stage 5 studs are closer than 40 mm after lean inflation: {min_gap}")

    chunks: list[tuple[np.ndarray, int, int]] = []
    studs: list[StudTruth] = []
    floor = _floor_points(x_w - 0.40, x_e + 0.40, -0.40, y_n + 0.40, floor_spacing_m)
    chunks.append((floor, 0, -1))

    def _plate(x0: float, x1: float, y0p: float, y1p: float, z0: float, z1: float) -> np.ndarray:
        return _box_surface(x0, x1, y0p, y1p, z0, z1, plate_spacing_m)

    top_z = plate_h + length_m
    plate_spans = [
        (along[0] - thickness / 2.0, along[-1] + thickness / 2.0, -width / 2.0, width / 2.0),
        (x_w - width / 2.0, x_w + width / 2.0, y_along[0] - thickness / 2.0, y_along[-1] + thickness / 2.0),
        (along[0] - thickness / 2.0, along[-1] + thickness / 2.0, y_n - width / 2.0, y_n + width / 2.0),
        (x_e - width / 2.0, x_e + width / 2.0, y_along[0] - thickness / 2.0, y_along[-1] + thickness / 2.0),
    ]
    for x0, x1, y0p, y1p in plate_spans:
        chunks.append((_plate(x0, x1, y0p, y1p, 0.0, plate_h), 1, -1))
        chunks.append((_plate(x0, x1, y0p, y1p, top_z, top_z + plate_h), 1, -1))

    for slot, (origin_xy, yaw_deg, lean) in enumerate(placements):
        points, truth, _ = _sample_stud(
            nominal=nominal,
            lean_deg=lean,
            origin_xy=origin_xy,
            z_base=plate_h,
            length_m=length_m,
            spacing_m=spacing_m,
            yaw_deg=yaw_deg,
        )
        chunks.append((points, 2, slot))
        studs.append(truth)

    south_kept = sum(1 for item in placements if item[1] == 0.0 and item[0][1] == 0.0)
    return _pack(
        name="stage5_room_bay_lot62_look",
        stage=5,
        chunks=chunks,
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            "Synthetic room or bay with a LOT-62 look: four stud walls, 16 inch centers, "
            f"corner air gap {corner_gap_m:.2f} m, door gap on the south wall "
            f"({south_kept} south studs kept), plates and floor, no header. "
            "Not the Lot 62 Polycam file. Not a real capture. Not stages 6 or 7."
        ),
        rng=rng,
        meta={
            "curriculum_class": "stage5_synthetic_room",
            "look": "LOT-62 framed bay you can walk",
            "not_the_polycam_loft": True,
            "parallel_corner_prs": [23, 24],
            "corner_gap_m": float(corner_gap_m),
            "min_plan_gap_after_lean_tip_m": None if min_gap is None else float(min_gap),
            "header": "omitted; a global Z peel would slice every stud",
            "door_x_m": [door_lo, door_hi],
            "n_studs": len(placements),
            "stud_spacing_m": float(spacing_m),
            "plate_spacing_m": float(plate_spacing_m),
            "floor_spacing_m": float(floor_spacing_m),
            "training_gate": False,
            "stage_gate": False,
        },
    )


FULL_ROOM_N_ALONG = 7
FULL_ROOM_N_STUDS = FULL_ROOM_N_ALONG * 4


def full_room_28(
    *,
    leans_deg: tuple[float, ...] | list[float],
    lean_axes: tuple[str, ...] | list[str],
    nominal: str = "2x4",
    seed: int = 1101,
    spacing_m: float = 0.006,
    plate_spacing_m: float = 0.01,
    floor_spacing_m: float = 0.02,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
    corner_gap_m: float = 0.10,
    name: str | None = None,
) -> Scene:
    """Four walls, seven studs each, plates, and a floor. Exactly 28 studs.

    Wall order is south, west, north, east. ``stage5_room_bay`` uses this
    plan and then drops two south studs for a door. This function keeps every
    center. Corner air gap and the 40 mm plan-gap check match that bay.
    ``lean_axes`` entries are ``+X``, ``-X``, ``+Y``, ``-Y``, or ``none``
    (a zero lean is stored as ``none`` and is not rotated).
    """
    if nominal not in DRESSED_SECTION_M:
        raise ValueError(f"nominal must be one of {sorted(DRESSED_SECTION_M)}")
    if corner_gap_m < 0.05:
        raise ValueError("corner gap must stay above the 25 mm DBSCAN eps with margin")
    leans = [float(value) for value in leans_deg]
    axes = [str(value) for value in lean_axes]
    if len(leans) != FULL_ROOM_N_STUDS or len(axes) != FULL_ROOM_N_STUDS:
        raise ValueError(f"full_room_28 wants {FULL_ROOM_N_STUDS} leans and axes")
    for axis, lean in zip(axes, leans):
        if lean == 0.0:
            if axis != "none":
                raise ValueError("a 0° stud uses lean axis 'none'")
        elif axis not in LEAN_AXES:
            raise ValueError(f"lean axis must be one of {LEAN_AXES} or 'none', got {axis!r}")
    thickness, width = DRESSED_SECTION_M[nominal]
    plate_h = thickness
    rng = np.random.default_rng(seed)
    along = [index * OC_16_IN_M for index in range(FULL_ROOM_N_ALONG)]
    x_w = -thickness / 2.0 - corner_gap_m - width / 2.0
    y0 = width / 2.0 + corner_gap_m + thickness / 2.0
    y_along = [y0 + index * OC_16_IN_M for index in range(FULL_ROOM_N_ALONG)]
    y_n = y_along[-1] + thickness / 2.0 + corner_gap_m + width / 2.0
    x_e = along[-1] + thickness / 2.0 + corner_gap_m + width / 2.0
    walls: list[tuple[tuple[float, float], float]] = []
    for x_center in along:
        walls.append(((x_center, 0.0), 0.0))
    for y_center in y_along:
        walls.append(((x_w, y_center), 90.0))
    for x_center in along:
        walls.append(((x_center, y_n), 0.0))
    for y_center in y_along:
        walls.append(((x_e, y_center), 90.0))
    if len(walls) != FULL_ROOM_N_STUDS:
        raise RuntimeError(f"full room layout is {len(walls)} studs, want {FULL_ROOM_N_STUDS}")

    boxes = []
    for (origin_xy, yaw_deg), lean in zip(walls, leans):
        tip = float(length_m * np.tan(np.deg2rad(abs(lean))))
        boxes.append(_section_aabb_xy(origin_xy, yaw_deg, thickness, width, inflate_m=tip))
    min_gap = None
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            gap = _plan_gap_m(boxes[i], boxes[j])
            min_gap = gap if min_gap is None else min(min_gap, gap)
    if min_gap is None or min_gap < 0.04:
        raise RuntimeError(f"full-room studs are closer than 40 mm after lean inflation: {min_gap}")

    chunks: list[tuple[np.ndarray, int, int]] = []
    studs: list[StudTruth] = []
    floor = _floor_points(x_w - 0.40, x_e + 0.40, -0.40, y_n + 0.40, floor_spacing_m)
    chunks.append((floor, 0, -1))

    def _plate(x0: float, x1: float, y0p: float, y1p: float, z0: float, z1: float) -> np.ndarray:
        return _box_surface(x0, x1, y0p, y1p, z0, z1, plate_spacing_m)

    top_z = plate_h + length_m
    plate_spans = [
        (along[0] - thickness / 2.0, along[-1] + thickness / 2.0, -width / 2.0, width / 2.0),
        (x_w - width / 2.0, x_w + width / 2.0, y_along[0] - thickness / 2.0, y_along[-1] + thickness / 2.0),
        (along[0] - thickness / 2.0, along[-1] + thickness / 2.0, y_n - width / 2.0, y_n + width / 2.0),
        (x_e - width / 2.0, x_e + width / 2.0, y_along[0] - thickness / 2.0, y_along[-1] + thickness / 2.0),
    ]
    for x0, x1, y0p, y1p in plate_spans:
        chunks.append((_plate(x0, x1, y0p, y1p, 0.0, plate_h), 1, -1))
        chunks.append((_plate(x0, x1, y0p, y1p, top_z, top_z + plate_h), 1, -1))

    for slot, ((origin_xy, yaw_deg), lean, axis) in enumerate(zip(walls, leans, axes)):
        sample_axis = "+X" if axis == "none" else axis
        points, truth, _ = _sample_stud(
            nominal=nominal,
            lean_deg=lean,
            origin_xy=origin_xy,
            z_base=plate_h,
            length_m=length_m,
            spacing_m=spacing_m,
            lean_axis=sample_axis,
            yaw_deg=yaw_deg,
        )
        if axis == "none":
            truth = StudTruth(
                stud_id=truth.stud_id,
                nominal=truth.nominal,
                lean_deg=truth.lean_deg,
                length_m=truth.length_m,
                section_m=truth.section_m,
                center_m=truth.center_m,
                long_axis=truth.long_axis,
                lean_axis="none",
                bow_m=truth.bow_m,
            )
        chunks.append((points, 2, slot))
        studs.append(truth)

    return _pack(
        name=name or f"fullroom_28_seed{seed}",
        stage=5,
        chunks=chunks,
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            "Synthetic four-wall room, 28 dressed 2x4 studs at 16 inch centers, "
            f"corner air gap {corner_gap_m:.2f} m, plates and floor, no door, no header. "
            "Train and full-room experiment generator. Not stage5_room_bay."
        ),
        rng=rng,
        meta={
            "curriculum_class": "fullroom_28",
            "n_studs": FULL_ROOM_N_STUDS,
            "wall_order": ["south", "west", "north", "east"],
            "studs_per_wall": FULL_ROOM_N_ALONG,
            "corner_gap_m": float(corner_gap_m),
            "min_plan_gap_after_lean_tip_m": float(min_gap),
            "header": "omitted",
            "door": "omitted so the stud count stays 28",
            "leans_deg": leans,
            "lean_axes": axes,
            "stud_spacing_m": float(spacing_m),
            "plate_spacing_m": float(plate_spacing_m),
            "floor_spacing_m": float(floor_spacing_m),
            "training_gate": True,
            "stage_gate": False,
        },
    )
