# Phase-2 neural corner (ranks 4 and 5)

Date (America/Los_Angeles): **2026-09-25**. Machine: **Oz_PC**. GPU: **NVIDIA GeForce RTX 4080 SUPER (16 GB)**. This pass is **Other** (Other Models pool).

The cloud is a synthetic outside corner: two vertical planes meeting at about 90°, plus an optional floor. It is not a stud box, not a dressed 2×4, and not the painted Polycam field scan. That field cloud stays with the classical phase-2 pass. The planted leans are the SKIL Face A and Face B means from that note (0.383° and 0.250° from plumb). This generator did not read a level.

`paper.md` is not edited here. The classical branch owns that file. Wording for a later section 5.6 is in [`papers/trueplank-stud-lean-qa/draft/phase2-neural-corner.patch`](../../papers/trueplank-stud-lean-qa/draft/phase2-neural-corner.patch), against paper-tip `e220747`. If that branch has already moved section 5, keep this note and skip the patch.

## Generator

`scripts/gen_wall_corner.py`. Gravity is +Z. The interior is the +X/+Y quadrant. Face A runs along +X and leans outward by a right-hand rotation about +X. Face B runs along +Y and leans outward by the opposite rotation about +Y. Spacing is 5 mm. Height is 8 ft (2.4384 m) and each face is 4 ft long (1.2192 m), so the tip offset of a 0.383° lean is about 16 mm, above the noise. Labels in the PLY are `0` floor, `1` face_a, `2` face_b.

PLY bytes are gitignored (`*.ply` and `data/cache/`). The committed record is `data/wall-corner/manifest.json`. Rebuild with the script above.

A plane fit on the noisy ground-truth labels of the primary cloud (`corner_skil_means_floor_n2`, 299,145 points, 2 mm noise, seed 23, floor on) recovers 0.3828° and 0.2489° (absolute errors 0.0002° and 0.0011°). The angle between the outward normals is 89.998°. The same check passes on the 1 mm, 5 mm, and no-floor clouds (refit error under 0.05°, corner angle within 1° of 90°).

## What was run

Same interpreters as the phase-1 fine-tune (doc 20):

| stack | interpreter | torch | weights tried |
| --- | --- | --- | --- |
| Rank 4 PTv3 | `.venv` in the ranks-4/5 worktree | 2.7.0+cu126 | BIMStruct3D control (`pointcept_ptv3._forward`, 10-class, 10-pass test-time augmentation), then the stud/clutter head |
| Rank 5 RandLA-Net | `.venv-o3dml` | 2.13.0+cu126 | S3DIS control (`open3d_ml_s3dis._forward`), then the stud/clutter head, then a 3-class corner head |

Each process started with about 14.7 GiB free. Passes were one at a time. None ran out of memory. There is no dollar cost; the cost column is wall time.

Lean for a control card is a 15 mm inlier plane fit to points the model called `wall`, matched to a ground-truth face only when the outward normals agree (dot at least 0.85). A stud label is not a wall face, so the stud heads do not get a lean. The corner head's reported lean is the same 15 mm inlier plane on points predicted as that face. An all-point least-squares lean is stored beside it as `svd_abs_error_deg`, because a few percent of points from the other face tilt that fit.

Rank 4's control already returned both faces, so it was not corner-fine-tuned. Rank 5's control and stud head did not, so a short corner fine-tune ran. Eight training corners, none of them the four eval scenes (the eval leans 0.383° / 0.250° with seeds 23 and 29 are held out). Three epochs stayed near chance (cross-entropy about ln 3). The saved run is 25 epochs, final train loss 0.306, wall time 31.7 s. Checkpoint: `artifacts/weights/corner/randlanet_corner_3class.pth` (20,173,163 bytes). The new layer is `fc1.3`; 328 S3DIS tensors were copied and those two were not.

## Primary cloud (2 mm, floor)

Ground truth: Face A 0.383°, Face B 0.250°.

| stack | weights | both faces | Face A | Face A abs. error | Face B | Face B abs. error | time |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Rank 4 | BIMStruct3D control | yes | 0.3813° | 0.00173° | 0.2500° | 0.00005° | 54.18 s |
| Rank 5 | S3DIS control | no | — | — | — | — | 2.45 s |
| Rank 4 | stud/clutter head | no | — | — | — | — | 0.79 s |
| Rank 5 | stud/clutter head | no | — | — | — | — | 1.01 s |
| Rank 5 | corner head, 25 epochs | yes | 0.3837° | 0.00069° | 0.2505° | 0.00055° | 1.38 s |

Rank 4 control called 96.0% of Face A and 97.6% of Face B `wall`, and 93.4% of the floor `floor` (the rest of the floor is `clutter`, not `wall`). Histogram: 231,956 wall, 59,889 floor, 7,300 clutter.

Rank 5 control called 99.1% of each face `clutter` and 99.9% of the floor `floor`. Wall points: 63. That is a floor detector on this cloud, not a wall detector. No lean is filled.

The stud heads do what they were trained to do. Rank 4 labeled 93.4% / 90.3% of the two faces `stud` and 81.5% of the floor `clutter`. Rank 5 labeled 99.8% / 98.9% of the faces `stud` and 99.4% of the floor `clutter`. Those are not corner-face scores, and they are not a stud found in a wall.

On the corner head, Face A precision / recall are 0.942 / 0.971 and Face B 0.972 / 0.935. The 15 mm inlier plane matches the planted leans. Least squares on every predicted point of the class does not: absolute errors 0.297° and 0.029°. The inlier rule is doing the work.

## The other three clouds

| scene | rank 4 control A / B abs. error | rank 4 time | rank 5 control | rank 5 corner head A / B abs. error | corner-head time |
| --- | --- | ---: | --- | --- | ---: |
| floor, 1 mm | 0.00026° / 0.00003° | 55.37 s | no wall faces (faces are clutter, floor is floor) | 0.00135° / 0.00004° | 0.90 s |
| no floor, 2 mm | 0.00026° / 0.00060° | 46.66 s | no wall faces (both faces clutter) | 0.00158° / 0.00175° | 0.87 s |
| floor, 5 mm | 0.356° / 0.305° | 50.49 s | no wall faces | 0.00262° / 0.00239° | 1.31 s |

Rank 4 at 5 mm noise still sets `both_faces_detected`, and the lean is wrong. Wall recall falls to 0.250 and 0.345. The surviving wall points fit a nearly plumb plane (measured 0.027° and −0.055°). A vertical plane in the wall class is not the planted lean. Majority label on both faces is `clutter`. Floor majority is `clutter` as well (99.5%).

Rank 5's corner head still recovers the planted leans at 5 mm noise, within 0.003°, because the face classes still cover the planes. Its all-point least-squares errors on that cloud are 0.047° and 0.143°. Same caveat as the primary cloud: the inlier plane, not the raw class cloud, is the lean in the table.

Rank 4 control with no floor labels every point `wall` (239,609 / 239,609) and the two inlier planes still match the generator. Rank 5 control on that cloud calls the faces clutter (about 99%) and also calls 2,302 points `floor` even though there is no floor.

## What this is not

Not a stud. Not a multi-stud wall. Not the painted drywall scan. Not a SKIL session; the angles were planted at the recorded means. Not a field mIoU. S3DIS mIoU is not copied. BIMStruct3D weights are CC BY-NC-SA 4.0 and are not committed. The rank-4 control time includes checkpoint load, normal estimation, and 10-pass test-time augmentation, which is why it sits near 50 s while the later head-only forwards sit near 1 s. A 3-epoch RandLA-Net corner pass was at chance and is not the table. Rank 4 was not given a corner head.
