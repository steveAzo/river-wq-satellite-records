"""Agreement of the frozen decoder (src/p3/certlang.py) with the rules as written in the manuscript (Section 3.2, Eqs. 3 to 6),
and soundness of both on random small days with known truth (second outside review, 2026-11-12, concern 1).

The manuscript rules are re-implemented here from the text, independently of certlang, and compared on random knowledge:
random intervals (some readings with the base range, some known censored), random minimum, maximum, and rate witnesses.
A second pass draws a true day first, builds valid knowledge around it (kept cells, tolerance-like intervals, base ranges, and
the honest witnesses of the true day), and checks that no certain answer of either implementation contradicts the truth.
Run from Paper3/: python -I paper_tools/spec_check.py [trials]
"""
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from p3 import certlang as cl  # noqa: E402
from p3 import frame  # noqa: E402

F = 0.10


# ---------------------------------------------------------------- the manuscript's rules, written from the text
def eff(K):                                                           # Eq. (3)
    return np.maximum(K.lo, K.g_lo), np.minimum(K.hi, K.g_hi)


def spec_below(K, th):                                                # Eq. (4)
    lo, hi = eff(K)
    m = ~K.excluded
    if not m.any():
        return -1
    if (hi[m] < th).any() or (K.wmin is not None and K.wmin[1] < th):
        return 1
    return 0 if (lo[m] >= th).all() else -1


def spec_above(K, th):                                                # Eq. (4), symmetric
    lo, hi = eff(K)
    m = ~K.excluded
    if not m.any():
        return -1
    if (lo[m] > th).any() or (K.wmax is not None and K.wmax[0] > th):
        return 1
    return 0 if (hi[m] <= th).all() else -1


def spec_min(K):                                                      # Eq. (5)
    lo, hi = eff(K)
    m = ~K.excluded
    a, b = lo[m].min(), hi[m].min()
    return a, (min(b, K.wmin[1]) if K.wmin is not None else b)


def spec_max(K):
    lo, hi = eff(K)
    m = ~K.excluded
    a, b = lo[m].max(), hi[m].max()
    return (max(a, K.wmax[0]) if K.wmax is not None else a), b


def spec_change(K, lag):                                              # Eq. (6), chain rule and rate witness
    lo, hi = eff(K)
    m = ~K.excluded
    if lag < 1 or K.n <= lag or (lo[m] <= 0).any():
        return -1
    if K.rate_cells is not None and K.rate_lag == lag:
        La, Ua, Lb, Ub = K.rate_cells
        r_lo, r_hi = Lb / Ua, Ub / La
        if r_lo >= 1 - F and r_hi <= 1 + F:
            return 0
        if r_lo > 1 + F or r_hi < 1 - F:
            return 1
    no = True
    for r in range(lag):
        chain = [t for t in range(r, K.n, lag)]
        reach = None
        for i, t in enumerate(chain):
            if not m[t]:
                reach = None
                continue
            if reach is None:
                reach = (lo[t], hi[t])
                continue
            p = chain[i - 1]
            if hi[t] > (1 + F) * lo[p] or lo[t] < (1 - F) * hi[p]:
                no = False
            reach = (max(lo[t], (1 - F) * reach[0]), min(hi[t], (1 + F) * reach[1]))
            if reach[0] > reach[1]:
                return 1
    return 0 if no else -1


# ---------------------------------------------------------------- random knowledge
def random_knowledge(rng, param, n, truth=None):
    K = cl.Knowledge(param=param, n=n)
    b0, b1 = cl.base_range(param)
    centre = (5.0, 9.0) if param != "EC" else (200.0, 800.0)
    x = truth if truth is not None else rng.uniform(*centre, n)
    for t in range(n):
        u = rng.random()
        if truth is None and u < 0.05:
            K.excluded[t] = True
        elif u < 0.25:
            continue                                                  # base range
        elif u < 0.55:
            K.add_kept(t, int(frame.quantise(param, [x[t]])[0]))
        else:
            w = rng.uniform(0.01, 0.6) * (1.0 if param != "EC" else x[t] / 7)
            a = x[t] - rng.uniform(0, w)
            K.lo[t], K.hi[t] = max(K.lo[t], a), min(K.hi[t], a + w)
    live = x[~K.excluded]
    if live.size and rng.random() < 0.6:
        K.add_min_witness_value(int(frame.quantise(param, [live.min() if truth is not None else rng.uniform(*centre)])[0]))
    if live.size and rng.random() < 0.6:
        K.add_max_witness_value(int(frame.quantise(param, [live.max() if truth is not None else rng.uniform(*centre)])[0]))
    return K, x


def true_change(x, lag):
    return bool(any(abs(x[t + lag] - x[t]) / x[t] > F for t in range(len(x) - lag)))


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    rng = np.random.default_rng(20261112)
    agree = {"below": 0, "above": 0, "min": 0, "max": 0, "change": 0}
    wrong = {"spec": 0, "code": 0}
    decided = 0
    for i in range(trials):
        param = ("DO", "pH", "T", "EC")[i % 4]
        n = int(rng.integers(2, 9))
        # agreement on arbitrary knowledge
        K, _ = random_knowledge(rng, param, n)
        if param == "EC" and rng.random() < 0.6:
            a, b = rng.uniform(200, 800, 2)
            K.add_rate_witness_values(int(frame.quantise("EC", [a])[0]), int(frame.quantise("EC", [b])[0]), 1)
        if (~K.excluded).any():
            for th in rng.uniform(4, 10, 3) if param != "EC" else []:
                assert spec_below(K, th) == cl.exceeds_below(K, th), (i, "below")
                assert spec_above(K, th) == cl.exceeds_above(K, th), (i, "above")
                agree["below"] += 1
                agree["above"] += 1
            assert np.allclose(spec_min(K), cl.min_bounds(K)), (i, "min", spec_min(K), cl.min_bounds(K))
            assert np.allclose(spec_max(K), cl.max_bounds(K)), (i, "max")
            agree["min"] += 1
            agree["max"] += 1
            if param == "EC":
                assert spec_change(K, 1) == cl.relative_change(K, 1, F), (i, "change")
                agree["change"] += 1
        # soundness with a known true day
        x = (np.round(rng.uniform(4.0, 9.5) + np.cumsum(rng.normal(0, 0.4, n)), 3) if param != "EC"
             else np.round(500 * np.exp(np.cumsum(rng.normal(0, 0.08, n))), 1))
        x = np.clip(x, 0.5, None)
        K, _ = random_knowledge(rng, param, n, truth=x)
        if param == "EC" and n > 1:
            r = [abs(x[t + 1] - x[t]) / x[t] for t in range(n - 1)]
            t = int(np.argmax(r))
            K.add_rate_witness_values(int(frame.quantise("EC", [x[t]])[0]), int(frame.quantise("EC", [x[t + 1]])[0]), 1)
        checks = []
        if param != "EC":
            for th in rng.uniform(3, 11, 4):
                checks += [(spec_below(K, th), cl.exceeds_below(K, th), bool(x.min() < th)),
                           (spec_above(K, th), cl.exceeds_above(K, th), bool(x.max() > th))]
            for f in (spec_min, cl.min_bounds):
                a, b = f(K)
                assert a - 1e-9 <= x.min() <= b + 1e-9, (i, "min interval excludes the truth")
            for f in (spec_max, cl.max_bounds):
                a, b = f(K)
                assert a - 1e-9 <= x.max() <= b + 1e-9, (i, "max interval excludes the truth")
        elif n > 1:
            checks.append((spec_change(K, 1), cl.relative_change(K, 1, F), true_change(x, 1)))
        for s, c, truth in checks:
            if s != -1:
                decided += 1
                wrong["spec"] += int(s != int(truth))
            wrong["code"] += int(c != -1 and c != int(truth))
    print(f"{trials} random days: manuscript rules and frozen decoder agreed on every comparison {agree}")
    print(f"soundness on days with known truth: {decided} certain answers, wrong (manuscript rules) {wrong['spec']}, "
          f"wrong (decoder) {wrong['code']}; every extremum interval contained the true extremum")
    assert wrong["spec"] == 0 and wrong["code"] == 0


if __name__ == "__main__":
    main()
