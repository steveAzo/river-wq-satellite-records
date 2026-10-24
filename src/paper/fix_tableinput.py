"""One-off repair (2026-10-23): restore the \\tableinput macro lines that a shell-quoting slip corrupted
(backslash-n became a newline, backslash-t a tab). Run from Paper3/draft: python -I ../src/paper/fix_tableinput.py
"""
BS = chr(92)
TAB = chr(9)

p = "main.tex"
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for line in lines:
    if line.strip() == BS + "makeatletter" or ("ableinput" in line and "@@input" in line):
        continue
    out.append(line)
    if line.strip() == BS + "input{numbers}":
        pass
text = "\n".join(out)
good = (BS + "makeatletter" + BS + "newcommand{" + BS + "tableinput}[1]{" + BS + "@@input #1 }" + BS + "makeatother")
marker = "% primitive input, expandable inside tabularx"
assert marker in text
text = text.replace(marker + " (" + BS + "input is not)", marker + " (" + BS + "input is not)\n" + good, 1)
open(p, "w", encoding="utf-8").write(text)

for p in ("sec_study.tex", "sec_results.tex"):
    s = open(p, encoding="utf-8").read()
    s = s.replace(TAB + "ableinput{", BS + "tableinput{")
    open(p, "w", encoding="utf-8").write(s)
print("repaired")
