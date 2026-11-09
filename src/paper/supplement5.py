"""Supplement of the v0.5 manuscript: site table of the sealed cohort (metadata from results/confirm3/selection.csv; days per
site counted from results/confirm3/robust2_stage1.csv) and the reading log of the related-work sources (docs/RELATED_WORK_REV2.md,
docs/SEARCH_LOG_REV2.md). Writes draft3/tables/sites.tex. Run from Paper3/: python -I src/paper/supplement5.py"""
import re

import pandas as pd

BS = chr(92)
sel = pd.read_csv("results/confirm3/selection.csv", dtype={"site_no": str})
sel = sel[sel.selected.astype(str) == "True"]
days = pd.read_csv("results/confirm3/robust2_stage1.csv", usecols=["site", "day"], dtype={"site": str}).drop_duplicates()
n = days.groupby("site").size()


def esc(x):
    return str(x).replace("&", BS + "&").replace("_", BS + "_").replace("%", BS + "%")


rows = []
for region, z in sel.sort_values(["region", "site_no"]).groupby("region", sort=False):
    rows.append(BS + "multicolumn{4}{@{}l}{" + esc(region) + "} " + BS + BS)
    for _, r in z.iterrows():
        rows.append(f"{r.site_no} & {esc(r.station_nm.title())} & {r.state} & {int(n.get(r.site_no, 0))} " + BS + BS)
    rows.append(BS + "midrule")
open("draft3/tables/sites.tex", "w", encoding="utf-8").write("\n".join(rows[:-1]) + "\n")
print(len(sel), "sites;", int(n.sum()), "days")
