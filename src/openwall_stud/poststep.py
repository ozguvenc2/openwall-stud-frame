"""Shared post-step: stud points, tight minimal OBB, angle versus +Z, paint.

Ranks differ in how they choose the points. Epsilon stays unlocked, so the
production color is yellow. Numbers come from the clusters passed in.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from openwall_stud.open3d_baseline import (
    BaselineRun,
    Detection,
    _angle_deg,
    _guess_nominal,
    _obb_segments,
    _point_cloud,
    score_run,
)
from openwall_stud.paint import hypothetical_placeholder, paint_stud
from openwall_stud.synthetic import Scene

REFERENCE = np.array([0.0, 0.0, 1.0])
REFERENCE_NAME = "gravity_z_no_floor_plane"


def detections_from_clusters(clusters: list[np.ndarray]) -> list[Detection]:
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
        theta = _angle_deg(long_axis, REFERENCE)
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
    angle_note: str,
    cost: dict[str, Any],
) -> tuple[dict[str, Any], list[Detection]]:
    """Score clusters with the same matcher the Open3D baseline uses."""
    detections = detections_from_clusters(clusters)
    run = BaselineRun(
        scene_name=scene.name,
        stage=scene.stage,
        keep_mask=np.ones(scene.n_points, dtype=bool),
        cluster_labels=np.full(scene.n_points, -1, dtype=int),
        detections=detections,
        floor_found=False,
        floor_normal=REFERENCE.copy(),
        reference=REFERENCE_NAME,
        runtime_s=runtime_s,
    )
    sections = score_run(scene, run)
    sections["detection"]["note"] = detection_note
    sections["geometry"]["note"] = geometry_note
    sections["angle"]["note"] = angle_note
    sections["cost"] = cost
    return sections, detections
