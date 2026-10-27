# Second confirmation: results (plan `docs/CONFIRM2_PLAN.md`, freeze `docs/FREEZE2.md`)

Frozen at commit 86f662b (tag `confirm2-freeze`); freeze record committed as 63967c0 before the data were opened.
Data: 36 new USGS sites in five regions, calendar year 2024, sealed unread before the freeze (seal verified at every
start of the run: 36 of 36 files). Run: `python -I src/p3/confirm2.py data/clean/usgs_new2024 confirm2
data/clean/usgs_new2024.md5`. Outputs: `results/confirm2/`.

Conduct of the run: the run was interrupted twice when the computing session ended (after the plans and 3 sites of
RQ1, and after 35 sites of RQ1) and was resumed with the same frozen command; completed per-site files were reused,
and no result was inspected before the run finished. The frozen files were unchanged at each resumption (git status
of `src/`, the plan, and the frozen parameters: clean).

Cohort: 12,380 record days at 36 sites, 11,133 with all four parameters (primary cohort), mostly at 15-min sampling
(10,667 days), with 342 days at 5 min and 118 at 30 min.

## 1. Verdicts

| ID | Hypothesis | Threshold | Result (95% interval) | Verdict |
|---|---|---|---|---|
| C1 | Median record of a four-parameter day at most two messages (30 B) | upper bound <= 30 B | 27 B (27 to 33) | Not supported |
| C2 | No certified reading outside tolerance and no wrong three-valued decision | exactly 0 | 96 readings on 1 day (see Section 2) | Not supported |
| C3 | Record-first code minus repetition, Q = 6, p = 0.3 | lower bound >= 0.03 | 0.101 (0.085 to 0.118) | Supported |
| C4 | Record-first code minus channel-blind fixed-K code (720 sampled days) | lower bound >= 0.05 | 0.120 (0.093 to 0.152) | Supported |
| C5 | Record-first code minus tag practice / minus every k-th reading | lower bounds >= 0.5 | 0.869 (0.841 to 0.897) / 0.881 (0.852 to 0.907) | Supported |
| C6 | Q = 12: G_cert under independent / bursty loss | lower bounds >= 0.95 | 0.987 (0.976 to 0.995) / 0.966 (0.954 to 0.976) | Supported |
| C7 | Conductance pulses missed / low-DO days decided, code minus every k-th (perfect delivery) | upper <= -0.3 / lower >= 0.3 | -0.551 (-0.617 to -0.488) / 0.806 (0.751 to 0.857) | Supported |
| C8 | A 28-day pilot (any month) chooses a sufficient tier | estimate >= 0.75 | 0.832 (0.754 to 0.904) of 398 site-pilots | Supported |

Six of eight hypotheses were supported; C1 and C2 were not.

## 2. Why C1 and C2 failed

- C1: the median record was 27 B (nine values), as in development (27 B), but the upper end of its interval was
  33 B (eleven values) because the confirmation sites varied more. The threshold, set at the upper end of the
  development interval, left no margin for between-cohort variation. The substantive claim (a typical day needs two
  messages) holds for the point estimate; the interval claim does not.
- C2: every one of the 96 falsely certified readings came from one draw of one day (site 04231600, 2024-12-28, 12
  messages per day, independent loss 0.3, bit-error rate 1e-2, record-first code). The day's record fitted one unit;
  nine messages arrived, only one of them intact, and the data message was not among them. The hardened receiver
  therefore rebuilt the unit from parity messages one by one; three attempts failed their CRC, and the fourth, built
  from a corrupted parity message, passed CRC-16 by chance and parsed into valid segments, three of whose five values
  were wrong (`src/p3/diagnose_c2.py` reproduces the event from the frozen code and seed). At that bit-error rate the
  confirmation made approximately 148,000 CRC checks on corrupted data (84,000 decoding attempts and 64,000 rejected
  data units); at 2^-16 per random pattern, approximately 2.3 accidental passes were expected. No false certificate
  occurred at bit-error rates of 1e-3 or less, with 10% of messages corrupted, without corruption, under glitches, or
  in any environmental decision (0 wrong three-valued decisions over 11,133 days and 20 draws).
  Interpretation: Proposition 1 assumes that every value used arrived as transmitted; the CRC enforces this only up
  to its residual error rate, and retrying the erasure decoding over many parity combinations multiplies the number
  of chances for a corrupted message to pass. The confirmation therefore did not support an unconditional zero; it
  supports soundness under erasures and under corruption up to a bit-error rate of 1e-3.

## 3. Other confirmation results (descriptive)

- RQ1 cost (four-parameter days): 90th percentile 54 B (48 to 63); 99th percentile 132 B (96 to 171); median value
  share 2.34% (2.08% to 2.86%); median byte share 4.33% (3.85% to 5.29%); days within one message 7.0% (3.8% to 10.7%).
- RQ2 at Q = 6 (exact, full cohort): code 0.963 / 0.900 / 0.733 at independent p = 0.1 / 0.3 / 0.5; 0.823 under
  bursts of 3 and 0.764 under bursts of 6. Code minus repetition: 0.031 / 0.101 / 0.144 (independent), 0.026 (bursts
  of 3), 0.006 (0.005 to 0.007; bursts of 6). Code minus the reliable-link design at p = 0.3: 0.788 (0.757 to 0.815).
  Site means of the code at p = 0.3 ranged from 0.627 to 0.989 (median 0.920). The 720 sampled days agreed with the
  full cohort to within 0.008.
- Season (Q = 6, p = 0.3): monthly G_cert from 0.820 (July and August) to 0.956 (February).
- RQ3: sites with G7 >= 0.9 at Q = 6: 22 of 36 (61%; 44% to 78%) under independent loss and 5 of 36 (14%; 3% to 25%)
  under bursty loss; at Q = 12: 35 of 36 under both; at Q = 24: 36 of 36. Plan sizing (C8) with a bursty planning
  channel: 0.819 (0.743 to 0.884); December pilots were the weakest (0.65 and 0.62).
- RQ4 environmental decisions (Q = 6; perfect delivery): low-DO days decided 0.966 (code) against 0.160 (every k-th)
  and 0.048 (tag practice); on the 750 low-DO event days, 0.737 decided by the code. Conductance pulses (766 events)
  missed 0.166 by the code against 0.717 (every k-th) and 0.679 (tag practice); differences -0.551 and -0.513. Naive pH exceedances (392 events)
  missed more often by the code than by every k-th reading (+0.209; 0.066 to 0.433), as in development. Low-DO
  misses, code minus every k-th: -0.007 (-0.083 to 0.045) with perfect delivery (no clear difference), -0.070
  (-0.130 to -0.027) at p = 0.3.

## 4. Post-confirmation changes (exploratory; do not alter the verdicts above)

See `docs/POSTHOC_C2.md`: a stricter acceptance rule for retried decodings, evaluated on both cohorts as an
exploratory analysis.

## 5. Temporal re-test (not confirmatory)

The same frozen command was run, from a separate checkout of the tag `confirm2-freeze` (git worktree; so that changes
made after the confirmation could not affect it), on the 2024 data of the 39 development sites (seal verified:
39 of 39). Outputs: `results/retest2024/`. Cohort: 11,168 four-parameter days at 38 sites. All eight criteria were
met: C1 median 24 B (21 to 30); C2 0; C3 0.087 (0.072 to 0.104); C4 0.108 (0.086 to 0.133); C5 0.801 / 0.867;
C6 0.990 / 0.971; C7 -0.587 / 0.626; C8 0.897. G_cert of the code at Q = 6, independent loss 0.3: 0.908 (0.872 to
0.939). These sites shaped the method in 2023, and their 2024 data were opened in the first round; the re-test shows
temporal stability, not independent confirmation.
