"""E11: how many bytes does a site-day NEED to meet the USGS "Excellent" tolerance everywhere?

For every USGS site-day (24 h, all parameters), the exact minimum number of values m that keeps the whole
day's record within tolerance (min-# polygonal approximation at tau = 1; E7's DP), charged 3 B per value
(2 B value + 1 B index). Compared with the TTN fair-use daily budget per spreading factor (E8: full
51-222 B frames; SF7 17,982, SF8 9,990, SF9 5,060, SF10 2,142, SF11 969, SF12 510 B/day).
Reports the distribution of need (median, p90, p99, max), the share of site-days whose need exceeds each
SF budget, and how need clusters in time (do the sites of one chain have their worst days together?).
Run from Paper3/: python -I src/scoping/e11_need_distribution.py [--tol usgs|L2]
"""
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
BUDGET = {7: 17982, 8: 9990, 9: 5060, 10: 2142, 11: 969, 12: 510}


def main():
    e5.TOLSET = sys.argv[sys.argv.index("--tol") + 1] if "--tol" in sys.argv else "usgs"
    days = e5.load_days()
    rows = []
    for c, (d, sites) in enumerate(sorted(days.items())):
        for s, (X, a, t) in sites.items():
            m = sum(e7.min_points(*e7.seg_tables(X[p], a[p], t[p]), 1.0) for p in range(X.shape[0]))
            rows.append({"day": d, "site": s, "n_par": X.shape[0], "n_slots": X.shape[1], "values": int(m),
                         "need_B": 3 * int(m), "full_B": 2 * X.size})
        if c % 30 == 0:
            print(d.date(), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(f"results/scoping/e11_need{e5.suffix()}.csv", index=False)
    # normalise to a 10-min, 4-parameter node (144 slots): need per slot-parameter scaled
    out["need_B_10min4p"] = out.need_B * (144 * 4) / (out.n_slots * out.n_par)
    out["frac_of_full"] = out.need_B / out.full_B
    q = out.need_B_10min4p.quantile([0.5, 0.9, 0.99]).round(0)
    print(f"\n{len(out)} site-days, tolerance set {e5.TOLSET}")
    print("Need to keep the whole day within tolerance, scaled to a 10-min 4-parameter node (B/day):",
          f"median {q[0.5]:.0f}, p90 {q[0.9]:.0f}, p99 {q[0.99]:.0f}, max {out.need_B_10min4p.max():.0f}  (raw full data 1,296 B/day)")
    print("As a fraction of the full backlog: median %.3f, p90 %.3f, p99 %.3f" % tuple(out.frac_of_full.quantile([0.5, 0.9, 0.99])))
    print("Share of site-days whose need exceeds the TTN daily budget:",
          {f"SF{k}": round(float((out.need_B_10min4p > v).mean()), 3) for k, v in BUDGET.items()})
    per_site = out.groupby("site").need_B_10min4p.agg(["median", lambda x: x.quantile(0.99)])
    print("Per-site median need, range over sites: %.0f-%.0f B/day; p99/median within a site, median over sites %.1f"
          % (per_site["median"].min(), per_site["median"].max(), float((per_site.iloc[:, 1] / per_site["median"]).median())))
    # temporal clustering of high-need days within chains
    out["hi"] = out.groupby("site").need_B_10min4p.transform(lambda x: x > x.quantile(0.9))
    for chain, members in e6.CHAINS.items():
        sub = out[out.site.isin(members)]
        piv = sub.pivot_table(index="day", columns="site", values="hi", aggfunc="max").dropna()
        if piv.shape[1] < 2 or len(piv) < 50:
            continue
        both = (piv.sum(axis=1) >= 2).mean()
        exp = 1 - ((1 - 0.1) ** piv.shape[1] + piv.shape[1] * 0.1 * (1 - 0.1) ** (piv.shape[1] - 1))
        print(f"  {chain}: days on which >= 2 sites are in their own top-10% need: {both:.3f} (independent: {exp:.3f})")


if __name__ == "__main__":
    main()
