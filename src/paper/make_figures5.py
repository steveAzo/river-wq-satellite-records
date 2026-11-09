"""Figures of the v0.5 manuscript. Figures 2 to 4 are drawn from the confirmation outputs (results/confirm3/verdicts3.*);
the development comparison values in Figure 4 are copied from docs/INTEGRITY_RESULTS.md (Stage 1, adopted receiver);
Figure 1 (schematic of intervals) uses constructed values and says so in its caption.
Run from Paper3/: python -I -W ignore src/paper/make_figures5.py
"""
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = "draft3/figs"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                     "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "pdf.fonttype": 42})
BLUE, ORANGE, AQUA, VIOLET, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#8a8984", "#0b0b0b"

v = pd.read_csv("results/confirm3/verdicts3.csv").set_index("id")
md = open("results/confirm3/verdicts3.md", encoding="utf-8").read()


def levels(q, loss):
    m = re.search(rf"Q = {q}, {loss}: pooled level.*?\n(.*?)\n\n", md, re.S)
    d = {}
    for line in m.group(1).splitlines():
        p = line.split()
        if p[0] in ("rec", "heur", "ex1", "tight50", "sod_mds", "sod_once", "flags", "randmix", "hyb1", "hyb2"):
            d[p[0]] = [float(x) for x in p[1:] if x != "/"]
    return d


# ---- Figure 1: what a record alone can and cannot decide (constructed values) ----
def fig_intervals():
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    theta = 5.0
    cases = [("Reading 5.6 mg/L", 5.6), ("Reading 5.2 mg/L", 5.2), ("Reading 4.85 mg/L", 4.85)]
    note = ["record alone decides: not exceeded", "record alone: undetermined; witness: not exceeded", "record alone: undetermined; witness: exceeded"]
    for i, (lab, x) in enumerate(cases):
        y = len(cases) - 1 - i
        tol = max(0.3, 0.05 * x)
        ax.plot([x - tol, x + tol], [y + 0.14] * 2, color=GREY, lw=4, solid_capstyle="butt")
        ax.plot([x - 0.012, x + 0.012], [y - 0.14] * 2, color=BLUE, lw=4, solid_capstyle="butt")
        ax.text(3.97, y + 0.02, lab, ha="left", va="center", fontsize=8.5, color=INK)
        ax.text(3.97, y - 0.2, note[i], ha="left", va="center", fontsize=7.3, color="#52514e")
    ax.axvline(theta, color=ORANGE, lw=1.4)
    ax.text(theta + 0.03, 2.62, "threshold 5 mg/L", color=INK, fontsize=8.5, va="center")
    ax.set_xlim(3.95, 6.3)
    ax.set_ylim(-0.7, 2.85)
    ax.set_yticks([])
    ax.set_xlabel("Dissolved oxygen (mg/L)")
    ax.plot([], [], color=GREY, lw=4, label="Interval from a record within tolerance")
    ax.plot([], [], color=BLUE, lw=4, label="Interval from a kept value or witness (cell, width enlarged)")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/intervals.pdf")
    plt.close(fig)


# ---- Figure 2: design trade-off (configured vs unanticipated thresholds) ----
def fig_tradeoff():
    names = {"rec": "Record only", "heur": "3b rule", "ex1": "Exact allocator", "tight50": "Tolerance x 0.5",
             "sod_mds": "Send-on-delta", "flags": "Decision flags", "randmix": "Random-day control",
             "hyb1": "Hybrid 1", "hyb2": "Hybrid 2"}
    style = {"rec": (GREY, "o"), "heur": (BLUE, "s"), "ex1": (BLUE, "D"), "tight50": (GREY, "^"), "sod_mds": (GREY, "v"),
             "flags": (ORANGE, "o"), "randmix": (GREY, "s"), "hyb1": (AQUA, "o"), "hyb2": (VIOLET, "s")}
    off = {"rec": (6, 4), "heur": (-6, 7), "ex1": (6, -8), "tight50": (-6, 0), "sod_mds": (6, -4), "flags": (-6, 6),
           "randmix": (-6, 0), "hyb1": (6, 0), "hyb2": (6, 0)}
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.4), sharey=True)
    for ax, (loss, title) in zip(axes, (("iid_p0.3", "Independent loss"), ("gilbert_p0.3_b3", "Gilbert loss"))):
        d = levels(6, loss)
        for k, nm in names.items():
            c, mk = style[k]
            x, y = d[k][1], d[k][2]
            ax.scatter(x, y, s=34, color=c, marker=mk, edgecolor="white", linewidth=0.8, zorder=3)
            dx, dy = off[k]
            ax.annotate(nm, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=7.5, color=INK,
                        ha="right" if dx < 0 else ("center" if dx == 0 else "left"), va="center")
        ax.set_title(title, fontsize=9, color=INK)
        ax.set_xlabel("Hard cases decided, configured thresholds")
        ax.set_xlim(0.25, 1.32)
        ax.set_ylim(0.15, 0.9)
        ax.grid(color="#e6e5e1", lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Hard cases decided, unanticipated thresholds")
    fig.tight_layout()
    fig.savefig(f"{OUT}/tradeoff.pdf")
    plt.close(fig)


# ---- Figure 3: confirmed contrasts with intervals and pre-registered limits ----
def fig_forest():
    pat = re.compile(r"([+-]\d\.\d+) \(([+-]\d\.\d+) to ([+-]\d\.\d+)\)")

    def get(h, i):
        return [float(x) for x in pat.findall(v.loc[h, "result"])[i]]

    rows = [("H2  3b rule minus record only (hard, configured)", "H2", 0, 0, 0.15, BLUE),
            ("H3  3b rule minus random-day layering", "H3", 0, 0, 0.05, BLUE),
            ("H4  record recovered, 3b rule minus record only", "H4", 0, 0, -0.12, BLUE),
            ("H5  3b rule minus flags (unanticipated)", "H5", 0, 0, 0.10, BLUE),
            ("H5  3b rule minus record only (unanticipated)", "H5", 2, 0, 0.10, BLUE),
            ("H7  flags minus 3b rule (configured)", "H7", 0, None, 0.0, ORANGE),
            ("H9  hybrid 1 minus flags (unanticipated)", "H9", 0, 0, 0.20, AQUA)]
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    for r, (lab, h, i, j, lim, col) in enumerate(rows):
        y = len(rows) - 1 - r
        vals = pat.findall(v.loc[h, "result"])
        pts = [vals[i]] if j is None else [vals[i], vals[i + 1]]
        for k, (est, lo, hi) in enumerate(pts):
            yy = y + (0.13 if k == 0 else -0.13)
            est, lo, hi = float(est), float(lo), float(hi)
            ax.plot([lo, hi], [yy, yy], color=col, lw=1.6)
            ax.scatter(est, yy, s=22, color=col, marker="o" if k == 0 else "s", edgecolor="white", linewidth=0.7, zorder=3)
        ax.plot([lim, lim], [y - 0.36, y + 0.36], color=INK, lw=1.0, ls=(0, (2, 1.5)))
    ax.axvline(0, color=GREY, lw=0.6)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.8)
    ax.set_xlabel("Difference in share of cases (95% interval; dashed tick: pre-registered limit)")
    ax.plot([], [], "o", color=GREY, label="Independent loss")
    ax.plot([], [], "s", color=GREY, label="Gilbert loss")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.grid(axis="x", color="#e6e5e1", lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(f"{OUT}/forest.pdf")
    plt.close(fig)


# ---- Figure 4: H8, false-certificate share given one CRC-valid forgery ----
def fig_h8():
    s = v.loc["H8", "result"]
    pat = re.compile(r"(record|layered)(?: k2)? Q ?(\d+): ([\d.]+) \(upper ([\d.]+), limit ([\d.]+)\)")
    got = {(a, int(q)): tuple(float(x) for x in rest) for a, q, *rest in pat.findall(s)}
    dev = {("record", 6): 0.027, ("record", 12): 0.0004, ("layered", 6): 0.086, ("layered", 12): 0.0029}  # docs/INTEGRITY_RESULTS.md
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5))
    for ax, q in zip(axes, (6, 12)):
        for k, (kind, lab) in enumerate((("record", "Record only"), ("layered", "Layered witnesses"))):
            y = 1 - k
            est, up, lim = got[(kind, q)]
            ok = up <= lim
            col = AQUA if ok else ORANGE
            ax.plot([0, up], [y, y], color=col, lw=2)
            ax.scatter(est, y, s=30, color=col, edgecolor="white", linewidth=0.8, zorder=3)
            ax.scatter(dev[(kind, q)], y - 0.22, s=24, color=GREY, marker="D", edgecolor="white", linewidth=0.7, zorder=3)
            ax.plot([lim, lim], [y - 0.35, y + 0.35], color=INK, lw=1.2)
            ax.text(max(up, lim) * 1.04, y + 0.0, "bound exceeded" if not ok else "within limit", fontsize=7.5, color=INK, ha="left", va="center")
        ax.set_yticks([1, 0])
        ax.set_yticklabels(["Record only", "Layered witnesses"] if q == 6 else ["", ""], fontsize=8)
        ax.set_title(f"Q = {q} messages per day", fontsize=9)
        ax.set_xlim(0, max(got[("record", q)][2], got[("layered", q)][2], got[("layered", q)][1]) * 2.3)
        ax.set_ylim(-0.7, 1.6)
        ax.grid(axis="x", color="#e6e5e1", lw=0.6)
        ax.set_axisbelow(True)
        ax.set_xlabel("False-certificate share of days")
    axes[0].scatter([], [], s=30, color=AQUA, label="Cohort estimate and upper bound")
    axes[0].scatter([], [], s=24, color=GREY, marker="D", label="Development estimate (6 sites)")
    axes[0].plot([], [], color=INK, lw=1.2, label="Pre-registered limit")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, loc="lower center", ncol=3, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(f"{OUT}/h8.pdf")
    plt.close(fig)


fig_intervals()
fig_tradeoff()
fig_forest()
fig_h8()
print("figures written to", OUT)
