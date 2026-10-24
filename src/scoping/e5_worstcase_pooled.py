"""E5: where does data-awareness pay?  (a) worst case within a node; (b) sharing a budget across nodes.

(a) Same setting as E2 (24 h backlog, byte budget f of the full backlog). For the strongest data-blind
    order (stride_nf: newest slot first, then bit-reversed stride; 2 B/value) and data-aware greedy
    (3 B/value), report per day: the maximum tolerance-normalised error over all values (the record's
    worst case) and whether the whole day's record is within tolerance (max error <= 1).
(b) A pooled budget: on each day, N sites share one total byte budget F (as in one satellite pass or a
    pooled data plan). Compare
      equal_stride : every site gets F/N bytes, stride_nf order       (data-blind, fair share)
      equal_greedy : every site gets F/N bytes, greedy order          (data-aware within node)
      pooled_greedy: one greedy over all sites' values, F bytes total (data-aware across nodes)
    Metric: share of all values within tolerance, and share of site-days fully within tolerance.
Uses USGS sites only (2023). Output: results/scoping/e5_*.csv. Run from Paper3/:
    python -I src/scoping/e5_worstcase_pooled.py
"""
import glob
import heapq
import os

import numpy as np
import pandas as pd

TOL = {"T": 0.2, "DO": 2.0, "pH": 0.1}
PARAMS = ["T", "DO", "pH", "EC"]
# Tolerance set. "L2": the levels used in the first scoping runs (T 0.2 degC, DO 2 %sat, pH 0.1, EC 2 %).
# "usgs": USGS TM 1-D3 (Wagner et al. 2006) Table 18 "Excellent" accuracy rating: T 0.2 degC, SC 3 %,
# DO 0.3 mg/L or 5 % whichever is greater (scoping simplification: 5 % of the site median, floor 0.3 mg/L),
# pH 0.2 units. Callers set e5.TOLSET before load_days(); SUFFIX is appended to output file names.
TOLSET = "L2"


def suffix():
    return "" if TOLSET == "L2" else f"_{TOLSET}"


def tols_for(df, params):
    if TOLSET == "usgs":
        table = {"T": 0.2, "pH": 0.2, "EC": 0.03 * np.nanmedian(df["EC"]) if "EC" in df else np.nan,
                 "DO": max(0.3, 0.05 * np.nanmedian(df["DO"])) if "DO" in df else np.nan}
        return np.array([table[p] for p in params])
    return np.array([TOL.get(p, 0.02 * np.nanmedian(df[p])) for p in params])
FRACS = [0.05, 0.1, 0.2]


def reconstruct(x, anchor, idx):
    n = len(x)
    if len(idx) == 0:
        return np.full(n, anchor)
    idx = np.sort(np.asarray(idx))
    return np.interp(np.arange(n), np.concatenate(([-1], idx)), np.concatenate(([anchor], x[idx])))


def bitrev_order(n):
    bits = max(1, int(np.ceil(np.log2(n))))
    return list(np.argsort([int(format(i, f"0{bits}b")[::-1], 2) for i in range(n)], kind="stable"))


class Node:
    """One site-day: values X (P x n), anchors, tolerances; keeps the server's picture under greedy."""

    def __init__(self, X, anchors, tols):
        self.X, self.a, self.t = X, anchors, tols
        self.sel = [[] for _ in range(X.shape[0])]
        self.err = np.stack([np.abs(X[p] - reconstruct(X[p], anchors[p], [])) / tols[p] for p in range(X.shape[0])])

    def top(self):
        return float(self.err.max())

    def send_top(self):
        p, i = np.unravel_index(np.argmax(self.err), self.err.shape)
        self.sel[p].append(i)
        self.err[p] = np.abs(self.X[p] - reconstruct(self.X[p], self.a[p], self.sel[p])) / self.t[p]
        self.err[p, self.sel[p]] = 0.0


def score(X, anchors, tols, delivered):
    e = np.stack([np.abs(X[p] - reconstruct(X[p], anchors[p], delivered[p])) / tols[p] for p in range(X.shape[0])])
    return float((e <= 1).mean()), float(e.max())


def stride_nf_delivered(n, P, nbytes):
    br = bitrev_order(n)
    order = [n - 1] + [i for i in br if i != n - 1]
    k = int(nbytes // 2)
    d = [[] for _ in range(P)]
    for j in range(min(k, n * P)):
        d[j % P].append(order[j // P])
    return d


def greedy_delivered(X, anchors, tols, nbytes):
    node = Node(X, anchors, tols)
    for _ in range(int(nbytes // 3)):
        if node.top() <= 0:
            break
        node.send_top()
    return node.sel


def load_days():
    days = {}
    for f in sorted(glob.glob("data/clean/usgs/*.csv")):
        site = os.path.basename(f)[:-4]
        df = pd.read_csv(f, parse_dates=["t"])
        if TOLSET == "usgs":
            df["DO"] = df["DO_mgL"]  # USGS rating is defined in mg/L
        step = int(round(df["t"].diff().dt.total_seconds().median() / 60))
        params = [p for p in PARAMS if p in df and df[p].notna().mean() > 0.5]
        tols = tols_for(df, params)
        g = df.set_index("t")[params].resample(f"{step}min").mean().interpolate(limit=2, limit_area="inside")
        n = int(24 * 60 / step)
        for start in range(1, len(g) - n, n):
            day = g.index[start].floor("D")
            win, prev = g.iloc[start:start + n].to_numpy(float).T, g.iloc[start - 1].to_numpy(float)
            if np.isnan(win).any() or np.isnan(prev).any():
                continue
            days.setdefault(day, {})[site] = (win, prev, tols)
    return days


def main():
    global TOLSET
    import sys
    if "--tol" in sys.argv:
        TOLSET = sys.argv[sys.argv.index("--tol") + 1]
    days = load_days()
    rows_a, rows_b = [], []
    for day, sites in sorted(days.items()):
        # (a) per node
        for site, (X, a, t) in sites.items():
            full = 2 * X.size
            for f in FRACS:
                for name, d in (("stride_nf", stride_nf_delivered(X.shape[1], X.shape[0], f * full)),
                                ("greedy", greedy_delivered(X, a, t, f * full))):
                    w, m = score(X, a, t, d)
                    rows_a.append({"day": day, "site": site, "frac": f, "order": name, "within": w, "maxerr": m})
        # (b) pooled across the sites present that day
        if len(sites) < 20:
            continue
        names = list(sites)
        total_full = sum(2 * sites[s][0].size for s in names)
        for f in FRACS:
            F = f * total_full
            res = {}
            res["equal_stride"] = [score(*sites[s], stride_nf_delivered(sites[s][0].shape[1], sites[s][0].shape[0], F / len(names))) for s in names]
            res["equal_greedy"] = [score(*sites[s], greedy_delivered(*sites[s], F / len(names))) for s in names]
            nodes = {s: Node(*sites[s]) for s in names}
            heap = [(-nodes[s].top(), s) for s in names]
            heapq.heapify(heap)
            for _ in range(int(F // 3)):
                negv, s = heapq.heappop(heap)
                if -negv <= 0:
                    break
                nodes[s].send_top()
                heapq.heappush(heap, (-nodes[s].top(), s))
            res["pooled_greedy"] = [score(*sites[s], nodes[s].sel) for s in names]
            for name, sc in res.items():
                rows_b.append({"day": day, "frac": f, "scheme": name, "n_sites": len(names),
                               "within": float(np.mean([w for w, _ in sc])),
                               "days_ok": float(np.mean([m <= 1 for _, m in sc])),
                               "worst_max": float(np.max([m for _, m in sc]))})
        print(day.date(), len(sites), flush=True) if day.day == 1 else None
    A, B = pd.DataFrame(rows_a), pd.DataFrame(rows_b)
    os.makedirs("results/scoping", exist_ok=True)
    A.to_csv(f"results/scoping/e5a_worstcase{suffix()}.csv", index=False)
    B.to_csv(f"results/scoping/e5b_pooled{suffix()}.csv", index=False)
    ps = A.groupby(["site", "frac", "order"]).agg(within=("within", "mean"), ok=("maxerr", lambda m: (m <= 1).mean()),
                                                  maxerr_med=("maxerr", "median")).reset_index()
    print("\n(a) median over sites: share of site-days whose WHOLE record is within tolerance | median daily max error")
    print(ps.pivot_table(index="frac", columns="order", values="ok", aggfunc="median").round(3).to_string())
    print(ps.pivot_table(index="frac", columns="order", values="maxerr_med", aggfunc="median").round(2).to_string())
    print(f"\n(b) pooled budget, {B.day.nunique()} days with >= 20 sites (median sites/day {B.n_sites.median():.0f}); means over days")
    print(B.groupby(["frac", "scheme"])[["within", "days_ok", "worst_max"]].mean().round(3).unstack("scheme").to_string())


if __name__ == "__main__":
    main()
