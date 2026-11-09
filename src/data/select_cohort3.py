"""Select the third (final) confirmation cohort from USGS metadata only (docs/CONFIRM3_PLAN.md, Section 2).

Same rules as the second cohort (src/data/select_new_cohort.py, docs/CONFIRM2_PLAN.md Section 2), with regions that share no
state with the second cohort and sites that were never used in development or in the second cohort:
  rule 1  the instantaneous-value series of all four parameters covers the whole year (series catalogue);
  rule 2  sites used before are excluded (development 2023, the 2024 re-test, the second cohort);
  rule 3  at least 250 approved ("A") daily means per parameter in 2024 (only the qualifiers are read, the values are discarded);
  rule 5  candidates are taken in a seeded random order within each region.
Output: results/confirm3/selection.csv (every candidate considered, the checks applied, and the selection). No water-quality
value is read or kept. Run from Paper3/: python -I src/data/select_cohort3.py
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import select_new_cohort as s2  # noqa: E402

REGIONS = {"Pacific coast": ["WA", "OR", "CA"],
           "Mid-Atlantic and Appalachia": ["PA", "MD", "VA", "WV", "NJ", "DE"],
           "Ohio valley and Great Lakes": ["OH", "IN", "MI", "IL", "KY", "TN"],
           "Gulf and lower Mississippi": ["LA", "MS", "AR", "OK"]}
PER_REGION = 9
SEED = 20261107


def used_sites():
    used = set()
    for folder in ("data/clean/usgs", "data/clean/usgs_2024", "data/clean/usgs_new2024"):
        if os.path.isdir(folder):
            used |= {f[:-4] for f in os.listdir(folder) if f.endswith(".csv")}
    if os.path.exists("results/confirm2/selection.csv"):
        sel = pd.read_csv("results/confirm2/selection.csv", dtype={"site_no": str})
        used |= set(sel[sel.selected].site_no)
    return used


def main():
    used = used_sites()
    print(f"{len(used)} sites already used (excluded)", flush=True)
    rows = []
    rng = np.random.default_rng(SEED)
    for region, states in REGIONS.items():
        cand = pd.concat([s2.covers_year(s2.catalogue(s)).assign(state=s) for s in states], ignore_index=True)
        cand = cand[~cand.site_no.isin(used)].sort_values("site_no").reset_index(drop=True)
        order = rng.permutation(len(cand))
        picked = 0
        print(f"{region}: {len(cand)} sites pass rules 1 and 2", flush=True)
        for rank, i in enumerate(order):
            r = cand.iloc[i].to_dict() | {"region": region, "draw_rank": rank}
            if picked < PER_REGION:
                cnt = s2.approved_days(r["site_no"])
                r.update({f"approved_days_{p}": c for p, c in cnt.items()})
                r["approved"] = min(cnt.values()) >= 250
                r["selected"] = r["approved"]
                picked += r["selected"]
                print(f"  {r['site_no']} {r['station_nm'][:40]:40s} {cnt} {'SELECTED' if r['selected'] else ''}", flush=True)
            else:
                r["selected"] = False
            rows.append(r)
    os.makedirs("results/confirm3", exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv("results/confirm3/selection.csv", index=False)
    print(f"selected {int(out.selected.sum())} sites:", out[out.selected].groupby("region").size().to_dict())


if __name__ == "__main__":
    main()
