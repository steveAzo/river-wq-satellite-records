"""Robustness of the confirmation statistics (outside review, point 9). Post hoc re-analysis of the per-site byte-level outputs of the
frozen run (results/<tag>/byte4); no new simulation. For H2, H3, and H4 in all four conditions it reports:
  - the pooled contrast with 10,000 site-clustered resamples (the run used 1,000);
  - equal-site weighting: the mean over sites of each site's own contrast, with a site bootstrap;
  - the macro average over the four query kinds (each kind weighted equally; hard-case contrasts only);
  - the per-site distribution: share of sites with a positive (H2, H3) or negative (H4) contrast, and the 5th, 50th, 95th percentiles.
Writes results/<tag>/robust_stats.csv and draft4/figs/sites.pdf (per-site H2 and H3 contrasts at Q = 6, independent loss).
Run from Paper3/: python -I -W ignore paper_tools/robust_stats.py <tag>"""
import glob
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "src")
from p3 import proto_base_eval as pe  # noqa: E402

TAG = sys.argv[1] if len(sys.argv) > 1 else "confirm4"
B = 10000
CONDS = ("iid_p0.3", "gilbert_p0.3_b3")
TESTS = {"H2": ("heur", "flagsrec", "hard_alt"), "H3": ("heur", "rec", "hard_alt"), "H4": ("heur", "rec", "rec")}
KIND_ALT = {"H2": ("heur", "flagsrec"), "H3": ("heur", "rec")}


def per_site(g, cond, d, metric):
    z = g[(g.cond == cond) & (g.design == d) & (g.metric == metric)].set_index("site")
    return z["sum"], z["count"]


def kind_sums(Q):
    """Per site, cond, design, kind: sums and counts of hard cases at the alternative thresholds."""
    parts = []
    for f in sorted(glob.glob(f"results/{TAG}/byte4/*_Q{Q}.csv")):
        if f.endswith("_meta.csv"):
            continue
        d = pd.read_csv(f, dtype={"site": str})
        m = pd.read_csv(f.replace(f"_Q{Q}.csv", f"_Q{Q}_meta.csv"), dtype={"site": str})
        for kind in pe.KINDS:
            for v in ("alt1", "alt2"):
                h = m[["site", "day", f"hard_{kind}_{v}"]].rename(columns={f"hard_{kind}_{v}": "hard"})
                t = d[d.kind == kind][["site", "day", "cond", "design", f"dc_{v}"]].rename(columns={f"dc_{v}": "dc"}).merge(h, on=["site", "day"])
                t = t[t.dc.notna() & t.hard.notna()]
                t = t[t.hard.astype(bool)]
                parts.append(t.groupby(["site", "cond", "design"]).dc.agg(["sum", "count"]).reset_index().assign(kind=kind))
    return pd.concat(parts).groupby(["site", "cond", "design", "kind"])[["sum", "count"]].sum().reset_index()


rows, site_effects = [], {}
for Q in (6, 12):
    g = pe.load_agg(TAG, Q, "byte4")
    K = kind_sums(Q)
    sites = sorted(g.site.unique())
    rng = np.random.default_rng(20261111 + Q)
    idx = rng.integers(0, len(sites), (B, len(sites)))
    for cond in CONDS:
        for h, (a, b, metric) in TESTS.items():
            sa, ca = (x.reindex(sites).to_numpy(float) for x in per_site(g, cond, a, metric))
            sb, cb = (x.reindex(sites).to_numpy(float) for x in per_site(g, cond, b, metric))
            pooled = sa.sum() / ca.sum() - sb.sum() / cb.sum()
            bs = sa[idx].sum(1) / ca[idx].sum(1) - sb[idx].sum(1) / cb[idx].sum(1)
            eff = sa / ca - sb / cb                          # each site's own contrast
            ok = np.isfinite(eff)
            e = eff[ok]
            be = e[rng.integers(0, len(e), (B, len(e)))].mean(1)
            r = {"Q": Q, "cond": cond, "test": h, "pooled": pooled, "pooled_lo": np.percentile(bs, 2.5), "pooled_hi": np.percentile(bs, 97.5),
                 "equal_site": e.mean(), "equal_site_lo": np.percentile(be, 2.5), "equal_site_hi": np.percentile(be, 97.5),
                 "sites": len(e), "share_favourable": float(np.mean(e > 0) if h != "H4" else np.mean(e < 0)),
                 "p05": np.percentile(e, 5), "p50": np.percentile(e, 50), "p95": np.percentile(e, 95)}
            if h in KIND_ALT:
                ka, kb = KIND_ALT[h]
                lv = []
                kidx = {}
                for kind in pe.KINDS:
                    za = K[(K.cond == cond) & (K.design == ka) & (K.kind == kind)].set_index("site").reindex(sites)
                    zb = K[(K.cond == cond) & (K.design == kb) & (K.kind == kind)].set_index("site").reindex(sites)
                    kidx[kind] = (za["sum"].fillna(0).to_numpy(), za["count"].fillna(0).to_numpy(), zb["sum"].fillna(0).to_numpy(), zb["count"].fillna(0).to_numpy())
                macro = np.mean([k[0].sum() / k[1].sum() - k[2].sum() / k[3].sum() for k in kidx.values()])
                mb = np.mean([k[0][idx].sum(1) / np.maximum(k[1][idx].sum(1), 1) - k[2][idx].sum(1) / np.maximum(k[3][idx].sum(1), 1) for k in kidx.values()], axis=0)
                r.update({"macro_kinds": macro, "macro_lo": np.percentile(mb, 2.5), "macro_hi": np.percentile(mb, 97.5)})
            rows.append(r)
            if Q == 6 and cond == "iid_p0.3" and h in ("H2", "H3"):
                site_effects[h] = e
out = pd.DataFrame(rows)
out.to_csv(f"results/{TAG}/robust_stats.csv", index=False)
pd.set_option("display.width", 250)
print(out.round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(6.4, 2.4))
for i, (h, lab) in enumerate((("H2", "3b rule minus flags plus record"), ("H3", "3b rule minus record only"))):
    e = np.sort(site_effects[h])
    y = np.full(len(e), 1 - i) + np.linspace(-0.18, 0.18, len(e))
    ax.scatter(e, y, s=14, color="#2a78d6", edgecolor="white", linewidth=0.5, zorder=3)
    ax.plot([np.median(e)] * 2, [1 - i - 0.3, 1 - i + 0.3], color="#0b0b0b", lw=1.2)
ax.axvline(0, color="#8a8984", lw=0.8)
ax.axvline(0.10, color="#eb6834", lw=1.0, ls=(0, (2, 1.5)))
ax.set_yticks([1, 0])
ax.set_yticklabels(["3b rule minus\nflags plus record", "3b rule minus\nrecord only"], fontsize=8)
ax.set_xlabel("Per-site contrast, hard cases at unconfigured thresholds (Q = 6, independent loss)", fontsize=8)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#e6e5e1", lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig("draft4/figs/sites.pdf")
fig.savefig("draft4/figs/sites.png", dpi=300)
print("figure: draft4/figs/sites.pdf")
