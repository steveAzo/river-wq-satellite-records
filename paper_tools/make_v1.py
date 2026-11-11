"""Tables and figures of the v1.0 manuscript (draft4/) from the version 3 confirmation (results/confirm4/) and the two development
rehearsals of the same driver (results/rehearsal4_2023/, results/rehearsal4v2/). Reads result files only; changes no threshold,
design, or site. Kept outside src/ because src/ is frozen (docs/FREEZE4.md).
Run from Paper3/: python -I -W ignore paper_tools/make_v1.py
"""
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "src")
from p3 import proto_base_eval as pe  # noqa: E402

OUT = "draft4"
RUNS = {"2023 (development)": "rehearsal4_2023", "2024, cohort 3 (development)": "rehearsal4v2", "2022, cohort 4 (confirmation)": "confirm4"}
CONDS = (("iid_p0.3", "independent"), ("gilbert_p0.3_b3", "Gilbert"))
CELLS = [(6, "iid_p0.3"), (6, "gilbert_p0.3_b3"), (12, "iid_p0.3"), (12, "gilbert_p0.3_b3")]
PAT = re.compile(r"([+-]\d\.\d+) \(([+-]\d\.\d+) to ([+-]\d\.\d+)\)")
NAMES = {"rec": "Record only", "heur": "3b rule", "flagsrec": "Flags plus record"}
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#52514e",
                     "xtick.color": "#52514e", "ytick.color": "#52514e", "pdf.fonttype": 42})
BLUE, ORANGE, AQUA, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#0b0b0b"


def verdicts(tag):
    return pd.read_csv(f"results/{tag}/verdicts4.csv").set_index("id")


def triples(text):
    return [tuple(float(x) for x in t) for t in PAT.findall(text)]


def m(x, d=3):
    """Number for LaTeX with a true minus sign."""
    s = f"{x:+.{d}f}"
    return s.replace("-", "$-$")


def ci(t, d=3):
    return f"{m(t[0], d)} ({m(t[1], d)} to {m(t[2], d)})"


def levels(tag, q, cond, label="Byte check (hypotheses)"):
    md = open(f"results/{tag}/verdicts4.md", encoding="utf-8").read()
    mt = re.search(rf"{re.escape(label)}, Q = {q}, {cond}: pooled level.*?\n(.*?)\n\n", md, re.S)
    out = {}
    for line in mt.group(1).splitlines():
        p = line.split()
        out[p[0]] = [float(x) for x in p[1:] if x != "/"]
    return out


def write(name, rows):
    open(f"{OUT}/tables/{name}", "w", encoding="utf-8").write("\n".join(rows) + "\n")


# ------------------------------------------------------------------ tables
def table_hyp():
    v = verdicts("confirm4")
    lab = {"H1": ("Code check", "No wrong certain decision; no decoded value differing from the plan; no decision-layer error; no round-trip mismatch", "all 0"),
           "H2": ("Test", "3b rule minus flags plus record, hard cases at unanticipated thresholds", "lower bound at least 0.10"),
           "H3": ("Test", "3b rule minus record only, hard cases at unanticipated thresholds", "lower bound at least 0.10"),
           "H4": ("Test", "Whole record recovered, 3b rule minus record only (the cost of the adopted design)", "lower bound at least $-$0.15 ($Q = 6$), $-$0.10 ($Q = 12$)"),
           "H6": ("Known limit", "3b rule minus flags plus record, hard cases at configured thresholds, $Q = 6$", "upper bound below 0"),
           "H7": ("Analytic bound", "Expected false-certificate days per million days, bit-error rate $10^{-3}$", "none (cannot fail)"),
           "H8": ("Code check", "Record only: byte frame and slot model agree in whole-record recovery", "absolute difference at most 0.01")}
    rows = []
    for h, (typ, st, lim) in lab.items():
        r = v.loc[h, "result"]
        if h in ("H2", "H3", "H4"):
            res = "; ".join(f"{'$Q$ = ' + str(q) + ', ' + c[:3]}: {ci(t)}" for (q, c), t in zip(CELLS, triples(r)))
            res = res.replace("iid", "ind.").replace("gil", "Gil.")
        elif h == "H6":
            res = "; ".join(f"{c}: {ci(t)}" for (_, c), t in zip(CONDS, triples(r)))
        elif h == "H1":
            res = "0 wrong decisions; 0 mismatches in 41,668 blocks"
        elif h == "H7":
            got = re.findall(r"(heur|rec) Q(\d+): ([\d.]+) \(upper ([\d.]+)", r)
            res = "; ".join(f"{'3b rule' if d == 'heur' else 'record'}, $Q = {q}$: {float(p):.4f} (upper {float(u):.4f})" for d, q, p, u in got)
        else:
            diffs = re.findall(r"\|diff\| ([\d.]+)", r)
            res = "largest absolute difference " + max(diffs)
        out = {"pass": "Pass", "fail": "Fail", "not a test": "Reported"}[v.loc[h, "verdict"]]
        if h == "H6":
            out = "Holds" if out == "Pass" else "Does not hold"
        rows.append(f"{h} & {typ} & {st} & {lim} & {res} & {out} \\\\")
    write("confirm_hyp.tex", rows)


def table_years():
    """Lower bounds of the three tests on the three years (same driver)."""
    rows = []
    for h, name in (("H2", "H2, 3b minus flags plus record"), ("H3", "H3, 3b minus record only"), ("H4", "H4, record recovered, 3b minus record only")):
        for yr, tag in RUNS.items():
            t = triples(verdicts(tag).loc[h, "result"])
            rows.append(f"{name if yr.startswith('2023') else ''} & {yr} & " + " & ".join(f"{m(x[0])} ({m(x[1])})" for x in t) + " \\\\")
        rows.append("\\midrule")
    write("years.tex", rows[:-1])


def table_levels(q):
    rows = []
    for cond, cl in CONDS:
        d = levels("confirm4", q, cond)
        s = levels("confirm4", q, cond, "Slot model (cross-check)")
        rows.append(f"\\multicolumn{{5}}{{@{{}}l}}{{{cl.capitalize()} loss}} \\\\")
        for k in ("rec", "heur", "flagsrec"):
            rows.append(f"{NAMES[k]} & " + " & ".join(f"{x:.3f}" for x in d[k]) + " \\\\")
        rows.append("Decision flags (slot model) & " + " & ".join(f"{x:.3f}" for x in s["flags"]) + " \\\\")
    write(f"confirm_desc{'' if q == 6 else '12'}.tex", rows)


def table_kinds():
    md = open("results/confirm4/verdicts4.md", encoding="utf-8").read()
    rows = []
    kname = {"do": "Dissolved oxygen", "ph": "pH", "ec": "Conductance change", "win7": "7DADM window"}
    for cond, cl in CONDS:
        rows.append(f"\\multicolumn{{4}}{{@{{}}l}}{{{cl.capitalize()} loss, $Q = 6$}} \\\\")
        sec = md.split("Byte check, Q = 6: hard cases per kind")[1].split("Byte check, Q = 12")[0]
        for k in ("do", "ph", "ec", "win7"):
            alt = re.search(rf"{cond} {k}_alt .*?3b minus flagsrec (\S+ \(\S+ to \S+\)); 3b minus record (\S+ \(\S+ to \S+\))", sec)
            cfg = re.search(rf"{cond} {k}_cfg .*?3b minus flagsrec (\S+ \(\S+ to \S+\))", sec)
            a, b, c = (triples(x)[0] for x in (alt.group(1), alt.group(2), cfg.group(1)))
            rows.append(f"{kname[k]} & {ci(a)} & {ci(b)} & {ci(c)} \\\\")
    write("confirm_kinds.tex", rows)


def table_region():
    sel = pd.read_csv("results/confirm4/selection.csv", dtype={"site_no": str})
    sel = sel[sel.selected.astype(str).str.lower() == "true"][["site_no", "region"]]
    g = pe.load_agg("confirm4", 6, "byte4").merge(sel, left_on="site", right_on="site_no")
    rows = []
    for cond, cl in CONDS:
        rows.append(f"\\multicolumn{{4}}{{@{{}}l}}{{{cl.capitalize()} loss, $Q = 6$ (hard cases decided at unanticipated thresholds | record recovered)}} \\\\")
        for region, z in g.groupby("region"):
            cells = []
            for d in ("rec", "heur", "flagsrec"):
                def lvl(metric):
                    t = z[(z.cond == cond) & (z.design == d) & (z.metric == metric)]
                    return t["sum"].sum() / t["count"].sum()
                cells.append(f"{lvl('hard_alt'):.3f} | {lvl('rec'):.3f}")
            rows.append(f"{region} ({z.site.nunique()}) & " + " & ".join(cells) + " \\\\")
        rows.append("\\midrule")
    write("confirm_region.tex", rows[:-1])


def table_integrity():
    md = open("results/confirm4/verdicts4.md", encoding="utf-8").read()
    rows = []
    for d, q, rest in re.findall(r"^\s+(heur|rec)\s+Q=\s*(\d+): (.*)$", md, re.M):
        cls = dict(re.findall(r"(N<K|N=K|N>K|uncoded) [\d.]+/([\d.]+)", rest))
        rej = re.search(r"rejected ([\d.]+)", rest).group(1)
        wd = re.search(r"wrong decision ([\d.]+) \(([\d.]+) to ([\d.]+)\)", rest).groups()
        rows.append(f"{'3b rule' if d == 'heur' else 'Record only'} & {q} & {float(rej):.3f} & " + " & ".join(
            f"{float(cls[c]):.3f}" if c in cls else "--" for c in ("N>K", "N=K", "N<K", "uncoded")) +
            f" & {float(wd[0]):.4f} ({float(wd[1]):.4f} to {float(wd[2]):.4f}) \\\\")
    order = {"Record only": 0, "3b rule": 1}
    rows.sort(key=lambda r: (order[r.split(" & ")[0]], int(r.split(" & ")[1])))
    write("confirm_integrity.tex", rows)


def table_sites():
    sel = pd.read_csv("results/confirm4/selection.csv", dtype={"site_no": str})
    sel = sel[sel.selected.astype(str).str.lower() == "true"]
    rt = pd.concat([pd.read_csv(f"results/confirm4/byte4/{s}_roundtrip.csv", dtype={"site": str}) for s in sel.site_no])
    days = rt.groupby("site").day.nunique()
    rows = []
    for region, z in sel.sort_values(["region", "site_no"]).groupby("region"):
        rows.append(f"\\multicolumn{{4}}{{@{{}}l}}{{{region}}} \\\\")
        for r in z.itertuples():
            name = r.station_nm.title().replace("&", "\\&").replace("#", "\\#")
            rows.append(f"{r.site_no} & {name} & {r.state} & {days.get(r.site_no, 0)} \\\\")
        rows.append("\\midrule")
    write("sites.tex", rows[:-1])


# ------------------------------------------------------------------ figures
def fig_forest():
    """H2, H3, H4 on the confirmation cohort with the development lower bounds and the limits."""
    v = {yr: verdicts(tag) for yr, tag in RUNS.items()}
    conf = v["2022, cohort 4 (confirmation)"]
    lim = {"H2": [0.10] * 4, "H3": [0.10] * 4, "H4": [-0.15, -0.15, -0.10, -0.10]}
    title = {"H2": "H2  3b rule minus flags plus record\n(hard cases, unanticipated thresholds)",
             "H3": "H3  3b rule minus record only\n(hard cases, unanticipated thresholds)",
             "H4": "H4  3b rule minus record only\n(whole record recovered)"}
    clab = ["Q = 6, independent", "Q = 6, Gilbert", "Q = 12, independent", "Q = 12, Gilbert"]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    for ax, h in zip(axes, ("H2", "H3", "H4")):
        t = triples(conf.loc[h, "result"])
        for i, (est, lo, hi) in enumerate(t):
            y = 3 - i
            ax.plot([lo, hi], [y, y], color=BLUE, lw=1.8)
            ax.scatter(est, y, s=26, color=BLUE, edgecolor="white", linewidth=0.7, zorder=3)
            for k, (yr, mk) in enumerate((("2023 (development)", "D"), ("2024, cohort 3 (development)", "^"))):
                dv = triples(v[yr].loc[h, "result"])[i]
                ax.scatter(dv[1], y + (0.22 if k == 0 else -0.22), s=16, color=GREY, marker=mk, zorder=2)
            ax.plot([lim[h][i]] * 2, [y - 0.38, y + 0.38], color=ORANGE, lw=1.4)
        ax.axvline(0, color=GREY, lw=0.6)
        ax.set_title(title[h], fontsize=8, color=INK)
        ax.grid(axis="x", color="#e6e5e1", lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_yticks([3, 2, 1, 0])
    axes[0].set_yticklabels(clab, fontsize=7.5)
    axes[1].set_xlabel("Difference in share of cases (95% interval)")
    axes[0].scatter([], [], s=26, color=BLUE, label="Cohort 4 (confirmation), estimate and interval")
    axes[0].scatter([], [], s=16, color=GREY, marker="D", label="Lower bound, 2023")
    axes[0].scatter([], [], s=16, color=GREY, marker="^", label="Lower bound, cohort 3")
    axes[0].plot([], [], color=ORANGE, lw=1.4, label="Pre-registered limit")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, loc="lower center", ncol=4, fontsize=7)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(f"{OUT}/figs/forest.pdf")
    fig.savefig(f"{OUT}/figs/forest.png", dpi=300)
    plt.close(fig)


def fig_tradeoff():
    style = {"rec": (GREY, "o", "Record only"), "heur": (BLUE, "s", "3b rule"), "flagsrec": (AQUA, "o", "Flags plus record"),
             "flags": (ORANGE, "o", "Decision flags (slot model)")}
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2), sharey=True)
    for ax, (cond, cl) in zip(axes, CONDS):
        for q, alpha in ((6, 1.0), (12, 0.45)):
            d = levels("confirm4", q, cond)
            d["flags"] = levels("confirm4", q, cond, "Slot model (cross-check)")["flags"]
            for k, (c, mk, nm) in style.items():
                x, y = d[k][1], d[k][2]
                ax.scatter(x, y, s=34, color=c, marker=mk, alpha=alpha, edgecolor="white", linewidth=0.8, zorder=3)
                if q == 6:
                    ax.annotate(nm, (x, y), xytext=(-6, 6), textcoords="offset points", fontsize=7.3, ha="right", color=INK)
        ax.set_title(f"{cl.capitalize()} loss (solid Q = 6, faded Q = 12)", fontsize=8.5)
        ax.set_xlabel("Hard cases decided, configured thresholds")
        ax.set_xlim(0.4, 1.05)
        ax.set_ylim(0.15, 0.9)
        ax.grid(color="#e6e5e1", lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Hard cases decided, unanticipated thresholds")
    fig.tight_layout()
    fig.savefig(f"{OUT}/figs/tradeoff.pdf")
    fig.savefig(f"{OUT}/figs/tradeoff.png", dpi=300)
    plt.close(fig)


table_hyp()
table_years()
table_levels(6)
table_levels(12)
table_kinds()
table_region()
table_integrity()
table_sites()
fig_forest()
fig_tradeoff()
print("tables and figures written to", OUT)
