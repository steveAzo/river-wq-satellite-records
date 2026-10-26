"""Worked encode/decode example for docs/FRAME_SPEC.md (development data, 2023).

Takes one 2023 site-day, plans the self-contained record at tau = 1 (record.Encoder), packs it into
data units, adds Reed-Solomon parity up to Q = 6 messages, prints every message in hex, drops Q - K
messages (the most the code can lose), decodes, parses, and certifies.
Run from Paper3/: python -I src/p3/frame_example.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame, record, rs  # noqa: E402
from p3.data import load_site  # noqa: E402

SITE, DAY, Q = "01467200", "2023-07-14", 6
EPOCH = pd.Timestamp("2000-01-01")


def main():
    sd = next(d for d in load_site(f"data/clean/usgs/{SITE}.csv") if str(d.day.date()) == DAY)
    vals = record.Encoder(record.channels_from_siteday(sd)).plan_at(1.0)
    day = (sd.day.tz_localize(None) - EPOCH).days
    units_segs = frame.pack([[0, vals, True, 0]], Q)
    K = len(units_segs)
    units = [frame.encode_unit(s, frame.Header(day, i, K), i) for i, s in enumerate(units_segs)]
    coded = rs.encode([list(u) for u in units], Q)
    msgs = [frame.message(frame.Header(day, i, K), c) for i, c in enumerate(coded)]

    print(f"site {SITE}, {DAY} (day number {day}, sent as {day % 64}); {sd.step_min}-min, {sd.n} slots/channel")
    print(f"planned values ({len(vals)}): " + ", ".join(f"{p}@{s}={frame.dequantise(p, c):.4g}" for p, s, c in vals))
    print(f"K = {K} data units, Q = {Q} messages, {23 * Q} B sent; useful payload {3 * len(vals)} B "
          f"({24 * len(vals) / (8 * 23 * Q):.0%} of the bytes sent)")
    for i, m in enumerate(msgs):
        kind = "data  " if i < K else "parity"
        print(f"  msg {i} {kind} {m[:3].hex(' ')} | {m[3:].hex(' ')}")

    lost = [0, 2, 5][:Q - K]
    print(f"lost: messages {lost}")
    rx = {}
    for i, m in enumerate(msgs):
        if i not in lost:
            h = frame.parse_header(m, day)   # reception on the same day
            rx[h.index] = list(m[3:])
    data = rs.decode(rx, K, Q)
    got = []
    for i, u in enumerate(data):
        segs = frame.decode_unit(bytes(u), frame.Header(day, i, K), i)
        assert segs is not None
        for s in segs:
            print(f"  unit {i}: day offset {s.day_offset}, positions {s.first}..{s.first + len(s.values) - 1}, "
                  f"last {s.last}, bound {s.bound}")
            got += s.values
    assert got == vals
    print("decoded values identical to the planned values")
    rx = dict(enumerate(got))
    cert, full = record.certify(rx, {p: sd.n for p in sd.params}, True, len(got) - 1)
    print(f"fully certified: {full}")


if __name__ == "__main__":
    main()
