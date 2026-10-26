# Step 8 analysis plan: environmental use of the delivered records (review M16, E5, Table C)

Written 2026-10-25 BEFORE any Step 8 comparison was computed. Development data (USGS 2023) only. The event base
rates below were counted on the true records to make sure each criterion has events; they say nothing about designs.

## Question
Do the delivered records support the decisions a monitoring agency makes, compared with the full sensor record
and with baselines at the same message quota, under message loss? The reference ("truth") is the full sensor
record; sensor accuracy is outside this study.

## Data
All 10,342 four-parameter record days of 2023 (38 sites).

## Designs and conditions
Designs (single-day delivery, frame v1): record-first code (proposed), record-first interleaved repetition, every
k-th reading (periodic telemetry), satellite-tag practice (broken-stick, channel-blind share from Step 5).
Tiers Q = 6 and 12. Conditions: perfect delivery (content only), independent loss p = 0.3, Gilbert p = 0.3 with
bursts of 3; 20 draws per day under loss. The server reconstructs from the values it received (decoding rule of
Steps 4 to 7) and certifies with `record.certify`.

## Criteria (thresholds fixed now)
| Criterion | Rule on a day | Source | 2023 event days |
|---|---|---|---|
| Low dissolved oxygen | daily minimum DO < 5.0 mg/L | US EPA (1986) DO criteria; 5 mg/L is a common state daily-minimum standard | 441 (12 sites) |
| pH outside range | any pH < 6.5 or > 9.0 | US EPA (1986) Quality Criteria for Water (freshwater aquatic life) | 414 (13 sites) |
| Warm water (multi-day regulatory metric) | 7-day average of daily maximum T (7DADM) > 20 degC | US EPA Region 10 (2003) temperature guidance (migration criterion) | 3,132 days with daily max > 20 |
| Rapid conductance change | some 1-h change in EC > 10% | event definition for pulses (e.g. discharges) | 735 (26 sites) |

## Outcomes per design and condition
1. Decisions for DO, pH, and 7DADM:
   - two-valued (naive): exceedance if the reconstruction crosses the threshold; false negatives (missed exceedance
     days) and false positives against the truth;
   - three-valued (certified): certainly exceeded / certainly not / undetermined, using x^ +/- delta only on
     certified readings; reported: share of days decided, and errors (expected 0 by Proposition 1);
   - a day with no reconstruction (nothing received) counts as undetermined (three-valued) and as "no exceedance"
     (two-valued), so missed data show up as false negatives.
2. Daily statistics: absolute error of daily minimum, maximum, and mean per parameter, in units of the parameter's
   tolerance at the true value; share of days within tolerance.
3. Timing: error (minutes) of the time of the daily maximum of T and DO, on days where the true daily range
   exceeds two tolerances (otherwise the peak time is undefined within tolerance).
4. DO diel range (daily max - min; a proxy used in stream-metabolism work): absolute error.
5. Rapid EC change: detection (event present if the reconstructed 1-h relative change exceeds 10%), misses, and
   the timing error of the largest 1-h change.
6. Decision delay: all designs here deliver the next day; multi-day designs' delays come from Step 7.

## Aggregation and uncertainty
Rates pooled over days; for loss conditions averaged over draws. Paired cluster-bootstrap intervals by site
(Step 11) for the main contrasts: record-first code vs every k-th reading and vs repetition, for DO false negatives
and the share of days decided.

## Expectations stated in advance
- Under perfect delivery, the record-first code makes no three-valued error and its daily statistics are within
  tolerance on every day (Proposition 1); the share of undetermined days is the price of honesty near thresholds.
- Periodic telemetry at the same quota will miss short excursions (low DO at night, EC pulses).
