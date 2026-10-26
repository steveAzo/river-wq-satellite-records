"""Exact delivery probabilities (src/p3/analytic.py) against brute force, simulation, and the byte pipeline.
Run from Paper3/: python -m pytest tests -q"""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from p3 import analytic, channel, delivery, record  # noqa: E402
from golden_day import synthetic_day  # noqa: E402

CHANNELS = [("iid", 0.1), ("iid", 0.3), ("iid", 0.5), ("gilbert", 0.1), ("gilbert", 0.3), ("gilbert", 0.5)]


def ch_of(kind, p, burst=3):
    return analytic.iid(p) if kind == "iid" else analytic.gilbert(p, burst)


def brute(Q, ch, ok):
    return sum(analytic.p_mask(m, ch) for m in itertools.product([False, True], repeat=Q) if ok(np.array(m)))


@pytest.mark.parametrize("kind,p", CHANNELS)
def test_mask_probabilities_sum_to_one(kind, p):
    assert brute(8, ch_of(kind, p), lambda m: True) == pytest.approx(1.0)


@pytest.mark.parametrize("kind,p", CHANNELS)
@pytest.mark.parametrize("K,D,Q", [(1, 1, 1), (2, 2, 6), (3, 2, 6), (3, 3, 6), (5, 4, 9), (6, 6, 10)])
def test_mds_matches_brute_force(kind, p, K, D, Q):
    ch = ch_of(kind, p)
    exact = brute(Q, ch, lambda m: m.sum() >= K or m[:D].all())
    assert analytic.p_mds(K, D, Q, ch) == pytest.approx(exact, abs=1e-12)


@pytest.mark.parametrize("kind,p", CHANNELS)
@pytest.mark.parametrize("order", [[0, 1, 2, 0, 1, 2], [0, 0, 0, 0, 0, 2], [0, 1, 2, 3, 0, 1, 2, 3, 0], [0]])
def test_units_match_brute_force(kind, p, order):
    ch = ch_of(kind, p)
    units = set(order)
    exact = brute(len(order), ch, lambda m: {u for u, a in zip(order, m) if a} == units)
    assert analytic.p_units(order, ch) == pytest.approx(exact, abs=1e-12)


def test_iid_mds_matches_the_binomial_formula():
    from math import comb
    K, Q, p = 4, 10, 0.3
    binom = sum(comb(Q, i) * (1 - p) ** i * p ** (Q - i) for i in range(K, Q + 1))
    assert analytic.p_mds(K, K, Q, analytic.iid(p)) == pytest.approx(binom, abs=1e-12)


def test_gilbert_matches_simulation():
    rng = np.random.default_rng(5)
    order = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
    sims = [len({u for u, a in zip(order, channel.gilbert(12, 0.3, 3, rng)) if a}) == 4 for _ in range(40000)]
    assert np.mean(sims) == pytest.approx(analytic.p_units(order, analytic.gilbert(0.3)), abs=0.01)


def test_record_first_mds_attains_the_counting_bound():
    """Proposition 2: P(full) of record-first MDS = P(at least D1 of Q arrive), and no other unit-level design
    over the same record does better, for every channel tried."""
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    Q = 8
    rec = delivery.mds_rec(rd, enc, Q)
    D1 = rec.meta["K"]
    for kind, p in CHANNELS:
        ch = ch_of(kind, p)
        bound_n = brute(Q, ch, lambda m: m.sum() >= D1)
        assert analytic.p_mds(D1, D1, Q, ch) == pytest.approx(bound_n, abs=1e-12)
        assert analytic.p_units(delivery.cyclic(D1, Q), ch) <= bound_n + 1e-12
        for K in range(D1, Q + 1):
            assert analytic.p_mds(K, D1, Q, ch) <= bound_n + 1e-12


def test_byte_pipeline_agrees_with_the_exact_probability():
    """Sum over all 2^Q masks of P(mask) x Phi(bytes) equals bound x p_mds."""
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    s = delivery.mds_rec(rd, enc, 8)
    for kind, p in CHANNELS:
        ch = ch_of(kind, p)
        by_bytes = sum(analytic.p_mask(m, ch) * delivery.outcome(rd, s, np.array(m))["Phi"]
                       for m in itertools.product([False, True], repeat=8))
        assert by_bytes == pytest.approx(s.bound * analytic.p_mds(s.meta["K"], s.meta["D"], 8, ch), abs=1e-12)


def test_a_unit_that_is_never_sent_makes_full_delivery_impossible():
    """Regression (found in Step 6): the tag policy can skip a unit; full delivery then has probability 0."""
    for kind, p in CHANNELS:
        assert analytic.p_units([2, 0, 0, 0, 0, 2], ch_of(kind, p), n_units=3) == 0.0
        assert analytic.p_units([2, 0, 1, 0, 0, 2], ch_of(kind, p), n_units=3) > 0.0
