"""Exploratory (after the freeze): put the low-cost deployments on a regular grid for the per-channel loader.

The InWaterSense node (Kosovo) samples every 10.2 min and the Weija node (Ghana) every 32.5 min; their clocks are
not aligned to the hour. Each reading is assigned to the bin of a 10-min (InWaterSense) or 30-min (Weija) grid that
starts at 00:00 UTC, and bins are averaged. Because the native interval is slightly longer than the grid step, an
occasional bin stays empty; the loader bridges such single gaps. Inputs: results/confirm/lowcost_input/*.csv
(src/p3/lowcost.py). Output: results/lowcost2/input/<name>.csv (Weija's file is private: see .gitignore).
Run from Paper3/: python -I src/p3/lowcost_grid.py
"""
import os

import pandas as pd

GRID = {"InWaterSense": 10, "Weija": 30}


def main():
    out = "results/lowcost2/input"
    os.makedirs(out, exist_ok=True)
    for name, step in GRID.items():
        d = pd.read_csv(f"results/confirm/lowcost_input/{name}.csv", parse_dates=["t"]).sort_values("t")
        d["t"] = d["t"].dt.floor(f"{step}min")
        g = d.groupby("t").mean(numeric_only=True).reset_index()
        g["t"] = g["t"].dt.tz_localize("UTC") if g["t"].dt.tz is None else g["t"]
        g.to_csv(f"{out}/{name}.csv", index=False)
        print(name, f"{len(d)} readings -> {len(g)} bins of {step} min")


if __name__ == "__main__":
    main()
