"""E7c: exact pooled min-max optimum ("common-tau min-#") vs the nested water-level greedy, on chain pools.

For a pool of N sites (one river chain, one day) sharing K values (budget fraction f of the pool's full
backlog, 3 B per value):
  pooled_opt   : smallest tau such that sum_n m_n(tau) <= K, where m_n(tau) = fewest values that keep
                 site n's whole record within tau x tolerance (min-# polygonal approximation, exact DP from
                 E7). Because each site's optimum curve is non-increasing, this IS the pooled min-max
                 optimum; every site sends its min-# set at the common tau.
  equal_opt    : each site gets K/N values and sends its own optimal set (exact).
  pooled_greedy: E6's nested water-level greedy.
Metric: the pool's worst normalised error and whether it is <= 1 (whole pool within tolerance).
Random sample of chain-days (seed 20261016). Run from Paper3/:
    python -I src/scoping/e7c_pooled_optimal.py [n_chain_days=60]
"""
import heapq
import importlib.util
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


e5, e6, e7 = load("e5", "e5_worstcase_pooled.py"), load("e6", "e6_pooled_chains.py"), load("e7", "e7_greedy_vs_optimal.py")


def site_tables(X, a, t):
    return [e7.seg_tables(X[p], a[p], t[p]) for p in range(X.shape[0])]


def m_site(tabs, tau):
    return sum(e7.min_points(s, tl, tau) for s, tl in tabs)


def best_tau(tab_list, K):
    cands = np.unique(np.concatenate([np.concatenate((s.ravel(), tl)) for tabs in tab_list for s, tl in tabs]))
    lo, hi = 0, len(cands) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(m_site(tabs, cands[mid]) for tabs in tab_list) <= K:
            hi = mid
        else:
            lo = mid + 1
    return float(cands[lo])


def main():
    if "--tol" in sys.argv:
        e5.TOLSET = sys.argv[sys.argv.index("--tol") + 1]
    n_cd = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 60
    days = e5.load_days()
    pools = [(c, d, [s for s in m if s in days[d]]) for c, m in e6.CHAINS.items() for d in days]
    pools = [p for p in pools if len(p[2]) >= 2]
    rng = np.random.default_rng(20261016)
    pick = rng.choice(len(pools), size=min(n_cd, len(pools)), replace=False)
    rows = []
    for c_i, idx in enumerate(pick):
        chain, d, names = pools[idx]
        sites = days[d]
        tabs = {s: site_tables(*sites[s]) for s in names}
        total_vals = sum(sites[s][0].size for s in names)
        for f in (0.1, 0.2):
            K = int(f * total_vals * 2 // 3)
            tau = best_tau([tabs[s] for s in names], K)
            eq = max(e7.optimum(*sites[s], K // len(names)) for s in names)
            nodes = {s: e5.Node(*sites[s]) for s in names}
            heap = [(-nodes[s].top(), s) for s in names]
            heapq.heapify(heap)
            for _ in range(K):
                negv, s = heapq.heappop(heap)
                if -negv <= 0:
                    break
                nodes[s].send_top()
                heapq.heappush(heap, (-nodes[s].top(), s))
            pg = max(e5.score(*sites[s], nodes[s].sel)[1] for s in names)
            rows.append({"chain": chain, "day": d, "n": len(names), "frac": f, "pooled_opt": tau, "equal_opt": eq, "pooled_greedy": pg})
        if c_i % 10 == 0:
            print(c_i, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(f"results/scoping/e7c_pooled_optimal{e5.suffix()}.csv", index=False)
    for f, g in out.groupby("frac"):
        print(f"\nf = {f}: {len(g)} chain-days")
        for col in ("pooled_opt", "equal_opt", "pooled_greedy"):
            print(f"  {col:13s} pool worst error median {g[col].median():.2f} | whole pool within tolerance {(g[col] <= 1).mean():.2f}")
        print(f"  pooled_greedy / pooled_opt median {np.median(g.pooled_greedy / g.pooled_opt.clip(lower=1e-9)):.2f}")


if __name__ == "__main__":
    main()
