"""Evaluation of Step 4 (src/p3/proto_base.py): baselines against the witness designs, with the pre-registered criteria
(docs/REVISION2_PLAN.md, "Step 4") evaluated at Q = 6 for both loss models.
Memory-lean: each site file is aggregated on its own (sum and count per condition, design, and metric), then pooled; the
site-clustered bootstrap resamples the per-site aggregates. Metrics (pooled day-queries of DO, pH, conductance, and 7DADM
windows): hard_cfg = hard cases at the configured thresholds; hard_alt = hard cases at the two alternative threshold sets
pooled; all_cfg = all cases at the configured thresholds; rec = whole record recovered.
Run from Paper3/: python -I src/p3/proto_base_eval.py <tag> <Q> [Q2 ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

B = 1000
NAMES = {"rec": "record only", "heur": "3b rule generalised", "ex1": "exact, lambda 1", "tight50": "tolerance x 0.5",
         "tight25": "tolerance x 0.25", "sod_once": "send-on-delta, once", "sod_mds": "send-on-delta, coded",
         "flags": "decision flags"}
KINDS = ("do", "ph", "ec", "win7")
SCEN = ("cfg", "alt1", "alt2")
KEYS = ("cond", "design")


def site_aggregate(path, meta_path):
    d = pd.read_csv(path, dtype={"site": str})
    m = pd.read_csv(meta_path, dtype={"site": str})
    site = d.site.iloc[0] if len(d) else os.path.basename(path)[:-4]
    out = []
    day = d[d.kind == "day"].groupby(list(KEYS)).rec_full.agg(["sum", "count"]).reset_index()
    day["metric"] = "rec"
    out.append(day)
    wrong = d.groupby(list(KEYS)).wrong.max().reset_index().assign(metric="wrong", sum=lambda x: x.wrong, count=1).drop(columns="wrong")
    out.append(wrong)
    for kind in KINDS:
        z = d[d.kind == kind]
        for v in SCEN:
            hard = m[["site", "day", f"hard_{kind}_{v}"]].rename(columns={f"hard_{kind}_{v}": "hard"})
            t = z[["site", "day", "cond", "design", f"dc_{v}"]].rename(columns={f"dc_{v}": "dc"}).merge(hard, on=["site", "day"])
            t = t[t.dc.notna() & t.hard.notna()]
            t["hard"] = t.hard.astype(bool)
            if v == "cfg":
                a = t.groupby(list(KEYS)).dc.agg(["sum", "count"]).reset_index().assign(metric="all_cfg")
                h = t[t.hard].groupby(list(KEYS)).dc.agg(["sum", "count"]).reset_index().assign(metric="hard_cfg")
                out += [a, h]
            else:
                h = t[t.hard].groupby(list(KEYS)).dc.agg(["sum", "count"]).reset_index().assign(metric="hard_alt")
                out.append(h)
    r = pd.concat(out)
    r["site"] = site
    return r


def load_agg(tag, Q, subdir="proto_b"):
    parts = []
    for f in sorted(glob.glob(f"results/{tag}/{subdir}/*_Q{Q}.csv")):
        if f.endswith("_meta.csv") or os.path.getsize(f) < 10:
            continue
        parts.append(site_aggregate(f, f.replace(f"_Q{Q}.csv", f"_Q{Q}_meta.csv")))
    a = pd.concat(parts)
    g = a.groupby(["site", "cond", "design", "metric"])[["sum", "count"]].sum().reset_index()
    return g


def pooled_ci(g, cond, design, metric, rng, idx_cache={}):
    z = g[(g.cond == cond) & (g.design == design) & (g.metric == metric)]
    s, c = z["sum"].to_numpy(), z["count"].to_numpy()
    if len(s) == 0 or c.sum() == 0:
        return (np.nan, np.nan, np.nan)
    idx = rng.integers(0, len(s), (B, len(s)))
    bs = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
    return s.sum() / c.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def fmt(t):
    return f"{t[0]:.3f} ({t[1]:.3f} to {t[2]:.3f})"


def main():
    tag = sys.argv[1]
    rng = np.random.default_rng(21)
    for Q in map(int, sys.argv[2:]):
        g = load_agg(tag, Q)
        meta = pd.concat([pd.read_csv(f, usecols=["V_pla", "V_sod", "V_t50", "V_t25"])
                          for f in glob.glob(f"results/{tag}/proto_b/*_Q{Q}_meta.csv") if os.path.getsize(f) > 10])
        wrong = g[g.metric == "wrong"]["sum"].max()
        print(f"\n## Q = {Q}: {g.site.nunique()} sites; wrong decisions max {wrong:.3f}")
        print("values per day: " + ", ".join(f"{k} {meta[k].mean():.1f}" for k in meta.columns))
        for cond in ("iid_p0.3", "gilbert_p0.3_b3"):
            rows, stat = [], {}
            for dn, nm in NAMES.items():
                rc, hc, ha, ac = (pooled_ci(g, cond, dn, mt, rng) for mt in ("rec", "hard_cfg", "hard_alt", "all_cfg"))
                stat[dn] = {"rec": rc[0], "hc": hc[0], "ha": ha[0]}
                rows.append({"design": nm, "record recovered": fmt(rc), "hard, configured": fmt(hc),
                             "hard, alternative thresholds": fmt(ha), "all, configured": fmt(ac)})
            print(f"\n### {cond}\n" + pd.DataFrame(rows).to_markdown(index=False))
            if Q == 6:
                print(f"\nCriteria at Q = 6, {cond}:")
                for x in ("heur", "ex1"):
                    for b in ("sod_once", "sod_mds", "tight50", "tight25"):
                        dom = stat[b]["rec"] >= stat[x]["rec"] - 0.005 and stat[b]["hc"] >= stat[x]["hc"] + 0.005
                        print(f"  (2) {b} dominates {x}: {dom}")
                    gap = stat[x]["ha"] - stat["flags"]["ha"]
                    print(f"  (3) {x} minus flags on alternative thresholds: {gap:+.3f} (needs at least +0.100: {gap >= 0.10})")
                    print(f"  (4) flags minus {x} on configured thresholds: {stat['flags']['hc'] - stat[x]['hc']:+.3f}; "
                          f"record {stat['flags']['rec'] - stat[x]['rec']:+.3f}")


if __name__ == "__main__":
    main()
