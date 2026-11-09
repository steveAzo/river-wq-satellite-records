"""Evaluation of the Step 3 prototype (src/p3/proto_decision.py). Share of day-queries with a certain CORRECT decision,
by design, for event days (truth: exceedance), non-event days, and near-threshold days; site-clustered bootstrap
intervals (sites resampled, days pooled); wrong decisions; per-day best-of-designs hindsight bound.
Run from Paper3/: python -I src/p3/proto_eval.py <tag> <Q> [Q2 ...]   -> docs/PROTO_RESULTS.md table text on stdout
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

B = 1000
LABEL = {"rec/old": "record, span-only rule", "rec/new": "record, cells (no grid)", "rec/grid": "record, cells + grid",
         "flat/new": "flat min/max, no grid", "flat/grid": "flat min/max, grid", "pet2/new": "PET c=2, no grid",
         "pet2/grid": "PET c=2, grid", "pet1/new": "PET c=1, no grid", "pet1/grid": "PET c=1, grid",
         "spare/new": "spare slots, no grid", "spare/grid": "spare slots, grid",
         "spare_adapt/new": "spare slots by margin, no grid", "spare_adapt/grid": "spare slots by margin, grid",
         "best/grid": "best of grid designs (hindsight)"}


def load(tag, Q):
    d = pd.concat([pd.read_csv(f, dtype={"site": str}) for f in glob.glob(f"results/{tag}/proto/*_Q{Q}.csv") if os.path.getsize(f) > 10])
    d["k"] = d.design + "/" + d.rule
    return d


def boot(d, col, rng):
    """Pooled mean over days and site-clustered 95% interval."""
    g = d.groupby("site")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    est = s.sum() / c.sum()
    idx = rng.integers(0, len(g), (B, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def table(d, query, stratum, rng):
    x = d[d["query"] == query]
    if stratum == "event":
        x = x[x.truth]
    elif stratum == "non-event":
        x = x[~x.truth]
    elif stratum == "near":
        x = x[x.near]
    rows = []
    best = x[x.design.isin(["rec", "flat", "pet2", "pet1", "spare", "spare_adapt"]) & (x.rule == "grid")]
    bd = best.groupby(["site", "day", "cond", "Q"]).decided_correct.max().reset_index()
    bd["design"], bd["rule"], bd["k"] = "best", "grid", "best/grid"
    for k, y in list(x.groupby("k")) + [("best/grid", bd)]:
        for cond, z in y.groupby("cond"):
            est, lo, hi = boot(z, "decided_correct", rng)
            rows.append({"design": LABEL[k], "cond": cond, "n_days": z[["site", "day"]].drop_duplicates().shape[0],
                         "decided_correct": f"{est:.3f} ({lo:.3f} to {hi:.3f})"})
    return pd.DataFrame(rows).pivot(index="design", columns="cond", values="decided_correct")


def main():
    tag = sys.argv[1]
    rng = np.random.default_rng(1)
    for Q in map(int, sys.argv[2:]):
        d = load(tag, Q)
        print(f"\n## Q = {Q}: {d.site.nunique()} sites, {d[['site', 'day']].drop_duplicates().shape[0]} days; "
              f"wrong decisions (max over rows): {d.wrong.max():.3f}")
        for q in ("DO", "pH"):
            for st in ("event", "non-event", "near"):
                n = d[(d["query"] == q) & ((d.truth if st == "event" else ~d.truth if st == "non-event" else d.near))]
                nd = n[["site", "day"]].drop_duplicates().shape[0]
                if nd < 30:
                    print(f"\n{q} {st}: {nd} days, skipped (under 30)")
                    continue
                print(f"\n### {q}, {st} days ({nd} days)")
                print(table(d, q, st, rng).to_markdown())


if __name__ == "__main__":
    main()
