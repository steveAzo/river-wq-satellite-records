"""Convert the low-cost deployments into the toolkit's per-site CSV format (t, T, DO_mgL, pH, EC).

InWaterSense node 1 (Kosovo; Ahmedi, Mendeley Data, CC BY 4.0): values flagged by the original cleaning
(*_range, *_plaus, *_spike True) are dropped. DO is reported in % saturation; it is converted to mg/L
with the Benson & Krause (1984) freshwater oxygen solubility at the measured temperature (zero salinity,
1 atm), so that the USGS mg/L tolerance applies.
Weija (Ghana; the Prof's deployment, permission 2026-10-23): T and EC only. Its pH record is the known
implausible series (8.5-12.8 daily, tracking temperature) and is not used. Flagged values are dropped.
Writes results/confirm/lowcost_input/{InWaterSense,Weija}.csv.
Run from Paper3/: python -I src/p3/lowcost.py
"""
import os

import numpy as np
import pandas as pd


def do_sat_mgL(temp_c):
    """Benson & Krause (1984) equilibrium O2 concentration in fresh water at 1 atm, mg/L."""
    T = np.asarray(temp_c, float) + 273.15
    ln_c = (-139.34411 + 1.575701e5 / T - 6.642308e7 / T ** 2 + 1.243800e10 / T ** 3 - 8.621949e11 / T ** 4)
    return np.exp(ln_c)


def drop_flagged(df, cols):
    for c in cols:
        for flag in (f"{c}_range", f"{c}_plaus", f"{c}_spike"):
            if flag in df:
                df.loc[df[flag].astype(str).str.lower() == "true", c] = np.nan
    return df


def main():
    out = "results/confirm/lowcost_input"
    os.makedirs(out, exist_ok=True)
    inws = pd.read_csv("data/clean/inws_cycles.csv", parse_dates=["t"])
    inws = drop_flagged(inws[inws.node == 1].copy(), ["T", "DO", "pH", "EC"])
    inws["DO_mgL"] = inws["DO"] / 100.0 * do_sat_mgL(inws["T"])
    inws[["t", "T", "DO_mgL", "pH", "EC"]].sort_values("t").to_csv(f"{out}/InWaterSense.csv", index=False)
    w = pd.read_csv("data/clean/weija_cycles.csv", parse_dates=["t"])
    w = drop_flagged(w, ["T", "EC"])
    w[["t", "T", "EC"]].sort_values("t").to_csv(f"{out}/Weija.csv", index=False)
    for name in ("InWaterSense", "Weija"):
        d = pd.read_csv(f"{out}/{name}.csv")
        print(name, len(d), "rows; non-missing share:", d.drop(columns="t").notna().mean().round(2).to_dict())


if __name__ == "__main__":
    main()
