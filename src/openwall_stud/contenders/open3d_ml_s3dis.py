"""Open3D-ML S3DIS control stub (rank 5).

Install
    Open3D-ML lives at https://github.com/isl-org/Open3D-ML (MIT). It is a
    separate install from the ``open3d`` pin in requirements.txt. This
    scaffold does not install it and does not load S3DIS weights.

Entrypoint
    python -m openwall_stud.contenders.open3d_ml_s3dis --out artifacts/scorecards/open3d_ml_stub.json

    When a Stage 5 room cloud exists, one forward pass of RandLA-Net or
    KPConv with the published S3DIS weights is the control. Record the label
    histogram. Do not fit QA boxes from those labels and do not paint them
    green or red. S3DIS mIoU stays on S3DIS.

Do not
    Do not treat office beam/column classes as wood studs.
    Do not copy the model-zoo mIoU into this scorecard.
    Confirm the in-tree RandLA-Net header before shipping; the upstream
    RandLA-Net repository is CC BY-NC-SA 4.0.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openwall_stud.contenders.common import emit_stub, stub_card

OPEN3D_ML = {
    "rank": 5,
    "algorithm_id": "A5",
    "status": "stub",
    "name": "Open3D-ML RandLA-Net or KPConv, S3DIS weights (control only)",
}


def build_card() -> dict:
    return stub_card(
        algorithm_id="A5",
        algorithm=OPEN3D_ML["name"],
        rank=5,
        license_name="Open3D-ML MIT; upstream RandLA-Net repo is CC BY-NC-SA 4.0",
        hardware="GPU typical for the zoo models; not used",
        failure_modes=[
            "S3DIS classes are finished office scenes, not a bare 2x4 wall.",
            "Semantic labels are not stud instances.",
            "Publishing S3DIS mIoU as stud accuracy would be a false claim.",
            "Open3D-ML weights were not downloaded and no forward pass was run.",
        ],
        note="Control-baseline stub. Open3D-ML was not executed. Detection, geometry, and angle are null.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the Open3D-ML stub scorecard. Does not load weights.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/scorecards/open3d_ml_stub.json"),
    )
    args = parser.parse_args(argv)
    path = emit_stub(args.out, build_card())
    print(f"Open3D-ML stub scorecard written to {path}. No forward pass was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
