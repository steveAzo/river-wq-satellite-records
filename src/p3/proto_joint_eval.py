"""Evaluation of Step 3c (src/p3/proto_joint.py). Per design: record recovered, decisive-correct share on hard cases for each
query and pooled over the four queries, and on all cases; paired site-clustered contrasts; the pre-registered criterion
(docs/REVISION2_PLAN.md, Step 3c, criterion 2) evaluated for exact lambda = 1 against the generalised 3b rule.
Run from Paper3/: python -I src/p3/proto_joint_eval.py <tag> <Q> [Q2 ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

B = 1000
NAMES = {"rec": "record only", "flat": "flat (all witnesses in record code)", "pet2": "PET c=2 (all witnesses)",
         "spare": "spare slots", "heur": "3b rule generalised", "randmix": "control: 3b pattern on random days",
         "ex05": "exact, lambda 0.5", "ex1": "exact, lambda 1", "ex2": "exact, lambda 2"}
KINDS = {"do": "DO", "ph": "pH", "ec": "conductance", "win7": "7DADM near windows"}


def read(pattern):
    return pd.concat([pd.read_csv(f, dtype={"site": str}) for f in glob.glob(pattern) if os.path.getsize(f) > 10])


def ci(z, col, rng):
    g = z.groupby("site")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), (B, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return f"{s.sum() / c.sum():.3f} ({np.percentile(bs, 2.5):.3f} to {np.percentile(bs, 97.5):.3f})"


def site_mean(z, col):
    return z.groupby("site")[col].mean()


def delta(a, b, rng):
    v = (a - b).dropna().to_numpy()
    bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
    return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def fmt(t):
    return f"{t[0]:+.3f} ({t[1]:+.3f} to {t[2]:+.3f})"


def main():
    tag = sys.argv[1]
    rng = np.random.default_rng(11)
    for Q in map(int, sys.argv[2:]):
        d = read(f"results/{tag}/proto_j/*_Q{Q}.csv")
        d["hard"] = d["hard"].fillna(False).astype(bool)
        print(f"\n## Q = {Q}: {d.site.nunique()} sites; wrong decisions max {d.wrong.max():.3f}")
        q = d[d.kind != "day"]
        for cond in ("iid_p0.3", "gilbert_p0.3_b3"):
            rows, per = [], {}
            for dn, nm in NAMES.items():
                z = d[(d.cond == cond) & (d.design == dn)]
                zd = z[z.kind == "day"]
                zq = z[z.kind != "day"]
                row = {"design": nm, "record recovered": ci(zd, "rec_full", rng)}
                for k, kn in KINDS.items():
                    zz = zq[(zq.kind == k) & zq.hard]
                    row[kn + ", hard"] = ci(zz, "decided_correct", rng)
                row["pooled, hard"] = ci(zq[zq.hard], "decided_correct", rng)
                row["pooled, all"] = ci(zq, "decided_correct", rng)
                rows.append(row)
                per[dn] = {"rec": site_mean(zd, "rec_full"), "hard": site_mean(zq[zq.hard], "decided_correct"),
                           "all": site_mean(zq, "decided_correct")}
            print(f"\n### {cond}\n" + pd.DataFrame(rows).to_markdown(index=False))
            print(f"\nPaired differences, {cond}, Q = {Q} (sites resampled, 95% interval); columns: record; pooled hard; pooled all")
            for x, y in (("ex1", "heur"), ("ex05", "heur"), ("ex2", "heur"), ("ex1", "randmix"), ("ex1", "flat"),
                         ("ex1", "pet2"), ("ex1", "rec"), ("heur", "randmix"), ("heur", "flat")):
                r, h, a = (delta(per[x][m], per[y][m], rng) for m in ("rec", "hard", "all"))
                print(f"  {x} minus {y}: record {fmt(r)}; hard {fmt(h)}; all {fmt(a)}")
            r, h, _ = (delta(per["ex1"][m], per["heur"][m], rng) for m in ("rec", "hard", "all"))
            c1 = h[0] >= 0.02 and r[0] >= -0.005
            c2 = r[0] >= 0.02 and h[0] >= -0.005
            print(f"  criterion 2 (exact lambda 1 vs 3b rule): hard +0.02 at record >= -0.005: {c1}; "
                  f"record +0.02 at hard >= -0.005: {c2}  ->  {'MET' if (c1 or c2) else 'NOT MET'}")


if __name__ == "__main__":
    main()
