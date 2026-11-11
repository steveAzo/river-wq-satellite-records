"""Summaries of the POST HOC exploratory runs (exploratory/explore4.py and run_baselines.py) for the response to the outside review.
Writes exploratory/out/summary_<tag>.md, draft4 tables (explore_loss.tex, explore_util.tex, explore_r.tex, explore_base.tex) and the figure
draft4/figs/thresholds.pdf (threshold sweep; the cohort in colour, the two development years in grey).
Run from Paper3/: python -I -W ignore exploratory/summarise4.py [tag ...]   (default: rehearsal4_2023 rehearsal4v2 confirm4)"""
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from p3 import proto_base_eval as pe  # noqa: E402

TAGS = sys.argv[1:] or ["rehearsal4_2023", "rehearsal4v2", "confirm4"]
LABEL = {"rehearsal4_2023": "2023 (dev.)", "rehearsal4v2": "2024 (dev.)", "confirm4": "2022 (cohort)"}
CONDS = ["iid_0.1", "iid_0.3", "iid_0.5", "gil_0.3_b3", "gil_0.3_b6", "gil_0.5_b3"]
CLAB = {"iid_0.1": "ind. 0.1", "iid_0.3": "ind. 0.3", "iid_0.5": "ind. 0.5", "gil_0.3_b3": "Gil. 0.3, b 3", "gil_0.3_b6": "Gil. 0.3, b 6", "gil_0.5_b3": "Gil. 0.5, b 3"}
KINDS = ["do", "ph_low", "ph_high", "ec", "win7"]
KLAB = {"do": "Dissolved oxygen\nbelow (mg/L)", "ph_low": "pH below", "ph_high": "pH above", "ec": "Conductance change\nabove (per hour)", "win7": "7DADM above\n(°C)"}
CFG = {"do": 5.0, "ph_low": 6.5, "ph_high": 9.0, "ec": 0.10, "win7": 20.0}
B = 2000


def load(tag):
    fs = sorted(glob.glob(os.path.join(HERE, "out", tag, "*.csv")))
    if not fs:
        return None
    d = pd.concat([pd.read_csv(f, dtype={"site": str, "theta": str, "subset": str}) for f in fs])
    d["theta"] = d["theta"].fillna("")
    d["subset"] = d["subset"].fillna("")
    return d


def boot_diff(z, a, b, seed):
    """Site-clustered contrast of pooled shares (design a minus b) from per-site sums and counts."""
    sa = z[z.design == a].groupby("site")[["sum", "count"]].sum()
    sb = z[z.design == b].groupby("site")[["sum", "count"]].sum()
    sites = sorted(set(sa.index) & set(sb.index))
    sa, sb = sa.loc[sites].to_numpy(float), sb.loc[sites].to_numpy(float)
    pt = sa[:, 0].sum() / sa[:, 1].sum() - sb[:, 0].sum() / sb[:, 1].sum()
    idx = np.random.default_rng(seed).integers(0, len(sites), (B, len(sites)))
    bs = sa[idx, 0].sum(1) / sa[idx, 1].sum(1) - sb[idx, 0].sum(1) / sb[idx, 1].sum(1)
    return pt, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def unconf(d, Q, cond):
    """Hard cases at the two alternative threshold sets of the study (the H2/H3 population, without 7DADM sets other than 19 and 21)."""
    alt = {"do": ("4.5", "5.5"), "ph_low": ("6.3", "6.7"), "ph_high": ("9.2", "8.8"), "ec": ("0.2", "0.05"), "win7": ("21.0", "19.0")}
    m = pd.concat([d[(d.Q == Q) & (d.cond == cond) & (d.metric == k) & (d.subset == "hard") & d.theta.isin(v)] for k, v in alt.items()])
    return m


def fmt(t):
    return f"{t[0]:+.3f} ({t[1]:+.3f} to {t[2]:+.3f})"


def main():
    data = {t: load(t) for t in TAGS}
    data = {t: d for t, d in data.items() if d is not None}
    lines, loss_rows, util_rows, r_rows = [], [], [], []
    for tag, d in data.items():
        lines.append(f"\n# {tag}: {d.site.nunique()} sites; wrong certain decisions (all non-R metrics): {int(d[~d.metric.str.startswith('R_')].wrong.sum())}")
        for Q in (6, 12):
            for cond in CONDS:
                full = d[(d.Q == Q) & (d.cond == cond) & (d.metric == "rec_full")]
                if full.empty:
                    continue
                u = unconf(d, Q, cond)
                h2 = boot_diff(u, "heur", "flagsrec", 1)
                h3 = boot_diff(u, "heur", "rec", 2)
                h4 = boot_diff(full, "heur", "rec", 3)
                lines.append(f"Q={Q} {cond:11s} H2-like {fmt(h2)} | H3-like {fmt(h3)} | H4-like {fmt(h4)}")
                loss_rows.append((tag, Q, cond, h2, h3, h4))
                for dn in ("rec", "heur", "flagsrec"):
                    cs = d[(d.Q == Q) & (d.cond == cond) & (d.metric == "cert_share") & (d.design == dn)]
                    a = cs[cs.subset == "all"]
                    nf = cs[cs.subset == "not_full"]
                    fr = full[full.design == dn]
                    util_rows.append((tag, Q, cond, dn, fr["sum"].sum() / fr["count"].sum(), a["sum"].sum() / a["count"].sum(),
                                      nf["sum"].sum() / max(nf["count"].sum(), 1), nf["count"].sum() / max(a["count"].sum(), 1)))
        rr = d[d.metric.str.startswith("R_")].groupby(["design", "metric"])[["sum", "count", "wrong"]].sum()
        for (dn, mt), r in rr.iterrows():
            r_rows.append((tag, dn, mt[2:], r["sum"] / r["count"], int(r["wrong"]), int(r["count"])))
            lines.append(f"R {dn:4s} {mt:11s} correct {r['sum'] / r['count']:.4f}  wrong {int(r['wrong'])}  of {int(r['count'])}")
    open(os.path.join(HERE, "out", "summary.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    write_tables(loss_rows, util_rows, r_rows)
    fig_thresholds(data)
    base_summary()


def write_tables(loss_rows, util_rows, r_rows):
    os.makedirs(os.path.join(ROOT, "draft4", "tables"), exist_ok=True)
    m = lambda x: f"{x:+.3f}".replace("-", "$-$")
    rows = []
    for tag, Q, cond, h2, h3, h4 in loss_rows:
        rows.append(f"{LABEL[tag]} & {Q} & {CLAB[cond]} & {m(h2[0])} ({m(h2[1])}) & {m(h3[0])} ({m(h3[1])}) & {m(h4[0])} ({m(h4[1])}) \\\\")
    open(os.path.join(ROOT, "draft4", "tables", "explore_loss.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    rows = []
    for tag, Q, cond, dn, full, cs, csnf, share_nf in util_rows:
        if cond in ("iid_0.3", "gil_0.3_b3", "iid_0.5"):
            name = {"rec": "Record only", "heur": "3b rule", "flagsrec": "Flags plus record"}[dn]
            rows.append(f"{LABEL[tag]} & {Q} & {CLAB[cond]} & {name} & {full:.3f} & {cs:.3f} & {csnf:.3f} \\\\")
    open(os.path.join(ROOT, "draft4", "tables", "explore_util.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    rows = []
    for tag, dn, var, share, wrong, n in r_rows:
        name = {"rec": "Record only", "heur": "3b rule"}[dn]
        rows.append(f"{LABEL[tag]} & {name} & {var} & {share:.4f} & {wrong:,} of {n:,} \\\\")
    open(os.path.join(ROOT, "draft4", "tables", "explore_r.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")


def fig_thresholds(data):
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 8,
                         "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    col = {"rec": "#8a8984", "heur": "#2a78d6", "flagsrec": "#1baf7a"}
    name = {"rec": "Record only", "heur": "3b rule", "flagsrec": "Flags plus record"}
    fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.4), sharey=True)
    for ax, k in zip(axes, KINDS):
        for tag, d in data.items():
            z = d[(d.Q == 6) & (d.cond == "iid_0.3") & (d.metric == k) & (d.subset == "hard")]
            if z.empty:
                continue
            for dn in ("rec", "heur", "flagsrec"):
                g = z[z.design == dn].groupby("theta")[["sum", "count"]].sum()
                th = np.array([float(x) for x in g.index])
                o = np.argsort(th)
                y = (g["sum"] / g["count"]).to_numpy()[o]
                cohort = tag == "confirm4"
                ax.plot(th[o], y, color=col[dn] if cohort else "#d0cfca", lw=1.6 if cohort else 0.8, marker="o" if cohort else None,
                        ms=2.5, zorder=3 if cohort else 1, label=name[dn] if cohort else None)
        ax.axvline(CFG[k], color="#eb6834", lw=0.8, ls=(0, (2, 1.5)))
        ax.set_title(KLAB[k], fontsize=7.5)
        ax.grid(color="#e6e5e1", lw=0.5)
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("Hard cases decided correctly")
    axes[0].legend(frameon=False, fontsize=6.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "draft4", "figs", "thresholds.pdf"))
    fig.savefig(os.path.join(ROOT, "draft4", "figs", "thresholds.png"), dpi=300)
    plt.close(fig)


def base_summary():
    rows, lines = [], ["\n# Baselines on the final frame (slot model, 4 slots; POST HOC)"]
    for tag in TAGS:
        od = os.path.join(HERE, "out", f"{tag}_baselines")
        fs = [f for f in sorted(glob.glob(os.path.join(od, "*_Q6.csv")))]
        if not fs:
            continue
        for Q in (6, 12):
            parts = [pe.site_aggregate(f.replace("_Q6", f"_Q{Q}"), f.replace("_Q6.csv", f"_Q{Q}_meta.csv")) for f in fs
                     if os.path.exists(f.replace("_Q6", f"_Q{Q}"))]
            g = pd.concat(parts).groupby(["site", "cond", "design", "metric"])[["sum", "count"]].sum().reset_index()
            for cond in ("iid_p0.3", "gilbert_p0.3_b3"):
                for dn in ("rec", "heur", "tight50", "sod_mds"):
                    lv = []
                    for mt in ("rec", "hard_cfg", "hard_alt"):
                        z = g[(g.cond == cond) & (g.design == dn) & (g.metric == mt)]
                        lv.append(z["sum"].sum() / max(z["count"].sum(), 1))
                    nm = {"rec": "Record only", "heur": "3b rule (slot model)", "tight50": "Tolerance x 0.5", "sod_mds": "Send-on-delta, coded"}[dn]
                    lc = "ind." if cond.startswith("iid") else "Gil."
                    rows.append(f"{LABEL[tag]} & {Q} & {lc} & {nm} & {lv[0]:.3f} & {lv[1]:.3f} & {lv[2]:.3f} \\\\")
                    lines.append(f"{tag} Q={Q} {cond} {dn:8s} rec {lv[0]:.3f} hard_cfg {lv[1]:.3f} hard_alt {lv[2]:.3f}")
    if rows:
        open(os.path.join(ROOT, "draft4", "tables", "explore_base.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
