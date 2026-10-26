"""Step 8 summary (docs/STEP8_PLAN.md): decisions, daily statistics, timing, and the 7DADM per design and condition.
Input: results/<tag>/env_days.csv, env_7dadm.csv. Output: results/<tag>/env_summary.csv (Table C).
Run from Paper3/: python -I src/p3/env_eval.py <tag>
"""
import sys

import numpy as np
import pandas as pd

ORDER = ["rec_code", "rec_rep", "every_k", "tag"]


def rate(num, den):
    return float(num.sum() / den.sum()) if den.sum() else np.nan


def main():
    tag = sys.argv[1]
    d = pd.read_csv(f"results/{tag}/env_days.csv", dtype={"site": str})
    s7 = pd.read_csv(f"results/{tag}/env_7dadm.csv", dtype={"site": str})
    rows = []
    for (Q, cond, design), g in d.groupby(["Q", "cond", "design"]):
        r = {"Q": Q, "cond": cond, "design": design, "days": len(g), "sites": g.site.nunique()}
        for k in ("DO", "pH", "EC"):
            ev = g[f"{k}_true"]
            r[f"{k}_events"] = int(ev.sum())
            r[f"{k}_miss_rate"] = rate(g[f"{k}_FN"], ev)                       # missed exceedance days / events
            r[f"{k}_false_alarm_rate"] = rate(g[f"{k}_FP"], 1 - ev)
            if k != "EC":
                r[f"{k}_decided"] = float(g[f"{k}_decided"].mean())
                r[f"{k}_decided_on_events"] = rate(g[f"{k}_decided"] * ev, ev)
                r[f"{k}_wrong"] = float(g[f"{k}_wrong"].sum())
        for p in ("T", "DO", "pH", "EC"):
            for st in ("min", "max", "mean"):
                r[f"{p}_{st}_within"] = float(g[f"{p}_{st}_within"].mean())
        r["T_peak_min"] = float(g["T_peak_min"].mean())
        r["DO_peak_min"] = float(g["DO_peak_min"].mean())
        r["DO_range_err"] = float(g["DO_range_err"].mean())
        r["EC_jump_min"] = float(g["EC_jump_min"].mean())
        r["certified_share"] = float(g["certified_share"].mean())
        h = s7[(s7.Q == Q) & (s7.cond == cond) & (s7.design == design)]
        r["7DADM_windows"], r["7DADM_events"] = len(h), int(h["true"].round().sum())
        r["7DADM_miss_rate"] = rate(h["FN"], h["true"])
        r["7DADM_false_alarm_rate"] = rate(h["FP"], 1 - h["true"])
        r["7DADM_decided"] = float(h["decided"].mean()) if len(h) else np.nan
        r["7DADM_wrong"] = float(h["wrong"].sum())
        rows.append(r)
    out = pd.DataFrame(rows)
    out["design"] = pd.Categorical(out.design, ORDER)
    out = out.sort_values(["Q", "cond", "design"])
    out.to_csv(f"results/{tag}/env_summary.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(f"days: {d[['site', 'day']].drop_duplicates().shape[0]}; 7DADM windows: "
          f"{s7[['site', 'window_end']].drop_duplicates().shape[0]}")
    print("three-valued decisions that were wrong (must be 0):",
          float(out[["DO_wrong", "pH_wrong", "7DADM_wrong"]].to_numpy().sum()))
    blocks = {
        "decisions (miss = missed exceedance days / event days; decided = certain yes or no)":
            ["DO_events", "DO_miss_rate", "DO_false_alarm_rate", "DO_decided", "DO_decided_on_events",
             "pH_events", "pH_miss_rate", "pH_false_alarm_rate", "pH_decided"],
        "7DADM > 20 degC and conductance pulses":
            ["7DADM_events", "7DADM_miss_rate", "7DADM_false_alarm_rate", "7DADM_decided",
             "EC_events", "EC_miss_rate", "EC_false_alarm_rate", "EC_jump_min"],
        "daily statistics within tolerance (share of days)":
            ["T_min_within", "T_max_within", "DO_min_within", "DO_max_within", "DO_mean_within", "pH_max_within",
             "EC_max_within", "certified_share"],
        "timing (minutes) and DO diel range error (mg/L)": ["T_peak_min", "DO_peak_min", "DO_range_err"],
    }
    for title, cols in blocks.items():
        print(f"\n== {title} ==")
        print(out.set_index(["Q", "cond", "design"])[cols].round(3).to_string())


if __name__ == "__main__":
    main()
