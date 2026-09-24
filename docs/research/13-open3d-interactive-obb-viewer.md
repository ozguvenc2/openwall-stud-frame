# Open3D interactive view: colored points and oriented boxes

Research date: **2026-09-24**. Oz has an Open3D window on screen and wants the same look as the matplotlib cluster views: points in label colors, and a wire box on each component. This note is the spec for `open3d.visualization.draw_geometries` in **Open3D 0.20.0** (the pin in `requirements.txt`). The sketch at the end was checked against the 0.20 API pages. It was **not executed** in this pass. There is no sample PLY in git.

The JSON contract lives on draft **PR #5**, branch `cursor/classical-seg-obb-1a3e`:

- Writer: `scripts/classical_segment_obb.py`
- Runbook: `docs/research/09-classical-seg-runbook.md`
- Shape example: `docs/research/examples/classical-seg-components.example.json`
- Schema string: `openwall.classical_seg.components.v1`

That branch is not merged. Main does not contain the script yet. The field names below are what that script writes (`np.asarray(box.R)` and `box.extent` from an Open3D `OrientedBoundingBox`).

## Why the window looks empty

`draw_geometries` draws only the geometries in the list. A call with an empty list, or a visualizer created and never given the cloud, is a blank window. Three other cases look the same:

| What happened | What you see | What to do |
| --- | --- | --- |
| The PLY stores RGB and every channel is 0 | Black points on the default dark background | Paint a color before drawing. The classical script already treats all-zero RGB as “no color” and uses timber brown `(0.45, 0.28, 0.14)`. |
| Only the boxes were built, or only the cloud, and the other was dropped | A window with nothing you recognize | Pass the point cloud and the line sets in the **same** list. |
| Coordinates are a map projection (hundreds of thousands) | The legacy view jitters or shows nothing useful | Subtract the centroid from the points and from every box center before display. Keep the original file unchanged. |
| `point_size` stays 1 and the cloud is sparse | A few dim pixels | `draw_geometries` has no point-size argument. Use `Visualizer`, `get_render_option().point_size = 2.0` (or larger), then `run()`. |

Press `H` in the window for the key list (orbit, pan, zoom, capture). The 0.20 tutorial is https://www.open3d.org/docs/release/tutorial/visualization/visualization.html.

## What the JSON gives you

Each component:

| Field | Role |
| --- | --- |
| `id` | Integer |
| `label` | `upright`, `beam_like`, `planar`, `blob`, or `clutter` |
| `center` | Length-3, file units |
| `R` | 3×3, Open3D rotation. Column `i` is the axis of `extents_units[i]`. |
| `extents_units` | Full side lengths, same units as the PLY. Not rescaled to metres. |
| `bbox_kind` | `obb`, `obb_robust`, `plane_obb`, or `aabb` |
| `n_points`, `volume`, `source`, `long_axis_abs_cos_up` | Report fields. Not required to draw the box. |

The JSON does **not** store point indices. Label colors on the points come from `labeled.ply` if the segmenter was run with `--save-colored-ply`. That PLY is colored by **label**, not by component id, matching the PNG views. A raw PLY plus the JSON can still show one timber-colored cloud and one colored wire box per component. Distinct hues per stud need indices the JSON does not have.

Label colors copied from the PR #5 script:

| Label | RGB |
| --- | --- |
| `upright` | 0.11, 0.45, 0.28 |
| `beam_like` | 0.77, 0.42, 0.10 |
| `planar` | 0.22, 0.40, 0.72 |
| `blob` | 0.42, 0.30, 0.60 |
| `clutter` | 0.55, 0.22, 0.22 |

`--up` in that script is the file axis used to assign those labels. It is not a gravity measurement. The boxes in the window use the same axis the JSON was built with.

## API

Open3D 0.20:

- `o3d.geometry.OrientedBoundingBox(center, R, extent)` — same layout the script stored.
- `o3d.geometry.LineSet.create_from_oriented_bounding_box(box)` — twelve edges. https://www.open3d.org/docs/latest/python_api/open3d.geometry.LineSet.html
- `line_set.paint_uniform_color([r, g, b])`
- `o3d.visualization.draw_geometries(geometry_list, window_name="Open3D", width=1920, height=1080, ...)`

An `OrientedBoundingBox` can also be passed straight into `draw_geometries` (upstream issue https://github.com/isl-org/Open3D/issues/2716). The line set is the one that takes a per-label color on the edges.

`draw_geometries` blocks until the window closes. It returns `None`.

## Sketch

Not wired into `scripts/`. Run it from the repo root after `pip install -r requirements.txt`, with a PLY that already exists on disk. Default paths match the PR #5 runbook and are gitignored.

```python
"""Interactive label colors + oriented boxes. Spec sketch, not a shipped tool."""

from pathlib import Path

import numpy as np
import open3d as o3d

LABEL_RGB = {
    "upright": (0.11, 0.45, 0.28),
    "beam_like": (0.77, 0.42, 0.10),
    "planar": (0.22, 0.40, 0.72),
    "blob": (0.42, 0.30, 0.60),
    "clutter": (0.55, 0.22, 0.22),
}
TIMBER = (0.45, 0.28, 0.14)


def load_points(path: Path) -> o3d.geometry.PointCloud:
    cloud = o3d.io.read_point_cloud(str(path))
    if len(cloud.points) == 0:
        raise SystemExit(f"no points in {path}")
    colors = np.asarray(cloud.colors) if cloud.has_colors() else np.zeros((0, 3))
    if colors.size == 0 or float(np.nanmax(colors)) <= 1e-8:
        cloud.paint_uniform_color(TIMBER)
    return cloud


def line_sets_from_components(payload: dict) -> list[o3d.geometry.LineSet]:
    sets = []
    for comp in payload["components"]:
        center = np.asarray(comp["center"], dtype=float)
        rotation = np.asarray(comp["R"], dtype=float)
        extent = np.asarray(comp["extents_units"], dtype=float)
        box = o3d.geometry.OrientedBoundingBox(center, rotation, extent)
        lines = o3d.geometry.LineSet.create_from_oriented_bounding_box(box)
        rgb = LABEL_RGB.get(comp.get("label", ""), (1.0, 1.0, 1.0))
        lines.paint_uniform_color(rgb)
        sets.append(lines)
    return sets


def main() -> None:
    import json

    root = Path("data/raw/darus-intcdc")
    labeled = root / "seg_out" / "labeled.ply"
    raw = root / "preview.ply"
    cloud = load_points(labeled if labeled.is_file() else raw)
    payload = json.loads((root / "seg_out" / "components.json").read_text())
    geoms = [cloud, *line_sets_from_components(payload)]
    o3d.visualization.draw_geometries(
        geoms,
        window_name="OpenWall components",
        width=1280,
        height=800,
    )


if __name__ == "__main__":
    main()
```

If the points are still hard to see, replace the last call with a visualizer and set `point_size`:

```python
vis = o3d.visualization.Visualizer()
vis.create_window(window_name="OpenWall components", width=1280, height=800)
for geom in geoms:
    vis.add_geometry(geom)
vis.get_render_option().point_size = 2.0
vis.run()
vis.destroy_window()
```

Shift a georeferenced cloud before either call: subtract `cloud.get_center()` from the point cloud (`translate`) and from each JSON `center`. Do not write that shift back to the survey file.

## What this window is not

The colors are the heuristic labels from the classical script, or a single timber color. They are not a trained stud/plate/beam segmentation. The long axis of a box is not compared with the 0.12° margin here. That comparison is still the unfinished paint in doc 02, and it still needs a gravity vector rather than the file’s Z axis.
