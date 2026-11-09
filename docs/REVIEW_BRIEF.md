# Brief for the adversarial review (to be used in a separate session)

Written for: a reviewer session that has not seen the drafting conversation. Task: find errors in the proofs, the code, the experiments, and the confirmation plan before the plan is frozen and the sealed cohort is opened. Date of the brief: 2026-11-07.
The drafting was done by one AI session (Claude Code) with the student; its own readings do not count as review. A reviewer session is also not an outside review (the research-integrity rules say so); label its notes "in-project reading by a separate AI session". Do not trust the claims below because they are written here; check each against the files.

## 1. What the project claims (development stage)

See docs/CLAIMS_REGISTER_REV2.md (15 claims with status and access) and docs/SEARCH_LOG_REV2.md (what was and was not searched or read). In one paragraph: for a one-way lossy satellite link with a byte quota, a node sends a self-contained error-bounded record and compact "witnesses" (daily extrema, a conductance rate pair); the server gives three-valued threshold decisions (exceeded, not exceeded, undetermined) that are sound under stated assumptions. Development results on USGS 2023 data: witnesses raise certain-correct decisions on hard cases; decision flags beat the method on thresholds fixed at configuration time; the method wins on unanticipated thresholds; an exact allocator did not beat a simple rule (pre-registered criterion not met).

## 2. Files to read, in this order

1. docs/CERTIFICATE_SPEC.md and src/p3/certlang.py: the certificate language, Lemmas 1 and 2, Propositions 1 to 4. Check each proof against the code, including the float padding (1e-9), assumption R (reporting resolution, grid snapping), slotless witnesses, the exact conductance rule, and the rolling mean.
2. docs/FRAME_SPEC_V2.md, src/p3/frame2.py, src/p3/capacity.py: frame version 2 (CRC-16 per message, witness descriptor, hosted witnesses, receiver rules: sanity, corroboration).
3. src/p3/allocate.py and docs/PROTO_J_RESULTS.md: the allocation objective Phi(k_g) + d max(0, Phi(k_R) - Phi(k_g)); the independence error that was found and corrected before results (docs/REVISION2_PLAN.md, 3c correction).
4. src/p3/proto_decision.py, proto_queries.py, proto_joint.py, proto_base.py and their evaluators: the group model (five slots per message, systematic MDS groups, recovery thresholds on the same arrival count), the designs, the decision logic, the metrics.
5. docs/BASELINES2_RESULTS.md, docs/INTEGRITY_RESULTS.md, docs/MUTATION_CHECK_REV2.md.
6. docs/CONFIRM3_PLAN.md, src/p3/confirm3.py, src/data/select_cohort3.py, src/data/prepare_cohort3.py, src/data/freeze3.py: the pre-registration, its code, and the sealing and freeze procedure.
7. docs/REVISION2_PLAN.md: the running log with the pre-registered criteria and every correction, in order.

## 3. What to try to break

Proofs and certificates
- Is Proposition 1 true when readings are exactly on a threshold, when the encoder's own 1e-9 slack is used, or when assumption R is wrong for a site (a reading not a multiple of the stated resolution)? What does a wrong resolution do to a decision?
- The "box model": decisions treat readings as independent within their intervals. Where does the witness constraint (minimum is among the readings) make the box answer wrong or too weak?
- Slotless witnesses: a witness claims the extremum of the uncensored readings. What if every reading of a day is censored, or the minimum equals a censored boundary?
- The conductance rule uses relative change |x_b - x_a| / x_a with a lag of 60 minutes divided by the native step; check day boundaries, missing readings, and the 7DADM window definition (seven consecutive days; unknown history treated as hard).

Codec and integrity
- Receiver rules in frame2.receive: can a CRC-valid message with a forged header or descriptor crash the receiver or slip through? The experiment forged body bytes only; header forgeries are not sampled at scale. Is the claimed "never crashes" true?
- Corroboration: with exactly K accepted messages nothing can be checked; is the stated residual risk the only one? Are there ways to make the encoded blocks of two different days look alike (day modulo 64, K, index)?
- Stage 2 of the integrity study multiplies a measured conditional probability by 2^-16 times the expected number of corrupted messages. Is that valid for the corruption models listed?

Experiments
- Loss draws are shared across designs. Are there places where designs get different information or different luck? The random-day control (randmix) permutes the hardness pattern within a site: does it keep the cost profile?
- The hard-case definitions use the encoder's knowledge of the truth (event state, margins). Is any metric leaking information that a real node would not have (for example, the 7DADM trailing mean of future days)?
- The flags design is modelled at 4.75 values per message although the frame gives 4; the alternative threshold sets were chosen by the analyst. Do these choices bias the comparison, and in which direction?
- The 7DADM band (3 degC) and the unknown-history rule were tuned on development data after a first run fell short. Is the tuning described honestly?
- Statistics: site-clustered percentile bootstrap, pooled day-query means. Is pooling across queries and days the right estimand for the stated hypotheses?

Confirmation plan and sealing
- Is the cohort really unseen? Check selection (metadata only), the exclusion of used sites, the sealing order (checksums written before analysis), and that no script in the confirmation reads values before the freeze.
- Are the thresholds in docs/CONFIRM3_PLAN.md (Section 4) identical to those in src/p3/confirm3.py? Can any hypothesis pass or fail for a reason other than the stated one? Which hypothesis could be passed trivially, and which could never pass?
- Is the freeze procedure (tag, test run, seal verification, checksums) enough to show that the code that ran is the code that was approved?

Claims and priority
- Check every novelty sentence against docs/SEARCH_LOG_REV2.md (what loaded, what did not). Albanese 1996 was not read; official indexes were not searched; several papers were read in part.
- Check that no number in a document was typed from memory: each public number should be traceable to a results file (the generated tables are copied from output; the prose findings were typed and should be audited against them).

## 4. Known weak points (stated by the drafter, not exhaustive)

- The conditional integrity probabilities come from six development sites, random-content forgeries, and independent loss. A first version of the study had a defective forgery function (found by the in-project review of 2026-11-09, which also tightened the receiver); the study was rerun and every quoted number updated (docs/INTEGRITY_RESULTS.md, Correction).
- The exact allocator criterion was not met; the simple rule is presented. The allocator's all-case gain at equal record was found after the fact and is exploratory.
- Several reading levels are partial (see the search log). The related-work matrix states the level for each row.
- The thinnest margin in the pre-registered hypotheses is H4 (record recovered, development -0.080 against a limit of -0.12).
- Everything is trace-driven simulation; there is no satellite or microcontroller measurement.
- The mutation check covers 18 hand-chosen faults in four modules and found six test gaps before it was complete.

## 5. How to run things

From Paper3/ (Windows PC with 3.7 GB RAM: run one heavy job at a time, one worker):
- Tests: python -m pytest tests -q (about 10 minutes).
- Mutation check: python tools/mutation_check.py (about 40 minutes), or with ids: python tools/mutation_check.py results/mutation_scratch M04,M12.
- Development evaluations: src/p3/proto_*_eval.py, src/p3/proto_frontier.py (inputs in results/dev/proto*).
- Rehearsal of the confirmation on development data (not confirmatory): python -I src/p3/confirm3.py <folder with a few development site files> rehearsal3.
- DO NOT run src/p3/confirm3.py with the seal file before the authors freeze the plan, and do not open data/clean/usgs_new3_2024.

## 6. What the review should return

A list of findings, each with: file and line or document section; why it is wrong or weak; a concrete failing case or a check that would expose it; severity (must fix before the freeze, should fix, note). Include findings that did not survive your own attempt to refute them, and say which parts you could not check.
