"""CloudCompare RANSAC Shape Detection / CloudComPy stub (rank 3).

Install
    CloudCompare is a desktop GUI (GPL-3.0). The RANSAC Shape Detection
    plugin implements Schnabel, Wahl, and Klein 2007 (planes, spheres,
    cylinders, cones, tori). CloudComPy exposes ``computeRANSAC_SD`` for a
    batch call. Neither binary is required here and neither is imported.

    GUI: https://www.cloudcompare.org/doc/wiki/index.php/RANSAC_Shape_Detection_(plugin)
    Batch: https://www.simulation.openfields.fr/documentation/CloudComPy/html/RANSAC_SD.html

Entrypoint
    python -m openwall_stud.contenders.cloudcompare_ransac --out artifacts/scorecards/cloudcompare_stub.json

    Inspector path, when someone runs it by hand: load the same PLY the
    Open3D baseline used, run RANSAC Shape Detection, export primitive point
    sets, then hand those points to the shared OBB post-step. Do not treat a
    cylinder fit on a 2x4 as a stud.

Do not
    Do not link CloudComPy into a closed-source app (GPL-3.0).
    Do not expect a rectangular stud to come back as one instance. Coplanar
    stud faces become one plane. That is why this rank is an inspector.

Citation
    Schnabel, Wahl, Klein 2007, https://doi.org/10.1111/j.1467-8659.2007.01016.x
    No stud accuracy is claimed from that paper.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openwall_stud.contenders.common import emit_stub, stub_card

CLOUDCOMPARE = {
    "rank": 3,
    "algorithm_id": "A3",
    "status": "stub",
    "name": "CloudCompare RANSAC-SD / CloudComPy",
}


def build_card() -> dict:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the CloudCompare stub scorecard. Does not run RANSAC-SD.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/scorecards/cloudcompare_stub.json"),
    )
    args = parser.parse_args(argv)
    path = emit_stub(args.out, build_card())
    print(f"CloudCompare stub scorecard written to {path}. RANSAC-SD was not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
