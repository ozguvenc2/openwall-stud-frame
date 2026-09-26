# OBB / primitive fitting and deformed-plank modeling

Date (America/Los_Angeles): **2026-09-26**. Writer: **Other**. Survey pass only — no new scorecard, no fabricated metrics, no fake URLs. Confidence is marked per row. Years and venues that were not re-checked against Crossref / official docs on this pass are labeled `surveyed; uncertain`.

Companion docs: [27-four-way-tool-classification.md](27-four-way-tool-classification.md) (live buckets), [30-fix-sam3d-openmask3d-stage0.md](30-fix-sam3d-openmask3d-stage0.md) (shared OBB after mask), [31-four-stage-error-table.md](31-four-stage-error-table.md) (Stage2 noise on minimal OBB), [32-pipeline-master-diagram.md](32-pipeline-master-diagram.md) (MASK → SAME shared minimal-OBB → Stage4). S1b bow probes: [25-ozpc-sam2-s1b.md](25-ozpc-sam2-s1b.md), generator `s1b_bowed_stud` / `s1b_bow_wall` in `src/openwall_stud/synthetic.py`.

## Current path (Stage0 default)

TruePlank / openwall-stud-frame fits each stud cluster with Open3D’s minimal oriented box:

| Step | Code |
| --- | --- |
| Fit | `_obb_segments` in `src/openwall_stud/open3d_baseline.py` calls `PointCloud.get_minimal_oriented_bounding_box()` |
| Shared post-step | `detections_from_clusters` / `score_clusters` in `src/openwall_stud/poststep.py` |
| Long axis | Extent-sorted OBB frame; longest axis → lean angle |
| Lean reference | Fitted floor normal when the scene has a floor/slab; generator **+Z** otherwise (`angle_reference.py`) |
| Paint | Yellow while device ε is unlocked |

**Why not PCA here.** The in-file note on `_obb_segments` states that PCA boxes yaw on a surface-sampled stud and inflate the section; the minimal box matches the point extent. Doc 31 measured Stage2 on the bake-off cloud (`stage0_2x4_lean0.000`, seed 1, 25,666 pts, `spacing_m=0.005`, `noise_std_m=0.001`): section **7.86 mm**, length **6.24 mm**, angle **0.03084°** under that same minimal OBB. That is sampling inflation, not a claim that another fitter is better.

**Honest default.** Keep **minimal OBB as Stage0 default** unless a bake-off alternative beats it on section / length / lean **and** stays robust on S1b bow scenes. This note ranks candidates for that bake-off; it does not replace the shared fitter.

Scene shape this survey assumes: dressed 2×4 surface samples (~38.1 × 88.9 × 2438.4 mm), 1 mm isotropic Gaussian noise, ~5 mm spacing, slender aspect, often one-sided or partial faces in field capture.

---

## TRACK A — Bounding box / primitive fitting

Frontier context ~2023–2026 for deep detectors; classical geometry is older and still the Stage0 stack (doc 27 bucket 1). Ranking below is for **our** stud bake-off, not KITTI / ScanNet mAP.

### Comparison table

| Method | Library / paper | Expected fit on noisy surface-sampled slender studs | Speed class | Partial / occlusion | Confidence |
| --- | --- | --- | --- | --- | --- |
| **Open3D minimal OBB (current)** | Open3D `get_minimal_oriented_bounding_box` / tensor `MINIMAL_APPROX`: hull-triangle frames, pick smallest volume. Docs: [OrientedBoundingBox](http://www.open3d.org/docs/latest/python_api/open3d.geometry.OrientedBoundingBox.html). Related theory: O’Rourke, *Finding minimal enclosing boxes*, Int. J. Comput. Inf. Sci. **1985** (`surveyed`). | Tight on full-surface clusters; Gaussian tails fatten section/length (doc 31). Bow fattens the prism and can fail rigid section bars (doc 25 S1b). | Fast (ms on ~25k pts in stage0 cards) | Encloses visible points only → short/yawed box if faces missing | `known` in-repo; `surveyed` API |
| **PCA-based OBB** | Open3D `get_oriented_bounding_box` / tensor `PCA` (PCA of convex hull). Same Open3D docs. | Code already rejects for Stage0: surface samples bias principal axes → yaw and section inflate. Fine as a warm start, not the scorecard box. | Fastest | Worse under one-sided sampling | `known` (code comment); `surveyed` API |
| **Minimum-volume BB (MVBB)** | Exact: O’Rourke **1985**. Approx: Barequet & Har-Peled, *J. Algorithms* **2001** / SODA 99 ([project page](https://sarielhp.org/p/98/bbox/)). Libs: ApproxMVBB ([gabyx/ApproxMVBB](https://gabyx.github.io/ApproxMVBB/)); Open3D tensor `MINIMAL_JYLANKI` (Jylänki / MathGeoLib-inspired); CGAL `oriented_bounding_box` (Optimal Bounding Box, approx; Chang et al. lineage per [CGAL manual](https://doc.cgal.org/latest/Optimal_bounding_box/index.html)). | Same geometry class as current minimal OBB. A slower “more exact” pass may shave volume on awkward hulls; on our dense noisy stud, gain is likely small vs Stage2 noise. | Medium–slow (exact cubic in hull size; approx / Jylänki slower than PCA) | Same enclosure limits as any OBB | `surveyed` papers/libs |
| **Convex hull** | Open3D / CGAL / scipy.spatial `ConvexHull` | Intermediate, not a stud model. Useful for MVBB input and outlier shells. Does not give lean or dressed section directly. | Fast–medium | Hull collapses to visible side | `surveyed` |
| **RANSAC primitives (planes, cylinders, boxes)** | Open3D RANSAC plane/cylinder; **CGAL** Efficient RANSAC (plane, cylinder, sphere, cone, torus) ([Shape Detection manual](https://doc.cgal.org/latest/Shape_detection/index.html)); **pyRANSAC-3D** v0.7.x cuboid/plane/cylinder ([docs](https://leomariga.github.io/pyRANSAC-3D/), bake-off rank 6); **PCL** sample consensus | Planes → face assembly (our PCL path). Cuboid RANSAC (pyRANSAC-3D) already a geometry-first peer. Cylinders are a poor stud prior (rectangular section). Multi-face planes need a merge step or they over-segment (CloudCompare archive). | Medium (depends on iterations) | Strong: inliers from visible faces; weak if threshold wrong | `known` for pyRANSAC/Open3D/PCL in-repo; `surveyed` CGAL |
| **J-Linkage (and related)** | Toldo & Fusiello, *Robust Multiple Structures Estimation with J-Linkage*, **ECCV 2008**. Soft variant: T-Linkage (Magri & Fusiello lineage, `surveyed; uncertain` exact venue on this pass). | Preference-set clustering for multiple planes/lines without fixing model count. Useful if a stud splits into several face hypotheses; not a one-shot stud box. | Medium–slow | Designed for multi-structure + outliers | `surveyed` |
| **Region growing + OBB (our PCL path)** | PCL `RegionGrowing` + adjacency cuboid (`region_grow.py` / `contenders/pcl_region_grow.py`); NumPy smoothness fallback | Geometry-first bucket 1 (doc 27). Grows faces, then reunites touching faces into a cuboid. Axis not forced to Z. Already measured on stage0 / S1b. | Medium (native PCL seconds on stage0 cards; NumPy port differs) | Face split under loose/tight thresholds; wall scenes can merge badly (doc 25) | `known` |
| **Deep OBB / cuboid detectors** | **3D-BoNet** — Yang et al., NeurIPS **2019** (instance boxes + masks). **VoteNet** — Qi et al., ICCV **2019**; **BoxNet** = VoteNet’s no-vote baseline in that paper. **V-DETR** — Shen et al., ICLR **2024** (vertex-relative PE). **Uni3DETR** — Wang et al., NeurIPS **2023**. Outdoor DETR peers (SEED / CenterFormer, etc.) are KITTI/Waymo-centric — weak transfer to bare studs without labels. | Indoor detectors propose furniture-scale boxes; no wood-stud class in ScanNet vocabularies (same issue as doc 26). Would need synthetic fine-tune and still emit a rigid prism — same limitation as minimal OBB on bows. | GPU, slower than classical per scene unless batched | Learned amodal completion can hallucinate occluded extent (helpful or harmful for metrology) | `surveyed` papers; fit on studs `unverified` |

Speed classes are relative (fast ≪ 0.1 s classical on ~25k pts; medium ~0.1–few s; slow = heavier combinatorial / GPU train-serve). They are not new wall-clock measurements from this pass.

### Top 5 alternatives (bake-off ranked)

Ranked for **TruePlank stud clusters** (noisy dressed 2×4, shared mask → box), not generic 3D detection leaderboards. Current minimal OBB stays the control, not “alternative #0”.

| Rank | Alternative | When it beats minimal OBB |
| --- | --- | --- |
| **1** | **Open3D tensor `MINIMAL_JYLANKI` (or CGAL / ApproxMVBB MVBB)** | Hull is awkward (clipped ends, plate stubs, mild bow) and approx-minimal leaves volume on the table; you can afford ~10× box time. Unlikely to beat Stage2 noise on clean stage0. |
| **2** | **pyRANSAC-3D cuboid (already bucket 1)** | Clutter or multi-primitive scenes where a global OBB on a dirty cluster over-covers; inlier cuboid rejects outliers better than enclosure. Already on the ladder — use as the robust-fit peer, not a second shared scorer until it wins head-to-head. |
| **3** | **Region-grow faces → cuboid (PCL / NumPy path)** | Need face evidence before a box (painted studs, one-sided scans). Beats whole-cluster OBB when DBSCAN merges a stud with a plate strip that a smoothness grow would peel. |
| **4** | **Multi-plane RANSAC + J-Linkage (or sequential plane peel) → assembled OBB** | Several coplanar patches / near-parallel faces; single OBB yaws. J-Linkage helps when model count is unknown. Heavier glue code. |
| **5** | **VoteNet / V-DETR-style head fine-tuned on synth studs** | Instance proposal in cluttered rooms where clustering fails. Beats classical only after labeled train; still a rigid box — not a bow meter. Outdoor DETR/SEED heads stay lower priority. |

**Not in the top 5 for our bake-off:** pure PCA OBB (already demoted in code); cylinder RANSAC as the stud model; CloudCompare interactive RANSAC-SD (doc 27 bucket 4); generic ScanNet detectors with no stud fine-tune.

---

## TRACK B — Non-primitive / deformed plank modeling

Goal: customer insight **beyond a single lean angle** — bow, twist, and surface distortion on a long slender stud. Ties to existing S1b scenes: parabolic midspan offset with ends on the chord (`_apply_bow` in `synthetic.py`). Doc 25 already shows rigid OBB/section bars fail or fatten on bows while reporting the **chord** angle.

### Comparison table

| Method | Library / paper | What it quantifies | Fit on S1b-style bow / twist | Speed / deps | Confidence |
| --- | --- | --- | --- | --- | --- |
| **Centerline spline / polynomial / NURBS** | scipy (`splprep` / `UnivariateSpline`); CGAL / custom B-splines; OpenCascade (OCCT) curve/face if a CAD solid is required. Timber-beam B-spline deformation analysis: e.g. laser-scan wooden dome curve-to-curve work (KIT open access; `surveyed`). Beam centroid-axis extraction from clouds (infrastructure / SHM literature, `surveyed`). | Midspan bow amplitude, camber profile along length, out-of-plane vs in-plane | Natural match to S1b parabolic generator; twist needs section frames, not only the centerline | Fast once sliced; OCCT heavier | `surveyed` |
| **Principal-axis deviation profiles** | NumPy/scipy on sliding windows or slices along PCA / OBB long axis | Per-station lateral offset from the chord; RMS bow; local lean | Cheap S1b metric; sensitive to missing faces | Fast | `surveyed` (standard engineering practice) |
| **ICP / registration to CAD reference** | Open3D ICP / colored ICP; PCL ICP; CloudCompare (interactive) | Residual field vs nominal 2×4 solid or mesh | Good for as-built vs as-designed if pose is locked; lean+bow couple into one residual unless decomposed | Medium | `surveyed` |
| **Deformation fields / Scan-vs-BIM** | Research scan-vs-BIM / as-built validation pipelines (ITcon and ISPRS FEM-from-LiDAR examples, `surveyed`); ETH beam-system reconstruction toolkit ([cea-ethz/beam_system_reconstruction](https://github.com/cea-ethz/beam_system_reconstruction), Open3D-based, `surveyed`) | Component-level deviation maps | Strong product story; needs a design model and registration quality | Medium–slow | `surveyed` |
| **Section tracking (twist)** | Slice → 2D OBB / PCA of each slice → heading along length; FEM/LiDAR twist from flange height difference (ISPRS Archives XLII-2, 2018, `surveyed`) | Twist angle profile | Required for “propeller” studs; S1b today is bend-only | Medium | `surveyed` |

### Track B ranked recommendations

| Priority | Candidate | Why for TruePlank |
| --- | --- | --- |
| **B1** | **Slice → centroid / 2D section → polynomial or cubic spline centerline; report midspan bow vs chord** | Directly mirrors `s1b_bowed_stud`. scipy + NumPy only. Keeps Stage0 lean from the chord (current OBB long axis) and adds a bow amplitude the rigid bars cannot see. |
| **B2** | **Principal-axis (or chord) deviation profile + RMS** | Same slices, cheaper than NURBS. Good debug plot for customers and for S1b scorecards. |
| **B3** | **Point-to-CAD ICP residual after rigid align to nominal dressed prism** | Open3D already in-stack. Separates “out of plumb” (lean) from “warped surface” if you subtract the best rigid pose. |
| **B4** | **Per-slice heading → twist profile** | Next step after bend; not in S1b generator yet. |
| **B5** | **Full Scan-vs-BIM / OCCT solid** | Later product tier when a wall BIM exists; out of Stage0 scope. |

---

## When to adopt (beyond rectangular prisms)

| Stay on minimal OBB prism | Move beyond the prism |
| --- | --- |
| Stage0–Stage3 rigid lean curriculum; all-nine shared scorer (docs 30–32) | S1b or field studs where section error is bow fattening, not finder error |
| Single lean vs floor / +Z paint is the product ask | Customer asks for bow, crown, twist, or “which face is cupped” |
| Cluster is complete enough that Stage2-scale noise dominates box choice | One-sided scans: prefer face RANSAC / region-grow before any OBB |
| No CAD wall model | As-built vs plate layout / BIM residual maps |

**Adoption rule.** Do not replace `_obb_segments` in the shared post-step until an alternative wins a recorded head-to-head on stage0 **and** does not regress S1b chord lean. Ship Track B metrics as **extra fields** on the scorecard (bow_mm, twist_deg_per_m) beside the existing prism lean.

---

## Links into the pipeline

```text
finder / foundation mask
        │
        ▼
poststep.detections_from_clusters
        │
        ▼
open3d_baseline._obb_segments
        │  PointCloud.get_minimal_oriented_bounding_box()
        ▼
long axis → lean vs +Z or floor_normal → paint (yellow if ε unlocked)
```

Doc 32 draws this as **MASK → SAME shared minimal-OBB fitter → Stage4 scorecard**. Track A alternatives are candidate swaps for that shared node. Track B sits **after** (or beside) it and does not remove lean paint.

---

## Status summary

| Claim | Status |
| --- | --- |
| Current fitter is Open3D minimal OBB via `_obb_segments` / `poststep` | `known` |
| PCA OBB demoted for surface-sampled studs | `known` (code + this survey) |
| Stage2 noise numbers on minimal OBB | `known` (doc 31 measured) |
| S1b rigid bars ≠ bow amplitude; angle is chord | `known` (doc 25 / synthetic.py) |
| Top-5 classical/deep alternatives above | `surveyed` ranking; not measured this pass |
| Track B slice-spline as first bow metric | `surveyed` recommendation; not implemented |
| Exact paper years/venues marked uncertain | `surveyed; uncertain` where noted |

**Bottom line.** Keep minimal OBB as Stage0 default. Bake-off Track A peers in order: tighter MVBB → pyRANSAC cuboid → region-grow cuboid → multi-plane/J-Linkage assembly → fine-tuned indoor detector. For deformation, start with slice centerline bow (+ deviation profile), then ICP-to-CAD, then twist.
