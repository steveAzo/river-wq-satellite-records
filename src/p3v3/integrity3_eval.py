"""Evaluation of the Phase 2 integrity study (src/p3v3/integrity3.py) with the rules of docs/METHOD_V3_PLAN.md, Section 8
(written before the run): H8' rate per million days, limit 0.5 at a bit-error rate of 1e-3 (upper end of the site-clustered 95% interval),
selection by whole-record recovery of the 3b rule at Q = 6 with ties below 0.01 resolved by simplicity (D0, D2, D1, D3).
Run from Paper3/: python -I src/p3v3/integrity3_eval.py <name>"""
import sys

import numpy as np
import pandas as pd

B = 1000
BERS = (1e-4, 1e-3, 1e-2)
BITS = {"D0": 16, "D1": 16, "D2": 24, "D3": 24}
LIMIT = 0.5
SIMPLE = ["D0", "D2", "D1", "D3"]


def pc(ber):
    return 1 - (1 - ber) ** (8 * 23)


def main():
    name = sys.argv[1]
    F = pd.read_csv(f"results/v3dev/integrity3_{name}.csv", dtype={"site": str})
    R = pd.read_csv(f"results/v3dev/integrity3_{name}_rec.csv", dtype={"site": str})
    sites = sorted(F.site.unique())
    rng = np.random.default_rng(5)
    idx = rng.integers(0, len(sites), (B, len(sites)))
    pos = {s: i for i, s in enumerate(sites)}

    def clustered(z, col):
        g = z.groupby("site")[col].agg(["sum", "count"])
        s = np.zeros(len(sites))
        c = np.zeros(len(sites))
        for site, r in g.iterrows():
            s[pos[site]], c[pos[site]] = r["sum"], r["count"]
        pt = s.sum() / max(c.sum(), 1)
        bs = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
        return pt, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

    print(f"# integrity study {name}: {len(sites)} sites, {len(F)} forged draws, {len(R)} unforged draws")
    print("\n## conditional false-certificate day share given one CRC-valid forgery (point, 95% interval)")
    cond = {}
    for (d, v, Q), z in F.groupby(["design", "variant", "Q"]):
        cond[(d, v, Q)] = clustered(z, "day_false")
        t = cond[(d, v, Q)]
        print(f"  {d} {v:6s} Q={Q:2d}: {t[0]:.4f} ({t[1]:.4f} to {t[2]:.4f})  draws {len(z)}")
    print("\n## H8': expected false-certificate days per million days (point / upper bound)")
    ok = {d: True for d in BITS}
    for ber in BERS:
        print(f"  bit-error rate {ber:g}")
        for (d, v, Q), (p, lo, hi) in sorted(cond.items()):
            f = Q * 0.7 * pc(ber) * 2.0 ** -BITS[d] * 1e6
            print(f"    {d} {v:6s} Q={Q:2d}: {f * p:.4f} / {f * hi:.4f}")
            if ber == 1e-3 and f * hi > LIMIT:
                ok[d] = False
    print("\n## classes of day among forged draws (share of draws, false share in class)")
    for (d, v, Q), z in F.groupby(["design", "variant", "Q"]):
        parts = []
        for c, y in z.groupby("cls"):
            parts.append(f"{c} {len(y) / len(z):.2f}/{y.day_false.mean():.3f}")
        print(f"  {d} {v:6s} Q={Q:2d}: " + "; ".join(parts))
    print("\n## whole-record recovery, unforged draws (point, 95% interval)")
    rec = {}
    for (d, v, Q), z in R.groupby(["design", "variant", "Q"]):
        rec[(d, v, Q)] = clustered(z, "full")
        t = rec[(d, v, Q)]
        print(f"  {d} {v:6s} Q={Q:2d}: {t[0]:.3f} ({t[1]:.3f} to {t[2]:.3f})")
    print("\n## selection")
    for d in BITS:
        print(f"  {d}: meets the limit of {LIMIT} per million at 1e-3 in every block: {ok[d]}")
    passing = [d for d in SIMPLE if ok[d]]
    if not passing:
        print("  no design meets the limit; report it, do not change the limit")
        return
    level = {d: rec[(d, "3b", 6)][0] for d in passing}
    best = max(level.values())
    near = [d for d in passing if best - level[d] < 0.01]
    print(f"  recovery of the 3b rule at Q = 6 among passing designs: {level}")
    print(f"  selected (highest recovery, ties within 0.01 go to the simplest): {near[0]}")


if __name__ == "__main__":
    main()
