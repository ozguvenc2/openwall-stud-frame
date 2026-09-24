"""Pointcept PTv3 / PointGroup hook (rank 4).

Install
    Pointcept is a CUDA training stack: https://github.com/Pointcept/Pointcept
    Code license is MIT. This environment does not install it and does not
    train. Do not download BIMStruct3D weights for a stud call: that file is
    CC BY-NC-SA 4.0 and its classes are wall, column, and similar, not stud.

Entrypoint
    python -m openwall_stud.contenders.pointcept_ptv3 --out artifacts/scorecards/pointcept_stub.json

    After labeled Stage 5 clouds exist, the real entry is Pointcept's train
    and test scripts on a stud/plate config that this repo does not contain
    yet. Instance labels would then go through the same OBB and paint
    post-step as the Open3D baseline. That config is intentionally absent.

Do not
    Do not start training in CI or on an unlabeled cloud.
    Do not paint green/red from a BIMStruct3D zero-shot label.
    Do not copy ScanNet or S3DIS scores into the stud scorecard.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openwall_stud.contenders.common import emit_stub, stub_card

POINTCEPT = {
    "rank": 4,
    "algorithm_id": "A4",
    "status": "stub",
    "name": "Pointcept PTv3 / PointGroup (hook only until labeled Stage 5)",
}


def build_card() -> dict:
    return stub_card(
        algorithm_id="A4",
        algorithm=POINTCEPT["name"],
        rank=4,
        license_name="MIT code; some public weights are CC BY-NC-SA 4.0",
        hardware="CUDA, not used",
        failure_modes=[
            "No stud labels yet, so there is nothing to fine-tune.",
            "Zero-shot BIMStruct3D has no stud class.",
            "Commercial use of CC BY-NC-SA weights is not allowed.",
            "A GPU train was not part of this scaffold and was not started.",
        ],
        note="Scaffold hook only. Pointcept was not trained or run. Detection, geometry, and angle are null.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the Pointcept stub scorecard. Does not train.")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/scorecards/pointcept_stub.json"),
    )
    args = parser.parse_args(argv)
    path = emit_stub(args.out, build_card())
    print(f"Pointcept stub scorecard written to {path}. No training was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
