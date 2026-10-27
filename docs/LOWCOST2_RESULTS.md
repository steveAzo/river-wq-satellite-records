# Low-cost deployments under the revised method (exploratory, after the second confirmation)

The two low-cost deployments of the first round were re-analysed with the revised method. They had been opened in
that round, and the gridding step below was chosen after the freeze; the results are exploratory and indicative.

Data and preparation (`src/p3/lowcost.py`, `src/p3/lowcost_grid.py`):
- InWaterSense node 1 (Sitnica River, Kosovo; 2015): T, DO (converted to mg/L), pH, and EC every 10.2 min; readings
  averaged in 10-min bins starting at 00:00 UTC.
- Weija intake (Ghana; 2018 to 2019): T and EC every 32.5 min (its pH record is implausible and unused); 30-min bins.
  The Weija data are private; derived counts and probabilities only are reported.
Because the native interval is slightly longer than the bin, an occasional bin is empty; the loader bridges such single
gaps. Record days: InWaterSense 61 (24 with all four parameters); Weija 74 (temperature and conductance).

Results (`results/lowcost2/`; same frozen parameters and scripts as development):

| Outcome | InWaterSense (24 four-parameter days) | Weija (74 two-parameter days) |
|---|---|---|
| Median bytes of the record | 64 (five messages); value share 3.73% | 27; value share 10.4% |
| G_cert, Q = 6, independent p = 0.3: code / repetition | 0.437 / 0.291 | 0.936 / 0.837 |
| G_cert, Q = 6, bursty p = 0.3: code / repetition | 0.418 / 0.372 | 0.865 / 0.840 |
| G_cert, Q = 12, independent p = 0.3: code / repetition | 0.763 / 0.582 | 1.000 / 0.975 |
| G_cert, Q = 24, independent p = 0.3: code | 0.875 | not computed |
| Every k-th reading and tag practice, Q = 6 | 0.000 and 0.000 | not computed |

Decisions (InWaterSense, Q = 6, perfect delivery): daily minimum DO below 5 mg/L on 20 of 24 days; the record decided
the criterion on 22 days and missed (read naively) 1 of the 20 exceedance days; every k-th reading and tag practice
decided none. Conductance pulses: 13 days; missed 8 by the record, 11 by every k-th reading, and 10 by tag practice. No
seven-day window of four-parameter days existed, so the 7DADM was not evaluated.

Interpretation: the noisy low-cost record cost approximately 2.4 times the USGS median and needed 12 to 24 messages per
day for most days to be certified, consistent with the first round (InWaterSense need 3.9 times the USGS median). The
small number of days limits these results to indications.
