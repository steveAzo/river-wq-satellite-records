"""Tests that pin the findings of the in-project review of 2026-11-09 (docs/CERTIFICATE_SPEC.md, Proposition 2 correction;
docs/CONFIRM3_PLAN.md, Section 3a). Run from Paper3/: python -m pytest tests/test_review_fixes.py -q"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import certlang as cl  # noqa: E402


def test_witness_rules_are_sound_but_not_exact():
    """Reading 2 cannot be the minimum, so reading 1 is in the witness cell and no reading exceeds 5; the box rule says -1."""
    K = cl.Knowledge("DO", 2)
    K.lo[:], K.hi[:] = [3.0, 4.5], [10.0, 4.6]
    K.g_lo, K.wmin = 4.0, (4.0, 4.01)
    assert cl.exceeds_above(K, 5.0) == -1        # incomplete (true answer 0); never wrong


def test_wrong_resolution_gives_a_certain_wrong_decision():
    """Documents the unsoundness of assumption R when the declared resolution is wrong (true reading 7.03, resolution 0.1)."""
    K = cl.Knowledge("DO", 1, resolution=0.1)
    K.lo[:], K.hi[:] = 7.02, 7.04
    assert cl.exceeds_below(K, 7.01) == 1        # wrong: 7.03 is not below 7.01
    K0 = cl.Knowledge("DO", 1, resolution=0.01)
    K0.lo[:], K0.hi[:] = 7.02, 7.04
    assert cl.exceeds_below(K0, 7.01) == 0       # correct with the right resolution


# ---- receiver (frame v2) findings
from p3 import frame2 as f2  # noqa: E402
from p3.frame import crc16  # noqa: E402

_VALS = [("T", s, 500 + s) for s in range(0, 40, 4)] + [("DO", s, 900 + s) for s in range(0, 40, 5)]
_WIT = {"DOmin": 800, "pHmin": 700, "pHmax": 1500}


def _refresh(m):
    m = bytearray(m)
    c = crc16(bytes(m[:3]) + bytes(m[5:]))
    m[3], m[4] = c >> 8, c & 255
    return bytes(m)


def _block():
    blk = f2.build_block(_VALS, True, 100, 12, layered=_WIT, kw=2)
    return blk, [blk.messages[i] for i in (0, 2, 4, 7, 9, 11)]


def test_descriptor_mismatch_rejects_the_block_even_without_the_sanity_rule():
    _, sel = _block()
    for t in range(6):
        ms = list(sel)
        m = bytearray(ms[t])
        m[5] ^= 0x01
        ms[t] = _refresh(m)
        d = f2.receive(ms)                       # no profile: no sanity rule
        assert d.record_rejected and d.witness_rejected and not d.values


def test_conflicting_duplicates_are_rejected_in_either_order():
    _, sel = _block()
    for byte in (15, 7):
        m = bytearray(sel[1])
        m[byte] ^= 0xFF
        dup = _refresh(m)
        for L in (sel + [dup], [dup] + sel):
            d = f2.receive(L)
            assert d.record_rejected and d.witness_rejected and not d.values


def test_identical_duplicates_are_harmless():
    blk, sel = _block()
    d = f2.receive(sel + [sel[0], sel[3]])
    assert not d.record_rejected and len(d.values) == len(_VALS) and d.witness == _WIT


def test_forge_always_changes_the_message_body():
    import numpy as np
    from p3 import robust2
    blk, _ = _block()
    rng = np.random.default_rng(0)
    for _ in range(3000):
        raw = blk.messages[int(rng.integers(12))]
        assert robust2.forge(raw, rng)[5:] != raw[5:]
