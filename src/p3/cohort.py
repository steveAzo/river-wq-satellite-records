"""Cohort audit (revision Step 1; review M10, M11, Table B).

For every site of a folder: sampling interval, parameters kept by the site-level coverage rule
(data.load_site), calendar days, and why each candidate day was or was not eligible. The day rules
mirror data.load_site exactly, and the eligible count is checked against it.

Three size metrics per eligible site-day, each with its denominator (needs the need_<tolset>.csv of RQ1):
  value_share  = kept values / raw values (P x n)                                  count ratio
  byte_share   = kept values x 24 bit / raw values x 13 bit                       application bytes;
                 kept values carry parameter (2) + slot (9) + reading (13) bits, raw readings only the
                 13-bit reading (time implicit in a periodic record): the smallest raw form, so this
                 ratio is conservative
  msgs_kept    = ceil(kept / 7) messages of 23 B (current frame; revised in Step 2), vs
  msgs_raw     = ceil(raw bits / (22 x 8)) messages carrying the 13-bit raw readings back to back
Outputs: results/cohort/<tag>_sites.csv, <tag>_flow.csv, <tag>_days.csv.
Run from Paper3/: python -I src/p3/cohort.py <folder> <tag> [need_csv]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3.data import COLUMN, PARAMS, load_site  # noqa: E402

V, VALUE_BITS, RAW_BITS, PAYLOAD = 7, 24, 13, 22


def audit_site(path, min_coverage=0.5):
    site = os.path.basename(path)[:-4]
    df = pd.read_csv(path, parse_dates=["t"])
    step = int(round(df["t"].diff().dt.total_seconds().median() / 60))
    cover = {p: (df[COLUMN[p]].notna().mean() if COLUMN[p] in df else 0.0) for p in PARAMS}
    params = tuple(p for p in PARAMS if cover[p] > min_coverage)
    g = (df.set_index("t")[[COLUMN[p] for p in params]].resample(f"{step}min").mean()
         .interpolate(limit=2, limit_area="inside"))
    n = int(24 * 60 / step)
    reasons = []
    for start in range(1, len(g) - n + 1, n):
        win = g.iloc[start:start + n].to_numpy(float)
        prev = g.iloc[start - 1].to_numpy(float)
        gap = np.isnan(win).any()
        reasons.append({"site": site, "day": str(g.index[start].floor("D").date()),
                        "status": "gap" if gap else ("no_anchor" if np.isnan(prev).any() else "eligible"),
                        # a day dropped for a gap in one channel may still be complete in the others
                        "complete_channels": int((~np.isnan(win)).all(axis=0).sum())})
    row = {"site": site, "step_min": step, "slots_per_day": n, "n_par": len(params), "params": "|".join(params),
           **{f"cover_{p}": round(cover[p], 3) for p in PARAMS},
           "first": str(df.t.min().date()), "last": str(df.t.max().date()),
           "candidate_days": len(reasons)}
    return row, reasons


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    need_csv = sys.argv[3] if len(sys.argv) > 3 else None
    sites, days = [], []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        row, reasons = audit_site(f)
        n_elig = sum(r["status"] == "eligible" for r in reasons)
        assert n_elig == len(load_site(f)), f"audit disagrees with data.load_site at {f}"
        row.update({k: sum(r["status"] == k for r in reasons) for k in ("eligible", "gap", "no_anchor")})
        row["gap_but_some_complete"] = sum(r["status"] == "gap" and r["complete_channels"] > 0 for r in reasons)
        sites.append(row)
        days += reasons
    sites = pd.DataFrame(sites)
    days = pd.DataFrame(days)

    if need_csv:
        need = pd.read_csv(need_csv, dtype={"site": str})
        need["value_share"] = need["values"] / need["raw_values"]
        need["byte_share"] = need["values"] * VALUE_BITS / (need["raw_values"] * RAW_BITS)
        need["bytes_kept"] = np.ceil(need["values"] * VALUE_BITS / 8)
        need["bytes_raw"] = np.ceil(need["raw_values"] * RAW_BITS / 8)
        need["msgs_kept"] = -(-need["values"] // V)
        need["msgs_raw"] = -(-need["bytes_raw"] // PAYLOAD)
        need["four"] = need["n_par"] == 4
        agg = need.groupby("site").agg(need_days=("values", "size"), bytes_med=("bytes_kept", "median"),
                                       bytes_p99=("bytes_kept", lambda x: x.quantile(.99)),
                                       value_share_med=("value_share", "median"),
                                       byte_share_med=("byte_share", "median")).reset_index()
        sites = sites.merge(agg, on="site", how="left")
        assert (sites.need_days == sites.eligible).all(), "need file and audit disagree on eligible days"
        days = days.merge(need[["site", "day", "values", "raw_values", "value_share", "byte_share",
                                "bytes_kept", "bytes_raw", "msgs_kept", "msgs_raw", "four", "step_min"]],
                          on=["site", "day"], how="left")

    os.makedirs("results/cohort", exist_ok=True)
    sites.to_csv(f"results/cohort/{tag}_sites.csv", index=False)
    days.to_csv(f"results/cohort/{tag}_days.csv", index=False)

    el = days[days.status == "eligible"].copy()
    if need_csv:
        el["four"] = el["four"].astype(bool)
    flow = [("sites", len(sites)),
            ("sites with 4 parameters", int((sites.n_par == 4).sum())),
            ("candidate site-days", len(days)),
            ("dropped: gap > 2 readings in a kept channel", int((days.status == "gap").sum())),
            ("  of which some channel complete", int(sites.gap_but_some_complete.sum())),
            ("dropped: no anchor", int((days.status == "no_anchor").sum())),
            ("eligible site-days", len(el))]
    if need_csv:
        flow += [("eligible, 4 parameters", int(el.four.sum())), ("eligible, < 4 parameters", int((~el.four).sum()))]
    pd.DataFrame(flow, columns=["stage", "count"]).to_csv(f"results/cohort/{tag}_flow.csv", index=False)
    print(f"== {tag} ==")
    for k, v in flow:
        print(f"  {k:45s} {v:>7,}")
    print("  sites by parameter set:", sites.params.value_counts().to_dict())
    print("  sites by interval (min):", sites.step_min.value_counts().sort_index().to_dict())
    if need_csv:
        def summary(d, label):
            print(f"  {label:34s} n={len(d):>6,}  bytes med {d.bytes_kept.median():5.0f}  p99 {d.bytes_kept.quantile(.99):5.0f}"
                  f"  value_share {100 * d.value_share.median():.2f}%  byte_share {100 * d.byte_share.median():.2f}%"
                  f"  msgs med {d.msgs_kept.median():.0f} (raw {d.msgs_raw.median():.0f})")
        summary(el, "all eligible site-days")
        summary(el[el.four], "four-parameter site-days")
        summary(el[~el.four], "fewer-parameter site-days")
        se = el.groupby("site")[["bytes_kept", "value_share", "byte_share"]].median()
        print(f"  site-equal-weighted (median of site medians): bytes {se.bytes_kept.median():.0f}"
              f"  value_share {100 * se.value_share.median():.2f}%  byte_share {100 * se.byte_share.median():.2f}%")
        for s, d in el.groupby("step_min"):
            summary(d, f"interval {s} min ({d.site.nunique()} sites)")


if __name__ == "__main__":
    main()
