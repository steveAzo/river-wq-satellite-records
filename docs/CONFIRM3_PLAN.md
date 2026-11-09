# Pre-registration of the third confirmation (decision-certificate method)

Status: first written 2026-11-07, before any value of the sealed cohort was analysed; revised 2026-11-09 after an in-project review (Section 3a) and after the authors decided to adopt hybrid 1 (Section 7). It becomes binding when the authors commit the repository and tag the commit `confirm3-freeze`; until then it is a draft. Nothing in this plan was tuned on the sealed cohort. An AI assistant (Claude Code) wrote the code, the plan, and the development results; one separate AI session read them on 2026-11-09 (an in-project reading, not an outside review); no outside reviewer has read them.

## 1. Purpose and scope

- The method under test is the revised one: a self-contained error-bounded record (frame version 2, one CRC-16 per transmitted message), feature-extremum witnesses (daily minimum of dissolved oxygen, minimum and maximum of pH, maximum of temperature, and the conductance rate pair), a protection rule (the generalised 3b rule: witnesses of hard queries in their own protected columns, easy witnesses in spare slots), and the three-valued certificate rules of docs/CERTIFICATE_SPEC.md.
- The study does not claim that witnesses are the best way to decide thresholds fixed at configuration time. Development showed that decision flags are better there (docs/BASELINES2_RESULTS.md); H7 tests whether that replicates. The claims under test are soundness, the benefit over a record alone, the value of targeting, the cost, generality to unanticipated thresholds, the comparison with send-on-delta and tightened tolerance, and the integrity of the receiver.
- Earlier confirmations (docs/CONFIRM_RESULTS.md, docs/CONFIRM2_RESULTS.md) tested a different method (frame version 1, no witnesses). Their failed hypotheses C1 and C2 stay reported; this cohort is new evidence for the revised method only.

## 2. Cohort

- Selection used metadata only (src/data/select_cohort3.py, seed 20261107): sites in Pacific coast (WA, OR, CA), Mid-Atlantic and Appalachia (PA, MD, VA, WV, NJ, DE), Ohio valley and Great Lakes (OH, IN, MI, IL, KY, TN), and Gulf and lower Mississippi (LA, MS, AR, OK) whose instantaneous series of temperature, conductance, dissolved oxygen, and pH cover 2024, that were never used in development (2023), the 2024 re-test, or the second cohort, with at least 250 approved daily means per parameter in 2024 (qualifiers read, values discarded), taken in seeded random order within region up to nine per region.
- Result: 249 candidates considered, 31 selected (Pacific coast 9, Mid-Atlantic 9, Ohio valley 9, Gulf 4: only 4 of the 16 Gulf candidates met the approval rule). The shortfall was not repaired by adding regions. The full log is results/confirm3/selection.csv.
- Data: 2024 instantaneous values downloaded by src/data/fetch_usgs.py, cleaned by the same rules as all earlier cohorts (src/data/clean_usgs.py, approved values only, no interpolation across gaps longer than 60 minutes) into data/clean/usgs_new3_2024, and sealed with MD5 checksums (data/raw/usgs_new3_2024.md5, data/clean/usgs_new3_2024.md5) before any analysis. Preparation printed counts only.
- Analysis population: sites with at least 100 four-parameter days. Days: four-parameter days with a record plan.

## 3. What is frozen

- Code: every file in src/p3, src/data, tests, and tools/mutation_check.py at the tagged commit; docs/CERTIFICATE_SPEC.md, docs/FRAME_SPEC_V2.md, and this plan. docs/FREEZE3.md records the commit, the test result, and the checksums (src/data/freeze3.py refuses to write it if the tag is not HEAD, if method files are uncommitted, if the tests fail, or if the seal does not verify).
- Parameters: USGS excellent-record tolerances; messages of 23 bytes (five value slots); Q = 6 and 12 messages per day; independent loss 0.3 and Gilbert loss 0.3 with bursts of three; 20 draws per day; seeds in the code; configured thresholds DO 5 mg/L, pH 6.5 and 9.0, 7DADM 20 degC, conductance change 10% in one hour; alternative threshold sets alt1 (4.5; 6.3 and 9.2; 21; 20%) and alt2 (5.5; 6.7 and 8.8; 19; 5%); hard cases (within 0.6 mg/L or 0.4 pH units of a threshold or in the event state; conductance rate at least 4%; 7DADM trailing mean within 3 degC of 20, or unknown history); near windows within 2 degC; assumption R (readings are multiples of the site's reporting resolution, inferred from the record as a site-profile field); allocation prior (independent loss averaged over p = 0.1 to 0.5) and lambda = 1.
- Receiver: CRC-16 per message, the sanity rule, and corroboration (docs/FRAME_SPEC_V2.md Section 3). CRC-16 is primary. CRC-24 is a descriptive sensitivity (record recovery with four values per message), not a hypothesis. The witness-versus-record cross-check is not part of the receiver (development showed it changes little).
- Designs run: record only, the 3b rule, exact lambda 1, tolerance x 0.5, send-on-delta (once and coded), decision flags, the random-day control, and the two hybrids (hybrid 1: flags with all witnesses hosted in spare slots; hybrid 2: flags with the 3b rule). The hybrids were exploratory in development (docs/HYBRID_RESULTS.md). Hybrid 1 was ADOPTED by the authors on 2026-11-09 (the drafter's recommendation) and carries H9; hybrid 2 is descriptive (Section 7).

### 3a. Scope of H1 and assumption R (added after the in-project review, 2026-11-09)

- Assumption R is not declared by the site in this study. The resolution is inferred from the analysed record (src/p3/certlang.py, infer_resolution), and the record contains readings that the loader bridged linearly over gaps of at most two readings. In development, 15 of 38 sites obtained no resolution for DO and for pH, so R is off for them.
- A wrong resolution is unsound: a reading of 7.03 with an assumed resolution of 0.1 gives a certain wrong decision for the threshold 7.01 (tests/test_review_fixes.py). Because the resolution is inferred from the same data, H1 cannot fail through R. H1 is therefore a test of the code and of the other assumptions, conditional on R being correct. It is not evidence that R holds for deployed sensors.
- Truth statements refer to the loader's record, which includes bridged readings, not only to sensor readings.

## 4. Hypotheses, thresholds, and rule of decision

Intervals are 95% percentile intervals from 1,000 site-clustered bootstrap resamples; differences are pooled day-query means (paired on the same resamples). Hard-case decisions pool dissolved oxygen, pH, conductance, and 7DADM windows; "decisive-correct" means a certain decision that equals the truth on the sensor record. A hypothesis is supported only if its stated bound holds in every listed condition.

| ID | Statement | Threshold | Development value (not tuned on the cohort) |
|---|---|---|---|
| H1 | No wrong decision in any certificate design (all Q and loss models), and no byte-level round-trip mismatch of frame version 2 on any analysed day | 0 wrong; 0 mismatches | 0 wrong in all development runs; 0 mismatches in tests |
| H2 | 3b rule minus record only, hard-case decisions at the configured thresholds, Q = 6, both loss models | lower bound at least 0.15 | +0.291 and +0.281 |
| H3 | 3b rule minus the same layering on random days, hard-case decisions, Q = 6, both | lower bound at least 0.05 | +0.171 and +0.172 |
| H4 | Record recovered, 3b rule minus record only, Q = 6, both | lower bound at least -0.12 | -0.080 and -0.067 |
| H5 | Unanticipated thresholds (alt1 and alt2 pooled), hard cases: 3b rule minus decision flags, and 3b rule minus record only, Q = 6, both | both lower bounds at least 0.10 | +0.566 and +0.483 (flags); +0.210 and +0.202 (record only) |
| H6 | Neither coded send-on-delta nor tolerance x 0.5 dominates the 3b rule (record recovered within 0.005 or better and hard-case decisions at least 0.005 higher), Q = 6, both | point estimates | no dominance in development |
| H7 | Known limit: decision flags exceed the 3b rule in hard-case decisions at the configured thresholds, Q = 6, independent loss | lower bound above 0 | +0.032 (and +0.108 under bursts) |
| H8 | Conditional false-certificate day share given one CRC-valid forgery (CRC-16, sanity, corroboration): record only at Q = 6 and 12; layered witnesses with k_w = 2 at Q = 6 and 12 | upper bounds at most 0.06, 0.01, 0.15, 0.02 | 0.027, 0.0004, 0.086, 0.0029 (six sites; recomputed after the review corrected the forgery function, docs/INTEGRITY_RESULTS.md) |
| H9 | Hybrid 1 minus decision flags, Q = 6, both loss models: hard cases at the unanticipated thresholds; hard-case decisions at the configured thresholds; record recovered | alt lower bound at least 0.20; configured and record lower bounds at least -0.01 | +0.416 and +0.355; 0.000; 0.000 |

H4 has the thinnest margin (development -0.080 against the limit -0.12); a failure there would be a real finding, not a reason to change the limit. H7 is stated against the method; its failure (flags not better) would also be reported.

## 5. Descriptive results (no verdict)

Exact lambda 1 against the 3b rule (development: criterion not met, so no confirmatory claim), Q = 12 levels, all-case decisions, values per day for send-on-delta and tightened tolerance, per-region heterogeneity, CRC-24 record recovery, the 7DADM band sensitivity, and the integrity table for every receiver variant. The development caveats stay attached: the 7DADM band and the unknown-history rule were tuned on development data.

## 6. Procedure and failure handling

1. The authors approve this plan, commit the repository, and tag it `confirm3-freeze`.
2. python -I src/data/freeze3.py confirm3-freeze writes docs/FREEZE3.md; the authors commit it.
3. python -I src/p3/confirm3.py data/clean/usgs_new3_2024 confirm3 data/clean/usgs_new3_2024.md5 is run once. It verifies the seal, builds plans, runs the designs on identical loss draws, runs the round trip and the forced-forgery study, and writes results/confirm3/verdicts3.md.
4. The run is resumable per site. Any interruption, restart, or resource failure is recorded in docs/CONFIRM3_RESULTS.md; a restart uses the frozen command unchanged.
5. A hypothesis that fails is reported as failed. No threshold, design, parameter, or site is changed after the cohort is opened. The cohort is not reused for tuning.

## 6a. Rehearsal

On 2026-11-07 the whole pipeline (src/p3/confirm3.py without a seal) was run on two development sites with 60 baseline days each (results/rehearsal3, a pipeline test only; the intervals of two sites are meaningless). All steps ran without error: plans, the nine designs on shared draws, the byte-level round trip (0 mismatches in 1,674 blocks), the forced-forgery study, and every verdict including H9. The cohort was not touched. The verdicts of the rehearsal say nothing about the hypotheses.

## 7. Open choices for the authors (before the freeze)

- Hybrid 1: ADOPTED. Development met the adoption rule written in advance (docs/HYBRID_RESULTS.md: identical to the flags on the configured thresholds and in record recovery, +0.416 and +0.355 on the unanticipated thresholds). The authors decided on 2026-11-09 to follow the drafter's recommendation; src/p3/confirm3.py has ADOPT_HYBRID = True and H9 stands as written in Section 4. Changing this after the freeze is not allowed.
- Receiver: CRC-16 is frozen as primary (record recovery 0.915 at Q = 6, independent loss); CRC-24 would cost 5 points of record recovery for a 256-fold lower forgery rate (docs/INTEGRITY_RESULTS.md).
- The thresholds in Section 4 may be tightened or loosened before the freeze; each change must be recorded with its reason.

## 8. Limits

Trace-driven simulation on USGS records; no satellite hardware, no real channel error statistics, no microcontroller measurements. The alternative threshold sets were chosen by the analyst. Conditional integrity probabilities rest on forced random-content forgeries and a model of the CRC pass rate. A pass here supports the method on 31 unseen US rivers in one year; it does not support claims about other regions, years, or deployments.
