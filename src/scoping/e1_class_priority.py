"""E1: is a fixed parameter-class priority (proposal 3: Temperature 'stable', DO 'volatile') supported?

For each site and calendar month, count send-on-delta (SOD) reports per parameter at the Paper 1 L2
tolerance (T 0.2 degC, DO 2 %sat, pH 0.1, EC 2 % of the site median). A parameter's SOD report rate
is the share of its samples that leave the tolerance band around the last reported value, i.e. how
much "news" it produces per sample, in units of its own tolerance.

Outputs: results/scoping/e1_sod_rates.csv (site, month, parameter, n, rate) and a printed summary of
which parameter ranks first (most news) per site and per site-month.
Run from Paper3/: python -I src/scoping/e1_class_priority.py
"""
import glob
import os

import numpy as np
import pandas as pd

TOL = {"T": 0.2, "DO": 2.0, "pH": 0.1}
PARAMS = ["T", "DO", "pH", "EC"]


def sod_flags(x, tol):
    """Boolean array: True where SOD (hold reconstruction) would send. NaNs never send and keep the reference."""
    sent = np.zeros(len(x), bool)
    ref = np.nan
    for i, v in enumerate(x):
        if np.isnan(v):
            continue
        if np.isnan(ref) or abs(v - ref) > tol:
            sent[i] = True
            ref = v
    return sent


def site_rows(name, df):
    rows = []
    tol = dict(TOL, EC=0.02 * np.nanmedian(df["EC"]))
    month = df["t"].dt.to_period("M").astype(str)
    for p in PARAMS:
        if p not in df or df[p].notna().sum() < 1000:
            continue
        flags = sod_flags(df[p].to_numpy(float), tol[p])
        ok = df[p].notna().to_numpy()
        for m in sorted(month.unique()):
            sel = (month == m).to_numpy() & ok
            if sel.sum() < 500:  # skip thin months
                continue
            rows.append({"site": name, "month": m, "param": p, "n": int(sel.sum()), "rate": flags[sel].mean()})
    return rows


def main():
    rows = []
    for f in sorted(glob.glob("data/clean/usgs/*.csv")):
        df = pd.read_csv(f, parse_dates=["t"])
        rows += site_rows(os.path.basename(f)[:-4], df)
    inws = pd.read_csv("data/clean/inws_cycles.csv", parse_dates=["t"])
    rows += site_rows("InWaterSense", inws[inws.node == 1])
    out = pd.DataFrame(rows)
    os.makedirs("results/scoping", exist_ok=True)
    out.to_csv("results/scoping/e1_sod_rates.csv", index=False)

    whole = out.groupby(["site", "param"]).apply(lambda g: np.average(g.rate, weights=g.n), include_groups=False).unstack()
    print("SOD report rate per sample at L2 (whole record):")
    print(whole.round(3).to_string())
    top = whole.idxmax(axis=1)
    print("\nMost 'volatile' parameter per site (highest rate):", top.value_counts().to_dict())
    print("Least 'volatile' per site:", whole.idxmin(axis=1).value_counts().to_dict())
    sm = out.pivot_table(index=["site", "month"], columns="param", values="rate")
    full = sm.dropna()
    print(f"\nSite-months with all four parameters: {len(full)}")
    print("Top parameter per site-month:", full.idxmax(axis=1).value_counts().to_dict())
    # how often does the site's top parameter change between months?
    changes = full.idxmax(axis=1).groupby(level=0).agg(lambda s: s.nunique())
    print("Distinct top parameters across months, per site (count of sites):", changes.value_counts().sort_index().to_dict())
    # T vs DO specifically (proposal 3's example)
    td = sm[["T", "DO"]].dropna()
    print(f"Site-months where T produces more news than DO: {(td['T'] > td['DO']).mean():.2f} of {len(td)}")
    # dynamic range of rates within a site across months
    rng = out.groupby(["site", "param"]).rate.agg(lambda r: r.max() / max(r.min(), 1e-4))
    print("Median max/min monthly rate ratio within a site-parameter:", round(float(rng.median()), 1))


if __name__ == "__main__":
    main()
