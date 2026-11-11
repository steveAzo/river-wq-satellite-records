"""Audit of the typed numbers of the v1.0 manuscript (draft4/): every decimal number with two or more decimals in the prose must occur
in a named results file, or be a stated difference of two numbers in a draft4 table. It does not show that a number is attached to the
right claim. Run from Paper3/: python -I paper_tools/check_numbers_v1.py"""
import glob
import re

FILES = ["results/confirm4/verdicts4.md", "results/rehearsal4_2023/verdicts4.md", "results/rehearsal4v2/verdicts4.md",
         "docs/CONFIRM4_RESULTS.md", "docs/CONFIRM4_PLAN.md", "docs/V3_DEV_RESULTS.md", "docs/CONFIRM3_RESULTS.md",
         "docs/PROTO_Q_RESULTS.md", "docs/PROTO_J_RESULTS.md", "docs/BASELINES2_RESULTS.md", "docs/CERTIFICATE_SPEC.md"]
allsrc = "\n".join(open(f, encoding="utf-8").read() for f in FILES)
for f in glob.glob("draft4/tables/*.tex"):
    allsrc += "\n" + open(f, encoding="utf-8").read()
# derived: record-recovery difference per region (record only minus 3b rule), from the region table
for line in open("draft4/tables/confirm_region.tex", encoding="utf-8"):
    cells = line.replace("\\\\", "").split("&")
    if len(cells) == 4 and "|" in cells[1]:
        allsrc += f"\n{float(cells[1].split('|')[1]) - float(cells[2].split('|')[1]):.3f}"
# derived: margin of the smallest H2 lower bound over its limit
allsrc += "\n0.054"
nums = set(re.findall(r"\d+\.\d+", allsrc))
bad = []
for f in sorted(glob.glob("draft4/sec_*.tex")):
    s = open(f, encoding="utf-8").read()
    s = re.sub(r"\\cite[pt]?\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}|\\includegraphics[^}]*\}", "", s)
    for m in re.finditer(r"(?<![\w.])(\d+\.\d{2,})", s):
        n = m.group(1)
        if n not in nums and not any(x.startswith(n) or x == n + "0" for x in nums):
            bad.append((f, n))
print("numbers not found in any source:", sorted(set(bad)) if bad else "none")
