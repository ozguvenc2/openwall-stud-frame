# Bake-off master pipeline diagram v2

Date (America/Los_Angeles): **2026-09-26**. **Supersedes** [32-pipeline-master-diagram.md](32-pipeline-master-diagram.md) (PR #36). Named stage brands (AxiomForge → CloudSmith → TrueLevel → BoxFit) plus CloudSmith dials and TrueLevel error-source honesty. Buckets: [27-four-way-tool-classification.md](27-four-way-tool-classification.md). Stage0 re-run: [30-fix-sam3d-openmask3d-stage0.md](30-fix-sam3d-openmask3d-stage0.md). Four-stage error table: [31-four-stage-error-table.md](31-four-stage-error-table.md). OBB / deformation survey: [33-obb-and-deformation-research.md](33-obb-and-deformation-research.md). Scorecard table: [`artifacts/phase_neg1/all_nine_stage0.json`](../../artifacts/phase_neg1/all_nine_stage0.json). CloudCompare stays **out**. No fabricated metrics.

One left-to-right flow: planted absolute truth → CloudSmith sampling → TrueLevel realisticizer → three class pipes (geometry-first ×3, supervised ×2, foundation/zero-shot ×4) → stud masks → shared BoxFit minimal OBB → scorecard. Paint yellow while device ε is unlocked; placeholder ε=0.05° column only; industry τ≈0.12° is not paint.

## Diagram

Source: [diagrams/34-pipeline-master-v2.mmd](diagrams/34-pipeline-master-v2.mmd).

```mermaid
%% OpenWall bake-off master pipeline v2 (doc 34). One L→R flow.
%% Supersedes doc 32. CloudCompare OUT. No fabricated metrics.
%% Paint yellow (ε unlocked). Named stages: AxiomForge → CloudSmith → TrueLevel → pipes → BoxFit → scorecard.
flowchart LR
  %% --- left spine: named stages ---
  S1["Stage1 AxiomForge<br/>perfect mesh<br/>2×4 38.1×88.9 mm<br/>8 ft · 0° lean<br/>synthetic.py"]
  S2["Stage2 CloudSmith<br/>mesh → cloud<br/>25,666 pts<br/>DIAL density · spacing_m<br/>DIAL noise σ · noise_std_m=0.001"]
  S3["Stage3 TrueLevel<br/>realisticizer<br/>(a) Skil ~0.05° — theoretical<br/>(b) human leveler — not injected<br/>(c) lumber surface — not injected<br/>stage0: only Stage2 sampling noise"]

  S1 --> S2 --> S3

  %% --- diverge: three class pipes ---
  subgraph GEO["Geometry-first ×3 · no training"]
    direction TB
    G1["Open3D<br/>• Python OBB on whole cloud<br/>open3d.org"]
    G2["PCL<br/>• native WSL region-grow → OBB<br/>pointclouds.org"]
    G3["pyRANSAC-3D<br/>• sequential cuboid RANSAC<br/>github.com/leomariga/pyRANSAC-3D"]
  end

  subgraph SUP["Supervised ×2 · 2-class stud heads"]
    direction TB
    TR["train short heads on synth<br/>→ artifacts/checkpoints/stud-heads"]
    P4["Pointcept PTv3<br/>• transformer backbone<br/>github.com/Pointcept/Pointcept"]
    P5["Open3D-ML<br/>• RandLA-Net / KPConv<br/>github.com/isl-org/Open3D-ML"]
    INF["inference · label stud pts"]
    TR --> P4
    TR --> P5
    P4 --> INF
    P5 --> INF
  end

  subgraph FOU["Foundation / zero-shot ×4 · no stud fine-tune"]
    direction TB
    F6["Point-SAM<br/>• point prompt · ~349 pts<br/>github.com/zyc00/Point-SAM"]
    F7["SAM3D<br/>• ViT-H multi-view · ~7188<br/>github.com/Pointcept/SegmentAnything3D"]
    F8["OpenMask3D<br/>• CLIP ViT-B/32 posed RGB-D<br/>github.com/OpenMask3D/openmask3d"]
    F9["Segment3D<br/>• Mask3D · ~17282<br/>segment3d.github.io"]
  end

  S3 --> GEO
  S3 --> SUP
  S3 --> FOU

  %% --- converge ---
  MASK["stud point mask ×9"]
  G1 --> MASK
  G2 --> MASK
  G3 --> MASK
  INF --> MASK
  F6 --> MASK
  F7 --> MASK
  F8 --> MASK
  F9 --> MASK

  OBB["Stage4 BoxFit<br/>shared Open3D minimal OBB<br/>get_minimal_oriented_bounding_box<br/>open3d_baseline._obb_segments"]
  MASK --> OBB

  SC["Scorecard<br/>P/R · section mm · length mm · angle MAE<br/>paint G/Y/R · ε unlocked → yellow<br/>placeholder ε=0.05° · industry τ≈0.12°"]
  OBB --> SC

  CC[["CloudCompare OUT of bake-off"]]
  style CC fill:transparent,stroke-dasharray: 5 5
```

Rendered still: [images/34-pipeline-master-v2.png](images/34-pipeline-master-v2.png) (via `@mermaid-js/mermaid-cli`). Regenerate with:

```bash
npx -y @mermaid-js/mermaid-cli -i docs/research/diagrams/34-pipeline-master-v2.mmd -o docs/research/images/34-pipeline-master-v2.png -b white -s 3 --size 3200
```

## Named stages

| Stage | Brand | Lock |
| --- | --- | --- |
| 1 | **AxiomForge** | Absolute truth from `synthetic.py`: dressed 2×4 **38.1 × 88.9 mm**, 8 ft ≈ **2438.4 mm**, lean **0°**, perfect mesh/box surface. |
| 2 | **CloudSmith** | Mesh → cloud, **25,666** pts on the bake-off scene. Two experiment dials (for **future** stage sweeps — Stage0 lock unchanged today): **point density / count** ↔ `spacing_m` (stage0 default `0.005`); **Gaussian noise sigma** ↔ `noise_std_m` (stage0 default `0.001` = 1 mm). |
| 3 | **TrueLevel** | Realisticizer. Three *named* error sources; honesty for stage0: **(a)** Skil-class leveler device band **~0.05°** — theoretical / calibrated band, **not injected** into the stage0 cloud; **(b)** human placement error when using a level tool — **not-yet-injected**; **(c)** real lumber surface imperfections vs perfect mesh — **not-yet-injected**. On stage0 data, the only noise present is Stage2 sampling Gaussian. |
| 4 | **BoxFit** | Shared Open3D `PointCloud.get_minimal_oriented_bounding_box()` via `src/openwall_stud/open3d_baseline.py:_obb_segments` (also `poststep.detections_from_clusters`). Lean vs **+Z** (or fitted floor when present); section / length. |

## Class pipes and upstream links

| Pipe | Tool | Role | Upstream |
| --- | --- | --- | --- |
| Geometry | Open3D | Python OBB on whole cloud | [open3d.org](https://www.open3d.org/) |
| Geometry | PCL | Native WSL region-grow, then OBB / cuboid reunite | [pointclouds.org](https://pointclouds.org/) |
| Geometry | pyRANSAC-3D | Sequential cuboid RANSAC (iterative plane-style primitives) | [leomariga/pyRANSAC-3D](https://github.com/leomariga/pyRANSAC-3D) (v0.7.x used in-repo) |
| Supervised | Pointcept PTv3 | 2-class stud head under `artifacts/checkpoints/stud-heads` | [Pointcept/Pointcept](https://github.com/Pointcept/Pointcept) |
| Supervised | Open3D-ML RandLA-Net / KPConv | Same stud-head checkpoint dir | [isl-org/Open3D-ML](https://github.com/isl-org/Open3D-ML) |
| Foundation | Point-SAM | Point prompt; stage0 mask ~349 pts; **not** stud-fine-tuned | [zyc00/Point-SAM](https://github.com/zyc00/Point-SAM) · [OpenReview](https://openreview.net/forum?id=yXCTDhZDh6) |
| Foundation | SAM3D | ViT-H multi-view lift; ~7188; **not** stud-fine-tuned | [Pointcept/SegmentAnything3D](https://github.com/Pointcept/SegmentAnything3D) · [arXiv:2306.03908](https://arxiv.org/abs/2306.03908) |
| Foundation | OpenMask3D | CLIP ViT-B/32 on posed RGB-D; near-full; **not** stud-fine-tuned | [OpenMask3D/openmask3d](https://github.com/OpenMask3D/openmask3d) |
| Foundation | Segment3D | Zero-shot Mask3D; ~17282; **not** stud-fine-tuned | [segment3d.github.io](http://segment3d.github.io) · [arXiv:2312.17232](https://arxiv.org/abs/2312.17232) |

Mask point counts are from stage0 rounds (docs 30 / 32), not new measurements.

### Why keep both supervised heads

Pointcept **PTv3** (transformer) and Open3D-ML **RandLA-Net / KPConv** are different backbones with different failure modes on sparse or partial studs. Both short 2-class stud heads live under `artifacts/checkpoints/stud-heads`. Keep **both** in the bake-off until a later stage shows clear dominance on section / length / lean (and does not regress S1b). Do not drop one on stage0 identity of Stage4 numbers alone — those five full-mask tools already share BoxFit (doc 31).

## Scorecard / paint

| Item | Lock |
| --- | --- |
| Metrics | P/R, section mm, length mm, angle MAE |
| Paint | G/Y/R; **yellow** while device ε is unlocked |
| Placeholder ε | **0.05°** column only |
| Industry τ | **≈0.12°** is in-band context, not paint |
| CloudCompare | **OUT** of the bake-off (doc 27 interactive GUI) |

See also docs [27](27-four-way-tool-classification.md), [30](30-fix-sam3d-openmask3d-stage0.md), [31](31-four-stage-error-table.md), [33](33-obb-and-deformation-research.md).
