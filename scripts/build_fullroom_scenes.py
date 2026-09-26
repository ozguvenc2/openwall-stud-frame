"""Write the lettered full-room scene catalog and check the generator.

    .venv\\Scripts\\python.exe scripts/build_fullroom_scenes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.fullroom_scenes import scene_specs  # noqa: E402
from openwall_stud.synthetic import FULL_ROOM_N_STUDS, full_room_28  # noqa: E402

OUT = ROOT / "artifacts" / "fullroom" / "scenes_expected.json"


def main() -> int:
    rows = scene_specs()
    checked = []
    for row in rows:
        scene = full_room_28(
            leans_deg=row["leans_deg"],
            lean_axes=row["lean_axes"],
            seed=row["seed"],
            spacing_m=row["spacing_m"],
            plate_spacing_m=row["plate_spacing_m"],
            floor_spacing_m=row["floor_spacing_m"],
            noise_std_m=row["noise_std_m"],
            name=row["name"],
        )
        if len(scene.studs) != FULL_ROOM_N_STUDS:
            raise SystemExit(f"{row['letter']} generated {len(scene.studs)} studs")
        planted = [float(stud.lean_deg) for stud in scene.studs]
        if planted != row["leans_deg"]:
            raise SystemExit(f"{row['letter']} planted leans did not round-trip")
        handbook = row["expected_plumb_counts"]["handbook_finish_plumb"]["absolute"]
        nahb = row["expected_plumb_counts"]["nahb_warranty_gauge"]["absolute"]
        checked.append(
            {
                "letter": row["letter"],
                "seed": row["seed"],
                "n_points": scene.n_points,
                "gap_m": scene.meta["min_plan_gap_after_lean_tip_m"],
                "handbook_absolute_red": handbook.get("red", 0),
                "nahb_absolute_red": nahb.get("red", 0),
            }
        )
        print(
            f"{row['letter']} seed={row['seed']} points={scene.n_points} "
            f"handbook_red={handbook.get('red', 0)} nahb_red={nahb.get('red', 0)} "
            f"gap_m={scene.meta['min_plan_gap_after_lean_tip_m']:.4f}",
            flush=True,
        )
    payload = {
        "experiment": "fullroom",
        "decision": "docs/research/37-fullroom-training-decision.md",
        "n_scenes": len(rows),
        "scenes": rows,
        "generator_check": checked,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
