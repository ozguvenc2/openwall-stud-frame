# Threats to validity

Written for the draft in [`draft/paper.md`](draft/paper.md). Items already realized are marked **open**. Items that would apply only after a field arm are marked **later**.

## Construct validity

**Open. Two different “up” vectors.** Floor-normal angle and gravity plumb answer different questions. A stud square to a tilted slab can look acceptable against the floor and out of plumb against gravity. Stage 0 uses generator +Z because there is no floor. Publishing a single word, “plumb,” for all three references would measure the wrong construct. The draft keeps the reference name on every angle.

**Open. τ is a derived finish guideline.** The working tolerance comes from `atan((1/4 inch) / (10 feet))` applied to the Handbook figure as summarized by WoodWorks. NAHB’s 3/8 inch in 32 inches and the UFGS 1/4 inch in 8 feet are different angles. The IRC reading in the repository notes did not find a general wood-stud plumb clause. A reader who treats τ as code is answering a different question than the paper.

**Open. Paint is not yet a decision.** ε is unlocked, so every production color is yellow. Percent-in-band and hypothetical colors at 0.05° can be mistaken for a pass rate. The scorecard stores them in different fields for that reason. The draft repeats the separation.

**Open. “Stud” is an instance, not a semantic pixel.** A merged bay is a miss even if every point is labeled wood. Metrics that reward a single wall plane (Schnabel plane count, coplanar patch merge, S3DIS “wall”) measure another construct. Rank 3 is in the plan as a disagreement check, not as a stud definition.

## Internal validity

**Open. The synthetic bar can be satisfied by the same process that built the cloud.** The generator samples dressed boxes, adds 1 mm Gaussian noise, and the fitter looks for those boxes. Agreement on section and angle shows that the peel, the cluster, and the minimal box are wired up. It does not show that the fitter recovers lumber it did not synthesize.

**Open. One loop of threshold changes.** Open3D `eps` and `min_points` were edited after a failed setting on this generator (`eps` 20 mm, `min_points` 80). The reported pass is after that edit. There is no held-out synthetic distribution.

**Open. Angle on stage 3 is partly the floor fit.** The design note states that a stud generated at 0° shows a few thousandths of a degree once the floor normal is not exactly +Z, because truth is the generator axis expressed in the fitted floor frame. That coupling belongs in the caption of the stage-3 angle.

**Open. Length error is partly the peeler.** The stage-3 bar is 30 mm because the plate peel shortens the stud. A reader who compares length to an uncut 8 ft stick without that sentence will call a designed shortening a failure, or will miss it.

**Later. SKIL agreement rule is untested.** The protocol says to withhold MAE when BOT / MID / TOP differ by more than the printed resolution. No session has shown whether that rule is too strict or too loose. The sentence stands until a session exists.

**Later. ε double-counts or omits a term.** If ε is filled from a brochure range specification alone, the paint interval ignores registration, peel, and box fit. If the same noise is both in the points and again in ε, the interval is conservative for a reason that should be written down. The budget form in [`METHODS.md`](METHODS.md) is empty so those choices stay visible.

## External validity

**Open. Object mismatch with the timber literature.** Özkan and Pöchtrager reconstruct historic roof beams. Chen, Jiang, and Xiong fit a small timber specimen and, in the engineering survey’s reading, force cylinders toward global Z. Neither object is a repetitive 2×4 wall at 16 inch centers. Completeness and “within 1°” do not travel.

**Open. Sensor mismatch.** The generator has no beam divergence, no flying pixels, no trajectory drift, and no wood reflectance. Phone LiDAR and a Livox Mid-360 are in the capture plan for detection. The sensing survey’s published specifications do not sit inside τ for those classes. A synthetic angle error of a few hundredths of a degree is not an estimate of error on those sensors.

**Open. Scene mismatch.** Stages 4–7 (openings, a room, a story, a complex frame) have no clouds. IntCDC, cited in the ranking as a negative control, is heavy timber with members that touch, and file Z is not documented there as gravity. It was not re-run for this draft.

**Later. One stud is not a wall.** E3, when it exists, estimates detection and angle on a single isolated member. Bays, plates, and openings arrive at E4. Generalizing E3 to a house is a separate claim.

**Later. Operator and site.** Level placement, scanner height, and how wet or warped the stud is are not in the generator. A single jobsite will not represent a framing crew.

## Statistical conclusion validity

**Open. Seven scenes, one algorithm, no interval.** The synthetic table is a census of the scripted scenes, not a sample with a confidence interval. Runtime is one process. Re-running the script can change the third digit of a timer without changing the scientific claim.

**Open. Perfect precision and recall on a designed gap.** With a clear bay and no occlusion, P = 1 and R = 1 is the expected bring-up outcome. It has no standard error worth reporting, and it will not survive contact with a merged cluster.

**Later. Multiple comparisons across five finders.** When E3 runs, five stacks on one stud can be over-read. The plan’s rule is one shared cloud and one scorecard schema, with stubs left null. A winner picked from nulls is not a result.

## Citation and reproducibility threats

**Open. A DOI in the engineering notes was checked and does not match the named authors.** `10.3390/s23041924` resolves to Ntiyakunze and Inoue (2023), not to Bassier. The draft cites Bassier and Vergauwen (2020) at title level and records the collision in [`RELATED_WORK.md`](RELATED_WORK.md).

**Open. Some numbers in the sensing survey were not re-extracted for this draft.** iPhone RMSE figures attributed to Erland and Gaulton (2026), and the Chen et al. (2025) specimen percentages, stay in the engineering notes. The paper names those papers and does not promote the un-re-read digits into a results table.

**Open. DBSCAN pagination** is the standard KDD 1996 citation and was not confirmed from a DOI record in this pass.

**Open. Figures for ranks 2–5 are scaffolds.** They draw the synthetic stage-3 input and a banner. Using them as outputs would fabricate a run.

## Ethics as a validity issue

A premature green/red call harms the construct as well as the user: the measured quantity would be “color under an invented ε,” not lean. Withholding the call until ε exists is part of validity, not only a product caution. Jobsite imagery that identifies a household cannot be treated as a public benchmark without consent; that limits external replication and should be planned before E3, not after the cloud is committed.
