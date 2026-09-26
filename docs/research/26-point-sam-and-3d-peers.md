# Point-SAM and 3D segmentation peers

Date: **2026-09-26**. Writer: **Other**. Bibliography check: UTC, against arXiv, Crossref, CVF open access, official README citation blocks, and GitHub/Hugging Face APIs. The machine this fit is written for is Oz_PC's RTX 4080 SUPER, the same card named in [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md). This pass loaded no checkpoint and wrote no scorecard.

Records live in [references.bib](../../papers/trueplank-stud-lean-qa/references.bib). Each key below is an entry in that file. Published ScanNet, ScanNet200, S3DIS, and STPLS3D figures stay on those benchmarks. None are recopied here, and none are a wood-stud score.

The order is the fit Oz asked to record for a residential wood-stud cloud (XYZ, with RGB when the capture has it) on that one GPU. It is a reading of input, prompt, and license. It is not a measured ranking.

**Reclassification (2026-09-26).** Live buckets are [27-four-way-tool-classification.md](27-four-way-tool-classification.md). Orders 1–4 below are bucket 3, the four promptable foundation models (transformer, no labels, GPU): Point-SAM, SAM3D (Pointcept SegmentAnything3D), OpenMask3D, and Segment3D. They have no scorecard here. Point Transformer V3 stays bucket 2 (supervised; former bake-off rank 4). SAM 2 stays adjacent to bucket 3: image-prompted, not native 3D, former bake-off rank 7. Mask3D, SoftGroup, and ISBNet stay outside the four foundation models. CloudCompare is not in this note; it is bucket 4 (interactive GUI), former bake-off rank 3.

## Fit order

| Order | Method | Key | License | Input | Promptable | GPU one-liner |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Point-SAM | `zhou2025pointsam` | Code MIT (GitHub API, `zyc00/Point-SAM`). Weights `apache-2.0` (Hugging Face API, `yuchen0187/Point-SAM`). | Point cloud. README inference takes prompt points and a PLY. ViT-L checkpoint on that Hugging Face repo. | Yes. Point prompts on the cloud. | README asks for PyTorch ≥ 2.1 and CUDA extensions. Hugging Face API: 311,042,732 F32 parameters. No 4080 SUPER memory figure on the card. |
| 2 | SAM3D (Yang et al.) | `yang2023sam3d` | MIT (`Pointcept/SegmentAnything3D`). | Posed RGB plus the point cloud. README maps 2D SAM masks into the cloud with depth, then merges adjacent frames. | 2D SAM on frames, then a 3D merge. A pure LAS or PLY has no frames. | README install pins PyTorch 1.11 and CUDA 11.3, and names CUDA arch 7.5 and 8.0 as compile examples. No 4080 SUPER figure. |
| 3 | OpenMask3D | `takmaz2023openmask3d` | MIT (`OpenMask3D/openmask3d`). | PLY in a z-up frame, plus posed RGB-D and a 4×4 intrinsics file. | Open-vocabulary queries over class-agnostic masks. The mask module checkpoint on the README is ScanNet200-trained, with a separate file for an arbitrary scene. | README flag `OPTIMIZE_GPU_USAGE` for a smaller footprint. Install notes name MinkowskiEngine. No 4080 SUPER figure. |
| 4 | Segment3D | `huang2024segment3d` | UNVERIFIED THIS PASS. The project page fetched that day had no code URL. | Project page: a native 3D model on the scene. Training text there uses RGB-D sequences and SAM pseudo-labels. | Class-agnostic masks. The page's text-retrieval example routes those masks through OpenMask3D. | No memory figure on the project page. |
| 5 | Mask3D | `schult2023mask3d` | MIT (`JonasSchult/Mask3D`). | Point cloud. Closed indoor vocabulary (the paper's benchmarks are ScanNet, S3DIS, STPLS3D, ScanNet200). | Closed-set instance masks. | No 4080 SUPER figure on the repo API. |
| 5 | SoftGroup | `vu2022softgroup` | MIT (`thangvubk/SoftGroup`). | Point cloud. Closed-set semantic grouping, then refinement. | Closed-set. | No 4080 SUPER figure on the repo API. |
| 5 | ISBNet | `ngo2023isbnet` | BSD-3-Clause (`VinAIResearch/ISBNet`). | Point cloud. The abstract uses axis-aligned boxes inside the mask decoder. | Closed-set. | No 4080 SUPER figure on the repo API. |

Point Transformer V3 (`wu2024ptv3`) stays the backbone already wired as former bake-off rank 4 in [11-stud-segmentation-algorithm-ranking.md](11-stud-segmentation-algorithm-ranking.md), through Pointcept (`pointcept`). That row is bucket 2 (supervised learning), a feature backbone, not one of the four foundation models. The promptable model in this table is Point-SAM. SAM 2 (`ravi2024sam2`) stays former bake-off rank 7 and stays adjacent to bucket 3: an image and video mask, lifted when a camera is already registered, not a native 3D model ([24-sam2-rank7-and-curriculum.md](24-sam2-rank7-and-curriculum.md), [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md)).

Order 1 is the peer that takes a cloud and a point prompt. Orders 2 and 3 need posed frames, the same gate a pure LAS or PLY already applies to SAM 2. Order 4 is a trained class-agnostic 3D model; its code URL was not on the page fetched. Order 5 is the closed-set indoor instance family. A stud class is absent from those vocabularies in the same way the BIMStruct3D control has no stud class.

## Also entered, outside that order

Authors and titles confirmed cleanly, so these two have bib entries. They are not inserted into the order above.

| Method | Key | What the live pages support |
| --- | --- | --- |
| Any3DIS | `nguyen2025any3dis` | CVPR 2025. Class-agnostic instances by tracking 2D masks with SAM 2 across RGB-D views, then lifting superpoints. Official code license: UNVERIFIED THIS PASS. |
| SegPoint | `he2024segpoint` | ECCV 2024. Point cloud plus a text query, through a multimodal language model (instruction, referring, semantic, open-vocabulary). Code URL: UNVERIFIED THIS PASS. |

## Omitted on purpose

SA3D is Cen, Fang, Zhou, Yang, Xie, Zhang, Shen, and Tian, *Segment Anything in 3D with Radiance Fields*, arXiv:2304.12308 (atom record, 2026-09-26; comment names a NeurIPS 2023 extension). The representation is a radiance field. It has no entry in `references.bib`.

The SAM3D entry in the bibliography is `yang2023sam3d`: Yang, Wu, He, Zhao, and Liu, *SAM3D: Segment Anything in 3D Scenes*, arXiv:2306.03908, code `Pointcept/SegmentAnything3D`. Meta's generative image-to-mesh SAM 3D model is a different task and has no entry.

## Key the pages would not support

arXiv:2312.17232 is Segment3D with first author Rui Huang, ECCV 2024. The bib key is `huang2024segment3d`. The Crossref author line has no Yan.

Mask3D's Crossref venue is ICRA 2023, pages 8216–8223, DOI `10.1109/icra48891.2023.10160590`. The arXiv comment says "ICRA 2023 camera-ready version". The key is `schult2023mask3d`.

SoftGroup pages in the bib are the Crossref IEEE pages 2698–2707. The CVF 2022 open-access bibtex prints 2708–2717. Both fetches are recorded on `vu2022softgroup`.
