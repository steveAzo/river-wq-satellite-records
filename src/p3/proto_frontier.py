"""Step 3 prototype: the trade-off between the record guarantee and decisive-correct threshold decisions.
For each design: probability that the whole record is recovered (record side) and the share of day-queries with a
certain, correct decision on (a) all days and (b) hard days (event or near-threshold), both queries pooled; site-
clustered 95% intervals (sites resampled, days pooled). Record side: for designs of results/<tag>/proto/ from
proto_record_Q<Q>.csv (its own loss draws); for results/<tag>/proto_adapt/ from the rec_full column (same draws as the
decisions). Run from Paper3/: python -I src/p3/proto_frontier.py <tag> <Q> [Q2 ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

B = 1000
NAMES = {"rec": "record only", "flat": "flat min/max", "pet1": "PET c=1", "pet2": "PET c=2",
         "spare": "spare slots", "spare_adapt": "spare slots by margin", "adapt": "decision-aware (hard days layered)",
         "randmix": "control: same layering on random days"}


def read(pattern):
    return pd.concat([pd.read_csv(f, dtype={"site": str}) for f in glob.glob(pattern) if os.path.getsize(f) > 10])


def ci(z, col, rng):
    g = z.groupby("site")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), (B, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return f"{s.sum() / c.sum():.3f} ({np.percentile(bs, 2.5):.3f} to {np.percentile(bs, 97.5):.3f})"


def per_site(dec, rec, cond, dn):
    """Per-site pooled means: record recovery, decisive-correct on hard days, on all days."""
    z = dec[(dec.cond == cond) & (dec.design == dn)]
    if dn in ("adapt", "randmix"):
        zr = z.drop_duplicates(["site", "day"]).groupby("site").rec_full.mean()
    else:
        zr = rec[(rec.cond == cond) & (rec.design == dn)].groupby("site").rec_full.mean()
    return pd.DataFrame({"rec": zr, "hard": z[z.hard].groupby("site").decided_correct.mean(),
                         "all": z.groupby("site").decided_correct.mean()})


def contrast(dec, rec, cond, x, y, rng):
    a, b = per_site(dec, rec, cond, x), per_site(dec, rec, cond, y)
    d = (a - b).dropna()
    out = []
    for col, name in (("rec", "record"), ("hard", "hard-day decisive"), ("all", "all-day decisive")):
        v = d[col].to_numpy()
        bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
        out.append(f"{name} {v.mean():+.3f} ({np.percentile(bs, 2.5):+.3f} to {np.percentile(bs, 97.5):+.3f})")
    return "; ".join(out)


def main():
    tag = sys.argv[1]
    rng = np.random.default_rng(3)
    for Q in map(int, sys.argv[2:]):
        a = read(f"results/{tag}/proto/*_Q{Q}.csv")
        a = a[a.rule == "grid"]
        b = pd.concat([read(f"results/{tag}/proto_adapt/*_Q{Q}.csv"), read(f"results/{tag}/proto_randmix/*_Q{Q}.csv")])
        dec = pd.concat([a, b])
        dec["hard"] = dec.truth | dec.near
        rec = read(f"results/{tag}/proto_record_Q{Q}.csv") if os.path.exists(f"results/{tag}/proto_record_Q{Q}.csv") else None
        print(f"\n## Q = {Q}: {dec.site.nunique()} sites; wrong decisions max {dec.wrong.max():.3f}")
        for cond in ("iid_p0.3", "gilbert_p0.3_b3"):
            rows = []
            for dn in NAMES:
                z = dec[(dec.cond == cond) & (dec.design == dn)]
                if z.empty:
                    continue
                if dn in ("adapt", "randmix"):
                    zr = z.drop_duplicates(["site", "day"])
                    rf = ci(zr, "rec_full", rng)
                else:
                    zr = rec[(rec.cond == cond) & (rec.design == dn)]
                    rf = ci(zr, "rec_full", rng)
                rows.append({"design": NAMES[dn], "record recovered": rf,
                             "decisive-correct, all days": ci(z, "decided_correct", rng),
                             "decisive-correct, hard days": ci(z[z.hard], "decided_correct", rng),
                             "hard day-queries": int(z.hard.sum() / 1)})
            print(f"\n### {cond}\n" + pd.DataFrame(rows).to_markdown(index=False))
            print(f"\nPaired differences, {cond}, Q = {Q} (sites resampled, 95% interval):")
            for x, y in (("adapt", "randmix"), ("adapt", "pet1"), ("adapt", "flat"), ("adapt", "rec"),
                         ("adapt", "spare_adapt")):
                print(f"  {x} minus {y}: " + contrast(dec, rec, cond, x, y, rng))


if __name__ == "__main__":
    main()
