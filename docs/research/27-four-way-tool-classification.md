# Four-way tool classification

Date: **2026-09-26**. Writer: **Other**. Oz locked this split. It sits on top of the rank ledger. It does not delete a scorecard, a day-table row, or a former bake-off rank.

The bake-off now has **three** true geometry-first tools, **two** supervised nets, **four** foundation models, and **one** interactive viewer.

## The lock

| Bucket | Kind | Members |
| --- | --- | --- |
| 1 | **Geometry-first automated.** RANSAC or other classical geometry. No training. | Open3D. PCL / NumPy region-grow cuboid. pyRANSAC-3D. |
| 2 | **Supervised learning.** Needs labeled training. | Pointcept / PTv3. Open3D-ML RandLA-Net. |
| 3 | **Promptable foundation models.** Transformer. No labels at inference. GPU. | Point-SAM. SAM3D (Pointcept SegmentAnything3D). OpenMask3D. Segment3D. |
| 4 | **Interactive GUI tools.** Manual edit and visualization. Not automated finders. | **CloudCompare.** |

CloudCompare is removed from bucket 1. Geometry-first automated means Open3D, the PCL / NumPy region-grow cuboid, and pyRANSAC-3D only.

**SAM 2** stays where it already is: a 2D mask lifted onto points when a camera is registered ([24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md), [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md)). It is **adjacent** to bucket 3 because it is image-prompted, not a native 3D model. It is not a fifth foundation model, and this note does not delete that work. Former bake-off rank 7 remains the archive label for those cards.

The closed-set indoor instance nets in [26-point-sam-and-3d-peers.md](26-point-sam-and-3d-peers.md) (Mask3D, SoftGroup, ISBNet) stay outside these four buckets. They are not the four foundation models. Point-SAM, SAM3D, OpenMask3D, and Segment3D have bibliography entries and no scorecard in this repository. This note does not invent a stud metric for them.

## Former ranks, same tools

| Former bake-off rank | Stack | Live bucket |
| --- | --- | --- |
| 1 | Refined Open3D | 1. Geometry-first automated |
| 2 | PCL / NumPy region-grow cuboid | 1. Geometry-first automated |
| 3 | CloudCompare RANSAC shape detection | **4. Interactive GUI.** Not geometry-first. |
| 4 | Pointcept / PTv3 | 2. Supervised learning |
| 5 | Open3D-ML RandLA-Net | 2. Supervised learning |
| 6 | pyRANSAC-3D sequential cuboid | 1. Geometry-first automated |
| 7 | SAM 2 image mask, lifted | Adjacent to 3. Image-prompted, not native 3D |

**Former bake-off rank 3 = CloudCompare, now bucket 4.**

The 2026-09-24 engineering master table in [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md) still numbers CloudCompare as row 3 and EdgeWise as row 7. Those row numbers are that survey. They are not this lock. Master-table row 6 (Chen, Jiang, and Xiong 2025) was never the pyRANSAC-3D bake-off add.

## Wrong / expected / change

Compared with the old reading that ranks 1–7 are one ordered list of automated finders.

| | Wrong | Expected | Change |
| --- | --- | --- | --- |
| Who finds studs | Ranks 1–7, including CloudCompare as a geometry-first automated finder (the old “rank 3” slot next to Open3D and PCL). | Three geometry-first automated tools (Open3D, PCL / NumPy region-grow cuboid, pyRANSAC-3D), two supervised nets, four promptable foundation models, and one interactive viewer. | Live framing tables and the paper draft use the four buckets. Former rank numbers stay as archive labels. |
| CloudCompare | Delete its results, or write that the plugin never ran, or keep counting it inside the geometry-first automated set. | The day table, the phase-1 cards, the room card, and the stud-only tune stay. They are archive measurements of an interactive tool. They are not a fourth geometry-first automated finder. | This note. Scorecards under `artifacts/scorecards/` are not rewritten. |
| SAM 2 | Drop the rank-7 cards, or call SAM 2 a native 3D foundation model beside Point-SAM. | SAM 2 remains the image-prompted lift already scored. The four foundation models are Point-SAM, SAM3D, OpenMask3D, and Segment3D. | Docs 24 and 25 stay. SAM 2 is named adjacent to bucket 3. |

## What stays an archive measurement

Historical rows are not re-labeled in place and are not recounted as geometry-first automated finders.

- `artifacts/scorecards/`, including CloudCompare JSON. Not rewritten by this lock.
- [13-stud-seg-results-by-day.md](13-stud-seg-results-by-day.md). Rows whose algorithm is `cloudcompare` stay, including the 2026-09-24 `not_run` stubs and the 2026-09-25 phase-1 measurements.
- Run notes that quote former ranks: [16-one-stud-five-finder-run.md](16-one-stud-five-finder-run.md), [18-ozpc-ranks4-5-run.md](18-ozpc-ranks4-5-run.md), [19-phase1-s1-lean-sweep.md](19-phase1-s1-lean-sweep.md), [20-synthetic-stud-finetune.md](20-synthetic-stud-finetune.md), [24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md), [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md). Their tables keep the rank numbers they were written with.
- The stud-only CloudCompare tune on branch `cursor/cc-stud-param-tune-78b7` (PR #22). That pass ran. It is an archive measurement of the interactive tool, not a geometry-first automated finder.

A later reader who needs the old order uses the former-rank column above. A later reader who needs the live split uses the four buckets.
