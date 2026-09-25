# TruePlank stud detection and lean QA — paper space

Status date: **2026-09-25**. This folder is the publication workspace for automated **stud instance detection** and **lean QA** from LiDAR and other point clouds.

| Name | What it means here |
| --- | --- |
| **BeamWeaver** | Platform. |
| **TruePlank** | Stud QA product: find each vertical stud, fit a tight box, report lean, paint only when a device band exists. |
| **OpenWall** | Engineering name of this repository and of the pipeline under `src/openwall_stud/`. |

This draft is venue-agnostic. It is not formatted for a journal, not uploaded to arXiv, and not sent to a publisher.

## Purpose

Keep one place where a paper can grow without mixing three kinds of statement:

1. **Synthetic bring-up.** The Open3D baseline on generator scenes (curriculum stages 0, 2, and 3). Scorecards exist. They are labeled synthetic.
2. **Engineering plan.** Stages, capture protocol, paint rule, and contender order, as written in [`docs/research/12-stud-seg-design-plan.md`](../../docs/research/12-stud-seg-design-plan.md) and [`docs/research/11-stud-segmentation-algorithm-ranking.md`](../../docs/research/11-stud-segmentation-algorithm-ranking.md).
3. **Field validation.** Empty. No jobsite cloud, no SKIL readings, and no locked device band ε are in this repository.

Read the draft at [`draft/paper.md`](draft/paper.md). Method outline: [`METHODS.md`](METHODS.md). Experiment plan: [`EXPERIMENTS.md`](EXPERIMENTS.md). Bibliography: [`references.bib`](references.bib) and [`RELATED_WORK.md`](RELATED_WORK.md). Validity: [`THREATS_TO_VALIDITY.md`](THREATS_TO_VALIDITY.md). Figure captions: [`figures/CAPTIONS.md`](figures/CAPTIONS.md).

## Status

| Piece | State |
| --- | --- |
| Folder, claim rules, BibTeX skeleton, IMRAD draft | **Draft**, this pass |
| Abstract | **TBD** |
| Synthetic Open3D numbers quoted in the draft | **Copied** from the 2026-09-24 scorecards. Labeled synthetic. |
| Ranks 2–5 (PCL, CloudCompare, Pointcept, Open3D-ML) | **Not run.** Stub scorecards only. |
| One-stud five-finder | **Planned.** Another agent owns that bake-off. This paper does not run it. |
| Stages 1 and 4–7 | **No clouds, no metrics** |
| Realisticized ground truth | **Not defined** in the design documents. Not invented here. |
| QA names Hypothetical / Ideal / Realistic / Absolute | **Not defined** in the design documents. Not adopted as a method. |
| Device band ε | **Unlocked.** Production paint is yellow. |
| Submission | **Out of scope** |

## Contribution-claim candidates

These are candidates for a later abstract. None of them is a field result.

| ID | Candidate claim | What would have to be true first |
| --- | --- | --- |
| C1 | A light-frame stud can be instance-segmented as its own box, with plates peeled and bays left unmerged, then given a long-axis angle against a stored reference. | A real bare-frame cloud with an independent stud count. Synthetic stage 3 is only a bring-up. |
| C2 | Lean QA stays yellow until a measured device-plus-algorithm band ε exists, so a binary green/red cannot outrun the sensor. | A measured ε on the capture path that will actually ship. The 0.05° placeholder in the scorecards is an illustration. |
| C3 | Floor-normal angle and gravity plumb are different references. Replacing the vector is a repaint of the same boxes. | Paired floor-normal and inclinometer (or IMU) readings on the same studs. |
| C4 | Historic-roof cuboid completeness, Schnabel primitives, and indoor mIoU are the wrong score for 2×4 lean. | The bake-off on one shared cloud, including the one-stud five-finder when that cloud exists. |
| C5 | An end-to-end error budget (level, LiDAR, algorithm) can be written beside the paint, with empty terms left empty. | At least one filled term from a real capture. The budget in [`METHODS.md`](METHODS.md) is a blank form. |

Drop a candidate if the experiment does not support it. Do not promote C1–C5 into the abstract from the synthetic table alone.

## Possible venues

Listed so a later choice has a shelf. Listing is not a submission plan and not a claim that the draft matches a call for papers.

| Venue family | Why it is on the shelf | Why it can wait |
| --- | --- | --- |
| Automation in Construction; ASCE Journal of Computing in Civil Engineering | Scan-to-model and construction QA readers | Need a field protocol, not only a synthetic bar |
| ISPRS Annals or a photogrammetry journal | TLS, registration, and error budgets | The sensing survey is already in `docs/research/01-sensing-modalities.md`; the stud-axis budget is still empty |
| Buildings (MDPI) or a similar applied built-environment journal | Timber point-cloud modeling is already published there (Chen et al., 2025) | Easy to blur a methods note into an accuracy claim |
| A vision conference or workshop (CVPR/ICCV workshop, 3DV) | Only if a learned instance head is actually trained | Pointcept is a stub. S3DIS mIoU must stay off the stud table |

Preferred shape until a venue is chosen: a methods-and-protocol paper with a clearly separated synthetic appendix. A short workshop note is possible later. A journal version wants the field arm.

## Authorship placeholder

Legal names are not recorded in this draft. Do not expand a GitHub handle into a name.

| Placeholder | Role in this draft |
| --- | --- |
| **Oz** | Product and engineering direction for BeamWeaver / TruePlank / OpenWall. Corresponding-author decision is open. |
| **Gwench** | Coauthor placeholder. Contribution role is unassigned. |

CRediT roles, affiliations, acknowledgements, and funding stay blank until Oz assigns them. Prior Cursor agents that touched the engineering notes are not authors.

## Ethics

- A green or red stud can be read as a code, safety, or payment decision. The working tolerance is a finish guideline summarized by WoodWorks from the Handbook of Construction Tolerances, derived here to about 0.12°. It is not an IRC plumb clause. Paint stays yellow while ε is unlocked.
- Residential and jobsite clouds can identify a household, a crew, or a street address. Publish coordinates, faces, and raw scans only with a written consent and data note. This draft contains neither.
- Do not capture people in order to collect lumber.
- Synthetic scorecards must keep the word synthetic in the caption, the table note, and the abstract.
- CloudCompare is GPL-3.0 if linked. BIMStruct3D weights, if used later as a control, are CC BY-NC-SA 4.0 on the model card cited in the engineering ranking. Neither belongs inside a closed application by default.
- This folder does not authorize a preprint or a publisher submission.

## Reproducibility

Synthetic bring-up, from the repository root after `pip install -r requirements.txt` (Open3D 0.20.0):

```bash
python scripts/run_stage0_baseline.py
python scripts/render_algo_figures.py
```

A minimal Linux image needs `libegl1` before `import open3d` succeeds. Seeds, spacing, and noise are in [`METHODS.md`](METHODS.md). Quote numbers from `artifacts/scorecards/*.json` and from [`docs/research/13-stud-seg-results-by-day.md`](../../docs/research/13-stud-seg-results-by-day.md). Runtimes are for that process. A re-run may change runtime and, if the code changes, the geometry. When a number changes, add a dated row. Do not silently replace a quoted 2026-09-24 figure.

Field reproducibility is a protocol, not a script: sensor, export format, whether Z is gravity, floor normal if one was fit, level model, printed resolution, and BOT / MID / TOP readings. None of those files exist yet.

## How to extend this folder

1. Keep claim class S (synthetic) and claim class F (field) in separate tables.
2. Add a BibTeX key only after the record is checked (Crossref, the publisher page, or the PDF).
3. Leave a metric null when the scorecard is null.
4. Regenerate figures from `scripts/render_algo_figures.py` or from a new script. Credit the script and the date. Scaffold diagrams for unrun stacks stay labeled scaffold.
