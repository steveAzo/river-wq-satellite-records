"""Byte-level message frame (revision Step 2; review M4, M5, M18). Specification: docs/FRAME_SPEC.md.

A message is the operator's user payload (23 B on KIM1; 19 B as sensitivity). The operator delivers each
message with the device identifier and the satellite reception time (UTC); neither is in the payload.

  outer header, 3 B, not erasure-coded:
    version 2 | block day mod 64 6 | message index 7 | K 7 | coded 1 | fountain 1
  unit, PAYLOAD - 3 B, erasure-coded (parity messages carry Reed-Solomon parity of the K data units):
    CRC-16 16 | segments 2 | segment* | zero padding
    segment: day offset 6 | first planned position 10 | count 3 | last 1 | bound 1 | value*count
    value:   parameter 2 | slot 9 | reading code 13

The CRC (CRC-16/CCITT-FALSE) covers the unit's content AND its context (version, block day, K, data
index), so a unit recovered from a corrupted or misassociated parity message fails the check.
Every unit parses on its own: an uncoded or systematic message that arrives alone is usable.
"""
from dataclasses import dataclass

import numpy as np

VERSION = 1
HEADER_BYTES = 3
DAY_MOD = 64
VALUE_BITS = 24
SEG_HEADER_BITS = 21
UNIT_FIXED_BITS = 16 + 2
PARAM_CODE = {"T": 0, "DO": 1, "pH": 2, "EC": 3}
PARAM_NAME = {v: k for k, v in PARAM_CODE.items()}
MAX_SLOT = 511          # 9 bits: native intervals of 3 min or longer
MAX_POS = 1023          # 10 bits: planned values per record day
CODE_MAX = 8191         # 13 bits; codes 0 and 8191 flag a reading below or above the range

# quantiser grids (lowest value, step, log10 scale). The linear grids are decimal, so readings reported at
# 0.01 degC, 0.005 mg/L, or 0.002 pH (and any coarser decimal resolution) are carried exactly.
GRIDS = {"T": (-5.0, 0.01, False), "DO": (0.0, 0.005, False), "pH": (0.0, 0.002, False),
         "EC": (0.0, 5.0 / (CODE_MAX - 2), True)}   # EC: 1 to 100,000 uS/cm on a log grid


def _grid(param):
    lo, step, log = GRIDS[param]
    return lo, step, lo + step * (CODE_MAX - 2), log


def quantise(param, x):
    """Reading -> code in 1..8190; 0 / 8191 if below / above the range (saturated, flagged)."""
    lo, step, hi, log = _grid(param)
    x = np.asarray(x, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.log10(x) if log else x
    bad = np.isnan(v) | (v < lo - step / 2)
    code = 1 + np.rint((np.where(bad, lo, v) - lo) / step).astype(np.int64)
    code = np.where(bad, 0, code)
    return np.where(v > hi + step / 2, CODE_MAX, np.clip(code, 0, CODE_MAX))


def dequantise(param, code):
    """Code -> reading; saturated codes map to the range ends (the caller treats them as censored)."""
    lo, step, _, log = _grid(param)
    v = lo + (np.clip(np.asarray(code, float), 1, CODE_MAX - 1) - 1) * step
    return 10 ** v if log else v


def roundtrip(param, x):
    return dequantise(param, quantise(param, x))


def saturated(code):
    code = np.asarray(code)
    return (code == 0) | (code == CODE_MAX)


# ---------------------------------------------------------------- bits and CRC
class BitWriter:
    def __init__(self):
        self.bits = []

    def put(self, value, n):
        if not 0 <= value < (1 << n):
            raise ValueError(f"{value} does not fit in {n} bits")
        self.bits += [(value >> (n - 1 - i)) & 1 for i in range(n)]

    def to_bytes(self, nbytes):
        if len(self.bits) > 8 * nbytes:
            raise ValueError("unit overflow")
        b = self.bits + [0] * (8 * nbytes - len(self.bits))
        return bytes(int("".join(map(str, b[i:i + 8])), 2) for i in range(0, len(b), 8))


class BitReader:
    def __init__(self, data):
        self.bits = [(byte >> (7 - i)) & 1 for byte in data for i in range(8)]
        self.pos = 0

    def get(self, n):
        if self.pos + n > len(self.bits):
            raise ValueError("read past end")
        v = 0
        for b in self.bits[self.pos:self.pos + n]:
            v = (v << 1) | b
        self.pos += n
        return v


def crc16(data, crc=0xFFFF):
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no final xor."""
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return crc


# ---------------------------------------------------------------- outer header
@dataclass(frozen=True)
class Header:
    block_day: int     # absolute day number of the block (days since 2000-01-01 UTC); sent mod 64
    index: int         # 0..K-1 data, K..Q-1 parity (coded); data-unit index (uncoded copies)
    K: int             # data units in the block
    coded: bool = True
    version: int = VERSION
    fountain: bool = False   # parity rows: 0 Reed-Solomon (Cauchy), 1 random linear (fountain.py)

    def to_bytes(self):
        w = BitWriter()
        w.put(self.version, 2)
        w.put(self.block_day % DAY_MOD, 6)
        w.put(self.index, 7)
        w.put(self.K, 7)
        w.put(int(self.coded), 1)
        w.put(int(self.fountain), 1)
        return w.to_bytes(HEADER_BYTES)


def parse_header(data, rx_day):
    """Outer header + operator reception day (days since 2000-01-01 UTC) -> Header.
    Rollover: the block day is the latest day <= rx_day + 1 congruent to the 6-bit field; valid while the
    delay from sending to reception is below 63 days and the node clock is within one day of UTC."""
    r = BitReader(data[:HEADER_BYTES])
    version, low, index, K, coded, fountain = r.get(2), r.get(6), r.get(7), r.get(7), r.get(1), r.get(1)
    top = rx_day + 1
    return Header(top - ((top - low) % DAY_MOD), index, K, bool(coded), version, bool(fountain))


# ---------------------------------------------------------------- unit (erasure-coded part)
@dataclass
class Segment:
    day_offset: int    # record day = block day - day_offset
    first: int         # planned position of the first value (planned order: parameter, then slot)
    values: list       # [(param name, slot, code)]
    last: bool         # the segment holds the record day's final planned value
    bound: bool        # the day's planned set keeps every reading within tolerance


def unit_capacity(payload=23, segments=1):
    """Values that fit in one unit with the given number of segments."""
    return (8 * (payload - HEADER_BYTES) - UNIT_FIXED_BITS - SEG_HEADER_BITS * segments) // VALUE_BITS


def _context(h, data_index):
    return bytes([h.version, h.block_day % DAY_MOD, h.K, data_index])


def _body(segments):
    w = BitWriter()
    w.put(len(segments), 2)
    for s in segments:
        w.put(s.day_offset, 6)
        w.put(s.first, 10)
        w.put(len(s.values), 3)
        w.put(int(s.last), 1)
        w.put(int(s.bound), 1)
        for p, slot, code in s.values:
            w.put(PARAM_CODE[p], 2)
            w.put(slot, 9)
            w.put(int(code), 13)
    return w.bits


def encode_unit(segments, h, data_index, payload=23):
    """Segments -> unit bytes (payload - 3). CRC over context + body bytes (body zero-padded)."""
    n = payload - HEADER_BYTES
    if len(segments) > 3:
        raise ValueError("at most 3 segments")
    body = _body(segments)
    if 16 + len(body) > 8 * n:
        raise ValueError("unit overflow")
    w = BitWriter()
    w.bits = body
    body_bytes = w.to_bytes(n - 2)
    crc = crc16(_context(h, data_index) + body_bytes)
    return bytes([crc >> 8, crc & 0xFF]) + body_bytes


def decode_unit(unit, h, data_index):
    """Unit bytes -> list of Segment, or None if the CRC fails (corrupted or misassociated)."""
    crc = (unit[0] << 8) | unit[1]
    if crc16(_context(h, data_index) + bytes(unit[2:])) != crc:
        return None
    r = BitReader(unit[2:])
    out = []
    try:
        for _ in range(r.get(2)):
            off, first, cnt, last, bound = r.get(6), r.get(10), r.get(3), r.get(1), r.get(1)
            vals = [(PARAM_NAME[r.get(2)], r.get(9), r.get(13)) for _ in range(cnt)]
            out.append(Segment(off, first, vals, bool(last), bool(bound)))
    except ValueError:
        return None
    return out


def message(h, unit):
    return h.to_bytes() + bytes(unit)


def pack(queue, n_units, payload=23):
    """Fill up to n_units units, oldest record day first (FIFO), splitting a day across units.

    queue: list of [day_offset, values, bound, next] where values is the day's planned list
    [(param, slot, code)] in planned order and next is the position of its first unsent value
    (updated in place). A new segment opens only when at least one value of it fits.
    Returns a list of segment lists, one per unit (empty units are dropped)."""
    budget = 8 * (payload - HEADER_BYTES) - UNIT_FIXED_BITS
    units = []
    for _ in range(n_units):
        segs, used = [], 0
        for item in queue:
            off, vals, bound, nxt = item
            if nxt >= len(vals) or len(segs) == 3:
                continue
            fit = min(7, (budget - used - SEG_HEADER_BITS) // VALUE_BITS, len(vals) - nxt)
            if fit < 1:
                break
            segs.append(Segment(off, nxt, list(vals[nxt:nxt + fit]), nxt + fit == len(vals), bound))
            used += SEG_HEADER_BITS + VALUE_BITS * fit
            item[3] = nxt + fit
        if not segs:
            break
        units.append(segs)
    return units
