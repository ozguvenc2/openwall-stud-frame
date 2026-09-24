# Classical Open3D segmentation runbook

Run `scripts/classical_segment_obb.py` on a PLY that already exists on disk. The IntCDC preview used here is `data/raw/darus-intcdc/preview.ply`. That file is gitignored. This runbook does not download it and does not claim a measured accuracy.

The script follows the classical path in the Open3D 0.20 notes: voxel downsample, statistical outlier removal, repeated `segment_plane` for large thin patches, `cluster_dbscan` on what remains, then `get_oriented_bounding_box` per cluster. Open3D does not ship region growing or a separate Euclidean-cluster call. `detect_planar_patches` is not used, because it returns one box per face and splits a member.

Labels (`upright`, `beam_like`, `planar`, `blob`, `clutter`) are extent-ratio heuristics plus the `--up` axis. They are not a trained stud model.

## Windows, from the repo root

`requirements.txt` pins `open3d==0.20.0` and includes `matplotlib` for the PNG views. Matplotlib uses the Agg backend, so the screenshots do not need an OpenGL window.

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python scripts\classical_segment_obb.py --input data\raw\darus-intcdc\preview.ply --out-dir data\raw\darus-intcdc\seg_out
```

The same command works if `preview.ply` is already at the default path; `--input` and `--out-dir` can be omitted. Pass `--input` when the PLY lives somewhere else.

PowerShell uses the same `activate` path. The default output directory is under `data/raw/`, which `.gitignore` already excludes. Leave the clouds and the PNGs there. Do not commit them.

## What the script writes

| File | Contents |
| --- | --- |
| `seg_out/components.json` | One record per kept plane or cluster: `id`, `label`, `n_points`, `extents_units`, `volume`, `center`, `R`, plus `bbox_kind`. |
| `seg_out/report.md` | Counts by label, kept and dropped clusters, noise points, min/median/max extent, a longest-side histogram. |
| `seg_out/views/front.png` | Orthographic view, depth along the horizontal axis perpendicular to `--up`. |
| `seg_out/views/side.png` | The other horizontal depth. |
| `seg_out/views/top.png` | Looking along `--up`. |
| `seg_out/views/iso.png` | Oblique orthographic view. |

`extents_units[i]` is the Open3D side length along column `i` of `R`. Values are the PLY's own units. The script does not rescale them and does not call them metres.

A shape example of that JSON, with `n_points` left at 0 so it cannot be read as a scan, is in [examples/classical-seg-components.example.json](examples/classical-seg-components.example.json).

`--save-colored-ply` also writes `seg_out/labeled.ply` (downsampled inliers, colored by label). It is off by default.

Points with missing or all-zero RGB are drawn timber-brown, matching the earlier preview renders. Box edges are line segments in the 2D projection, colored by the heuristic label.

## Gravity

`--up` defaults to `z`. That is the axis the heuristic compares to the long side of each box. It is not a gravity measurement.

The DaRUS IntCDC record does not state that scan Z is plumb. If this preview is that cloud, treat `upright` and `beam_like` as file-axis labels. The report repeats this. Pass `--up y` or `--up 0,1,0` when the vertical axis is something else. The ~0.12° check in [../tolerances.md](../tolerances.md) is not computed here.

## Defaults, and when to retune

Defaults assume coordinates on the order of metres (`--voxel-size 0.02`, `--dbscan-eps 0.06`, plane sides of about 1 m). The report prints the raw axis-aligned size. If that size is millimetres, or a few centimetres, retune before reading the labels.

| Argument | Default | Role |
| --- | --- | --- |
| `--voxel-size` | 0.02 | `voxel_down_sample` |
| `--sor-neighbors` / `--sor-std-ratio` | 20 / 2 | `remove_statistical_outlier` |
| `--max-planes` | 6 | Stop after this many accepted planes |
| `--plane-distance` | max(0.03, 1.5 × voxel) | RANSAC inlier distance |
| `--plane-min-fraction` | 0.05 | Minimum inlier share, unless `--plane-min-points` is set |
| `--plane-min-extent` / `--plane-min-span` | 1.5 / 1.0 | Longest and middle side required to peel a plane |
| `--plane-min-coverage` | 0.35 | Inliers must fill this fraction of their own rectangle |
| `--thin-ratio` | 0.20 | Smallest/middle side; plane gate and `planar` label |
| `--dbscan-eps` | 0.06 | Neighbourhood radius |
| `--dbscan-min-points` | 10 | DBSCAN core-point minimum; `-1` is noise |
| `--min-cluster-size` | 30 | Clusters smaller than this are counted as dropped |
| `--elongation` | 2.8 | Longest/middle side for a stick |
| `--vertical-cos` / `--horizontal-cos` | 0.85 / 0.34 | Long-axis alignment with `--up` |
| `--seed` | 0 | NumPy seed for the PNG subsample |

`--seed` does not seed `segment_plane`. Open3D 0.20 exposes no seed on that call, so the peeled planes can change between runs.

If the report says most DBSCAN points are noise, raise `--dbscan-eps`. If two studs become one box, lower it. A gap smaller than `eps` merges members. A joint where members touch merges them too.

A plane is peeled only when it is crowded, wide, and its inliers fill the rectangle they span (`--plane-min-coverage`). A single member face fails the middle-side test. Several separated studs that happen to be coplanar fail the coverage test, and peeling stops so those points are clustered instead. A truly solid wall or floor still peels. Members that touch at a joint can still become one DBSCAN cluster.

## Label rules

Applied in this order to each kept box:

1. `planar` — smallest side / middle side ≤ `--thin-ratio` (also forced on every peeled plane).
2. `upright` — longest/middle ≥ `--elongation`, and the long axis is within `--vertical-cos` of `--up`.
3. `beam_like` — same elongation, long axis at or below `--horizontal-cos` with `--up` (nearly horizontal).
4. `blob` — longest/shortest ≤ `--blob-ratio`.
5. `clutter` — the rest, including diagonal sticks.

A cluster box is `get_oriented_bounding_box` (PCA). If Qhull rejects a flat cluster, the script retries with `robust=True`, then an axis-aligned box. A peeled plane is stored as `plane_obb`: the RANSAC normal plus the minimum-area rectangle of the inliers. Open3D's robust hull stretches a flat patch (a square becomes a diamond), so that box is not the one written for planes. `bbox_kind` is `obb`, `obb_robust`, `plane_obb`, or `aabb`.
