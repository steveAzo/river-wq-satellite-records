"""Audit the development values typed in docs/CONFIRM3_PLAN.md (Section 4) against the result files that produced them.

Each expected value is recomputed from results/dev (the Step 4 aggregates through src/p3/confirm3.Agg, the Step 3c printout
results/proto_j_eval.txt, and results/dev/robust2_summary.csv), compared with the number typed in the plan within a tolerance,
and the plan text is searched for the typed number inside the row of its hypothesis. The program exits non-zero on any
disagreement. Failure control: --plant-fault changes one expected value and must make the program exit non-zero.
Run from Paper3/: python tools/audit_plan_numbers.py [--plant-fault]
"""
import os
import re
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(ROOT)
from p3 import confirm3 as c3  # noqa: E402
from p3 import proto_base_eval as pe  # noqa: E402

PLAN = open("docs/CONFIRM3_PLAN.md", encoding="utf-8").read()
TOL = 0.0006


def row_of(hid):
    m = re.search(rf"^\| {hid} .*$", PLAN, re.M)
    return m.group(0) if m else ""


def main(plant):
    g6 = pd.concat([pe.load_agg("dev", 6), pe.load_agg("dev", 6, "proto_b_hyb1_hyb2")])
    A6 = c3.Agg(g6)
    got = {}
    for c, tag in (("iid_p0.3", "iid"), ("gilbert_p0.3_b3", "gil")):
        got[f"H2_{tag}"] = A6.diff(c, "heur", "rec", "hard_cfg")[0]
        got[f"H4_{tag}"] = A6.diff(c, "heur", "rec", "rec")[0]
        got[f"H5f_{tag}"] = A6.diff(c, "heur", "flags", "hard_alt")[0]
        got[f"H5r_{tag}"] = A6.diff(c, "heur", "rec", "hard_alt")[0]
    for c, tag in (("iid_p0.3", "iid"), ("gilbert_p0.3_b3", "gil")):
        got[f"H9a_{tag}"] = A6.diff(c, "hyb1", "flags", "hard_alt")[0]
        got[f"H9c_{tag}"] = A6.diff(c, "hyb1", "flags", "hard_cfg")[0]
        got[f"H9r_{tag}"] = A6.diff(c, "hyb1", "flags", "rec")[0]
    got["H7_iid"] = A6.diff("iid_p0.3", "flags", "heur", "hard_cfg")[0]
    got["H7_gil"] = A6.diff("gilbert_p0.3_b3", "flags", "heur", "hard_cfg")[0]
    txt = open("results/proto_j_eval.txt", encoding="utf-8").read()
    q6 = txt.split("## Q = 12")[0]
    parts = q6.split("### gilbert_p0.3_b3")
    for tag, part in (("iid", parts[0]), ("gil", parts[1])):
        m = re.search(r"heur minus randmix: record [+-][\d.]+ \([^)]*\); hard ([+-][\d.]+)", part)
        got[f"H3_{tag}"] = float(m.group(1))
    s = pd.read_csv("results/dev/robust2_summary.csv")
    sel = s[s.receiver == "CRC + sanity + corroboration"].set_index(["variant", "Q"]).false_day
    got["H8_rec6"], got["H8_rec12"] = sel[("record", 6)], sel[("record", 12)]
    got["H8_k2_6"], got["H8_k2_12"] = sel[("layered k2", 6)], sel[("layered k2", 12)]
    typed = {"H2": [("H2_iid", "+0.291"), ("H2_gil", "+0.281")], "H3": [("H3_iid", "+0.171"), ("H3_gil", "+0.172")],
             "H4": [("H4_iid", "-0.080"), ("H4_gil", "-0.067")],
             "H5": [("H5f_iid", "+0.566"), ("H5f_gil", "+0.483"), ("H5r_iid", "+0.210"), ("H5r_gil", "+0.202")],
             "H7": [("H7_iid", "+0.032"), ("H7_gil", "+0.108")],
             "H9": [("H9a_iid", "+0.416"), ("H9a_gil", "+0.355"), ("H9c_iid", "0.000"), ("H9r_iid", "0.000")],
             "H8": [("H8_rec6", "0.027"), ("H8_rec12", "0.0004"), ("H8_k2_6", "0.086"), ("H8_k2_12", "0.0029")]}
    if plant:
        typed["H2"][0] = ("H2_iid", "+0.391")                      # planted fault: the typed number is wrong
    bad = 0
    for hid, items in typed.items():
        row = row_of(hid)
        for key, text in items:
            v = float(text)
            ok_value = abs(abs(got[key]) - abs(v)) <= max(TOL, 0.0006) and (got[key] >= 0) == (v >= 0 or v == 0)
            ok_text = text in row or text.lstrip("+") in row
            flag = "ok" if ok_value and ok_text else "MISMATCH"
            bad += flag != "ok"
            print(f"{hid} {key}: file {got[key]:+.4f}, typed {text}, value {'ok' if ok_value else 'WRONG'}, in plan row {'yes' if ok_text else 'NO'} -> {flag}")
    # thresholds: the numbers frozen in src/p3/confirm3.py must appear in the plan row of their hypothesis
    T = dict(c3.T)
    if plant:
        T["H3_lower"] = 0.07                                       # planted fault: code and plan disagree
    thr = {"H2": [("H2_lower", "0.15")], "H3": [("H3_lower", "0.05")], "H4": [("H4_lower", "-0.12")],
           "H5": [("H5_flags_lower", "0.10"), ("H5_rec_lower", "0.10")], "H9": [("H9_alt_lower", "0.20"), ("H9_cfg_lower", "-0.01")],
           "H8": [("H8_record_q6", "0.06"), ("H8_record_q12", "0.01"), ("H8_layered_q6", "0.15"), ("H8_layered_q12", "0.02")]}
    for hid, items in thr.items():
        row = row_of(hid)
        for key, text in items:
            same_code = abs(T[key] - float(text)) < 1e-12
            in_plan = text in row
            flag = "ok" if same_code and in_plan else "MISMATCH"
            bad += flag != "ok"
            print(f"{hid} threshold {key}: code {T[key]}, plan text {text}, in plan row {'yes' if in_plan else 'NO'} -> {flag}")
    if abs(c3.T["H6_margin"] - 0.005) > 1e-12 or "0.005" not in row_of("H6"):
        bad += 1
        print("H6 margin MISMATCH")
    print("audit failed" if bad else "audit passed", f"({bad} problems)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main("--plant-fault" in sys.argv)
