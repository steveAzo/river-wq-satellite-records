"""Cohort flow under the per-channel loader (revision Step 4a; review M10, Table B).

Counts channel-days by status and parameter, record days by channel count, and intervals; compares with
the draft loader's counts (results/cohort/<old_tag>_flow.csv). Outputs results/cohort/<tag>_v2_*.csv.
Run from Paper3/: python -I src/p3/cohort2.py <folder> <tag> [old_tag]
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3.loader import load_records  # noqa: E402


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    old_tag = sys.argv[3] if len(sys.argv) > 3 else None
    audit = []
    days = load_records(folder, audit=audit)
    a = pd.DataFrame(audit, columns=["site", "day", "param", "status", "step"])
    r = pd.DataFrame([{"site": d.site, "day": str(d.day.date()), "n_par": len(d.channels),
                       "params": "|".join(d.params), "steps": "|".join(str(d.steps[p]) for p in d.params),
                       "raw_values": d.raw_values} for d in days])
    os.makedirs("results/cohort", exist_ok=True)
    a.to_csv(f"results/cohort/{tag}_v2_channel_days.csv", index=False)
    r.to_csv(f"results/cohort/{tag}_v2_record_days.csv", index=False)
    print(f"== {tag} (per-channel loader) ==")
    print("channel-days by status:")
    print(a.pivot_table(index="param", columns="status", values="day", aggfunc="count", fill_value=0).to_string())
    print("eligible channel-days by interval (min):")
    el = a[a.status == "eligible"]
    print(el.pivot_table(index="param", columns="step", values="day", aggfunc="count", fill_value=0).to_string())
    print(f"record days (>= 1 channel): {len(r):,}; sites {r.site.nunique()}")
    print("record days by channel count:", r.n_par.value_counts().sort_index().to_dict())
    print(f"four-parameter record days: {(r.n_par == 4).sum():,} at {r[r.n_par == 4].site.nunique()} sites")
    print("sites by number of four-parameter days:",
          r[r.n_par == 4].groupby("site").size().describe()[["min", "50%", "max"]].to_dict())
    mixed = r[(r.n_par == 4) & (r.steps.str.split("|").map(lambda s: len(set(s)) > 1))]
    print(f"four-parameter days with mixed intervals across channels: {len(mixed):,}")
    if old_tag:
        old = pd.read_csv(f"results/cohort/{old_tag}_flow.csv").set_index("stage")["count"]
        print(f"draft loader: eligible {old['eligible site-days']:,}, four-parameter {old['eligible, 4 parameters']:,}")


if __name__ == "__main__":
    main()
