# Results of the third confirmation (decision-certificate method)

Status: written 2026-11-09 from results/confirm3/verdicts3.md and verdicts3.csv, produced by one run of src/p3/confirm3.py. Pre-registration: docs/CONFIRM3_PLAN.md. Nothing (threshold, design, parameter, site) was changed after the cohort was opened. An AI assistant (Claude Code) wrote this summary; no outside reviewer has read it.

## 1. Run record

- Command (frozen, unchanged): python -I src/p3/confirm3.py data/clean/usgs_new3_2024 confirm3 data/clean/usgs_new3_2024.md5
- Launched 2026-11-09 at 12:41 on the PC clock, one worker. Freeze check against tag confirm3-freeze passed. Seal check: 31 of 31 checksums OK.
- Stage 1 (record plans, 31 sites) finished at about 14:01. Stage 2 (all designs) finished at about 15:55. Verdict files were written at 16:08.
- Interruptions and restarts: none. The log contains no error, traceback, or memory failure. The run was not restarted.
- Analysis population: 31 of 31 sites (at least 100 four-parameter days); 10,095 days with a forgery-study row (144 to 365 per site), counted from results/confirm3/robust2_stage1.csv.
- Byte-level round trip: 30,285 blocks, 0 mismatches.
- Forgery study: 908,180 rows in results/confirm3/robust2_stage1.csv.

## 2. Verdicts

Intervals are 95% percentile intervals from 1,000 site-clustered bootstrap resamples. Pairs of values are independent loss and Gilbert loss (burst length three), loss probability 0.3.

| ID | Result | Bound required | Verdict |
|---|---|---|---|
| H1 | Wrong decisions: maximum 0.000 in every certificate design; round trip 0 mismatches in 30,285 blocks | 0 and 0 | Supported (conditional on assumption R, see Section 4) |
| H2 | +0.318 (+0.234 to +0.417) and +0.300 (+0.223 to +0.390) | lower bound at least 0.15 | Supported |
| H3 | +0.141 (+0.105 to +0.174) and +0.130 (+0.096 to +0.165) | lower bound at least 0.05 | Supported |
| H4 | -0.083 (-0.105 to -0.062) and -0.071 (-0.091 to -0.053) | lower bound at least -0.12 | Supported, with the thinnest margin (lower bound -0.105 against -0.12) |
| H5 | Against flags: +0.531 (+0.494 to +0.569) and +0.441 (+0.411 to +0.472). Against record only: +0.260 (+0.191 to +0.344) and +0.245 (+0.184 to +0.320) | both lower bounds at least 0.10 | Supported |
| H6 | No dominance by coded send-on-delta or by tolerance x 0.5 in any of the four combinations | no dominance | Supported |
| H7 | Flags minus 3b rule, configured thresholds: +0.043 (+0.025 to +0.068) | lower bound above 0 | Supported (the known limit replicated) |
| H8 | See Section 3 | four upper bounds | NOT supported (two of four bounds exceeded) |
| H9 | Alternative thresholds: +0.355 (+0.297 to +0.418) and +0.294 (+0.248 to +0.345). Configured hard-case decisions: +0.000 in both. Record recovered: +0.000 in both | alt lower bound at least 0.20; others at least -0.01 | Supported |

Eight of nine hypotheses are supported; H8 failed.

## 3. H8 (integrity under one CRC-valid forgery): failed

The rule was that a hypothesis is supported only if its bound holds in every listed condition. Two of the four conditions exceeded their limits.

- Record only, Q = 6: 0.0463, upper bound 0.0584, limit 0.06. Within the limit.
- Record only, Q = 12: 0.0061, upper bound 0.0134, limit 0.01. Exceeded (the point estimate is inside the limit; the upper bound is not).
- Layered witnesses with k_w = 2, Q = 6: 0.1050, upper bound 0.1197, limit 0.15. Within the limit.
- Layered witnesses with k_w = 2, Q = 12: 0.0126, upper bound 0.0215, limit 0.02. Exceeded (same pattern).

Comparison with development (six sites): 0.027, 0.0004, 0.086, 0.0029. Every cohort value is higher than the development value; the Q = 12 record-only value is about 15 times higher. The development estimate was therefore optimistic. The limits are not changed. The forgery model is a forced random-content forgery with a modelled CRC pass rate, so the figures are conditional on that model.

Where the false certificates came from (added after the in-project review of 2026-11-09, finding A1; shares recomputed from results/confirm3/robust2_stage1.csv, record only, receiver with CRC, sanity, and corroboration). The residual risk named in docs/FRAME_SPEC_V2.md Section 5 (only exactly the needed number of messages) is incomplete; there are three classes of day:
- Exactly the needed number of messages arrived: 58% of the rate at Q = 6 and 23% at Q = 12 (false share on such days 0.26 and 0.18).
- Fewer messages arrived than needed, so only systematic units were used and nothing could be compared: 24% at Q = 6 and 40% at Q = 12 (false share on such days 0.17 and 0.19).
- Extra messages arrived but were not compared: 18% at Q = 6 and 37% at Q = 12 (false share on such days 0.010 and 0.002). The reviewer inferred that these are blocks with one needed message that were not rejected, probably days whose record exceeded the quota and had no parity. A follow-up check supports this without opening the plans: all 257 (Q = 6) and 68 (Q = 12) such false days have need = 1; among need = 1 blocks with extra messages only 90% (Q = 6) and 96% (Q = 12) were rejected, whereas need = 2 blocks were rejected in 100% of rows; and in the receiver (src/p3/frame2.py, corroboration only `if coded`, with coded = K <= Q) uncoded blocks, which are exactly the oversize days, have need = 1 and are never corroborated. The number of units per day was still not computed from the plans, so the attribution remains an inference, now a strong one.
The development sample had 10 days with fewer messages than needed at Q = 12 (0.06% of its rows) against 401 (1.3%) in the cohort, so it did not contain the dominant failure mode.

H8 is conditional on one CRC-valid forgery. A longer CRC (CRC-24 costs about 5 points of record recovery in development for a 256-fold lower forgery rate by the stated model) lowers the probability that a forgery passes, but it does not change this conditional share. It is therefore not a remedy for the failed hypothesis, and an earlier version of this paragraph that called it "the obvious remedy" was wrong. Correction (2026-11-10): the review's remedy, corroboration for days with at most the needed number of messages and for oversize days, is only partly possible. A check over the whole record can verify a day only when every unit was decoded (the exactly-needed class). It cannot verify units that never arrived (the fewer-than-needed class) and uncoded oversize days have no parity; for those days only more check bits per message reduce the rate, which a metric conditional on passing the check cannot show. An unconditional rate at a stated bit-error rate is the measure that can. No remedy was tested.

## 4. Caveats that stay attached

- Assumption R was off for about 15 of 38 development sites; the resolution is inferred from the same record. H1 cannot fail through R, so it tests the code and the other assumptions and is not evidence that R holds for deployed sensors (docs/CONFIRM3_PLAN.md Section 3a).
- Flags are modelled at 4.75 values per message against the frame's 4. This also enlarges the spare room in which hybrid 1 hosts witnesses, so it favours hybrid 1 on the H9 contrast at the unanticipated thresholds (lower bound 0.248 against a limit of 0.20); the size of the effect was not measured (review finding A4).
- Flags comparator (review finding A2): the flags design decides from its flags alone and does not use the record, even when the whole record arrives (src/p3/proto_base.py, the flags branch). At the unanticipated thresholds it therefore decided less than the record alone (0.275 against 0.546 under independent loss, 0.264 against 0.460 under Gilbert loss). The contrast of the 3b rule with the record alone (H5, second part: +0.260 and +0.245) is the fairer measure of the benefit of witnesses. Hybrid 1 exceeded the record alone at the unanticipated thresholds by 0.083 under independent loss and 0.097 under Gilbert loss (descriptive point differences of pooled levels, no interval).
- By construction (review finding A3): H7 and the configured and record parts of H9 hold by construction (flags are correct whenever a message arrives, and hybrid 1 merges the same flags at the same capacity, so both contrasts are exactly +0.000). H1 cannot fail through assumption R, and H6 passed with large margins. The informative hypotheses are H2 to H5, the unanticipated-threshold part of H9, and H8.
- Model scope (review finding A4): the design comparisons use an abstract slot model (five slots per message, maximum-distance-separable group recovery) with slotted witnesses, not frame bytes. The byte-level checks (the H1 round trip with all messages delivered, and H8) cover the record and a layered group of four witnesses. Hosted witnesses, the conductance pair codes, the flags, and decoding from a subset of messages had no byte-level test in the confirmation; the flags have no byte-level representation at all.
- Forgery model (review finding A6): forgeries changed body bytes only, only independent loss 0.3 was used, and "false" counts readings certified outside tolerance and witness codes that differ from the truth, not wrong decisions. A forged saturated record code (which marks a reading censored) is not counted.
- Run record (review finding A8): the environment variables P3_TBAND, P3_UNKNOWN, and P3_MAXDAYS are read by the method code, were not recorded in the log, and cannot be confirmed from the outputs; the full-year round-trip count (30,285 = 3 x 10,095 blocks) rules out P3_MAXDAYS. Library versions were not recorded. The tag confirm3-freeze was created on commit a217e46 (12:33), docs/FREEZE3.md was written at 12:41 when the run started, and it was first committed at 16:57, after the run. The checksums were verified by the run script. After the run, the drafting session edited docs/REVISION2_PLAN.md (a frozen file) to record the manuscript status, and reverted the edit the same day (its hash equals the one in docs/FREEZE3.md again); the status is now in docs/MANUSCRIPT_STATUS.md. The edited version was committed in between (commit e6c2e1a).
- Seeds (review finding A7): sites 03293500 and 04193500 share their random streams (the same site number modulo 100000).
- The alternative thresholds (alt1, alt2) were chosen by the analyst. H5 and H9 depend on them.
- 31 US sites in one year (2024); the Gulf region contributed only 4 sites. No claim for other regions, years, or deployments.
- Trace-driven simulation: no satellite hardware, no real channel statistics, no microcontroller measurements.
- Truth statements refer to the loader's record, which includes bridged readings.
- The 7DADM band and the unknown-history rule were tuned on development data.

## 5. Descriptive secondary results (no verdict)

Pooled levels, record recovered / hard configured / hard alternative / all configured, Q = 6, independent loss: record only 0.892 / 0.638 / 0.546 / 0.883; flags 0.877 / 0.999 / 0.275 / 0.999; hybrid 1 0.877 / 0.999 / 0.629 / 0.999; hybrid 2 0.779 / 0.999 / 0.806 / 0.999; random-day control 0.812 / 0.815 / 0.707 / 0.914; tolerance x 0.5 0.698 / 0.524 / 0.526 / 0.754; coded send-on-delta 0.533 / 0.396 / 0.369 / 0.620.

- The decision flags are close to perfect on configured thresholds (0.999) and weak on unanticipated ones (0.275). Hybrid 1 keeps the flag performance and raises the unanticipated level to 0.629 at no cost in record recovery. Hybrid 2 reaches 0.806 on unanticipated thresholds but loses about 10 points of record recovery (0.779 against 0.877); it is descriptive only.
- Exact allocation (lambda 1) minus the 3b rule, Q = 6, independent loss: record +0.028, hard configured -0.015, hard alternative -0.057, all configured +0.049. As in development, it did not beat the simple rule on hard cases, so no confirmatory claim is made.
- Under Gilbert loss and at Q = 12 the orderings are the same (full tables in results/confirm3/verdicts3.md). Per-region levels at Q = 6 were computed after the run by src/paper/region5.py from the per-site result files (draft3/tables/confirm_region.tex): the ordering on unanticipated thresholds held in every region, and the loss of record recovery of the 3b rule relative to the record alone was 0.166 in the Gulf region (4 sites) and 0.062 to 0.084 elsewhere (independent loss). CRC-24 record recovery and the 7DADM band sensitivity were not computed for the cohort.

## 6. What the evidence supports

- Supported: soundness (no wrong certified decision), benefit over a record alone and of targeting, generality to unanticipated thresholds, no dominance by the two simple baselines, the known flag advantage on configured thresholds, and the adopted hybrid design.
- Not supported: the integrity bound under forgery at Q = 12 (record only and layered). The paper must report this as a failed pre-registered hypothesis and state the remedy as untested.
- The claim stays generality and certificates, not best decisions for known thresholds.
