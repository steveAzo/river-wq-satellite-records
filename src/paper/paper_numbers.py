"""Every number quoted in the Paper 3 manuscript, generated from result files (never typed by hand).

Writes draft/numbers.tex (one \\newcommand per number, each with a % source comment) and table bodies
in draft/tables/*.tex. Comparisons stated in the text are ASSERTED here, so the prose cannot drift
from the data. Run from Paper3/: python -I src/paper/paper_numbers.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("draft")
TAB = OUT / "tables"
OUT.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)
MACROS = []


def mac(name, value, source):
    assert name.isalpha(), name
    MACROS.append((name, value, source))


def num(x, d=0):
    return f"{x:,.{d}f}"


def pct(x, d=0):
    return f"{100 * x:.{d}f}\\%"


# ------------------------------------------------------------------ data
need23 = pd.read_csv("results/dev/need_excellent.csv", dtype={"site": str})
need24 = pd.read_csv("results/confirm/need_excellent.csv", dtype={"site": str})
needlc = pd.read_csv("results/lowcost/need_excellent.csv", dtype={"site": str})
rq3 = pd.read_csv("results/confirm/usgs2024_rq3.csv", dtype={"site": str})
rq3dev = pd.read_csv("results/dev/dev_results.csv", dtype={"site": str})
rq3lc = pd.read_csv("results/confirm/lowcost_rq3.csv", dtype={"site": str})
pool24 = pd.read_csv("results/confirm/usgs2024_pooling.csv", dtype={"site": str})
pool23 = pd.read_csv("results/dev/pooling.csv", dtype={"site": str})
size24 = pd.read_csv("results/confirm/usgs2024_sizing.csv", dtype={"site": str})
tuning = json.load(open("results/dev/dev_tuning.json"))
for d in (need23, need24, needlc):
    d["bytes"] = 3 * d["values"]
    d["share"] = d["values"] / d["raw_values"]
SRC_N23, SRC_N24, SRC_NLC = "results/dev/need_excellent.csv", "results/confirm/need_excellent.csv", "results/lowcost/need_excellent.csv"

# ------------------------------------------------------------------ data set sizes
mac("nSites", str(need24.site.nunique()), SRC_N24)
assert need23.site.nunique() == need24.site.nunique()
mac("nDaysDev", num(len(need23)), SRC_N23)
mac("nDaysConf", num(len(need24)), SRC_N24)
mac("nDaysAllFour", num((need24.params == "T|DO|pH|EC").sum()), SRC_N24)
steps = need24.groupby("site").step_min.first().value_counts()
mac("nSitesFifteen", str(int(steps.get(15, 0))), SRC_N24)
mac("nSitesThirty", str(int(steps.get(30, 0))), SRC_N24)
inws, weija = needlc[needlc.site == "InWaterSense"], needlc[needlc.site == "Weija"]
mac("nDaysInws", str(len(inws)), SRC_NLC)
mac("nDaysWeija", str(len(weija)), SRC_NLC)
mac("nSampleRQ", str(rq3[(rq3.Q == 6) & (rq3.loss == "iid") & (rq3.p == 0.3) & (rq3.design == "mds")].shape[0]), "results/confirm/usgs2024_rq3.csv")
mac("nSampleLC", str(rq3lc[(rq3lc.Q == 6) & (rq3lc.loss == "iid") & (rq3lc.p == 0.3) & (rq3lc.design == "mds")].shape[0]), "results/confirm/lowcost_rq3.csv")

# ------------------------------------------------------------------ RQ1 need
for tag, d, src in (("Dev", need23, SRC_N23), ("Conf", need24, SRC_N24)):
    mac(f"needMed{tag}", num(d.bytes.median()), src)
    mac(f"needPninety{tag}", num(d.bytes.quantile(0.9)), src)
    mac(f"needPnn{tag}", num(d.bytes.quantile(0.99)), src)
    mac(f"needMax{tag}", num(d.bytes.max()), src)
    mac(f"needShare{tag}", pct(d.share.median(), 1), src)
    mac(f"needMsgMax{tag}", num(d.messages.max()), src)
    mac(f"needMsgPnn{tag}", num(d.messages.quantile(0.99)), src)
    mac(f"needOneMsg{tag}", pct((d.messages <= 1).mean()), src)
assert need24.share.median() <= 0.05  # H1
site_med = need24.groupby("site").bytes.median()
mac("siteMedMin", num(site_med.min()), SRC_N24)
mac("siteMedMax", num(site_med.max()), SRC_N24)
rel = need24.groupby("site").bytes.agg(lambda x: x.quantile(0.99) / max(x.median(), 1))
mac("siteTailRatio", num(rel.median(), 1), SRC_N24)
need24["month"] = pd.to_datetime(need24.day).dt.month
mon = need24.groupby("month").bytes.median()
mac("monthMin", num(mon.min()), SRC_N24)
mac("monthMax", num(mon.max()), SRC_N24)
mac("monthMaxName", pd.Timestamp(2024, int(mon.idxmax()), 1).strftime("%B"), SRC_N24)
mac("monthMinName", pd.Timestamp(2024, int(mon.idxmin()), 1).strftime("%B"), SRC_N24)
# parameter shares (sites with all four parameters)
four = need24[need24.params == "T|DO|pH|EC"]
tot = four[["v_T", "v_DO", "v_pH", "v_EC"]].sum()
for p in ("T", "DO", "pH", "EC"):
    mac(f"parShare{p.replace('DO', 'Dox').replace('EC', 'Sc').replace('pH', 'Ph').replace('T', 'Temp')}", pct(tot[f"v_{p}"] / tot.sum()), SRC_N24)
mac("needInws", num(inws.bytes.median(), 1), SRC_NLC)
mac("needInwsRatio", num(inws.bytes.median() / need24.bytes.median(), 1), SRC_NLC + "; " + SRC_N24)
assert inws.bytes.median() / need24.bytes.median() >= 3  # H7
mac("needWeija", num(weija.bytes.median()), SRC_NLC)
mac("needWeijaRatio", num(weija.bytes.median() / need24.bytes.median(), 1), SRC_NLC)
mac("rawBytes", num(1296), "10-min, 4-parameter node, 2 B/value + 1 B slot index per cycle (144 x 9 B)")

# ------------------------------------------------------------------ RQ3 delivery
def g(d, Q, loss, p, design, stat="mean"):
    s = d[(d.Q == Q) & (d.loss == loss) & (d.p == p) & (d.design == design)].G
    return getattr(s, stat)()


S3 = "results/confirm/usgs2024_rq3.csv"
names = {"mds": "Code", "repeat": "Rep", "srdl_style": "Srdl", "reliable_opt": "Rel", "raw_periodic": "Raw"}
for des, nm in names.items():
    mac(f"g{nm}Ind", num(g(rq3, 6, "iid", 0.3, des), 2), S3)
    mac(f"g{nm}Bur", num(g(rq3, 6, "gilbert", 0.3, des), 2), S3)
    mac(f"g{nm}Med", num(g(rq3, 6, "iid", 0.3, des, "median"), 2), S3)
    mac(f"g{nm}LC", num(g(rq3lc, 6, "iid", 0.3, des), 2), "results/confirm/lowcost_rq3.csv")
    mac(f"g{nm}IndPct", pct(g(rq3, 6, "iid", 0.3, des)), S3)
    mac(f"g{nm}BurPct", pct(g(rq3, 6, "gilbert", 0.3, des)), S3)
    mac(f"g{nm}LCPct", pct(g(rq3lc, 6, "iid", 0.3, des)), "results/confirm/lowcost_rq3.csv")
r3 = g(rq3, 6, "iid", 0.3, "mds", "median") / g(rq3, 6, "iid", 0.3, "reliable_opt", "median")
assert r3 >= 2  # H3
mac("hThreeRatio", num(r3, 1), S3)
mac("hThreeMeanRatio", num(g(rq3, 6, "iid", 0.3, "mds") / g(rq3, 6, "iid", 0.3, "reliable_opt"), 1), S3)
h4 = g(rq3, 6, "iid", 0.3, "mds", "median") - g(rq3, 6, "iid", 0.3, "srdl_style", "median")
assert h4 >= 0.25  # H4
mac("hFourDiff", num(h4, 2), S3)
pv = rq3[(rq3.Q == 6) & (rq3.loss == "iid") & (rq3.p == 0.3)].pivot_table(index=["site", "day"], columns="design", values="G")
mac("pairBeatRel", pct((pv.mds > pv.reliable_opt).mean()), S3)
mac("pairBeatSrdl", pct((pv.mds > pv.srdl_style).mean()), S3)
h5 = []
for Q in (6, 12, 24):
    for loss in ("iid", "gilbert"):
        for p in (0.3, 0.5):
            m = rq3[(rq3.Q == Q) & (rq3.loss == loss) & (rq3.p == p)].groupby("design").G.mean()
            h5 += [m["mds"] - m["reliable_opt"], m["repeat"] - m["reliable_opt"]]
assert min(h5) >= 0.2  # H5
mac("hFiveMin", num(min(h5), 2), S3)
mac("gCodeOneMax", pct(max(g(rq3, 1, l, p, d) for l in ("iid", "gilbert") for p in (0.1, 0.3, 0.5)
                            for d in ("mds", "reliable_opt", "srdl_style", "raw_periodic"))), S3)
mac("gCodeTwelveInd", num(g(rq3, 12, "iid", 0.3, "mds"), 2), S3)
mac("gCodeTwelveBur", num(g(rq3, 12, "gilbert", 0.3, "mds"), 2), S3)
mac("gRelTwentyFour", pct(g(rq3, 24, "iid", 0.3, "reliable_opt")), S3)
assert g(rq3, 24, "iid", 0.3, "reliable_opt") < 0.5
# development counterparts (for the "development vs confirmation" sentence)
mac("gCodeIndDev", num(g(rq3dev, 6, "iid", 0.3, "mds"), 2), "results/dev/dev_results.csv")
mac("gRelIndDev", num(g(rq3dev, 6, "iid", 0.3, "reliable_opt"), 2), "results/dev/dev_results.csv")
# tuned parameters at the headline setting
mac("tunedK", str(tuning["Q6_iid_p0.3"]["mds"] + 1), "results/dev/dev_tuning.json (index + 1)")
mac("tunedR", str((2, 3, 4, 6)[tuning["Q6_iid_p0.3"]["repeat"]]), "results/dev/dev_tuning.json")

cs = rq3[(rq3.Q == 6) & (rq3.loss == "iid") & (rq3.p == 0.3) & (rq3.design == "mds")].C
mac("certCode", pct(cs.mean()), S3)
cr = rq3[(rq3.Q == 6) & (rq3.loss == "iid") & (rq3.p == 0.3) & (rq3.design == "reliable_opt")].C
mac("certRel", pct(cr.mean()), S3)
assert cs.mean() > cr.mean()
# satellite passes over Weija (Kinéis, SGP4, 7 days, elevation >= 25 degrees; scoping E4, second run)
e4 = pd.read_csv("results/scoping/e4_contacts.csv")
assert e4.max_el.min() >= 25  # the text states "above 25 degrees elevation"
mac("passesWeija", num((e4.site == "Weija intake (GH)").sum() / 7), "results/scoping/e4_contacts.csv")
mac("passMinWeija", num(e4[e4.site == "Weija intake (GH)"].dur_s.median() / 60, 1), "results/scoping/e4_contacts.csv")

# ------------------------------------------------------------------ RQ2 buffering, RQ4 sizing
SP = "results/confirm/usgs2024_pooling.csv"


def sites_ok(d, Q, loss, p=0.3):
    s = d[(d.Q == Q) & (d.loss == loss) & (d.p == p)].G7
    return int((s >= 0.9).sum()), len(s)


for Q, loss, nm in ((6, "iid", "SixInd"), (6, "gilbert", "SixBur"), (12, "gilbert", "TwelveBur"), (12, "iid", "TwelveInd"), (1, "iid", "OneInd"), (24, "gilbert", "TwentyFourBur")):
    k, n = sites_ok(pool24, Q, loss)
    mac(f"pool{nm}", f"{k}", SP)
k1, _ = sites_ok(pool24, 1, "iid")
mac("poolOnePhrase", "no site" if k1 == 0 else ("one site" if k1 == 1 else f"{k1} sites"), SP)
k6, n6 = sites_ok(pool24, 6, "iid")
assert k6 / n6 >= 0.75  # H2
k12, n12 = sites_ok(pool24, 12, "gilbert")
assert k12 / n12 >= 0.85  # H2b
mac("poolSixIndPct", pct(k6 / n6), SP)
mac("poolTwelveBurPct", pct(k12 / n12), SP)
mac("poolDelayMed", num(pool23[(pool23.Q == 6) & (pool23.loss == "iid") & (pool23.p == 0.3)].delay_med.median()), "results/dev/pooling.csv")
ti = {q: i for i, q in enumerate((1, 6, 12, 24, 96))}
dd = size24.pilot_tier.map(ti) - size24.hindsight_tier.map(ti)
assert (dd >= 0).mean() >= 0.8 and (dd <= 1).mean() >= 0.8  # H6
mac("sizeSafety", num(json.load(open("results/dev/sizing_tuning.json"))["safety_factor"], 1), "results/dev/sizing_tuning.json")
assert json.load(open("results/dev/sizing_tuning.json"))["safety_factor"] == 1.0  # the text says "no inflation"
mac("sizeSuff", pct((dd >= 0).mean()), "results/confirm/usgs2024_sizing.csv")
mac("sizeOver", pct((dd <= 1).mean()), "results/confirm/usgs2024_sizing.csv")
WORDS = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
mac("sizeShort", WORDS.get(int((dd < 0).sum()), str(int((dd < 0).sum()))), "results/confirm/usgs2024_sizing.csv")
low = 0
for site in size24[dd < 0].site:
    gg = need24[need24.site == site].sort_values("day")
    pil = pd.to_datetime(gg.day) < pd.to_datetime(gg.day).min() + pd.Timedelta(days=28)
    low += int(gg[pil].bytes.median() < gg[~pil].bytes.median())
mac("sizeShortLow", WORDS.get(low, str(low)), "results/confirm/usgs2024_sizing.csv; results/confirm/need_excellent.csv")


# ------------------------------------------------------------------ LoRaWAN contrast (TTN fair use)
import math


def lora_toa(pl_app, sf, bw=125e3, cr=1, preamble=8):
    """LoRa time on air (Semtech SX1276 datasheet formula), LoRaWAN overhead 13 B, explicit header, CRC on."""
    pl = pl_app + 13
    de = 1 if sf >= 11 else 0
    ts = (2 ** sf) / bw
    n = 8 + max(math.ceil((8 * pl - 4 * sf + 28 + 16) / (4 * (sf - 2 * de))) * (cr + 4), 0)
    return (preamble + 4.25) * ts + n * ts


ttn_sf12 = math.floor(30 / lora_toa(51, 12)) * 51  # 30 s airtime/day, full 51-B frames at SF12
assert ttn_sf12 > need24.bytes.max() and ttn_sf12 > need23.bytes.max()
mac("ttnSFtwelve", num(ttn_sf12), "TTN fair use 30 s/day; SF12, 51-B frames; LoRa time-on-air formula")

# ------------------------------------------------------------------ message format and software
mac("rawMsgs", num(math.ceil(1296 / 21)), "1,296 B / 21 B of values per 23-B message")
mac("needValMaxConf", num(need24["values"].max()), SRC_N24)
assert 6 * 96 > need24["values"].max()  # the 96-message tier with a two-byte header still exceeds any day's need
mac("progLines", num(round(sum(len(open(f, encoding="utf-8").read().splitlines())
                               for f in sorted(Path("src/p3").glob("*.py")) + sorted(Path("src/paper").glob("*.py"))), -2)),
    "src/p3/*.py and src/paper/*.py")

# ------------------------------------------------------------------ bootstrap intervals (src/p3/bootstrap.py)
SB = "results/sens/bootstrap.json"
bs = json.load(open(SB))
mac("nBoot", "2,000", SB)


def ci(key, scale=1.0, d=0, unit=""):
    return f"{scale * bs[key]['lo']:.{d}f}{unit}--{scale * bs[key]['hi']:.{d}f}{unit}"


assert abs(bs["need_median"]["point"] - need24.bytes.median()) < 1e-9
mac("ciNeed", ci("need_median"), SB)
for des, nm in (("mds", "Code"), ("reliable_opt", "Rel"), ("srdl_style", "Srdl"), ("raw_periodic", "Raw")):
    assert abs(bs[f"G_iid_{des}"]["point"] - g(rq3, 6, "iid", 0.3, des)) < 1e-9
    mac(f"ci{nm}Ind", ci(f"G_iid_{des}", 100, 0, "\\%"), SB)
mac("ciHThree", ci("H3_ratio", 1, 1), SB)
assert bs["H3_ratio"]["lo"] >= 2 and bs["H4_diff"]["lo"] >= 0.25  # thresholds hold across the interval
mac("diffCodeRep", num(bs["code_minus_repeat"]["point"], 2), SB)
mac("ciDiffCodeRep", ci("code_minus_repeat", 1, 2), SB)
assert bs["code_minus_repeat"]["lo"] > 0  # "small but consistent"

# ------------------------------------------------------------------ sensitivity analyses (exploratory)
SS, SL = "results/sens/need_sensitivity_usgs2024.csv", "results/sens/need_sensitivity_lowcost.csv"
sens = pd.read_csv(SS, dtype={"site": str})
sens_lc = pd.read_csv(SL, dtype={"site": str})
assert (sens.v_exc.to_numpy() == need24["values"].to_numpy()).all()  # same days, same encoder as the main result
med = {c: 3 * sens[c].median() for c in sens if c.startswith("v_")}
p99 = {c: 3 * sens[c].quantile(0.99) for c in sens if c.startswith("v_")}
mac("sensQMed", num(med["v_exc_q"]), SS)
mac("sensQPct", pct(sens.v_exc_q.sum() / sens.v_exc.sum() - 1), SS)
mac("sensHalfMed", num(med["v_exc_half"]), SS)
mac("sensHalfRatio", num(sens.v_exc_half.median() / sens.v_exc.median(), 1), SS)
mac("sensGoodMed", num(med["v_good"]), SS)
mac("sensGreedyMed", num(med["v_greedy"]), SS)
mac("sensGreedyPct", pct(sens.v_greedy.sum() / sens.v_exc.sum() - 1), SS)
mac("sensDeadMed", num(med["v_deadband"]), SS)
mac("sensDeadRatio", num(sens.v_deadband.sum() / sens.v_exc.sum(), 1), SS)
assert (sens.v_greedy >= sens.v_exc).all()  # min-# is optimal for this reconstruction
fifteen = sens[sens.step_min == 15]
mac("sensXTwoMed", num(3 * fifteen.v_exc_x2.median()), SS)
mac("sensXFourMed", num(3 * fifteen.v_exc_x4.median()), SS)
mac("sensFifteenMed", num(3 * fifteen.v_exc.median()), SS)
# the text says coarser sampling "did not reduce the need" and the ranking was "unchanged" with 19-B messages
assert fifteen.v_exc_x2.median() >= fifteen.v_exc.median() and fifteen.v_exc_x4.median() >= fifteen.v_exc.median()
assert sens.v_good.median() < sens.v_exc.median() < sens.v_exc_half.median()
assert sens.v_deadband.sum() > sens.v_greedy.sum() > sens.v_exc.sum()
rows = []
for c, label in (("v_exc", "Main result: excellent record, fewest values"),
                 ("v_exc_q", "Excellent record within 0.975 of the tolerance (quantiser margin)"),
                 ("v_exc_half", "Excellent record within half the tolerance (sensor margin)"),
                 ("v_good", "Good record, fewest values"),
                 ("v_greedy", "Excellent record, greedy online segmentation"),
                 ("v_deadband", "Excellent record, deadband reporting")):
    rows.append(f"{label} & {med[c]:.0f} & {p99[c]:.0f} & {3 * sens[c].max():.0f} & {3 * sens_lc[sens_lc.site == 'InWaterSense'][c].median():.1f} \\\\")
(TAB / "sensitivity.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")
# 19-byte messages (6 values), frozen tuning
SV = "results/sens/usgs2024_rq3_V6.csv"
v6 = pd.read_csv(SV, dtype={"site": str})
for des, nm in names.items():
    mac(f"vSix{nm}Ind", pct(g(v6, 6, "iid", 0.3, des)), SV)
    mac(f"vSix{nm}Bur", pct(g(v6, 6, "gilbert", 0.3, des)), SV)
order = lambda d: sorted(names, key=lambda des: -g(d, 6, "iid", 0.3, des))  # noqa: E731
assert order(v6) == order(rq3), (order(v6), order(rq3))
v6r = g(v6, 6, "iid", 0.3, "mds", "median") / max(g(v6, 6, "iid", 0.3, "reliable_opt", "median"), 1e-9)
mac("vSixHThree", num(v6r, 1), SV)
mac("vSixHFour", num(g(v6, 6, "iid", 0.3, "mds", "median") - g(v6, 6, "iid", 0.3, "srdl_style", "median"), 2), SV)

# ------------------------------------------------------------------ tables
# Table: delivery designs at 6 messages/day (2024), both loss models, plus low-cost
rows = []
for des, label in (("mds", "Guaranteed set + erasure code (proposed)"), ("repeat", "Guaranteed set + repetition"),
                   ("srdl_style", "Fixed points + random resending (tag practice)"),
                   ("reliable_opt", "Guaranteed set, sent once (reliable-link design)"), ("raw_periodic", "Every $k$-th reading")):
    rows.append(f"{label} & {g(rq3, 6, 'iid', 0.1, des):.2f} & {g(rq3, 6, 'iid', 0.3, des):.2f} & {g(rq3, 6, 'iid', 0.5, des):.2f}"
                f" & {g(rq3, 6, 'gilbert', 0.3, des):.2f} & {g(rq3lc, 6, 'iid', 0.3, des):.2f} \\\\")
(TAB / "designs_results.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")

# Table: hypotheses
hyp = [
    ("H1", "Median daily need at most 5\\% of the raw readings", f"{100 * need24.share.median():.1f}\\%"),
    ("H2", "Sites with at least 90\\% of days guaranteed within 7 d (6 msg/d, independent loss, $p=0.3$): at least 75\\%", f"{k6}/{n6}"),
    ("H2b", "Same at 12 msg/d under bursty loss: at least 85\\%", f"{k12}/{n12}"),
    ("H3", "Median $G$, code over reliable-link design: at least $2\\times$", f"{r3:.1f}$\\times$"),
    ("H4", "Median $G$, code minus tag practice: at least 0.25", f"{h4:.2f}"),
    ("H5", "Code and repetition each exceed the reliable-link design by at least 0.2 in 12 settings", f"12/12 (min.\\ {min(h5):.2f})"),
    ("H6", "Pilot-based tier sufficient at least 80\\%; at most one tier too large at least 80\\%", f"{100 * (dd >= 0).mean():.0f}\\%; {100 * (dd <= 1).mean():.0f}\\%"),
    ("H7", "InWaterSense median need at least $3\\times$ the USGS median", f"{inws.bytes.median() / need24.bytes.median():.1f}$\\times$"),
]
(TAB / "hypotheses.tex").write_text("\n".join(f"{h} & {t} & {v} & Passed \\\\" for h, t, v in hyp) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ highlights (typed by hand): their numbers must match
hl = (OUT / "highlights.txt").read_text(encoding="utf-8").splitlines()
assert len(hl) <= 5 and all(len(h) <= 85 for h in hl), "EMS: at most five highlights of at most 85 characters"
values = {m: v.replace("\\%", "%") for m, v, _ in MACROS}
for i, keys in enumerate((("needMedConf", "needShareConf"), ("gRelIndPct",), ("gCodeIndPct",), ("poolSixInd", "nSites"))):
    for k in keys:
        assert values[k] in hl[i], (hl[i], k, values[k])

# ------------------------------------------------------------------ write
with open(OUT / "numbers.tex", "w", encoding="utf-8") as fh:
    fh.write("% Generated by src/paper/paper_numbers.py; do not edit by hand.\n")
    for name, value, src in MACROS:
        fh.write(f"\\newcommand{{\\{name}}}{{{value}}} % source: {src}\n")
print(f"{len(MACROS)} macros, tables written")
