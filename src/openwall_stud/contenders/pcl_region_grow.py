"""PCL region-grow, then a cuboid, on the one Stage 0 stud.

Install
    The scored path links Ubuntu ``libpcl-segmentation1.14`` (PCL 1.14, BSD)
    through ``tools/pcl_region_grow.cpp``. Headers may be taken from the
    ``libpcl-dev`` deb without installing the VTK development stack.
    ``tools/build_pcl_region_grow.sh`` builds ``artifacts/bin/pcl_region_grow``.

    If that binary cannot be built, the same smoothness test runs in-process
    and the scorecard says so. Metrics then belong to that port, not to libpcl.

Entrypoint
    python -m openwall_stud.contenders.pcl_region_grow

    That loads the one synthetic 2x4 at 0.05 degree lean (seed 2) and writes
    ``artifacts/scorecards/one_stud_pcl.json``. ``--stub`` writes the old null
    card and does not segment.

Do not
    Do not port Bassier's remote coplanar merge.
    Do not force the cuboid axis to global Z.
    Do not copy Özkan's roof-beam percentages into this scorecard.

Citations
    Özkan et al. 2022, https://doi.org/10.3390/jimaging8010010
    PCL RegionGrowing, https://pointclouds.org/documentation/classpcl_1_1_region_growing.html
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from openwall_stud.contenders.common import blocked_card, emit_stub, ran_card, stub_card
from openwall_stud.one_stud import make_scene, scene_record
from openwall_stud.results_by_day import repo_root
from openwall_stud.synthetic import Scene

PCL = {
    "rank": 2,
    "algorithm_id": "A2",
    "status": "stub",
    "name": "PCL region-grow + cuboid (Ozkan/Pochtrager, no Bassier merge)",
}


def build_stub_card() -> dict:
    return stub_card(
        algorithm_id="A2",
        algorithm=PCL["name"],
        rank=2,
        license_name="BSD",
        hardware="CPU",
        failure_modes=[
            "PCL is not installed in this environment, so no cloud was segmented.",
            "Remote coplanar merge (Bassier) would glue studs in one wall plane.",
            "Forcing the cuboid axis to Z would hide lean.",
            "A region-grow smoothness threshold that is too loose merges a stud into a plate.",
        ],
        note="Stub only. PCL was not executed. Detection, geometry, and angle are null.",
    )


def build_card() -> dict:
    """Backward-compatible name for the null stub card."""
    return build_stub_card()


def run_one_stud(scene: Scene | None = None) -> tuple[dict[str, Any], list]:
    """Segment the one stud. Returns the scorecard and OBB detections."""
    from openwall_stud.poststep import score_clusters
    from openwall_stud.region_grow import members_from_labels, grow_labels

    scene = scene or make_scene()
    started = time.perf_counter()
    work = repo_root() / "artifacts" / "one_stud" / "pcl"
    labels, provenance = grow_labels(scene.points_m, work)
    members, assembly = members_from_labels(scene.points_m, labels)
    runtime_s = time.perf_counter() - started
    native = bool(provenance.get("native_pcl_region_growing"))
    n_faces = int(assembly["n_face_clusters"])
    n_merges = int(assembly["adjacency_merges"])
    n_out = int(assembly["n_unassigned"])
    if native and n_faces == 1 and n_merges == 0:
        short = (
            f"PCL 1.14 RegionGrowing returned 1 cluster and left {n_out} points unassigned. "
            "No face-union step ran. Minimal OBB, axis not forced to Z."
        )
        detection_note = (
            f"pcl::RegionGrowing (libpcl 1.14) returned {n_faces} cluster and left {n_out} points unassigned. "
            "Adjacency merges were 0, so this cloud did not exercise a face-to-cuboid join. "
            "The box is the minimal OBB of that cluster. Counts are this synthetic stud, not a field accuracy."
        )
        geometry_note = (
            "Section and length are that cluster's minimal OBB versus the dressed generator size. "
            "The long axis is not forced to Z. "
            "Printed errors can match the Open3D row when both boxes cover nearly the same points. The runtime and the cluster count are this PCL call."
        )
    elif native:
        short = (
            f"PCL 1.14 RegionGrowing ({n_faces} face clusters, {n_merges} adjacency merges). "
            "Axis not forced to Z."
        )
        detection_note = (
            "Face clusters are pcl::RegionGrowing on this cloud. "
            "Members join only when voxel samples are within 20 mm. Remote coplanar patches are not merged. "
            "Counts are this synthetic stud, not a field accuracy."
        )
        geometry_note = (
            "Section and length are the minimal OBB of each adjacency member versus the dressed generator size. "
            "The long axis is not forced to Z."
        )
    else:
        short = "NumPy smoothness region-grow port, because the PCL binary did not run. Adjacent-face cuboid. Axis not forced to Z."
        detection_note = (
            "libpcl RegionGrowing did not return labels. "
            f"Fallback: {provenance.get('fallback_reason')}. "
            "The numbers below are the in-process port on this synthetic stud, not a libpcl measurement and not a field accuracy."
        )
        geometry_note = (
            "Section and length are the minimal OBB of each adjacency member versus the dressed generator size. "
            "The long axis is not forced to Z."
        )
    sections, detections = score_clusters(
        scene,
        members,
        runtime_s=runtime_s,
        detection_note=detection_note,
        geometry_note=geometry_note,
        angle_extra="The long axis is not forced to Z.",
        cost={
            "runtime_s": round(runtime_s, 4),
            "license": "BSD",
            "license_url": "https://raw.githubusercontent.com/PointCloudLibrary/pcl/master/LICENSE.txt",
            "hardware": "CPU",
            "n_points_in": scene.n_points,
            "failure_modes": [
                "Smoothness growing splits a stud into faces; the cuboid step has to reunite faces that touch.",
                "An adjacency gap wide enough to cross a bay would merge neighboring studs. This run uses 20 mm.",
                "Remote coplanar merge (Bassier) is not used.",
                "Forcing the axis to Z would hide lean. This run does not.",
                "Özkan 2022 beam-completeness figures are one historic roof and are not this score.",
            ],
            "note": "Runtime is this process on this one stud. It is not a field budget.",
            "region_grow": provenance,
            "cuboid_assembly": assembly,
        },
    )
    card = ran_card(
        algorithm_id="A2",
        algorithm=PCL["name"],
        rank=2,
        scene=scene_record(scene),
        sections=sections,
        implementation={
            "native_pcl_region_growing": native,
            "region_grow": provenance,
            "cuboid_assembly": assembly,
        },
        implementation_short=short,
    )
    return card, detections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PCL region-grow on the one synthetic stud, or write a stub card.")
    parser.add_argument("--stub", action="store_true", help="Write the null stub card and do not segment.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=None)
    parser.add_argument("--skip-day-row", action="store_true")
    args = parser.parse_args(argv)
    if args.stub:
        dest = args.out or Path("artifacts/scorecards/pcl_stub.json")
        path = emit_stub(dest, build_stub_card())
        print(f"PCL stub scorecard written to {path}. PCL was not executed.")
        return 0

    from openwall_stud.one_stud_publish import publish_attempt

    scene = make_scene()
    card, detections = run_one_stud(scene)
    dest = args.out or (repo_root() / "artifacts" / "scorecards" / "one_stud_pcl.json")
    figure = args.figure or (repo_root() / "docs" / "research" / "images" / "one-stud-five-finders" / "02-pcl.png")
    publish_attempt(
        algorithm="pcl",
        card=card,
        detections=detections,
        scene=scene,
        out=dest,
        figure=figure,
        write_day_row=not args.skip_day_row,
    )
    print(f"PCL one-stud scorecard written to {dest}. status={card['status']} bars={card.get('stage0_pass_fail')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
