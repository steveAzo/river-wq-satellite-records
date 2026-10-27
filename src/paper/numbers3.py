"""Numbers and tables of the revised manuscript (v0.3), generated from the result files.
Writes draft/numbers.tex (one macro per number, with its source) and draft/tables/{cohorts,hypotheses,delivery,env}.tex.
Sources: results/dev (development 2023), results/confirm2 (confirmation), results/retest2024 (temporal re-test),
results/{dev,confirm2}_posthoc2 (exploratory re-run after the confirmation, final rule). Missing sources give '??' and a warning.
Run from Paper3/: python -I src/paper/numbers3.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from p3 import stats  # noqa: E402

OUT = "draft"
M = []
WARN = []


def mac(name, value, src):
    M.append(f"\\newcommand{{\\{name}}}{{{value}}} % source: {src}")


def num(x, nd=0):
    return f"{x:,.{nd}f}"


def pct(x, nd=1):
    return f"{100 * x:.{nd}f}\\%"


def ci(lo, hi, nd=3):
    return f"{lo:.{nd}f} to {hi:.{nd}f}"


def read(tag, f, **kw):
    p = f"results/{tag}/{f}"
    if not os.path.exists(p):
        WARN.append(p)
        return None
    return pd.read_csv(p, **kw)


def row(df, **kw):
    m = df
    for k, v in kw.items():
        m = m[m[k] == v]
    assert len(m) == 1, (kw, len(m))
    return m.iloc[0]


# ---------------------------------------------------------------- cohorts
need = {t: read(t, "need2.csv", dtype={"site": str}) for t in ("dev", "confirm2", "retest2024")}
d, c = need["dev"], need["confirm2"]
mac("nSitesDev", d.site.nunique(), "results/dev/need2.csv")
mac("nSitesDevFour", d[d.n_par == 4].site.nunique(), "results/dev/need2.csv")
mac("nDaysDevAll", num(len(d)), "results/dev/need2.csv")
mac("nDaysDevFour", num((d.n_par == 4).sum()), "results/dev/need2.csv")
mac("nSitesConf", c.site.nunique(), "results/confirm2/need2.csv")
mac("nSitesConfFour", c[c.n_par == 4].site.nunique(), "results/confirm2/need2.csv")
mac("nDaysConfFour", num((c.n_par == 4).sum()), "results/confirm2/need2.csv")
r = need["retest2024"]
mac("nDaysRetestFour", num((r.n_par == 4).sum()) if r is not None else "??", "results/retest2024/need2.csv")

rows = []
for label, t in (("Development 2023 (39 sites)", "dev"), ("Confirmation 2024 (new sites)", "confirm2"),
                 ("Temporal re-test 2024 (development sites)", "retest2024")):
    x = need[t]
    if x is None:
        rows.append(f"{label} & ?? & ?? & ?? & ?? \\\\")
        continue
    x = x[x.n_par == 4]
    mode = x.steps.str.split("|").str[0].astype(int).mode().iloc[0]
    rows.append(f"{label} & {x.site.nunique()} & {num(len(x))} & {mode} min & {int(x.groupby('site').size().median())} \\\\")
open(f"{OUT}/tables/cohorts.tex", "w").write("\n".join(rows) + "\n")

# ---------------------------------------------------------------- RQ1
r1 = read("confirm2", "stats_rq1.csv")
x = row(r1, outcome="median bytes per day")
mac("needMedConf", num(x.estimate), "results/confirm2/stats_rq1.csv")
mac("needMedConfCI", f"{num(x.lo)} to {num(x.hi)}", "results/confirm2/stats_rq1.csv")
mac("needMedConfHi", num(x.hi), "results/confirm2/stats_rq1.csv")
mac("needPninetyConf", num(row(r1, outcome="90th percentile bytes").estimate), "results/confirm2/stats_rq1.csv")
mac("needPnnConf", num(row(r1, outcome="99th percentile bytes").estimate), "results/confirm2/stats_rq1.csv")
mac("needMaxConf", num(3 * c[c.n_par == 4]["values"].max()), "results/confirm2/need2.csv")
mac("valueShareConf", pct(row(r1, outcome="median value share").estimate, 2), "results/confirm2/stats_rq1.csv")
mac("byteShareConf", pct(row(r1, outcome="median byte share").estimate, 2), "results/confirm2/stats_rq1.csv")
mac("oneMsgConf", pct(row(r1, outcome="share of days in one message").estimate), "results/confirm2/stats_rq1.csv")
mac("needMedDev", num(3 * d[d.n_par == 4]["values"].median()), "results/dev/need2.csv")
mac("needMedRetest", num(3 * r[r.n_par == 4]["values"].median()) if r is not None else "??", "results/retest2024/need2.csv")
d4 = d[d.n_par == 4].copy()
d4["one"] = d4.steps.str.split("|").map(lambda s: len(set(s)) == 1)
by = d4[d4.one].groupby(d4.steps.str.split("|").str[0].astype(int))["value_share"].median()
mac("shareFiveDev", pct(by[5], 2), "results/dev/need2.csv")
mac("shareFifteenDev", pct(by[15], 2), "results/dev/need2.csv")
mac("shareSixtyDev", pct(by[60], 1), "results/dev/need2.csv")
ce = read("confirm2", "cohort_exact.csv", dtype={"site": str})
mon = ce[(ce.Q == 6) & (ce.design == "rec_code")].groupby("month")["iid_p0.3"].mean()
mac("monthMaxConf", f"{mon.max():.3f}", "results/confirm2/cohort_exact.csv")
mac("monthMinConf", f"{mon.min():.3f}", "results/confirm2/cohort_exact.csv")

# ---------------------------------------------------------------- RQ2
r3 = read("confirm2", "stats_rq3.csv")


def contrast(Q, ch, name):
    return row(r3, Q=Q, channel=ch, contrast=name)


x = contrast(6, "iid_p0.3", "rec_code")
mac("gCodeIidConf", f"{x.estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("gCodeIidConfCI", ci(x.lo, x.hi), "results/confirm2/stats_rq3.csv")
for key, ch in (("Iid", "iid_p0.3"), ("Bur", "gilbert_p0.3_b3"), ("Bsix", "gilbert_p0.3_b6")):
    x = contrast(6, ch, "rec_code - rec_rep")
    mac(f"dRep{key}Conf", f"{x.estimate:.3f}", "results/confirm2/stats_rq3.csv")
    mac(f"dRep{key}ConfCI", ci(x.lo, x.hi), "results/confirm2/stats_rq3.csv")
x = contrast(6, "iid_p0.3", "rec_code - fixed_K")
mac("dFixedIidConf", f"{x.estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("dFixedIidConfCI", ci(x.lo, x.hi), "results/confirm2/stats_rq3.csv")
mac("dRelIidConf", f"{contrast(6, 'iid_p0.3', 'rec_code - reliable').estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("dTagIidConf", f"{contrast(6, 'iid_p0.3', 'rec_code - tag').estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("dEveryIidConf", f"{contrast(6, 'iid_p0.3', 'rec_code - every_k').estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("gTwelveIidConf", f"{contrast(12, 'iid_p0.3', 'rec_code').estimate:.3f}", "results/confirm2/stats_rq3.csv")
mac("gTwelveBurConf", f"{contrast(12, 'gilbert_p0.3_b3', 'rec_code').estimate:.3f}", "results/confirm2/stats_rq3.csv")

reg = pd.read_csv("results/dev/robust_regret.csv")
mac("regretFixedDev", f"{reg[(reg.Q == 6) & (reg.design == 'mds') & (reg.rule == 'minimax')].regret_vs_oracle_mds.max():.3f}",
    "results/dev/robust_regret.csv")
mm = pd.read_csv("results/dev/robust_mismatch.csv")
sm = pd.read_csv("results/dev/robust_summary.csv")
orc = sm[(sm.Q == 6) & (sm.design == "mds") & (sm.rule == "oracle")].set_index("channel").G_cert
mq = mm[(mm.Q == 6) & (mm.design == "mds")]
mac("mismatchMaxDev", f"{(mq.true.map(orc) - mq.G_cert).max():.3f}", "results/dev/robust_mismatch.csv")
rb = pd.read_csv("results/dev/robust_bytes.csv", dtype={"site": str})
g = rb[rb.Q == 6].pivot_table(index="design", columns="channel", values="G_cert")
mac("tagPolicyDev", f"{g.loc['rep_rec', 'iid_p0.3'] - g.loc['tag_rec', 'iid_p0.3']:.3f}", "results/dev/robust_bytes.csv")
mac("tagContentDev", f"{g.loc['tag_rec', 'iid_p0.3'] - g.loc['tag', 'iid_p0.3']:.3f}", "results/dev/robust_bytes.csv")
mac("interleaveDev", f"{g.loc['rep_rec', 'gilbert_p0.3_b3'] - g.loc['rep_block_rec', 'gilbert_p0.3_b3']:.3f}",
    "results/dev/robust_bytes.csv")

# delivery table (confirmation): code, repetition, every k-th, tag (full cohort); fixed K, reliable (720 sampled days)
CH = ("iid_p0.1", "iid_p0.3", "gilbert_p0.3_b3", "gilbert_p0.3_b6")
samp = read("confirm2", "robust_exact.csv", dtype={"site": str})
chc = json.load(open("results/dev/robust_choice.json"))
lines = []
for Q in (6, 12):
    lines.append(f"\\multicolumn{{5}}{{@{{}}l}}{{$Q = {Q}$ messages per day}} \\\\")
    for des, label in (("rec_code", "Record-first code (proposed)"), ("rec_rep", "Record-first repetition"),
                       ("fixed_K", "Fixed-$K$ code, channel-blind$^{a}$"), ("reliable", "Reliable-link design$^{a}$"),
                       ("tag", "Tag practice"), ("every_k", "Every $k$-th reading")):
        cells = []
        for chn in CH:
            if des in ("fixed_K", "reliable"):
                fam, j = ("mds", chc[str(Q)]["mds"]["minimax"]) if des == "fixed_K" else ("reliable", 0)
                s = samp[(samp.Q == Q) & (samp.fam == fam) & (samp.j == j)]
                est, (lo, hi) = stats.boot_mean(s, chn)
            else:
                x = contrast(Q, chn, des)
                est, lo, hi = x.estimate, x.lo, x.hi
            cells.append(f"{est:.3f}\\newline{{\\scriptsize ({lo:.3f}--{hi:.3f})}}")
        lines.append(f"{label} & " + " & ".join(cells) + " \\\\")
lines.append("\\multicolumn{5}{@{}p{\\linewidth}@{}}{\\footnotesize $^{a}$ 720 sampled days (20 per site); other rows: all days, exact.} \\\\")
open(f"{OUT}/tables/delivery.tex", "w").write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- RQ3
r2 = read("confirm2", "stats_rq2.csv")
for key, ch, Q in (("SixIid", "iid_p0.3", 6), ("SixBur", "gilbert_p0.3_b3", 6), ("TwelveIid", "iid_p0.3", 12),
                   ("TwelveBur", "gilbert_p0.3_b3", 12)):
    x = row(r2, channel=ch, Q=Q)
    mac(f"sites{key}Conf", f"{int(x['sites_G7_ge_0.9'])} of {int(x.n_sites)}", "results/confirm2/stats_rq2.csv")
r4 = row(read("confirm2", "stats_rq4.csv"), planning_channel="iid_p0.3")
mac("sizeSuffConf", pct(r4.sufficient), "results/confirm2/stats_rq4.csv")
mac("sizeSuffConfCI", f"{pct(r4.suff_lo)} to {pct(r4.suff_hi)}", "results/confirm2/stats_rq4.csv")
mac("sizePilotsConf", int(r4.pilots), "results/confirm2/stats_rq4.csv")
mac("sizeOverConf", pct(1 - r4.over1), "results/confirm2/stats_rq4.csv")
mac("sizeDecConf", pct(r4.suff_month_min, 0), "results/confirm2/stats_rq4.csv (worst month: December)")
md = pd.read_csv("results/dev/multiday.csv", dtype={"site": str, "variant": str})
sites = sorted(md.site.unique())
mt = md[md.site.isin(sites[1::2])]


def pooled(design, ch, col, Q=6, variant=None):
    gg = mt[(mt.Q == Q) & (mt.design == design) & (mt.channel == ch)]
    if variant is not None:
        gg = gg[gg.variant == variant]
    return np.average(gg[col], weights=gg.n_four)


mac("rotBsixDev", f"{pooled('rep_multi_rec', 'gilbert_p0.3_b6', 'G7'):.3f}", "results/dev/multiday.csv")
mac("dailyBsixDev", f"{pooled('daily_rec', 'gilbert_p0.3_b6', 'G7'):.3f}", "results/dev/multiday.csv")
mac("rotGoneDev", f"{pooled('rep_multi_rec', 'gilbert_p0.3_b6', 'G1'):.3f}", "results/dev/multiday.csv")
ms = pd.read_csv("results/dev/multiday_summary.csv", dtype={"variant": str})
mac("droppedDev", num(row(ms, Q=1, design="buf_rec (chosen rho)", channel="iid_p0.3").dropped),
    "results/dev/multiday_summary.csv")

# ---------------------------------------------------------------- RQ4 (Table C)
es = read("confirm2", "env_summary.csv")
p6 = es[(es.Q == 6) & (es.cond == "perfect")].set_index("design")
i6 = es[(es.Q == 6) & (es.cond == "iid_p0.3")].set_index("design")
mac("decDOConf", f"{p6.loc['rec_code', 'DO_decided']:.3f}", "results/confirm2/env_summary.csv")
mac("decDOEventConf", f"{p6.loc['rec_code', 'DO_decided_on_events']:.3f}", "results/confirm2/env_summary.csv")
mac("eventsDOConf", num(p6.loc["rec_code", "DO_events"]), "results/confirm2/env_summary.csv")
mac("decDOEveryConf", f"{p6.loc['every_k', 'DO_decided']:.3f}", "results/confirm2/env_summary.csv")
mac("decDOTagConf", f"{p6.loc['tag', 'DO_decided']:.3f}", "results/confirm2/env_summary.csv")
mac("missECConf", f"{p6.loc['rec_code', 'EC_miss_rate']:.3f}", "results/confirm2/env_summary.csv")
mac("eventsECConf", num(p6.loc["rec_code", "EC_events"]), "results/confirm2/env_summary.csv")
mac("missECEveryConf", f"{p6.loc['every_k', 'EC_miss_rate']:.3f}", "results/confirm2/env_summary.csv")
mac("missECTagConf", f"{p6.loc['tag', 'EC_miss_rate']:.3f}", "results/confirm2/env_summary.csv")
mac("missPHConf", f"{p6.loc['rec_code', 'pH_miss_rate']:.3f}", "results/confirm2/env_summary.csv")
mac("eventsPHConf", num(p6.loc["rec_code", "pH_events"]), "results/confirm2/env_summary.csv")
mac("missPHEveryConf", f"{p6.loc['every_k', 'pH_miss_rate']:.3f}", "results/confirm2/env_summary.csv")
env_rows = [("Low-DO criterion decided, all days", "DO_decided"), ("Low-DO criterion decided, event days", "DO_decided_on_events"),
            ("Low-DO days missed", "DO_miss_rate"), ("pH out-of-range days missed", "pH_miss_rate"),
            ("Conductance pulses missed", "EC_miss_rate"), ("7DADM above 20\\,\\textdegree C decided", "7DADM_decided"),
            ("7DADM exceedances missed", "7DADM_miss_rate")]
lines = [f"{label} & " + " & ".join(f"{p6.loc[dz, col]:.3f} / {i6.loc[dz, col]:.3f}"
                                    for dz in ("rec_code", "rec_rep", "every_k", "tag")) + " \\\\" for label, col in env_rows]
lines.append("\\multicolumn{5}{@{}p{\\linewidth}@{}}{\\footnotesize Each cell: perfect delivery / independent loss of 0.3. Events: "
             f"{num(p6.loc['rec_code', 'DO_events'])} low-DO, {num(p6.loc['rec_code', 'pH_events'])} pH, "
             f"{num(p6.loc['rec_code', 'EC_events'])} conductance, {num(p6.loc['rec_code', '7DADM_events'])} 7DADM.}} \\\\")
open(f"{OUT}/tables/env.tex", "w").write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- robustness and resources
gl = pd.read_csv("results/dev/robust9_glitch.csv", dtype={"site": str})
mac("glitchCostDev", f"{gl[gl.k == 1].extra_values.mean():.1f}", "results/dev/robust9_glitch.csv")
co = read("confirm2", "robust9_corrupt.csv", dtype={"site": str})
cc = co[(co.Q == 6) & (co.design == "rec_code")].groupby("corruption").Phi.mean()
mac("corrNoneConf", f"{cc['none']:.3f}", "results/confirm2/robust9_corrupt.csv")
mac("corrBerThreeConf", f"{cc['ber_1e-3']:.3f}", "results/confirm2/robust9_corrupt.csv")
mac("falseCertConf", int(co.false_cert_total.sum()), "results/confirm2/robust9_corrupt.csv")
mac("nDaysCorrConf", co[["site", "day"]].drop_duplicates().shape[0], "results/confirm2/robust9_corrupt.csv (sampled test days)")
b2 = co[co.corruption == "ber_1e-2"]
checks = (b2.decode_tries * 20).sum() + (b2.crc_fails * 20).sum()
mac("crcChecksConf", num(checks), "results/confirm2/robust9_corrupt.csv (decoding attempts + rejected data units)")
mac("collisionsExpConf", f"{checks / 2 ** 16:.1f}", "CRC checks / 2^16")
for tag, key in (("confirm2_posthoc2", "Conf"), ("dev_posthoc2", "Dev")):
    p = read(tag, "robust9_corrupt.csv", dtype={"site": str})
    mac(f"falseCertPost{key}", int(p.false_cert_total.sum()) if p is not None else "??", f"results/{tag}/robust9_corrupt.csv")
p = read("confirm2_posthoc2", "robust9_corrupt.csv", dtype={"site": str})


def g6(df, cor, des):
    return df[(df.corruption == cor) & (df.design == des) & (df.Q == 6)].Phi.mean()


SRC_P = "results/confirm2{,_posthoc2}/robust9_corrupt.csv (Q = 6)"
mac("postCostThreeConf", f"{g6(co, 'ber_1e-3', 'rec_code') - g6(p, 'ber_1e-3', 'rec_code'):.3f}" if p is not None else "??", SRC_P)
mac("postCodeTwoConf", f"{g6(p, 'ber_1e-2', 'rec_code'):.3f}" if p is not None else "??", SRC_P)
mac("postRepTwoConf", f"{g6(p, 'ber_1e-2', 'rec_rep'):.3f}" if p is not None else "??", SRC_P)
res = pd.read_csv("results/dev/bench_resources.csv")
ops = res.groupby("step_min").ops.median()
mac("opsFifteenDev", num(ops[15]), "results/dev/bench_resources.csv")
mac("opsFiveDev", num(ops[5]), "results/dev/bench_resources.csv")
mac("mcuFiveDev", f"{ops[5] * 200 / 48e6:.2f}", "200 cycles per update at 48 MHz")

# ---------------------------------------------------------------- confirmation table and re-test
v = read("confirm2", "verdicts.csv")
TH = {"C1": "upper bound $\\le$ 30 B", "C2": "exactly 0", "C3": "lower bound $\\ge$ 0.03", "C4": "lower bound $\\ge$ 0.05",
      "C5": "lower bounds $\\ge$ 0.5", "C6": "lower bounds $\\ge$ 0.95", "C7": "upper $\\le -0.3$; lower $\\ge$ 0.3",
      "C8": "estimate $\\ge$ 0.75"}
TEXT = {"C1": "Median record of a four-parameter day (bytes)", "C2": "Readings certified outside tolerance or wrong certain decisions",
        "C3": "Code minus repetition, $Q = 6$, $p = 0.3$", "C4": "Code minus channel-blind fixed-$K$ code (sampled days)",
        "C5": "Code minus tag practice / minus every $k$-th reading", "C6": "$G_{\\mathrm{cert}}$ at $Q = 12$, independent / bursty loss",
        "C7": "Conductance pulses missed / low-DO days decided, code minus every $k$-th",
        "C8": "28-day pilots choosing a sufficient plan"}
lines = []
for _, x in v.iterrows():
    if x.id == "C2":
        res_ = f"{int(float(x.estimate))} readings (1 day)"
    elif x.id in ("C1",):
        res_ = f"{float(x.estimate):.0f} ({float(x.lo):.0f} to {float(x.hi):.0f})"
    elif "/" in str(x.estimate):
        a, b = str(x.estimate).split(" / ")
        la, lb = str(x.lo).split(" / ")
        ha, hb = str(x.hi).split(" / ")
        res_ = f"{a} ({la} to {ha}) /\\newline {b} ({lb} to {hb})"
    else:
        res_ = f"{float(x.estimate):.3f} ({float(x.lo):.3f} to {float(x.hi):.3f})"
    res_ = res_.replace("-0.", "$-$0.")                       # typographic minus
    lines.append(f"{x.id} & {TEXT[x.id]} & {TH[x.id]} & {res_} & {'Supported' if x['pass'] else 'Not supported'} \\\\")
open(f"{OUT}/tables/hypotheses.tex", "w").write("\n".join(lines) + "\n")
rt = read("retest2024", "stats_rq3.csv")
mac("gCodeIidRetest", f"{row(rt, Q=6, channel='iid_p0.3', contrast='rec_code').estimate:.3f}" if rt is not None else "??",
    "results/retest2024/stats_rq3.csv")

# ---------------------------------------------------------------- low-cost deployments (exploratory)
import pickle  # noqa: E402
from p3 import cohort_exact as cex  # noqa: E402
ln = read("lowcost2", "need2.csv", dtype={"site": str})
lc = read("lowcost2", "cohort_exact.csv", dtype={"site": str})
if ln is not None and lc is not None:
    w = ln[ln.site == "InWaterSense"]
    w4 = w[w.n_par == 4]
    mac("inwsDays", len(w4), "results/lowcost2/need2.csv")
    mac("inwsMedBytes", num(3 * w4["values"].median()), "results/lowcost2/need2.csv")
    for Q, key in ((6, "Six"), (12, "Twelve")):
        for des, dk in (("rec_code", "Code"), ("rec_rep", "Rep")):
            mac(f"inws{dk}{key}", f"{lc[(lc.Q == Q) & (lc.design == des)]['iid_p0.3'].mean():.3f}",
                "results/lowcost2/cohort_exact.csv")
    P = pickle.load(open("results/lowcost2/plans/Weija.pkl", "rb"))
    D = [-(-len(v["plan"][0]) // 5) for v in P.values()]
    B = [v["plan"][1] for v in P.values()]
    mac("weijaDays", len(P), "results/lowcost2/plans/Weija.pkl (private data; derived count)")
    mac("weijaMedBytes", num(3 * ln[ln.site == "Weija"]["values"].median()), "results/lowcost2/need2.csv")
    for f, dk in ((cex.p_code, "Code"), (cex.p_rep, "Rep")):
        mac(f"weija{dk}Six", f"{np.mean([b * f(dd, 6, ('iid', 0.3, 0)) for dd, b in zip(D, B)]):.3f}",
            "results/lowcost2/plans/Weija.pkl (exact)")

# ---------------------------------------------------------------- final-check additions (review M3, M8, M10, M12, M17)
SRC = "results/dev/e2_anchor_Q6.csv (Q = 6, p = 0.3)"
e2 = pd.read_csv("results/dev/e2_anchor_Q6.csv")
gm = e2.groupby(["loss", "design"])[["Gcert_self", "Gcert_chain"]].mean()
gain = gm.Gcert_self - gm.Gcert_chain
pairs = e2.drop_duplicates(["site", "day"])
mac("chainPairsDev", len(pairs), SRC)
mac("chainSaveDev", f"{(pairs.need_self - pairs.need_chain).mean():.1f}", SRC)
mac("chainGainLoDev", f"{gain.min():.2f}", SRC)
mac("chainGainHiDev", f"{gain.max():.2f}", SRC)
pl = pd.read_csv("results/dev/robust_pilot.csv")
pl = pl[(pl.Q == 6) & (pl.design == "mds")]
mac("pilotLossDev", f"{(pl.G_cert_oracle - pl.G_cert_pilot).max():.3f}", "results/dev/robust_pilot.csv (Q = 6)")
f = c[c.n_par < 4]
mac("nDaysConfFewer", num(len(f)), "results/confirm2/need2.csv")
mac("needMedConfFewer", num(3 * f["values"].median()), "results/confirm2/need2.csv")
c4 = c[c.n_par == 4]
mac("needSiteEqConf", num(3 * c4.groupby("site")["values"].median().median()), "results/confirm2/need2.csv (median of site medians)")
sg = ce[(ce.Q == 6) & (ce.design == "rec_code")].groupby("site")["iid_p0.3"].mean()
mac("gSiteMinConf", f"{sg.min():.3f}", "results/confirm2/cohort_exact.csv (site means)")
mac("gSiteMedConf", f"{sg.median():.3f}", "results/confirm2/cohort_exact.csv (site means)")
mac("gSiteMaxConf", f"{sg.max():.3f}", "results/confirm2/cohort_exact.csv (site means)")
x = row(r3, Q=6, channel="iid_p0.3", contrast="rec_code, site x month block bootstrap")
mac("gCodeIidBlockCI", ci(x.lo, x.hi), "results/confirm2/stats_rq3.csv (site x month blocks)")
bm = res.groupby("step_min").median(numeric_only=True)
mac("hostFiveS", f"{bm.stream_s[5]:.1f}", "results/dev/bench_resources.csv (table-free, Python)")
mac("hostFiveKB", num(bm.stream_peak_B[5] / 1000), "results/dev/bench_resources.csv")
mac("hostFifteenS", f"{bm.stream_s[15]:.2f}", "results/dev/bench_resources.csv")
mac("hostFifteenKB", num(bm.stream_peak_B[15] / 1000), "results/dev/bench_resources.csv")
mac("hostTableFiveS", f"{bm.table_s[5]:.1f}", "results/dev/bench_resources.csv (reference table encoder)")
mac("hostTableFiveMB", f"{bm.table_peak_B[5] / 1e6:.1f}", "results/dev/bench_resources.csv")

# ---------------------------------------------------------------- software
import glob  # noqa: E402
import re  # noqa: E402
files = glob.glob("src/p3/*.py") + glob.glob("src/data/*.py") + glob.glob("src/paper/*.py")
mac("progLines", num(round(sum(len(open(f, encoding="utf-8").read().splitlines()) for f in files), -2)),
    "src/{p3,data,paper}/*.py")
n_tests = 0
for f in glob.glob("tests/test_*.py"):
    n_tests += len(re.findall(r"^def test_", open(f, encoding="utf-8").read(), re.M))
mac("nTests", n_tests, "tests/test_*.py (test functions; parametrised cases counted once)")

open(f"{OUT}/numbers.tex", "w").write("% generated by src/paper/numbers3.py; do not edit\n" + "\n".join(M) + "\n")
print(f"{len(M)} macros written; missing sources: {WARN or 'none'}")
