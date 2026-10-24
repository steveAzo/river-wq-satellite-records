"""Confirmatory RQ2/RQ4 run: frozen K (dev_tuning.json) and frozen safety factor (sizing_tuning.json),
applied to every site of a confirmation need file. Reuses pooling.py unchanged.
Output: results/confirm/<tag>_pooling.csv and <tag>_sizing.csv.
Run from Paper3/: python -I src/p3/confirm_pooling.py <need_csv> <tag>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import pooling as pl  # noqa: E402


def main():
    need_csv, tag = sys.argv[1], sys.argv[2]
    df = pd.read_csv(need_csv, dtype={"site": str})
    tuning = json.load(open("results/dev/dev_tuning.json"))
    s = json.load(open("results/dev/sizing_tuning.json"))["safety_factor"]
    rng = np.random.default_rng(pl.SEED)
    sites = sorted(df.site.unique())
    rows = []
    for site in sites:
        needs = pl.site_series(df, site)
        for Q in pl.TIERS:
            for loss in ("iid", "gilbert"):
                for p in (0.1, 0.3, 0.5):
                    K = pl.K_for(Q, loss, p, tuning)
                    g7 = np.mean([[x[0] for x in pl.simulate(needs, Q, K, loss, p, rng)] for _ in range(5)])
                    rows.append({"site": site, "Q": Q, "K": K, "loss": loss, "p": p, "G7": g7})
    out = pd.DataFrame(rows)
    os.makedirs("results/confirm", exist_ok=True)
    out.to_csv(f"results/confirm/{tag}_pooling.csv", index=False)
    K_of = {Q: pl.K_for(Q, "iid", 0.3, tuning) for Q in pl.TIERS}

    def tier_from(needs, scale):
        for Q in pl.TIERS:
            if pl.share_within(needs, Q, K_of[Q], "iid", 0.3, rng, scale) >= 0.9:
                return Q
        return pl.TIERS[-1]
    sz = []
    for site in sites:
        needs = pl.site_series(df, site)
        sz.append({"site": site, "pilot_tier": tier_from(needs[:28], s), "hindsight_tier": tier_from(needs[28:], 1.0)})
    sz = pd.DataFrame(sz)
    sz.to_csv(f"results/confirm/{tag}_sizing.csv", index=False)
    ti = {q: i for i, q in enumerate(pl.TIERS)}
    sz["d"] = sz.pilot_tier.map(ti) - sz.hindsight_tier.map(ti)
    print(f"{tag}: {len(sites)} sites")
    for loss, Q in (("iid", 6), ("gilbert", 12), ("gilbert", 6)):
        g = out[(out.loss == loss) & (out.p == 0.3) & (out.Q == Q)]
        print(f"  share of sites with G7 >= 0.9, {loss} p=0.3, Q={Q}: {(g.G7 >= 0.9).mean():.3f} ({(g.G7 >= 0.9).sum()}/{len(g)})")
    print(f"  RQ4 (s = {s}): sufficient {(sz.d >= 0).mean():.3f}; over-provision <= 1 tier {(sz.d <= 1).mean():.3f}")


if __name__ == "__main__":
    main()
