"""Synthetic stud scenes for curriculum stages 0, 2, and 3.

Stage 0 is one dressed stud. Gravity in the generator is +Z. Lean is a
rotation about +X through the base center, so the long-axis angle from +Z
equals the requested lean.

Stage 2 adds a floor slab in the same frame. Stage 3 is a 3–5 stud mini wall
(default 4) at 16 inch centers, with a bottom plate, a top plate, and a floor.
Plates are context for the peeler. They are not a QA class.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from openwall_stud.lumber import DRESSED_SECTION_M, OC_16_IN_M, STUD_LENGTH_8FT_M


@dataclass(frozen=True)
class StudTruth:
    stud_id: str
    nominal: str
    lean_deg: float
    length_m: float
    section_m: tuple[float, float]
    center_m: np.ndarray
    long_axis: np.ndarray


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


def _lean_rotation(lean_deg: float) -> np.ndarray:
    angle = np.deg2rad(lean_deg)
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))
    return np.array(
        [[1.0, 0.0, 0.0], [0.0, cosine, -sine], [0.0, sine, cosine]],
        dtype=float,
    )


def _sample_stud(
    *,
    nominal: str,
    lean_deg: float,
    origin_xy: tuple[float, float],
    z_base: float,
    length_m: float,
    spacing_m: float,
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
    rotation = _lean_rotation(lean_deg)
    world = local @ rotation.T
    world[:, 0] += origin_xy[0]
    world[:, 1] += origin_xy[1]
    world[:, 2] += z_base
    axis = rotation @ np.array([0.0, 0.0, 1.0])
    center = np.array([origin_xy[0], origin_xy[1], z_base]) + rotation @ np.array([0.0, 0.0, length_m / 2.0])
    truth = StudTruth(
        stud_id="",
        nominal=nominal,
        lean_deg=float(lean_deg),
        length_m=float(length_m),
        section_m=(float(thickness), float(width)),
        center_m=center,
        long_axis=axis,
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
    )


def stage0_single_stud(
    *,
    nominal: str = "2x4",
    lean_deg: float = 0.0,
    seed: int = 0,
    spacing_m: float = 0.005,
    noise_std_m: float = 0.001,
    length_m: float = STUD_LENGTH_8FT_M,
) -> Scene:
    """One stud standing on z = 0. No floor and no plate."""
    if nominal not in DRESSED_SECTION_M:
        raise ValueError(f"nominal must be one of {sorted(DRESSED_SECTION_M)}")
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=lean_deg,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
    )
    return _pack(
        name=f"stage0_{nominal}_lean{lean_deg:.3f}",
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
) -> Scene:
    """One stud plus a horizontal floor slab at z = 0."""
    rng = np.random.default_rng(seed)
    points, truth, _ = _sample_stud(
        nominal=nominal,
        lean_deg=lean_deg,
        origin_xy=(0.0, 0.0),
        z_base=0.0,
        length_m=length_m,
        spacing_m=spacing_m,
    )
    floor = _floor_points(-0.7, 0.7, -0.7, 0.7, floor_spacing_m)
    return _pack(
        name=f"stage2_{nominal}_lean{lean_deg:.3f}",
        stage=2,
        chunks=[(floor, 0, -1), (points, 2, 0)],
        studs=[truth],
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description="Synthetic stud on a floor slab. Floor is context to remove, not the plumb reference for a later gravity call.",
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
    return _pack(
        name=f"stage3_mini_wall_{n_studs}",
        stage=3,
        chunks=chunks,
        studs=studs,
        seed=seed,
        spacing_m=spacing_m,
        noise_std_m=noise_std_m,
        description=(
            f"Synthetic mini wall, {n_studs} {nominal} studs at 16 inch centers, "
            "bottom and top plates, floor slab, 1 mm noise. First product-shaped scene."
        ),
        rng=rng,
    )
