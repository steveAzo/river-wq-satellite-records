"""Tests of the send-on-delta baseline and the scaled certificates (src/p3/sod.py, certlang scale)."""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import certlang as cl  # noqa: E402
from p3 import frame, record, sod  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402

BASE = {"T": 15.0, "DO": 8.0, "pH": 7.5, "EC": 400.0}
SCALE = {"T": 0.25, "DO": 0.4, "pH": 0.25, "EC": 20.0}


def walk(param, n, seed):
    rng = np.random.default_rng(seed)
    x = BASE[param] + np.cumsum(rng.normal(0, SCALE[param], n))
    x = np.abs(x) + (50 if param == "EC" else 0)
    return np.round(x, 2)


def chan(p, n, seed):
    x = walk(p, n, seed)
    return Channel(p, x, tolerance(p, x))


@pytest.mark.parametrize("param", ["T", "DO", "pH", "EC"])
@pytest.mark.parametrize("seed", range(5))
def test_full_delivery_is_within_tolerance_and_starts_at_slot_zero(param, seed):
    ch = chan(param, 60, seed)
    kept, codes = sod.select(ch)
    assert kept[0] == 0
    xhat = sod.reconstruct_hold(ch.n, kept, frame.dequantise(param, codes[kept]))
    assert np.isfinite(xhat).all()
    assert (np.abs(ch.x - xhat) / ch.tol <= 1 + 1e-9).all()
    # no claim about the number of values against the piecewise-linear record: neither rule dominates (measured in Step 4)


def test_flat_channel_is_one_value():
    ch = Channel("pH", np.full(40, 7.4), np.full(40, 0.2))
    assert sod.select(ch)[0] == [0]


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("params", [("T", "DO"), ("DO", "pH", "EC")])
def test_every_subset_is_valid_and_sound(seed, params):
    chans = [chan(p, 9, seed) for p in params]
    pl = sod.plan(chans)
    assert 2 <= len(pl) <= 15
    n_of = {c.param: c.n for c in chans}
    last = len(pl) - 1
    for r in range(len(pl) + 1):
        for got in itertools.combinations(range(len(pl)), r):
            rx = {i: pl[i] for i in got}
            cert = sod.certify_hold(rx, n_of, last if last in rx else None)
            for c in chans:
                K = sod.knowledge_hold(c.param, c.n, rx, cert[c.param])
                lo, hi = K.eff()
                assert (lo <= c.x).all() and (c.x <= hi).all(), (got, c.param)
                for thr in (c.x.min() - 0.1, c.x.min(), float(np.median(c.x)), c.x.max(), c.x.max() + 0.1):
                    d = cl.exceeds_below(K, thr)
                    assert d == -1 or bool(d) == bool((c.x < thr).any())
                    d = cl.exceeds_above(K, thr)
                    assert d == -1 or bool(d) == bool((c.x > thr).any())


@pytest.mark.parametrize("scale", [0.5, 0.25])
@pytest.mark.parametrize("seed", range(4))
def test_scaled_record_is_valid_and_sound_over_subsets(scale, seed):
    chans = [chan("DO", 8, seed), chan("pH", 8, seed)]
    scaled = [Channel(c.param, c.x, c.tol * scale) for c in chans]
    pl = record.Encoder(scaled).plan_at(1.0)
    n_of = {c.param: c.n for c in chans}
    last = len(pl) - 1
    for r in range(len(pl) + 1):
        for got in itertools.combinations(range(len(pl)), r):
            rx = {i: pl[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            for c in chans:
                K = cl.knowledge_from_rx(c.param, c.n, rx, cert[c.param], scale=scale)
                lo, hi = K.eff()
                assert (lo <= c.x).all() and (c.x <= hi).all(), (got, c.param, scale)
