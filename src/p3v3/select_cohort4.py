"""Select the confirmation cohort for method version 3 from USGS metadata only (docs/CONFIRM4_PLAN_DRAFT.md, Section 2; approved by the user
2026-11-10: calendar year 2022, new regions, about 40 sites). The rules of src/data/select_cohort3.py with the year set to 2022:
  rule 1  instantaneous-value series of temperature, conductance, dissolved oxygen, and pH cover the whole of 2022;
  rule 2  every site used so far is excluded (development 2023, 2024 re-test, cohort 2, cohort 3);
  rule 3  at least 250 approved daily means per parameter in 2022 (only the qualifiers are read, values discarded);
  rule 5  candidates in a seeded random order within each region, at most PER_REGION selected per region (no trimming afterwards).
Output: results/confirm4/selection.csv. No water-quality value is read or kept. Run from Paper3/: python -I src/p3v3/select_cohort4.py"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
import select_new_cohort as s2  # noqa: E402

s2.YEAR = 2022
REGIONS = {"Pacific coast": ["WA", "OR", "CA"],
           "Mid-Atlantic and Appalachia": ["PA", "MD", "VA", "WV", "NJ", "DE"],
           "Ohio valley and Great Lakes": ["OH", "IN", "MI", "IL", "KY", "TN"],
           "Gulf and lower Mississippi": ["LA", "MS", "AR", "OK"],
           "Northeast and New England": ["NY", "VT", "NH", "ME", "MA", "CT", "RI"],
           "Southeast": ["NC", "SC", "GA", "FL", "AL"],
           "Texas": ["TX"],
           "Mountain West": ["CO", "UT", "ID", "MT", "WY", "NM", "AZ", "NV"],
           "Upper Midwest": ["MN", "WI", "IA", "MO"]}
PER_REGION = 5
SEED = 20261113


def used_sites():
    used = set()
    for folder in ("data/clean/usgs", "data/clean/usgs_2024", "data/clean/usgs_new2024", "data/clean/usgs_new3_2024"):
        if os.path.isdir(folder):
            used |= {f[:-4] for f in os.listdir(folder) if f.endswith(".csv")}
    for sel_path in ("results/confirm2/selection.csv", "results/confirm3/selection.csv"):
        if os.path.exists(sel_path):
            sel = pd.read_csv(sel_path, dtype={"site_no": str})
            used |= set(sel[sel.selected].site_no)
    return used


def main():
    used = used_sites()
    print(f"{len(used)} sites already used (excluded)", flush=True)
    rows = []
    rng = np.random.default_rng(SEED)
    os.makedirs("results/confirm4", exist_ok=True)
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
        pd.DataFrame(rows).to_csv("results/confirm4/selection.csv", index=False)
    out = pd.DataFrame(rows)
    out.to_csv("results/confirm4/selection.csv", index=False)
    print(f"selected {int(out.selected.sum())} sites:", out[out.selected].groupby("region").size().to_dict())


if __name__ == "__main__":
    main()
