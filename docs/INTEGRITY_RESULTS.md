# Integrity study for frame v2 (revision 2, Step 6b), development data only

Date: 2026-11-09 (rerun after the in-project review; first version 2026-11-06). Code: `src/p3/frame2.py` (codec), `src/p3/robust2.py` (experiment), `src/p3/integrity_report.py` (this document), `src/p3/certlang.py` (`witness_consistent`), `src/p3/capacity.py`. Specification and threat model: docs/FRAME_SPEC_V2.md. Results: `results/dev/robust2_stage1.csv`, `results/dev/robust2_summary.csv`, printout `results/robust2_stage12.txt`.
Command (from Paper3/): `python -I src/p3/robust2.py data/clean/usgs dev 6 10`, then `python -I src/p3/integrity_report.py`.
Status of every number: numerical (conditional on forced forgeries, random content, six development sites) or model-based (Stage 2). An AI assistant wrote and ran the code; a separate in-project AI reading found the forgery defect; no outside reviewer has read it.

## Method

- A corrupted message passes the per-message CRC-16 with probability about 2^-16 (an upper bound for random errors; every single-bit error and every burst of up to 16 bits is detected). A direct simulation would need millions of days, so the study has two stages.
- Stage 1 (measured): 6 development sites, 1,631 days, byte-level blocks (record only; record with a layered witness group of k_w = 1 or 2 carrying DO minimum, pH minimum and maximum, T maximum), Q = 6 and 12, independent loss 0.3. In each draw one arrived message is replaced by a CRC-valid forgery (1 to 3 distinct body bytes after the CRC changed by a nonzero XOR, CRC recomputed, so the message always differs from the original). At least 16,294 draws per cell. A day is false if any reading is certified outside tolerance, any witness code differs from the truth, or a value outside the site profile is accepted.
- Stage 2 (model): expected CRC-passing corruptions per day = Q x 0.7 x P(message corrupted) x 2^-16, times the Stage 1 conditional probability.
- Receivers: CRC only; plus the sanity rule (values inside the site profile and in planned order; censored witness codes rejected); plus corroboration (re-encode and compare when more messages arrive than needed; a mismatch rejects the block; a descriptor that differs between messages, or two CRC-valid copies of one message that disagree, also reject the block); both; both plus the witness-versus-record cross-check.

## Stage 1: share of days with a false certificate, given one CRC-valid forgery (day-clustered 95% bootstrap interval)

| Block | Q | CRC only | CRC + sanity | CRC + corroboration | CRC + sanity + corroboration | CRC + sanity + corroboration + cross-check |
|---|---|---|---|---|---|---|
| layered k1 | 6 | 0.4672 (0.4593 to 0.4753) | 0.3034 (0.2963 to 0.3103) | 0.2427 (0.2337 to 0.2519) | 0.1221 (0.1164 to 0.1280) | 0.1202 (0.1143 to 0.1259) |
| layered k1 | 12 | 0.2965 (0.2879 to 0.3046) | 0.1698 (0.1641 to 0.1752) | 0.0334 (0.0296 to 0.0379) | 0.0142 (0.0120 to 0.0164) | 0.0137 (0.0116 to 0.0159) |
| layered k2 | 6 | 0.4963 (0.4861 to 0.5061) | 0.3072 (0.3005 to 0.3139) | 0.1830 (0.1744 to 0.1925) | 0.0855 (0.0804 to 0.0910) | 0.0834 (0.0787 to 0.0886) |
| layered k2 | 12 | 0.2925 (0.2833 to 0.3006) | 0.1679 (0.1620 to 0.1735) | 0.0091 (0.0070 to 0.0116) | 0.0029 (0.0020 to 0.0042) | 0.0029 (0.0020 to 0.0040) |
| record | 6 | 0.4044 (0.3952 to 0.4131) | 0.1330 (0.1275 to 0.1386) | 0.0865 (0.0801 to 0.0926) | 0.0266 (0.0242 to 0.0300) | 0.0265 (0.0240 to 0.0291) |
| record | 12 | 0.2032 (0.1964 to 0.2107) | 0.0726 (0.0684 to 0.0767) | 0.0018 (0.0009 to 0.0030) | 0.0004 (0.0001 to 0.0009) | 0.0004 (0.0001 to 0.0008) |

## Stage 2: expected days with a false certificate per million days (independent loss 0.3)

| Corruption | Block | Q | CRC-16, CRC only | CRC-16, sanity + corroboration | CRC-24, sanity + corroboration |
|---|---|---|---|---|---|
| bit errors 1e-4 | layered k1 | 6 | 0.546 | 0.143 | 0.00056 |
| bit errors 1e-4 | layered k1 | 12 | 0.693 | 0.0331 | 0.00013 |
| bit errors 1e-4 | layered k2 | 6 | 0.58 | 0.0999 | 0.00039 |
| bit errors 1e-4 | layered k2 | 12 | 0.684 | 0.00688 | 2.7e-05 |
| bit errors 1e-4 | record | 6 | 0.473 | 0.0311 | 0.00012 |
| bit errors 1e-4 | record | 12 | 0.475 | 0.001 | 3.9e-06 |
| bit errors 1e-3 | layered k1 | 6 | 5.03 | 1.32 | 0.0051 |
| bit errors 1e-3 | layered k1 | 12 | 6.39 | 0.305 | 0.0012 |
| bit errors 1e-3 | layered k2 | 6 | 5.35 | 0.922 | 0.0036 |
| bit errors 1e-3 | layered k2 | 12 | 6.3 | 0.0634 | 0.00025 |
| bit errors 1e-3 | record | 6 | 4.36 | 0.287 | 0.0011 |
| bit errors 1e-3 | record | 12 | 4.38 | 0.00925 | 3.6e-05 |
| bit errors 1e-2 | layered k1 | 6 | 25.2 | 6.59 | 0.026 |
| bit errors 1e-2 | layered k1 | 12 | 32 | 1.53 | 0.006 |
| bit errors 1e-2 | layered k2 | 6 | 26.8 | 4.62 | 0.018 |
| bit errors 1e-2 | layered k2 | 12 | 31.6 | 0.318 | 0.0012 |
| bit errors 1e-2 | record | 6 | 21.8 | 1.44 | 0.0056 |
| bit errors 1e-2 | record | 12 | 21.9 | 0.0464 | 0.00018 |
| 10% of messages hit | layered k1 | 6 | 2.99 | 0.782 | 0.0031 |
| 10% of messages hit | layered k1 | 12 | 3.8 | 0.182 | 0.00071 |
| 10% of messages hit | layered k2 | 6 | 3.18 | 0.548 | 0.0021 |
| 10% of messages hit | layered k2 | 12 | 3.75 | 0.0377 | 0.00015 |
| 10% of messages hit | record | 6 | 2.59 | 0.171 | 0.00067 |
| 10% of messages hit | record | 12 | 2.6 | 0.0055 | 2.1e-05 |

The CRC-24 column divides by 256 (2^-8 more bits) and ignores the change in the Stage 1 conditional; its cost is in the findings.

## Findings

1. A per-message CRC with sanity rules and corroboration lowers the conditional false-certificate probability for record-only days from 40.4% (CRC only) to 2.7% at Q = 6, and from 20.3% to 0.04% at Q = 12.
2. The sanity rule alone (no extra bits) brings the Q = 6 record-only share to 13.3%; corroboration (free when extra messages arrive) removes most of the rest. Neither helps when exactly the needed number of messages arrives, which is the structural residual.
3. Layered witness groups raise the conditional risk (Q = 6: 12.2% for k_w = 1 and 8.6% for k_w = 2, against 2.7% record only; Q = 12: 1.42% and 0.29%), because a smaller record unit needs more messages and leaves fewer for corroboration, and a forged witness is a global claim. k_w = 2 is safer than k_w = 1 in this respect.
4. The witness-versus-record cross-check is sound (honest witnesses are never contradicted; tested over every subset) but changes little (false witnesses 322 against 243 for k_w = 1 at Q = 6); in most residual cases no record arrived to check against. It is not part of the receiver in the pre-registration.
5. At a bit-error rate of 1e-3 the expected rate with CRC-16, sanity and corroboration is 0.29 false-certificate days per million for record-only blocks at Q = 6 and 0.0092 at Q = 12; with CRC only it is 4.4 at Q = 6 (tables above). These are model estimates built on an upper bound for the CRC pass rate and on random-content forgeries.
6. The alternative is a longer check. CRC-24 cuts the forgery rate 256-fold and leaves 4 values per message instead of 5 (src/p3/capacity.py); fully recovered records fall from 0.915 to 0.862 at Q = 6 and from 0.992 to 0.982 at Q = 12 under independent loss (0.850 to 0.800 and 0.972 to 0.957 under bursts; computed by the capacity argument on the development plans, 2026-11-06). Which point is right depends on the real channel error rate, which is not known here.

## Limits

- Forgeries change body bytes only; a header forgery changes the block identity and is rejected when accepted messages disagree on it (unit-tested for single cases, not sampled at scale).
- Random-content forgeries are not adversarial; an adversary (tampering) needs authentication, which is out of scope.
- The conditional probabilities come from 6 development sites; the arrival model is independent loss 0.3 (Gilbert loss changes how often corroboration is possible).
- This is development data. The confirmation run repeats the study on new data with the receiver rules frozen as above.
- The frozen C2 failure (96 readings, frame v1) and the post-confirmation rule B stay reported as they are; frame v2 is a new design, not a re-evaluation of the confirmed one.

## Correction (2026-11-09): the first version of this study had a defective forgery function

The in-project review of 2026-11-09 found that the forgery function of the first run could choose the two CRC bytes (positions 3 and 4) among the bytes to change; the CRC is then recomputed, so some "forgeries" changed nothing and could never produce a false certificate. The review also tightened the receiver for the corroborating variants (a witness descriptor that differs between messages, or two CRC-valid copies of one message that disagree, now reject the block). This document replaces the earlier numbers; the superseded run is kept (results/dev/robust2_stage1_forge_noop_bug.csv, results/dev/robust2_summary_forge_noop_bug.csv, results/INTEGRITY_RESULTS_before_review_fix.md).
The two changes act in opposite directions, and the effect of the forgery fix alone can be read from the receivers that the new receiver rules do not touch. Ratio of the corrected to the superseded conditional share, over the six blocks (variant and Q): CRC only 1.05 to 1.11; CRC + sanity 0.96 to 1.10 (the superseded shares were therefore mostly understated by the defective forgery; part of the difference is sampling noise because the random draws changed). For the corroborating receivers the stricter rules lower the shares: CRC + corroboration 0.82 to 1.01; CRC + sanity + corroboration (the adopted receiver) 0.63 to 0.93. Any figure quoted from the earlier version (the claims register, the pre-registration, the review brief) was updated in the same change.
