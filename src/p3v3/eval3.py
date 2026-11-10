"""Evaluation of version 3, Phase 1a (docs/METHOD_V3_PLAN.md): paired, site-clustered contrasts between designs, including the fair
comparators (record only, and decision flags that also use the recovered record). DEVELOPMENT DATA ONLY; no verdict is written.
Run from Paper3/: python -I src/p3v3/eval3.py <outname> [<outname2> ...]   (reads results/v3dev/dev_<outname>/)"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import proto_base_eval as pe  # noqa: E402

B = 1000
LOSS = ("iid_p0.3", "gilbert_p0.3_b3")
METRICS = ("rec", "hard_cfg", "hard_alt", "all_cfg")


def piv(g, cond):
    z = g[g.cond == cond]
    out = {}
    for (d, m), t in z.groupby(["design", "metric"]):
        t = t.sort_values("site")
        out[(d, m)] = (t.site.to_numpy(), t["sum"].to_numpy(), t["count"].to_numpy())
    return out


def level(P, d, m):
    s, su, c = P[(d, m)]
    return su.sum() / c.sum()


def diff(P, a, b, m, rng):
    sa, xa, ca = P[(a, m)]
    sb, xb, cb = P[(b, m)]
    assert (sa == sb).all()
    n = len(sa)
    idx = rng.integers(0, n, (B, n))
    bs = xa[idx].sum(1) / np.maximum(ca[idx].sum(1), 1) - xb[idx].sum(1) / np.maximum(cb[idx].sum(1), 1)
    pt = xa.sum() / ca.sum() - xb.sum() / cb.sum()
    return pt, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def fmt(t):
    return f"{t[0]:+.3f} ({t[1]:+.3f} to {t[2]:+.3f})"


def main():
    names = sys.argv[1:]
    for name in names:
        print(f"\n# run {name}")
        for Q in (6, 12):
            g = pe.load_agg("v3dev", Q, subdir=f"dev_{name}")
            wrong = g[g.metric == "wrong"]["sum"].max()
            print(f"\n## Q = {Q}: {g.site.nunique()} sites; wrong decisions max {wrong:.3f}")
            for cond in LOSS:
                P = piv(g[g.metric.isin(METRICS)], cond)
                designs = sorted({d for d, _ in P})
                print(f"\n### levels, {cond} (record recovered / hard cfg / hard alt / all cfg)")
                for d in designs:
                    print(f"  {d:9s} " + " / ".join(f"{level(P, d, m):.3f}" for m in METRICS))
                rng = np.random.default_rng(31)
                print(f"### contrasts, {cond} (paired, site-clustered 95% interval)")
                for a, b in (("heur", "rec"), ("flagsrec", "rec"), ("flags", "rec"), ("hyb1", "rec"), ("hyb1", "flagsrec"),
                             ("hyb1", "flags"), ("heur", "flagsrec"), ("heur", "flags"), ("hyb2", "flagsrec"), ("hyb2", "rec"), ("ex1", "flagsrec"), ("ex1", "rec"), ("hyb2", "heur"), ("ex1", "heur")):
                    if (a, "rec") in P and (b, "rec") in P:
                        print(f"  {a} minus {b}: " + "; ".join(f"{m} {fmt(diff(P, a, b, m, rng))}" for m in ("rec", "hard_cfg", "hard_alt")))


if __name__ == "__main__":
    main()
