"""Tests of the integrity-study codec src/p3v3/frame3.py (development only). Run from Paper3/: python -m pytest -q -p no:cacheprovider tests/v3"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src", "p3v3"))
import frame3 as f3  # noqa: E402


@pytest.fixture(params=[(2, False), (2, True), (3, False), (3, True)])
def setting(request):
    f3.CRCB, f3.RECCRC = request.param
    yield request.param
    f3.CRCB, f3.RECCRC = 2, False


def vals(n):
    return [("DO", i, 100 + 7 * i) for i in range(n)]


@pytest.mark.parametrize("n", [3, 12, 24, 31, 40])
def test_roundtrip_all_and_subset(setting, n):
    v = vals(n)
    blk = f3.build_block(v, True, 5, 12)
    assert all(len(m) == 23 for m in blk.messages)
    d = f3.receive(blk.messages)
    assert not d.record_rejected and d.crc_failed == 0
    assert all(d.values.get(i) == v[i] for i in range(n))
    if blk.coded:
        sub = [blk.messages[i] for i in range(12 - blk.K, 12)]
        d = f3.receive(sub)
        assert not d.record_rejected and len(d.values) == n and all(d.values[i] == v[i] for i in range(n))


def test_record_check_detects_forged_unit_when_exactly_k(setting):
    crcb, rc = setting
    v = vals(24)
    blk = f3.build_block(v, True, 5, 6)
    if not blk.coded:
        pytest.skip("uncoded")
    msgs = list(blk.messages[:blk.K])
    b = bytearray(msgs[0])
    b[10] ^= 0x55
    crc = f3.msg_crc(bytes(b[:3]) + bytes(b[3 + crcb:]))
    b[3:3 + crcb] = crc.to_bytes(crcb, "big")
    msgs[0] = bytes(b)
    d = f3.receive(msgs)
    if rc:
        assert d.record_rejected and not d.values
    else:
        assert d.values != {i: v[i] for i in range(len(v))}


def test_capacity_of_crc24():
    f3.CRCB = 3
    try:
        assert f3.values_per_unit(f3.record_unit_bits(0)) == 4
    finally:
        f3.CRCB = 2
    assert f3.values_per_unit(f3.record_unit_bits(0)) == 5


def test_default_matches_frame2():
    from p3 import frame2 as f2
    v = vals(20)
    assert f3.build_block(v, True, 9, 6).messages == f2.build_block(v, True, 9, 6).messages
