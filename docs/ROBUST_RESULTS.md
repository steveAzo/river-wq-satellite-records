# Step 5 results: channel-blind configuration (review M8, E3, Fig. C, maths audit)

Plan fixed before the run: `docs/STEP5_PLAN.md`. Code: `src/p3/analytic.py`, `run_robust.py`, `robust_eval.py`.
Data: 2023 development year only; four-parameter days; 380 tuning and 380 test days at 38 sites (01474500 has
no four-parameter days). 57,000 design-day rows; every probability exact (no simulated fallback was needed).
Outputs: `results/dev/robust_{exact,summary,regret,mismatch,pilot}.csv`, `robust_choice.json`;
log `results/robust_eval_dev.log`.

Correction (2026-10-25, during Step 6): the first version of this page overstated tag practice. The exact
recursion `analytic.p_units` treated the units present in a transmission order as all the units, so a random tag
order that never sent some unit still counted as fully delivered. Fixed (`p_units(..., n_units)`), with a
regression test and a test that the exact path equals byte-level enumeration for every design
(`tests/test_baselines.py`). The table was recomputed; only the tag rows changed (every other family identical to
four decimals). Tag at Q = 6, independent p = 0.3: 0.108 (was reported as 0.255; Step 4 bytes gave 0.105).
The superseded files are in `results/dev/superseded/`.

## 1. Main finding: the proposed design no longer needs to know the channel

Record-first coding (K = D1, the units of the day's record, plus Q - D1 parity; Proposition 2 in
`docs/RECORD_MODEL.md`) had zero or negative regret against the fixed-K code tuned for the true channel, on
all 15 true channels at every tier (maximum regret: Q = 6, -0.034; Q = 12, -0.002; Q = 24, -0.005; Q = 1, 0).
It was never below record-first repetition (difference 0.000 to +0.152 over all 60 tier-channel pairs), as
Proposition 2 requires.

G_cert on test days at Q = 6 (true channel in columns; "fixed K" is the draft's design):

| Design | iid 0.1 | iid 0.3 | iid 0.5 | iid 0.6 | bursty 0.1 | bursty 0.3 | bursty 0.5 | bursty 0.6 | burst 6, 0.3 |
|---|---|---|---|---|---|---|---|---|---|
| Record-first code (proposed) | 0.971 | 0.905 | 0.741 | 0.616 | 0.937 | 0.833 | 0.694 | 0.598 | 0.775 |
| Record-first repetition | 0.936 | 0.802 | 0.609 | 0.495 | 0.930 | 0.806 | 0.633 | 0.513 | 0.768 |
| Fixed K, tuned for the true channel (oracle) | 0.930 | 0.775 | 0.548 | 0.442 | 0.857 | 0.679 | 0.509 | 0.417 | 0.630 |
| Fixed K, channel-blind (minimax regret; K = 3) | 0.833 | 0.775 | 0.548 | 0.381 | 0.790 | 0.679 | 0.509 | 0.381 | 0.630 |
| Fixed r repetition, channel-blind (r = 2) | 0.810 | 0.632 | 0.358 | 0.225 | 0.788 | 0.652 | 0.427 | 0.267 | 0.627 |
| Tag practice, channel-blind (share 0.5) | 0.155 | 0.108 | 0.057 | 0.035 | 0.150 | 0.103 | 0.058 | 0.036 | 0.109 |
| Reliable-link | 0.525 | 0.118 | 0.016 | 0.004 | 0.733 | 0.321 | 0.066 | 0.013 | 0.476 |
| Every k-th reading | 0.176 | 0.039 | 0.005 | 0.001 | 0.247 | 0.107 | 0.022 | 0.004 | 0.160 |

Columns 0.05, 0.2, and 0.4 and tiers 1, 12, and 24: `results/robust_eval_dev.log`.

Ceiling: a day can be fully certified only if its record fits the tier (D1 <= Q): 19.2% of test days at Q = 1,
98.2% at Q = 6, 99.5% at Q = 12, 100% at Q = 24. At Q = 1 every bound design is identical (the record must fit
one message).

## 2. What channel knowledge was worth for the draft's fixed-K design

- Channel-blind fixed K (minimax regret over the six tuning channels) lost up to 0.108 against the per-channel
  oracle at Q = 6 (0.048 at Q = 12, 0.021 at Q = 24); mean regret 0.033 / 0.015 / 0.008.
- Mismatch (Fig. C data, `robust_mismatch.csv`): K tuned for p = 0.1 and deployed at p = 0.6 lost 0.272
  (0.170 against an oracle 0.442); tuned for p = 0.1 and deployed at p = 0.5 lost 0.222.
- The minimax and mean rules chose the same K at Q = 6 and 12; at Q = 24 the mean rule's choice had a worst-case
  regret of 0.172 against 0.021 for minimax.
- Pilot scenario (server estimates p and burstiness from 28 days of message indices; the node is reconfigured):
  worst loss against the oracle 0.061 (fixed K, Q = 6). Feasible, but unnecessary with record-first coding.

## 3. Code versus repetition (the strong baseline)

Record-first repetition is itself channel-blind and was the strongest baseline. Advantage of the code at Q = 6:
independent loss +0.017 (p = 0.05) to +0.132 (p = 0.5); bursty loss (mean burst 3) +0.003 to +0.085, +0.027 at
p = 0.3; mean burst 6 at p = 0.3, +0.006. Under long bursts the two are nearly equal, because a burst erases a
run of messages whatever they carry. The paper must report this plainly.

## 4. Analytic check against the byte pipeline (maths audit)

Exact mean G_cert versus the Step 4 byte-level simulation (30 draws), same test days and variants:
the largest difference was 0.005 (Q = 6 independent p = 0.3: code 0.775 exact vs 0.780 bytes; repetition
0.632 vs 0.636; reliable 0.118 vs 0.116); 11 of 16 comparisons agreed to 0.001. The exhaustive test
`test_byte_pipeline_agrees_with_the_exact_probability` shows exact agreement (1e-12) when all 2^Q masks are
enumerated.

## 5. Consequences

- The proposed design changes from "fixed K tuned per channel" to "record-first code": K = D1 each day, all
  other messages parity, no channel parameter. This answers review M8 by construction, and Proposition 2 makes
  it optimal among unit-level linear designs on every erasure channel.
- Baselines in Step 6: record-first repetition becomes the main comparison; tag practice must be strengthened.
- Remaining channel assumptions: none for the proposed design's choice; the channels still define where it was
  evaluated (synthetic; no field link).
- Byte-level confirmation of the record-first designs under all 15 channels runs with Step 6, together with the
  strengthened baselines, to avoid running the expensive byte simulation twice.
