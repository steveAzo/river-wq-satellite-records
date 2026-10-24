"""Figures for the Paper 3 manuscript (vector PDF, greyscale-safe: every series has its own marker and
line style and is labelled directly). Palette: the validated categorical order of the dataviz reference
(blue, orange, aqua, yellow, magenta); validator: all checks pass, contrast relief = direct labels.
Run from Paper3/: python -I src/paper/make_figures.py
"""
import os
import sys

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "src")
from p3 import pla  # noqa: E402
from p3.data import load_site  # noqa: E402

OUT = "draft/figs"
os.makedirs(OUT, exist_ok=True)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
DESIGN = {  # name -> (label, colour, marker, linestyle)
    "mds": ("Guaranteed set + erasure code", "#2a78d6", "o", "-"),
    "repeat": ("Guaranteed set + repetition", "#eb6834", "s", "--"),
    "srdl_style": ("Tag practice", "#1baf7a", "^", "-."),
    "reliable_opt": ("Reliable-link design", "#eda100", "D", ":"),
    "raw_periodic": ("Every k-th reading", "#e87ba4", "v", (0, (5, 2, 1, 2))),
}
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"], "mathtext.fontset": "stix",
    "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.5, "lines.markersize": 5,
    "legend.frameon": False, "pdf.fonttype": 42,
})


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Fig. example day
def fig_example():
    # illustrative day (development data, 2023): the first July site-day, in site order, whose DO record
    # needs 6-12 values (a day with movement; most days need far fewer, see the need figure)
    n23 = pd.read_csv("results/dev/need_excellent.csv", dtype={"site": str})
    pick = n23[(pd.to_datetime(n23.day).dt.month == 7) & n23.v_DO.between(6, 12)].sort_values(["site", "day"]).iloc[0]
    days = load_site(f"data/clean/usgs/{pick.site}.csv", "excellent")
    for sd in days:
        if str(sd.day.date()) != pick.day:
            continue
        p = sd.params.index("DO")
        x, a, tol = sd.X[p], sd.anchor[p], sd.tol[p]
        seg, tail = pla.tables(x, a, tol)
        kept = pla.min_set(seg, tail, 1.0)
        if 6 <= len(kept) <= 12:
            break
    k = len(kept)
    print("example day:", sd.site, sd.day.date())
    stride = int(np.ceil(sd.n / k))
    periodic = list(range(sd.n - 1, -1, -stride))[::-1]
    hours = np.arange(sd.n) * sd.step_min / 60
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4), sharey=True)
    panels = ((axes[0], kept, f"(a) Guaranteed set, {k} values", "#2a78d6", "-", "Reconstruction from the guaranteed set"),
              (axes[1], periodic, f"(b) Evenly spaced readings, {len(periodic)} values", "#e87ba4", "--",
               "Reconstruction from evenly spaced readings"))
    handles = []
    for ax, sel, title, c, ls, lab in panels:
        rec = pla.reconstruct_one(x, a, sel)
        band = ax.fill_between(hours, x - tol, x + tol, color="#d6e4f5", lw=0, label="Tolerance band")
        meas, = ax.plot(hours, x, color=INK, lw=1.0, label="Measured readings")
        line, = ax.plot(hours, rec, color=c, lw=1.5, ls=ls, marker="o", ms=4, mec="white", mew=0.6,
                        markevery=list(sel), label=lab)
        worst = np.max(np.abs(x - rec) / tol)
        ax.set_title(title, fontsize=8, color=INK)
        ax.text(0.97, 0.95, f"Worst error: {worst:.1f} $\\times$ tolerance", transform=ax.transAxes, ha="right", va="top",
                fontsize=7.5, color=INK)
        ax.set_xlabel("Hour of day")
        ax.set_xlim(0, 24)
        handles = handles or [band, meas]
        handles.append(line)
    axes[0].set_ylabel("Dissolved oxygen (mg/L)")
    # one legend for both panels, below the axes, so that no data are covered; markers are the transmitted values
    fig.legend(handles, [h.get_label() for h in handles], loc="upper center", ncol=2, fontsize=7.5,
               bbox_to_anchor=(0.5, -0.05))
    save(fig, "example_day")
    return k, len(periodic)


# ---------------------------------------------------------------- Fig. need ECDF
def fig_need():
    n23 = pd.read_csv("results/dev/need_excellent.csv")
    n24 = pd.read_csv("results/confirm/need_excellent.csv")
    lc = pd.read_csv("results/lowcost/need_excellent.csv")
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    series = [("USGS 2023 (development)", 3 * n23["values"], "#2a78d6", "-"),
              ("USGS 2024 (confirmation)", 3 * n24["values"], "#eb6834", "--"),
              ("InWaterSense (Kosovo)", 3 * lc[lc.site == "InWaterSense"]["values"], "#1baf7a", "-."),
              ("Weija (Ghana)", 3 * lc[lc.site == "Weija"]["values"], "#6250d6", ":")]
    for label, b, c, ls in series:
        v = np.sort(np.maximum(b.to_numpy(float), 1))
        y = np.arange(1, len(v) + 1) / len(v)
        ax.step(v, y, where="post", color=c, ls=ls, label=label)
    for msgs, txt in ((1, "1 msg"), (6, "6 msg"), (12, "12 msg")):
        ax.axvline(21 * msgs, color=MUTED, lw=0.8, ls=(0, (1, 2)))
        # labels where no curve passes: top for 1 message, bottom for 6 and 12
        ax.text(21 * msgs * 1.06, 0.97 if msgs == 1 else 0.03, txt, color=MUTED, fontsize=7, rotation=90,
                va="top" if msgs == 1 else "bottom")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel("Bytes per day for a guaranteed record (3 B per value)")
    ax.set_ylabel("Share of site-days")
    ax.set_ylim(0, 1.01)
    ax.legend(loc="upper left", fontsize=7)
    save(fig, "need_ecdf")


# ---------------------------------------------------------------- Fig. monthly need
def fig_month():
    n24 = pd.read_csv("results/confirm/need_excellent.csv")
    n24["b"] = 3 * n24["values"]
    n24["m"] = pd.to_datetime(n24.day).dt.month
    q = n24.groupby("m").b.quantile([0.25, 0.5, 0.75, 0.9]).unstack()
    fig, ax = plt.subplots(figsize=(4.6, 2.4))
    ax.plot(q.index, q[0.9], "--s", color="#eb6834", label="90th percentile")
    ax.plot(q.index, q[0.5], "-o", color="#2a78d6", label="Median")
    ax.fill_between(q.index, q[0.25], q[0.75], color="#d6e4f5", lw=0, label="Interquartile range")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.set_xlim(0.7, 12.3)
    ax.set_ylim(0, 1.25 * q[0.9].max())
    ax.legend(loc="upper left", fontsize=7, ncol=3)
    ax.set_ylabel("Bytes per day")
    ax.set_xlabel("Month (2024)")
    save(fig, "need_month")


# ---------------------------------------------------------------- Fig. delivery designs
def fig_designs():
    d = pd.read_csv("results/confirm/usgs2024_rq3.csv")
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.4), sharex=True, sharey=True)
    for ax, (Q, loss) in zip(axes.ravel(), ((6, "iid"), (6, "gilbert"), (12, "iid"), (12, "gilbert"))):
        sub = d[(d.Q == Q) & (d.loss == loss)]
        for des, (label, c, mk, ls) in DESIGN.items():
            m = sub[sub.design == des].groupby("p").G.mean()
            ax.plot(m.index, m.values, color=c, marker=mk, ls=ls, label=label)
        ax.set_title(f"{Q} messages/day, {'independent' if loss == 'iid' else 'bursty'} loss", fontsize=8, color=INK)
        ax.set_ylim(0, 1.02)
        ax.set_xticks([0.1, 0.3, 0.5])
    for ax in axes[1]:
        ax.set_xlabel("Message loss probability")
    for ax in axes[:, 0]:
        ax.set_ylabel("Share of days guaranteed")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(bottom=0.16)
    save(fig, "designs")


# ---------------------------------------------------------------- Fig. buffering by tier
def fig_pool():
    d = pd.read_csv("results/confirm/usgs2024_pooling.csv")
    tiers = [1, 6, 12, 24, 96]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.4), sharey=True)
    shades = {0.1: ("#8fb7e8", "o", "-"), 0.3: ("#2a78d6", "s", "--"), 0.5: ("#174a8a", "^", ":")}
    for ax, loss in zip(axes, ("iid", "gilbert")):
        for p, (c, mk, ls) in shades.items():
            s = d[(d.loss == loss) & (d.p == p)].groupby("Q").G7.apply(lambda x: (x >= 0.9).mean()).reindex(tiers)
            ax.plot(range(len(tiers)), s.values, color=c, marker=mk, ls=ls, label=f"p = {p}")
        ax.set_xticks(range(len(tiers)))
        ax.set_xticklabels(tiers)
        ax.set_xlabel("Messages per day")
        ax.set_title("Independent loss" if loss == "iid" else "Bursty loss", fontsize=8, color=INK)
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("Share of sites meeting\nthe 90% / 7-day target")
    axes[0].legend(loc="lower right", fontsize=7)
    save(fig, "pooling")


if __name__ == "__main__":
    k, kp = fig_example()
    fig_need()
    fig_month()
    fig_designs()
    fig_pool()
    print("figures written; example day: guaranteed set", k, "values; periodic", kp)
