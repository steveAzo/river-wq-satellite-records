"""Site-clustered bootstrap intervals for the headline statistics (exploratory; after confirmation).

Site-days of one site are not independent, so sites are resampled with replacement (B = 2000) and every
statistic is recomputed on the resampled site-days. Reports 95% percentile intervals for:
  the median daily need (bytes) on USGS 2024;
  mean G per design at 6 messages/day, p = 0.3, independent and bursty loss;
  the H3 ratio (median G, code / reliable-link design) and the H4 difference (median G, code - tag practice).
Output: results/sens/bootstrap.json
Run from Paper3/: python -I src/p3/bootstrap.py
"""
import json
import os

import numpy as np
import pandas as pd

B, SEED = 2000, 20261024
rng = np.random.default_rng(SEED)
need = pd.read_csv("results/confirm/need_excellent.csv", dtype={"site": str})
need["bytes"] = 3 * need["values"]
rq3 = pd.read_csv("results/confirm/usgs2024_rq3.csv", dtype={"site": str})
q6 = rq3[(rq3.Q == 6) & (rq3.p == 0.3)]
sites = sorted(need.site.unique())
need_by = {s: need.bytes[need.site == s].to_numpy() for s in sites}
g_by = {(s, l, d): q6[(q6.site == s) & (q6.loss == l) & (q6.design == d)].G.to_numpy()
        for s in sites for l in ("iid", "gilbert") for d in q6.design.unique()}
designs = sorted(q6.design.unique())


def stats(pick):
    out = {"need_median": float(np.median(np.concatenate([need_by[s] for s in pick])))}
    for l in ("iid", "gilbert"):
        cat = {d: np.concatenate([g_by[(s, l, d)] for s in pick]) for d in designs}
        for d in designs:
            out[f"G_{l}_{d}"] = float(cat[d].mean())
        if l == "iid":
            out["H3_ratio"] = float(np.median(cat["mds"]) / max(np.median(cat["reliable_opt"]), 1e-9))
            out["H4_diff"] = float(np.median(cat["mds"]) - np.median(cat["srdl_style"]))
            out["code_minus_repeat"] = float(cat["mds"].mean() - cat["repeat"].mean())
    return out


point = stats(sites)
reps = [stats(list(rng.choice(sites, len(sites), replace=True))) for _ in range(B)]
res = {k: {"point": point[k], "lo": float(np.percentile([r[k] for r in reps], 2.5)),
           "hi": float(np.percentile([r[k] for r in reps], 97.5))} for k in point}
os.makedirs("results/sens", exist_ok=True)
json.dump(res, open("results/sens/bootstrap.json", "w"), indent=1)
for k, v in res.items():
    print(f"{k:28s} {v['point']:.3f}  [{v['lo']:.3f}, {v['hi']:.3f}]")
