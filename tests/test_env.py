"""Environmental decisions from delivered records (src/p3/env.py). Run from Paper3/: python -m pytest tests -q"""
import itertools
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import env, frame, record  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.loader import RecordDay  # noqa: E402

SLACK = 1 + 1e-9


def crossing_day(seed, do_base=6.0, ph_base=8.4):
    """A day whose DO dips near 5 mg/L at night and whose pH peaks near 9 in the afternoon."""
    rng = np.random.default_rng(seed)
    n, t = 96, np.arange(96)
    x = {"T": np.round(22 + 3 * np.sin(2 * np.pi * (t - 36) / n) + np.cumsum(rng.normal(0, 0.03, n)), 1),
         "DO": np.round(do_base + 1.6 * np.sin(2 * np.pi * (t - 40) / n) + np.cumsum(rng.normal(0, 0.03, n)), 1),
         "pH": np.round(ph_base + 0.6 * np.sin(2 * np.pi * (t - 40) / n), 1),
         "EC": np.round(400 + np.where((t > 50) & (t < 56), 80, 0) + np.cumsum(rng.normal(0, 1, n)))}
    chs = [record.Channel(p, x[p].astype(float), tolerance(p, x[p])) for p in ("T", "DO", "pH", "EC")]
    return RecordDay("env", pd.Timestamp("2023-07-14"), chs, {p: 15 for p in x})


def delivered(plan, units):
    rx = {}
    for u in units:
        for pos in range(5 * u, min(5 * u + 5, len(plan))):
            rx[pos] = plan[pos]
    last = len(plan) - 1 if (len(plan) - 1) // 5 in units else None
    return rx, last


BASES = [(6.0, 8.4), (8.5, 7.4), (5.6, 9.2), (5.3, 6.6)]   # (DO, pH) levels: dips, safe, peaks, both edges
SEEN = set()


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("bases", BASES)
def test_three_valued_decisions_are_never_wrong_for_any_loss_pattern(seed, bases):
    rd = crossing_day(seed, *bases)
    plan = record.Encoder(rd.channels).plan_at(1.0)
    n_units = -(-len(plan) // 5)
    assert n_units <= 12
    decided = 0
    for r in range(n_units + 1):
        for units in itertools.combinations(range(n_units), r):
            rx, last = delivered(plan, set(units))
            m = env.day_metrics(rd, rx, True, last)
            for k in ("DO", "pH"):
                if m[f"{k}_3v"] != -1:
                    decided += 1
                    assert m[f"{k}_3v"] == int(m[f"{k}_true"])
                SEEN.add((k, m[f"{k}_3v"]))


def test_every_three_valued_outcome_was_exercised():
    """Runs after the parametrised test above (pytest keeps file order)."""
    assert {("DO", 1), ("DO", 0), ("pH", 1), ("pH", 0), ("DO", -1), ("pH", -1)} <= SEEN


@pytest.mark.parametrize("seed", range(6))
def test_full_delivery_keeps_daily_extremes_within_tolerance(seed):
    rd = crossing_day(seed)
    plan = record.Encoder(rd.channels).plan_at(1.0)
    rx, last = delivered(plan, set(range(-(-len(plan) // 5))))
    m = env.day_metrics(rd, rx, True, last)
    for p in ("T", "DO", "pH", "EC"):
        assert m[f"{p}_min_err"] <= SLACK and m[f"{p}_max_err"] <= SLACK
    for p in ("T", "pH", "EC"):
        assert m[f"{p}_mean_err"] <= SLACK
    assert m["certified_share"] == 1.0


def test_certified_7dadm_bounds_contain_the_truth():
    rng = np.random.default_rng(0)
    days = list(range(100, 120))
    true, lo, hi = {}, {}, {}
    for d in days:
        rd = crossing_day(int(rng.integers(1000)))
        plan = record.Encoder(rd.channels).plan_at(1.0)
        n_units = -(-len(plan) // 5)
        units = {u for u in range(n_units) if rng.random() < 0.8}
        m = env.day_metrics(rd, *delivered(plan, units), True)
        true[d], lo[d], hi[d] = m["Tmax_true"], m["Tmax_lo"], m["Tmax_hi"]
    t7, l7, h7 = env.seven_dadm(days, true), env.seven_dadm(days, lo), env.seven_dadm(days, hi)
    assert t7 and set(t7) == set(l7) == set(h7)
    for d in t7:
        assert l7[d] <= t7[d] + 1e-9 <= h7[d] + 2e-9


def test_nothing_received_is_undetermined_and_a_naive_miss():
    rd = crossing_day(1, do_base=5.2)
    m = env.day_metrics(rd, {}, False, None)
    assert m["DO_3v"] == -1 and not m["DO_naive"] and m["DO_true"]
    assert np.isnan(m["DO_min_err"]) and m["Tmax_lo"] == -np.inf
