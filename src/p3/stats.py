"""Step 11: uncertainty and denominators for the headline results (review M17). Development year 2023.

Site-clustered percentile bootstrap (2,000 resamples of sites with replacement; seed fixed) for means pooled over
days, medians, paired differences between designs (same days in both arms), and shares of sites. A site x month
block bootstrap is reported as a sensitivity for the main G_cert estimate.
Inputs: results/<tag>/need2.csv, cohort_exact.csv, robust_exact.csv, env_days.csv, multiday.csv,
robust_choice.json. Outputs: results/<tag>/stats_*.csv. Run from Paper3/: python -I src/p3/stats.py <tag>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import cohort_exact as ce  # noqa: E402
from p3 import run_robust as rr  # noqa: E402

B = 2000
SEED = 20261025
TIERS = (1, 6, 12, 24, 96)
MAIN_CH = ("iid_p0.1", "iid_p0.3", "iid_p0.5", "gilbert_p0.3_b3", "gilbert_p0.3_b6")


def ci(samples):
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def boot_ratio(df, num, den, cluster="site", seed=SEED):
    """sum(num) / sum(den) pooled over rows; clusters resampled."""
    g = df.groupby(cluster)[[num, den]].sum()
    n, d = g[num].to_numpy(), g[den].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), (B, len(g)))
    num, den = n[idx].sum(1), d[idx].sum(1)
    ok = den > 0                      # a resample without any denominator (e.g. no event day) carries no information
    if not ok.any() or d.sum() == 0:
        return np.nan, (np.nan, np.nan)
    return float(n.sum() / d.sum()), ci(num[ok] / den[ok])


def boot_mean(df, col, cluster="site", seed=SEED):
    df = df.assign(_one=1.0)
    return boot_ratio(df, col, "_one", cluster, seed)


def boot_quantile(df, col, q, cluster="site", seed=SEED):
    groups = [g[col].to_numpy() for _, g in df.groupby(cluster)]
    rng = np.random.default_rng(seed)
    est = float(np.quantile(df[col], q))
    reps = [np.quantile(np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]), q)
            for _ in range(B)]
    return est, ci(reps)


def boot_site_share(values, thr, seed=SEED):
    """Share of sites with value >= thr; sites resampled."""
    v = np.asarray(values) >= thr
    rng = np.random.default_rng(seed)
    return float(v.mean()), ci(v[rng.integers(0, len(v), (B, len(v)))].mean(1))


def fmt(est, lo_hi, pct=False, nd=3):
    f = (lambda x: f"{100 * x:.1f}%") if pct else (lambda x: f"{x:.{nd}f}")
    return f"{f(est)} ({f(lo_hi[0])} to {f(lo_hi[1])})"


def rq1(tag):
    d = pd.read_csv(f"results/{tag}/need2.csv", dtype={"site": str})
    d = d[d.n_par == 4].assign(one=(d.msgs <= 1).astype(float))
    rows = [("median bytes per day", *boot_quantile(d, "bytes", 0.5)),
            ("90th percentile bytes", *boot_quantile(d, "bytes", 0.9)),
            ("99th percentile bytes", *boot_quantile(d, "bytes", 0.99)),
            ("median value share", *boot_quantile(d, "value_share", 0.5)),
            ("median byte share", *boot_quantile(d, "byte_share", 0.5)),
            ("share of days in one message", *boot_mean(d, "one"))]
    print(f"\nRQ1: four-parameter record days n = {len(d):,} at {d.site.nunique()} sites (site-clustered 95% intervals)")
    for name, est, lohi in rows:
        print(f"  {name:32s} {fmt(est, lohi, nd=4 if 'share' in name else 1)}")
    return pd.DataFrame([{"outcome": r[0], "estimate": r[1], "lo": r[2][0], "hi": r[2][1], "n_days": len(d),
                          "n_sites": d.site.nunique()} for r in rows])


def rq3(tag, split="test"):
    full = pd.read_csv(f"results/{tag}/cohort_exact.csv", dtype={"site": str})
    out = []
    print(f"\nRQ3 full cohort (exact): {full[['site', 'day']].drop_duplicates().shape[0]:,} four-parameter days at "
          f"{full.site.nunique()} sites")
    for Q in (6, 12):
        w = full[full.Q == Q].pivot_table(index=["site", "day", "month"], columns="design", values=list(MAIN_CH))
        for c in MAIN_CH:
            x = w[c].reset_index()
            line = []
            for des in ("rec_code", "rec_rep", "every_k", "tag"):
                est, lohi = boot_mean(x, des)
                out.append({"Q": Q, "channel": c, "contrast": des, "estimate": est, "lo": lohi[0], "hi": lohi[1],
                            "n_days": len(x), "n_sites": x.site.nunique(), "source": "full cohort, exact"})
                line.append(f"{des} {fmt(est, lohi)}")
            for other in ("rec_rep", "every_k", "tag"):
                x["_d"] = x["rec_code"] - x[other]
                est, lohi = boot_mean(x, "_d")
                out.append({"Q": Q, "channel": c, "contrast": f"rec_code - {other}", "estimate": est, "lo": lohi[0],
                            "hi": lohi[1], "n_days": len(x), "n_sites": x.site.nunique(),
                            "source": "full cohort, exact, paired"})
                line.append(f"code-{other} {fmt(est, lohi)}")
            site = x.groupby("site").rec_code.mean()
            out.append({"Q": Q, "channel": c, "contrast": "rec_code site means: min / median / max",
                        "estimate": float(site.median()), "lo": float(site.min()), "hi": float(site.max()),
                        "n_days": len(x), "n_sites": len(site), "source": "full cohort, site distribution"})
            print(f"  Q {Q:2d} {c:16s} " + "; ".join(line))
            print(f"      site means of the code: min {site.min():.3f}, median {site.median():.3f}, max {site.max():.3f}")
    # sample-only baselines (fixed K, reliable) on the 380 test days, and sample vs full agreement
    ch = json.load(open(f"results/{tag}/robust_choice.json"))
    s = pd.read_csv(f"results/{tag}/robust_exact.csv", dtype={"site": str})
    s = s if split is None else s[s.split == split]
    for Q in (6, 12):
        sq = s[s.Q == Q]
        sel = {"rec_code": sq[sq.fam == "mds_rec"], "fixed_K": sq[(sq.fam == "mds") & (sq.j == ch[str(Q)]["mds"]["minimax"])],
               "reliable": sq[sq.fam == "reliable"], "rec_rep": sq[sq.fam == "rep_rec"]}
        for c in MAIN_CH:
            base = sel["rec_code"].set_index(["site", "day"])[c]
            for other in ("fixed_K", "reliable"):
                o = sel[other].set_index(["site", "day"])[c]
                x = pd.DataFrame({"_d": base - o}).reset_index()
                est, lohi = boot_mean(x, "_d")
                out.append({"Q": Q, "channel": c, "contrast": f"rec_code - {other}", "estimate": est, "lo": lohi[0],
                            "hi": lohi[1], "n_days": len(x), "n_sites": x.site.nunique(),
                            "source": "380 sampled test days, exact, paired"})
            fq = full[(full.Q == Q) & (full.design == "rec_code")][c].mean()
            out.append({"Q": Q, "channel": c, "contrast": "rec_code sample mean (vs full cohort in hi)",
                        "estimate": float(base.mean()), "lo": float(base.mean()), "hi": float(fq),
                        "n_days": len(base), "n_sites": base.index.get_level_values(0).nunique(),
                        "source": "sample vs full"})
    o = pd.DataFrame(out)
    print("\n  sampled-day contrasts and sample vs full agreement (Q = 6):")
    print(o[(o.Q == 6) & o.source.str.contains("sample")][["channel", "contrast", "estimate", "lo", "hi", "n_days"]]
          .round(3).to_string(index=False))
    # season: monthly means and a site x month block bootstrap for the main estimate
    x = full[(full.Q == 6) & (full.design == "rec_code")].copy()
    x["block"] = x.site + "_" + x.month.astype(str)
    print("\n  Season (Q = 6, record-first code): monthly mean G_cert, independent / bursty p = 0.3")
    print("   ", x.groupby("month")[["iid_p0.3", "gilbert_p0.3_b3"]].mean().round(3).T.to_string().replace("\n", "\n    "))
    for c in ("iid_p0.3", "gilbert_p0.3_b3"):
        e1, s1 = boot_mean(x, c)
        e2, s2 = boot_mean(x, c, cluster="block")
        print(f"    {c}: site clusters {fmt(e1, s1)}; site x month blocks {fmt(e2, s2)}")
        out.append({"Q": 6, "channel": c, "contrast": "rec_code, site x month block bootstrap", "estimate": e2,
                    "lo": s2[0], "hi": s2[1], "n_days": len(x), "n_sites": x.site.nunique(), "source": "block bootstrap"})
    return pd.DataFrame(out)


def rq2_rq4(tag, frozen_T=None):
    full = pd.read_csv(f"results/{tag}/cohort_exact.csv", dtype={"site": str})
    code = full[full.design == "rec_code"]
    # Q = 96 from the record size (exact)
    q24 = code[code.Q == 24].copy()
    q96 = q24.assign(Q=96, **{rr.ch_name(c): [ce.p_code(int(D1), 96, c) for D1 in q24.D1] for c in rr.CHANNELS})
    code = pd.concat([code, q96])
    out, sz = [], []
    print("\nRQ2 (daily record-first code; a day is certified within 7 days iff its block decodes; exact):")
    for c in ("iid_p0.3", "gilbert_p0.3_b3"):
        for Q in TIERS:
            site = code[code.Q == Q].groupby("site")[c].mean()
            est, lohi = boot_site_share(site, 0.9)
            out.append({"channel": c, "Q": Q, "sites_G7_ge_0.9": int((site >= 0.9).sum()), "n_sites": len(site),
                        "share": est, "lo": lohi[0], "hi": lohi[1]})
            print(f"  {c:16s} Q {Q:2d}: {int((site >= 0.9).sum())}/{len(site)} sites {fmt(est, lohi, pct=True)}")
    # RQ4: 28-day pilot starting in each month; hindsight tier from the other days
    print("\nRQ4 (pilot of 28 days starting in each month; threshold T tuned on even sites; exact):")
    sites = sorted(code.site.unique())
    for c in ("iid_p0.3", "gilbert_p0.3_b3"):
        g = {s: code[code.site == s] for s in sites}
        cases = []
        for s in sites:
            days = g[s].day.unique()
            for m in range(1, 13):
                first = g[s][g[s].month == m].day.min() if (g[s].month == m).any() else None
                if first is None:
                    continue
                pilot = (g[s].day >= first) & (g[s].day < first + 28)
                if g[s][pilot].day.nunique() < 14 or g[s][~pilot].day.nunique() < 28:
                    continue
                pg = g[s][pilot].groupby("Q")[c].mean()
                rg = g[s][~pilot].groupby("Q")[c].mean()
                cases.append({"site": s, "month": m, "pilot": pg.to_dict(), "rest": rg.to_dict(), "days": len(days)})

        def tier(d, thr):
            ok = [q for q in TIERS if d.get(q, 0) >= thr]
            return min(ok) if ok else TIERS[-1]
        ti = {q: i for i, q in enumerate(TIERS)}

        def evaluate(cs, T):
            dd = np.array([ti[tier(x["pilot"], T)] - ti[tier(x["rest"], 0.9)] for x in cs])
            return dd
        if frozen_T is None:          # development: tune T on even sites, report odd sites
            tune = [x for x in cases if sites.index(x["site"]) % 2 == 0]
            test = [x for x in cases if sites.index(x["site"]) % 2 == 1]
            best = max((0.9, 0.95, 0.99, 1.0),
                       key=lambda T: (lambda d: min((d >= 0).mean(), 0.8) + (d <= 1).mean())(evaluate(tune, T)))
        else:                         # confirmation: threshold frozen from development, all sites reported
            test, best = cases, frozen_T[c]
        dd = evaluate(test, best)
        tdf = pd.DataFrame([{"site": x["site"], "month": x["month"], "suff": float(v >= 0), "over1": float(v <= 1)}
                            for x, v in zip(test, dd)])
        e1, s1 = boot_mean(tdf, "suff")
        e2, s2 = boot_mean(tdf, "over1")
        by_m = tdf.groupby("month").suff.mean()
        print(f"  planning {c}: T = {best}; {len(tdf)} site-pilots at {tdf.site.nunique()} test sites: sufficient "
              f"{fmt(e1, s1, pct=True)}, over-provision <= 1 tier {fmt(e2, s2, pct=True)}; sufficient by pilot month: "
              f"min {by_m.min():.2f} ({int(by_m.idxmin())}), max {by_m.max():.2f}")
        sz.append({"planning_channel": c, "T": best, "pilots": len(tdf), "test_sites": tdf.site.nunique(),
                   "sufficient": e1, "suff_lo": s1[0], "suff_hi": s1[1], "over1": e2, "over1_lo": s2[0],
                   "over1_hi": s2[1], "suff_month_min": float(by_m.min()), "suff_month_max": float(by_m.max())})
    return pd.DataFrame(out), pd.DataFrame(sz)


def env(tag):
    d = pd.read_csv(f"results/{tag}/env_days.csv", dtype={"site": str})
    out = []
    print("\nStep 8 contrasts (Q = 6; rates pooled over days; paired by day; site-clustered intervals):")
    for cond in ("perfect", "iid_p0.3"):
        w = d[(d.Q == 6) & (d.cond == cond)].pivot_table(index=["site", "day"], columns="design",
                                                           values=["DO_FN", "DO_true", "DO_decided", "EC_FN", "EC_true",
                                                                   "pH_FN", "pH_true"])
        x = pd.DataFrame({"site": w.index.get_level_values(0)})
        for k in ("DO", "pH", "EC"):
            for other in ("every_k", "tag"):
                x["_n"] = (w[(f"{k}_FN", "rec_code")] - w[(f"{k}_FN", other)]).to_numpy()
                x["_d"] = w[(f"{k}_true", "rec_code")].to_numpy()
                est, lohi = boot_ratio(x, "_n", "_d")
                out.append({"cond": cond, "outcome": f"{k} miss rate, code - {other}", "estimate": est, "lo": lohi[0],
                            "hi": lohi[1], "events": int(x._d.sum()), "n_days": len(x)})
        x["_d"] = (w[("DO_decided", "rec_code")] - w[("DO_decided", "every_k")]).to_numpy()
        est, lohi = boot_mean(x, "_d")
        out.append({"cond": cond, "outcome": "DO decided share, code - every_k", "estimate": est, "lo": lohi[0],
                    "hi": lohi[1], "events": np.nan, "n_days": len(x)})
    o = pd.DataFrame(out)
    print(o.round(3).to_string(index=False))
    return o


def multiday(tag):
    m = pd.read_csv(f"results/{tag}/multiday.csv", dtype={"site": str, "variant": str})
    sites = sorted(m.site.unique())
    test = set(sites[1::2])
    out = []
    print("\nStep 7 contrast (Q = 6, test sites; G7 pooled over four-parameter days; paired by site):")
    for c in ("iid_p0.3", "gilbert_p0.3_b3", "gilbert_p0.3_b6"):
        a = m[(m.Q == 6) & (m.channel == c) & (m.design == "daily_rec") & m.site.isin(test)].set_index("site")
        b = m[(m.Q == 6) & (m.channel == c) & (m.design == "rep_multi_rec") & m.site.isin(test)].set_index("site")
        x = pd.DataFrame({"site": a.index, "_n": (a.G7 - b.G7.reindex(a.index)).to_numpy() * a.n_four.to_numpy(),
                          "_w": a.n_four.to_numpy()})
        est, lohi = boot_ratio(x, "_n", "_w")
        out.append({"channel": c, "contrast": "G7 daily code - 7-day rotation", "estimate": est, "lo": lohi[0],
                    "hi": lohi[1], "n_sites": len(x)})
        print(f"  {c:16s} {fmt(est, lohi)} ({len(x)} sites)")
    return pd.DataFrame(out)


def main():
    """python -I src/p3/stats.py <tag> [confirm]: confirm mode uses every sampled day, the RQ4 thresholds frozen
    from development (results/dev/stats_rq4.csv), and skips the development-only multi-day contrast."""
    tag = sys.argv[1]
    confirm = len(sys.argv) > 2 and sys.argv[2] == "confirm"
    os.makedirs(f"results/{tag}", exist_ok=True)
    rq1(tag).to_csv(f"results/{tag}/stats_rq1.csv", index=False)
    rq3(tag, None if confirm else "test").to_csv(f"results/{tag}/stats_rq3.csv", index=False)
    frozen = None
    if confirm:
        r = pd.read_csv("results/dev/stats_rq4.csv")
        frozen = dict(zip(r.planning_channel, r["T"]))
    a, b = rq2_rq4(tag, frozen)
    a.to_csv(f"results/{tag}/stats_rq2.csv", index=False)
    b.to_csv(f"results/{tag}/stats_rq4.csv", index=False)
    env(tag).to_csv(f"results/{tag}/stats_env.csv", index=False)
    if not confirm:
        multiday(tag).to_csv(f"results/{tag}/stats_multiday.csv", index=False)


if __name__ == "__main__":
    main()
