"""E7: how far is the greedy value order from the per-budget OPTIMUM of the worst-case record error?

For one site-day (all parameters) and a budget of k values, the optimum is
    eps*(k) = min over value sets S, |S| = k, of max over (p, t) |x_p(t) - xhat_p(t)| / tol_p,
with the same server reconstruction as E2/E5 (interpolate from the anchor through delivered values,
hold the last). It is computed exactly: for each parameter, seg[i, j] = worst normalised error of the
straight segment between kept points i < j (i = -1 is the anchor) and tail[j] = worst error when j is
the last kept point; a dynamic program gives the fewest points m_p(eps) that keep parameter p within eps,
and eps*(k) is the smallest candidate eps with sum_p m_p(eps) <= k (binary search over candidates).
Greedy is E5's Node (largest normalised error first). Also checks whether greedy's worst error is
monotone non-increasing in the number of values sent (a property a guarantee would need).
Random sample of USGS site-days (seed 20261016). Run from Paper3/:
    python -I src/scoping/e7_greedy_vs_optimal.py [n_samples=300]
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("e5", os.path.join(os.path.dirname(__file__), "e5_worstcase_pooled.py"))
e5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e5)


def seg_tables(x, anchor, tol):
    """seg[i+1, j]: worst normalised error of the segment from kept point i (-1 = anchor) to kept j."""
    n = len(x)
    xs = np.concatenate(([anchor], x))  # index shift: position q in xs is slot q-1
    seg = np.zeros((n + 1, n + 1))
    for a in range(n + 1):
        for b in range(a + 2, n + 1):
            t = np.arange(a + 1, b)
            line = xs[a] + (xs[b] - xs[a]) * (t - a) / (b - a)
            seg[a, b] = np.max(np.abs(xs[t] - line)) / tol
    tail = np.array([np.max(np.abs(xs[q + 1:] - xs[q])) / tol if q < n else 0.0 for q in range(n + 1)])
    return seg, tail


def min_points(seg, tail, eps):
    """Fewest kept slots so that the whole series is within eps (positions 1..n in xs; 0 is the anchor)."""
    n1 = seg.shape[0]
    INF = 10 ** 9
    f = np.full(n1, INF)
    f[0] = 0
    for b in range(1, n1):
        ok = seg[:b, b] <= eps
        if ok.any():
            f[b] = f[:b][ok].min() + 1
    cand = [f[q] for q in range(n1) if tail[q] <= eps and f[q] < INF]
    return min(cand)


def optimum(X, anchors, tols, k):
    tabs = [seg_tables(X[p], anchors[p], tols[p]) for p in range(X.shape[0])]
    cands = np.unique(np.concatenate([np.concatenate((s.ravel(), t)) for s, t in tabs]))
    lo, hi = 0, len(cands) - 1
    while lo < hi:  # smallest eps with total points <= k
        mid = (lo + hi) // 2
        if sum(min_points(s, t, cands[mid]) for s, t in tabs) <= k:
            hi = mid
        else:
            lo = mid + 1
    return float(cands[lo])


def main():
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    days = e5.load_days()
    items = [(d, s) for d, sites in days.items() for s in sites]
    rng = np.random.default_rng(20261016)
    pick = rng.choice(len(items), size=min(n_samples, len(items)), replace=False)
    rows, nonmono = [], 0
    for c, idx in enumerate(pick):
        d, s = items[idx]
        X, a, t = days[d][s]
        full_vals = X.size
        node = e5.Node(X, a, t)
        trace = [node.top()]
        kmax = int(0.2 * full_vals * 2 / 3)
        for _ in range(kmax):
            if node.top() <= 0:
                break
            node.send_top()
            trace.append(node.top())
        trace = np.array(trace)
        nonmono += int(np.any(np.diff(trace) > 1e-12))
        for f in e5.FRACS:
            k = int(f * full_vals * 2 // 3)  # same byte budget, 3 B per value
            g = float(trace[min(k, len(trace) - 1)])
            o = optimum(X, a, t, k)
            rows.append({"day": d, "site": s, "frac": f, "k": k, "greedy": g, "opt": o})
        if c % 50 == 0:
            print(c, flush=True)
    out = pd.DataFrame(rows)
    out["ratio"] = out.greedy / out.opt.clip(lower=1e-9)
    out.to_csv("results/scoping/e7_greedy_vs_optimal.csv", index=False)
    print(f"\n{len(pick)} site-days. Greedy worst error non-monotone in {nonmono} of them.")
    print(out.groupby("frac").agg(opt_med=("opt", "median"), greedy_med=("greedy", "median"),
                                  ratio_med=("ratio", "median"), ratio_p90=("ratio", lambda r: r.quantile(0.9)),
                                  opt_ok=("opt", lambda o: (o <= 1).mean()), greedy_ok=("greedy", lambda g: (g <= 1).mean())).round(3).to_string())


if __name__ == "__main__":
    main()
