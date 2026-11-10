# Confirmation plan for method version 3 (DRAFT, not frozen, not approved)

Status: draft written 2026-11-10 by an AI assistant (Claude Code) from development results (docs/V3_DEV_RESULTS.md). Nothing here is frozen. No outside reviewer has read it. It becomes binding only when the user commits a freeze record before the run (Phase 4 of docs/METHOD_V3_PLAN.md).

## 1. What version 3 is

- Frame: version 2 with a CRC-24 per message (4 record values per message) instead of CRC-16 (src/p3v3/frame3.py, setting CRCB = 3, RECCRC off). Selected by the pre-written rule of docs/METHOD_V3_PLAN.md (Phase 2): the only candidates meeting the integrity limit were D2 and D3; D2 is simpler.
- Design adopted: the 3b rule (hard objects in a layered witness group, easy objects hosted in the record unit). The adoption is POST HOC. The written adoption rule (docs/METHOD_V3_PLAN.md, Section 8) required a record cost of at most 0.08 against the record only; on the CRC-24 frame the 3b rule costs about 0.09 at Q = 6 (byte level: -0.088 on 2023 development data, -0.094 on cohort 3). The first adoption entry re-read the clause "against the fair comparator", but that argument rested on a modelling error (flag capacity 3 instead of 4; review finding A1 of docs/REVIEW_FINDINGS_V3.md): with the flags modelled correctly, flagsrec recovers the record exactly as often as the record only, so the 3b rule misses the clause against both. The authors adopted it anyway; H4 tests its record cost with limits written before the cohort 3 rehearsal and not widened.
- Comparators: record only; decision flags (record discarded; slot model only, descriptive); flags plus record (flagsrec), the fair comparator. On the CRC-24 frame the flag field (4 bits) fits in the 16 spare bits of the record symbol, so flagsrec carries the same record as the record only plus the configured flags. flagsrec decides the configured thresholds from the truth whenever a message arrives: an idealised node, fair as a bound (review finding D5).
- Where the hypotheses are measured: the byte check (real frame3 messages with CRC-24, the hardened receiver src/p3v3/receiver3.py, decisions built only from decoded values and decoded witness codes, loss masks shared by all designs). The slot model is run as a descriptive cross-check only (it gives the layered group whole slots and overstates the 3b rule's record cost by 0.04 to 0.08; review finding A2).
- Dropped from version 2: hybrid 1 and hybrid 2 (development: docs/V3_DEV_RESULTS.md, Phase 1a), exact allocator, send-on-delta and tolerance x 0.5 are NOT in this confirmation (not re-run in version 3; stated as a limit).

## 2. Data

- Development data (everything opened so far): 2023 development sites, 2024 re-test, the 36-site cohort of the earlier version, cohort 3 (31 sites, 2024).
- Confirmation data: a NEW sealed cohort. OPEN DECISIONS (user and Prof): calendar year, target size, region mix. Nothing is selected or downloaded until these are decided. Same approval rule as before (at least 250 approved daily means per parameter), sites chosen from metadata only with a fresh seed, excluding every site used so far.

- Selection DONE 2026-11-10 (user approved year 2022, new regions, about 40 sites; Prof's agreement reported by the user's go-ahead): src/p3v3/select_cohort4.py, seed 20261113, at most 5 per region, metadata and approval qualifiers only (values discarded), 106 used sites excluded. Result: 35 sites (Pacific coast 5, Mid-Atlantic and Appalachia 5, Ohio valley and Great Lakes 5, Southeast 5, Mountain West 5, Upper Midwest 5, Gulf and lower Mississippi 2 of 9 candidates, Texas 2 of 18, Northeast and New England 1 of 18). Within the stated range (minimum 30, target 40); the shortfall was not repaired. Log: results/confirm4/selection.csv, results/select_cohort4.log. NOT downloaded, NOT sealed: the download waits for the freeze work (Section 5) and a further go-ahead.

## 3. Hypotheses (each can fail; limits come from development, not from the cohort)

Analysis population: sites with at least the minimum number of four-parameter days (as before). Estimand: pooled over days, site-clustered 95% paired bootstrap (B = 1,000), Q = 6 and Q = 12, independent and Gilbert loss, unless stated.

Machine-read limits (src/p3v3/confirm4.py refuses to run if its limits differ from this line; tests/v3/test_confirm4.py checks it):

`LIMITS: H2_lower=0.10 H3_lower=0.10 H4_lower_q6=-0.15 H4_lower_q12=-0.10 H6_upper=0.0 H8_rec=0.01`

Revised 2026-11-10 after the in-project review (docs/REVIEW_FINDINGS_V3.md). Development values come from the final driver (src/p3v3/confirm4.py) run as a rehearsal on the two development years: 2023 (35 sites in the analysis population; results/rehearsal4_2023/verdicts4.md) and cohort 3, 2024 (31 sites; results/rehearsal4v2/verdicts4.md). Values are lower bounds of the 95% interval in the order Q 6 independent / Q 6 Gilbert / Q 12 independent / Q 12 Gilbert, unless stated.

Only H2, H3, and H4 are tests of the method. H1 and H8 are code checks, H6 is a known limit, and H7 is an analytic bound. The results document must not report "n of 7 held" without this distinction.

| # | Type | Statement (byte level unless stated) | Limit (pass if) | 2023 development | Cohort 3 (2024) |
|---|---|---|---|---|---|
| H1 | Code check (by construction under assumption R) | No wrong decision (byte check and slot model, all Q and loss models), no decoded value differing from the plan, no decision-layer error, no round-trip mismatch on any analysed day | all 0 | 0 (40,468 round-trip blocks) | 0 (40,380 blocks) |
| H2 | Test | 3b rule minus flagsrec, hard cases at unanticipated thresholds | lower bound at least +0.10, all four | +0.196 / +0.161 / +0.156 / +0.164 | +0.204 / +0.166 / +0.159 / +0.167 |
| H3 | Test | 3b rule minus record only, hard cases at unanticipated thresholds | lower bound at least +0.10, all four | +0.234 / +0.218 / +0.163 / +0.183 | +0.251 / +0.230 / +0.165 / +0.188 |
| H4 | Test | Cost of the post-hoc adopted design: 3b rule minus record only, whole record recovered | lower bound at least -0.15 at Q 6 and -0.10 at Q 12 | -0.113 / -0.089 / -0.039 / -0.043 (points -0.088, -0.071, -0.027, -0.032) | -0.113 / -0.089 / -0.039 / -0.045 (points -0.094, -0.075, -0.027, -0.034) |
| H6 | Known limit | flagsrec exceeds the 3b rule on hard cases at the configured thresholds (Q 6) | upper bound of (3b minus flagsrec) below 0, both loss models | upper -0.027 / -0.111 | upper -0.027 / -0.116 |
| H7 | Analytic bound (cannot fail) | Expected false-certificate days per million days at bit-error rate 1e-3 under random corruption; ceiling with a conditional share of 1 is 0.042 (Q 6) and 0.084 (Q 12) | none (reported) | upper 0.0006 to 0.0036 | upper 0.0014 to 0.0036 |
| H8 | Code check | Record only: byte frame and slot model agree in whole-record recovery | absolute difference at most 0.01, all four | 0.000 | at most 0.001 |

Notes:
- Dropped after the review: H5 (3b rule minus flagsrec, whole record recovered) is identical to H4 once the flags are modelled with their correct capacity; the H8 clause for the 3b rule measured a known bias of the slot model (reported descriptively now); the H7 limit of 0.5 per million could not be reached by any receiver.
- H4 was measured on the slot model in the first draft; it is now measured at byte level with the same limits (-0.15, -0.10), which were written before the cohort 3 rehearsal. The proposal to widen them after the rehearsal was withdrawn (review finding D2). Its margin is the smallest of the three tests (about 0.04 at Q 6): H4 is the hypothesis most likely to fail.
- Reported against the original adoption rule as well: the byte-level point cost at Q 6 independent (about -0.09) is beyond the -0.08 of the written rule; that is why the adoption is post hoc.
- Descriptive (no limit), given one CRC-valid forgery of a header or body: share of days with a wrong decision, 0.018 to 0.024 at Q 6 and about 0.002 at Q 12 on both development years; share of blocks rejected 0.80 (Q 6) and 0.91 (Q 12). Multiplied by the chance that a corrupted message passes the CRC-24, this is far below one wrong-decision day per million days; it is the measured consequence of the declared limit that forged censored codes remove readings from decisions.
- H7 depends on an assumed bit-error rate and a random-corruption model; no channel was measured. The conditional shares by class of day (N = K, N < K, uncoded oversize) are reported descriptively.
- H1 for wrong decisions holds by construction under assumption R and Propositions 1 and 2; it tests the code, not the sensors (as in docs/CONFIRM3_PLAN.md Section 3a).
- Dropped as untestable or already known: the version 2 hypotheses on send-on-delta, tolerance x 0.5, and the random-day control are not part of this plan unless re-run in development first (see Section 5).

## 4. Rules for reporting

- Every hypothesis is reported pass or fail with its interval. A failure is reported as a finding; limits are not changed after the cohort is opened.
- Per-kind contrasts (DO, pH, temperature, conductance) are descriptive tables.
- The count of sites with an inferred reporting resolution (assumption R) is printed by the run.
- Library versions and all settings are logged in the run record; the run uses no environment-variable switches (src/p3v3/proto_base4.py reads none).

## 5. Work still needed before the freeze (development only)

1. DONE 2026-11-10: byte-level recovery and decisions on the D2 frame, both loss models (src/p3v3/bytecheck2.py, docs/V3_DEV_RESULTS.md); H8 limits set from it.
2. WRITTEN 2026-11-10: the confirmation driver src/p3v3/confirm4.py and the freeze-record writer src/p3v3/freeze4.py; tests tests/v3/test_confirm4.py (38 pass).
   - Stages, each resumable per site: plans; analysis population (at least 100 four-parameter days); slot model (proto_base4.run_site, 4 slots, flag capacity 3, designs rec, heur, flags, flagsrec); byte check (frame3 CRCB = 3, receiver3, decisions from decoded values, every day, 20 draws per condition) with a lossless round trip of every analysed day; integrity (as integrity3.py, D2 only, receiver3, every third day, 8 forged draws); verdicts H1 to H8 and descriptive tables (per kind, assumption R count, integrity classes).
   - Guards: refuses to start if any P3_* environment variable is set or proto_queries settings differ from 3.0 and True; confirmatory tag needs tag confirm4-freeze, clean method files equal to the tag, every MD5 of docs/FREEZE4.md, a verifying seal, and only selected sites in the folder; a rehearsal cannot open a folder named for cohort 4 or 2022. Run log results/<tag>/RUN4.log with library versions and all settings.
   - proto_base4.decide now uses certlang3.max_bounds (edited by hand; identical whenever a reading is uncensored).
   - At the freeze the authors copy this draft to docs/CONFIRM4_PLAN.md (the name the driver and freeze4.py check).
   - Two-site rehearsal on cohort 3 (development data): runs end to end in about 2 minutes; 0 wrong decisions, 0 round-trip mismatches in 2,860 blocks. The 3b-rule byte versus slot gap was 0.070 to 0.077 on these two sites, above the drafted H8 limit of 0.06; a 31-site rehearsal checks this before the freeze.
   - Full rehearsal on all 31 cohort 3 sites (2024, development data for version 3; results/rehearsal4/verdicts4.md, RUN4.log): slot model 9.3 min, byte check 14.9 min, integrity 1.9 min, verdicts 1 min (plans were cached; plans cost about 2 minutes per site, so the cohort 4 run should take about 1.5 to 2 hours). With the drafted limits, 6 of 8 hypotheses would pass and 2 would fail (see the rehearsal column of Section 3). This is development information; the limits are still a draft and are a decision for the authors (Section 6).

   - SUPERSEDED 2026-11-10 (evening): the in-project review (docs/REVIEW_FINDINGS_V3.md) found that this first rehearsal used the wrong flag capacity (3 instead of 4) and measured H4 on the slot model. The driver was revised (byte-level hypotheses with paired masks, flag capacity 4, H5 dropped, H7 an analytic bound, seal tied to the folder, run stamp, strict freeze-record check, limits read from this plan) and re-rehearsed on both development years: all three tests pass with the drafted limits (Section 3). Run times of the revised driver on 31 sites: slot model 11 min, byte check 15 min, integrity 3 min. The table below is kept as the record of the first rehearsal only.

### First rehearsal on cohort 3 with the drafted limits, FLAG CAPACITY 3 AND SLOT MODEL (superseded; lower bound unless stated; Q 6 independent / Q 6 Gilbert / Q 12 independent / Q 12 Gilbert)

| # | Rehearsal value | Drafted limit | Would pass |
|---|---|---|---|
| H1 | 0 wrong decisions, 0 value mismatches, 0 round-trip mismatches in 40,380 blocks | 0 | yes |
| H2 | +0.229 / +0.184 / +0.139 / +0.163 | +0.10 | yes |
| H3 | +0.223 / +0.210 / +0.134 / +0.159 | +0.10 | yes |
| H4 | -0.177 / -0.148 / -0.097 / -0.098 (points -0.142, -0.118, -0.069, -0.073) | -0.15 (Q 6), -0.10 (Q 12) | NO (Q 6 independent) |
| H5 | -0.058 / -0.049 / -0.066 / -0.057 (points -0.026, -0.023, -0.045, -0.038) | -0.06 | NO (Q 12 independent) |
| H6 | upper -0.026 / -0.105 | below 0 | yes |
| H7 | upper 0.0048, 0.0020, 0.0035, 0.0016 per million | 0.5 | yes |
| H8 | 3b rule 0.039 to 0.047; record only 0.000 | 0.06; 0.01 | yes |

Reading: the benefit hypotheses (H2, H3) have wide margins on a second year; the two cost hypotheses were set from the 2023 development point values with little room for site-to-site spread, and the 2024 cohort, whose record recovery is lower for every design, exceeds them.
3. DONE 2026-11-10: receiver hardening (finding A5 of the in-project review) in new files only. src/p3v3/receiver3.py wraps frame3: any exception type, including in the sanity rule, rejects the block; non-bytes or wrong-length messages count as failed messages. src/p3v3/certlang3.py: min_bounds, max_bounds, and day_max_bounds return (-inf, inf) when no reading is uncensored (certlang raises ValueError). Tests: tests/v3/test_receiver3.py (51 tests: equality with frame3 on honest and fuzzed input, 7,200 fuzz calls over four frame settings, injected TypeError, OverflowError, and others, malformed site profile, guarded bounds equal to certlang whenever a reading is live). Not changed, kept as a declared limit: a forged censored code (0 or 8191) in a record value passes the sanity rule, because honest records carry such codes. The confirmation driver must call receiver3.receive and certlang3 bounds, not frame3.receive and certlang bounds.
4. Decide whether the random-day control (targeting) and the older comparators are re-run in version 3; if yes, support in proto_base4.py and a development run first.
5. Tests for every new file (tests/v3), full test suite green, freeze record with file hashes.
6. A second AI session reads the code and this plan before the freeze (in-project, not outside).

## 6. Decisions needed from the user and the Prof

- Cohort year, size, and region mix (Section 2).
- Whether the limits of Section 3 are acceptable, in particular H4 (-0.15 at Q = 6), which was set after seeing development numbers and is the declared cost of the design.
- Whether item 4 of Section 5 is in scope.
