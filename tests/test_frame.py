"""Tests of the byte-level frame (src/p3/frame.py; docs/FRAME_SPEC.md). Run from Paper3/: python -m pytest tests -q"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import frame, rs  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.frame import Header, Segment  # noqa: E402


def full_unit(h, data_index, payload=23):
    vals = [("T", 10, 1234), ("T", 200, 4321), ("DO", 287, 8190), ("pH", 0, 1), ("EC", 511, 5000)]
    segs = [Segment(1, 0, vals[:frame.unit_capacity(payload)], False, True)]
    return frame.encode_unit(segs, h, data_index, payload), segs


# ---- quantiser ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("param,lo,hi", [("T", -5, 76.89), ("DO", 0, 40.94), ("pH", 0, 16.37), ("EC", 1, 1e5)])
def test_quantiser_error_is_small_against_usgs_excellent_tolerance(param, lo, hi):
    x = np.geomspace(lo, hi, 200001) if param == "EC" else np.linspace(lo, hi, 200001)
    err = np.abs(frame.roundtrip(param, x) - x) / tolerance(param, x)
    assert err.max() < {"T": 0.0251, "DO": 0.0084, "pH": 0.0051, "EC": 0.024}[param]


@pytest.mark.parametrize("param,res,lo,hi", [("T", 0.1, -5, 40), ("T", 0.01, -5, 40), ("DO", 0.1, 0, 25),
                                             ("DO", 0.01, 0, 25), ("pH", 0.1, 0, 14), ("pH", 0.01, 0, 14)])
def test_decimal_readings_are_carried_exactly(param, res, lo, hi):
    x = np.round(np.arange(lo, hi, res), 6)
    assert np.abs(frame.roundtrip(param, x) - x).max() < 1e-9


def test_out_of_range_readings_are_flagged_not_wrapped():
    codes = frame.quantise("T", np.array([-40.0, -5.0, 76.89, 90.0, np.nan]))
    assert codes.tolist()[0] == 0 and codes.tolist()[3] == frame.CODE_MAX and codes.tolist()[4] == 0
    assert frame.saturated(codes).tolist() == [True, False, False, True, True]
    assert frame.quantise("EC", np.array([0.0]))[0] == 0  # log of zero: below range


# ---- capacity ----------------------------------------------------------------------------------------
def test_capacity():
    assert frame.unit_capacity(23, 1) == 5 and frame.unit_capacity(23, 2) == 4
    assert frame.unit_capacity(19, 1) == 3


def test_unit_overflow_raises():
    h = Header(9000, 0, 1)
    vals = [("T", s, 100) for s in range(6)]
    with pytest.raises(ValueError):
        frame.encode_unit([Segment(0, 0, vals, True, True)], h, 0)


# ---- header and rollover -----------------------------------------------------------------------------
@pytest.mark.parametrize("delay", [0, 1, 30, 62])
def test_block_day_unwraps_from_reception_day(delay):
    for day in (9000, 9063, 9064, 9127):
        h = Header(day, 17, 40, True)
        got = frame.parse_header(h.to_bytes(), day + delay)
        assert (got.block_day, got.index, got.K, got.coded) == (day, 17, 40, True)


def test_node_clock_one_day_ahead_still_unwraps():
    h = Header(9000, 0, 3)
    assert frame.parse_header(h.to_bytes(), 8999).block_day == 9000


# ---- unit round trip and integrity -------------------------------------------------------------------
def test_unit_round_trip():
    h = Header(9000, 2, 4)
    unit, segs = full_unit(h, 2)
    assert len(unit) == 20
    assert frame.decode_unit(unit, h, 2) == segs


def test_two_segments_round_trip():
    h = Header(9000, 0, 1)
    segs = [Segment(3, 14, [("pH", 5, 77), ("EC", 9, 6000)], True, True),
            Segment(2, 0, [("T", 0, 3000), ("T", 95, 3100)], False, False)]
    assert frame.decode_unit(frame.encode_unit(segs, h, 0), h, 0) == segs


def test_crc_catches_every_single_and_double_bit_flip():
    h = Header(9000, 1, 3)
    unit, _ = full_unit(h, 1)
    bits = 8 * len(unit)
    for i in range(bits):
        u = bytearray(unit)
        u[i // 8] ^= 0x80 >> (i % 8)
        assert frame.decode_unit(bytes(u), h, 1) is None
    rng = np.random.default_rng(1)
    for _ in range(3000):
        i, j = rng.choice(bits, 2, replace=False)
        u = bytearray(unit)
        u[i // 8] ^= 0x80 >> (i % 8)
        u[j // 8] ^= 0x80 >> (j % 8)
        assert frame.decode_unit(bytes(u), h, 1) is None


def test_crc_rejects_wrong_context():
    h = Header(9000, 1, 3)
    unit, _ = full_unit(h, 1)
    assert frame.decode_unit(unit, Header(9001, 1, 3), 1) is None   # other block day
    assert frame.decode_unit(unit, Header(9000, 1, 4), 1) is None   # other K
    assert frame.decode_unit(unit, h, 2) is None                    # other data index


# ---- packing -----------------------------------------------------------------------------------------
def test_pack_is_fifo_splits_days_and_keeps_positions():
    a = [("T", s, 100 + s) for s in range(8)]
    b = [("DO", s, 200 + s) for s in range(3)]
    queue = [[2, a, True, 0], [1, b, False, 0]]
    units = frame.pack(queue, 5)
    assert [len(u) for u in units] == [1, 2, 1]                     # 5 | 3 + 1 (two segments: 4) | 2
    flat = [(s.day_offset, s.first + k, v) for u in units for s in u for k, v in enumerate(s.values)]
    assert flat == [(2, i, v) for i, v in enumerate(a)] + [(1, i, v) for i, v in enumerate(b)]
    assert [s.last for u in units for s in u] == [False, True, False, True]
    assert queue[0][3] == 8 and queue[1][3] == 3
    h = frame.Header(9000, 0, len(units))
    for i, segs in enumerate(units):
        assert frame.decode_unit(frame.encode_unit(segs, h, i), h, i) == segs


def test_pack_respects_unit_limit():
    queue = [[0, [("T", s, 1) for s in range(12)], True, 0]]
    assert len(frame.pack(queue, 2)) == 2 and queue[0][3] == 10


# ---- with the erasure code ---------------------------------------------------------------------------
def test_units_survive_reed_solomon_erasures():
    K, Q, day = 3, 6, 9000
    units = [full_unit(Header(day, i, K), i)[0] for i in range(K)]
    coded = rs.encode([list(u) for u in units], Q)
    got = rs.decode({3: coded[3], 4: coded[4], 1: coded[1]}, K, Q)
    for i in range(K):
        assert frame.decode_unit(bytes(got[i]), Header(day, i, K), i) is not None


def test_corrupted_parity_is_detected_after_decoding():
    K, Q, day = 3, 6, 9000
    units = [full_unit(Header(day, i, K), i)[0] for i in range(K)]
    coded = rs.encode([list(u) for u in units], Q)
    bad = list(coded[4])
    bad[7] ^= 0x10
    got = rs.decode({3: coded[3], 4: bad, 5: coded[5]}, K, Q)
    assert any(frame.decode_unit(bytes(got[i]), Header(day, i, K), i) is None for i in range(K))
