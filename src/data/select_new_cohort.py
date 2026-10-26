"""Select the second-confirmation cohort from USGS metadata only (docs/CONFIRM2_PLAN.md, Section 2).

Rule 1 (series catalogue) and rule 2 (exclusion) use the site service; rule 3 (approval) counts approved ("A")
daily-mean qualifiers for 2024 and discards the values unread; rule 5 draws sites in a seeded random order.
Output: results/confirm2/selection.csv (every candidate, the checks applied, and the selection).
Run from Paper3/: python -I src/data/select_new_cohort.py
"""
import io
import json
import os
import time
import urllib.request

import numpy as np
import pandas as pd

PARAMS = {"00010": "T", "00095": "EC", "00300": "DO", "00400": "pH"}
REGIONS = {"Southeast": ["GA", "FL", "AL", "SC", "NC"], "Mountain West": ["CO", "UT", "MT", "ID", "WY"],
           "Great Plains and upper Midwest": ["MN", "WI", "KS", "NE", "MO", "SD", "ND"],
           "Southwest and Texas": ["AZ", "NM", "TX", "NV"],
           "New England and New York": ["MA", "NY", "VT", "NH", "ME", "CT", "RI"]}
PER_REGION = 8
SEED = 20261025
YEAR = 2024
SITE_URL = ("https://waterservices.usgs.gov/nwis/site/?format=rdb&stateCd={s}&siteType=ST&hasDataTypeCd=iv"
            "&parameterCd=00010,00095,00300,00400&seriesCatalogOutput=true&outputDataTypeCd=iv")
DV_URL = ("https://waterservices.usgs.gov/nwis/dv/?format=json&sites={site}&parameterCd=00010,00095,00300,00400"
          "&statCd=00003,00008&startDT={y}-01-01&endDT={y}-12-31&siteStatus=all")


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return r.read().decode()
        except Exception as e:  # network hiccups: back off and retry
            print("   retry", k + 1, e, flush=True)
            time.sleep(5 * (k + 1))
    return None


def catalogue(state):
    t = get(SITE_URL.format(s=state))
    if not t:
        return pd.DataFrame()
    lines = [x for x in t.splitlines() if not x.startswith("#")]
    return pd.read_csv(io.StringIO("\n".join([lines[0]] + lines[2:])), sep="\t", dtype=str)


def covers_year(df):
    """Sites whose iv series of every parameter covers the whole year (rule 1)."""
    df = df[(df.site_tp_cd == "ST") & df.data_type_cd.isin(["uv", "iv"]) & df.parm_cd.isin(PARAMS)]
    ok = df[(df.begin_date <= f"{YEAR}-01-01") & (df.end_date >= f"{YEAR}-12-31")]
    n = ok.groupby("site_no").parm_cd.nunique()
    good = n[n == len(PARAMS)].index
    return df.drop_duplicates("site_no").set_index("site_no").loc[good, ["station_nm", "dec_lat_va", "dec_long_va",
                                                                       "huc_cd"]].reset_index()


def approved_days(site):
    """Approved daily means per parameter in YEAR (rule 3). Only qualifiers are read; values are discarded."""
    t = get(DV_URL.format(site=site, y=YEAR))
    cnt = {p: 0 for p in PARAMS.values()}
    if not t:
        return cnt
    for ts in json.loads(t)["value"]["timeSeries"]:
        name = PARAMS.get(ts["variable"]["variableCode"][0]["value"])
        for block in ts["values"]:
            n = sum("A" in v["qualifiers"] for v in block["value"])
            cnt[name] = max(cnt[name], n)
    return cnt


def main():
    used = {f[:-4] for f in os.listdir("data/clean/usgs") if f.endswith(".csv")}
    rows = []
    rng = np.random.default_rng(SEED)
    for region, states in REGIONS.items():
        cand = pd.concat([covers_year(catalogue(s)).assign(state=s) for s in states], ignore_index=True)
        cand = cand[~cand.site_no.isin(used)].sort_values("site_no").reset_index(drop=True)
        order = rng.permutation(len(cand))
        picked = 0
        print(f"{region}: {len(cand)} sites pass rules 1, 2, and 4", flush=True)
        for rank, i in enumerate(order):
            r = cand.iloc[i].to_dict() | {"region": region, "draw_rank": rank}
            if picked < PER_REGION:
                cnt = approved_days(r["site_no"])
                r.update({f"approved_days_{p}": c for p, c in cnt.items()})
                r["approved"] = min(cnt.values()) >= 250
                r["selected"] = r["approved"]
                picked += r["selected"]
                print(f"  {r['site_no']} {r['station_nm'][:40]:40s} {cnt} {'SELECTED' if r['selected'] else ''}", flush=True)
            else:
                r["selected"] = False
            rows.append(r)
    os.makedirs("results/confirm2", exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv("results/confirm2/selection.csv", index=False)
    print(f"selected {int(out.selected.sum())} sites:", out[out.selected].groupby("region").size().to_dict())


if __name__ == "__main__":
    main()
