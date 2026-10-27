"""Figures for the revised Paper 3 manuscript (v0.3). Vector PDF and PNG; greyscale-safe (every series has its
own marker and line style and is labelled directly). Palette: the validated categorical order of the dataviz
reference (blue, orange, aqua, yellow, magenta), as in make_figures.py.
Inputs: results/dev/*, results/confirm2/* (confirmation), results/retest2024/* (temporal re-test), when present.
Run from Paper3/: python -I src/paper/make_figures3.py
"""
import os
import pickle
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "src")
from p3 import delivery, frame, record  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

OUT = "draft/figs"
os.makedirs(OUT, exist_ok=True)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
DESIGN = {  # name -> (label, colour, marker, linestyle)
    "rec_code": ("Record-first code", BLUE, "o", "-"),
    "rec_rep": ("Record-first repetition", ORANGE, "s", "--"),
    "tag": ("Tag practice", AQUA, "^", "-."),
    "every_k": ("Every k-th reading", MAGENTA, "v", (0, (5, 2, 1, 2))),
}
COHORTS = {"dev": ("Development 2023", BLUE, "-"), "confirm2": ("Confirmation 2024", ORANGE, "--"),
           "retest2024": ("Re-test 2024", AQUA, ":")}
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "STIXGeneral"], "mathtext.fontset": "stix",
    "font.size": 8.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.5, "lines.markersize": 5,
    "legend.frameon": False, "pdf.fonttype": 42,
})


def have(tag, f):
    return os.path.exists(f"results/{tag}/{f}")


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- example day (development data)
def fig_example():
    """A DO channel-day: readings, tolerance band, record, reconstruction; then the record after losing one
    unit, with the readings the server can still certify. Development data (2023)."""
    # the first July 2023 four-parameter day, in site order, whose DO record needs 11 to 15 values (three units):
    # site 01427510, 2023-07-01 (15 values); losing the middle unit (one message) leaves part certified
    rd = next(d for d in load_site_records("data/clean/usgs/01427510.csv") if str(d.day.date()) == "2023-07-01")
    ch = next(c for c in rd.channels if c.param == "DO")
    plan = record.Encoder([ch]).plan_at(1.0)
    assert 11 <= len(plan) <= 15
    hours = np.arange(ch.n) * rd.steps["DO"] / 60
    rx_all = dict(enumerate(plan))
    rx = {i: v for i, v in rx_all.items() if i // frame.unit_capacity() != 1}       # unit 1 (one message) lost
    print("example day:", rd.day.date(), len(plan), "DO values")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)
    for ax, got, title in ((axes[0], rx_all, "All messages arrived"), (axes[1], rx, "One message (five values) lost")):
        slots = [s for _, s, _ in got.values()]
        vals = [frame.dequantise("DO", c) for _, _, c in got.values()]
        rec = record.reconstruct(ch.n, slots, vals)
        cert, _ = record.certify(got, {"DO": ch.n}, True, len(plan) - 1 if len(plan) - 1 in got else None)
        ax.fill_between(hours, ch.x - ch.tol, ch.x + ch.tol, color=GRID, lw=0, label="Tolerance band")
        ax.plot(hours, ch.x, color=MUTED, lw=1.0, label="Sensor readings")
        ax.plot(hours, rec, color=BLUE, lw=1.4, label="Reconstruction")
        ax.plot(hours[slots], np.array(vals), "o", color=BLUE, ms=4, label="Values received")
        c = cert["DO"]
        ax.fill_between(hours, ax.get_ylim()[0] if False else (ch.x - ch.tol).min() - 0.15,
                        (ch.x - ch.tol).min() - 0.05, where=c, color=AQUA, lw=0, step="mid", label="Certified")
        ax.set_title(title, fontsize=8.5, color=INK)
        ax.set_xlabel("Hour of day (UTC)")
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 6))
    axes[0].set_ylabel("Dissolved oxygen (mg/L)")
    axes[0].legend(loc="upper left", fontsize=7, ncol=1)
    save(fig, "example_day")


# ---------------------------------------------------------------- record cost (RQ1)
def fig_need():
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    for tag, (label, col, ls) in COHORTS.items():
        if not have(tag, "need2.csv"):
            continue
        d = pd.read_csv(f"results/{tag}/need2.csv")
        d = d[d.n_par == 4]
        b = np.sort(np.maximum(3 * d["values"], 1))
        ax.plot(b, np.arange(1, len(b) + 1) / len(b), color=col, ls=ls, label=f"{label} (n = {len(b):,})")
    for m, word in ((1, "one"), (2, "two"), (6, "six")):
        ax.axvline(3 * 5 * m, color=MUTED, lw=0.7, ls=":")
        ax.text(3 * 5 * m, 1.02, f"{word}\nmsg", color=MUTED, fontsize=6.5, ha="center", va="bottom",
                transform=ax.get_xaxis_transform())
    ax.set_xscale("log")
    ticks = [10, 20, 30, 50, 100, 200]
    ax.set_xticks(ticks, [str(t) for t in ticks])
    ax.set_xticks([], minor=True)
    ax.set_xlabel("Bytes of values per four-parameter day")
    ax.set_ylabel("Share of days")
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right", fontsize=6.5)
    save(fig, "need_ecdf")


# ---------------------------------------------------------------- delivery designs (RQ2)
def fig_delivery(tag):
    d = pd.read_csv(f"results/{tag}/cohort_exact.csv", dtype={"site": str})
    d = d[d.Q == 6]
    ps = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    for ax, kind, title in ((axes[0], "iid", "Independent loss"), (axes[1], "gilbert", "Bursty loss (mean burst 3)")):
        cols = [f"iid_p{p}" if kind == "iid" else f"gilbert_p{p}_b3" for p in ps]
        for des, (label, col, mk, ls) in DESIGN.items():
            y = d[d.design == des][cols].mean().to_numpy()
            ax.plot(ps, y, color=col, marker=mk, ls=ls, label=label)
        ax.set_title(title, fontsize=8.5, color=INK)
        ax.set_xlabel("Message loss probability $p$")
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Days fully certified, $G_{\\mathrm{cert}}$")
    axes[0].legend(loc="center left", bbox_to_anchor=(0.0, 0.45), fontsize=7)
    save(fig, "delivery")


# ---------------------------------------------------------------- mismatch of a fixed code (development)
def fig_mismatch():
    m = pd.read_csv("results/dev/robust_mismatch.csv")
    s = pd.read_csv("results/dev/robust_summary.csv")
    m = m[(m.Q == 6) & (m.design == "mds")]
    true = ["iid_p0.05", "iid_p0.1", "iid_p0.2", "iid_p0.3", "iid_p0.4", "iid_p0.5", "iid_p0.6",
            "gilbert_p0.1_b3", "gilbert_p0.3_b3", "gilbert_p0.5_b3", "gilbert_p0.3_b6"]
    assumed = ["iid_p0.1", "iid_p0.3", "iid_p0.5", "gilbert_p0.1_b3", "gilbert_p0.3_b3", "gilbert_p0.5_b3"]
    rec = s[(s.Q == 6) & (s.design == "mds_rec")].set_index("channel").G_cert
    z = np.array([[rec[t] - m[(m.assumed == a) & (m.true == t)].G_cert.iloc[0] for t in true] for a in assumed])
    nice = lambda c: ("indep. " if c.startswith("iid") else "bursty ") + c.split("_p")[1].split("_")[0] + \
        (" (b6)" if c.endswith("b6") else "")
    fig, ax = plt.subplots(figsize=(7.0, 2.4))
    im = ax.imshow(z, cmap="Blues", vmin=0, vmax=max(0.35, z.max()), aspect="auto")
    for i in range(len(assumed)):
        for j in range(len(true)):
            ax.text(j, i, f"{z[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if z[i, j] > 0.22 else INK)
    ax.set_xticks(range(len(true)), [nice(t) for t in true], rotation=35, ha="right")
    ax.set_yticks(range(len(assumed)), [nice(a) for a in assumed])
    ax.set_xlabel("True channel")
    ax.set_ylabel("Channel assumed\nwhen choosing $K$")
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("Record-first code minus fixed-$K$ code", fontsize=7.5)
    save(fig, "mismatch")


# ---------------------------------------------------------------- multi-day designs (development)
def fig_multiday():
    m = pd.read_csv("results/dev/multiday.csv", dtype={"site": str, "variant": str})
    sites = sorted(m.site.unique())
    m = m[(m.Q == 6) & m.site.isin(sites[1::2])]
    rows = {"daily_rec": ("Record-first code, next day", BLUE), "rep_multi_rec": ("Record units, 7-day rotation", ORANGE),
            "tag_multi_rec": ("Record units, random 7-day rotation", AQUA)}
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4), sharey=True)
    for ax, ch, title in ((axes[0], "iid_p0.3", "Independent, $p = 0.3$"),
                          (axes[1], "gilbert_p0.3_b3", "Bursts of 3, $p = 0.3$"),
                          (axes[2], "gilbert_p0.3_b6", "Bursts of 6, $p = 0.3$")):
        x = np.arange(3)
        for k, (des, (label, col)) in enumerate(rows.items()):
            g = m[(m.design == des) & (m.channel == ch)]
            y = [np.average(g[c], weights=g.n_four) for c in ("G1", "G2", "G7")]
            ax.bar(x + (k - 1) * 0.26, y, 0.26, color=col, label=label,
                   hatch=["", "//", ".."][k], edgecolor="white", lw=0.4)
        ax.set_xticks(x, ["1 day", "2 days", "7 days"])
        ax.set_title(title, fontsize=8.5, color=INK)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Days fully certified within")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7)
    save(fig, "multiday")


# ---------------------------------------------------------------- season
def fig_season():
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    for tag, (label, col, ls) in COHORTS.items():
        if not have(tag, "cohort_exact.csv"):
            continue
        d = pd.read_csv(f"results/{tag}/cohort_exact.csv", dtype={"site": str})
        d = d[(d.Q == 6) & (d.design == "rec_code")]
        g = d.groupby("month")["iid_p0.3"].mean()
        ax.plot(g.index, g.to_numpy(), color=col, ls=ls, marker="o", ms=3.5, label=label)
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_xlabel("Month")
    ax.set_ylabel("$G_{\\mathrm{cert}}$, $Q = 6$, $p = 0.3$")
    ax.set_ylim(0.5, 1)
    ax.legend(loc="lower left", fontsize=6.5)
    save(fig, "season")


if __name__ == "__main__":
    main_tag = "confirm2" if have("confirm2", "cohort_exact.csv") else "dev"
    fig_example()
    fig_need()
    fig_delivery(main_tag)
    fig_mismatch()
    fig_multiday()
    fig_season()
    print("figures written to", OUT, "(delivery figure from", main_tag + ")")
