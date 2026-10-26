# Step 11 results: denominators and uncertainty (review M17)

Code: `src/p3/cohort_exact.py` (exact G_cert of every four-parameter day), `src/p3/stats.py` (bootstrap analyses).
Outputs: `results/dev/cohort_exact.csv`, `stats_rq1.csv`, `stats_rq3.csv`, `stats_rq2.csv`, `stats_rq4.csv`,
`stats_env.csv`, `stats_multiday.csv`; log `results/stats_dev.log`. Development year 2023 only; the same scripts
will be applied to the confirmation data (Step 12).

## 1. Methods

- Unit of analysis: the record day; days are clustered within sites. Intervals are 95% percentile intervals from
  2,000 bootstrap resamples of sites (with replacement; fixed seed). Means are pooled over the days of the resampled
  sites; differences between designs are paired (the same days in both arms).
- Sensitivity: a site x month block bootstrap for the main G_cert estimate.
- Exact probabilities replace simulation wherever possible: for the record-first code and repetition a day's
  probability of full certification depends only on its record size, the tier, and the channel, so these designs,
  every k-th reading, and tag practice were evaluated exactly on all 10,342 four-parameter days. The fixed-K code
  and the reliable-link design need plans fitted to each budget and were evaluated on the 380 sampled test days.
  Monte Carlo error then remains only in Steps 4, 6, 7, and 8 (20 to 30 draws per day), where it is small compared
  with the between-site variation.

## 2. Denominators of the headline outcomes

| Outcome | Unit | n | Sites | Source |
|---|---|---|---|---|
| RQ1 record cost | four-parameter record day | 10,342 | 38 | `need2.csv` (all eligible days) |
| RQ3 G_cert: code, repetition, every k-th, tag | four-parameter record day | 10,342 | 38 | `cohort_exact.csv` (exact) |
| RQ3 G_cert: fixed-K code, reliable-link | sampled test day | 380 | 38 | `robust_exact.csv` (exact) |
| RQ3 byte-level confirmation | sampled test day x 30 draws | 380 | 38 | `robust_bytes.csv` |
| RQ2 sites with G7 >= 0.9 | site | 38 | 38 | `cohort_exact.csv` (exact, daily design) |
| RQ2 multi-day designs | test site (odd index) | 19 | 19 | `multiday.csv` (30 draws) |
| RQ4 plan sizing | site x pilot month (test sites) | 186 | 19 | `cohort_exact.csv` (exact) |
| Environmental decisions | four-parameter record day; event days as stated | 10,342 (DO 441, pH 414, EC 735 events) | 38 | `env_days.csv` (20 draws) |
| 7DADM decisions | seven-day window | 7,902 (2,399 events) | 38 | `env_7dadm.csv` |

## 3. RQ1: cost of the record (four-parameter days)

Median 27 B per day (21 to 30); 90th percentile 54 B (45 to 60); 99th percentile 114 B (93 to 132); median value
share 2.60% (2.34% to 3.12%); median byte share 4.81% (4.33% to 5.77%); days within one message 19.0% (13.9% to 24.4%).

## 4. RQ3: delivery designs (full cohort, exact)

| Q | Channel | Record-first code | Code - repetition | Code - every k-th | Code - tag | Site means of the code: min / median / max |
|---|---|---|---|---|---|---|
| 6 | iid 0.1 | 0.965 (0.946 to 0.982) | 0.030 (0.021 to 0.039) | 0.794 (0.756 to 0.831) | 0.828 (0.776 to 0.875) | 0.83 / 0.99 / 1.00 |
| 6 | iid 0.3 | 0.905 (0.873 to 0.934) | 0.092 (0.075 to 0.109) | 0.867 (0.839 to 0.892) | 0.809 (0.772 to 0.843) | 0.61 / 0.93 / 1.00 |
| 6 | iid 0.5 | 0.754 (0.707 to 0.798) | 0.126 (0.112 to 0.139) | 0.748 (0.703 to 0.792) | 0.703 (0.665 to 0.739) | 0.34 / 0.77 / 0.98 |
| 6 | bursty 0.3 | 0.835 (0.808 to 0.860) | 0.024 (0.019 to 0.029) | 0.731 (0.710 to 0.750) | 0.743 (0.713 to 0.772) | 0.59 / 0.85 / 0.96 |
| 6 | burst 6, 0.3 | 0.775 (0.755 to 0.794) | 0.005 (0.004 to 0.007) | 0.620 (0.593 to 0.645) | 0.679 (0.648 to 0.708) | 0.60 / 0.78 / 0.88 |
| 12 | iid 0.3 | 0.991 (0.984 to 0.996) | 0.039 (0.026 to 0.053) | 0.981 (0.974 to 0.986) | 0.845 (0.791 to 0.892) | 0.94 / 1.00 / 1.00 |
| 12 | bursty 0.3 | 0.971 (0.962 to 0.978) | 0.020 (0.014 to 0.027) | 0.892 (0.880 to 0.904) | 0.838 (0.791 to 0.880) | 0.91 / 0.98 / 1.00 |

On the 380 sampled test days (Q = 6), the code exceeded the channel-blind fixed-K code by 0.130 (0.096 to 0.166) at
iid 0.3 and 0.155 (0.125 to 0.187) under bursty loss, and the reliable-link design by 0.787 (0.759 to 0.814) and
0.513 (0.490 to 0.535). The sampled mean of the code agreed with the full-cohort value to within 0.013 in every
channel (for example 0.905 and 0.905 at iid 0.3).

Season (Q = 6): the monthly mean G_cert of the code ranged from 0.809 (July) to 0.958 (February) at iid 0.3 and from
0.744 to 0.902 under bursty loss, because summer records are larger. The site x month block bootstrap gave narrower
intervals than site clustering (0.889 to 0.919 against 0.873 to 0.934 at iid 0.3), so site clustering is the
conservative choice reported throughout.

## 5. RQ2 and RQ4 (daily record-first code, exact)

- Sites with G7 >= 0.9 (all 38 sites; for the daily design a day is certified within seven days exactly when its
  block decodes): Q = 6, 25 of 38 (66%; 50% to 79%) at iid 0.3 and 9 of 38 (24%; 11% to 37%) under bursty loss;
  Q = 12, 24, and 96, 38 of 38 under both; Q = 1, none.
- Plan sizing from a 28-day pilot started in each month (test sites; threshold T = 0.9 tuned on the even sites):
  sufficient in 87.6% (77.2% to 96.6%) of 186 site-pilots and never over-provisioned by more than one tier with an
  independent planning channel; 79.6% (68.6% to 89.7%) with a bursty planning channel. The worst pilot month was
  November (75% sufficient) for the independent and December (42%) for the bursty planning channel: pilots in the
  quiet season underestimate the summer need. This replaces the Step 7 estimate (FIFO buffer, first 28 days only;
  17 of 19), because Step 7 concluded that the buffer is not proposed.

## 6. Environmental and multi-day contrasts

Q = 6, paired by day, site-clustered intervals (`stats_env.csv`, `stats_multiday.csv`):
- Low DO missed (naive), code - every k-th: -0.109 (-0.236 to 0.000) with perfect delivery, which is not a clear
  difference; -0.180 (-0.269 to -0.103) at iid 0.3.
- pH out of range missed (naive), code - every k-th: +0.278 (0.192 to 0.338) with perfect delivery: the record is
  clearly worse for near-threshold pH peaks (Step 8).
- Conductance pulses missed, code - every k-th: -0.722 (-0.833 to -0.538) with perfect delivery.
- Low DO decided (three-valued), code - every k-th: +0.656 (0.585 to 0.726) with perfect delivery.
- G7, daily code - seven-day rotation (19 test sites): +0.125 (0.094 to 0.156) at iid 0.3, +0.037 (0.012 to 0.062)
  under bursts of 3, and -0.031 (-0.060 to -0.001) under bursts of 6: the rotation's advantage under long bursts is
  small but clear.

## 7. Consequences for the paper

- Every result in the manuscript will carry its unit, n, and sites (Section 2) and a site-clustered interval.
- The code-versus-repetition advantage is reported with its dependence on the channel; under long bursts it is
  0.005 (0.004 to 0.007).
- RQ4 is reported with its seasonal dependence; the pilot should not be run in the quiet season alone.
