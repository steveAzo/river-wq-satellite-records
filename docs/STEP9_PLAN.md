# Step 9 analysis plan: robustness beyond erasures (review M18)

Written 2026-10-25 BEFORE the Step 9 experiments were run. Development data (USGS 2023) only.

## Changes made before the experiments (with tests)

- Censoring (`record.tables`, `record.certify`, `record.errors`): a reading outside the quantiser range is always
  kept, carried as its flag code, excluded from the tolerance requirement, and reported by the server as
  censored; spans next to it are checked against the clipped value the server holds. Previously one such reading
  made the whole day impossible to bound. On USGS data (no reading outside the ranges) the plans are unchanged
  (152 days compared, 0 differences).
- Hardened receiver (`delivery.recover_units`): majority header per block, CRC-verified data units, and decoding
  retried over parity combinations until every recovered unit passes its CRC; only verified units are used.
  Without corruption the outputs are unchanged (all exhaustive byte-level tests pass).

## Experiments

Sample: the 380 test days of Steps 4 to 6 (four-parameter, 38 sites). Designs: record-first code and record-first
interleaved repetition at Q = 6 and 12. Erasures: independent p = 0.3. 20 draws.

1. Corruption of arriving messages (headers included):
   - none (reference);
   - independent bit errors at rates 1e-4, 1e-3, and 1e-2;
   - 10% of arriving messages hit by 1 to 8 random bit flips.
   Outcomes: certified readings outside tolerance (false certificates; expected 0 up to the CRC's residual rate),
   G_cert and certified reading share relative to no corruption, CRC failures, header rejections, decode retries.
2. Sensor glitches injected into the record (perfect delivery):
   - out of range: 1 or 3 readings per day replaced by out-of-range values (T 90 degC, DO -1 mg/L, pH 17,
     EC 200,000 uS/cm), channel and time chosen at random;
   - in range: 1 or 3 readings per day raised by 10 tolerances.
   Outcomes: whether the day can still be planned and certified, extra values against the clean day, false
   certificates (expected 0), and the share of readings certified.
3. Node outage: a test that removing record days leaves the bytes of every other day's block unchanged (daily
   design), so outages do not propagate.

## Analyses without simulation (stated in the results)

- Clock: drift needed to move a slot by half an interval, for typical real-time clocks (20 ppm crystal, 2 ppm
  temperature-compensated), and the resulting resynchronisation interval; the rollover rule tolerates a node clock
  one day off (tested in Step 2).
- Source authentication: the operator's device identifier is not cryptographic; the capacity cost of replacing the
  CRC-16 by a 32-bit truncated message authentication code is computed from the frame layout.
- Sensor faults inside the range (fouling, drift, calibration): outside the reconstruction bound; the record
  faithfully carries what the sensor reports, so quality assurance remains upstream.
