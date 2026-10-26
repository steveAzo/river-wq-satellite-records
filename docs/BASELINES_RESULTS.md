# Step 6 results: stronger baselines (review M14, E7)

Code: `src/p3/fountain.py` (systematic random linear code), `delivery.py` (rlnc_rec, rep_block_rec, tag_rec),
`run_robust.py` (exact table), `robust_bytes.py` (byte-level confirmation). Tests: `tests/test_baselines.py`.
Data: 2023 development year, the 380 test days of Steps 4 and 5 (38 sites), 15 channels, Q = 1, 6, 12, 24,
30 loss draws per day shared by all designs (common random numbers). Outputs: `results/dev/robust_bytes.csv`,
`results/dev/robust_exact.csv` (recomputed), `results/robust_eval_dev.log`.

Equal footing: every design uses frame v1 (same 23-B payload), at most Q messages per day, and delivers within
the day (no buffering, so equal acquisition delay). Hardware overhead differs only in encoding effort (none for
repetition; GF(2^8) table look-ups for the codes); it is measured in Step 10. The multi-day tag buffer rotation
needs the multi-day framework and is compared in Step 7 at equal acquisition delay.

## 1. Byte-level results at Q = 6 (G_cert; G_ok and certified reading share in `robust_bytes.csv`)

| Design | iid 0.1 | iid 0.3 | iid 0.5 | bursty 0.3 | burst 6, 0.3 |
|---|---|---|---|---|---|
| Record-first Reed-Solomon (proposed) | 0.970 | 0.909 | 0.739 | 0.833 | 0.774 |
| Record-first fountain (random linear) | 0.970 | 0.908 | 0.738 | 0.833 | 0.774 |
| Record-first repetition, interleaved | 0.933 | 0.804 | 0.607 | 0.807 | 0.769 |
| Record-first repetition, block order | 0.935 | 0.799 | 0.604 | 0.699 | 0.675 |
| Tag policy with the record's units | 0.801 | 0.701 | 0.539 | 0.634 | 0.615 |
| Fixed K, channel-blind | 0.833 | 0.775 | 0.543 | 0.673 | 0.631 |
| Fixed r repetition, channel-blind | 0.809 | 0.632 | 0.359 | 0.649 | 0.627 |
| Tag practice (broken-stick content, channel-blind share 0.5) | 0.155 | 0.108 | 0.057 | 0.107 | 0.109 |
| Reliable-link | 0.520 | 0.123 | 0.017 | 0.321 | 0.474 |
| Every k-th reading | 0.175 | 0.042 | 0.006 | 0.111 | 0.162 |

Certified reading share (partial certificates) at Q = 6: record-first code 0.938 / 0.867 / 0.799 (iid 0.3 /
bursty 0.3 / burst 6); interleaved repetition 0.908 / 0.876 / 0.813; reliable-link 0.658 / 0.672 / 0.678.

## 2. Findings

- Fountain-style coding: the systematic random linear code matched Reed-Solomon to within 0.001 everywhere at
  Q = 6 (rank deficiency over GF(2^8) is rare). As Proposition 2 requires, it was never better on any arrival mask
  (exhaustive test). Its practical advantage (rateless) matters only if the quota is unknown in advance.
- Tag practice, separated into content and policy (independent p = 0.3): record content with cyclic repetition
  0.804; the same content with the tag's random-with-replacement policy 0.701 (the policy costs 0.10); broken-stick
  content with the tag policy 0.108 (the content costs approximately 0.59). Tag practice loses mainly because its
  points are not chosen against a tolerance, not because of how it transmits.
- Interleaving: irrelevant under independent loss (0.804 vs 0.799) but worth +0.108 under bursty loss
  (0.807 vs 0.699) and +0.094 with bursts of 6.
- Code versus the strongest baseline (interleaved record-first repetition): +0.105 at independent p = 0.3; +0.026
  under bursty p = 0.3; +0.005 with bursts of 6. Under long bursts the two are practically equal, and repetition
  gives slightly more partial certification (0.876 vs 0.867; 0.813 vs 0.799), because when a code block fails only
  its systematic units are usable, whereas every repeated unit has several chances.
- Byte level versus exact: over 525 design-channel-tier cells, mean absolute difference 0.0014, largest 0.011
  (Monte Carlo error of 30 draws per day); no systematic bias.

## 3. Consequences for the paper

- The comparison set: record-first code (proposed), record-first fountain, interleaved and block repetition,
  tag policy with record content, tag practice, fixed-parameter channel-blind code and repetition, reliable-link,
  every k-th reading. Repetition is reported prominently, including the near-ties under bursty loss and its
  slightly larger partial certification.
- Claim wording: the code is never worse than repetition at full certification and is clearly better under
  independent loss; under bursty loss the advantage is small.
