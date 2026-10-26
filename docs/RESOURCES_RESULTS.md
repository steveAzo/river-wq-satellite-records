# Step 10 results: complexity, resources, and energy (review M12, E8)

Code: `src/p3/stream.py` (table-free exact encoder), `src/p3/bench.py`. Tests: `tests/test_stream.py` (230 cases:
same plan as the table encoder, including censored readings, other levels, and readings exactly at the tolerance).
Outputs: `results/dev/bench_equiv.csv`, `bench_resources.csv`, `bench_rs.csv`; log `results/bench_dev.log`.
All times were measured on this PC (Python 3.13, single process); microcontroller figures are estimates from
operation counts and are labelled as such. No microcontroller was available.

## 1. Complexity of the draft's implementation

The table encoder (`record.tables`) builds the full n x n table of span errors, with one vector operation per pair
of start and interior reading: O(n^3) arithmetic and O(n^2) memory. The draft cited a linear-time algorithm
(Imai and Iri, 1988) for the same result; that equivalence was never shown for this objective (per-reading
tolerances, dequantised endpoints, first value held back to midnight, last value held, censored readings) and the
claim is withdrawn.

## 2. Table-free exact encoder

For a fixed start a, the span to b keeps every reading between them within tolerance exactly when the slope from a
to b lies in the intersection of the slope windows imposed by those readings. The intersection only shrinks as b
grows, so each step updates it in constant time and the scan stops when it empties or reaches a censored reading.
Head and tail feasibility are prefix and suffix interval tests. Time: O(n^2) in the worst case; memory: O(n).

Equivalence: on all 12,674 record days of 2023 (39 sites), the table-free encoder produced exactly the plan of the
table encoder on every day (100%). The window updates per channel-day were close to the worst case n^2 / 2
(at n = 288: median 25,399, maximum 41,041 against 41,472), because smooth river records rarely empty the window.

## 3. Measured host resources (four-parameter days, 20 per interval; medians)

| Interval | n per channel | Table encoder: time, peak memory | Table-free: time, peak memory | Window updates per day: median (max) |
|---|---|---|---|---|
| 60 min | 24 | 0.08 s, 68 kB | 0.03 s, 6 kB | 802 (957) |
| 30 min | 48 | 0.32 s, 233 kB | 0.15 s, 9 kB | 3,977 (4,324) |
| 15 min | 96 | 1.31 s, 907 kB | 0.54 s, 16 kB | 14,416 (17,593) |
| 10 min | 144 | 2.89 s, 2.0 MB | 1.18 s, 22 kB | 33,456 (39,247) |
| 5 min | 288 | 11.9 s, 7.9 MB | 4.87 s, 42 kB | 134,167 (161,698) |

The 10-min days were made by taking every second reading of 5-min days (no 10-min site exists in the data).
Python times are dominated by interpreter overhead; the operation counts are the portable measure.

Reed-Solomon parity (`bench_rs.csv`): (Q - K) x K x 20 table look-up multiplications in GF(2^8) per block, for
example 160 at Q = 6 and K = 2, 880 at Q = 24 and K = 2, and 3,760 at Q = 96 and K = 2 (host: 0.04 to 0.7 ms).

## 4. Microcontroller estimates (not measured)

- Memory: the table-free encoder needs approximately 12 arrays of n numbers per channel (readings, tolerances,
  dequantised values, two window bounds, four prefix and suffix bounds, counts, predecessors, flags): at n = 288
  approximately 14 kB in single precision, against 330 kB for one n x n table in single precision. The table
  encoder does not fit typical low-power microcontrollers (64 to 256 kB of RAM); the table-free encoder does.
- Time: at a conservative 200 cycles per window update (two divisions and four comparisons in software double
  precision) and 48 MHz, the median 5-min four-parameter day (134,167 updates) needs approximately 0.56 s and the
  15-min day (14,416 updates) approximately 0.06 s.
- Arithmetic: readings exactly at the tolerance are common (decimal readings against decimal tolerances), so a node
  implementation should use the same comparisons as the reference or exact integer arithmetic (readings and codes
  scaled to integers; slope comparisons by cross-multiplication), and be checked against the reference plans
  (`bench_equiv.csv` provides 12,674 test days).

## 5. Energy per daily report

- Transmission (KIM1 datasheet: 500 mA at 5 V, less than 1 s per message): at most 2.5 J per message, so at most
  15 J per day at Q = 6 and 30 J at Q = 12.
- Encoding (estimate): 0.56 s at approximately 30 mW for the 5-min day is approximately 0.017 J, approximately 0.1%
  of the transmission energy at Q = 6; Reed-Solomon parity is negligible.
- The daily energy is therefore set by the message quota, which the record-first design spends in full whatever
  the day's record size; a node could send fewer messages on quiet days to save energy, at the cost of protection.

## 6. Consequences for the paper

- State the implemented complexity: O(n^2) time and O(n) memory for the table-free exact encoder, O(n^3) and
  O(n^2) for the table version; withdraw the linear-time statement.
- Report host measurements as such and microcontroller figures as estimates; hardware validation is future work.
