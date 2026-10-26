# Step 7 results: packet-level multi-day replay (review M9, E4, Fig. D; RQ2, RQ4)

Plan fixed before the run: `docs/STEP7_PLAN.md`. Code: `src/p3/multiday.py`, `run_multiday.py`, `multiday_eval.py`;
`delivery.receive_multi`. Tests: `tests/test_multiday.py`. Data: 2023, every record day of 38 sites replayed in
date order (plans cached in `results/dev/plans/`), 15 channels, 30 draws, tiers 1, 6, 12, 24, 96.
Outputs: `results/dev/multiday.csv`, `multiday_summary.csv`, `multiday_sizing.csv`, `multiday_choice.json`;
log `results/multiday_eval_dev.log`. Parameters chosen on the 19 even-indexed sites; results on the 19 others.

Byte check: draw 0 of three channels (independent p = 0.3; Gilbert p = 0.3 with bursts of 3 and 6) for every site,
tier, and design was decoded from its bytes (multi-day blocks, day offsets, split days): 6,270 schedule-channel
replays, no mismatch with the decoding rule used for the other draws.

## 1. RQ2 revisited: buffering does not help once the record is honest

G7 (four-parameter days certified within 7 days, pooled over the test sites):

| Q | Design | iid 0.1 | iid 0.3 | iid 0.5 | bursty 0.3 | burst 6, 0.3 |
|---|---|---|---|---|---|---|
| 1 | FIFO buffer, record-first code | 0.095 | 0.066 | 0.043 | 0.073 | 0.075 |
| 1 | Daily record-first code (no buffer) | 0.196 | 0.153 | 0.109 | 0.155 | 0.153 |
| 6 | FIFO buffer (rho = 1, chosen) | 0.953 | 0.881 | 0.734 | 0.823 | 0.772 |
| 6 | Daily record-first code | 0.956 | 0.892 | 0.744 | 0.829 | 0.769 |
| 6 | 7-day rotation, cyclic (repetition) | 0.873 | 0.767 | 0.609 | 0.791 | 0.800 |
| 6 | 7-day rotation, random, record content | 0.744 | 0.655 | 0.528 | 0.647 | 0.639 |
| 6 | 7-day rotation, random, broken-stick (CTD-SRDL practice) | 0.124 | 0.080 | 0.039 | 0.080 | 0.081 |
| 12 | Daily record-first code | 0.997 | 0.988 | 0.951 | 0.967 | 0.915 |
| 12 | 7-day rotation, cyclic | 0.969 | 0.929 | 0.837 | 0.938 | 0.944 |
| 24 | Daily record-first code | 1.000 | 1.000 | 0.997 | 0.999 | 0.987 |

Test sites with G7 >= 0.9 (of 19): Q = 6: daily code 13 (independent p = 0.3) and 5 (bursty); cyclic rotation
5 and 6. Q = 12: daily code 19 and 19. Q = 24: all designs with record content 17 to 19.

Findings:
- The FIFO buffer was never better than daily record-first coding at Q >= 6 (differences -0.011 to +0.007) and
  much worse at Q = 1, where the backlog grew without bound (p95 168 units, maximum 460), fresh days waited behind
  old ones, and 3,018 record days hit the 63-day limit. As stated in advance, a buffer cannot raise a block's
  decoding probability; at Q >= 6, 98% of days fit their tier already. The draft's RQ2 result (35/39 sites at six
  messages a day with a buffer) came from the capacity model and the smaller, anchored record; it does not survive.
- Spreading copies of a day over the following seven days (cyclic rotation) beat the single-day code under long
  bursts (G7 0.800 vs 0.769 at Q = 6, bursts of 6) because it adds time diversity, but it delivered later: G1 0.245
  against 0.769 and 0.204 against 0.892 under independent loss. Under independent loss and bursts of 3, the daily
  code was better at G7 too. Coding across days (spreading a code block's parity over later days) would combine
  both advantages; it was not designed or tested here and is listed as future work rather than added after seeing
  these data.
- Satellite-tag practice with its own content (broken-stick points, random rotation) certified few days (G7 0.080
  at Q = 6; 0.479 at Q = 24); with the record's content the same policy reached 0.655 and 0.972.

## 2. Delay and backlog (daily record-first code, Q = 6, independent p = 0.3)

Every certified day was certified the next day (delay 1, p95 1): the daily code has no queue. For the FIFO buffer at
Q = 6 the backlog was empty on at least 95% of days (p95 0 units; maximum 73 units after a day whose record exceeded
the tier). Delay distributions per design and channel: `multiday.csv` (Fig. D). The burst-at-midnight example for
Fig. D will be drawn from this replay in Step 13.

## 3. RQ4: plan sizing from a 28-day pilot

FIFO buffer with the chosen rho (equal to the daily code at Q >= 6). Planning channel independent p = 0.3:
threshold T = 0.99 (tuned on the even sites); on the 19 test sites the pilot chose a sufficient tier for 17 sites
(0.895) and over-provisioned by more than one tier at none (1.000). With a bursty planning channel: 19 of 19
sufficient (1.000), none over by more than one tier. Draft (2024, capacity model): 84.6% and 100%.

## 4. Consequences for the paper

- RQ2 changes from "buffering lets six messages a day suffice" to: daily record-first coding needs no buffer; six
  messages a day give G7 >= 0.9 at 13 of 19 test sites under independent loss of 0.3 and 5 of 19 under bursty
  loss; twelve messages a day give it at all 19. The draft's H2 and H2b cannot be claimed.
- The proposed design for the paper is daily record-first coding. The FIFO buffer is reported as a negative result.
- Multi-day repetition's advantage under long bursts (at the cost of delay) is reported, with coding across days
  as future work.
