"""Tables of the v0.5 manuscript, copied from the confirmation outputs (no number is typed here).
Reads results/confirm3/verdicts3.csv and verdicts3.md; writes draft3/tables/confirm_hyp.tex, confirm_desc.tex (Q = 6)
and confirm_desc12.tex (Q = 12).
Run from Paper3/: python -I src/paper/tables5.py
"""
import re

import pandas as pd

OUT = "draft3/tables"
LIMIT = {  # the pre-registered limit of each hypothesis (docs/CONFIRM3_PLAN.md, Section 4)
    "H1": "0 wrong; 0 mismatches",
    "H2": "lower bound at least 0.15",
    "H3": "lower bound at least 0.05",
    "H4": "lower bound at least $-$0.12",
    "H5": "both lower bounds at least 0.10",
    "H6": "no dominance",
    "H7": "lower bound above 0",
    "H8": "upper bounds at most 0.06, 0.01, 0.15, 0.02",
    "H9": "alt lower bound at least 0.20; others at least $-$0.01",
}
SHORT = {
    "H1": "No wrong decision in any certificate design; no frame round-trip mismatch",
    "H2": "3b rule minus record only, hard cases at configured thresholds",
    "H3": "3b rule minus random-day layering, hard cases",
    "H4": "Record recovered, 3b rule minus record only",
    "H5": "Unanticipated thresholds, hard cases: 3b rule minus flags, and minus record only",
    "H6": "Neither send-on-delta nor tolerance x 0.5 dominates the 3b rule",
    "H7": "Known limit: flags minus 3b rule, configured thresholds, independent loss",
    "H8": "False-certificate day share given one CRC-valid forgery",
    "H9": "Hybrid 1 minus flags: unanticipated thresholds; configured thresholds; record recovered",
}
BS = chr(92)


def tex(s):
    s = str(s)
    for a, b in (("sod_mds", "send-on-delta"), ("tight50", "tolerance x 0.5"), ("gilbert_p0.3_b3", "Gilbert"),
                 ("iid_p0.3", "independent"), ("layered k2", "layered"), ("record Q", "record, Q = "),
                 ("layered Q", "layered, Q = "), ("cfg:", "configured:")):
        s = s.replace(a, b)
    s = s.replace("%", BS + "%").replace("_", BS + "_").replace("&", BS + "&")
    s = re.sub(r"(?<![\w.])-(?=\d)", "$-$", s)
    s = re.sub(r"(?<=\()-(?=\d)", "$-$", s)
    s = re.sub(r"(?<=\s)-(?=\d)", "$-$", s)
    return s.replace(" / ", "; ").replace(">=", "$" + BS + "ge$")


EOL = " " + BS + BS
v = pd.read_csv("results/confirm3/verdicts3.csv")
rows = []
for _, r in v.iterrows():
    outcome = "Supported" if str(r["supported"]) == "True" else "Not supported"
    rows.append(f"{r['id']} & {SHORT[r['id']]} & {LIMIT[r['id']]} & {tex(r['result'])} & {outcome}" + EOL)
open(f"{OUT}/confirm_hyp.tex", "w", encoding="utf-8").write("\n".join(rows) + "\n")

md = open("results/confirm3/verdicts3.md", encoding="utf-8").read()
NAMES = {"rec": "Record only", "heur": "3b rule", "ex1": "Exact allocator", "tight50": "Tolerance x 0.5",
         "sod_mds": "Send-on-delta, coded", "sod_once": "Send-on-delta, once", "flags": "Decision flags",
         "randmix": "Random-day control", "hyb1": "Hybrid 1", "hyb2": "Hybrid 2"}
for qq, fname in (("6", "confirm_desc"), ("12", "confirm_desc12")):
    out = []
    for loss, label in (("iid_p0.3", "Independent loss"), ("gilbert_p0.3_b3", "Gilbert loss")):
        m = re.search(rf"Q = {qq}, {loss}: pooled level.*?\n(.*?)(?:\n\n|\Z)", md, re.S)
        out.append(BS + "multicolumn{5}{@{}l}{" + f"{label}, $Q = {qq}$" + "}" + EOL)
        for line in m.group(1).splitlines():
            parts = line.split()
            if parts[0] in NAMES:
                vals = [x for x in parts[1:] if x != "/"]
                out.append(f"{NAMES[parts[0]]} & " + " & ".join(vals) + EOL)
        out.append(BS + "midrule")
    open(f"{OUT}/{fname}.tex", "w", encoding="utf-8").write("\n".join(out[:-1]) + "\n")
print("wrote", OUT)
