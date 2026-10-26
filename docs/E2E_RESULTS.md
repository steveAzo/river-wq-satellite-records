# End-to-end byte-level results, development year 2023 (revision Step 4; review M4, M6, E1, E2)

All numbers on this page come from transmitted bytes: plan -> frame v1 (`docs/FRAME_SPEC.md`) -> Reed-Solomon ->
erasure -> header parsing, decoding, CRC -> positions -> reconstruction -> certificate (`src/p3/delivery.py`).
The server sees only the bytes that arrived. Decoding is deterministic given the arrived messages, so each
distinct arrival pattern of a plan is decoded once and cached (test `test_cache_does_not_change_outcomes`).
Data: per-channel loader (`src/p3/loader.py`), UTC days, 2023 only. 2024 is re-run once the revised method is
frozen (Steps 5 to 7), as a temporal re-test.

## 1. Delivery designs (RQ3), matched-channel tuning as in the draft

`src/p3/run_e2e.py`; `results/dev/e2e_results.csv`, `e2e_tuning.json`. Four-parameter record days, up to 20 per
site (seed 20261023): 10 tuning and 10 test days per site, 380 test days at 38 sites; 30 loss draws per test day
and setting. Each family's parameter was tuned for G_cert per (Q, loss, p); Step 5 replaces this with a
channel-blind choice. Chosen at Q = 6: K = 3, r = 2.

p = 0.3. Draft G: mask-based, exact values, draft loader (`results/dev/dev_results.csv`). Bytes: this run.

| Loss | Q | Design | Draft G | Bytes G_ok | Bytes G_cert | Share of plans bound |
|---|---|---|---|---|---|---|
| independent | 6 | erasure code | 0.897 | 0.781 | 0.780 | 0.834 |
| | | repetition | 0.853 | 0.643 | 0.636 | 0.834 |
| | | reliable-link | 0.340 | 0.210 | 0.116 | 0.982 |
| | | tag practice | 0.424 | 0.111 | 0.105 | 0.174 |
| | | every k-th | 0.275 | 0.134 | 0.040 | 0.332 |
| | 12 | erasure code | 0.973 | 0.960 | 0.960 | 0.968 |
| | | repetition | 0.941 | 0.855 | 0.847 | 0.945 |
| | 24 | erasure code | 0.997 | 0.994 | 0.994 | 0.995 |
| | | repetition | 0.973 | 0.943 | 0.942 | 0.945 |
| bursty | 6 | erasure code | 0.812 | 0.680 | 0.679 | 0.834 |
| | | repetition | 0.807 | 0.652 | 0.647 | 0.834 |
| | | reliable-link | 0.468 | 0.371 | 0.324 | 0.982 |
| | | tag practice | 0.411 | 0.111 | 0.104 | 0.174 |
| | | every k-th | 0.321 | 0.152 | 0.107 | 0.332 |
| | 12 | erasure code | 0.939 | 0.897 | 0.897 | 0.945 |
| | | repetition | 0.925 | 0.856 | 0.852 | 0.945 |

Full tables for Q in {1, 6, 12, 24} and p in {0.1, 0.3, 0.5}: `results/e2e_dev.log`.

Findings:
- Consistency with the analytic rules (record model, Section 6): reliable-link G_cert = 0.982 x 0.7^6 = 0.116
  (measured 0.116); every k-th = 0.332 x 0.7^6 = 0.039 (measured 0.040).
- Every design lost relative to the draft, for three reasons: the honest record is larger (self-contained,
  every channel present; RQ1 below), a message carries 5 values instead of 7, and success now means a
  server-verified certificate.
- For coded designs G_cert is almost equal to G_ok: the server can verify nearly every success. For every k-th
  reading, most of its within-tolerance days were unverifiable luck (0.134 vs 0.040).
- At Q = 6 the code reached 94% of its ceiling (0.780 of the 0.834 of days whose record fits K = 3 units).
- The code now beats repetition clearly under independent loss (+0.14 at Q = 6) and slightly under bursty
  loss (+0.03); the draft had them nearly equal. Paired intervals follow in Step 11.
- Tag practice fell most (0.424 -> 0.105): the smaller frame and broken-stick endpoints leave approximately three
  points per channel at Q = 6, which rarely meets the tolerance (17% of plans bound). Step 6 strengthens this
  baseline (multi-day buffer rotation and variants) so that the comparison does not rest on a weak baseline.

## 2. Self-contained versus chained days under loss (E2)

`src/p3/e2_anchor.py`; `results/dev/e2_anchor_Q6.csv`. 380 pairs of consecutive four-parameter days (up to 10 per
site, 38 sites), Q = 6, p = 0.3, 30 draws; the 12 transmissions of the two days pass through one loss process,
so bursts can span midnight. Results for day d+1:

| Loss | Design | Values needed, self / chain | G_cert self | G_cert chain | Chain: complete but anchor missing | Pairs with self >= chain |
|---|---|---|---|---|---|---|
| independent | erasure code | 10.4 / 9.6 | 0.762 | 0.737 | 6.0% | 96.8% |
| bursty | erasure code | | 0.668 | 0.576 | 13.5% | 96.8% |
| independent | repetition | | 0.618 | 0.529 | 12.5% | 96.8% |
| bursty | repetition | | 0.643 | 0.559 | 12.4% | 96.8% |

Chaining saves approximately 0.8 values per day, yet self-contained days were certified more often in every
setting (+0.03 to +0.09), because a chained day depends on the previous day's final message. Bursts across
midnight hurt chaining most. This answers review M3: the anchor is now delivered by construction (each day
carries its own first value), and the alternative was measured rather than assumed.

## 3. RQ1 (cost of the record) under the revised method

`src/p3/need2.py`; `results/dev/need2.csv`; full table in `docs/COHORT_AUDIT.md`. Four-parameter days (10,342):
median 27 B (p99 114 B, max 219 B), value share 2.60%, byte share 4.81%, median 2 messages (p99 8, max 15),
against at least 32 messages for the raw readings at 15 min. Draft (2023, same tolerance): 18 B, 2.1%.

## 4. What is still to come for a complete Step 4

- RQ2 (buffering) and RQ4 (plan sizing) on bytes: Step 7 (packet-level multi-day FIFO), because the draft's
  queue model is replaced rather than re-run.
- Exact-value vs quantised vs missed-anchor error CDF (review Fig. B): data are in hand (draft results, this run,
  E2); the figure is drawn in Step 13.
- Errors at parameter-range limits: no USGS reading lies outside the quantiser ranges (T -0.1 to 33.3 degC,
  DO 0 to 24.9 mg/L, pH 6.0 to 10.1, EC 28 to 4,020 uS/cm over both years); injected out-of-range tests: Step 9.
