# Review findings for Paper 3 (in-project reading by a separate AI session)

Date: 2026-11-09. Scope: docs/REVIEW_BRIEF.md (code, proofs, experiments, confirmation plan), then the manuscript draft (draft3/main.tex and its sections, tables, and figures). Label: in-project reading by a separate AI session. It is not an outside review, and the drafting session's own readings are not counted.
State when reviewed: the confirmatory run had finished (2026-11-09, 16:08, no restart), docs/CONFIRM3_RESULTS.md existed, and the manuscript draft v0.5 existed. The brief asked for findings before the freeze. This review came after the run, so no finding below changes a confirmatory result. Each finding is therefore labelled by what it changes now:

- Fix in text: a statement in a document or the manuscript is wrong, incomplete, or misleading, and the text should change.
- Report as limit: the evidence is weaker than it reads and the limit should be stated.
- Note: low consequence, or a check that held.

Nothing in the repository was edited by this review. Proposed replacement text is in docs/REVIEW_PROPOSED_TEXT_2026-11-09.md.

## A. Findings on the code, the experiments, and the confirmation

### A1. H8 failed for structural reasons that the specification does not describe (Fix in text)

Where: docs/FRAME_SPEC_V2.md Section 5 (threat table), docs/CONFIRM3_RESULTS.md Section 3, manuscript Section 5.4 and Discussion.
What: the specification says a false certificate "needs that message to be used with no corroborating message (N = K exactly, or k_w copies...)". The forgery table of the confirmation (results/confirm3/robust2_stage1.csv, receiver "CRC + sanity + corroboration", record only) shows three classes of days, not one:

| Class (accepted messages N, needed K) | Q = 6 share of the false rate | Q = 12 share of the false rate | False share on days of that class |
|---|---|---|---|
| N = K | 58% (0.0268 of 0.0463) | 23% (0.0014 of 0.0061) | 0.26 (Q = 6), 0.18 (Q = 12) |
| N < K, partial systematic use, nothing to compare | 24% (0.0110) | 41% (0.0025) | 0.17 (Q = 6), 0.19 (Q = 12) |
| N > need but no corroboration possible (need = 1 and the block was not rejected) | 18% (0.0085) | 36% (0.0022) | 0.051 (Q = 6), 0.016 (Q = 12) among days with need = 1 |

- The third class is an inference. Every false certificate among days with extra messages lies in blocks with need = 1, and only there does corroboration fail to reject (about 10% of such days at Q = 6). A coded block with K = 1 consists of identical copies and always rejects a mismatch, so the unrejected blocks are most likely uncoded days whose record exceeds the quota (K > Q). I did not confirm K from the plan files, to avoid opening cohort-derived data further. A check that settles it: compute K per day from the plan pickles and cross-tabulate.
- Why development missed it: the six development sites had 10 days with N < K at Q = 12 (0.06% of rows) against 401 (1.3%) in the cohort, and mean need 2.14 against 2.55 (maximum 8 against 12). The pre-registered Q = 12 limits were calibrated on a sample that did not contain the dominant failure mode.
- The results write-up calls CRC-24 "the obvious remedy". H8 is conditional on a CRC-valid forgery, so a longer CRC does not change the metric. It only lowers the unconditional rate (256-fold, by the same model). A remedy for the conditional share has to add corroboration for days with N <= K and for oversize days.
Severity: must fix in the text. The failure itself stands as reported.

### A2. The decision-flags comparator throws the record away (Fix in text)

Where: src/p3/proto_base.py lines 237 to 240; docs/BASELINES2_RESULTS.md; manuscript Abstract, Section 5.2 (H5 and H9), Discussion, Conclusion.
What: the flags design decides from the flags alone. When the whole record arrives, it is not used. At the unanticipated thresholds the flags design therefore decides less than the record alone (independent loss, Q = 6: flags 0.275, record only 0.546; Gilbert: 0.264 and 0.460).
Consequences:
- H5 first half (3b rule minus flags, +0.531 and +0.441) mostly measures that the comparator ignores a record it holds. The fair figure for "witnesses against a node that uses its record" is the second half of H5 (3b rule minus record only, +0.260 and +0.245).
- The headline for hybrid 1 ("added 0.29 to 0.36 on thresholds that nobody configured") is the same effect. Hybrid 1 minus record only, from the pooled levels in results/confirm3/verdicts3.md (point differences, no interval): 0.629 - 0.546 = +0.083 under independent loss and 0.557 - 0.460 = +0.097 under Gilbert loss. That is the size attributable to the hosted witnesses and the flags together, over a node that uses what it recovers. It is still positive and still worth reporting.
- No design "flags plus record certificate without witnesses" exists, so the added value of the hosted witnesses over such a node was not measured directly.
Severity: must fix in text.

### A3. H7 and the configured and record clauses of H9 hold by construction (Report as limit)

Where: src/p3/proto_base.py lines 243 to 252 (hybrid 1 merges the flag decision whenever the certificate is undetermined and any message arrived), results/confirm3/verdicts3.md.
What:
- H7 (flags minus 3b rule at configured thresholds, lower bound above 0): flags are correct whenever one message arrives (0.999), so H7 could fail only if the 3b rule were nearly perfect. It carries no information beyond the descriptive level.
- H9, configured hard-case decisions and record recovered, lower bounds at least -0.01: hybrid 1 and flags have the same capacity and the same flag fallback, so both contrasts are exactly +0.000 (0.000 to 0.000). Only the unanticipated-threshold clause (limit 0.20) is informative.
- H1 cannot fail through assumption R (stated in the plan, Section 3a).
- H6 passed with large margins on record recovery, so it is a weak test.
The headline "eight of nine held" counts H7 and most of H9 as support.
Severity: should report as a limit in the paper.

### A4. The adopted design was not tested at the byte level, and the simulation does not use the bytes (Report as limit)

Where: src/p3/confirm3.py lines 56 to 76 and 262 to 266; src/p3/robust2.py lines 82 to 84 and 98; src/p3/proto_base.py lines 56 to 87; src/p3/frame2.py (no flags field).
What:
- The H1 round trip uses perfect delivery (all Q messages), covers record only and a layered group of four witnesses (DOmin, pHmin, pHmax, Tmax), and does not cover hosted witnesses (the mechanism of hybrid 1), the conductance pair codes (ECa and ECb), flags, or decoding from a subset of messages. Hosted witnesses have one unit test (tests/test_frame2.py line 77).
- A silent skip exists (`except ValueError: continue`, confirm3.py lines 66 and 67). It did not act in this run: 30,285 blocks equals 3 x 10,095 days exactly.
- H8 covers record only and layered k_w = 1 and 2, not hosted witnesses or flags. Flags, the adopted hybrid's integrity-relevant field, have no byte-level representation at all; one forged message with a wrong flag byte could set a flag decision with no corroboration (flags are 8 bits in every message in the model only).
- All design comparisons come from an abstract slot model (five slots per message, MDS group recovery), not from frame bytes. The model gives flags 4.75 values per message against the frame's 4. The direction of that bias is stated for H4 and H7 in the plan, but it also inflates the spare room in which hybrid 1 hosts witnesses (src/p3/proto_base.py, spare_f), so it favours hybrid 1 on the H9 alternative-threshold contrast (lower bound 0.248 against a limit of 0.20). The magnitude is unmeasured. A sensitivity run of hybrid 1 only, with the flag capacity set to 4 in a scratch copy, would measure it.
- The experiments use slotted witnesses (src/p3/proto_base.py lines 74 to 79; src/p3/proto_joint.py lines 105 to 112), while the frame carries slotless ones. tests/test_certlang.py line 263 shows equality only for the witness's own query. A slotted min witness also pins one reading's upper end, which can matter for the opposite query when only part of a witness group arrives.
Severity: should report as limit.

### A5. Receiver rules: "never crashes" held in my test, with caveats (Note, one Fix)

- Test: 12,000 calls to `frame2.receive` (6,000 random blocks, with and without corroboration) in which one to three messages were replaced by random bytes anywhere (header, body, or both) with the CRC recomputed. No exception escaped, and the slowest call took 0.08 s. Script: C:\Users\User\AppData\Local\Temp\claude\68e606a9f8e1c1c5\b1b087f8-364d-4100-9408-6908a83b7963\scratchpad\review_checks.py.
- The except clause names ValueError, IndexError, KeyError, and ZeroDivisionError only, and `_sanity` runs outside the try block. The fuzz found no gap, but a TypeError, OverflowError, or similar would crash the receiver.
- The sanity rule rejects saturated codes in witnesses but not in record values. A forged record value with code 0 or 8191 marks a reading as censored and removes it from every decision. The forgery study cannot count this as a false certificate, because it counts readings certified outside tolerance and witness codes that differ from the truth, not wrong decisions.
- Decision layer: `max_bounds` and `min_bounds` (src/p3/certlang.py lines 190 to 208) raise ValueError when every reading is flagged censored (verified). `exceeds_below` and `exceeds_above` guard this case. It is reachable only by a forged record that covers every slot.
Severity: note. Replacing the except clause by `except Exception` and guarding `min_bounds` and `max_bounds` would be a post-freeze change and would need a new, non-confirmatory version.

### A6. Integrity study: model scope (Report as limit)

- Forgeries change body bytes only (src/p3/robust2.py line 60). A natural corruption that passes the CRC changes the header with probability about 3 in 23. A lone message with a forged header (index, K, descriptor) is not sampled. With corroboration, header forgeries reject the block when accepted messages disagree, so the omission probably errs toward safety, but for N <= K there is nothing to compare.
- "False" counts readings certified outside tolerance and witness codes that differ from the truth. It is not a wrong decision. A forged saturated code (see A5) is invisible to it.
- Stage 2 multiplies the conditional share by 2^-16 times the expected number of corrupted messages. For random-looking corruption and for bursts of up to 16 bits this is an upper bound, as stated. It is not valid for structured error patterns (the CCITT polynomial has undetected patterns of weight 4) or for an adversary. Stage 2 was not part of the confirmation.
- Only independent loss 0.3 was used in the forgery study.

### A7. Seed collision (Note)

Sites 03293500 and 04193500 give the same `site_number(name) % 100000` (93500). They receive identical random streams for loss draws and for the random-day permutation (src/p3/proto_base.py lines 181 to 183, and every other prototype), at both Q. The effect is a slight dependence between two of 31 sites in the clustered bootstrap, and it is negligible. Found from file names only.

### A8. The freeze does not pin the runtime environment (Report as limit)

- src/p3/proto_queries.py lines 36 to 38 read P3_TBAND and P3_UNKNOWN (the 7DADM band and the unknown-history rule, the two values tuned on development data). src/p3/proto_base.py line 167 reads P3_MAXDAYS (truncates days). confirm3.py passes os.environ to its children, and `python -I` does not ignore these names.
- The run log records none of them, and docs/FREEZE3.md hashes files only. Python 3.13 appears in the log, but numpy and pandas versions are recorded nowhere.
- What I could check: the round-trip count (3 x 10,095) shows full years, so P3_MAXDAYS was not set. P3_TBAND and P3_UNKNOWN cannot be confirmed from the outputs. The current shell has none, but that is not the shell of the launch.
- Process: the tag confirm3-freeze was created on commit a217e46 (12:33) and docs/FREEZE3.md was written at 12:41, when the run started. FREEZE3.md was first committed at 16:57, after the run. The plan (Section 6, step 2) says the authors commit the freeze record before the run. The checksums were verified by the runner, so the freeze worked, but git history alone does not show that the record existed before the data were opened.
Severity: report in the run record and in the manuscript's procedure section.

### A9. Estimand and control (Note, Report as limit for the first)

- Hard-case decisions pool DO, pH, conductance, and 7DADM day-queries, weighted by how many hard cases each has. A hypothesis can pass because of one query type. A per-kind table from the existing result files would show whether the contrasts agree. It would be descriptive, with no verdict.
- The random-day control permutes the hardness pattern across days within a site but keeps each day's record length. Event days tend to have longer records, so H3 mixes the value of targeting with a mismatch between hardness and record size.
- Checked and held: loss draws are shared across designs (masks are drawn before the design loop and the random stream does not depend on the design list); hardness uses only encoder-known truth; the 7DADM trailing mean uses the current and the previous six days only (no future days); hardness at the alternative thresholds is not used by the allocation.

### A10. Proofs and certificates

- Proposition 1, censored readings (Fix in text, Note): the proof says that a censored reading unknown to the server "is not in the domain of the truth". That is not an argument about the decision, because a rule such as "some hi(t) < theta" could use an interval that belongs to a reading outside the truth domain. For the threshold queries the claim is true, because the piecewise-linear reconstruction at an unflagged censored position lies inside the range of the neighbouring kept values, but this argument is not written down. For the conductance chain rule and the daily maxima of the 7DADM it is not shown. The test test_censored_reading_is_outside_every_decision is one example.
- Readings exactly on a threshold (held): the 1e-9 padding and the snapping tolerance of 1e-6 grid units only widen intervals. With assumption R, a reading exactly at the threshold becomes decidable and the decision is correct. I also checked exact 10% pairs on an integer grid up to 5000 against the code's test (1 + frac) x lo >= hi: no failure.
- Wrong resolution (known): unsound. After snapping, an interval can become empty (lo above hi) without any flag. That inconsistency could be used to reject assumption R, and it is not used.
- Box model (held, as documented): Proposition 2's correction stands, and the box answer is too weak, never wrong, with a witness. The counterexample is in tests/test_review_fixes.py.
- Documentation mismatch (Note): the docstring of `rolling_mean_decision` says information-free days give (-inf, inf), while the code and the specification use the base range.
- Day-association (Note): a message delayed by 32 days or more is mapped to the wrong day by the modulo-64 unwrapping and is CRC-valid, so no integrity layer catches it. This is outside the stated scope.

### A11. Cohort, seal, and freeze (held)

- Selection read qualifier counts only (src/data/select_new_cohort.py `approved_days`; results/confirm3/usgs_quality.json has counts and timestamps, no values). The exclusion list covers usgs, usgs_2024, usgs_new2024, and the confirm2 selection.
- The log shows `freeze verified against tag confirm3-freeze`, `31/31 checksums OK`, and 31 sites in the analysis population. `git diff confirm3-freeze -- src/p3 src/data tests tools` is empty. The only differences from the tag are the later src/paper files, which are not method files.
- The thresholds in src/p3/confirm3.py equal those of docs/CONFIRM3_PLAN.md Section 4, including the H8 limits in the order record Q = 6, record Q = 12, layered Q = 6, layered Q = 12. The H8 numbers in the verdicts reproduce from results/confirm3/robust2_stage1.csv.
- The development values in the plan trace to docs/BASELINES2_RESULTS.md by subtraction (for example 0.968 - 0.677 = +0.291, 0.825 - 0.905 = -0.080, 0.783 - 0.573 = +0.210). They are derived, not printed verbatim in any results file.
- The 7DADM tuning is described honestly in docs/REVISION2_PLAN.md (lines 89 to 91: rule stated before the sensitivity run, no band met it, the unknown-history change stated before the rerun, band 3 chosen by the stated rule and labelled as tuned on development data).

### A12. Document consistency (Fix in text)

- Albanese 1996: docs/REVIEW_BRIEF.md says it was not read, docs/HANDOFF_2026-11-09.md (item 4) says the user still has to obtain it, docs/SEARCH_LOG_REV2.md (edited 18:02) says it was obtained and read in part, and the file papers/pdf/Priority_encoding_transmission.pdf exists (17:00). Reconcile.
- docs/CLAIMS_REGISTER_REV2.md items 12 and 13 still carry the development integrity numbers (2.7% and 0.04% at Q = 12 for record only). The confirmation gave 4.6% and 0.61%. Update before any text quotes them.
- docs/HYBRID_RESULTS.md and the manuscript say the 4.75-versus-4 modelling favours hybrid 1 and flags "equally". It does not (A4).

## B. Findings on the manuscript (draft3, v0.5)

### B1. Hybrid 1 and H5 headline numbers (Fix in text)

Where: Abstract (sentence on the hybrid), Section 5.2 (H5, H9 bullets), Section 5.3, Discussion Section 6.1, Conclusion.
What: see A2. The Abstract and Conclusion state that hybrid 1 "added 0.29 to 0.36 on thresholds that nobody configured". That is a difference against a comparator that ignores its record. The Designs section never says how the flags design decides, and a reader will assume it uses the record it recovers. Discussion bullet 1 ("recover the record almost as often as the record alone (0.877 against 0.892), but decide only 0.275 of hard cases at thresholds that were not configured") reads as though a flags node with a recovered record could decide no more than 0.275, while the record alone decides 0.546.
Fix: state the flags decision rule in Section 3.5 and in the H5 and H9 results, report the record-only contrast beside every flags contrast, and quote +0.08 to +0.10 (hybrid 1 over record only, descriptive) in the Abstract.

### B2. The explanation and the remedy for H8 (Fix in text)

Where: Discussion Section 6.2 ("Corroboration" bullet, last paragraph), Conclusion (last sentence of the second paragraph), Section 5.4 (last paragraph).
What: see A1. The text says the residual is structural "when exactly the required number of messages arrives". At Q = 12 that class is 23% of the false rate. The larger parts are partial systematic use (41%) and days without redundancy (36%, inferred). The text also recommends CRC-24 or a message authentication code as the remedy for the failed hypothesis, but H8 is conditional on a passing forgery, so a longer CRC cannot repair it. It reduces the unconditional rate. The "Sample size" lesson is right (six sites understated the rate) but the cause is the composition of days (more days with fewer messages than needed), not only the number of sites.

### B3. The slot model is not stated (Fix in text)

Where: Section 4 (Study), Section 3.5, Limits.
What: all design comparisons (H2 to H7, H9) come from an abstract slot model with slotted witnesses, not from the byte frame, and the byte-level checks (H1 round trip, H8) cover record and layered witnesses only (A4). Section 3.4 mentions "the slot model used in the prototypes" once, and Section 4 does not say that the confirmation used it. State this in Section 4 and in the Limits, together with the list of what has no byte-level test (hosted witnesses, conductance pair codes, flags, decoding from subsets).

### B4. Wording and checkable statements (Fix in text)

- Section 5.3, bullet 4: "Send-on-delta and the tightened tolerance were below the record alone in record recovery and in hard-case decisions at this quota." One cell is not below: tolerance x 0.5 under Gilbert loss at the unanticipated thresholds is 0.464 against 0.460 for the record alone (results/confirm3/verdicts3.md).
- Section 5.2, H4: "the lower bound of the loss was 0.105". The interval of the difference is -0.105 to -0.062, so 0.105 is the upper bound of the loss.
- Discussion 6.1: "the witnesses also decided thresholds that nobody configured, which flags cannot (H5)". Flags decided 0.275 by monotone implication. Replace "cannot" by a statement of the numbers.
- Discussion Limits: "favours the flags and hybrid 1 equally and does not affect comparisons among the other designs". See A4: the bias is larger for hybrid 1 on H9 because it enlarges the spare room for hosting.
- Introduction, paragraph 3: "with soundness that holds whatever the loss". Soundness also needs uncorrupted messages (H8 is about this), so write "whatever the loss pattern".
- Section 5.1, bullet 3 ("Targeting paid"): the 0.001 to 0.005 record-recovery cost belongs to the single-query prototype (docs/PROTO_Q_RESULTS.md line 18). The generalised rule against random days cost 0.008 (-0.013 to -0.004) in docs/PROTO_J_RESULTS.md line 57. Name the source of each number.
- Section 5.1, bullet 1 of the hybrid text ("About 78% of development days had at least one spare slot and 21% had four") is from docs/HYBRID_RESULTS.md and was computed at the 4.75 capacity (A4).

### B5. Procedure and limits that are missing (Report as limit)

- Section 4.3 says the repository was committed and tagged and a freeze record with checksums was written. Add that the tag was created on the commit of 12:33 on the authors' instruction, that the freeze record was written when the run started, and that it was first committed after the run (A8).
- Add to the Limits: the structural integrity classes (B2), no byte-level test of hosted witnesses, conductance pair codes, or flags (B3), slotted witnesses in the experiments (A4), body-only forgeries (A6), and the unfrozen environment variables and library versions (A8).
- Report how many of the 31 confirmation sites obtained an inferred resolution for DO and pH (assumption R). This is a descriptive count that the run already computed (`res` in prepare_items) but did not print.
- Section 4.3 says the run "took about 3.5 hours". The log gives 12:41 to 16:08 (3 h 27 min), which agrees.
- H1 in Section 5.2 should say that the round trip used all Q messages, the record and a layered group of four witnesses, and 3 x 10,095 blocks.
- State that H7 and the configured and record parts of H9 hold by construction (A3). The table marks H9 "Supported" without that remark.

### B6. Proposition 1 (Note)

The Method repeats the censored-reading sentence of the specification (A10). Either add the interpolation argument for the threshold queries and restrict the proposition for the conductance chain rule and the daily maxima, or state the assumption that no unflagged censored reading lies inside a certified span.

### B7. Related work (Note)

- The text says Albanese et al. "constructed systems that reach the girth" while the search log records that only the start of Section IV was read and the proofs were not. Keep the sentence to the theorems that were read, or read the construction.
- I did not audit the claims attached to the other citations (the medium-access cluster, the reproducibility papers of Essawy and Choi, Argos practice). The search log covers 15 queries and the papers listed in it.
- Bibliography: 48 keys cited, 48 in refs.bib, none missing or unused. BibTeX reports undefined month strings (july, june, sept) in refs.bib; check how those entries print.

### B8. Figures and numbers (held)

- The project's audit (src/paper/check_numbers5.py) reports "numbers not found in any source: none". I also matched by hand: the hypothesis table to results/confirm3/verdicts3.md, the descriptive tables, the regional sentences (the Gulf loss of 0.166 and the other regions 0.062 to 0.084), the H8 values, 30,285 blocks, and 10,095 days with 144 to 365 per site (from the forgery table).
- Figures: forest.png and h8.png agree with the verdicts. In the forest plot the legend overlaps the H9 interval for independent loss. The bars in the H8 figure run from 0 to the upper bound, not over the 95% interval, which the legend states.

## C. Attempts that did not produce a finding

- A sound-but-wrong decision at a threshold with the encoder's 1e-9 slack: none found (A10).
- A crash of `frame2.receive` by forged headers or descriptors: none found in 12,000 calls (A5).
- Leakage of future days into the 7DADM hardness: none (A9).
- A difference between the thresholds in the plan and in the code: none (A11).
- Unequal luck across designs: none (A9).

## D. What I could not check

- I did not run the test suite (717 tests, about 10 minutes) or the mutation check.
- I did not open the sealed data or the plan pickles. The claim in A1 that the third class consists of oversize days is therefore an inference.
- I did not read the supplement (draft3/supplement.tex), the Word build scripts, or the generated tables beyond their text.
- I read part of docs/REVISION2_PLAN.md and of the results documents, not all of them, and I did not re-derive the development numbers.
- I did not check the references against their sources.
