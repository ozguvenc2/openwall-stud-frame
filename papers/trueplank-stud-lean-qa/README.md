# TruePlank stud detection and lean QA — paper space

Status date: **2026-09-25**.

**Working title.** Instance detection and lean assessment of light-frame wood studs from point clouds.

**Alternate titles** (not used as the H1):

1. Scan-to-BIM lean measurement for light-frame wood studs: instance boxes, a finish tolerance, and a withheld pass/fail.
2. Plumbness of bare wood studs from LiDAR point clouds: six finders, an oriented box, and a yellow paint rule.

| Name | What it means here |
| --- | --- |
| **OpenWall** | The suite. |
| **BeamWeaver** | An OpenWall app. |
| **TruePlank** | An OpenWall app: find each vertical stud, fit a tight box, report lean, paint yellow until a device band exists. This paper is that app’s draft. |

Live draft: [`draft/paper.md`](draft/paper.md). This branch is `cursor/trueplank-phase2-wall-corner-fdf2`, cut from `cursor/trueplank-paper-draft-20c5`.

Parent draft: [https://github.com/ozguvenc2/openwall-stud-frame/pull/21](https://github.com/ozguvenc2/openwall-stud-frame/pull/21) (branch `cursor/trueplank-paper-draft-20c5`). Phase 2 is the pull request opened from this branch onto that paper branch.

Pandoc metadata: [`draft/header.yaml`](draft/header.yaml). Optional PDF note: [`Makefile`](Makefile) (`make note`). No journal class is bundled. This folder is not an arXiv upload and not a publisher submission.

## What to read

| File | Role |
| --- | --- |
| [`draft/paper.md`](draft/paper.md) | Article skeleton: abstract through references |
| [`METHODS.md`](METHODS.md) | Pipeline, six finders, τ and the 0.15° alternate, blank error budget |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | Which class-S runs exist |
| [`RELATED_WORK.md`](RELATED_WORK.md) | How each bib key may be used |
| [`references.bib`](references.bib) | Keys. Unverified entries stay marked |
| [`THREATS_TO_VALIDITY.md`](THREATS_TO_VALIDITY.md) | Construct, internal, external |
| [`figures/CAPTIONS.md`](figures/CAPTIONS.md) | Figure credits |

Source notes for the numbers, in-tree on this branch:

- `docs/research/16-one-stud-five-finder-run.md`
- `docs/research/18-ozpc-ranks4-5-run.md`
- `docs/research/19-phase1-s1-lean-sweep.md`
- `docs/research/20-synthetic-stud-finetune.md`
- `docs/research/22-phase2-wall-corner-field.md`

Cited by branch because they are not in this tree: house-alike hunt on `cursor/house-alike-cloud-hunt-0474` (PR #12); methods shortlist on `cursor/methods-beat-shortlist-e9dc` (PR #14); CloudCompare stud-only tune on `cursor/cc-stud-param-tune-78b7` (PR #22), `docs/research/21-cloudcompare-stud-param-tune.md` and `artifacts/scorecards/phase1_s1_cc_tuned/`.

## Status

| Piece | State |
| --- | --- |
| Title and abstract | **Drafted.** Class-S caveat stays. The abstract also names the phase-2 painted-corner pilot and keeps ε unlocked |
| Authors | **Placeholders** (Oz, Gwench). Legal names unassigned |
| E0 Open3D, seven scenes | **Quoted**, class S, 2026-09-24 |
| Phase 1 S1, 25 × 6 | **Quoted** from doc 19. Ranks 1, 2, 6 pass 25/25. Rank 3 untuned: lean 25/25, stage-0 bars 0/25. Ranks 4 and 5 are controls. Final comparison is Table 8 of the draft |
| CloudCompare stud-only parameter tune | **Quoted** from PR #22. Stage-0 pass 25/25, one box per scene. Untuned row kept |
| Synthetic fine-tune, ranks 4 and 5 | **Quoted** from doc 20, control and fine-tune both in Table 8. Train about 98 s and 237 s. Phase-1 stud boxes 25/25. Floorless limitation stated |
| Class F, ε, SAM 2, native PCL on the 25-scene matrix | **Empty or not run** |
| Phase 2 painted wall corner | **Quoted** from doc 22. Wall-plumb pilot, not class F. Table 9 is the density ladder. Table 10 is SKIL versus cloud lean. ε stays unlocked |
| Bibliography | **Usable draft.** NAHB, UFGS, DBSCAN pagination, RoomPlan, and ARKit remain marked unverified |

## Contribution candidates

Status against the runs is Section 1.2 of the draft. Short form: C1 and C4 are illustrated on class S only. C2 is implemented as yellow paint and is not a measured ε. C3 and C5 still lack a field term.

## Possible venues

Listing is not a submission plan.

| Venue family | Why it is on the shelf | Why it can wait |
| --- | --- | --- |
| Automation in Construction; ASCE Journal of Computing in Civil Engineering | Scan-to-BIM and construction QA | The field arm is empty |
| ISPRS Annals or a photogrammetry journal | TLS and error budgets | The stud-axis budget is still empty |
| Buildings (MDPI) or a similar applied journal | Timber point-cloud modeling already appears there | Easy to blur a methods note into an accuracy claim |

Preferred shape until a venue is chosen: a methods-and-protocol paper with the synthetic tables clearly marked class S.

## Authorship placeholder

| Placeholder | Role in this draft |
| --- | --- |
| **Oz** | Product direction for the OpenWall suite and the BeamWeaver and TruePlank apps. Corresponding-author decision is open. |
| **Gwench** | Coauthor placeholder. Contribution role is unassigned. |

CRediT, affiliations, acknowledgements, and funding stay blank until Oz assigns them.

## Ethics

- Production paint stays yellow while ε is unlocked. τ ≈ 0.12° is a derived finish guideline. The ≈ 0.15° figure is a second derivation from WoodWorks’s UFGS summary, not a code clause and not the paint band.
- This draft contains no committed scan and no photograph. The phase-2 cloud stayed gitignored.
- Synthetic tables keep the class-S label.
- CloudCompare is GPL-3.0 if linked. BIMStruct3D weights are CC BY-NC-SA 4.0. Ultralytics YOLO is AGPL-3.0 in the citation file this bibliography checked. None of those licenses is a reason to ship the component inside a closed application by default.

## Reproducibility

Quote numbers from the research notes and the scorecards named in [`EXPERIMENTS.md`](EXPERIMENTS.md). A re-run that changes a quoted number needs a new dated row.

```bash
python scripts/run_stage0_baseline.py
python scripts/run_phase1_s1_lean_sweep.py
```

The phase-1 sweep and the fine-tune were run on Oz_PC, not on a CPU-only cloud VM. Rank 3 needs `CLOUDCOMPARE_EXE` or an install the discovery order can see. Rank 4 reload needs the gitignored BIMStruct3D cache plus `artifacts/weights/finetune/pointcept_stud_2class.pth`. Rank 5 inference uses `predict_labels` so S3DIS batch-norm averages are not reused. Commands and interpreters are in `docs/research/20-synthetic-stud-finetune.md`.
