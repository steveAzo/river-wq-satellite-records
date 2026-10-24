# Paper 3 confirmation results (frozen plan of 2026-10-23)

**Data:**
- **Sealed set:** USGS 2024, 39 sites, 12,221 site-days. The seal was verified (39/39 checksums OK) immediately before first use.
- **Low-cost deployments:** InWaterSense node 1 (Kosovo) and Weija (Ghana), first used here.

**What was applied unchanged:** the plan (`STUDY_PLAN.md`), the frozen design parameters (`results/dev/dev_tuning.json`, `sizing_tuning.json`) and the checksummed toolkit (`FREEZE.md`). The confirmation used only new wrapper scripts (`lowcost.py`, `run_confirm.py`, `confirm_pooling.py`), which call the frozen modules without changing them.

**Logs and outputs:** `results/confirm/` (seal_check, need_2024, pooling_2024, rq3_2024, need_lowcost, rq3_lowcost); `results/lowcost/`.

## Verdicts

| Hypothesis | Threshold | 2024 result | Verdict |
|---|---|---|---|
| H1 need (RQ1) | median need ≤ 5% of raw | **1.8%** (15 B/day; p90 45 B, p99 108 B, max 201 B; at most 10 × 23-B messages) | Pass |
| H2 buffering, 6 messages/day, independent p = 0.3 (RQ2) | ≥ 75% of sites with ≥ 90% of days guaranteed within 7 d | **35/39 = 90%** | Pass |
| H2b buffering, 12 messages/day, bursty p = 0.3 | ≥ 85% of sites | **35/39 = 90%** | Pass |
| H3 code vs reliable-link design, 6 messages/day, independent p = 0.3 (RQ3) | median G ratio ≥ 2 | **3.5** (0.933 vs 0.267; mean ratio 2.59) | Pass |
| H4 code vs satellite-tag practice, same setting | median G difference ≥ 0.25 | **+0.333** (mean +0.46) | Pass |
| H5 code and repetition each ≥ reliable-link + 0.2, Q ∈ {6, 12, 24}, p ∈ {0.3, 0.5}, both loss models | all 12 settings | all 12; smallest margin 0.339 (repetition, 6 messages/day, bursty p = 0.3) | Pass |
| H6 sizing from a 28-day pilot (RQ4) | sufficient ≥ 80%; over by ≤ 1 tier ≥ 80% | **84.6%; 100%** | Pass |
| H7 InWaterSense need ≥ 3 × the USGS median | ratio ≥ 3 | **3.9** (58.5 vs 15 B/day) | Pass, indicative only: 22 complete days |

**Reported as pre-stated limitations, not hypotheses:**
- Under bursty loss, 6 messages/day kept ≥ 90% of days guaranteed at only 17/39 sites (development: 18/39). Such links need 12 messages/day.
- At 1 message/day, no design exceeded G = 0.56.

## Further results (descriptive)

**RQ3 on 2024, mean G** (6 messages/day; independent / bursty loss, p = 0.3):

| Design | Independent | Bursty |
|---|---|---|
| Code (mds) | 0.891 | 0.812 |
| Repetition | 0.850 | 0.811 |
| Satellite-tag practice (srdl_style) | 0.431 | 0.413 |
| Reliable-link optimum | 0.345 | 0.472 |
| Raw periodic | 0.283 | 0.331 |

- **Paired comparison:** the code beat the reliable-link design on 90.6% of site-days and satellite-tag practice on 87.1%.
- **Code vs repetition:** by median G, repetition (0.967) was slightly ahead of the code (0.933); by mean G, the code was ahead (0.891 vs 0.850). The two are equivalent under bursty loss. As planned, the paper does not claim the code beats repetition on USGS-quality data.

**Low-cost deployments** (62 sampled site-days, mean G at 6 messages/day, independent p = 0.3):

| Design | G |
|---|---|
| Code | 0.767 |
| Repetition | 0.578 |
| Satellite-tag practice | 0.204 |
| Reliable-link design | 0.170 |
| Raw periodic | 0.008 |

On these noisier, more expensive records, the code's efficiency gives a clear margin over repetition.

**Low-cost needs:**
- InWaterSense: median 58.5 B/day (3.4% of raw), p90 204 B; 22 complete days.
- Weija (T and EC only): median 36 B/day; 49 complete days.

Both records are gap-heavy, so only a few of their days could be scored.

## Caveats to carry into the paper
- The plan tiers are illustrative (the Kinéis service pages are behind a sign-in). The message size and the one-way link rest on the KIM1 datasheet.
- Loss rates are swept, not measured; no measured Kinéis loss rate was found.
- The low-cost results rest on few complete days.
- The DO tolerance for InWaterSense uses Benson–Krause conversion from % saturation.
