"""Descriptive per-query-kind contrasts of the confirmation (review finding A9): do the pooled hard-case contrasts agree across
dissolved oxygen, pH, conductance, and the 7DADM window, or does one kind drive them? Reads only the per-site result files that
confirm3.py wrote; no threshold, design, or site is changed; point estimates, no verdict.
Run from Paper3/: python -I src/paper/kinds5.py   (writes draft3/tables/confirm_kinds.tex and prints the table)"""
import glob
import os

import pandas as pd

SUB = "results/confirm3/proto_b_rec_heur_ex1_tight50_sod_mds_sod_once_flags_randmix_hyb1_hyb2"
KINDS = {"do": "Dissolved oxygen", "ph": "pH", "ec": "Conductance", "win7": "7DADM"}
LOSS = {"iid_p0.3": "Independent loss", "gilbert_p0.3_b3": "Gilbert loss"}
parts = []
for f in sorted(glob.glob(f"{SUB}/*_Q6.csv")):
    if f.endswith("_meta.csv") or os.path.getsize(f) < 10:
        continue
    d = pd.read_csv(f, dtype={"site": str})
    m = pd.read_csv(f.replace("_Q6.csv", "_Q6_meta.csv"), dtype={"site": str})
    for kind in KINDS:
        z = d[d.kind == kind]
        for v in ("cfg", "alt1", "alt2"):
            hard = m[["site", "day", f"hard_{kind}_{v}"]].rename(columns={f"hard_{kind}_{v}": "hard"})
            t = z[["site", "day", "cond", "design", f"dc_{v}"]].rename(columns={f"dc_{v}": "dc"}).merge(hard, on=["site", "day"])
            t = t[t.dc.notna() & t.hard.notna()]
            t["hard"] = t.hard.astype(bool)
            t = t[t.hard]
            g = t.groupby(["cond", "design"]).dc.agg(["sum", "count"]).reset_index()
            g["kind"], g["scen"] = kind, "cfg" if v == "cfg" else "alt"
            parts.append(g)
a = pd.concat(parts).groupby(["cond", "design", "kind", "scen"])[["sum", "count"]].sum().reset_index()
a["lvl"] = a["sum"] / a["count"]


def lvl(cond, design, kind, scen):
    return float(a[(a.cond == cond) & (a.design == design) & (a.kind == kind) & (a.scen == scen)].lvl.iloc[0])


def n(cond, kind, scen):
    return int(a[(a.cond == cond) & (a.design == "rec") & (a.kind == kind) & (a.scen == scen)]["count"].iloc[0])


BS = chr(92)
EOL = " " + BS + BS
rows = []
for cond, lab in LOSS.items():
    rows.append(BS + "multicolumn{6}{@{}l}{" + lab + EOL.strip() + "}" if False else BS + "multicolumn{6}{@{}l}{" + lab + "}" + EOL)
    for kind, name in KINDS.items():
        c1 = lvl(cond, "heur", kind, "cfg") - lvl(cond, "rec", kind, "cfg")
        c2 = lvl(cond, "heur", kind, "alt") - lvl(cond, "flags", kind, "alt")
        c3 = lvl(cond, "heur", kind, "alt") - lvl(cond, "rec", kind, "alt")
        c4 = lvl(cond, "hyb1", kind, "alt") - lvl(cond, "flags", kind, "alt")
        c5 = lvl(cond, "hyb1", kind, "alt") - lvl(cond, "rec", kind, "alt")
        rows.append(f"{name} ({n(cond, kind, 'cfg')}; {n(cond, kind, 'alt')}) & {c1:+.3f} & {c2:+.3f} & {c3:+.3f} & {c4:+.3f} & {c5:+.3f}" + EOL)
    rows.append(BS + "midrule")
body = "\n".join(rows[:-1]).replace("-0", "$-$0")
open("draft3/tables/confirm_kinds.tex", "w", encoding="utf-8").write(body + "\n")
print(body)
