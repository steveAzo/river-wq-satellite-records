# Step 9 results: robustness beyond erasures (review M18)

Plan fixed before the experiments: `docs/STEP9_PLAN.md`. Code: `record.py` (censoring), `delivery.recover_units`
(hardened receiver), `src/p3/robustness.py`. Tests: `tests/test_record.py` (censoring), `tests/test_robust_receive.py`,
`tests/test_multiday.py::test_node_outages_do_not_change_any_other_days_bytes`; 238 tests pass.
Data: the 380 test days of Steps 4 to 6 (2023, four-parameter, 38 sites). Outputs: `results/dev/robust9_corrupt.csv`,
`results/dev/robust9_glitch.csv`; log `results/robust9_dev.log`.

## 1. Two weaknesses found and fixed

- Out-of-range readings: before this step, one reading outside the quantiser range (for example a sensor glitch
  reported as -1 mg/L of DO) made the whole day impossible to bound, so the day lost all certification. Such
  readings are now censored: they are always kept and carried as their flag code, they are excluded from the
  tolerance requirement, and the spans next to them are checked against the clipped value that the server holds.
  The server reports them as below or above range, which is itself certain information. On USGS data, which contain
  no out-of-range reading, the plans were unchanged (152 days compared).
- Corrupted headers: the receiver previously took K and the block day from the last header it parsed, so one
  corrupted header could spoil a whole block. The hardened receiver keeps the majority header, accepts only units
  that pass their CRC, and retries the erasure decoding over other parity messages until every recovered unit
  passes its CRC. Without corruption its output is identical to the previous receiver (all exhaustive tests pass).

## 2. Corruption of arriving messages

Independent erasure p = 0.3; corruption applied to the arriving messages, headers included; 378 days (two days whose
record exceeded six messages were excluded) and 20 draws per day.

| Q | Design | Corruption | G_cert | Certified reading share | CRC failures per day | False certificates |
|---|---|---|---|---|---|---|
| 6 | Record-first code | none | 0.926 | 0.958 | 0 | 0 |
| 6 | Record-first code | bit errors 1e-4 | 0.919 | 0.953 | 0.03 | 0 |
| 6 | Record-first code | bit errors 1e-3 | 0.843 | 0.894 | 0.24 | 0 |
| 6 | Record-first code | bit errors 1e-2 | 0.158 | 0.219 | 1.11 | 0 |
| 6 | Record-first code | 10% of messages hit | 0.878 | 0.923 | 0.09 | 0 |
| 6 | Interleaved repetition | none | 0.818 | 0.928 | 0 | 0 |
| 6 | Interleaved repetition | bit errors 1e-3 | 0.715 | 0.869 | 0.34 | 0 |
| 6 | Interleaved repetition | 10% of messages hit | 0.755 | 0.892 | 0.13 | 0 |
| 12 | Record-first code | bit errors 1e-3 | 0.984 | 0.990 | 0.25 | 0 |
| 12 | Record-first code | bit errors 1e-2 | 0.334 | 0.376 | 1.12 | 0 |

Findings:
- No certified reading was outside its tolerance under any corruption level, including a bit-error rate of 1e-2, at
  which only 16% of 23-B messages arrive intact. Corruption therefore acted as additional erasure.
- Certification degraded gracefully: a bit-error rate of 1e-4 cost 0.007 of G_cert and 1e-3 cost 0.083 at Q = 6;
  the code stayed ahead of repetition at every level.
- The residual risk is the CRC-16's undetected-error rate (2^-16 per corrupted unit for random patterns); it was
  not observed in these experiments and remains a stated limit.

## 3. Sensor glitches (perfect delivery)

| Glitch | Per day | Days still planned and fully certified | Extra values per day | Readings certified |
|---|---|---|---|---|
| Out of range (censored) | 1 | 380 of 380 | 2.36 | 0.997 |
| Out of range (censored) | 3 | 380 of 380 | 7.15 | 0.990 |
| In range (+10 tolerances) | 1 | 380 of 380 | 2.34 | 1.000 |
| In range (+10 tolerances) | 3 | 380 of 380 | 7.17 | 1.000 |

- No false certificate occurred. Each glitch cost approximately 2.35 values (the glitch and the readings beside it),
  that is, approximately one extra message for every two glitches.
- The encoder carries what the sensor reports: an in-range spike is kept faithfully because the bound is relative to
  the sensor record. Detecting and flagging sensor faults (spikes, fouling, drift, calibration) remains the task of
  quality assurance upstream of the encoder.

## 4. Outages, clock, and source identity

- Outages: with the daily record-first design, removing record days leaves every other day's transmitted bytes
  unchanged (test), so node or sensor outages do not propagate. A missing day is simply absent at the server.
- Clock: a slot is assigned to the wrong time once the node clock drifts by half an interval. A 20 ppm crystal
  drifts by 1.73 s per day, so it must be resynchronised within 87 days at 5-min sampling, 260 days at 15 min, and
  521 days at 30 min; a 2 ppm temperature-compensated clock lasts approximately 2.4 years at 5 min. The day-number
  rule tolerates a node clock one day off and reception delays below 63 days (tested in Step 2). The KIM1 module has
  no satellite time source, so resynchronisation at maintenance visits, or a module with one, is assumed.
- Source identity: the operator's device identifier is not cryptographic. Replacing the CRC-16 by a 24- or 32-bit
  truncated message authentication code (which also detects errors) leaves 113 or 105 bits for one segment, so a
  unit carries 4 values instead of 5: authentication would cost 20% of the capacity. It was not implemented.

## 5. Claims after this step

- Certificates are sound under erasures and under random corruption caught by the CRC; the residual undetected-error
  rate of the CRC is stated.
- Out-of-range readings are carried as censored flags; the bound covers all other readings.
- The bound is relative to the sensor record; sensor faults inside the range are outside it.
- Clock synchronisation and source authentication are stated assumptions with quantified requirements and costs.
