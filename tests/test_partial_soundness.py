"""Exhaustive small-case soundness of partial certificates and three-valued decisions (revision 2, Step 1;
review item 5.5). For small multi-parameter days, EVERY subset of the planned values is treated as the set that
arrived (this includes the prefixes sent on oversize days and the absence of the last-value flag). For each subset:
  - every certified reading satisfies e <= 1 against the true record;
  - a three-valued decision that is not 'undetermined' agrees with the truth, for thresholds on both sides of the
    record, below and above.
Run from Paper3/: python -m pytest tests/test_partial_soundness.py -q"""
import itertools
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import env, frame, record  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402

SLACK = 1 + 1e-9
BASE = {"T": 15.0, "DO": 8.0, "pH": 7.5, "EC": 400.0}
SCALE = {"T": 0.25, "DO": 0.4, "pH": 0.25, "EC": 15.0}


def make_day(seed, params, n):
    rng = np.random.default_rng(seed)
    chans = []
    for p in params:
        x = BASE[p] + np.cumsum(rng.normal(0, SCALE[p], n))
        if p == "EC":
            x = np.abs(x) + 50
        chans.append(Channel(p, np.round(x, 2), tolerance(p, np.round(x, 2))))
    return chans


def thresholds(x, param):
    lo, hi = float(x.min()), float(x.max())
    span = max(hi - lo, 0.05)
    return [lo - 0.5 * span, lo - 0.05 * span, lo, lo + 0.1 * span, 0.5 * (lo + hi), hi - 0.1 * span,
            hi, hi + 0.05 * span, hi + 0.5 * span]


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("params", [("T", "DO"), ("DO", "pH", "EC")])
def test_every_subset_is_sound(seed, params):
    chans = make_day(seed, params, 8)
    plan = record.Encoder(chans).plan_at(1.0)
    assert plan is not None and 2 <= len(plan) <= 13
    n_of = {c.param: c.n for c in chans}
    last = len(plan) - 1
    checked = decided = 0
    for r in range(len(plan) + 1):
        for got in itertools.combinations(range(len(plan)), r):
            rx = {i: plan[i] for i in got}
            cert, full = record.certify(rx, n_of, True, last if last in rx else None)
            err = record.errors(chans, rx)
            rec = env.reconstruct_all(type("RD", (), {"channels": chans})(), rx)
            for c in chans:
                e = np.nan_to_num(err[c.param], nan=np.inf)
                assert (e[cert[c.param]] <= SLACK).all(), (got, c.param)
                for thr in thresholds(c.x, c.param):
                    for kw, truth in (({"below": thr}, bool((c.x < thr).any())),
                                      ({"above": thr}, bool((c.x > thr).any()))):
                        d = env.three_valued(c.param, rec[c.param], cert[c.param], **kw)
                        checked += 1
                        if d != -1:
                            decided += 1
                            assert bool(d) == truth, (got, c.param, kw, d, truth)
            if full:
                assert all(np.isfinite(err[c.param]).all() and (err[c.param] <= SLACK).all() for c in chans)
    assert checked > 0 and decided > 0
