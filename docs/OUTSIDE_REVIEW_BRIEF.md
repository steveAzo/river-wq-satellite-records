# Request for an outside review: certified threshold decisions over one-way satellite IoT links

Prepared 2026-11-11 for a reviewer outside the project. The authors (University of Ghana) ask for a critical reading before any preprint or submission (target: Environmental Modelling & Software). No one outside the project has read the work. Two separate AI sessions read the code and plans in-project; that is not a substitute for this review.

## What the paper claims

- Problem: a river sensor node sends a few 23-byte, one-way satellite messages per day; some are lost and the node never learns which. What can the server soundly decide about regulatory thresholds (dissolved oxygen, pH, 7-day temperature maximum, conductance change) from what arrives?
- Method: the node sends an error-bounded record within USGS "excellent" accuracy plus compact witnesses of hard cases (quantised daily extrema, a conductance rate pair), erasure-coded over the day's messages with a CRC-24 per message. The server answers each query with exceeded, not exceeded, or undetermined, and the answers are proved sound under stated assumptions.
- Evidence: trace-driven simulation on USGS records with modelled loss (independent and bursty, 30%). Development on 2023 (38 rivers) and 2024 (31 rivers); one pre-registered confirmation on 35 sealed rivers of 2022, measured on real message bytes.
- Result: all three hypotheses that could fail held. On thresholds nobody configured, the witness design decided 0.18 to 0.23 more hard cases than a node that sends configured decision flags plus its record, and 0.20 to 0.28 more than the record alone, at a cost of 0.03 to 0.08 in whole-record recovery. No certain decision was wrong.

## What the authors already know is weak (please judge whether it is stated well enough)

- The witness design was adopted although its record cost at six messages per day (about 0.08 to 0.09) exceeded the adoption limit the authors had written in advance (0.08). The cost was then tested with a looser pre-registered limit.
- An earlier confirmation of the previous version failed its integrity hypothesis and used a comparator that discarded the record; the method was revised and confirmed again on new data. Both are reported.
- A modelling error in the comparator (flag capacity) was found by an in-project reading before the second freeze and corrected; the benefit results were not affected.
- Only three of seven pre-registered statements can fail; the others are code checks, a known limit, and an analytic bound.
- The flags comparator takes its configured answers from the truth (idealised). The unanticipated thresholds and hardness bands were chosen by the analyst and seen on every development cohort.
- No hardware, no measured channel, simulated loss only; one country, one year per cohort; the reporting resolution (assumption R) is inferred from the record.

## What to read

1. The manuscript: draft4/deliverables/Paper3_draft_v1.0.pdf (34 pages) and Paper3_supplement_v1.0.pdf.
2. If you want the proofs: docs/CERTIFICATE_SPEC.md (Propositions 1 and 2) and docs/FRAME_SPEC_V2.md (frame and receiver).
3. If you want the pre-registration and its history: docs/CONFIRM4_PLAN.md (frozen at git tag confirm4-freeze, record docs/FREEZE4.md), docs/CONFIRM4_PLAN_DRAFT.md (how it changed), docs/REVIEW_FINDINGS_V3.md (the in-project review that changed it).
4. Results: results/confirm4/verdicts4.md and RUN4.log; summary docs/CONFIRM4_RESULTS.md.

## Questions we most want answered

1. Novelty: is the combination (source-side selection of an error-bounded record plus extremum witnesses under a byte quota, with sound three-valued certificates over a one-way lossy link) genuinely new, or is there prior work we missed (priority encoding transmission, PlatoDB/Plato, TREAT, send-on-delta, satellite tag telemetry are cited)?
2. Soundness: do Propositions 1 and 2 hold as stated? Are the assumptions (honest encoder, correct site profile, assumption R, uncorrupted accepted messages) stated where a reader needs them?
3. Fairness of the comparison: is "flags plus record" the right comparator? Is anything else a practitioner would deploy missing?
4. The post-hoc adoption: is the way it is reported acceptable, or does it undermine the confirmation?
5. Relevance: would an agency or modeller use certified decisions on unconfigured thresholds? Are the alternative threshold sets reasonable?
6. Presentation: is the paper readable for Environmental Modelling & Software readers? What should be cut or moved to the supplement?

## How to reproduce (optional)

- Repository: the Paper3 folder of the project repository (ask the authors for access). Python 3.13, numpy 2.3, pandas 2.3, scipy 1.17; run from Paper3/.
- Tests: python -m pytest -q -p no:cacheprovider tests (858 tests; about 5 minutes).
- The confirmation run (about 2.5 hours on a 4 GB laptop): python -I src/p3v3/confirm4.py data/clean/usgs_new4_2022 confirm4 data/clean/usgs_new4_2022.md5. It refuses to start unless the code equals the frozen tag and the data seal verifies, and it refuses to run again once the recorded run has finished. To repeat the analysis independently, copy the cohort folder to a name without "new4" or "2022" (for example data/clean/review_copy) and run python -I src/p3v3/confirm4.py data/clean/review_copy review_rerun; this rehearsal mode runs the same code without the freeze checks and writes to results/review_rerun.
- Tables and figures of the manuscript: python -I -W ignore paper_tools/make_v1.py.

## What we would like back

- A short list of problems ranked by severity (fatal, must fix, should fix, minor), each with where it is and why it matters.
- Your view on questions 1 and 4 above in particular.
- Any claim in the abstract that you think the evidence does not support.
