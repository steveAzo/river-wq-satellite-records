"""Frame v2 codec tests (src/p3/frame2.py; docs/FRAME_SPEC_V2.md)."""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import capacity as cp  # noqa: E402
from p3 import frame2 as f2  # noqa: E402
from p3 import record  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402


def day_values(seed, n=24):
    rng = np.random.default_rng(seed)
    chans = []
    for p, base, sc in (("T", 15.0, 0.25), ("DO", 8.0, 0.4), ("pH", 7.5, 0.25)):
        x = np.round(base + np.cumsum(rng.normal(0, sc, n)), 2)
        chans.append(Channel(p, x, tolerance(p, x)))
    plan = record.Encoder(chans).plan_at(1.0)
    return plan


WIT = {"DOmin": 1700, "pHmin": 3300, "pHmax": 3900, "Tmax": 2100, "ECa": 4000, "ECb": 4100}


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("Q", [6, 12])
def test_round_trip_record_only(seed, Q):
    vals = day_values(seed)
    blk = f2.build_block(vals, True, 9000 + seed, Q)
    assert all(len(m) == 23 for m in blk.messages)
    d = f2.receive(blk.messages)
    assert [d.values[i] for i in range(len(vals))] == vals and d.bound and d.last_pos == len(vals) - 1
    assert d.crc_failed == 0 and not d.record_rejected


@pytest.mark.parametrize("seed", range(4))
def test_any_k_of_q_messages_recover_the_record(seed):
    vals = day_values(seed)
    blk = f2.build_block(vals, True, 100, 6)
    K = blk.K
    for sub in itertools.combinations(range(6), K):
        d = f2.receive([blk.messages[i] for i in sub])
        assert [d.values[i] for i in range(len(vals))] == vals, sub


@pytest.mark.parametrize("kw", [1, 2, 3])
@pytest.mark.parametrize("names", [("DOmin",), ("pHmin", "pHmax"), ("DOmin", "pHmin", "pHmax", "Tmax"), tuple(WIT)])
def test_layered_witnesses_round_trip_with_any_kw_messages(kw, names):
    vals = day_values(1)
    lay = {n: WIT[n] for n in names}
    blk = f2.build_block(vals, True, 77, 6, layered=lay, kw=kw)
    assert len(blk.messages) == 6
    for sub in itertools.combinations(range(6), max(kw, blk.K)):
        d = f2.receive([blk.messages[i] for i in sub])
        assert d.witness == lay, (kw, names, sub)
    d = f2.receive(blk.messages)
    if blk.coded:                                           # a record that does not fit in Q units is truncated by design
        assert [d.values[i] for i in range(len(vals))] == vals
    else:
        assert all(d.values[i] == vals[i] for i in d.values)


def test_witness_group_decodes_from_kw_messages_even_when_the_record_cannot():
    vals = day_values(2, n=60)
    blk = f2.build_block(vals, True, 5, 6, layered={"DOmin": 1234}, kw=1)
    assert blk.K >= 2
    d = f2.receive([blk.messages[5]])                       # one message: the witness group is decoded from it alone
    assert d.witness == {"DOmin": 1234}
    assert not blk.coded and set(d.values) <= set(range(len(vals)))      # an oversize record is uncoded: only its own unit shows


def test_hosted_witnesses_travel_with_the_record():
    vals = day_values(3, n=10)
    vpu = f2.values_per_unit(f2.record_unit_bits(0))
    hosted = {"DOmin": 1700}
    n_needed = -(-len(vals) // vpu)
    last = len(vals) - (n_needed - 1) * vpu
    if 24 + 24 * last + 6 + 13 > 144:
        pytest.skip("no room in the last unit for this seed")
    blk = f2.build_block(vals, True, 5, 6, hosted=hosted)
    d = f2.receive(blk.messages)
    assert d.witness == hosted


def test_record_capacity_equals_the_bit_budget():
    for names, kw in (((), 0), (("DO",), 1), (("pH",), 2), (("DO", "pH", "T", "EC"), 2)):
        wbytes = 0
        if names:
            wbytes = -(-(-(-cp.witness_bits(list(names)) // kw)) // 8)
        vpu = f2.values_per_unit(f2.record_unit_bits(wbytes))
        groups = [(list(names), kw)] if names else []
        assert vpu == cp.record_values_per_message(groups)


def test_single_bit_flip_in_any_message_is_always_detected():
    vals = day_values(4)
    blk = f2.build_block(vals, True, 40, 6, layered={"DOmin": 99}, kw=1)
    rng = np.random.default_rng(0)
    for i in range(6):
        for _ in range(40):
            raw = bytearray(blk.messages[i])
            b = int(rng.integers(0, len(raw) * 8))
            raw[b // 8] ^= 1 << (b % 8)
            assert f2._parse_message(bytes(raw)) is None


def test_corrupted_message_is_dropped_and_the_rest_still_decodes():
    vals = day_values(5)
    blk = f2.build_block(vals, True, 41, 6)
    msgs = list(blk.messages)
    bad = bytearray(msgs[0]); bad[10] ^= 0xFF
    msgs[0] = bytes(bad)
    d = f2.receive(msgs)
    assert d.crc_failed == 1 and [d.values[i] for i in range(len(vals))] == vals


def forge(raw, pos=12):
    """A corrupted message that passes the CRC (recomputed): the 2^-16 event."""
    b = bytearray(raw)
    b[pos] ^= 0x5A
    crc = f2.crc16(bytes(b[:3]) + bytes(b[5:]))
    b[3], b[4] = crc >> 8, crc & 0xFF
    return bytes(b)


def test_corroboration_detects_a_crc_passing_corruption_when_extra_messages_arrive():
    vals = day_values(6)[:9]                                # K = 2 of Q = 6: four redundant messages
    blk = f2.build_block(vals, True, 42, 6)
    assert blk.coded and blk.K < 6
    msgs = list(blk.messages)
    msgs[1] = forge(msgs[1])
    d = f2.receive(msgs)                                    # all six arrive: five are consistent, one is not
    assert d.record_rejected and len(d.values) == 0         # nothing certified from it
    d2 = f2.receive(msgs, corroborate=False)
    assert d2.accepted == 6                                  # without corroboration the forged message is used


def test_residual_risk_without_a_corroborating_message_is_stated():
    """With exactly K accepted messages a CRC-passing corruption cannot be detected: this is the residual risk."""
    vals = day_values(7)
    blk = f2.build_block(vals, True, 43, 6)
    K = blk.K
    msgs = [forge(blk.messages[i]) if i == 0 else blk.messages[i] for i in range(K)]
    d = f2.receive(msgs)
    assert not d.record_rejected and [d.values.get(i) for i in range(len(vals))] != vals


def test_layered_witness_copies_must_agree():
    vals = day_values(8)
    blk = f2.build_block(vals, True, 44, 6, layered={"DOmin": 1700}, kw=1)
    msgs = list(blk.messages)
    msgs[2] = forge(msgs[2], pos=6)                          # inside the witness symbol
    d = f2.receive(msgs)
    assert d.witness_rejected and "DOmin" not in d.witness


def test_golden_vector():
    vals = [("T", 10, 2000), ("T", 90, 2050), ("DO", 0, 1700), ("pH", 5, 3500)]
    blk = f2.build_block(vals, True, 9731, 3, layered={"DOmin": 1650}, kw=1, hosted=None)
    golden = [m.hex() for m in blk.messages]
    path = os.path.join(os.path.dirname(__file__), "golden", "frame2_example.txt")
    if not os.path.exists(path):
        with open(path, "w") as fh:
            fh.write("\n".join(golden) + "\n")
    assert golden == open(path).read().split()
