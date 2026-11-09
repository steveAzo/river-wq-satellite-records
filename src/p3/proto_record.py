"""Step 3 prototype, record side: probability that the day's whole record is recovered (and hence fully certified) under
each prototype design, from the cached 2023 plans only (no data loading). Same group model as proto_decision.py.
Outputs results/<tag>/proto_record_Q<Q>.csv (one row per site-day, condition, design) and prints pooled means with
site-clustered intervals. Run from Paper3/: python -I src/p3/proto_record.py <tag> <Q> [draws=4000]
"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import proto_decision as pdx  # noqa: E402
from p3 import run_robust as rr  # noqa: E402

CONDS = [("iid_p0.3", ("iid", 0.3, 0)), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3))]
WIT = {n: None for n in ("DOmin", "pHmin", "pHmax")}
B = 1000


def main():
    tag, Q = sys.argv[1], int(sys.argv[2])
    draws = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
    rng = np.random.default_rng(20261103)
    masks = {c: rr.sim_masks(spec, Q, rng, draws=draws) for c, spec in CONDS}
    rows = []
    for f in sorted(glob.glob(f"results/{tag}/plans/*.pkl")):
        site = os.path.basename(f)[:-4]
        P = pickle.load(open(f, "rb"))
        cache = {}
        for d, rec in P.items():
            vals, bound = rec["plan"]
            if not bound:
                continue
            n = len(vals)
            for dn in pdx.DESIGNS:
                key = (dn, n)
                if key not in cache:
                    groups = pdx.design_groups(dn, WIT, vals)
                    out = {}
                    for c, M in masks.items():
                        full = 0
                        for mask in M:
                            got = {it for items, cc in groups for it in pdx.group_recover(items, cc, mask)}
                            full += all(("R", p) in got for p in range(n))
                        out[c] = full / len(M)
                    cache[key] = out
                for c in masks:
                    rows.append({"site": site, "day": d, "cond": c, "design": dn, "Q": Q, "rec_full": cache[key][c]})
    df = pd.DataFrame(rows)
    df.to_csv(f"results/{tag}/proto_record_Q{Q}.csv", index=False)
    rng2 = np.random.default_rng(2)
    print(f"Q = {Q}: {df.site.nunique()} sites, {df[['site', 'day']].drop_duplicates().shape[0]} days")
    for (c, dn), z in df.groupby(["cond", "design"]):
        g = z.groupby("site").rec_full.agg(["sum", "count"])
        s, k = g["sum"].to_numpy(), g["count"].to_numpy()
        idx = rng2.integers(0, len(g), (B, len(g)))
        bs = s[idx].sum(1) / k[idx].sum(1)
        print(f"{c:18s} {dn:5s} record fully recovered {s.sum() / k.sum():.3f} "
              f"({np.percentile(bs, 2.5):.3f} to {np.percentile(bs, 97.5):.3f})")


if __name__ == "__main__":
    main()
