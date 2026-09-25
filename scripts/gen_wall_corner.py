"""Write a synthetic outside wall-corner cloud and a small manifest.

Two vertical planes meet at about 90 degrees. An optional floor sits in the
interior quadrant. Spacing is 5 mm. Noise is 1–5 mm. Planted leans are the
SKIL Face A / Face B means (0.383° and 0.250° from plumb). The PLY is
gitignored. The manifest is the committed record.

    python scripts/gen_wall_corner.py

This is not a stud generator and it does not read the painted field scan.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.wall_corner import (  # noqa: E402
    CLOUD_DIR,
    MANIFEST_PATH,
    default_scenes,
    make_corner,
    refit_report,
    scene_record,
    write_manifest,
    write_ply,
)


def build() -> list[dict]:
    records = []
    for spec in default_scenes():
        cloud = make_corner(
            name=spec["name"],
            noise_std_m=float(spec["noise_mm"]) / 1000.0,
            seed=int(spec["seed"]),
            floor=bool(spec["floor"]),
        )
        report = refit_report(cloud)
        worst = max(report["face_a_abs_error_deg"], report["face_b_abs_error_deg"])
        if worst > 0.05:
            raise SystemExit(
                f"{cloud.name} plane refit missed the planted lean by {worst:.4f} deg"
            )
        if not 89.0 <= report["corner_angle_deg"] <= 91.0:
            raise SystemExit(f"{cloud.name} corner angle {report['corner_angle_deg']:.3f} is not ~90 deg")
        ply_rel = f"data/cache/wall-corner/{cloud.name}.ply"
        sha = write_ply(CLOUD_DIR / f"{cloud.name}.ply", cloud.points_m, cloud.labels)
        record = scene_record(cloud, ply_rel, sha)
        records.append(record)
        print(
            f"{cloud.name}: n={record['n_points']} "
            f"A={record['face_a_refit_lean_deg']:.4f} (err {record['face_a_abs_error_deg']:.4f}) "
            f"B={record['face_b_refit_lean_deg']:.4f} (err {record['face_b_abs_error_deg']:.4f}) "
            f"corner={record['corner_angle_deg']:.3f}"
        )
    write_manifest(records, MANIFEST_PATH)
    print(f"manifest {MANIFEST_PATH}")
    return records


if __name__ == "__main__":
    build()
