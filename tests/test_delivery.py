"""Tests of the byte-level delivery designs and server (src/p3/delivery.py).
Run from Paper3/: python -m pytest tests -q"""
import itertools
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from p3 import delivery, frame, record  # noqa: E402
from golden_day import GOLDEN, golden_cases, synthetic_day  # noqa: E402

SLACK = 1 + 1e-9


@pytest.fixture(scope="module")
def cases():
    return golden_cases()


def all_masks(n):
    return [np.array(m, bool) for m in itertools.product([False, True], repeat=n)]


# ---- golden vectors ----------------------------------------------------------------------------------
def test_golden_bytes_are_reproduced(cases):
    _, got = cases
    gold = json.load(open(GOLDEN))
    for k, s in got.items():
        assert [m.hex() for m in s.msgs] == gold[k]["msgs"], k
        assert [list(v) for v in s.planned] == gold[k]["planned"], k


def test_golden_bytes_decode_without_the_plan(cases):
    rd, _ = cases
    gold = json.load(open(GOLDEN))
    day = delivery.day_number(rd.day)
    for k, g in gold.items():
        rx, last, bound, fails = delivery.receive([bytes.fromhex(m) for m in g["msgs"]], day)
        assert fails == 0 and bound == g["bound"]
        assert all(tuple(v) == tuple(g["planned"][i]) for i, v in rx.items())     # every value at its position
        if k != "tag_Q6":   # tag practice picks units with replacement; with this seed unit 1 is never sent
            assert len(rx) == len(g["planned"]) and last == len(g["planned"]) - 1
    assert sorted(set(json.load(open(GOLDEN))["tag_Q6"]["idx"])) == [0, 2]


# ---- every arrival pattern ---------------------------------------------------------------------------
def test_mds_full_certification_matches_the_analytic_rule(cases):
    rd, got = cases
    s = got["mds_K4_Q6"]
    K, D = s.meta["K"], s.meta["D"]
    for mask in all_masks(6):
        o = delivery.outcome(rd, s, mask)
        expect = mask.sum() >= K or mask[:D].all()
        assert o["Phi"] == (expect and s.bound)
        if o["Phi"]:
            assert o["F"] and o["cert"] == 1.0


def test_repetition_full_iff_every_unit_arrives(cases):
    rd, got = cases
    s = got["repeat2_Q6"]
    for mask in all_masks(6):
        o = delivery.outcome(rd, s, mask)
        units = {i for i, ok in zip(s.idx, mask) if ok}
        assert o["Phi"] == (units == set(s.idx))


@pytest.mark.parametrize("name", ["mds_K4_Q6", "repeat2_Q6", "every_k_Q6", "tag_Q6"])
def test_certified_readings_are_within_tolerance_for_every_pattern(cases, name):
    rd, got = cases
    s = got[name]
    day = delivery.day_number(rd.day)
    for mask in all_masks(len(s.msgs)):
        rx, last, bound, _ = delivery.receive([m for m, ok in zip(s.msgs, mask) if ok], day)
        cert, _ = record.certify(rx, rd.n_of, bound, last)
        err = record.errors(rd.channels, rx)
        for p in cert:
            assert (err[p][cert[p]] <= SLACK).all()


def test_unbound_designs_are_never_certified(cases):
    rd, got = cases
    for name in ("every_k_Q6", "tag_Q6"):
        assert not got[name].bound
        assert delivery.outcome(rd, got[name], np.ones(6, bool))["cert"] == 0.0


def test_reliable_needs_every_unit():
    rd = synthetic_day()
    s = delivery.reliable(rd, record.Encoder(rd.channels), 6)
    assert s.bound
    for mask in all_masks(len(s.msgs)):
        assert delivery.outcome(rd, s, mask)["Phi"] == mask.all()


# ---- integrity ---------------------------------------------------------------------------------------
def test_a_corrupted_message_never_produces_a_false_certificate(cases):
    rd, got = cases
    s = got["mds_K4_Q6"]
    day = delivery.day_number(rd.day)
    rng = np.random.default_rng(0)
    for _ in range(300):
        msgs = [bytearray(m) for m in s.msgs]
        j, b = rng.integers(0, 6), rng.integers(8 * frame.HEADER_BYTES, 8 * 23)
        msgs[j][b // 8] ^= 0x80 >> (b % 8)
        keep = rng.random(6) < 0.8
        rx, last, bound, fails = delivery.receive([bytes(m) for m, ok in zip(msgs, keep) if ok], day)
        cert, _ = record.certify(rx, rd.n_of, bound, last)
        err = record.errors(rd.channels, rx)
        for p in cert:
            assert (err[p][cert[p]] <= SLACK).all()


def test_cache_does_not_change_outcomes(cases):
    rd, got = cases
    s = got["mds_K4_Q6"]
    mask = np.array([1, 0, 1, 1, 0, 1], bool)
    first = dict(delivery.outcome(rd, s, mask))
    s.cache.clear()
    assert delivery.outcome(rd, s, mask) == first
