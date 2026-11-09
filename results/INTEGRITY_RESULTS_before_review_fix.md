# Integrity study for frame v2 (revision 2, Step 6b), development data only

Date: 2026-11-06. Code: `src/p3/frame2.py` (codec, 37 tests), `src/p3/robust2.py` (experiment), `src/p3/certlang.py` (`witness_consistent`), `src/p3/capacity.py`. Specification and threat model: docs/FRAME_SPEC_V2.md. Results: `results/dev/robust2_stage1.csv`, `results/dev/robust2_summary.csv`, full printout `results/robust2_stage12.txt`.
Command (from Paper3/): `python -I src/p3/robust2.py data/clean/usgs dev 6 10`.

## Method

- A corrupted message passes the per-message CRC-16 with probability about 2^-16 (an upper bound for random errors; every single-bit error and every burst of up to 16 bits is detected). A direct simulation would need millions of days, so the study has two stages.
- Stage 1 (measured): 6 development sites, 1,631 days, byte-level blocks (record only; record with a layered witness group of k_w = 1 or 2 carrying DO minimum, pH minimum and maximum, T maximum), Q = 6 and 12, independent loss 0.3. In each draw one arrived message is replaced by a CRC-valid forgery (1 to 3 random body bytes changed, CRC recomputed). 16,296 or more draws per cell. Outcomes: a day is false if any reading is certified outside tolerance, any witness code differs from the truth, or a value outside the site profile is accepted.
- Stage 2 (model): expected CRC-passing corruptions per day = Q x 0.7 x P(message corrupted) x 2^-16, times the Stage 1 conditional probability.
- Receivers: CRC only; plus the sanity rule (values inside the site profile and in planned order; censored witness codes rejected); plus corroboration (re-encode and compare when more messages arrive than needed; mismatch rejects the block); both; both plus the witness-versus-record cross-check.

## Stage 1: share of days with a false certificate, given one CRC-valid forgery (day-clustered 95% bootstrap interval)

| Block | Q | CRC only | CRC + sanity | CRC + corroboration | CRC + sanity + corroboration | CRC + sanity + corroboration + cross-check |
|---|---|---|---|---|---|---|
| layered k1 | 6 | 0.4282 (0.4208 to 0.4361) | 0.2755 (0.2686 to 0.2826) | 0.2737 (0.2639 to 0.2831) | 0.1544 (0.1475 to 0.1613) | 0.1536 (0.1461 to 0.1602) |
| layered k1 | 12 | 0.2795 (0.2722 to 0.2870) | 0.1635 (0.1583 to 0.1694) | 0.0407 (0.0363 to 0.0458) | 0.0226 (0.0196 to 0.0259) | 0.0225 (0.0197 to 0.0254) |
| layered k2 | 6 | 0.4714 (0.4628 to 0.4803) | 0.2968 (0.2899 to 0.3032) | 0.1980 (0.1882 to 0.2077) | 0.0939 (0.0889 to 0.0992) | 0.0911 (0.0861 to 0.0966) |
| layered k2 | 12 | 0.2644 (0.2564 to 0.2720) | 0.1553 (0.1488 to 0.1608) | 0.0102 (0.0075 to 0.0131) | 0.0036 (0.0025 to 0.0048) | 0.0036 (0.0025 to 0.0048) |
| record | 6 | 0.3806 (0.3719 to 0.3888) | 0.1387 (0.1335 to 0.1441) | 0.0858 (0.0793 to 0.0924) | 0.0285 (0.0257 to 0.0313) | 0.0284 (0.0257 to 0.0310) |
| record | 12 | 0.1879 (0.1803 to 0.1947) | 0.0678 (0.0634 to 0.0718) | 0.0019 (0.0012 to 0.0028) | 0.0006 (0.0002 to 0.0010) | 0.0006 (0.0002 to 0.0009) |

## Stage 2: expected days with a false certificate per million days (independent loss 0.3)

| Corruption | Block | Q | CRC-16, CRC only | CRC-16, sanity + corroboration | CRC-24, sanity + corroboration |
|---|---|---|---|---|---|
| bit errors 1e-4 | layered k1 | 6 | 0.5 | 0.18 | 0.0007 |
| bit errors 1e-4 | layered k1 | 12 | 0.653 | 0.0529 | 0.00021 |
| bit errors 1e-4 | layered k2 | 6 | 0.551 | 0.11 | 0.00043 |
| bit errors 1e-4 | layered k2 | 12 | 0.618 | 0.00845 | 3.3e-05 |
| bit errors 1e-4 | record | 6 | 0.445 | 0.0333 | 0.00013 |
| bit errors 1e-4 | record | 12 | 0.439 | 0.00129 | 5e-06 |
| bit errors 1e-3 | layered k1 | 6 | 4.61 | 1.66 | 0.0065 |
| bit errors 1e-3 | layered k1 | 12 | 6.02 | 0.488 | 0.0019 |
| bit errors 1e-3 | layered k2 | 6 | 5.08 | 1.01 | 0.004 |
| bit errors 1e-3 | layered k2 | 12 | 5.7 | 0.078 | 0.0003 |
| bit errors 1e-3 | record | 6 | 4.1 | 0.307 | 0.0012 |
| bit errors 1e-3 | record | 12 | 4.05 | 0.0119 | 4.6e-05 |
| bit errors 1e-2 | layered k1 | 6 | 23.1 | 8.34 | 0.033 |
| bit errors 1e-2 | layered k1 | 12 | 30.2 | 2.44 | 0.0095 |
| bit errors 1e-2 | layered k2 | 6 | 25.5 | 5.07 | 0.02 |
| bit errors 1e-2 | layered k2 | 12 | 28.6 | 0.391 | 0.0015 |
| bit errors 1e-2 | record | 6 | 20.6 | 1.54 | 0.006 |
| bit errors 1e-2 | record | 12 | 20.3 | 0.0596 | 0.00023 |
| 10% of messages hit | layered k1 | 6 | 2.74 | 0.99 | 0.0039 |
| 10% of messages hit | layered k1 | 12 | 3.58 | 0.29 | 0.0011 |
| 10% of messages hit | layered k2 | 6 | 3.02 | 0.602 | 0.0024 |
| 10% of messages hit | layered k2 | 12 | 3.39 | 0.0464 | 0.00018 |
| 10% of messages hit | record | 6 | 2.44 | 0.183 | 0.00071 |
| 10% of messages hit | record | 12 | 2.41 | 0.00707 | 2.8e-05 |

The CRC-24 column divides by 256 (2^-8 more bits) and ignores the change in the Stage 1 conditional; its cost is in the next section.

## Findings

1. A per-message CRC with sanity rules and corroboration lowers the conditional false-certificate probability from 38.1% (CRC only) to 2.9% for record-only days at Q = 6, and from 18.8% to 0.06% at Q = 12.
2. The sanity rule (free, no bits) removes 36% to 64% of the false days by itself; corroboration (free when extra messages arrive) removes most of the rest. Neither helps when exactly the needed number of messages arrives, which is the structural residual.
3. Layered witness groups raise the conditional risk (Q = 6: 15.4% for k_w = 1 and 9.4% for k_w = 2, against 2.9% record only; Q = 12: 2.3% and 0.36%), because a smaller record unit needs more messages and leaves fewer for corroboration, and a forged witness is a global claim. k_w = 2 is safer than k_w = 1 in this respect.
4. The witness-versus-record cross-check is sound (honest witnesses are never contradicted; tested over every subset) but changes little: false witnesses fall by 1% to 20% only, because in most residual cases no record arrived to check against. It costs no bits; it is kept as an optional rule, not claimed as a safeguard.
5. At a bit-error rate of 1e-3 the expected rate with CRC-16, sanity and corroboration is about 0.3 false-certificate days per million for record-only blocks at Q = 6 (0.01 at Q = 12) and 1.0 to 1.7 per million for layered witness blocks at Q = 6 (0.08 to 0.5 at Q = 12); with CRC only it is 4 to 6 per million (table above). These are model estimates built on an upper bound for the CRC pass rate and on random-content forgeries.
6. The alternative is a longer check. CRC-24 cuts the forgery rate 256-fold and leaves 4 values per message instead of 5 (src/p3/capacity.py); fully recovered records fall from 0.915 to 0.862 at Q = 6 and from 0.992 to 0.982 at Q = 12 under independent loss (0.850 to 0.800 and 0.972 to 0.957 under bursts). Which point is right depends on the real channel error rate, which is not known here.

## Limits

- Forgeries change body bytes only; header forgeries (identity mismatch) are not in the sample and are handled by rejection on conflicting identities (tested for a single forgery, not at scale).
- Random-content forgeries are not adversarial; an adversary (tampering) needs authentication, which is out of scope.
- The conditional probabilities come from six development sites; the arrival model is independent loss 0.3 (Gilbert loss changes how often corroboration is possible).
- This is development data. The confirmation run must repeat the study on new data, with the receiver rules frozen as above.
- The frozen C2 failure (96 readings, v1) and the post-confirmation rule B stay reported as they are; frame v2 is a new design, not a re-evaluation of the confirmed one.
