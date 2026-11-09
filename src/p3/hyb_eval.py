"""Evaluation of the exploratory hybrid designs (docs/REVISION2_PLAN.md, 'Exploratory hybrid designs'): hyb1 (flags plus all
witnesses hosted in spare slots) and hyb2 (flags plus the generalised 3b rule), against record only, the 3b rule, exact lambda 1,
and the flags design, on the same development loss draws as Step 4. Adoption rule written before the run: a hybrid may be adopted
if it matches the flags on the configured thresholds (hard-case decisions within 0.01 and record recovery within 0.01) and keeps at
least +0.20 over the flags on the alternative thresholds (pooled hard cases), at Q = 6 under both loss models.
Run from Paper3/: python -I src/p3/hyb_eval.py dev 6 12
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from p3 import confirm3 as c3  # noqa: E402
from p3 import proto_base_eval as pe  # noqa: E402

NAMES = {"rec": "record only", "heur": "3b rule", "ex1": "exact, lambda 1", "flags": "decision flags", "hyb1": "hybrid 1 (flags + hosted witnesses)",
         "hyb2": "hybrid 2 (flags + 3b rule)"}


def main():
    tag = sys.argv[1]
    for Q in map(int, sys.argv[2:]):
        g = pd.concat([pe.load_agg(tag, Q, "proto_b"), pe.load_agg(tag, Q, "proto_b_hyb1_hyb2")])
        g = g[g.design.isin(NAMES)]
        A = c3.Agg(g)
        print(f"\n## Q = {Q}: {len(A.sites)} sites; wrong decisions max {g[g.metric == 'wrong']['sum'].max():.3f}")
        for cond in c3.CONDS:
            rows = []
            for dn, nm in NAMES.items():
                f = lambda m: "{:.3f} ({:.3f} to {:.3f})".format(*A.level(cond, dn, m))
                rows.append({"design": nm, "record recovered": f("rec"), "hard, configured": f("hard_cfg"),
                             "hard, alternative": f("hard_alt"), "all, configured": f("all_cfg")})
            print(f"\n### {cond}\n" + pd.DataFrame(rows).to_markdown(index=False))
            if Q == 6:
                for h in ("hyb1", "hyb2"):
                    d_hard = A.point(cond, h, "hard_cfg") - A.point(cond, "flags", "hard_cfg")
                    d_rec = A.point(cond, h, "rec") - A.point(cond, "flags", "rec")
                    d_alt = A.point(cond, h, "hard_alt") - A.point(cond, "flags", "hard_alt")
                    ok = abs(d_hard) <= 0.01 or d_hard > 0
                    ok = ok and (abs(d_rec) <= 0.01 or d_rec > 0) and d_alt >= 0.20
                    print(f"  {h} minus flags: hard configured {d_hard:+.3f}, record {d_rec:+.3f}, hard alternative {d_alt:+.3f} "
                          f"-> adoption rule {'MET' if ok else 'NOT MET'} for {cond}")


if __name__ == "__main__":
    main()
