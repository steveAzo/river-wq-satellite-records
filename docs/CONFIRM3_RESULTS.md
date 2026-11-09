# Results of the third confirmation (decision-certificate method)

Status: written 2026-11-09 from results/confirm3/verdicts3.md and verdicts3.csv, produced by one run of src/p3/confirm3.py. Pre-registration: docs/CONFIRM3_PLAN.md. Nothing (threshold, design, parameter, site) was changed after the cohort was opened. An AI assistant (Claude Code) wrote this summary; no outside reviewer has read it.

## 1. Run record

- Command (frozen, unchanged): python -I src/p3/confirm3.py data/clean/usgs_new3_2024 confirm3 data/clean/usgs_new3_2024.md5
- Launched 2026-11-09 at 12:41 on the PC clock, one worker. Freeze check against tag confirm3-freeze passed. Seal check: 31 of 31 checksums OK.
- Stage 1 (record plans, 31 sites) finished at about 14:01. Stage 2 (all designs) finished at about 15:55. Verdict files were written at 16:08.
- Interruptions and restarts: none. The log contains no error, traceback, or memory failure. The run was not restarted.
- Analysis population: 31 of 31 sites (at least 100 four-parameter days).
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

Comparison with development (six sites): 0.027, 0.0004, 0.086, 0.0029. Every cohort value is higher than the development value; the Q = 12 record-only value is about 15 times higher. The development estimate was therefore optimistic. The limits are not changed. The forgery model is a forced random-content forgery with a modelled CRC pass rate, so the figures are conditional on that model. CRC-24 (descriptive sensitivity, about 5 points of record recovery for a 256-fold lower forgery rate) was not a hypothesis and is the obvious remedy to discuss, but it was not tested for H8 here.

## 4. Caveats that stay attached

- Assumption R was off for about 15 of 38 development sites; the resolution is inferred from the same record. H1 cannot fail through R, so it tests the code and the other assumptions and is not evidence that R holds for deployed sensors (docs/CONFIRM3_PLAN.md Section 3a).
- Flags are modelled at 4.75 values per message against the frame's 4.
- The alternative thresholds (alt1, alt2) were chosen by the analyst. H5 and H9 depend on them.
- 31 US sites in one year (2024); the Gulf region contributed only 4 sites. No claim for other regions, years, or deployments.
- Trace-driven simulation: no satellite hardware, no real channel statistics, no microcontroller measurements.
- Truth statements refer to the loader's record, which includes bridged readings.
- The 7DADM band and the unknown-history rule were tuned on development data.

## 5. Descriptive secondary results (no verdict)

Pooled levels, record recovered / hard configured / hard alternative / all configured, Q = 6, independent loss: record only 0.892 / 0.638 / 0.546 / 0.883; flags 0.877 / 0.999 / 0.275 / 0.999; hybrid 1 0.877 / 0.999 / 0.629 / 0.999; hybrid 2 0.779 / 0.999 / 0.806 / 0.999; random-day control 0.812 / 0.815 / 0.707 / 0.914; tolerance x 0.5 0.698 / 0.524 / 0.526 / 0.754; coded send-on-delta 0.533 / 0.396 / 0.369 / 0.620.

- The decision flags are close to perfect on configured thresholds (0.999) and weak on unanticipated ones (0.275). Hybrid 1 keeps the flag performance and raises the unanticipated level to 0.629 at no cost in record recovery. Hybrid 2 reaches 0.806 on unanticipated thresholds but loses about 10 points of record recovery (0.779 against 0.877); it is descriptive only.
- Exact allocation (lambda 1) minus the 3b rule, Q = 6, independent loss: record +0.028, hard configured -0.015, hard alternative -0.057, all configured +0.049. As in development, it did not beat the simple rule on hard cases, so no confirmatory claim is made.
- Under Gilbert loss and at Q = 12 the orderings are the same (full tables in results/confirm3/verdicts3.md). Per-region heterogeneity, CRC-24 record recovery, and the 7DADM band sensitivity are in results/confirm3/verdicts3.csv and the run outputs and have not yet been summarised here.

## 6. What the evidence supports

- Supported: soundness (no wrong certified decision), benefit over a record alone and of targeting, generality to unanticipated thresholds, no dominance by the two simple baselines, the known flag advantage on configured thresholds, and the adopted hybrid design.
- Not supported: the integrity bound under forgery at Q = 12 (record only and layered). The paper must report this as a failed pre-registered hypothesis and state the remedy as untested.
- The claim stays generality and certificates, not best decisions for known thresholds.
