# Confirmation plan for method version 3 (DRAFT, not frozen, not approved)

Status: draft written 2026-11-10 by an AI assistant (Claude Code) from development results (docs/V3_DEV_RESULTS.md). Nothing here is frozen. No outside reviewer has read it. It becomes binding only when the user commits a freeze record before the run (Phase 4 of docs/METHOD_V3_PLAN.md).

## 1. What version 3 is

- Frame: version 2 with a CRC-24 per message (4 record values per message) instead of CRC-16 (src/p3v3/frame3.py, setting CRCB = 3, RECCRC off). Selected by the pre-written rule of docs/METHOD_V3_PLAN.md (Phase 2): the only candidates meeting the integrity limit were D2 and D3; D2 is simpler.
- Design adopted: the 3b rule (hard objects in a layered witness group, easy objects hosted in the record unit). Adopted on 2026-11-10 by the post-hoc re-reading of the record clause (Section 8 of the plan): on the CRC-24 frame the record cost against the record only is -0.129 and -0.109 at Q = 6 (slot model; byte level -0.087), over the written limit of -0.08. This is declared, not hidden; hypothesis H4 below makes the cost testable.
- Comparators: record only; decision flags (record discarded); flags plus record (flagsrec), which is the fair comparator.
- Dropped from version 2: hybrid 1 and hybrid 2 (development: docs/V3_DEV_RESULTS.md, Phase 1a), exact allocator, send-on-delta and tolerance x 0.5 are NOT in this confirmation (not re-run in version 3; stated as a limit).

## 2. Data

- Development data (everything opened so far): 2023 development sites, 2024 re-test, the 36-site cohort of the earlier version, cohort 3 (31 sites, 2024).
- Confirmation data: a NEW sealed cohort. OPEN DECISIONS (user and Prof): calendar year, target size, region mix. Nothing is selected or downloaded until these are decided. Same approval rule as before (at least 250 approved daily means per parameter), sites chosen from metadata only with a fresh seed, excluding every site used so far.

- Selection DONE 2026-11-10 (user approved year 2022, new regions, about 40 sites; Prof's agreement reported by the user's go-ahead): src/p3v3/select_cohort4.py, seed 20261113, at most 5 per region, metadata and approval qualifiers only (values discarded), 106 used sites excluded. Result: 35 sites (Pacific coast 5, Mid-Atlantic and Appalachia 5, Ohio valley and Great Lakes 5, Southeast 5, Mountain West 5, Upper Midwest 5, Gulf and lower Mississippi 2 of 9 candidates, Texas 2 of 18, Northeast and New England 1 of 18). Within the stated range (minimum 30, target 40); the shortfall was not repaired. Log: results/confirm4/selection.csv, results/select_cohort4.log. NOT downloaded, NOT sealed: the download waits for the freeze work (Section 5) and a further go-ahead.

## 3. Hypotheses (each can fail; limits come from development, not from the cohort)

Analysis population: sites with at least the minimum number of four-parameter days (as before). Estimand: pooled over days, site-clustered 95% paired bootstrap (B = 1,000), Q = 6 and Q = 12, independent and Gilbert loss, unless stated.

| # | Hypothesis | Limit (pass if) | Development value |
|---|---|---|---|
| H1 | No wrong decision in any design, all Q and loss models; no byte-level round-trip mismatch on any analysed day | 0 and 0 | 0 (all runs) |
| H2 | 3b rule minus flagsrec, hard cases at unanticipated thresholds | lower bound at least +0.10, all four conditions | +0.244, +0.198, +0.161, +0.180 |
| H3 | 3b rule minus record only, hard cases at unanticipated thresholds | lower bound at least +0.10, all four conditions | +0.238, +0.222, +0.153, +0.177 |
| H4 | 3b rule minus record only, whole record recovered (the declared cost) | lower bound at least -0.15 at Q = 6 and -0.10 at Q = 12 | -0.129, -0.109; -0.061, -0.065 (slot model) |
| H5 | 3b rule minus flagsrec, whole record recovered | lower bound at least -0.06, all four conditions | -0.010, -0.012, -0.035, -0.028 |
| H6 | Known limit: flagsrec exceeds the 3b rule on hard cases at the CONFIGURED thresholds | upper bound of (3b minus flagsrec) below 0, Q = 6, both loss models | -0.035, -0.114 |
| H7 | Integrity (H8' of the plan): expected false-certificate days per million days at bit-error rate 1e-3, frame D2, receiver with sanity and corroboration, forced CRC-valid forgery of one message; record only and 3b rule | upper bound at most 0.5, all four blocks | upper bounds 0.0034 to 0.0045 (Q = 6), 0.0007 to 0.0015 (Q = 12) |
| H8 | Byte frame (CRC-24, frame3) reproduces the slot model (4 slots): whole-record recovery, Q = 6 and 12, both loss models; record only and 3b rule | absolute difference at most 0.01 for record only and at most 0.06 for the 3b rule (the slot model is pessimistic for the layered group) | at most 0.003 (record only); 0.030 to 0.040 (3b rule) |

Notes:
- H7 depends on an assumed bit-error rate and a random-corruption model; no channel was measured. The conditional shares by class of day (N = K, N < K, uncoded oversize) are reported descriptively, not tested.
- H1 for wrong decisions holds by construction under assumption R and Propositions 1 and 2; it tests the code, not the sensors (as in docs/CONFIRM3_PLAN.md Section 3a).
- H3 and H5 are not by construction; both can fail.
- Dropped as untestable or already known: the version 2 hypotheses on send-on-delta, tolerance x 0.5, and the random-day control are not part of this plan unless re-run in development first (see Section 5).

## 4. Rules for reporting

- Every hypothesis is reported pass or fail with its interval. A failure is reported as a finding; limits are not changed after the cohort is opened.
- Per-kind contrasts (DO, pH, temperature, conductance) are descriptive tables.
- The count of sites with an inferred reporting resolution (assumption R) is printed by the run.
- Library versions and all settings are logged in the run record; the run uses no environment-variable switches (src/p3v3/proto_base4.py reads none).

## 5. Work still needed before the freeze (development only)

1. DONE 2026-11-10: byte-level recovery and decisions on the D2 frame, both loss models (src/p3v3/bytecheck2.py, docs/V3_DEV_RESULTS.md); H8 limits set from it.
2. The confirmation driver: a version 3 counterpart of src/p3/confirm3.py with a freeze check (tag comparison), run log, and the byte round trip on frame3 settings D2. Not written.
3. DONE 2026-11-10: receiver hardening (finding A5 of the in-project review) in new files only. src/p3v3/receiver3.py wraps frame3: any exception type, including in the sanity rule, rejects the block; non-bytes or wrong-length messages count as failed messages. src/p3v3/certlang3.py: min_bounds, max_bounds, and day_max_bounds return (-inf, inf) when no reading is uncensored (certlang raises ValueError). Tests: tests/v3/test_receiver3.py (51 tests: equality with frame3 on honest and fuzzed input, 7,200 fuzz calls over four frame settings, injected TypeError, OverflowError, and others, malformed site profile, guarded bounds equal to certlang whenever a reading is live). Not changed, kept as a declared limit: a forged censored code (0 or 8191) in a record value passes the sanity rule, because honest records carry such codes. The confirmation driver must call receiver3.receive and certlang3 bounds, not frame3.receive and certlang bounds.
4. Decide whether the random-day control (targeting) and the older comparators are re-run in version 3; if yes, support in proto_base4.py and a development run first.
5. Tests for every new file (tests/v3), full test suite green, freeze record with file hashes.
6. A second AI session reads the code and this plan before the freeze (in-project, not outside).

## 6. Decisions needed from the user and the Prof

- Cohort year, size, and region mix (Section 2).
- Whether the limits of Section 3 are acceptable, in particular H4 (-0.15 at Q = 6), which was set after seeing development numbers and is the declared cost of the design.
- Whether item 4 of Section 5 is in scope.
