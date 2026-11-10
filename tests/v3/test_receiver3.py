"""Tests and fuzz tests of the hardened receiver src/p3v3/receiver3.py and the guarded bounds src/p3v3/certlang3.py (finding A5).
Run from Paper3/: python -m pytest -q -p no:cacheprovider tests/v3/test_receiver3.py"""
import os
import sys
import time

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src", "p3v3"))
import certlang3 as cl3  # noqa: E402
import frame3 as f3  # noqa: E402
import receiver3 as r3  # noqa: E402
from p3 import certlang as cl  # noqa: E402

SETTINGS = [(2, False), (2, True), (3, False), (3, True)]
N_OF = {"T": 96, "DO": 96, "pH": 96, "EC": 96}
PARAMS = ("T", "DO", "pH", "EC")          # receiver order of parameters (frame3.PARAM_ORDER)


@pytest.fixture(params=SETTINGS, ids=lambda s: f"crc{8 * s[0]}{'_rec' if s[1] else ''}")
def setting(request):
    f3.CRCB, f3.RECCRC = request.param
    yield request.param
    f3.CRCB, f3.RECCRC = 2, False


def random_block(rng):
    """A valid block with random values, layered and hosted witnesses; None when the random layout does not fit."""
    nv = int(rng.integers(1, 41))
    keys = sorted({(int(rng.integers(0, 4)), int(rng.integers(0, 96))) for _ in range(nv)})
    vals = [(PARAMS[p], s, int(rng.integers(1, 8191))) for p, s in keys]
    Q = int(rng.choice([6, 12]))
    objs = list(f3.OBJECT_CODES)
    lay_objs = [o for o in objs if rng.random() < 0.4] if rng.random() < 0.6 else []
    host_objs = [o for o in objs if o not in lay_objs and rng.random() < 0.3]
    layered = {n: int(rng.integers(1, 8191)) for o in lay_objs for n in f3.OBJECT_CODES[o]} or None
    hosted = {n: int(rng.integers(1, 8191)) for o in host_objs for n in f3.OBJECT_CODES[o]} or None
    kw = int(rng.integers(1, 4))
    try:
        blk = f3.build_block(vals, bool(rng.random() < 0.8), int(rng.integers(0, 400)), Q, layered=layered, kw=kw, hosted=hosted)
    except ValueError:
        return None
    return blk


def _fix_crc(b):
    c = f3.CRCB
    crc = f3.msg_crc(bytes(b[:3]) + bytes(b[3 + c:]))
    b[3:3 + c] = crc.to_bytes(c, "big")
    return bytes(b)


def forge(msg, rng):
    """One corrupted copy of a message; most modes recompute the CRC so the receiver accepts it."""
    b = bytearray(msg)
    mode = rng.choice(["body", "header", "both", "descriptor", "flip", "trunc", "extend"])
    c = f3.CRCB
    if mode in ("body", "both"):
        b[3 + c:] = rng.integers(0, 256, len(b) - 3 - c, dtype=np.uint8).tobytes()
    if mode in ("header", "both"):
        b[:3] = rng.integers(0, 256, 3, dtype=np.uint8).tobytes()
        b[0] = (b[0] & 0x3F) | 0x80          # keep version 2 so that the message is parsed
    if mode == "descriptor":
        b[3 + c] = int(rng.integers(0, 256))
    if mode in ("body", "header", "both", "descriptor"):
        return _fix_crc(b)
    if mode == "flip":
        i = int(rng.integers(0, len(b)))
        b[i] ^= 1 << int(rng.integers(0, 8))
        return bytes(b)
    if mode == "trunc":
        return bytes(b[:int(rng.integers(0, len(b)))])
    return bytes(b) + b"\x00"


def scramble(msgs, rng):
    """Random subset, order, and duplicates of a list of messages, with one to three of them forged."""
    m = [x for x in msgs if rng.random() < 0.7] or [msgs[0]]
    for i in rng.choice(len(m), size=min(int(rng.integers(1, 4)), len(m)), replace=False):
        m[int(i)] = forge(m[int(i)], rng)
    if rng.random() < 0.3:
        m.append(m[int(rng.integers(0, len(m)))])
    order = rng.permutation(len(m))
    return [m[i] for i in order]


def invariants(d, raws):
    assert isinstance(d, f3.Decoded)
    assert d.accepted + d.crc_failed == len(raws)
    assert all(isinstance(k, int) for k in d.values)
    assert all(c not in (0, 8191) for c in d.witness.values())
    assert set(d.witness) <= set(f3.WITNESS_CODES)


# ------------------------------------------------------------------ equivalence on honest input
def test_equal_to_frame3_on_honest_blocks(setting):
    rng = np.random.default_rng(1)
    done = 0
    while done < 60:
        blk = random_block(rng)
        if blk is None:
            continue
        done += 1
        for raws in (blk.messages, scramble_honest(blk.messages, rng)):
            for corr in (True, False):
                for n_of in (None, N_OF):
                    assert r3.receive(raws, corr, n_of) == f3.receive(raws, corr, n_of)


def scramble_honest(msgs, rng):
    m = [x for x in msgs if rng.random() < 0.6] or [msgs[-1]]
    m += [m[0]] if rng.random() < 0.5 else []
    return [m[i] for i in rng.permutation(len(m))]


def test_honest_roundtrip_values(setting):
    vals = [("T", i, 100 + i) for i in range(10)] + [("DO", i, 200 + i) for i in range(3)]   # last unit leaves room for hosted codes
    blk = f3.build_block(vals, True, 3, 12, layered={"DOmin": 77, "Tmax": 900}, kw=2, hosted={"pHmin": 50, "pHmax": 60})
    d = r3.receive(blk.messages, n_of=N_OF)
    assert not d.record_rejected and not d.witness_rejected
    assert [d.values[i] for i in range(len(vals))] == vals
    assert d.witness == {"DOmin": 77, "Tmax": 900, "pHmin": 50, "pHmax": 60}


# ------------------------------------------------------------------ fuzz: forged, truncated, duplicated messages
@pytest.mark.parametrize("seed", [11, 12, 13])
def test_fuzz_never_raises_and_matches_frame3(setting, seed):
    rng = np.random.default_rng(seed + 100 * setting[0] + int(setting[1]))
    calls = f3_crash = 0
    slowest = 0.0
    while calls < 600:
        blk = random_block(rng)
        if blk is None:
            continue
        raws = scramble(blk.messages, rng)
        for corr in (True, False):
            n_of = N_OF if rng.random() < 0.5 else None
            t0 = time.perf_counter()
            d = r3.receive(raws, corr, n_of)
            slowest = max(slowest, time.perf_counter() - t0)
            calls += 1
            invariants(d, raws)
            try:
                ref = f3.receive(raws, corr, n_of)
            except Exception:                       # noqa: BLE001  (the gap the new receiver closes)
                f3_crash += 1
                assert d.record_rejected and d.witness_rejected and not d.values and not d.witness
                continue
            assert d == ref
    assert slowest < 2.0, slowest


def test_fuzz_honest_messages_survive_junk_objects(setting):
    """Non-message objects among honest messages count as failed messages and do not reject the block."""
    rng = np.random.default_rng(7)
    vals = [("pH", i, 3000 + i) for i in range(9)]
    blk = f3.build_block(vals, True, 8, 6)
    junk = [None, "abc", 17, 3.5, [1, 2, 3], b"", b"\x00" * 22, b"\xff" * 24, object(), {"a": 1}, bytearray(5)]
    raws = list(blk.messages) + junk
    raws = [raws[i] for i in rng.permutation(len(raws))]
    d = r3.receive(raws, n_of=N_OF)
    assert not d.record_rejected
    assert [d.values[i] for i in range(len(vals))] == vals
    assert d.accepted == len(blk.messages) and d.crc_failed == len(junk)


@pytest.mark.parametrize("raws", [None, 5, 3.0, object()])
def test_non_iterable_input_is_rejected(raws):
    d = r3.receive(raws)
    assert d.record_rejected and d.witness_rejected and not d.values and d.accepted == 0


def test_failing_iterator_is_rejected():
    def gen():
        yield b"\x00" * 23
        raise RuntimeError("broken source")
    d = r3.receive(gen())
    assert d.record_rejected and d.witness_rejected and not d.values


def test_empty_input():
    d = r3.receive([])
    assert d == f3.Decoded()


# ------------------------------------------------------------------ fault injection: error types frame3 does not catch
@pytest.mark.parametrize("exc", [TypeError, OverflowError, AttributeError, RecursionError, MemoryError, ArithmeticError])
@pytest.mark.parametrize("where", ["_receive_body", "_sanity"])
def test_any_exception_rejects(monkeypatch, exc, where):
    blk = f3.build_block([("T", i, 500 + i) for i in range(8)], True, 1, 6, layered={"Tmax": 600})

    def boom(*a, **k):
        raise exc("injected")
    monkeypatch.setattr(f3, where, boom)
    with pytest.raises(exc):
        f3.receive(blk.messages, n_of=N_OF)
    d = r3.receive(blk.messages, n_of=N_OF)
    assert d.record_rejected and d.witness_rejected and not d.values and not d.witness and d.last_pos is None
    if where == "_sanity":
        assert d.accepted == len(blk.messages)


def test_malformed_site_profile_rejects_instead_of_crashing():
    """A sanity rule that cannot be evaluated (profile entry of the wrong type) rejects the record; frame3 raises TypeError."""
    blk = f3.build_block([("EC", i, 4000 + i) for i in range(5)], True, 2, 6)
    bad = {"EC": None}
    with pytest.raises(TypeError):
        f3.receive(blk.messages, n_of=bad)
    d = r3.receive(blk.messages, n_of=bad)
    assert d.record_rejected and not d.values


# ------------------------------------------------------------------ guarded bounds
def all_censored(param="T", n=24, witness=False):
    K = cl.Knowledge(param, n)
    for s in range(n):
        K.add_kept(s, 0 if s % 2 else 8191)
    if witness:
        K.add_min_witness_value(1200)
        K.add_max_witness_value(1300)
    return K


@pytest.mark.parametrize("witness", [False, True])
def test_bounds_all_censored(witness):
    K = all_censored(witness=witness)
    with pytest.raises(ValueError):
        cl.max_bounds(K)
    with pytest.raises(ValueError):
        cl.min_bounds(K)
    assert cl3.min_bounds(K) == cl3.max_bounds(K) == cl3.day_max_bounds(K) == (-np.inf, np.inf)
    assert cl.exceeds_above(K, 20.0) == -1 and cl.exceeds_below(K, 5.0) == -1


def test_undefined_day_makes_rolling_mean_undetermined():
    days = [(30.0, 30.5)] * 6
    assert cl.rolling_mean_decision(days + [(30.0, 30.5)], 20.0) == 1
    assert cl.rolling_mean_decision(days + [cl3.day_max_bounds(all_censored())], 20.0) == -1


def test_zero_length_channel():
    K = cl.Knowledge("DO", 0)
    assert cl3.min_bounds(K) == cl3.max_bounds(K) == (-np.inf, np.inf)


@pytest.mark.parametrize("param", ["T", "DO", "pH", "EC"])
def test_bounds_equal_certlang_when_a_reading_is_live(param):
    rng = np.random.default_rng(PARAMS.index(param) + 40)
    for _ in range(300):
        n = int(rng.integers(1, 97))
        K = cl.Knowledge(param, n, resolution=rng.choice([None, 0.1, 0.01]))
        live = int(rng.integers(0, n))
        for s in range(n):
            r = rng.random()
            if s != live and r < 0.3:
                K.add_kept(s, int(rng.choice([0, 8191])))
            elif r < 0.7:
                K.add_kept(s, int(rng.integers(1, 8191)))
        if rng.random() < 0.4:
            K.add_min_witness_value(int(rng.integers(1, 8191)))
        if rng.random() < 0.4:
            K.add_max_witness_value(int(rng.integers(1, 8191)))
        assert cl3.min_bounds(K) == cl.min_bounds(K)
        assert cl3.max_bounds(K) == cl3.day_max_bounds(K) == cl.max_bounds(K)
