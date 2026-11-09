"""Descriptive per-region summary of the confirmation (docs/CONFIRM3_PLAN.md Section 5: per-region heterogeneity, no verdict).
Written after the confirmatory run; it reads only the per-site result files that confirm3.py produced and the metadata-only
selection file, and it changes no threshold, design, or site. Writes draft3/tables/confirm_region.tex.
Run from Paper3/: python -I src/paper/region5.py
"""
import sys

import pandas as pd

sys.path.insert(0, "src/p3")
import proto_base_eval as pe  # noqa: E402

SUB = "proto_b_rec_heur_ex1_tight50_sod_mds_sod_once_flags_randmix_hyb1_hyb2"
sel = pd.read_csv("results/confirm3/selection.csv", dtype={"site_no": str})
sel = sel[sel.selected.astype(str) == "True"][["site_no", "region"]]
g = pe.load_agg("confirm3", 6, subdir=SUB)
print(sorted(g.cond.unique()))
g = g.merge(sel, left_on="site", right_on="site_no")
rows = []
LOSS = {"iid_p0.3": "Independent loss", "gilbert_p0.3_b3": "Gilbert loss"}
DES = (("rec", "Record only"), ("heur", "3b rule"), ("flags", "Decision flags"), ("hyb1", "Hybrid 1"))
for cond, lab in LOSS.items():
    rows.append(f"\\multicolumn{{5}}{{@{{}}l}}{{{lab}, $Q = 6$ (hard cases decided at unanticipated thresholds | record recovered)}} \\\\")
    for region, z in g.groupby("region"):
        n = z.site.nunique()
        cells = []
        for d, _ in DES:
            def lvl(metric):
                t = z[(z.cond == cond) & (z.design == d) & (z.metric == metric)]
                return t["sum"].sum() / t["count"].sum()
            cells.append(f"{lvl('hard_alt'):.3f} | {lvl('rec'):.3f}")
        rows.append(f"{region} ({n} sites) & " + " & ".join(cells) + " \\\\")
    rows.append("\\midrule")
open("draft3/tables/confirm_region.tex", "w", encoding="utf-8").write("\n".join(rows[:-1]) + "\n")
print("\n".join(rows))
