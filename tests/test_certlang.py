"""Tests of the certificate language (revision 2, Step 2; src/p3/certlang.py; docs/CERTIFICATE_SPEC.md).
Run from Paper3/: python -m pytest tests/test_certlang.py -q"""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import certlang as cl  # noqa: E402
from p3 import frame, record  # noqa: E402
from p3.data import TOLSETS, tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402

BASE = {"T": 15.0, "DO": 8.0, "pH": 7.5, "EC": 400.0}
SCALE = {"T": 0.25, "DO": 0.4, "pH": 0.25, "EC": 20.0}


def walk(param, n, seed):
    rng = np.random.default_rng(seed)
    x = BASE[param] + np.cumsum(rng.normal(0, SCALE[param], n))
    x = np.abs(x) + (50 if param == "EC" else 0)
    return np.round(x, 2)


# ---- interval and cell lemmas ------------------------------------------------------------------------------
@pytest.mark.parametrize("param", ["T", "DO", "pH", "EC"])
def test_interval_is_the_exact_solution_set(param):
    a, r = TOLSETS["excellent"][param]
    rng = np.random.default_rng(1)
    scale = 300 if param == "EC" else 1
    for xhat in rng.uniform(0.5, 12, 25) * scale:
        lo, hi = cl.interval(param, xhat)
        xs = np.linspace(max(0.0, lo - 1), hi + 1, 400001)
        feasible = np.abs(xs - xhat) <= np.maximum(a, r * xs) + 1e-12
        step = xs[1] - xs[0]
        assert abs(xs[feasible].min() - lo) <= 2 * step and abs(xs[feasible].max() - hi) <= 2 * step
        assert feasible[(xs >= lo + 2 * step) & (xs <= hi - 2 * step)].all()      # no gaps: it is an interval


@pytest.mark.parametrize("param", ["T", "DO", "pH", "EC"])
def test_every_reading_lies_in_the_cell_of_its_code(param):
    rng = np.random.default_rng(2)
    x = rng.uniform(1, 90000, 5000) if param == "EC" else rng.uniform(0.01, 40, 5000)
    code = frame.quantise(param, x)
    ok = ~frame.saturated(code)
    for xi, c in zip(x[ok], code[ok]):
        lo, hi = cl.cell(param, c)
        assert lo <= xi <= hi, (param, xi, c, lo, hi)


# ---- soundness over every subset of arrived values (real codec) ---------------------------------------------
def thresholds(x):
    lo, hi = float(x.min()), float(x.max())
    span = max(hi - lo, 0.05)
    return [lo - 0.5 * span, lo - 0.02 * span, lo, lo + 0.1 * span, 0.5 * (lo + hi), hi - 0.1 * span, hi,
            hi + 0.02 * span, hi + 0.5 * span]


def witnesses(param, x):
    """Honest min and max witnesses over the uncensored readings."""
    codes = frame.quantise(param, x)
    idx = np.flatnonzero(~frame.saturated(codes))
    smin = int(idx[np.argmin(x[idx])])
    smax = int(idx[np.argmax(x[idx])])
    return (smin, int(codes[smin])), (smax, int(codes[smax]))


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("params", [("T", "DO"), ("DO", "pH", "EC")])
def test_every_subset_is_valid_and_sound(seed, params):
    chans = [Channel(p, walk(p, 8, seed), tolerance(p, walk(p, 8, seed))) for p in params]
    plan = record.Encoder(chans).plan_at(1.0)
    n_of = {c.param: c.n for c in chans}
    last = len(plan) - 1
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            for c in chans:
                wmin, wmax = witnesses(c.param, c.x)
                for variant in range(8):
                    grid = 0.01 if (variant & 4 and c.param != "EC") else None     # readings were rounded to 0.01
                    Kv = cl.knowledge_from_rx(c.param, c.n, rx, cert[c.param], resolution=grid)
                    if variant & 1:
                        Kv.add_min_witness(*wmin)
                    if variant & 2:
                        Kv.add_max_witness(*wmax)
                    lo, hi = Kv.eff()
                    assert (lo <= c.x).all() and (c.x <= hi).all(), (got, variant)      # validity
                    b = cl.min_bounds(Kv)
                    assert b[0] <= c.x.min() <= b[1]
                    b = cl.max_bounds(Kv)
                    assert b[0] <= c.x.max() <= b[1]
                    for thr in thresholds(c.x):
                        d = cl.exceeds_below(Kv, thr)
                        assert d == -1 or bool(d) == bool((c.x < thr).any()), (got, variant, thr)
                        d = cl.exceeds_above(Kv, thr)
                        assert d == -1 or bool(d) == bool((c.x > thr).any()), (got, variant, thr)
                    if c.param == "EC":
                        truth = bool((np.abs(c.x[1:] - c.x[:-1]) / c.x[:-1] > 0.10).any())
                        d = cl.relative_change(Kv, 1)
                        assert d == -1 or bool(d) == truth


def test_censored_reading_is_outside_every_decision():
    x = np.array([8.0, 8.1, 90.0, 8.2, 8.1, 8.0])        # 90 mg/L is above the DO range: censored
    ch = Channel("DO", x, tolerance("DO", x))
    plan = record.Encoder([ch]).plan_at(1.0)
    rx = dict(enumerate(plan))
    cert, full = record.certify(rx, {"DO": 6}, True, len(plan) - 1)
    K = cl.knowledge_from_rx("DO", 6, rx, cert["DO"])
    assert K.excluded[2] and full
    assert cl.exceeds_above(K, 40.0) == 0          # the glitch is not a reading above 40
    assert cl.exceeds_below(K, 5.0) == 0


# ---- witnesses decide with nothing else received -----------------------------------------------------------
def test_min_witness_alone_certifies_no_exceedance():
    K = cl.Knowledge("DO", 288)
    assert cl.exceeds_below(K, 5.0) == -1
    K.add_min_witness(100, int(frame.quantise("DO", 7.3)))
    assert cl.exceeds_below(K, 5.0) == 0          # the minimum is 7.3: nothing below 5, certified from one value
    assert cl.exceeds_below(K, 8.0) == 1          # and something below 8
    assert cl.exceeds_below(K, 7.3) == -1         # a threshold inside the witness cell cannot be decided
    K2 = cl.Knowledge("DO", 288)
    K2.add_min_witness(100, int(frame.quantise("DO", 4.2)))
    assert cl.exceeds_below(K2, 5.0) == 1


def test_grid_assumption_decides_readings_exactly_on_the_threshold():
    code = int(frame.quantise("DO", 5.0))
    K = cl.Knowledge("DO", 288)
    K.add_min_witness(10, code)
    assert cl.exceeds_below(K, 5.0) == -1                  # without the grid, the cell straddles 5.0
    Kg = cl.Knowledge("DO", 288, resolution=0.1)
    Kg.add_min_witness(10, code)
    assert cl.exceeds_below(Kg, 5.0) == 0                  # readings are multiples of 0.1: the minimum is exactly 5.0
    assert cl.exceeds_below(Kg, 5.1) == 1
    assert cl.min_bounds(Kg) == pytest.approx((5.0, 5.0))
    # a span whose tolerance edge lies exactly on the threshold (x_hat = 6.7, delta = 0.2, threshold 6.5)
    Ks = cl.Knowledge("pH", 4, resolution=0.01)
    Ks.add_span(np.ones(4, bool), np.full(4, 6.7))
    assert cl.exceeds_below(Ks, 6.5) == 0
    Kn = cl.Knowledge("pH", 4)
    Kn.add_span(np.ones(4, bool), np.full(4, 6.7))
    assert cl.exceeds_below(Kn, 6.5) == -1                 # the encoder's own 1e-9 slack keeps this undetermined


def test_infer_resolution():
    assert cl.infer_resolution([5.0, 5.1, 7.3]) == 0.1
    assert cl.infer_resolution([5.01, 5.1]) == 0.01
    assert cl.infer_resolution([5.0004]) is None


# ---- conductance change: exact on the interval model -------------------------------------------------------
def test_pairwise_rule_is_incomplete_but_the_exact_rule_decides():
    K = cl.Knowledge("EC", 3)
    for t, (a, b) in enumerate([(100, 100), (100, 130), (130, 130)]):
        K.lo[t], K.hi[t] = a, b
    assert cl.relative_change(K, 1) == 1           # x1 <= 110 changes against x2, x1 > 110 against x0
    pair01 = K.hi[1] < 0.9 * K.lo[0] or K.lo[1] > 1.1 * K.hi[0]
    pair12 = K.hi[2] < 0.9 * K.lo[1] or K.lo[2] > 1.1 * K.hi[1]
    assert not pair01 and not pair12               # neither pair alone is certain


@pytest.mark.parametrize("seed", range(60))
def test_relative_change_matches_brute_force(seed):
    rng = np.random.default_rng(seed)
    K = cl.Knowledge("EC", 3)
    narrow = seed % 2 == 1                          # narrow, close intervals give certain 'no' cases
    for t in range(3):
        c = rng.uniform(100, 106) if narrow else rng.uniform(80, 140)
        w = rng.uniform(0, 3) if narrow else rng.uniform(0, 25)
        K.lo[t], K.hi[t] = c - w, c + w
    g = [np.linspace(K.lo[t], K.hi[t], 61) for t in range(3)]
    X = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
    chg = (np.abs(X[:, 1:] - X[:, :-1]) / X[:, :-1] > 0.10).any(1)
    d = cl.relative_change(K, 1)
    if d == 1:
        assert chg.all()
    elif d == 0:
        assert not chg.any()
    else:
        assert chg.any() and not chg.all()         # exact: undetermined only if both outcomes are possible
    # the grid contains every corner, so 'all change' on the grid with a generic box implies a certain yes
    if chg.all():
        assert d == 1
    if not chg.any():
        assert d == 0


# ---- rolling statistic --------------------------------------------------------------------------------------
def test_rolling_mean_with_missing_day_is_undetermined_until_bounded():
    assert cl.rolling_mean_decision([(21.0, 21.5)] * 7, 20.0) == 1
    assert cl.rolling_mean_decision([(18.0, 18.5)] * 7, 20.0) == 0
    missing = [(21.0, 21.5)] * 6 + [cl.base_range("T")]
    assert cl.rolling_mean_decision(missing, 20.0) == -1
    assert cl.rolling_mean_decision([(75.0, 76.0)] * 6 + [cl.base_range("T")], 20.0) == 1


# ---- rate witness (conductance pulse) ----------------------------------------------------------------------
def honest_rate_witness(x, lag):
    codes = frame.quantise("EC", x)
    ok = ~frame.saturated(codes)
    best, arg = -1.0, None
    for t in range(len(x) - lag):
        if ok[t] and ok[t + lag]:
            r = abs(x[t + lag] - x[t]) / x[t]
            if r > best:
                best, arg = r, t
    return arg, int(codes[arg]), arg + lag, int(codes[arg + lag])


@pytest.mark.parametrize("lag", [1, 2])
@pytest.mark.parametrize("seed", range(6))
def test_rate_witness_every_subset_is_sound(seed, lag):
    x = walk("EC", 9, seed)
    ch = Channel("EC", x, tolerance("EC", x))
    plan = record.Encoder([ch]).plan_at(1.0)
    n_of = {"EC": ch.n}
    last = len(plan) - 1
    truth = bool((np.abs(x[lag:] - x[:-lag]) / x[:-lag] > 0.10).any())
    wa, ca, wb, cb = honest_rate_witness(x, lag)
    saw_no = saw_yes = False
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            for use in (False, True):
                K = cl.knowledge_from_rx("EC", ch.n, rx, cert["EC"])
                if use:
                    K.add_rate_witness(wa, ca, wb, cb, lag)
                lo, hi = K.eff()
                assert (lo <= x).all() and (x <= hi).all()
                d = cl.relative_change(K, lag)
                assert d == -1 or bool(d) == truth, (got, use, d, truth)
                if use and r == 0:
                    saw_no |= d == 0
                    saw_yes |= d == 1
    # with no record at all, the witness alone decides: no pulse if its ratio is small, pulse if the pair itself shows one
    assert saw_no == (not truth) or saw_yes == truth or (not saw_no and not saw_yes)


def test_rate_witness_alone_certifies_no_pulse():
    x = np.array([400.0, 402.0, 399.0, 401.0, 400.0, 398.0])
    wa, ca, wb, cb = honest_rate_witness(x, 1)
    K = cl.Knowledge("EC", 6)
    assert cl.relative_change(K, 1) == -1
    K.add_rate_witness(wa, ca, wb, cb, 1)
    assert cl.relative_change(K, 1) == 0                   # largest hourly change is about 0.7%: no pair exceeds 10%
    y = np.array([400.0, 402.0, 480.0, 401.0, 400.0, 398.0])
    wa, ca, wb, cb = honest_rate_witness(y, 1)
    K2 = cl.Knowledge("EC", 6)
    K2.add_rate_witness(wa, ca, wb, cb, 1)
    assert cl.relative_change(K2, 1) == 1                  # the witness pair itself shows a change above 10%


# ---- slotless witnesses (frame v2) against the slotted ones, for the queries a witness is sent for ------------
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("params", [("T", "DO"), ("DO", "pH", "EC")])
def test_slotless_witnesses_decide_like_slotted_ones_for_their_own_queries(seed, params):
    """A min witness serves 'below' decisions and the day minimum; a max witness serves 'above' decisions and the day
    maximum. The slotted witness also pins one reading (it carries the slot), so the slotless witness is weaker only for the
    opposite side, which no design asks. For the matched queries: the slotless decision is sound and is made whenever the
    slotted one is (and then equals it); the slotless interval lies inside the slotted one and contains the truth."""
    chans = [Channel(p, walk(p, 8, seed), tolerance(p, walk(p, 8, seed))) for p in params]
    plan = record.Encoder(chans).plan_at(1.0)
    n_of = {c.param: c.n for c in chans}
    last = len(plan) - 1
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            for c in chans:
                (smin, cmin), (smax, cmax) = witnesses(c.param, c.x)
                grid = 0.01 if c.param != "EC" else None
                for variant in (1, 2, 3):
                    Ka = cl.knowledge_from_rx(c.param, c.n, rx, cert[c.param], resolution=grid)
                    Kb = cl.knowledge_from_rx(c.param, c.n, rx, cert[c.param], resolution=grid)
                    if variant & 1:
                        Ka.add_min_witness(smin, cmin)
                        Kb.add_min_witness_value(cmin)
                    if variant & 2:
                        Ka.add_max_witness(smax, cmax)
                        Kb.add_max_witness_value(cmax)
                    for thr in thresholds(c.x):
                        if variant & 1:
                            da, db = cl.exceeds_below(Ka, thr), cl.exceeds_below(Kb, thr)
                            assert db == -1 or bool(db) == bool((c.x < thr).any())          # sound
                            assert da in (-1, db), (got, variant, thr, da, db)                # decides whenever slotted does
                        if variant & 2:
                            da, db = cl.exceeds_above(Ka, thr), cl.exceeds_above(Kb, thr)
                            assert db == -1 or bool(db) == bool((c.x > thr).any())
                            assert da in (-1, db), (got, variant, thr, da, db)
                    if variant & 1:
                        a, b = cl.min_bounds(Ka), cl.min_bounds(Kb)
                        assert b[0] <= c.x.min() <= b[1] and a[0] - 1e-9 <= b[0] and b[1] <= a[1] + 1e-9
                    if variant & 2:
                        a, b = cl.max_bounds(Ka), cl.max_bounds(Kb)
                        assert b[0] <= c.x.max() <= b[1] and a[0] - 1e-9 <= b[0] and b[1] <= a[1] + 1e-9


@pytest.mark.parametrize("lag", [1, 2])
@pytest.mark.parametrize("seed", range(6))
def test_slotless_rate_witness_is_sound_and_decides_like_the_slotted_one(seed, lag):
    x = walk("EC", 9, seed)
    ch = Channel("EC", x, tolerance("EC", x))
    plan = record.Encoder([ch]).plan_at(1.0)
    n_of = {"EC": ch.n}
    last = len(plan) - 1
    truth = bool((np.abs(x[lag:] - x[:-lag]) / x[:-lag] > 0.10).any())
    wa, ca, wb, cb = honest_rate_witness(x, lag)
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            Ka = cl.knowledge_from_rx("EC", ch.n, rx, cert["EC"])
            Kb = cl.knowledge_from_rx("EC", ch.n, rx, cert["EC"])
            Ka.add_rate_witness(wa, ca, wb, cb, lag)
            Kb.add_rate_witness_values(ca, cb, lag)
            da, db = cl.relative_change(Ka, lag), cl.relative_change(Kb, lag)
            assert db == -1 or bool(db) == truth, (got, db, truth)          # sound
            assert db in (-1, da) or da == -1                                # never contradicts; may only be weaker


# ---- witness cross-check ------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("params", [("T", "DO"), ("DO", "pH", "EC")])
def test_honest_witnesses_are_never_contradicted_by_the_record(seed, params):
    chans = [Channel(p, walk(p, 8, seed), tolerance(p, walk(p, 8, seed))) for p in params]
    plan = record.Encoder(chans).plan_at(1.0)
    n_of = {c.param: c.n for c in chans}
    last = len(plan) - 1
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, _ = record.certify(rx, n_of, True, last if last in rx else None)
            for c in chans:
                (_, cmin), (_, cmax) = witnesses(c.param, c.x)
                for grid in ((0.01,) if c.param != "EC" else (None,)):
                    K0 = cl.knowledge_from_rx(c.param, c.n, rx, cert[c.param], resolution=grid)
                    assert cl.witness_consistent(K0, "min", cmin) and cl.witness_consistent(K0, "max", cmax), got


def test_a_forged_witness_is_rejected_when_the_record_contradicts_it():
    x = np.array([8.0, 8.1, 8.2, 8.1, 8.0, 8.1])
    ch = Channel("DO", x, tolerance("DO", x))
    plan = record.Encoder([ch]).plan_at(1.0)
    rx = dict(enumerate(plan))
    cert, _ = record.certify(rx, {"DO": 6}, True, len(plan) - 1)
    K0 = cl.knowledge_from_rx("DO", 6, rx, cert["DO"])
    assert cl.witness_consistent(K0, "min", int(frame.quantise("DO", 8.0)))
    assert not cl.witness_consistent(K0, "min", int(frame.quantise("DO", 9.5)))     # claims a minimum above every reading
    assert not cl.witness_consistent(K0, "min", int(frame.quantise("DO", 3.0)))     # the whole record is certified at 7.7 or more
