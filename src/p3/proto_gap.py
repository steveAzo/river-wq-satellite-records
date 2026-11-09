"""Step 3c: model-level optimality gap. For every development day, the objective J of allocate.py is evaluated for the plan
of each design (record only, flat, PET c = 2, spare, the generalised 3b rule, exact) and compared with the exact optimum
under the same prior and lambda. J is a model quantity (independent loss averaged over p in 0.1..0.5), not a measured
outcome; the measured outcomes are in proto_joint_eval.py. Run from Paper3/: python -I src/p3/proto_gap.py <folder> <tag>
Output: results/<tag>/proto_gap.csv (one row per day, Q, design, lambda) and a summary on stdout.
"""
import glob
import os
import sys
from math import ceil

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import allocate as al  # noqa: E402
from p3.proto_joint import ORDER, build_groups, prepare_items  # noqa: E402

DESIGNS = ("rec", "flat", "pet2", "spare", "heur", "ex1")
LAMS = (0.5, 1.0, 2.0)


def j_of_groups(groups, present, dq, Q, lam, phi):
    """Objective of an explicit group layout: every object's term uses the group that carries its values."""
    where = {}
    kR = None
    for items_, c in groups:
        k = ceil(len(items_) / c)
        if any(t == "R" for t, _ in items_):
            kR = k
        for t, name in items_:
            if t == "W":
                where[name] = k
    PhiR = float(phi[kR]) if kR is not None and kR <= Q else 0.0
    J = lam * PhiR
    names = {"DO": "DO", "pH": "pHmin", "T": "T", "EC": "ECa"}
    for o in present:
        k = where.get(names[o])
        if k is None:
            J += PhiR * dq[o]
        else:
            Pg = float(phi[k]) if k <= Q else 0.0
            J += Pg + dq[o] * max(0.0, PhiR - Pg)
    return J


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    rows, cache = [], {}
    phis = {Q: al.phi_table(Q) for Q in (6, 12)}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        site, items, _ = prepare_items(path, tag)
        for it in items:
            present = [o for o in ORDER if o != "EC" or it["ew"] is not None]
            for Q in (6, 12):
                for lam in LAMS:
                    best = None
                    for dn in DESIGNS:
                        design = "ex" + {0.5: "05", 1.0: "1", 2.0: "2"}[lam] if dn == "ex1" else dn
                        g = build_groups(design, it, Q, it["hard"], cache)
                        J = j_of_groups(g, present, it["dq"], Q, lam, phis[Q])
                        rows.append({"site": site, "day": it["d"], "Q": Q, "lam": lam, "design": dn, "J": J})
        print(site, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/{tag}/proto_gap.csv", index=False)
    print()
    for (Q, lam), z in df.groupby(["Q", "lam"]):
        ex = z[z.design == "ex1"].set_index(["site", "day"]).J
        out = {}
        for dn in DESIGNS:
            j = z[z.design == dn].set_index(["site", "day"]).J
            out[dn] = (j.mean(), (ex - j).mean(), float((ex - j <= 1e-9).mean()))
        print(f"Q = {Q}, lambda = {lam}: mean J, mean gap to exact, share of days at the optimum")
        for dn, (m, g, s) in out.items():
            print(f"  {dn:6s} J {m:.4f}  gap {g:.4f}  optimal on {s:.3f} of days")


if __name__ == "__main__":
    main()
