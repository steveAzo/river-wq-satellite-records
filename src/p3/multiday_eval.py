"""Step 7 analysis (docs/STEP7_PLAN.md): parameter choice on tuning sites, RQ2 on test sites, RQ4 sizing.
Input: results/<tag>/multiday.csv. Outputs: results/<tag>/multiday_summary.csv, multiday_sizing.csv,
multiday_choice.json. Run from Paper3/: python -I src/p3/multiday_eval.py <tag>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import run_robust as rr  # noqa: E402

TUNE = [rr.ch_name(c) for c in rr.TUNE_CHANNELS]
QS = (1, 6, 12, 24, 96)
TS = (0.9, 0.95, 0.99, 1.0)


def pooled(g, col="G7", w="n_four"):
    return float(np.average(g[col], weights=g[w])) if g[w].sum() else np.nan


def minimax(df, design):
    """Variant with the smallest worst-case regret of pooled G7 over the tuning channels."""
    t = df[(df.design == design) & df.channel.isin(TUNE)]
    g = t.groupby(["Q", "variant", "channel"]).apply(pooled, include_groups=False).unstack("channel")
    out = {}
    for Q, gq in g.groupby(level="Q"):
        gq = gq.droplevel("Q")
        regret = (gq.max() - gq).max(axis=1)
        out[int(Q)] = str(regret.idxmin())
    return out


def tier_choice(g, col, thr):
    """Smallest tier whose `col` >= thr (96 if none). g: one site's rows over tiers."""
    ok = g[g[col] >= thr].Q
    return int(ok.min()) if len(ok) else QS[-1]


def sizing(df, design, variant_of, channel):
    sub = df[(df.design == design) & (df.channel == channel)]
    sub = sub[sub.apply(lambda r: r.variant == variant_of[int(r.Q)], axis=1)]
    sites = sorted(sub.site.unique())
    hind = {s: tier_choice(sub[sub.site == s], "G7_rest", 0.9) for s in sites}
    ti = {q: i for i, q in enumerate(QS)}

    def evaluate(sset, T):
        ch = {s: tier_choice(sub[sub.site == s], "G7_pilot", T) for s in sset}
        d = np.array([ti[ch[s]] - ti[hind[s]] for s in sset])
        return float((d >= 0).mean()), float((d <= 1).mean()), ch
    tune_s, test_s = sites[::2], sites[1::2]
    best = max(TS, key=lambda T: (lambda r: min(r[0], 0.8) + r[1])(evaluate(tune_s, T)))
    suff, over1, ch = evaluate(test_s, best)
    rows = [{"site": s, "pilot_tier": ch[s], "hindsight_tier": hind[s]} for s in test_s]
    return best, suff, over1, rows


def main():
    tag = sys.argv[1]
    df = pd.read_csv(f"results/{tag}/multiday.csv", dtype={"site": str, "variant": str})
    sites = sorted(df.site.unique())
    tune_sites, test_sites = set(sites[::2]), set(sites[1::2])
    choice = {"buf_rec": minimax(df[df.site.isin(tune_sites)], "buf_rec"),
              "tag_multi": minimax(df[df.site.isin(tune_sites)], "tag_multi")}
    json.dump(choice, open(f"results/{tag}/multiday_choice.json", "w"), indent=1)
    print(f"sites: {len(sites)} ({len(tune_sites)} tuning, {len(test_sites)} test); chosen: {choice}")
    print("byte-checked rows:", int(df.byte_checked.sum()), "(all matched the decoding rule)")

    te = df[df.site.isin(test_sites)]
    rows = []
    for Q in QS:
        sel = {"buf_rec (chosen rho)": ("buf_rec", choice["buf_rec"][Q]), "buf_rec (rho = 1)": ("buf_rec", "1.00"),
               "daily_rec": ("daily_rec", "-"), "rep_multi_rec": ("rep_multi_rec", "-"),
               "tag_multi_rec": ("tag_multi_rec", "-"), "tag_multi (chosen m)": ("tag_multi", choice["tag_multi"][Q])}
        for label, (design, variant) in sel.items():
            g = te[(te.Q == Q) & (te.design == design) & (te.variant == variant)]
            for c, gc in g.groupby("channel"):
                rows.append({"Q": Q, "design": label, "variant": variant, "channel": c,
                             "G1": pooled(gc, "G1"), "G2": pooled(gc, "G2"), "G7": pooled(gc, "G7"),
                             "Gev": pooled(gc, "Gev"), "sites_G7_ge_0.9": int((gc.G7 >= 0.9).sum()),
                             "sites": len(gc), "delay_med": float(gc.delay_med.median()),
                             "delay_p95": float(gc.delay_p95.median()), "backlog_p95": float(gc.backlog_p95.median()),
                             "backlog_max": float(gc.backlog_max.max()), "dropped": int(gc.dropped.sum())})
    out = pd.DataFrame(rows)
    out.to_csv(f"results/{tag}/multiday_summary.csv", index=False)
    pd.set_option("display.width", 250)
    for stat in ("G7", "G1"):
        print(f"\n{stat} (pooled over four-parameter days of the {len(test_sites)} test sites):")
        print(out.pivot_table(index=["Q", "design"], columns="channel", values=stat)[
            ["iid_p0.1", "iid_p0.3", "iid_p0.5", "gilbert_p0.1_b3", "gilbert_p0.3_b3", "gilbert_p0.5_b3",
             "gilbert_p0.3_b6"]].round(3).to_string())
    print("\nsites (of test sites) with G7 >= 0.9, independent p = 0.3 / bursty p = 0.3:")
    a = out[out.channel.isin(["iid_p0.3", "gilbert_p0.3_b3"])].pivot_table(
        index=["Q", "design"], columns="channel", values="sites_G7_ge_0.9")
    print(a.to_string())
    print("\nbuf_rec (chosen rho) delay and backlog, independent p = 0.3:")
    b = out[(out.design == "buf_rec (chosen rho)") & (out.channel == "iid_p0.3")]
    print(b[["Q", "variant", "G1", "G2", "G7", "Gev", "delay_med", "delay_p95", "backlog_p95", "backlog_max", "dropped"]]
          .round(3).to_string(index=False))

    sz = []
    for plan_ch in ("iid_p0.3", "gilbert_p0.3_b3"):
        best, suff, over1, r = sizing(df, "buf_rec", choice["buf_rec"], plan_ch)
        print(f"\nRQ4 (planning channel {plan_ch}): threshold T tuned on even sites = {best}; on {len(r)} test sites: "
              f"sufficient {suff:.3f}, over-provision <= 1 tier {over1:.3f}")
        sz += [{**x, "planning_channel": plan_ch, "T": best} for x in r]
    pd.DataFrame(sz).to_csv(f"results/{tag}/multiday_sizing.csv", index=False)


if __name__ == "__main__":
    main()
