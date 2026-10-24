"""Unit tests for the Paper 3 toolkit (src/p3). Run from Paper3/: python -m pytest tests -q"""
import itertools
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import channel, designs, pla, rs, server  # noqa: E402
from p3.data import SiteDay, tolerance  # noqa: E402


def make_sd(n=24, P=2, seed=0):
    rng = np.random.default_rng(seed)
    X = np.cumsum(rng.normal(0, 0.15, (P, n)), axis=1) + 10
    anchor = X[:, 0] - 0.05
    tol = np.full((P, n), 0.2)
    return SiteDay("test", pd.Timestamp("2023-01-01"), tuple(f"p{i}" for i in range(P)), X, anchor, tol, 60)


# ---- tolerances -------------------------------------------------------------------------------------
def test_usgs_excellent_tolerances():
    assert tolerance("T", [5.0, 30.0]).tolist() == [0.2, 0.2]
    assert tolerance("pH", [7.0]).tolist() == [0.2]
    assert tolerance("EC", [500.0])[0] == pytest.approx(15.0)          # 3 %
    assert tolerance("DO", [4.0])[0] == pytest.approx(0.3)             # floor
    assert tolerance("DO", [10.0])[0] == pytest.approx(0.5)            # 5 % is greater


# ---- min-# ------------------------------------------------------------------------------------------
def brute_min_points(x, anchor, tol, eps):
    n = len(x)
    for k in range(0, n + 1):
        for kept in itertools.combinations(range(n), k):
            err = np.abs(x - pla.reconstruct_one(x, anchor, list(kept))) / tol
            if err.max() <= eps + 1e-12:
                return k
    return n


@pytest.mark.parametrize("seed", range(6))
def test_min_set_is_minimal_and_feasible(seed):
    sd = make_sd(n=9, P=1, seed=seed)
    seg, tail = pla.tables(sd.X[0], sd.anchor[0], sd.tol[0])
    for eps in (0.5, 1.0, 2.0):
        kept = pla.min_set(seg, tail, eps)
        err = np.abs(sd.X[0] - pla.reconstruct_one(sd.X[0], sd.anchor[0], kept)) / sd.tol[0]
        assert err.max() <= eps + 1e-9
        assert len(kept) == brute_min_points(sd.X[0], sd.anchor[0], sd.tol[0], eps)


def test_fit_respects_budget_and_is_monotone():
    enc = pla.Encoder(make_sd(n=48, P=3, seed=3))
    taus = []
    for k in (3, 6, 12, 24, 48):
        tau, vals = enc.fit(k)
        assert len(vals) <= k
        e = server.picture(enc.sd, vals)
        assert e.max() <= tau + 1e-9
        taus.append(tau)
    assert all(a >= b for a, b in zip(taus, taus[1:]))


# ---- Reed-Solomon -------------------------------------------------------------------------------------
@pytest.mark.parametrize("K,Q", [(1, 6), (2, 6), (3, 6), (4, 6), (6, 6), (5, 12)])
def test_rs_any_K_of_Q_recover(K, Q):
    rng = np.random.default_rng(K * 100 + Q)
    data = [list(rng.integers(0, 256, 22)) for _ in range(K)]
    code = rs.encode(data, Q)
    assert code[:K] == data  # systematic
    for subset in itertools.islice(itertools.combinations(range(Q), K), 40):
        assert rs.decode({i: code[i] for i in subset}, K, Q) == data


# ---- designs and decoding -----------------------------------------------------------------------------
def test_designs_respect_quota_and_message_size():
    enc = pla.Encoder(make_sd(n=48, P=4, seed=5))
    Q = 6
    plans = [designs.raw_periodic(enc.sd, Q), designs.srdl_style(enc, Q), designs.reliable_opt(enc, Q),
             designs.repeat_r(enc, Q, 2), designs.repeat_r(enc, Q, 3), designs.mds_K(enc, Q, 3)]
    for pl in plans:
        assert len(pl.tx) <= Q, pl.name
        assert all(len(m) <= designs.V_DEFAULT for m in pl.data), pl.name
        assert 1 + 3 * designs.V_DEFAULT <= 23


def test_mds_decoding_rule():
    enc = pla.Encoder(make_sd(n=48, P=4, seed=6))
    pl = designs.mds_K(enc, 6, 3)
    all_vals = set(pl.planned)
    assert pl.delivered([True, False, False, True, True, False]) == all_vals          # 3 of 6
    some = pl.delivered([True, False, False, False, True, False])                      # 2 of 6
    assert some == set(pl.data[0])


def test_repeat_delivers_union_of_any_copy():
    enc = pla.Encoder(make_sd(n=48, P=4, seed=7))
    pl = designs.repeat_r(enc, 6, 3)
    mask = [False] * len(pl.tx)
    mask[len(pl.tx) - 1] = True  # only the last copy of the last message arrives
    assert pl.delivered(mask) == set(pl.data[pl.tx[-1]])


# ---- certification ------------------------------------------------------------------------------------
def test_certification_full_and_partial():
    sd = make_sd(n=24, P=1, seed=8)
    enc = pla.Encoder(sd)
    tau, vals = enc.fit(8)
    assert server.certified_share(sd, vals, vals) == pytest.approx(1.0)
    missing = vals[len(vals) // 2]
    share = server.certified_share(sd, vals, set(vals) - {missing})
    assert 0 < share < 1
    assert server.certified_share(sd, vals, set()) < 1


# ---- channels -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("p", [0.1, 0.3, 0.5])
def test_channel_mean_loss(p):
    rng = np.random.default_rng(1)
    assert 1 - channel.iid(200000, p, rng).mean() == pytest.approx(p, abs=0.01)
    assert 1 - channel.gilbert(200000, p, 3, rng).mean() == pytest.approx(p, abs=0.02)


# ---- buffer model (pooling.py) ------------------------------------------------------------------------
def test_buffer_lossless_fifo_and_delay():
    from p3 import pooling
    rng = np.random.default_rng(0)
    needs = np.array([7.0, 0.0, 21.0, np.nan, 0.0])
    out = pooling.simulate(needs, Q=1, K=1, loss="iid", p=0.0, rng=rng, D=7)
    # a day's values are complete at its end, so they leave on the next day (delay 1 = next day).
    # day 0 (7 values) goes on day 1; day 2 (21 values = 3 one-message blocks) goes on days 3, 4, 5.
    # days with zero need are guaranteed immediately (delay 0).
    assert [o[1] for o in out] == [True, True, True, True]
    assert [o[2] for o in out] == [1, 0, 3, 0]


def test_buffer_total_loss_never_guarantees():
    from p3 import pooling
    rng = np.random.default_rng(0)
    out = pooling.simulate(np.array([5.0, 5.0]), Q=6, K=3, loss="iid", p=1.0, rng=rng)
    assert not any(o[1] for o in out)
