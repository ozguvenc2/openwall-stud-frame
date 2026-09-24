"""PCL region-grow + Euclidean + cuboid stub (rank 2).

Install
    PCL is a C++ library (BSD). This repo does not vendor it and does not
    import it. A later port should call ``pcl::RegionGrowing`` and
    ``pcl::EuclideanClusterExtraction`` from the Point Cloud Library, then fit
    a cuboid the way Özkan / Pöchtrager do for timber members. Do not add a
    Python dependency that claims to be PCL unless that wheel is actually
    installed and imports.

Entrypoint
    python -m openwall_stud.contenders.pcl_region_grow --out artifacts/scorecards/pcl_stub.json

    That command writes a stub scorecard and does not segment a cloud.

Do not
    Do not port Bassier's remote coplanar merge. Joining coplanar patches
    glues neighboring studs that share a wall plane.
    Do not force a member axis to global Z. That zeros the lean this project
    exists to measure (the Chen / Jiang / Xiong 2025 cylinder assumption).

Citations
    Özkan et al. 2022, https://doi.org/10.3390/jimaging8010010
    Pöchtrager et al. 2018, https://doi.org/10.4995/var.2018.8855
    PCL RegionGrowing, https://pointclouds.org/documentation/classpcl_1_1_region_growing.html
    The 29% to 63% beam-completeness figures in Özkan 2022 are one historic
    roof, not a 2x4 stud score. Do not copy them into a scorecard as accuracy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openwall_stud.contenders.common import emit_stub, stub_card

PCL = {
    "rank": 2,
    "algorithm_id": "A2",
    "status": "stub",
    "name": "PCL region-grow + cuboid (Ozkan/Pochtrager, no Bassier merge)",
}


def build_card() -> dict:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the PCL stub scorecard. Does not run PCL.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/scorecards/pcl_stub.json"),
    )
    args = parser.parse_args(argv)
    path = emit_stub(args.out, build_card())
    print(f"PCL stub scorecard written to {path}. PCL was not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
