# Cohort audit (revision Step 1; review M10, M11, Table B)

Script: `src/p3/cohort.py` (mirrors `data.load_site`; asserts the same eligible count per site).
Outputs: `results/cohort/{dev2023,usgs2024}_{sites,flow,days}.csv`. Run 2026-10-25.

## Flow (current loader)

| Stage | 2023 (dev) | 2024 |
|---|---|---|
| Sites | 39 | 39 |
| Sites with all four parameters kept | 34 | 33 |
| Candidate site-days | 13,252 | 13,547 |
| Dropped: gap > 2 readings in a kept channel | 2,266 | 1,320 |
| of which at least one channel was complete | 1,432 | 846 |
| Dropped: no anchor | 8 | 6 |
| Eligible site-days | 10,978 | 12,221 |
| Eligible, four parameters | 9,625 | 10,164 |
| Eligible, fewer than four | 1,353 | 2,057 |

Intervals (loader's median step): 2023 5 min x3, 15 x25, 30 x10, 60 x1; 2024 5 x1, 15 x28, 30 x9, 60 x1.
Eight sites changed interval or kept-parameter set between the years.

## Size metrics with denominators (2024)

| Cohort | n site-days | Median bytes | p99 bytes | Value share (kept / raw values) | Byte share (24-bit kept / 13-bit raw) |
|---|---|---|---|---|---|
| All eligible (paper's headline) | 12,221 | 15 | 108 | 1.82% | 3.37% |
| Four-parameter days | 10,164 | 18 | 114 | 1.56% | 2.88% |
| Fewer-parameter days | 2,057 | 12 | 57 | 2.78% | 5.13% |
| Site-equal (median of site medians) | 39 sites | 15 | n/a | 2.08% | 3.85% |
| 60-min site (01463500) | 361 | 30 | 67 | 10.42% | 19.23% |

Consequences for the paper:
- The headline "15 B/day, 1.8% of the raw readings" pooled four-, three-, and one-parameter days. On four-parameter days the median is 18 B (value share 1.56%).
- "1.8% of the raw readings" is a count ratio. In bytes against the smallest raw form (13-bit readings, implicit time) the ratio is approximately 1.85x larger (3.4% pooled).
- The intro example (1,296 B raw = 144 x 9 B with 2 B/value + 1 B slot) used a different serialisation from the kept values (24 bit). Replace it with one codec for both sides (Step 2).
- The share rises steeply with the interval: 0.7% at 5 min, 10.4% at 60 min. Report by interval.

## Loader artefacts found (fix in Step 4, new per-channel data model)

1. Mixed native intervals: at 01400500 (2023) T is 5-min and DO/pH/EC 15-min; at 14162500 T is 15-min and DO/pH/EC 30-min. The loader grids all channels at the finest step, so the coarser channels show approximately 33% or 50% coverage and are dropped for the whole year although never missing.
2. Seasonal sensors: DO at 03075070 (2024) runs May to October only; DO/pH/EC at 01438500 (2024) are off April to August; T at 14210000 (2023) runs January to March only. The whole-year 50% coverage rule drops the channel on every day, including days on which it is complete.
3. A single gappy channel drops the whole site-day (1,432 and 846 days had at least one complete channel).

Revised rule (Step 4): each channel keeps its native interval; a channel-day is eligible when its gaps are <= 2 readings; a site-day carries its eligible channels; the primary cohort is four-parameter site-days, with the mixed cohort and site-equal results reported separately, and results by interval.

## Per-channel loader (Step 4a; `src/p3/loader.py`, `src/p3/cohort2.py`)

Each channel keeps its native interval per UTC day (5, 10, 15, 20, 30, or 60 min); runs of at most two missing
readings with valid neighbours on both sides are bridged (the draft's `interpolate(limit=2)` also filled the first
two readings of longer gaps); a record day carries its eligible channels. Outputs:
`results/cohort/{dev2023,usgs2024}_v2_{channel_days,record_days}.csv`. Tests: `tests/test_loader.py`.

| | 2023 draft loader | 2023 per-channel | 2024 draft loader | 2024 per-channel |
|---|---|---|---|---|
| Record days (>= 1 channel) | 10,978 | 12,674 | 12,221 | 13,080 |
| Four-parameter days | 9,625 (34 sites) | 10,342 (38 sites) | 10,164 (33 sites) | 11,168 (38 sites) |
| Four-parameter days with mixed intervals across channels | 0 (dropped) | 632 | 0 (dropped) | 320 |
| Record days with 1 / 2 / 3 channels | n/a | 48 / 131 / 2,153 | n/a | 297 / 175 / 1,440 |

Days are now UTC days (the draft used windows starting at each file's first timestamp, i.e. local midnight).

## RQ1 under the revised method (2023 development data; `results/dev/need2.csv`)

Self-contained, quantisation-exact record at tau = 1, frame v1 (5 values per 23-B message).

| Cohort | n | Median bytes (p90 / p99 / max) | Value share | Byte share | Messages median (p99 / max) | Raw readings, messages >= |
|---|---|---|---|---|---|---|
| Four-parameter (primary) | 10,342 | 27 (54 / 114 / 219) | 2.60% | 4.81% | 2 (8 / 15) | 32 |
| Fewer-parameter | 2,332 | 15 (33 / 89 / 225) | 2.08% | 3.85% | 1 (6 / 15) | 24 |
| Four-parameter, 5-min | 339 | 27 | 0.78% | 1.44% | 2 | 94 |
| Four-parameter, 15-min | 6,657 | 27 | 2.34% | 4.33% | 2 | 32 |
| Four-parameter, 30-min | 2,354 | 21 | 3.65% | 6.73% | 2 | 16 |
| Four-parameter, 60-min | 360 | 36 | 12.50% | 23.08% | 3 | 8 |
| Site-equal (four-parameter) | 38 sites | 27 | 2.73% | 5.05% | | |

Example for the introduction (replaces 1,296 B / 62 messages): a 10-min four-parameter node produces 576 readings
per day, at least 936 B at 13 bits each, or at least 47 messages of 20 B of unit payload.
