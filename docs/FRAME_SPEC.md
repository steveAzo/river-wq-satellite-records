# Message frame specification, version 1 (revision Step 2; review M5, M18)

Code: `src/p3/frame.py`. Tests: `tests/test_frame.py`. Worked example: `src/p3/frame_example.py`.
Every primary result after the revision is computed on these bytes (Step 4).

## 1. What the operator provides and what the payload carries

| Item | Source | Notes |
|---|---|---|
| Source identity | Operator: device ID delivered with every message | Not in the payload. Authentication beyond the operator's device ID is out of scope. |
| Reception time | Operator: UTC reception time at the satellite | Used only to unwrap the 6-bit day field (Section 4). |
| User payload | 23 B (KIM1 datasheet "typical payload"); 19 B as sensitivity | Delivered in the operator's raw format as hex, regardless of integrity, so the frame carries its own CRC. |
| Operator codec (KIM1 Standard: integrity check, error correction, message counter) | Optional | Not used; it would use payload bits that the operator does not publish openly. The 19-B case bounds a smaller payload. |
| Sampling interval of each channel, site profile | Provisioned once per device (public protocol state) | Needed to map a slot to a clock time. |

Sources: KIM1 datasheet (KINEIS-MU-22-0032); Kinéis help centre, distribution formats (device ID, `MSG_DATE` reception time at the satellite in UTC, `RAW_DATA` user payload; `CRC_OK` only in processed formats). The Kinéis pages are behind a sign-in; the facts above come from their public index text and must be re-confirmed with Kinéis before submission.

## 2. Layout (23-B message)

| Part | Bits | Field | Range and meaning |
|---|---|---|---|
| Outer header (3 B, not coded) | 2 | version | 1 |
| | 6 | block day | days since 2000-01-01 UTC, mod 64 |
| | 7 | message index i | coded: 0..K-1 data, K..Q-1 parity; uncoded: data-unit index (copies share it) |
| | 7 | K | data units in the block, 1..127 |
| | 1 | coded | 1 = Reed-Solomon parity exists in this block |
| | 1 | fountain | parity rows: 0 = Reed-Solomon (Cauchy), 1 = random linear combinations seeded by (block day, K, index) (`fountain.py`; Step 6 baseline) |
| Unit (20 B, erasure-coded) | 16 | CRC-16 | CRC-16/CCITT-FALSE over context (version, block day mod 64, K, data index) + the 18 body bytes |
| | 2 | segments | 0..3 |
| Segment (repeated) | 6 | day offset | record day = block day - offset (0..63) |
| | 10 | first | planned position of the segment's first value (0..1023) |
| | 3 | count | values in the segment (1..7) |
| | 1 | last | the segment ends the record day's planned list |
| | 1 | bound | the day's planned set keeps every reading within tolerance (Step 3) |
| Value (repeated) | 2 | parameter | 0 T, 1 DO, 2 pH, 3 EC |
| | 9 | slot | index on the channel's native grid within the UTC day (0..511) |
| | 13 | reading | quantised code (Section 3) |
| Padding | | zeros | to the end of the unit |

Planned order: parameter (T, DO, pH, EC), then slot. A position is an index into that list, so a server
that holds positions 0..m knows exactly which planned values it lacks, without any oracle knowledge.

Parity messages carry the same outer header (index K..Q-1) and the Reed-Solomon parity (GF(2^8), Cauchy
generator, `rs.py`) of the K data units. Any K of the Q messages recover all K units.

## 3. Readings

| Parameter | Range | Scale | Step | Worst error / USGS-excellent tolerance |
|---|---|---|---|---|
| T | -5 to 76.89 degC | linear | 0.01 degC | 2.5% |
| DO | 0 to 40.945 mg/L | linear | 0.005 mg/L | 0.83% |
| pH | 0 to 16.378 | linear | 0.002 | 0.5% |
| EC | 1 to 100,000 uS/cm | log10 | 0.141% of value | 2.34% |

The linear grids are decimal: a reading reported at 0.1 or 0.01 (T, DO, pH) is carried exactly (tested).
This matters. USGS reports T and pH to 0.1 with a 0.2 tolerance, so many interpolation errors fall exactly on
the tolerance. A non-decimal grid (the first version, step 45/8189 degC) pushed such ties just over the limit and
cost approximately 0.3 extra values per channel-day for T and pH on 2023 data (`results/dev/need_modes_grid_v0.csv`).

Codes 1..8190 are readings; 0 and 8191 flag a reading below or above the range (or missing). Such a
reading is censored (Step 9): the encoder always keeps it, the server reports it as below or above range and
never certifies it, and the reconstruction passes through the range end; the readings beside it are checked
against that clipped value, so they can still be certified. Step 3 makes the error bound exact under quantisation: the encoder measures each
candidate's error against the quantised endpoint values the server will hold, so no tolerance margin is needed.

## 4. Day numbering and rollover

The node numbers UTC days from 2000-01-01 and sends the block day mod 64. The server takes the operator's
reception day R and sets the block day to the latest day d <= R + 1 with d = field (mod 64). This is
unambiguous while (a) the delay from sending to reception is below 63 days and (b) the node clock is within
one day of UTC (tested: delays 0 to 62 days; node one day ahead). Record days in a block are at most 63
days old (6-bit offset); a node discards backlog older than that and the server reports those days as lost.

Clock assumption: the node clock is set at installation and drifts by seconds per day, which is small
against slots of 3 min or more. A clock error of more than half a slot shifts slot times; this is outside the
reconstruction bound and is tested in Step 9.

## 5. Packing

`frame.pack` fills units in FIFO order of record days. Within a unit it opens a new segment when the next
record day starts, up to three segments, and only if at least one value of the new segment fits; a day is
split across units where needed. Unit capacity in values (1 / 2 / 3 segments): 5 / 4 / 3 at 23 B and
3 / 2 / 1 at 19 B.

Useful share of the payload: 5 values x 24 bit = 120 of 184 bit (65%), against 91% in the draft's
unframed format. Effect on the 2024 needs (draft selection rule, one day per block): days that fit one
message fall from 63.5% to 51.8%; messages per day p99 6 -> 8, maximum 10 -> 14. With 19 B: one-message
days 58.0% -> 34.2%.

## 6. Integrity

- The CRC detects every single-bit and every tested double-bit error in a unit (tests: all 160 single
  flips of a 20-B unit; 3,000 random double flips), and any unit read with the wrong block day,
  K, or index.
- Reed-Solomon in erasure mode cannot detect errors. A corrupted parity message produces wrong recovered
  units, which then fail their CRC (tested). With more than K arrivals the server can try other K-subsets.
- An outer-header error that changes the block or index is caught by the same CRC context.
- What the frame does not protect: a consistent but wrong reading from the sensor itself (calibration,
  fouling). The bound is relative to the sensor record (Step 9 and the Discussion).

## 7. Worked example (development data)

Site 01467200, 2023-07-14 (day 8595, sent as 19), 5-min sampling, 288 slots per channel. The self-contained
encoder (`record.Encoder`, tau = 1) planned 16 values: T@2 = 27.4, T@89 = 26.8, T@144 = 27.6, T@232 = 26.8,
T@250 = 27.2, DO@66 = 5.3, DO@85 = 5.7, DO@114 = 5.5, DO@229 = 6, DO@265 = 5.4, pH@0 = 7.1, EC@0 = 236.9,
EC@91 = 212.9, EC@122 = 230, EC@228 = 209, EC@261 = 228.1 (pH is flat within tolerance all day, so one
value carries it). K = 4 units, Q = 6 messages (138 B sent; 48 B of values).

```
msg 0 data    53 00 12 | 48 4e 40 00 2a 00 99 52 16 58 da 24 19 7a 3a 18 da 3e 99 2a
msg 1 data    53 02 12 | a0 c0 40 01 6a 90 88 4a 95 48 ea 9c 88 9a b9 49 62 c2 48 72
msg 2 data    53 04 12 | 82 7e 40 02 ab 00 1b bf 80 1e 65 96 dd cd 9e 9e 3b b9 1d b2
msg 3 data    53 06 12 | f5 56 40 03 cf c1 5e 2e 00 00 00 00 00 00 00 00 00 00 00 00
msg 4 parity  53 08 12 | 2a 36 e8 80 62 9f 0f b9 9a f0 b7 1c c2 11 3a 8c 71 57 09 a9
msg 5 parity  53 0a 12 | 5a 2d e8 a0 88 7e e4 84 6a 3e c8 53 36 cc a2 94 26 0c 81 4e
```

Header `53 00 12` = 01 010011 0000000 0000100 1 0: version 1, day 19, index 0, K 4, coded.
Unit 0 body `40 00 2a ...` = segments 1; offset 0, first 0, count 5, last 0, bound 1; then T@2 ...
Messages 0 and 2 were dropped; 1, 3, 4, and 5 decoded to units 0..3 (positions 0-4, 5-9, 10-14, 15; the last
segment has last = 1). The 16 values were recovered exactly and the day was fully certified.

## 8. Limits of version 1

Native intervals of 3 min or longer (9-bit slot); at most 1,023 planned values per record day; at most 63
days of backlog; at most 127 data units and 128 messages per block (Q <= 96 in all tiers); four parameter
codes. Alternatives considered: implicit parameter codes with per-channel counts (cheaper only for large days);
CRC-8 (one more value per 19-B message, weaker detection). Kept: the simpler self-parsing form.
