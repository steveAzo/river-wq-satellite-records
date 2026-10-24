"""E13: guaranteed records over a one-way, quota-limited, lossy link (satellite IoT micro-plan).

Each site-day the node has Q messages of 19 B: 1 B header + 6 values x 3 B (2 B value + 1 B slot/param
index). Each message is lost independently with probability p, and the node never learns which ones
arrived. The server interpolates through whatever values arrive (E2's reconstruction).
Strategies, all using exactly Q messages:
  oblivious   : smallest tau whose min-# set fits 6Q values; each message sent once (loss-oblivious
                optimum; the reliable-link design of SBR-like schemes and of scope A2).
  repeat_r    : smallest tau whose min-# set fits 6Q/r values; every message sent r times (blind
                repetition, as satellite IoT practice does), r = 2, 3.
  layered     : coarse layer = min-# set at the smallest tau fitting a share s of the values, sent r_c
                times; fine layer = the remaining values of the oblivious set's ... (see code: the values
                of the min-# set at the smallest tau fitting the rest, excluding coarse values), sent once.
                (s, r_c) chosen per p from a small grid on the TUNING half of the sample (even site-days),
                then evaluated on the other half.
Metrics over 40 loss draws per site-day: P(whole day within tolerance, worst error <= 1) and the mean
worst error (tolerance units). USGS-Excellent tolerances. Sample: 200 random USGS site-days.
Run from Paper3/: python -I src/scoping/e13_oneway_loss.py [Q=6]
"""
import importlib.util
import itertools
import os
import sys

import numpy as np
import pandas as pd

here = os.path.dirname(__file__)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


e5, e7 = load("e5", "e5_worstcase_pooled.py"), load("e7", "e7_greedy_vs_optimal.py")
VPM = 6  # values per 19-byte message


def min_set(seg, tail, eps):
    """Positions (1-based in the anchor-prefixed series) of a fewest-points set within eps."""
    n1 = seg.shape[0]
    INF = 10 ** 9
    f = np.full(n1, INF)
    back = np.full(n1, -1)
    f[0] = 0
    for b in range(1, n1):
        ok = np.flatnonzero(seg[:b, b] <= eps)
        if len(ok):
            a = ok[np.argmin(f[ok])]
            f[b], back[b] = f[a] + 1, a
    ends = [q for q in range(n1) if tail[q] <= eps and f[q] < INF]
    q = min(ends, key=lambda q: f[q])
    pts = []
    while q > 0:
        pts.append(q)
        q = back[q]
    return pts[::-1]


class SiteDay:
    def __init__(self, X, a, t):
        self.X, self.a, self.t = X, a, t
        self.tabs = [e7.seg_tables(X[p], a[p], t[p]) for p in range(X.shape[0])]
        self.cands = np.unique(np.concatenate([np.concatenate((s.ravel(), tl)) for s, tl in self.tabs]))

    def set_for_budget(self, k):
        """(tau, [(p, slot), ...]) for the smallest tau whose total min-# fits k values."""
        lo, hi = 0, len(self.cands) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if sum(e7.min_points(s, tl, self.cands[mid]) for s, tl in self.tabs) <= k:
                hi = mid
            else:
                lo = mid + 1
        tau = float(self.cands[lo])
        vals = [(p, q - 1) for p, (s, tl) in enumerate(self.tabs) for q in min_set(s, tl, tau)]
        return tau, vals

    def worst(self, vals):
        d = [[] for _ in range(self.X.shape[0])]
        for p, i in vals:
            d[p].append(i)
        return e5.score(self.X, self.a, self.t, d)[1]


def messages(vals, copies):
    msgs = [vals[i:i + VPM] for i in range(0, len(vals), VPM)]
    return [m for m in msgs for _ in range(copies)]


def evaluate(sd, msg_list, p, rng, draws=40):
    out = []
    for _ in range(draws):
        got = [v for m in msg_list if rng.random() > p for v in m]
        out.append(sd.worst(list(set(got))))
    out = np.array(out)
    return float((out <= 1).mean()), float(out.mean())


def strategies(sd, Q, s_share=None, r_c=None):
    K = VPM * Q
    res = {}
    _, v = sd.set_for_budget(K)
    res["oblivious"] = messages(v, 1)
    for r in (2, 3):
        _, v = sd.set_for_budget(K // r)
        res[f"repeat_{r}"] = messages(v, r)[:Q]
    if s_share is not None:
        kc = max(1, int(round(s_share * K / r_c)))
        _, vc = sd.set_for_budget(kc)
        kf = K - len(messages(vc, r_c)) * VPM // 1 if False else K - r_c * VPM * int(np.ceil(len(vc) / VPM))
        fine = []
        if kf > 0:
            _, vf = sd.set_for_budget(kf + len(vc))
            fine = [x for x in vf if x not in set(vc)][:kf]
        res["layered"] = (messages(vc, r_c) + messages(fine, 1))[:Q]
    return res


def main():
    Q = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    e5.TOLSET = "usgs"
    days = e5.load_days()
    items = [(d, s) for d, sites in days.items() for s in sites]
    rng = np.random.default_rng(20261023)
    pick = rng.choice(len(items), size=200, replace=False)
    sds = [SiteDay(*days[items[i][0]][items[i][1]]) for i in pick]
    print("prepared", len(sds), flush=True)
    P = (0.1, 0.3, 0.5)
    grid = [(s, r) for s in (0.3, 0.5, 0.7) for r in (2, 3)]
    tune, test = sds[::2], sds[1::2]
    best = {}
    for p in P:  # tune the layered split on the tuning half
        scores = {}
        for s_share, r_c in grid:
            ok = [evaluate(sd, strategies(sd, Q, s_share, r_c)["layered"], p, rng, 15)[0] for sd in tune]
            scores[(s_share, r_c)] = np.mean(ok)
        best[p] = max(scores, key=scores.get)
        print(f"p={p}: tuned layered (share, copies) = {best[p]}", flush=True)
    rows = []
    for j, sd in enumerate(test):
        for p in P:
            for name, ml in strategies(sd, Q, *best[p]).items():
                ok, mw = evaluate(sd, ml, p, rng)
                rows.append({"p": p, "strategy": name, "p_ok": ok, "mean_worst": mw})
        if j % 20 == 0:
            print(j, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(f"results/scoping/e13_oneway_Q{Q}.csv", index=False)
    print(f"\nQ = {Q} messages/day x 19 B, test half ({len(test)} site-days), USGS-Excellent")
    print("Probability the whole day is within tolerance (mean over site-days):")
    print(out.pivot_table(index="p", columns="strategy", values="p_ok").round(3).to_string())
    print("Mean worst error (tolerance units):")
    print(out.pivot_table(index="p", columns="strategy", values="mean_worst").round(2).to_string())


if __name__ == "__main__":
    main()
