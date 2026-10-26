# Second confirmation: plan for the revised method (DRAFT for approval by the authors)

Status: DRAFT, written 2026-10-25. Nothing in this plan is frozen until the authors approve it and the freeze record
(`docs/FREEZE2.md`: commit, tag, and checksums) is written. No reading of the new cohort is opened before then.

## 1. Why a second confirmation

The first round (frozen 2026-10-23; `docs/FREEZE.md`, `docs/CONFIRM_RESULTS.md`) tested the draft method on USGS 2024
data of the 39 development sites. The pre-submission review led to a revised method: byte-level frame, self-contained
days, quantisation-exact encoder, record-first code, hardened receiver, and censoring. The 2024 data of the 39 sites
were opened in the first round, so they can only serve as a temporal re-test. The first round is kept, unedited, as a
documented first round.

## 2. New cohort (selected from metadata only)

Rules:
1. USGS stream sites (site type ST) with instantaneous-value series of water temperature (00010), specific
   conductance (00095), dissolved oxygen in mg/L (00300), and pH (00400), each covering 2024-01-01 to 2024-12-31
   in the USGS series catalogue.
2. Not among the 39 sites used in Papers 1 to 3.
3. Approval: at least 250 approved ("A") daily means in 2024 for each of the four parameters. Only the qualifier
   counts are used; the daily values are discarded unread.
4. Regions not represented among the 39 sites:
   - Southeast: GA, FL, AL, SC, NC;
   - Mountain West: CO, UT, MT, ID, WY;
   - Great Plains and upper Midwest: MN, WI, KS, NE, MO, SD, ND;
   - Southwest and Texas: AZ, NM, TX, NV;
   - New England and New York: MA, NY, VT, NH, ME, CT, RI.
5. Up to 8 sites per region: the sites passing rules 1, 2, and 4 are sorted by site number, shuffled with seed
   20261025, and checked against rule 3 in that order; the first 8 that pass are selected (a seeded random sample of
   the eligible sites); at most 40 sites. Script: `src/data/select_new_cohort.py`; record of every candidate and
   check: `results/confirm2/selection.csv`.
6. Download of calendar year 2024 with the unchanged Paper 2 tools (`fetch_usgs.py`, `clean_usgs.py`: approved values
   only, one method per parameter); checksums (MD5) of every raw and clean file recorded immediately in
   `data/clean/usgs_new2024.md5`; no file is read for analysis until the freeze.

Outcome of the selection and download (2026-10-25 and 26; before any approval or freeze; no reading opened):
- 36 sites: 8 each in the Southeast (from 74 eligible), Mountain West (37), Great Plains and upper Midwest (38), and
  Southwest and Texas (31); 4 in New England and New York, where only 4 of the 15 catalogue-eligible sites met the
  approval rule (`results/confirm2/selection.csv`).
- 2024 downloaded with the unchanged Paper 2 tools (identical MD5), cleaned into `data/clean/usgs_new2024/`, and
  sealed: `data/raw/usgs_new2024.md5` and `data/clean/usgs_new2024.md5` (36 files each). A first download attempt
  was interrupted by a network failure after 4 sites; the partial clean files and seals were deleted unread and the
  download was completed and sealed once.
- The confirmation runner (`src/p3/confirm2.py`) was tested end-to-end on four 2023 development sites
  (`results/confirm2/pipeline_dryrun_dev_subset.log`); the test exposed and fixed a bootstrap edge case (resamples
  with no event day), which left the development statistics unchanged.

## 3. Method under test (frozen at the freeze commit)

`loader.py` (per-channel UTC days), `record.py` and `stream.py` (self-contained, quantisation-exact record at the
USGS "excellent" tolerances, censoring), `frame.py` (frame v1), `delivery.py` (record-first code, baselines, hardened
receiver), `analytic.py`, `env.py`, and the analysis scripts `need2.py`, `cohort_exact.py`, `run_robust.py`,
`robust_bytes.py`, `run_env.py`, `robustness.py`, and `stats.py`, all unchanged. Channel-blind parameters of the
baselines come from the 2023 development files (`results/dev/robust_choice.json`). Primary cohort: four-parameter
record days. Intervals: site-clustered 95% bootstrap (Step 11).

## 4. Hypotheses (proposed; thresholds set from the 2023 development results with margins)

Each hypothesis passes when its 95% interval lies entirely on the stated side of the threshold. Q = messages per day;
independent loss p = 0.3 unless stated.

| ID | Family | Hypothesis | Development value (2023) | Threshold |
|---|---|---|---|---|
| C1 | Cost (RQ1) | Median record size of a four-parameter day is at most two messages (10 values, 30 B) | 27 B (21 to 30) | upper bound <= 30 B |
| C2 | Soundness | No certified reading outside its tolerance and no wrong three-valued decision, on bytes, with and without loss and corruption | 0 | exactly 0 (deterministic) |
| C3 | Design (RQ3) | Record-first code minus record-first repetition, Q = 6 | 0.092 (0.075 to 0.109) | lower bound >= 0.03 |
| C4 | Design (RQ3) | Record-first code minus channel-blind fixed-K code, Q = 6 (sampled days) | 0.130 (0.096 to 0.166) | lower bound >= 0.05 |
| C5 | Design (RQ3) | Record-first code minus tag practice and minus every k-th reading, Q = 6 | 0.809 and 0.867 | lower bounds >= 0.5 |
| C6 | Sufficiency (RQ2) | At Q = 12, mean G_cert >= 0.95 under independent and under bursty (mean burst 3) loss | 0.991 and 0.971 | lower bounds >= 0.95 |
| C7 | Environment | Conductance pulses missed, code minus every k-th, Q = 6, perfect delivery; and low-DO days decided, code minus every k-th | -0.722 and +0.656 | upper bound <= -0.3; lower bound >= 0.3 |
| C8 | Sizing (RQ4) | A 28-day pilot (any month) chooses a sufficient tier for at least 75% of site-pilots | 87.6% (77.2% to 96.6%) | point estimate >= 0.75 (interval reported) |

Reported without a hypothesis: code minus repetition under bursty loss and bursts of 6; sites with G7 >= 0.9 per
tier; seasonal results; naive pH decisions; corruption and glitch costs; resource figures; the temporal re-test on the
39 sites in 2024 (Section 6). C2 holds by construction (Propositions 1 and 2) and is a test of the implementation.

Multiplicity: eight hypothesis families with their tests (C5 and C7 have two parts each, both of which must pass).
They are reported jointly; no adjustment is applied because each threshold is a substantive margin, not a test of a
null effect. Exploratory analyses are labelled as such.

## 5. Procedure

1. Authors approve this plan (possibly with changed thresholds).
2. Authors commit and tag the repository (`confirm2-freeze`); `docs/FREEZE2.md` records the commit, the tag, and MD5
   checksums of the method files, this plan, and the sealed data.
3. The seal is verified, and the scripts are run once on the new cohort; outputs go to `results/confirm2/`.
4. `docs/CONFIRM2_RESULTS.md` reports every hypothesis with its interval and verdict, whatever the outcome.

## 6. Temporal re-test (not confirmatory)

The same scripts are run on the 2024 data of the 39 development sites and reported as a temporal re-test, opened
during the first round (2026-10-23).
