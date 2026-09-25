"""Write the phase-2 synthetic outside corner and its planted leans.

PLY is gitignored (``*.ply``). The committed copies are the JSON ground
truth and a compressed npz of points and labels. This is not a stud cloud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.phase2_corner import synthesize_corner  # noqa: E402

OUT = ROOT / "artifacts" / "phase2_corner_synth"


def _write_ply(path: Path, points: np.ndarray, labels: np.ndarray) -> None:
    import open3d as o3d

    colors = np.zeros_like(points)
    colors[labels == 1] = (0.75, 0.22, 0.17)
    colors[labels == 2] = (0.14, 0.44, 0.70)
    colors[labels == 0] = (0.55, 0.55, 0.55)
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    cloud.colors = o3d.utility.Vector3dVector(colors)
    if not o3d.io.write_point_cloud(str(path), cloud):
        raise RuntimeError(f"failed to write {path}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scene = synthesize_corner()
    points = scene["points"]
    labels = scene["labels"]
    np.savez_compressed(OUT / "corner_skil_means.npz", points=points.astype(np.float32), labels=labels.astype(np.int16))
    _write_ply(OUT / "corner_skil_means.ply", points, labels)
    public = {key: value for key, value in scene.items() if key not in {"points", "labels"}}
    public["n_points"] = int(len(points))
    public["npz"] = "artifacts/phase2_corner_synth/corner_skil_means.npz"
    public["ply"] = "artifacts/phase2_corner_synth/corner_skil_means.ply"
    public["ply_gitignored"] = True
    public["note"] = (
        "Synthetic outside corner. Labels are floor, wall_a, wall_b. "
        "Not studs. Planted leans are the SKIL face means. "
        "svd_on_noisy_labels is the plane fit on the noisy points of each class."
    )
    with (OUT / "corner_skil_means.json").open("w", encoding="utf-8") as handle:
        json.dump(public, handle, indent=2)
        handle.write("\n")
    print(json.dumps(public, indent=2))


if __name__ == "__main__":
    main()
