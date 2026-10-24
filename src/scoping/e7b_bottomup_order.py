"""E7b: can a better NESTED (anytime) order close greedy's gap to the per-budget optimum?

Same 300 site-days as E7 (same seed and sampling). Two nested orders over all (parameter, slot) values:
  greedy   : top-down, largest normalised error first (E5's Node)
  bottomup : start from the full record (error 0) and repeatedly REMOVE the value whose removal gives
             the smallest local worst error (the merged segment between its kept neighbours, or the
             held tail if it is the last kept value); the upload order is the reverse of removal.
             The anchor (value before the window) always stays.
For each order: worst normalised error at budgets 5/10/20 % (3 B per value), compared with E7's exact
optimum (read from results/scoping/e7_greedy_vs_optimal.csv). Also the size of non-monotone steps:
how much the worst error rises when one more value is sent.
Run from Paper3/: python -I src/scoping/e7b_bottomup_order.py
"""
import heapq
import importlib.util
import os

import numpy as np
import pandas as pd

here = os.path.dirname(__file__)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, file))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


e5 = load("e5", "e5_worstcase_pooled.py")


def worst_curve(X, anchors, tols, order, kmax):
    """Worst normalised error after sending the first k values of `order`, k = 0..kmax."""
    P = X.shape[0]
    sel = [[] for _ in range(P)]
    cur = [np.abs(X[p] - e5.reconstruct(X[p], anchors[p], [])) / tols[p] for p in range(P)]
    out = [max(c.max() for c in cur)]
    for p, i in order[:kmax]:
        sel[p].append(i)
        cur[p] = np.abs(X[p] - e5.reconstruct(X[p], anchors[p], sel[p])) / tols[p]
        out.append(max(c.max() for c in cur))
    return np.array(out)


def greedy_order(X, anchors, tols, kmax):
    node = e5.Node(X, anchors, tols)
    order = []
    for _ in range(kmax):
        if node.top() <= 0:
            break
        p, i = np.unravel_index(np.argmax(node.err), node.err.shape)
        order.append((int(p), int(i)))
        node.send_top()
    return order


def bottomup_order(X, anchors, tols):
    """Reverse of greedy removal by smallest local worst error."""
    P, n = X.shape
    order_removed = []
    heap, alive, prv, nxt, cost = [], {}, {}, {}, {}
    for p in range(P):
        xs = np.concatenate(([anchors[p]], X[p]))  # position 0 = anchor, q = slot q-1
        alive[p] = np.ones(n + 1, bool)
        prv[p] = np.arange(-1, n)
        nxt[p] = np.arange(1, n + 2)
        nxt[p][n] = -1  # last has no next
        cost[p] = np.zeros(n + 1)

        def local(q, p=p, xs=xs):
            a, b = prv[p][q], nxt[p][q]
            if b == -1:  # q is the last kept point: removing it holds xs[a] to the end
                seg = xs[a + 1:]
                return float(np.max(np.abs(seg - xs[a])) / tols[p])
            t = np.arange(a + 1, b)
            line = xs[a] + (xs[b] - xs[a]) * (t - a) / (b - a)
            return float(np.max(np.abs(xs[t] - line)) / tols[p])

        prv[p][0] = -1
        cost[p] = local
        for q in range(1, n + 1):
            heapq.heappush(heap, (local(q), p, q, 0))
    version = {(p, q): 0 for p in range(P) for q in range(1, n + 1)}
    while heap:
        c, p, q, v = heapq.heappop(heap)
        if not alive[p][q] or version[(p, q)] != v:
            continue
        alive[p][q] = False
        order_removed.append((p, q - 1))
        a, b = prv[p][q], nxt[p][q]
        if b != -1:
            prv[p][b] = a
        nxt[p][a] = b
        for r in (a, b):
            if r is not None and r > 0 and r != -1 and alive[p][r]:
                version[(p, r)] += 1
                heapq.heappush(heap, (cost[p](r), p, r, version[(p, r)]))
    return order_removed[::-1]


def main():
    e7 = pd.read_csv("results/scoping/e7_greedy_vs_optimal.csv", parse_dates=["day"], dtype={"site": str})
    days = e5.load_days()
    rows, rises = [], []
    for (d, s), g in e7.groupby(["day", "site"]):
        X, a, t = days[d][s]
        kmax = int(g.k.max())
        go = greedy_order(X, a, t, kmax)
        bo = bottomup_order(X, a, t)
        cg, cb = worst_curve(X, a, t, go, kmax), worst_curve(X, a, t, bo, kmax)
        rises.append({"greedy_max_rise": float(np.max(np.diff(cg), initial=0)), "bottomup_max_rise": float(np.max(np.diff(cb), initial=0)),
                      "greedy_nonmono": bool(np.any(np.diff(cg) > 1e-12)), "bottomup_nonmono": bool(np.any(np.diff(cb) > 1e-12))})
        for r in g.itertuples():
            k = int(r.k)
            rows.append({"frac": r.frac, "opt": r.opt, "greedy": float(cg[min(k, len(cg) - 1)]), "bottomup": float(cb[min(k, len(cb) - 1)])})
    out = pd.DataFrame(rows)
    R = pd.DataFrame(rises)
    out.to_csv("results/scoping/e7b_bottomup.csv", index=False)
    summ = out.groupby("frac").agg(opt_med=("opt", "median"), greedy_med=("greedy", "median"), bottomup_med=("bottomup", "median"),
                                   opt_ok=("opt", lambda x: (x <= 1).mean()), greedy_ok=("greedy", lambda x: (x <= 1).mean()),
                                   bottomup_ok=("bottomup", lambda x: (x <= 1).mean()))
    out["r_g"], out["r_b"] = out.greedy / out.opt.clip(lower=1e-9), out.bottomup / out.opt.clip(lower=1e-9)
    summ["greedy/opt_med"] = out.groupby("frac").r_g.median()
    summ["bottomup/opt_med"] = out.groupby("frac").r_b.median()
    summ["bottomup/opt_p90"] = out.groupby("frac").r_b.quantile(0.9)
    print(summ.round(3).to_string())
    print("\nNon-monotone worst-error curves (share of site-days):", R[["greedy_nonmono", "bottomup_nonmono"]].mean().round(3).to_dict())
    print("Largest single-step rise, median over site-days (tolerance units):", R[["greedy_max_rise", "bottomup_max_rise"]].median().round(3).to_dict())


if __name__ == "__main__":
    main()
