# Threats to validity

Written for the draft in [`draft/paper.md`](draft/paper.md). Items already realized are marked **open**. Items that would apply only after a field arm are marked **later**.

## Construct validity

**Open. Two different “up” vectors.** Floor-normal angle and gravity plumb answer different questions. A stud square to a tilted slab can look acceptable against the floor and out of plumb against gravity. Stage 0 uses generator +Z because there is no floor. Publishing a single word, “plumb,” for all three references would measure the wrong construct. The draft keeps the reference name on every angle.

**Open. τ is a derived finish guideline.** The working tolerance comes from `atan((1/4 inch) / (10 feet))` applied to the Handbook figure as summarized by WoodWorks (≈ 0.1194°). The same derivation on WoodWorks’s summary of UFGS 1/4 inch in 8 feet is ≈ 0.1492°. The phase-1 matrix also uses 0.15° as a requested lean. Those are three different uses of a similar number: paint band, alternate guideline, scene magnitude. NAHB’s 3/8 inch in 32 inches is a further linear figure and was not adopted as τ. The UFGS PDF was not opened. A reader who treats τ as code is answering a different question than the paper.

**Open. Paint is not yet a decision.** ε is unlocked, so every production color is yellow. Percent-in-band and hypothetical colors at 0.05° can be mistaken for a pass rate. The scorecard stores them in different fields for that reason. The draft repeats the separation.

**Open. “Stud” is an instance, not a semantic pixel.** A merged bay is a miss even if every point is labeled wood. Metrics that reward a single wall plane (Schnabel plane count, coplanar patch merge, S3DIS “wall”) measure another construct. Rank 3 is in the plan as a disagreement check, not as a stud definition.

## Internal validity

**Open. The synthetic bar can be satisfied by the same process that built the cloud.** The generator samples dressed boxes, adds 1 mm Gaussian noise, and the fitter looks for those boxes. Agreement on section and angle shows that the peel, the cluster, and the minimal box are wired up. It does not show that the fitter recovers lumber it did not synthesize.

**Open. One loop of threshold changes.** Open3D `eps` and `min_points` were edited after a failed setting on this generator (`eps` 20 mm, `min_points` 80). The reported pass is after that edit. There is no held-out synthetic distribution.

**Open. Angle on stage 3 is partly the floor fit.** The design note states that a stud generated at 0° shows a few thousandths of a degree once the floor normal is not exactly +Z, because truth is the generator axis expressed in the fitted floor frame. That coupling belongs in the caption of the stage-3 angle.

**Open. Length error is partly the peeler.** The stage-3 bar is 30 mm because the plate peel shortens the stud. A reader who compares length to an uncut 8 ft stick without that sentence will call a designed shortening a failure, or will miss it.

**Open. SKIL agreement rule, first session is paint.** The protocol says to withhold MAE when bottom / middle / top differ by more than the printed resolution. Phase 2 is that session on painted drywall, not on a stud. Both faces span more than the 0.05° display step, so no angle MAE against the level is published. The rule’s strictness on lumber is still untested.

**Later. ε double-counts or omits a term.** If ε is filled from a brochure range specification alone, the paint interval ignores registration, peel, and box fit. If the same noise is both in the points and again in ε, the interval is conservative for a reason that should be written down. The budget form in [`METHODS.md`](METHODS.md) is empty so those choices stay visible.

## External validity

**Open. Object mismatch with the timber literature.** Özkan and Pöchtrager reconstruct historic roof beams. Chen, Jiang, and Xiong fit a small timber specimen and, in the engineering survey’s reading, force cylinders toward global Z. Neither object is a repetitive 2×4 wall at 16 inch centers. Completeness and “within 1°” do not travel.

**Open. Sensor mismatch.** The generator has no beam divergence, no flying pixels, no trajectory drift, and no wood reflectance. Phone LiDAR and a Livox Mid-360 are in the capture plan for detection. The sensing survey’s published specifications do not sit inside τ for those classes. A synthetic angle error of a few hundredths of a degree is not an estimate of error on those sensors.

**Open. Scene mismatch.** Stages 4–7 (openings, a room, a story, a complex frame) have no clouds. IntCDC, cited in the ranking as a negative control, is heavy timber with members that touch, and file Z is not documented there as gravity. It was not re-run for this draft.

**Open. A painted corner is not a stud.** Phase 2 measures two finished faces. Export +Z is not a gravity vector paired to the level. The planes are not registered to the SKIL faces. Open3D plane RANSAC is unseeded, so the third decimal of a degree can move. None of that is class F.

**Later. One stud is not a wall.** E3, when it exists, estimates detection and angle on a single isolated member. Bays, plates, and openings arrive at E4. Generalizing E3 to a house is a separate claim. Phase 2 does not start that ladder.

**Later. Operator and site.** Level placement, scanner height, and how wet or warped the stud is are not in the generator. A single jobsite will not represent a framing crew.

## Statistical conclusion validity

**Open. Scripted scenes, no interval.** The seven-scene table and the 25-scene S1 table are censuses of generator scripts, not samples with a confidence interval. Runtime is one process on one machine (a Linux VM for the early cards, Oz_PC for the sweep and the fine-tune). Re-running can change the third digit of a timer.

**Open. Perfect precision and recall on a designed gap.** With a clear bay and no occlusion, P = 1 and R = 1 on ranks 1, 2, and 6, and on the tuned CloudCompare row, is the expected bring-up outcome. The untuned rank-3 precision of 0.125–0.25 on the same clouds is the disagreement check. The tuned pass (25/25, one box) is still one synthetic stud. The merge keeps that one box and would drop a second stud. It is not a wall segmenter.

**Open. Rank 2 on the 25-scene matrix is not native PCL.** `native_pcl_region_growing` is false. Treating that row as a libpcl measurement would credit a binary that did not run.

**Open. The fine-tune can look perfect on a cloud that is only a stud.** Both models labeled all 25,666 phase-1 points as stud. The 0.004° mean absolute error is the shared minimal box of that cloud. The two floor clouds are a different, still synthetic, result, with larger angle errors and about 20 mm section error.

**Open. Rank 5 validation depends on which batch-norm statistics are used.** `model.eval()` with S3DIS running statistics is not the result recorded from `randlanet_val_corrected.json`.

**Later. Multiple comparisons across finders.** When a real stud exists, six stacks on one cloud can be over-read. Stubs and in-progress tunes stay null.

## Citation and reproducibility threats

**Open. A DOI in the engineering notes was checked and does not match the named authors.** `10.3390/s23041924` resolves to Ntiyakunze and Inoue (2023), not to Bassier. The draft cites Bassier and Vergauwen (2020) at title level and records the collision in [`RELATED_WORK.md`](RELATED_WORK.md).

**Open. Some numbers in the sensing survey were not re-extracted for this draft.** iPhone RMSE figures attributed to Erland and Gaulton (2026), and the Chen et al. (2025) specimen percentages, stay in the engineering notes. The paper names those papers and does not promote the un-re-read digits into a results table.

**Open. DBSCAN pagination** is the standard KDD 1996 citation and was not confirmed from a DOI record in this pass.

**Open. The 2026-09-24 rank 2–5 pictures are scaffolds.** They draw the synthetic stage-3 input and a banner. Using them as outputs would fabricate that day’s run. The 2026-09-25 phase-1 PNGs for ranks 1, 2, 3, and 6 are separate files and are credited as that sweep. Ranks 4 and 5 still have no stud-box figure.

## Ethics as a validity issue

A premature green/red call harms the construct as well as the user: the measured quantity would be “color under an invented ε,” not lean. Withholding the call until ε exists is part of validity, not only a product caution. Jobsite imagery that identifies a household cannot be treated as a public benchmark without consent; that limits external replication and should be planned before E3, not after the cloud is committed.
