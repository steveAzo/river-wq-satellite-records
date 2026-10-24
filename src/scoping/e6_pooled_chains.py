"""E6: does pooling a budget pay when the pool is a realistic gateway group (2-5 sites on one river)?

E5(b) pooled ~31 sites from five states, which overstates heterogeneity. Here each pool is one real
river chain (sites on the same river, the groups used in Paper 2's chain analysis). Same schemes and
metrics as E5(b): equal_stride, equal_greedy, pooled_greedy, at budget fractions 5/10/20 %.
Reuses E5's functions. Output: results/scoping/e6_pooled_chains.csv. Run from Paper3/:
    python -I src/scoping/e6_pooled_chains.py
"""
import heapq
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("e5", os.path.join(os.path.dirname(__file__), "e5_worstcase_pooled.py"))
e5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e5)

CHAINS = {
    "Delaware": ["01427510", "01438500", "01458500", "01463500"],
    "Illinois": ["05537980", "05543010", "05553700", "05559900", "05586300"],
    "Klamath": ["11509370", "11509500", "11510700"],
    "McKenzie": ["14162500", "14163900"],
    "Tualatin": ["14203500", "14206241", "14206694", "14207200"],
    "Clackamas": ["14209710", "14210000", "14211010"],
}


def main():
    if "--tol" in sys.argv:
        e5.TOLSET = sys.argv[sys.argv.index("--tol") + 1]
    days = e5.load_days()
    rows = []
    for chain, members in CHAINS.items():
        for day, sites in sorted(days.items()):
            names = [s for s in members if s in sites]
            if len(names) < 2:
                continue
            total_full = sum(2 * sites[s][0].size for s in names)
            for f in e5.FRACS:
                F = f * total_full
                res = {
                    "equal_stride": [e5.score(*sites[s], e5.stride_nf_delivered(sites[s][0].shape[1], sites[s][0].shape[0], F / len(names))) for s in names],
                    "equal_greedy": [e5.score(*sites[s], e5.greedy_delivered(*sites[s], F / len(names))) for s in names],
                }
                nodes = {s: e5.Node(*sites[s]) for s in names}
                heap = [(-nodes[s].top(), s) for s in names]
                heapq.heapify(heap)
                for _ in range(int(F // 3)):
                    negv, s = heapq.heappop(heap)
                    if -negv <= 0:
                        break
                    nodes[s].send_top()
                    heapq.heappush(heap, (-nodes[s].top(), s))
                res["pooled_greedy"] = [e5.score(*sites[s], nodes[s].sel) for s in names]
                for name, sc in res.items():
                    rows.append({"chain": chain, "day": day, "frac": f, "scheme": name, "n_sites": len(names),
                                 "within": float(np.mean([w for w, _ in sc])),
                                 "days_ok": float(np.mean([m <= 1 for _, m in sc])),
                                 "pool_max": float(np.max([m for _, m in sc]))})
        print(chain, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(f"results/scoping/e6_pooled_chains{e5.suffix()}.csv", index=False)
    print("\nMeans over chain-days (all chains):")
    print(out.groupby(["frac", "scheme"])[["within", "days_ok", "pool_max"]].mean().round(3).unstack("scheme").to_string())
    print("\nMedian pool max error (tolerance units) per chain at 10 %:")
    t = out[out.frac == 0.1].groupby(["chain", "scheme"]).pool_max.median().unstack().round(2)
    t["n_days"] = out[(out.frac == 0.1) & (out.scheme == "pooled_greedy")].groupby("chain").size()
    print(t.to_string())
    print("\nShare of chain-days where the pool's worst value is within tolerance, at 10 % / 20 %:")
    for f in (0.1, 0.2):
        print(f, out[out.frac == f].assign(ok=lambda d: d.pool_max <= 1).groupby("scheme").ok.mean().round(3).to_dict())


if __name__ == "__main__":
    main()
