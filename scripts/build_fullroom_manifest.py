"""Write the 28-stud full-room train/val manifest.

    .venv\\Scripts\\python.exe scripts/build_fullroom_manifest.py
    .venv\\Scripts\\python.exe scripts/build_fullroom_manifest.py --check-one
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.finetune_fullroom import (  # noqa: E402
    CORNER_SLOTS,
    FULL_ROOM_N_STUDS,
    build_manifest,
    materialize,
    write_manifest,
)
from openwall_stud.synthetic import full_room_28  # noqa: E402
from openwall_stud.finetune_synth import point_labels  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the full-room 28-stud manifest.")
    parser.add_argument("--check-one", action="store_true", help="Generate train seed 1101 and print counts.")
    args = parser.parse_args(argv)
    path = write_manifest()
    payload = build_manifest()
    print(
        f"wrote {path.relative_to(ROOT)} train={payload['counts']['train']} val={payload['counts']['val']}",
        flush=True,
    )
    if args.check_one:
        spec = payload["train"][0]
        scene = materialize(spec)
        labels = point_labels(scene)
        print(
            f"check {spec['id']} seed={spec['seed']} studs={len(scene.studs)} "
            f"points={scene.n_points} clutter={(labels == 0).sum()} stud={(labels == 1).sum()}",
            flush=True,
        )
        if len(scene.studs) != FULL_ROOM_N_STUDS:
            raise SystemExit(f"expected {FULL_ROOM_N_STUDS} studs")
        leans = [0.67 if slot in CORNER_SLOTS else 2.0 for slot in range(FULL_ROOM_N_STUDS)]
        axes = ["+X" if slot in CORNER_SLOTS else "-Y" for slot in range(FULL_ROOM_N_STUDS)]
        worst = full_room_28(leans_deg=leans, lean_axes=axes, seed=1101, noise_std_m=0.0)
        print(
            f"worst-case gap_m={worst.meta['min_plan_gap_after_lean_tip_m']:.4f} studs={len(worst.studs)}",
            flush=True,
        )
        if len(worst.studs) != FULL_ROOM_N_STUDS:
            raise SystemExit("worst-case room lost a stud")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
