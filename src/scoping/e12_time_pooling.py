"""E12: can a node's buffer pool its budget across days on a satellite micro-plan?

Uses E11's exact daily need (bytes to keep the whole day within the USGS-Excellent tolerance, scaled to a
10-min 4-parameter node). A daily queue per site: backlog B(t+1) = max(0, B(t) + need(t) - C). Need is
treated as additive across days (a slight overestimate: a day's optimal set is computed alone).
Budgets C: Kinéis plan tiers at 19 B/message (1, 6, 24 msg/day) plus 12/day. Reports, over sites: share
of days ending with a backlog (record of some past day not yet guaranteed), the longest backlog
duration (days a reading waits to be guaranteed), and the share of sites whose backlog never clears
(long-run need > C: these must relax tau). Run from Paper3/: python -I src/scoping/e12_time_pooling.py
"""
import numpy as np
import pandas as pd

d = pd.read_csv("results/scoping/e11_need_usgs.csv", parse_dates=["day"], dtype={"site": str})
d["need"] = d.need_B * (144 * 4) / (d.n_slots * d.n_par)
plans = {"1 msg/day (19 B)": 19, "6 msg/day (114 B)": 114, "12 msg/day (228 B)": 228, "24 msg/day (456 B)": 456}
print(f"{d.site.nunique()} sites, {len(d)} site-days. Same-day share of days whose need exceeds C (no buffer):")
for name, C in plans.items():
    print(f"  {name:20s}: {(d.need > C).mean():.3f}")
print("\nWith a buffer (backlog carried to later days):")
for name, C in plans.items():
    share, longest, never = [], [], 0
    for s, g in d.sort_values("day").groupby("site"):
        B, run, runs, open_days = 0.0, 0, [0], 0
        for x in g.need.to_numpy():
            B = max(0.0, B + x - C)
            run = run + 1 if B > 0 else 0
            runs.append(run)
            open_days += B > 0
        share.append(open_days / len(g))
        longest.append(max(runs))
        never += g.need.mean() > C
    print(f"  {name:20s}: days with backlog, median over sites {np.median(share):.3f} (p90 {np.percentile(share,90):.3f}); "
          f"longest wait median {np.median(longest):.0f} d (max {max(longest)} d); sites with mean need > C: {never}/{d.site.nunique()}")
