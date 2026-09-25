"""Write the fine-tune manifest and cache labeled clouds under data/cache/.

    .venv-o3dml\\Scripts\\python.exe scripts/build_finetune_synth.py
    .venv-o3dml\\Scripts\\python.exe scripts/build_finetune_synth.py --manifest-only
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openwall_stud.finetune_synth import (  # noqa: E402
    build_manifest,
    ensure_cloud,
    materialize,
    point_labels,
    write_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the synthetic stud/clutter fine-tune set.")
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args(argv)
    payload = build_manifest()
    path = write_manifest()
    counts = payload["counts"]
    print(
        f"manifest {path} train={counts['train']} "
        f"(stud {counts['train_stud']}, floor {counts['train_stud_floor']}) "
        f"val={counts['val']} (stud {counts['val_stud']}, floor {counts['val_stud_floor']})"
    )
    probe = next(spec for spec in payload["train"] if spec["kind"] == "stud_floor")
    scene = materialize(probe)
    labels = point_labels(scene)
    if int(labels.min()) != 0 or int(labels.max()) != 1:
        raise SystemExit("floor scene did not produce both clutter and stud labels")
    if scene.studs[0].lean_axis != probe["axis"] and probe["lean_deg"] != 0.0:
        raise SystemExit("floor scene lean axis did not follow the spec")
    print(
        f"probe {probe['id']} points={scene.n_points} "
        f"stud={int((labels == 1).sum())} clutter={int((labels == 0).sum())} "
        f"axis={scene.studs[0].lean_axis}"
    )
    if args.manifest_only:
        return 0
    rows = payload["train"] + payload["val"]
    started = time.perf_counter()
    for index, spec in enumerate(rows, start=1):
        cloud = ensure_cloud(spec)
        if index == 1 or index % 25 == 0 or index == len(rows):
            print(
                f"cached {index}/{len(rows)} {spec['id']} "
                f"points={cloud['points'].shape[0]} elapsed_s={time.perf_counter() - started:.1f}",
                flush=True,
            )
    print(f"cache done in {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
