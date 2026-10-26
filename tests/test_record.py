"""Tests of the record model, encoder and certificates (src/p3/record.py; docs/RECORD_MODEL.md).
Run from Paper3/: python -m pytest tests -q"""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import frame, record  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402

SLACK = 1 + 1e-9


def walk(param, n, seed, scale):
    rng = np.random.default_rng(seed)
    base = {"T": 15.0, "DO": 8.0, "pH": 7.5, "EC": 400.0}[param]
    x = base + np.cumsum(rng.normal(0, scale, n))
    if param == "EC":
        x = np.abs(x) + 50
    return Channel(param, x, tolerance(param, x))


def err_of(ch, kept, anchor=None):
    codes = frame.quantise(ch.param, ch.x[kept])
    rec = record.reconstruct(ch.n, kept, frame.dequantise(ch.param, codes), anchor)
    return np.abs(ch.x - rec) / ch.tol


def brute_min(ch, eps, anchor=None):
    for k in range(1, ch.n + 1):
        for kept in itertools.combinations(range(ch.n), k):
            if err_of(ch, list(kept), anchor).max() <= eps + 1e-12:
                return k
    return None


# ---- encoder ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("anchored", [False, True])
def test_min_set_is_feasible_and_minimal(seed, anchored):
    ch = walk(["T", "DO", "pH", "EC"][seed % 4], 9, seed, 0.12 if seed % 4 != 3 else 9.0)
    if anchored:
        ch.anchor = float(frame.roundtrip(ch.param, ch.x[0] - 0.05))
    tab = record.tables(ch)
    for eps in (0.5, 1.0, 2.0):
        kept = record.min_set(tab, eps)
        assert err_of(ch, kept, ch.anchor).max() <= eps * SLACK          # exact under quantisation
        assert len(kept) == brute_min(ch, eps, ch.anchor)                # and minimal


def test_flat_channel_needs_one_value_self_contained():
    ch = Channel("pH", np.full(50, 7.4), np.full(50, 0.2))
    assert len(record.min_set(record.tables(ch), 1.0)) == 1


def test_out_of_range_reading_is_censored_kept_and_excluded():
    """Step 9: a reading outside the quantiser range (sensor glitch) is carried as a flag, always kept, and
    excluded from the tolerance requirement; the rest of the day stays certifiable."""
    x = np.array([10.0, 10.1, 90.0, 10.2, 10.1, 10.0])      # 90 degC is above the quantiser range
    ch = Channel("T", x, np.full(6, 0.2))
    plan = record.Encoder([ch]).plan_at(1.0)
    assert plan is not None and ("T", 2, frame.CODE_MAX) in plan
    rx = dict(enumerate(plan))
    e = record.errors([ch], rx)["T"]
    assert e[2] == 0 and (e <= SLACK).all()
    cert, full = record.certify(rx, {"T": 6}, True, len(plan) - 1)
    assert full and not cert["T"][2] and cert["T"][[0, 1, 3, 4, 5]].all()


def brute_min_censored(ch, eps):
    codes = frame.quantise(ch.param, ch.x)
    cen = frame.saturated(codes)
    must = set(np.flatnonzero(cen))
    for k in range(1, ch.n + 1):
        for kept in itertools.combinations(range(ch.n), k):
            if not must <= set(kept):
                continue
            rec = record.reconstruct(ch.n, list(kept), frame.dequantise(ch.param, codes[list(kept)]))
            if (np.abs(ch.x - rec)[~cen] / ch.tol[~cen]).max(initial=0) <= eps + 1e-12:
                return k
    return None


@pytest.mark.parametrize("seed", range(10))
def test_censored_plans_are_minimal_and_certificates_sound(seed):
    rng = np.random.default_rng(seed)
    ch = walk("DO", 10, seed, 0.12)
    glitch = rng.choice(10, size=int(rng.integers(1, 3)), replace=False)
    ch.x[glitch] = rng.choice([-1.0, 55.0], size=len(glitch))       # below and above the DO range
    plan = record.Encoder([ch]).plan_at(1.0)
    assert len(plan) == brute_min_censored(ch, 1.0)
    planned = dict(enumerate(plan))
    for r in range(len(planned) + 1):
        for got in itertools.combinations(range(len(planned)), r):
            rx = {i: planned[i] for i in got}
            L = len(planned) - 1
            cert, full = record.certify(rx, {"DO": 10}, True, L if L in rx else None)
            assert not cert["DO"][glitch].any()
            assert (record.errors([ch], rx)["DO"][cert["DO"]] <= SLACK).all()
            assert full == (len(got) == len(planned))


def test_fit_uses_the_smallest_level_that_fits():
    chs = [walk("T", 30, 1, 0.15), walk("DO", 30, 2, 0.2)]
    enc = record.Encoder(chs)
    for k in (2, 4, 8, 16):
        tau, plan = enc.fit(k)
        assert len(plan) <= k
        lower = enc.cands[enc.cands < tau]
        assert len(lower) == 0 or enc.count(len(lower) - 1) > k


# ---- certificates: exhaustive over losses ------------------------------------------------------------
def plan_positions(chs, tau=1.0):
    plan = record.Encoder(chs).plan_at(tau)
    return {i: v for i, v in enumerate(plan)}


@pytest.mark.parametrize("seed", range(10))
def test_certificate_is_sound_for_every_loss_pattern(seed):
    chs = [walk("T", 14, seed, 0.25), walk("DO", 14, seed + 100, 0.35)]
    planned = plan_positions(chs)
    L = len(planned) - 1
    assert L <= 13, "keep the exhaustive test small"
    n_of = {c.param: c.n for c in chs}
    for r in range(len(planned) + 1):
        for got in itertools.combinations(range(len(planned)), r):
            rx = {i: planned[i] for i in got}
            cert, full = record.certify(rx, n_of, True, L if L in rx else None)
            err = record.errors(chs, rx)
            for p in n_of:
                assert (err[p][cert[p]] <= SLACK).all()                  # every certified reading in tolerance
            assert full == (len(got) == len(planned))                    # full iff everything arrived


def test_certificate_is_not_vacuous():
    """Some loss pattern leaves an uncertified reading outside tolerance (the certificate matters)."""
    found = False
    for seed in range(20):
        chs = [walk("T", 14, seed, 0.25)]
        planned = plan_positions(chs)
        for i in range(1, len(planned) - 1):
            rx = {j: v for j, v in planned.items() if j != i}
            cert, _ = record.certify(rx, {"T": 14}, True, len(planned) - 1)
            e = record.errors(chs, rx)["T"]
            found |= bool((e[~cert["T"]] > 1).any())
    assert found


def test_unbound_day_is_never_certified():
    chs = [walk("T", 14, 3, 0.25)]
    planned = plan_positions(chs)
    cert, full = record.certify(planned, {"T": 14}, False, len(planned) - 1)
    assert not full and not cert["T"].any()


def test_channel_boundary_needs_the_neighbouring_position():
    """The first DO value is known to be first only if the last T value (previous position) arrived."""
    chs = [walk("T", 14, 5, 0.25), walk("DO", 14, 6, 0.35)]
    planned = plan_positions(chs)
    first_do = min(i for i, v in planned.items() if v[0] == "DO")
    rx = {i: v for i, v in planned.items() if i != first_do - 1}
    cert, _ = record.certify(rx, {"T": 14, "DO": 14}, True, len(planned) - 1)
    s = planned[first_do][1]
    assert s == 0 or not cert["DO"][:s].any()


# ---- anchors -----------------------------------------------------------------------------------------
def test_chained_head_is_certified_only_with_a_known_anchor():
    chs = [walk("T", 14, 8, 0.25)]
    chs[0].anchor = float(frame.roundtrip("T", chs[0].x[0] + 0.15))
    planned = plan_positions(chs)
    s = planned[0][1]
    cert, _ = record.certify(planned, {"T": 14}, True, len(planned) - 1, anchor_ok={"T": False})
    assert s == 0 or not cert["T"][:s].any()
    cert, full = record.certify(planned, {"T": 14}, True, len(planned) - 1, anchor_ok={"T": True})
    assert full and (record.errors(chs, planned, {"T": chs[0].anchor})["T"] <= SLACK).all()


def test_lost_anchor_breaks_a_chained_plan():
    """Burst across midnight: a chained plan that leans on the anchor violates tolerance when the
    previous day's last value is lost; the self-contained plan of the same day does not."""
    x = np.concatenate((np.linspace(16.0, 14.0, 6), np.full(8, 14.0)))
    tol = np.full(14, 0.2)
    chain = Channel("T", x, tol, anchor=float(frame.roundtrip("T", 16.2)))
    plan = record.Encoder([chain]).plan_at(1.0)
    rx = {i: v for i, v in enumerate(plan)}
    with_anchor = record.errors([chain], rx, {"T": chain.anchor})["T"]
    without = record.errors([chain], rx, None)["T"]
    assert with_anchor.max() <= SLACK and without.max() > 1
    selfc = Channel("T", x, tol)
    plan_s = record.Encoder([selfc]).plan_at(1.0)
    assert record.errors([selfc], {i: v for i, v in enumerate(plan_s)})["T"].max() <= SLACK
    assert len(plan_s) >= len(plan)


def test_oracle_anchor_is_not_what_the_server_holds():
    """The draft started each day from the TRUE previous reading. The server only holds the previous day's
    held value, which can differ by up to one tolerance; a plan built on the true reading can then fail."""
    fails = 0
    for seed in range(40):
        rng = np.random.default_rng(seed)
        prev_true = 15.0
        held = float(frame.roundtrip("T", prev_true + rng.uniform(-0.19, 0.19)))   # within tolerance
        x = prev_true + np.cumsum(rng.normal(0, 0.08, 14))
        ch = Channel("T", x, np.full(14, 0.2), anchor=prev_true)
        plan = record.Encoder([ch]).plan_at(1.0)
        rx = {i: v for i, v in enumerate(plan)}
        fails += record.errors([ch], rx, {"T": held})["T"].max() > SLACK
    assert fails > 0


# ---- server-side intervals (Step 8) -----------------------------------------------------------------------
@pytest.mark.parametrize("param,lo,hi", [("T", -1, 35), ("DO", 0.1, 20), ("pH", 6, 10), ("EC", 20, 5000)])
def test_interval_contains_every_true_value_within_tolerance(param, lo, hi):
    rng = np.random.default_rng(3)
    x = rng.uniform(lo, hi, 200000)
    d = tolerance(param, x)
    xhat = x + rng.uniform(-1, 1, len(x)) * d          # anything the certificate allows
    L, U = record.interval(param, xhat)
    assert (L <= x + 1e-12).all() and (x <= U + 1e-12).all()
    # and the interval is not loose by more than two tolerances
    assert ((U - L) <= 2.2 * tolerance(param, xhat) + 1e-9).all()
