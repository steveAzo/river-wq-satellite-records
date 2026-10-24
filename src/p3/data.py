"""Site-day loading with per-value tolerances (Paper 3 study plan, Section 4).

A site-day holds the 24-h record of every parameter of one site, an anchor (the last value before
the day, assumed known to the server), and a per-value tolerance array:

  USGS TM 1-D3 Table 18 (Wagner et al., 2006)
    "excellent": T 0.2 degC; SC 3 % of the value; DO max(0.3 mg/L, 5 % of the value); pH 0.2
    "good":      T 0.5 degC; SC 10 %;               DO max(0.5 mg/L, 10 %);              pH 0.5

DO is used in mg/L (the unit of the rating). Gaps of <= 2 slots inside a day are bridged linearly;
a day with any longer gap, or without an anchor, is dropped.
"""
import glob
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

PARAMS = ("T", "DO", "pH", "EC")
COLUMN = {"T": "T", "DO": "DO_mgL", "pH": "pH", "EC": "EC"}
TOLSETS = {
    "excellent": {"T": (0.2, 0.0), "EC": (0.0, 0.03), "DO": (0.3, 0.05), "pH": (0.2, 0.0)},
    "good": {"T": (0.5, 0.0), "EC": (0.0, 0.10), "DO": (0.5, 0.10), "pH": (0.5, 0.0)},
}


def tolerance(param, values, tolset="excellent"):
    """Per-value tolerance: max(absolute floor, relative share x |value|)."""
    absolute, relative = TOLSETS[tolset][param]
    return np.maximum(absolute, relative * np.abs(np.asarray(values, float)))


@dataclass
class SiteDay:
    site: str
    day: pd.Timestamp
    params: tuple
    X: np.ndarray       # P x n true values
    anchor: np.ndarray  # P values just before the day
    tol: np.ndarray     # P x n per-value tolerances
    step_min: int

    @property
    def n(self):
        return self.X.shape[1]

    @property
    def P(self):
        return self.X.shape[0]


def load_site(path, tolset="excellent", min_coverage=0.5):
    site = os.path.basename(path)[:-4]
    df = pd.read_csv(path, parse_dates=["t"])
    step = int(round(df["t"].diff().dt.total_seconds().median() / 60))
    params = tuple(p for p in PARAMS if COLUMN[p] in df and df[COLUMN[p]].notna().mean() > min_coverage)
    g = (df.set_index("t")[[COLUMN[p] for p in params]].resample(f"{step}min").mean()
         .interpolate(limit=2, limit_area="inside"))
    g.columns = list(params)
    n = int(24 * 60 / step)
    days = []
    for start in range(1, len(g) - n + 1, n):
        win = g.iloc[start:start + n].to_numpy(float).T
        prev = g.iloc[start - 1].to_numpy(float)
        if np.isnan(win).any() or np.isnan(prev).any():
            continue
        tol = np.stack([tolerance(p, win[i], tolset) for i, p in enumerate(params)])
        days.append(SiteDay(site, g.index[start].floor("D"), params, win, prev, tol, step))
    return days


def load_folder(folder, tolset="excellent"):
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        out += load_site(f, tolset)
    return out
