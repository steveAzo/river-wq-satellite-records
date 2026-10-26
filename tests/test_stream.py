"""Table-free encoder (src/p3/stream.py) gives exactly the plans of the table encoder (record.Encoder).
Run from Paper3/: python -m pytest tests -q"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from p3 import record, stream  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402
from golden_day import synthetic_day  # noqa: E402
from test_env import crossing_day  # noqa: E402


def walk(param, n, seed, scale, decimals=1):
    rng = np.random.default_rng(seed)
    base = {"T": 15.0, "DO": 8.0, "pH": 7.5, "EC": 400.0}[param]
    x = np.round(base + np.cumsum(rng.normal(0, scale, n)), decimals)
    if param == "EC":
        x = np.abs(x) + 50
    return Channel(param, x, tolerance(param, x))


@pytest.mark.parametrize("seed", range(40))
@pytest.mark.parametrize("n", [1, 2, 7, 24, 96])
def test_same_plan_as_the_table_encoder(seed, n):
    p = ["T", "DO", "pH", "EC"][seed % 4]
    ch = walk(p, n, seed, {"T": 0.15, "DO": 0.2, "pH": 0.06, "EC": 8.0}[p], decimals=0 if p == "EC" else 1)
    assert stream.plan([ch]) == record.Encoder([ch]).plan_at(1.0)


@pytest.mark.parametrize("seed", range(20))
def test_same_plan_with_censored_readings(seed):
    rng = np.random.default_rng(seed)
    ch = walk("DO", 48, seed, 0.2)
    ch.x[rng.choice(48, size=int(rng.integers(1, 4)), replace=False)] = rng.choice([-1.0, 55.0])
    assert stream.plan([ch]) == record.Encoder([ch]).plan_at(1.0)


@pytest.mark.parametrize("eps", [0.5, 1.0, 2.0])
def test_same_plan_at_other_levels(eps):
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    assert stream.plan(rd.channels, eps) == enc.plan_at(eps)


@pytest.mark.parametrize("seed", range(6))
def test_same_plan_on_days_with_ties_at_the_tolerance(seed):
    """Decimal readings (0.1 resolution) against a 0.2 tolerance produce errors exactly at the tolerance."""
    rd = crossing_day(seed)
    assert stream.plan(rd.channels) == record.Encoder(rd.channels).plan_at(1.0)


def test_flat_and_constant_channels():
    ch = Channel("pH", np.full(288, 7.4), np.full(288, 0.2))
    assert stream.plan([ch]) == record.Encoder([ch]).plan_at(1.0) and len(stream.plan([ch])) == 1
