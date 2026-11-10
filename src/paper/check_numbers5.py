"""Audit of the typed numbers of the v0.5 manuscript: every decimal number with two or more decimals in the prose
must occur in a named results file (confirmation outputs or development documents). Run from Paper3/."""
import glob
import re

src = {}
for f in ["results/confirm3/verdicts3.md", "docs/HYBRID_RESULTS.md", "docs/BASELINES2_RESULTS.md",
          "docs/INTEGRITY_RESULTS.md", "docs/PROTO_Q_RESULTS.md", "docs/PROTO_RESULTS.md", "docs/PROTO_J_RESULTS.md",
          "docs/CONFIRM3_PLAN.md", "docs/CERTIFICATE_SPEC.md", "docs/FRAME_SPEC_V2.md"]:
    src[f] = open(f, encoding="utf-8").read()
allsrc = "\n".join(src.values())
# the per-region table is a source too; the loss of record recovery per region (record only minus 3b rule) is derived from it
reg = open("draft3/tables/confirm_region.tex", encoding="utf-8").read()
allsrc += "\n" + reg
for line in reg.splitlines():
    cells = line.replace("\\\\", "").split("&")
    if len(cells) == 5 and "|" in cells[1]:
        r0 = float(cells[1].split("|")[1])
        r1 = float(cells[2].split("|")[1])
        allsrc += f"\n{r0 - r1:.3f}"
allsrc += "\n" + open("draft3/tables/confirm_kinds.tex", encoding="utf-8").read()
bad = []
for f in sorted(glob.glob("draft3/sec_*.tex")):
    s = open(f, encoding="utf-8").read()
    s = re.sub(r"\\cite[pt]?\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}", "", s)
    for m in re.finditer(r"(?<![\w.])(\d+\.\d{2,})", s):
        n = m.group(1)
        if n not in allsrc:
            # tolerate a trailing-zero difference (0.30 for 0.300) and the rounding of 3-decimals to 2
            if not any(x.startswith(n) for x in re.findall(r"\d+\.\d+", allsrc)):
                bad.append((f, n))
print("numbers not found in any source:", sorted(set(bad)) if bad else "none")
