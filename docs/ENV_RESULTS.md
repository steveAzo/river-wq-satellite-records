# Step 8 results: environmental decisions from delivered records (review M16, E5, Table C)

Plan fixed before the run (thresholds confirmed by the user): `docs/STEP8_PLAN.md`. Code: `src/p3/env.py`,
`run_env.py`, `env_eval.py`; `record.interval`. Tests: `tests/test_env.py` (every decision outcome exercised and
never wrong over all loss patterns), `tests/test_record.py::test_interval_*`.
Data: all 10,342 four-parameter record days of 2023 (38 sites), 7,902 seven-day windows. Designs at Q = 6 and 12;
perfect delivery, independent p = 0.3, Gilbert p = 0.3 (20 draws). Outputs: `results/dev/env_days.csv`,
`env_7dadm.csv`, `env_summary.csv` (Table C); log `results/env_eval_dev.log`.

## 1. Certain decisions are never wrong, and the record decides most days

Three-valued decisions (certainly exceeded / certainly not / undetermined) made from certified readings were wrong
on 0 days for every design, condition, and criterion, as Proposition 1 and the server-side interval guarantee.

Share of days decided (certain yes or certain no), Q = 6:

| Criterion | Record-first code, perfect / iid 0.3 / bursty 0.3 | Every k-th reading, perfect / iid 0.3 | Tag practice, perfect |
|---|---|---|---|
| Low DO (all days) | 0.975 / 0.919 / 0.855 | 0.319 / 0.157 | 0.154 |
| Low DO (event days only) | 0.667 / 0.612 / 0.556 | 0.018 / 0.014 | 0.002 |
| pH out of range (all days) | 0.960 / 0.912 / 0.841 | 0.318 / 0.114 | 0.153 |
| pH out of range (event days only) | 0.464 / 0.407 / n/a | 0.060 / 0.058 | 0.019 |
| 7DADM > 20 degC (windows) | 0.985 / 0.775 / 0.486 | 0.125 / 0.004 | 0.035 |

On the event days it does not decide, the record says "undetermined"; it never says "no exceedance" on an
exceedance day. Baselines cannot tell their reliable answers from their unreliable ones.

## 2. Naive (two-valued) decisions: the record's tolerance hides near-threshold excursions

Missed exceedance days / event days with the naive rule (Q = 6):

| Criterion (events) | Record code perfect / iid 0.3 / bursty 0.3 | Every k-th perfect / iid 0.3 | Tag perfect / iid 0.3 |
|---|---|---|---|
| Low DO (441) | 0.116 / 0.187 / 0.257 | 0.224 / 0.367 | 0.093 / 0.308 |
| pH out of range (414) | 0.374 / 0.446 / 0.485 | 0.097 / 0.185 | 0.080 / 0.102 |
| 7DADM > 20 degC (2,399 windows) | 0.009 / 0.274 / 0.580 | 0.019 / 0.492 | 0.017 / 0.923 |
| Conductance pulse > 10% in 1 h (735) | 0.114 / 0.186 / 0.269 | 0.837 / 0.886 | 0.758 / 0.782 |

No design raised false alarms (all rates <= 0.001).
- Short events: the record caught conductance pulses far better than periodic or tag telemetry (11% missed
  against 84% and 76% with perfect delivery), and located the largest 1-h change within 38 min on average
  against 268 and 309 min.
- Near-threshold events: pH exceedances in these data are mostly peaks of 9.1 to 9.2 against a tolerance of 0.2; a
  record that keeps every reading within tolerance may flatten such a peak below 9.0. Read naively, the record then
  missed more pH exceedances (37%) than periodic samples (10%) or broken-stick points (8%). The three-valued
  reading turns these into "undetermined" instead of "no". The general lesson: a tolerance chosen for record
  accuracy limits the resolution of decisions whose thresholds lie within one tolerance of typical values; a
  decision-aware tolerance (tighter near thresholds) would address this and is future work.
- Under loss, every design missed more; the record degraded least for DO and EC, and periodic telemetry kept its
  advantage for naive pH.

## 3. Daily statistics, timing, and diel range (Q = 6)

| Outcome | Record code perfect / iid 0.3 / bursty 0.3 | Every k-th perfect / iid 0.3 | Tag perfect / iid 0.3 |
|---|---|---|---|
| Daily max T within tolerance | 1.000 / 0.958 / 0.896 | 0.852 / 0.649 | 0.887 / 0.620 |
| Daily min DO within tolerance | 0.997 / 0.956 / 0.888 | 0.958 / 0.823 | 0.951 / 0.810 |
| Daily mean DO within tolerance | 0.996 / 0.955 / 0.887 | 0.997 / 0.850 | 0.913 / 0.851 |
| Certified reading share | 0.991 / 0.945 / 0.876 | 0.322 / 0.214 | 0.154 / 0.126 |
| Time of daily max T, mean error (min) | 143 / 157 / 153 | 167 / 341 | 165 / 165 |
| Time of daily max DO, mean error (min) | 246 / 275 / 274 | 229 / 384 | 243 / 421 |
| DO diel range, mean error (mg/L) | 0.44 / 0.49 / 0.48 | 0.21 / 0.40 | 0.20 / 0.52 |

With perfect delivery at Q = 6, the record misses within-tolerance statistics only on the 1.8% of days whose record
exceeds the tier (and DO means, whose tolerance rule is convex; Section 8 of the plan). Under loss it keeps daily
extremes within tolerance on 89 to 96% of days against 62 to 82% for the baselines. But shape quantities below the
tolerance (time of the daily peak, the diel DO range used in metabolism work) are not better than periodic
samples: a record allowed to deviate by 0.3 mg/L may flatten a diel peak by up to that amount and make its time
ill-defined. At Q = 12, periodic samples were clearly better for these (peak time 90 vs 143 min; range 0.12 vs
0.43 mg/L).

## 4. Consequences for the paper

- The environmental claim is decision-oriented and conditional: certified records never give a wrong certain
  decision, decide most days, and catch short pulses that periodic and tag telemetry miss; they do not resolve
  quantities finer than the tolerance (near-threshold exceedances read naively, diel peak timing, diel range), where
  periodic sampling at the same quota is as good or better.
- Table C of the review: `results/dev/env_summary.csv`.
- Future work: decision-aware tolerances; coding across days (Step 7).
- Uncertainty intervals for the main contrasts follow in Step 11.
