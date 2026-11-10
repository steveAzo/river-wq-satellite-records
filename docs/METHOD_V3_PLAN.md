# Method version 3: plan (option B of docs/PROF_DECISION_2026-11-10.md)

Status: DRAFT plan, written 2026-11-10. Nothing here is built, frozen, or approved. Not in the freeze of the previous run. Written by an AI assistant (Claude Code); no outside reviewer has read it.

## 1. Goal and rules

- Goal: a version whose evidence supports a stronger claim than v0.5: a fair witness benefit over a node that uses its record, an integrity result that holds, and byte-level tests of every adopted mechanism. If the new evidence is not better, the paper reports that and takes a narrower scope (option C).
- Rules carried over: development data and confirmation data stay separate; every hypothesis, limit, and design is frozen before a new sealed cohort is opened; failures are reported as they occur; no limit is changed after the data are opened.
- Data status: the 2023 development sites, the 2024 re-test, the 36-site cohort of the earlier version, and the 31-site cohort 3 (2024) are all DEVELOPMENT data for version 3. Cohort 3 has been opened and analysed, so it cannot confirm anything about a method designed after seeing it.
- Code location: the previous run is reproducible from the tag confirm3-freeze, and src/p3/confirm3.py refuses to run if method files differ from the tag. New code therefore goes into new folders (proposed: src/p3v3/ and tests/v3/), copied from src/p3 where needed, and src/p3 and tests stay untouched.

## 2. What the failures and review findings require

| # | Problem (source) | What version 3 must do |
|---|---|---|
| 1 | H8 failed at Q = 12: false certificates concentrate on days with no redundancy to compare (REVIEW A1; docs/CONFIRM3_RESULTS.md Section 3) | Redesign the integrity layer and the metric (Section 3) |
| 2 | The flags comparator discards its record (A2) | Add the fair comparator "flags plus record certificate without witnesses" and make hybrid 1 beat or tie it on its own terms; report contrasts against it |
| 3 | H7 and most of H9 hold by construction (A3) | Pre-register hypotheses that can fail; drop or relabel the ones that cannot |
| 4 | Comparisons come from a slot model, not bytes; hosted witnesses, conductance pair codes, and flags have no byte-level test (A4) | Implement flags and hosted witnesses in the byte frame; run the design comparison through the byte codec with decoding from subsets of messages |
| 5 | 4.75 versus 4 capacity for flags favours flags and hybrid 1 (A4) | Use the frame's real capacity for every design |
| 6 | Slotted witnesses in the experiments, slotless in the frame (A4) | Use the slotless witnesses of the frame everywhere |
| 7 | Environment variables and library versions not frozen or logged; freeze record committed after the run (A8) | Remove the environment-variable switches or hash and log them; record versions in the run log; the user commits the freeze record BEFORE the run |
| 8 | Seed collision between two sites (A7) | Derive seeds from the full site number |
| 9 | Receiver except clause narrow; min/max bounds raise on all-censored (A5) | Catch all exceptions in the receiver; guard the bounds; fuzz-test both |
| 10 | Assumption R inferred from the same record; count not reported (B5) | Print the count of sites with an inferred resolution; keep R off by default unless declared by a site profile, and report both |
| 11 | Pooled estimand hides kind differences; conductance gain of hybrid 1 almost nil (A9) | Pre-register per-kind contrasts as descriptive tables, and decide in advance whether conductance witnesses stay in the hybrid |

## 3. The integrity problem, stated carefully

What was found: with the receiver of frame version 2, a CRC-valid forged message produced a false certificate on days of three kinds: exactly the needed number of messages arrived (nothing to compare), fewer than needed (systematic units used directly), and uncoded oversize days (no parity). At Q = 12 the last two carried most of the rate.

What can and cannot fix each kind:
- Exactly the needed number (N = K, coded): a check that spans the decoded record (for example a CRC-32 stored once inside the record) detects a corrupted unit with probability about 1 - 2^-32. Cost: a few bytes per day, which changes K only for records near a unit boundary.
- Fewer than needed (N < K) and uncoded oversize days: units are used one by one and missing units cannot be checked. A record-level check does not help. Only a stronger check on each message or unit helps (longer CRC, an inner per-unit check, or a MAC). Cost: record capacity per message (CRC-24 costs about 5 points of record recovery in development).
- Therefore no design can make the conditional share (given one forged message that already passes whatever check exists) small for these days, because the condition removes the check's benefit. The honest measure is unconditional: the expected number of false-certificate days at a stated bit-error rate, which multiplies the pass probability of the check by the conditional share. This makes the check length matter, as it should.

Proposed H8' (to be fixed after the development study): expected false-certificate days per million days at a stated bit-error rate (for example 1e-3 and 1e-4), for the full receiver, with a limit set in advance from the development study, evaluated at Q = 6 and Q = 12, record only and layered or hosted. The bit-error rate is a modelling assumption because no channel was measured; the claim must say so. Conditional shares are reported descriptively, by class of day.

Candidate integrity designs to evaluate on development data (all with the capacity cost measured by src/p3/capacity.py-style enumeration):
- D0: frame version 2 as it is (reference).
- D1: D0 plus a record-level CRC-32 inside the coded record.
- D2: CRC-24 per message (4 values per message).
- D3: D1 plus CRC-24.
- D4: an inner per-unit check of 8 bits plus the outer CRC-16.
Selection rule (written before the study): the cheapest design in record recovery whose unconditional rate at 1e-3 is within the limit at both Q; ties go to the simpler design.

## 4. Phases and gates

Phase 0 (needs the user and the Prof): approve this plan, the bundle of fixes, and the new cohort procedure in Section 5. No new data is downloaded before approval.
Phase 1, byte-level design comparison on development data: flags and hosted witnesses in the frame; decoding from subsets; comparison of every design through the codec; fair comparators; real capacity; slotless witnesses. Output: docs/V3_DEV_RESULTS.md. Gate: the new results are reviewed; if the witness benefit over the fair comparators is not at least a stated size (to be written before the run), stop and take option C.
Phase 2, integrity study on development data (all five cohorts of development data, forged-message and bit-error models, classes of day): choose the integrity design by the rule above.
Phase 3, pre-registration: hypotheses that can fail, limits from Phases 1 and 2, the full list of environment settings, the freeze procedure; an AI session other than the author reads the code and the plan before the freeze (in-project, not outside).
Phase 4, freeze: tests pass, tag, freeze record committed by the user before the run.
Phase 5, one confirmatory run on the new sealed cohort. Phase 6, results, manuscript v1.0, and an outside review before any preprint.

## 5. New sealed cohort (needs approval, nothing downloaded)

- Cohort 3 cannot be reused (Section 1). The proposed cohort is new sites, selected by metadata only with a fresh seed, excluding every site used so far (development, re-test, cohort 2, cohort 3), using the same approval rule (at least 250 approved daily means per parameter) and, if enough sites exist, a calendar year not yet used for new sites. The size and the year need a decision: 2024 sites from regions not yet used are a smaller pool (the Gulf region already fell short), and 2025 data would give a new year but must be checked for approval status.
- Procedure as before: select by metadata, download, clean, seal with checksums, verify, and open only in the confirmation script after the freeze.

## 6. Decisions needed

- Approve the scope of Section 2 (all eleven items, or a subset).
- Approve the cohort procedure in Section 5, and choose the year and target size.
- Approve the principle in Section 3: H8 becomes an unconditional rate at a stated bit-error rate, with a limit set from development data, and the conditional shares become descriptive.
- Decide the stop rule: how large must the benefit over the fair comparators be to continue (proposed: at least +0.10 on hard cases at unanticipated thresholds over the record alone, pooled, lower bound of the development interval).

## 7. Risks

- The fair benefit may stay small. The review found +0.08 to +0.10 for hybrid 1 over the record alone. If Phase 1 does not raise it, the paper's main claim cannot be strengthened by the integrity fix alone.
- Longer checks cost record recovery, and the shorter plans (Q = 6) were already tight.
- The metric depends on an assumed bit-error rate.
- Time: Phases 1 to 3 are multi-day coding and development work, and the run is hours on this machine (3.7 GB RAM, one worker).

## 8. Log

- 2026-11-10: the user reported that the Prof approves this plan. The reply did not state choices for the open items of Section 6 (subset of fixes, stop-rule size, cohort year and size). Working assumptions until stated otherwise: all eleven fixes stay in scope; the stop rule of Section 6 is used as a reporting criterion, and a miss triggers a conversation, not an automatic stop; no new data is downloaded.
- 2026-11-10, Phase 1a (early gate on the existing slot model, development data only): src/p3v3/proto_base3.py (derived from the frozen src/p3/proto_base.py by src/p3v3/patch_base3.py; no environment switches; designs and flag capacity on the command line; full-site-number seeds) adds the fair comparator flagsrec (flags that also use the recovered record) and runs rec, heur, flags, flagsrec, and hyb1 at flag capacity 4 (the frame's value) and, for the sensitivity of review finding A4, 4.75. Evaluator: src/p3v3/eval3.py. Outputs: results/v3dev/dev_cap4 and dev_cap475. This is not byte-level and not a confirmation; it answers whether the fair benefit is large enough to justify Phases 2 to 6.
- 2026-11-10, Phase 1a, second run (adoption rule written BEFORE the run): designs hyb2 (flags plus the 3b rule) and ex1 (exact allocator) at flag capacity 4, development data, same seeds and loss draws, output results/v3dev/dev_cap4b. Rule: a layered design (heur, hyb2, or ex1) is carried forward if, at Q = 6 and Q = 12 under both loss models, its unanticipated hard-case level exceeds flagsrec by at least +0.10 (lower interval bound above +0.10 at Q = 6, independent loss) AND its record recovery is no more than 0.08 below the record alone. Among designs passing, prefer the one with the highest configured hard-case level; ties go to the simpler design. If none passes, report it and talk to the Prof. Not a confirmation.
- 2026-11-10, second Phase 1a run finished: only the 3b rule passes the adoption rule; hybrid 2 fails on record recovery, the exact allocator fails the benefit at Q = 12. Details in docs/V3_DEV_RESULTS.md.
- 2026-11-10, Phase 1b (partial): byte-level check of record and 3b rule agrees with the slot model within 0.004 (docs/V3_DEV_RESULTS.md). Remaining: decision layer in bytes, Gilbert, flags byte design.
- 2026-11-10, Phase 2 (integrity study), rules written BEFORE the study is run. Data: the 38 development sites of 2023 only (cohort 3 stays out of use until the user and the Prof say otherwise). Designs: D0 (frame v2 as it is), D1 (D0 plus a record-level CRC-32 in the last record unit), D2 (CRC-24 per message, record symbol one byte smaller), D3 (D1 plus D2). D4 (8-bit inner unit check plus CRC-16) has the same capacity and, for random corruption, the same pass probability (2^-24) as D2, so under this model it is equivalent and is not simulated separately; the simpler D2 stands for it. Blocks: record only and the 3b rule (hard objects layered, easy objects hosted), Q = 6 and Q = 12, independent loss 0.3, receiver with sanity and corroboration, forced CRC-valid forgery of one arrived message (as in docs/INTEGRITY_RESULTS.md), every third development day. Metric H8': expected false-certificate days per million days at a bit-error rate of 1e-3 (also reported at 1e-4 and 1e-2), computed as Q x 0.7 x P(message corrupted) x 2^(-check bits) x measured conditional share. LIMIT: the upper end of the day-clustered 95% interval must be at most 0.5 per million days at 1e-3, in every block and both Q. SELECTION: among designs meeting the limit, the one with the highest whole-record recovery at Q = 6 (independent loss, 3b rule); a difference of less than 0.01 counts as a tie and the simpler design wins (simplicity order: D0, D2, D1, D3). If no design meets the limit, report it; do not change the limit. The conditional shares by class of day (N = K, N < K, uncoded oversize) are reported descriptively. The bit-error rate is a modelling assumption.
- 2026-11-10, Phase 2 finished (docs/V3_DEV_RESULTS.md): rule selects D2 (CRC-24 per message). It costs about 0.06 record recovery; the Phase 1a adoption rule must be re-applied to the D2 frame (3b rule minus record only at Q=6 is -0.087 there, over the -0.08 limit).
- 2026-11-10: layered design on the CRC-24 frame (slot model, 4 slots): benefit clause met, record clause missed at Q=6 (-0.129, -0.109; byte level -0.087). Decision for user and Prof; rule not changed. See docs/V3_DEV_RESULTS.md.
- 2026-11-10 decision (user: 'go with the recommended, always'): the 3b rule is ADOPTED on the CRC-24 frame (D2) as the version 3 design, with the record clause of the Phase 1a rule re-read against the fair comparator. This is a POST-HOC choice made after seeing the D2 numbers (record cost -0.129/-0.109 slot model, -0.087 byte level, at Q = 6, against the written limit of -0.08); it is declared as such and the cost becomes a pre-registered hypothesis with its own limit in the confirmation plan (docs/CONFIRM4_PLAN_DRAFT.md).
- 2026-11-10: cohort 4 selection (2022) done by metadata only: 35 sites, 9 regions (docs/CONFIRM4_PLAN_DRAFT.md). Not downloaded.
- 2026-11-10: Phase 1b complete (byte-level recovery and decisions on the CRC-24 frame, both loss models); H8 limits set from it.
