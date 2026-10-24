"""E2: does the ORDER in which a node uploads a buffered backlog matter when capacity is short?

Setting: a node holds a W-hour backlog of every parameter (e.g. after an outage, or between satellite
passes) and the link delivers only a byte budget B, a fraction f of the full backlog. Whatever
arrives, the server reconstructs (truth: gaps of <= 2 slots are bridged linearly; longer gaps drop the window) each parameter by linear interpolation between delivered values,
anchored at the (known) value just before the window, and holds the last delivered value to the end.

Orderings compared (each a nested sequence, so any prefix is what a truncated upload delivers):
  fifo     oldest slot first, all parameters of a slot together (2 B per value, index implicit)
  lifo     newest slot first (Paper 2's newest-first)                 (2 B per value)
  stride   bit-reversed slot order: a data-blind progressive order    (2 B per value)
  class    proposal 3: DO, then pH, then EC, then T, each in stride order (2 B per value + 1 B tag per run)
  greedy   data-aware: repeatedly send the value with the largest server error divided by its tolerance
           (the node knows the server's reconstruction exactly)       (3 B per value: 2 B value + 1 B index)

Metric: share of all (slot, parameter) values that the server holds within the Paper 1 L2 tolerance,
and the mean tolerance-normalised absolute error, per budget fraction.
Outputs results/scoping/e2_upload_order.csv. Run from Paper3/:
    python -I src/scoping/e2_upload_order.py [window_hours=24]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

TOL = {"T": 0.2, "DO": 2.0, "pH": 0.1}
PARAMS = ["T", "DO", "pH", "EC"]
FRACS = [0.05, 0.1, 0.2, 0.3, 0.5]


def reconstruct(x, anchor, idx):
    """Server picture of one parameter given delivered slot indices idx (any order)."""
    n = len(x)
    if len(idx) == 0:
        return np.full(n, anchor)
    idx = np.sort(np.asarray(idx))
    xp = np.concatenate(([-1], idx))
    fp = np.concatenate(([anchor], x[idx]))
    out = np.interp(np.arange(n), xp, fp)  # holds fp[-1] after the last delivered slot
    return out


def bitrev_order(n):
    bits = max(1, int(np.ceil(np.log2(n))))
    keys = [int(format(i, f"0{bits}b")[::-1], 2) for i in range(n)]
    return list(np.argsort(keys, kind="stable"))


def greedy_order(X, anchors, tols, max_items):
    """Data-aware nested order of (param, slot) pairs: largest normalised error first."""
    P, n = X.shape
    sel = [[] for _ in range(P)]
    rec = np.stack([reconstruct(X[p], anchors[p], []) for p in range(P)])
    err = np.abs(X - rec) / tols[:, None]
    order = []
    for _ in range(max_items):
        p, i = np.unravel_index(np.argmax(err), err.shape)
        if err[p, i] <= 0:
            break
        order.append((p, i))
        sel[p].append(i)
        rec[p] = reconstruct(X[p], anchors[p], sel[p])
        err[p] = np.abs(X[p] - rec[p]) / tols[p]
        err[p, sel[p]] = -1.0  # already delivered
    return order


def evaluate(X, anchors, tols, delivered):
    P, n = X.shape
    within, nerr, last = [], [], []
    for p in range(P):
        rec = reconstruct(X[p], anchors[p], delivered[p])
        e = np.abs(X[p] - rec) / tols[p]
        within.append(e <= 1.0)
        nerr.append(e)
        last.append(e[-1])  # status: the server's view of the CURRENT (newest) value
    last = np.array(last)
    return np.mean(within), np.mean(nerr), np.mean(last <= 1.0), np.mean(last)


def run_window(X, anchors, tols):
    P, n = X.shape
    full_bytes = 2 * P * n
    res = []
    br = bitrev_order(n)
    slot_orders = {"fifo": list(range(n)), "lifo": list(range(n))[::-1], "stride": br,
                   # strongest data-blind baseline: newest slot first (status), then the progressive order
                   "stride_nf": [n - 1] + [i for i in br if i != n - 1]}
    g = greedy_order(X, anchors, tols, int(max(FRACS) * full_bytes / 3) + 1)
    class_rank = [PARAMS_PRESENT.index(q) for q in ["DO", "pH", "EC", "T"] if q in PARAMS_PRESENT]
    for f in FRACS:
        budget = f * full_bytes
        out = {}
        for name, so in slot_orders.items():
            k = int(budget // 2)  # values that fit
            delivered = [[] for _ in range(P)]
            for j in range(k):
                s, p = so[j // P], j % P
                delivered[p].append(s)
            out[name] = evaluate(X, anchors, tols, delivered)
        # class priority: whole parameters in rank order, each in stride order; 1 B tag per parameter run
        delivered, left = [[] for _ in range(P)], budget
        for p in class_rank:
            left -= 1
            take = int(max(0, left) // 2)
            take = min(take, n)
            delivered[p] = slot_orders["stride_nf"][:take]  # class baseline gets the newest-first fix too
            left -= 2 * take
        out["class"] = evaluate(X, anchors, tols, delivered)
        k = int(budget // 3)
        delivered = [[] for _ in range(P)]
        for p, i in g[:k]:
            delivered[p].append(i)
        out["greedy"] = evaluate(X, anchors, tols, delivered)
        for name, (w, e, sw, se) in out.items():
            res.append({"frac": f, "order": name, "within": w, "nerr": e, "status_within": sw, "status_nerr": se})
    return res


PARAMS_PRESENT = []


def run_site(name, df, step_min, W):
    global PARAMS_PRESENT
    params = [p for p in PARAMS if p in df and df[p].notna().mean() > 0.5]
    PARAMS_PRESENT = params
    tols = np.array([TOL.get(p, 0.02 * np.nanmedian(df[p])) for p in params])
    df = df.set_index("t")[params]
    grid = df.resample(f"{step_min}min").mean().interpolate(limit=2, limit_area="inside")  # scoping: bridge gaps of <= 2 slots
    n = int(W * 60 / step_min)
    rows = []
    for start in range(1, len(grid) - n, n):
        win = grid.iloc[start:start + n].to_numpy(float).T
        prev = grid.iloc[start - 1].to_numpy(float)
        if np.isnan(win).any() or np.isnan(prev).any():
            continue
        for r in run_window(win, prev, tols):
            rows.append(dict(r, site=name, start=str(grid.index[start])))
    return rows


def main():
    W = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
    rows = []
    for f in sorted(glob.glob("data/clean/usgs/*.csv")):
        df = pd.read_csv(f, parse_dates=["t"])
        step = int(round(df["t"].diff().dt.total_seconds().median() / 60))
        rows += run_site(os.path.basename(f)[:-4], df, step, W)
        print(os.path.basename(f), step, "min", len(rows), flush=True)
    inws = pd.read_csv("data/clean/inws_cycles.csv", parse_dates=["t"])
    rows += run_site("InWaterSense", inws[inws.node == 1][["t"] + PARAMS], 10, W)
    out = pd.DataFrame(rows)
    os.makedirs("results/scoping", exist_ok=True)
    out.to_csv(f"results/scoping/e2_upload_order_W{int(W)}.csv", index=False)
    per_site = out.groupby(["site", "frac", "order"])[["within", "nerr", "status_within", "status_nerr"]].mean().reset_index()
    usgs = per_site[per_site.site != "InWaterSense"]
    print(f"\nWindow {W} h. Median over USGS sites of the share of values within L2 tolerance:")
    print(usgs.pivot_table(index="frac", columns="order", values="within", aggfunc="median").round(3).to_string())
    print("\nMedian over USGS sites of mean normalised error:")
    print(usgs.pivot_table(index="frac", columns="order", values="nerr", aggfunc="median").round(2).to_string())
    print("\nInWaterSense, within tolerance:")
    print(per_site[per_site.site == "InWaterSense"].pivot_table(index="frac", columns="order", values="within").round(3).to_string())
    best_other = usgs[usgs.order != "greedy"].groupby(["site", "frac"]).within.max()
    gr = usgs[usgs.order == "greedy"].set_index(["site", "frac"]).within
    print("\nShare of USGS sites where greedy beats every other order (within):",
          (gr > best_other).groupby(level="frac").mean().round(2).to_dict())


if __name__ == "__main__":
    main()
