# Results of the version 3 confirmation (cohort 4, 2022)

Status: written 2026-11-11 from results/confirm4/verdicts4.md, verdicts4.csv, and RUN4.log, produced by one run of src/p3v3/confirm4.py (resumed once after a PC restart, Section 1). Pre-registration: docs/CONFIRM4_PLAN.md, frozen at tag confirm4-freeze with docs/FREEZE4.md. Nothing (limit, design, parameter, site) was changed after the cohort was downloaded. An AI assistant (Claude Code) wrote this summary; no outside reviewer has read it.

## 1. Run record

- Order of events: plan and code committed and tagged confirm4-freeze (commit 0f5dec6); docs/FREEZE4.md written by src/p3v3/freeze4.py (124 hashed files, test suite 858 passed, 1 skipped; no cohort data present) and committed (36fcfa5); cohort downloaded, cleaned, and sealed by src/p3v3/prepare_cohort4.py; seal files committed (9dfb1ef); run.
- Download: 35 of 35 selected sites, none excluded for missing 2022 data. The first attempt stopped at site 11 of 35 when the internet connection dropped (name lookup failures on three retries); it was resumed with the same command and skipped the 10 finished sites. Both logs are kept (results/confirm4/prepare4_attempt1.log and prepare4.log). Raw and clean seals: 35 of 35 checksums each.
- Command (frozen, unchanged): python -I src/p3v3/confirm4.py data/clean/usgs_new4_2022 confirm4 data/clean/usgs_new4_2022.md5
- Launched 2026-11-11 at 06:44 on the PC clock. Every start check passed: freeze verified against tag confirm4-freeze (124 hashed files unchanged), limits equal to the plan's LIMITS line, seal covering exactly the cohort folder and verifying, 35 of 35 selected sites present, run stamp written.
- Stages: plans finished 08:40 (116 min, about twice the rehearsal estimate); slot model 08:49; byte check reached site 26 of 35 at 09:01.
- Interruption: the PC restarted at about 09:01 (Windows System log: a restart initiated at 09:01:35, event 1074, followed by start-up events at 09:23). The run log and the error stream contain no error or traceback. Following Section 5 of the plan, the run was resumed at 09:28 with the same command and the same code: the start checks passed again, the run stamp matched (freeze 0f5dec6), and 35 slot-model and 26 byte-check site outputs were reused (written atomically, so an interrupted site leaves no partial file). Byte check finished 09:33, integrity 09:36, verdicts 09:37.
- Analysis population: 35 of 35 sites (at least 100 four-parameter days); 10,417 analysed days (100 to 361 per site). Regions: 5 each in Pacific coast, Mid-Atlantic and Appalachia, Ohio valley and Great Lakes, Southeast, Mountain West, and Upper Midwest; 2 each in Gulf and lower Mississippi and Texas; 1 in Northeast and New England.
- Byte check: 20 paired loss draws per day, Q, and condition. Round trip: 41,668 blocks. Integrity: 111,502 forged draws.

## 2. Verdicts

Intervals are 95% percentile intervals from 1,000 site-clustered bootstrap resamples; contrasts are paired. Values are given in the order Q = 6 independent loss, Q = 6 Gilbert loss (burst length three), Q = 12 independent, Q = 12 Gilbert, loss probability 0.3. All hypotheses are measured at byte level (real CRC-24 messages, the hardened receiver, decisions from decoded values only).

| ID | Type | Result | Required | Verdict |
|---|---|---|---|---|
| H1 | Code check | Wrong decisions 0 (byte check and slot model); decoded values differing from the plan 0; decision-layer errors 0; round trip 0 mismatches in 41,668 blocks | all 0 | Pass (by construction under assumption R) |
| H2 | Test | 3b rule minus flagsrec, unanticipated thresholds: +0.226 (+0.196 to +0.258), +0.189 (+0.165 to +0.215), +0.182 (+0.154 to +0.214), +0.191 (+0.164 to +0.222) | lower bound at least +0.10 | Pass |
| H3 | Test | 3b rule minus record only, unanticipated thresholds: +0.275 (+0.233 to +0.324), +0.249 (+0.212 to +0.292), +0.197 (+0.160 to +0.246), +0.217 (+0.181 to +0.263) | lower bound at least +0.10 | Pass |
| H4 | Test | 3b rule minus record only, whole record recovered: -0.082 (-0.099 to -0.064), -0.068 (-0.081 to -0.055), -0.026 (-0.035 to -0.017), -0.032 (-0.041 to -0.023) | lower bound at least -0.15 (Q 6), -0.10 (Q 12) | Pass |
| H6 | Known limit | 3b rule minus flagsrec, configured thresholds, Q 6: -0.028 (-0.034 to -0.022), -0.107 (-0.117 to -0.099) | upper bound below 0 | Holds (the limit replicated) |
| H7 | Analytic bound | Expected false-certificate days per million days at a bit-error rate of 1e-3: record only 0.0022 (upper 0.0026) at Q 6 and 0.0006 (upper 0.0009) at Q 12; 3b rule 0.0030 (upper 0.0035) and 0.0008 (upper 0.0012); ceilings 0.042 and 0.084 | none | Not a test |
| H8 | Code check | Record only, byte frame against slot model, whole record recovered: absolute differences 0.001, 0.001, 0.000, 0.000 | at most 0.01 | Pass |

The three tests of the method (H2, H3, H4) passed. The two code checks passed, and the known limit replicated.

Margins:
- H2 and H3: the smallest lower bounds (+0.154 and +0.160, Q = 12 independent loss) were 0.05 and 0.06 above the limit.
- H4: the smallest margin was at Q = 6 independent loss (lower bound -0.099 against -0.15, a margin of 0.05). The cohort's cost was slightly smaller than on either development year (point -0.082 against -0.088 and -0.094).

Comparison with development (lower bounds, Q = 6 independent): H2 +0.196 (2023), +0.204 (cohort 3), +0.196 (cohort 4); H3 +0.234, +0.251, +0.233; H4 -0.113, -0.113, -0.099. The cohort fell inside the range of the two development years on every test.

## 3. Caveats that stay attached

- Post-hoc adoption: the 3b rule was adopted after its record cost at Q = 6 exceeded the written adoption limit of 0.08 on development data. In this cohort the point cost at Q = 6 independent loss was -0.082, again beyond -0.08, while the lower bound met the pre-registered H4 limit of -0.15. H4 shows the cost is bounded, not that the original adoption rule was met (docs/CONFIRM4_PLAN.md, Section 1).
- What is tested: only H2, H3, and H4 test the method. H1 cannot fail through assumption R; H8 compares two implementations of the same code; H6 holds largely by construction because flagsrec takes its configured decisions from the truth whenever a message arrives; H7 cannot exceed its ceiling. A count such as "seven of seven" must not be reported.
- Assumption R: the reporting resolution was inferred from the record itself for 26 of 35 sites (DO 14, pH 23, temperature 11). H1 is conditional on it.
- Comparator: flagsrec is an idealised node (perfect configured-threshold decisions whenever a message arrives). Its flag field is assumed to occupy 4 of the 16 spare bits of the CRC-24 record symbol; the frame has no flag field implemented.
- Integrity: the bit-error rate (1e-3) and independent random bit errors are assumptions; no channel was measured. A structured fault could defeat the CRC pass-probability argument.
- Forged censored codes: a CRC-valid forged record value with code 0 or 8191 passes the sanity rule and removes a reading from decisions. Given one CRC-valid forgery (header or body), 1.9% (record only) and 2.2% (3b rule) of days had a wrong decision at Q = 6, and 0.17% and 0.24% at Q = 12 (Section 4); the analytic ceiling of H7 bounds the unconditional rate of such days far below one per million at the assumed bit-error rate.
- Thresholds: the unanticipated thresholds (alt1, alt2) and the hardness bands were chosen by the analyst and were seen on every development cohort.
- Scope: 35 US sites in one year (2022), with 1 to 2 sites in three regions; trace-driven simulation of loss (independent and Gilbert, p = 0.3), no satellite hardware, no measured channel, no microcontroller measurements. Truth refers to the loader's record, which includes bridged readings.
- Not re-run in version 3 and therefore not claimed: send-on-delta, tolerance x 0.5, the random-day control for targeting, the exact allocator, and the hybrid designs (the version 2 confirmation, docs/CONFIRM3_RESULTS.md, holds the earlier results under its own caveats).
- Run interruption: the PC restart during the byte check (Section 1); the resumed run used the same frozen code, verified by the start checks and the run stamp.

## 4. Descriptive results (no verdict)

Pooled levels at byte level, Q = 6, independent loss (record recovered / hard cases at configured thresholds / hard cases at unanticipated thresholds / all cases at configured thresholds):
- Record only: 0.842 / 0.608 / 0.523 / 0.857
- 3b rule: 0.760 / 0.971 / 0.798 / 0.882
- Flagsrec: 0.842 / 0.999 / 0.572 / 0.999
- Under Gilbert loss and at Q = 12 the ordering was the same (results/confirm4/verdicts4.md).

Per kind, byte level, Q = 6, independent loss, 3b rule minus flagsrec at unanticipated thresholds (all intervals above 0):
- DO: +0.162 (+0.113 to +0.216)
- pH: +0.106 (+0.066 to +0.151)
- Conductance: +0.311 (+0.279 to +0.341)
- 7DADM window: +0.258 (+0.216 to +0.296)
- At the configured thresholds flagsrec exceeded the 3b rule for every kind (-0.020 to -0.043), most under Gilbert loss for the 7DADM window (-0.289), where a seven-day window needs every day's witness.

Slot model as a cross-check: for the record only and flagsrec it reproduced the byte frame within 0.001. For the 3b rule it was pessimistic by 0.027 to 0.036 in whole-record recovery (it gives the witness group whole slots), as known from development; the hypotheses do not use it.

Integrity, given one CRC-valid forgery of a header or body byte (shares of forged draws):
- Rejected: 0.80 to 0.81 at Q = 6 and 0.91 at Q = 12.
- False certificates were found only on days on which no redundant message arrived: exactly the needed number (false share 0.16 to 0.22 in that class), fewer than needed (0.11 to 0.16), or uncoded oversize days (0.11 to 0.17); with more messages than needed the share was 0.000 in every block, as corroboration predicts.
- Wrong decision on the day: record only 0.0187 (0.0152 to 0.0226) at Q = 6 and 0.0017 (0.0010 to 0.0026) at Q = 12; 3b rule 0.0219 (0.0184 to 0.0255) and 0.0024 (0.0016 to 0.0033). Decision-layer errors: 0.

## 5. What the evidence supports

- Supported on a sealed cohort, by tests that could fail: on thresholds nobody configured, the targeted witness design decided 0.18 to 0.23 more hard cases than a fair flag-plus-record node and 0.20 to 0.28 more than the record alone, at a cost of 0.03 to 0.08 in whole-record recovery.
- Replicated limit: a node that knows the configured thresholds and sends their answers decides those thresholds better (by 0.03 to 0.11 at Q = 6).
- Not shown: that the design meets its own written adoption rule (it was adopted post hoc), any field performance, and anything about the baselines that were not re-run.
- The claim is a trade-off for unanticipated decisions with certificates, not the best decisions for known thresholds.
