"""Shared post-step: stud points, tight minimal OBB, synthetic lean, paint.

Ranks differ in how they choose the points. The angle reference is the fitted
floor normal when the cloud has a floor or slab, and generator +Z only when
it does not. A SKIL or other level reading is not used. Epsilon stays
unlocked, so the production color is yellow. Numbers come from the clusters
passed in.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from openwall_stud.angle_reference import (
    GENERATOR_UP,
    REFERENCE_FLOOR,
    lock_synthetic_reference,
    scene_has_floor,
    synthetic_angle_note,
)
from openwall_stud.open3d_baseline import (
    BaselineRun,
    Detection,
    _angle_deg,
    _guess_nominal,
    _obb_segments,
    _point_cloud,
    peel_horizontal_slabs,
    score_run,
)
from openwall_stud.paint import hypothetical_placeholder, paint_stud
from openwall_stud.synthetic import Scene

# Stage 0 default. Floored scenes pass the fitted normal into the fitter.
REFERENCE = GENERATOR_UP.copy()
REFERENCE_NAME = "gravity_z_no_floor_plane"


def detections_from_clusters(
    clusters: list[np.ndarray],
    *,
    reference: np.ndarray | None = None,
) -> list[Detection]:
    """Fit one minimal OBB per cluster. The long axis is not forced to Z."""
    detections: list[Detection] = []
    for cluster_id, points in enumerate(clusters):
        if len(points) < 10:
            continue
        center, extent, rotation, segments = _obb_segments(_point_cloud(points))
        order = np.argsort(extent)
        extent_sorted = extent[order]
        long_axis = rotation[:, int(order[-1])]
        long_axis = long_axis / np.linalg.norm(long_axis)
        axis_ref = REFERENCE if reference is None else reference
        theta = _angle_deg(long_axis, axis_ref)
        production = paint_stud(theta, epsilon_locked=False)
        hypo = hypothetical_placeholder(theta)
        detections.append(
            Detection(
                cluster_id=cluster_id,
                n_points=int(len(points)),
                center_m=center,
                extent_sorted_m=extent_sorted,
                long_axis=long_axis,
                theta_deg=theta,
                nominal_guess=_guess_nominal(extent_sorted[:2]),
                segments_m=segments,
                production_color=production.color,
                hypothetical_color=hypo.color,
            )
        )
    detections.sort(key=lambda item: float(item.center_m[2]))
    return detections


def score_clusters(
    scene: Scene,
    clusters: list[np.ndarray],
    *,
    runtime_s: float,
    detection_note: str,
    geometry_note: str,
    angle_extra: str = "",
    cost: dict[str, Any],
) -> tuple[dict[str, Any], list[Detection]]:
    """Score clusters with the same matcher the Open3D baseline uses."""
    has_floor = scene_has_floor(scene)
    _, floor_normal, _ = peel_horizontal_slabs(scene.points_m)
    reference_name, reference_vec = lock_synthetic_reference(
        floor_normal,
        has_floor=has_floor,
    )
    detections = detections_from_clusters(clusters, reference=reference_vec)
    run = BaselineRun(
        scene_name=scene.name,
        stage=scene.stage,
        keep_mask=np.ones(scene.n_points, dtype=bool),
        cluster_labels=np.full(scene.n_points, -1, dtype=int),
        detections=detections,
        floor_found=reference_name == REFERENCE_FLOOR,
        floor_normal=reference_vec,
        reference=reference_name,
        runtime_s=runtime_s,
    )
    sections = score_run(scene, run)
    sections["detection"]["note"] = detection_note
    sections["geometry"]["note"] = geometry_note
    sections["angle"]["note"] = synthetic_angle_note(reference_name, extra=angle_extra)
    sections["cost"] = cost
    return sections, detections
