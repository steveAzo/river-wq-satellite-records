"""Supplementary material of the revised manuscript (v0.3): draft/supplement.tex.

Table S1 and S2: every development and confirmation site (name, state or region, sampling interval, four-parameter
days, median record size, and the site's share of days fully certified at Q = 6, independent loss of 0.3).
Table S3: cohort flow (channel-days and record days) of both cohorts.
Table S4: G_cert of the four full-cohort designs under all 15 channels, confirmation sites, Q = 6 and 12.
Fig. S1: monthly G_cert of the record-first code (moved from the manuscript).
Run from Paper3/: python -I src/paper/supplement.py
"""
import pandas as pd

ESC = {"&": "\\&", "%": "\\%", "#": "\\#", "_": "\\_"}

# moved from the manuscript to shorten it (Fig. S1; drawn by make_figures3.py)
FIG_S1 = ("\\begin{figure}[h]\n\\centering\n\\includegraphics[width=0.6\\textwidth]{figs/season.pdf}\n"
          "\\caption{Monthly share of days fully certified by the record-first code, six messages per day, independent "
          "loss of 0.3 (four-parameter days of each cohort).}\\label{fig:s1}\n\\end{figure}\n")


def esc(s, title=True):
    s = str(s)
    for a, b in ESC.items():
        s = s.replace(a, b)
    return s.title() if title and s.isupper() else s


def site_table(tag, meta, label_col):
    n = pd.read_csv(f"results/{tag}/need2.csv", dtype={"site": str})
    n = n[n.n_par == 4]
    ce = pd.read_csv(f"results/{tag}/cohort_exact.csv", dtype={"site": str})
    g = ce[(ce.Q == 6) & (ce.design == "rec_code")].groupby("site")["iid_p0.3"].mean()
    agg = n.groupby("site").agg(days=("values", "size"), med=("values", "median"),
                                step=("steps", lambda s: s.str.split("|").str[0].astype(int).mode().iloc[0]))
    rows = []
    for site, a in agg.iterrows():
        m = meta.loc[site]
        rows.append(f"{site} & {esc(m.station_nm)} & {esc(m[label_col], False)} & {int(a.step)} & {int(a.days)} & {3 * a.med:.0f} & "
                    f"{g.get(site, float('nan')):.3f} \\\\")
    return rows


def longtable(caption, label, head, rows, spec="@{}lp{6.2cm}lrrrr@{}"):
    return (f"\\begin{{longtable}}{{{spec}}}\n"
            f"\\caption{{{caption}}}\\label{{{label}}}\\\\\n\\toprule\n{head}\\\\\n\\midrule\n\\endfirsthead\n"
            f"\\toprule\n{head}\\\\\n\\midrule\n\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{longtable}\n")


def flow_table():
    """Table S3: cohort flow under the per-channel loader (results/cohort/{dev2023,confirm2}_v2_*.csv)."""
    cols = []
    for tag in ("dev2023", "confirm2"):
        a = pd.read_csv(f"results/cohort/{tag}_v2_channel_days.csv", dtype={"site": str})
        r = pd.read_csv(f"results/cohort/{tag}_v2_record_days.csv", dtype={"site": str})
        k = r.n_par.value_counts()
        four = r[r.n_par == 4]
        cols.append([len(a), (a.status != "eligible").sum(), (a.status == "eligible").sum(), len(r),
                     k.get(1, 0), k.get(2, 0), k.get(3, 0), k.get(4, 0), four.site.nunique(),
                     four.steps.str.split("|").map(lambda s: len(set(s)) > 1).sum()])
    labels = ["Channel-days with data", "Ineligible (gap of more than two readings, or too few readings)",
              "Eligible channel-days", "Record days (at least one eligible parameter)", "\\quad with one parameter",
              "\\quad with two parameters", "\\quad with three parameters",
              "\\quad with four parameters (primary cohort)",
              "Sites with four-parameter days", "Four-parameter days with mixed intervals across parameters"]
    rows = [f"{lab} & {a:,} & {b:,} \\\\" for lab, (a, b) in zip(labels, zip(*cols))]
    return ("\\begin{table}[h]\n\\centering\n\\caption{Cohort flow: channel-days (one parameter of one site on one UTC "
            "day) and record days, development (2023) and confirmation (2024) cohorts.}\\label{tab:s3}\n\\small\n"
            "\\begin{tabular}{@{}lrr@{}}\n\\toprule\nStage & Development & Confirmation \\\\\n\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")


def main():
    head = "Site & Name & {} & Interval (min) & Days & Median bytes & $G_{{\\mathrm{{cert}}}}$"
    dev = pd.read_csv("results/cohort/dev_sites_meta.csv", dtype={"site_no": str}).set_index("site_no")
    sel = pd.read_csv("results/confirm2/selection.csv", dtype={"site_no": str})
    sel = sel[sel.selected.astype(str) == "True"].set_index("site_no")
    s1 = longtable("Development sites (2023): four-parameter record days, median bytes of the record, and the share of "
                   "days fully certified at six messages per day with independent loss of 0.3.", "tab:s1",
                   head.format("State"), site_table("dev", dev, "state"))
    s2 = longtable("Confirmation sites (2024), with the same columns as Table S1.", "tab:s2",
                   head.format("Region"), site_table("confirm2", sel, "region"),
                   spec="@{}lp{4.6cm}p{3.0cm}rrrr@{}")
    s3 = flow_table()
    ce = pd.read_csv("results/confirm2/cohort_exact.csv", dtype={"site": str})
    chans = [c for c in ce.columns if c.startswith(("iid_", "gilbert_"))]
    nice = {"rec_code": "Record-first code", "rec_rep": "Record-first repetition", "every_k": "Every $k$-th reading",
            "tag": "Tag practice"}
    rows = []
    for c in chans:
        kind, rest = c.split("_p")
        lab = ("Independent" if kind == "iid" else "Gilbert") + f", $p = {rest.split('_')[0]}$" + \
            (f", burst {rest.split('_b')[1]}" if "_b" in rest else "")
        vals = [f"{ce[(ce.Q == Q) & (ce.design == d)][c].mean():.3f}" for Q in (6, 12) for d in nice]
        rows.append(f"{lab} & " + " & ".join(vals) + " \\\\")
    s4 = ("\\begin{table}[h]\n\\centering\n\\caption{Days fully certified, $G_{\\mathrm{cert}}$, on the confirmation sites "
          "under all channels (exact; all four-parameter days).}\\label{tab:s4}\n\\footnotesize\n"
          "\\begin{tabular}{@{}lrrrrrrrr@{}}\n\\toprule\n & \\multicolumn{4}{c}{$Q = 6$} & \\multicolumn{4}{c}{$Q = 12$} \\\\\n"
          "Channel & Code & Rep. & Every $k$ & Tag & Code & Rep. & Every $k$ & Tag \\\\\n\\midrule\n" + "\n".join(rows) +
          "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    doc = ("\\documentclass[11pt]{article}\n\\usepackage[margin=2cm]{geometry}\n\\usepackage{mathptmx}\n"
           "\\usepackage{booktabs}\n\\usepackage{longtable}\n\\usepackage{graphicx}\n"
           "\\renewcommand{\\thetable}{S\\arabic{table}}\n\\renewcommand{\\thefigure}{S\\arabic{figure}}\n"
           "\\begin{document}\n\\section*{Supplementary material}\nError-bounded reconstruction and loss-resilient "
           "delivery of river water-quality records over satellite IoT: A reproducible framework.\n\n"
           + s1 + s2 + s3 + s4 + FIG_S1 + "\\end{document}\n")
    open("draft/supplement.tex", "w", encoding="utf-8").write(doc)
    print("draft/supplement.tex written")


if __name__ == "__main__":
    main()
