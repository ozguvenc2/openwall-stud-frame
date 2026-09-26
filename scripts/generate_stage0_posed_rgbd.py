"""Write stage0 posed RGB-D for OpenMask3D CLIP / open-vocab.

    .venv\\Scripts\\python.exe scripts/generate_stage0_posed_rgbd.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.synth_posed_rgbd import write_posed_rgbd_scene  # noqa: E402
from openwall_stud.synthetic import stage0_single_stud  # noqa: E402

DEST = ROOT / "artifacts" / "phase_neg1" / "stage0_posed_rgbd"


def main() -> int:
    cloud = stage0_single_stud(nominal="2x4", lean_deg=0.0, seed=1)
    meta = write_posed_rgbd_scene(cloud, DEST)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
