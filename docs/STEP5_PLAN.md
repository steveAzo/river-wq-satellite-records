# Step 5 analysis plan: channel-blind configuration (review M8, E3, Fig. C)

Written 2026-10-25 BEFORE any Step 5 result was computed. Development data (USGS 2023) only.

## Data and sample
The same sample as Step 4 (`run_e2e.sample_site`): four-parameter record days, up to 20 per site, seed
20261023; even-indexed days = tuning, odd-indexed days = test (380 test days, 38 sites).

## Designs
- Parameter-free (record-first): mds_rec, rep_rec (`delivery.py`).
- Parametric: mds_K (K = 1..Q; even K at Q = 24), repeat_r (r = 2, 3, 4, 6; cyclic fill), tag share
  (0.25, 0.5, 0.75, 1.0).
- Fixed: reliable, every_k.
Tiers Q = 1, 6, 12, 24.

## Channels
- Tuning set (six): independent and Gilbert (mean burst 3), p = 0.1, 0.3, 0.5.
- Test set (15): independent and Gilbert (burst 3) at p = 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, plus Gilbert
  with mean burst 6 at p = 0.3. Eight of these were never used for tuning.

## Outcome
G_cert(day, design, channel) = bound x P(full delivery), computed exactly (`analytic.py`) where the unit order has
at most 16 distinct units or sends each unit once, otherwise by 20,000 vectorised draws (flagged). Means over days.

## Selection rules (fixed now)
- Oracle for channel c: the parameter with the highest mean tuning-day G_cert under c (computed for every test
  channel, including those outside the tuning set).
- Primary channel-blind rule for parametric designs: minimax regret over the six tuning channels on tuning days,
  i.e. argmin_j max_c [G(oracle_c, c) - G(j, c)].
- Sensitivity rule: the highest mean G_cert over the six tuning channels.
- Mismatch: the parameter tuned for an assumed channel (any of the six) evaluated under every true test channel.

## Reported on test days
- G_cert for every design under every true channel; regret = oracle(c) - design; worst-case regret over the
  15 channels; the mismatch heatmap (Fig. C) of assumed x true channel for mds_K and the difference from repetition.
- Pilot scenario: the server estimates p (share of missing message indices) and burstiness (mean run length of
  missing indices against the independent-loss expectation 1 / (1 - p)) from 28 days x Q messages, and the node
  is reconfigured with the tuned parameter of the nearest tuning channel; 1,000 pilot replicates per true channel.
- Byte-level confirmation: 30 draws of the byte pipeline per test day for the record-first designs, the robust
  parametric choices, reliable, and every_k under all 15 channels (G_cert, G_ok, certified share), with the
  agreement between simulated and exact G_cert.

## Expectation stated in advance
By Proposition 2, mds_rec should have zero regret against every unit-level design on every channel (up to
the oracle being tuned on other days). If it does not, the implementation or the proposition is wrong.
