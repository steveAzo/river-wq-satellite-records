"""Flatten draft/main.tex (elsarticle) for pandoc, so that the Word copy is built from the same source as the PDF:
  sections, generated tables, and numbers.tex inlined; figures -> PNG copies (Fig. 1 from figs/arch.tex);
  every \\ref resolved to the number LaTeX printed (main.aux); headings numbered as in the PDF (1., 2.1.);
  the elsarticle front matter (title, authors, affiliation, abstract, keywords) turned into marked paragraphs.
Layout the Word writer cannot express is passed to src/paper/fix_word.py as @@...@@ markers:
  @@TITLE@@ @@AUTHORS@@ @@AFFIL@@ @@ABSHEAD@@ @@ABS@@ @@KW@@ (front matter); @@H1@@ / @@H2@@ / @@H1U@@ (numbered and
  unnumbered headings); @@TAB:<n>@@ / @@FIG:<n>:<width fraction>@@ at the start of captions; @@NOIND@@ on text
  that continues a paragraph after a display equation. Display equation k gets number k (checked against main.aux).
Usage (from Paper3/draft4): python -I ../paper_tools/make_word_v1.py . word_main.tex (copy of src/paper/make_word5.py with a six-column hypothesis table)
"""
import json
import re
import sys

d, out = sys.argv[1], sys.argv[2]
s = open(f"{d}/main.tex", encoding="utf-8").read()
s = s.replace(r"\makeatletter\newcommand{\tableinput}[1]{\@@input #1 }\makeatother", "")
s = s.replace(r"\input{numbers}", open(f"{d}/numbers.tex", encoding="utf-8").read())
s = re.sub(r"\\input\{(sec_[a-z]+)\}", lambda m: open(f"{d}/{m.group(1)}.tex", encoding="utf-8").read(), s)
s = re.sub(r"\\input\{(tables/[a-z_0-9]+\.tex)\}", lambda m: open(f"{d}/{m.group(1)}", encoding="utf-8").read(), s)
s = re.sub(r"\\tableinput\{(tables/[a-z_0-9]+\.tex)\}", lambda m: open(f"{d}/{m.group(1)}", encoding="utf-8").read(), s)
# the long hypothesis table becomes an ordinary table for Word
s = re.sub(r"\{\\footnotesize\s*\\begin\{longtable\}\{[^\n]*\}\s*\\caption\{(.*?)\}\\label\{(tab:hyp)\}\\\\(.*?)\\endfoot\s*(.*?)\\end\{longtable\}\s*\}",
           lambda m: "\\begin{table}[t]\n\\caption{" + m.group(1) + "}\n\\label{" + m.group(2) + "}\n\\begin{tabularx}{\\textwidth}{llllll}\n\\toprule\nID & Type & Statement & Limit & Result (95\\% interval) & Outcome \\\\\n\\midrule\n" + m.group(4) + "\\bottomrule\n\\end{tabularx}\n\\end{table}",
           s, flags=re.S)
# any other long table (the appendices) becomes an ordinary table with as many plain columns as its header
def plain_longtable(m):
    cap, lab, head, body = m.group(1), m.group(2), m.group(3), m.group(4)
    ncol = max(line.count("&") for line in head.splitlines()) + 1
    return ("\\begin{table}[t]\n\\caption{" + cap + "}\n\\label{" + lab + "}\n\\begin{tabularx}{\\textwidth}{" + "l" * ncol + "}\n"
            + head.strip() + "\n" + body.strip() + "\n\\bottomrule\n\\end{tabularx}\n\\end{table}")


s = re.sub(r"\{\\(?:footnotesize|scriptsize)[^\n]*\n\\begin\{longtable\}[^\n]*\n\\caption\{(.*?)\}\\label\{([^}]+)\}\\\\(.*?)\\endfirsthead.*?\\endfoot\s*(.*?)\\end\{longtable\}\s*\}",
           plain_longtable, s, flags=re.S)
assert r"\begin{longtable}" not in s, "a long table was not converted"
s = s.replace("$-$", "\u2212")   # one run: a separate math minus is dropped by text extraction (review 2, C7 interval)
s = re.sub(r"\\includegraphics(\[[^\]]*\])?\{figs/([a-z_0-9]+)\.pdf\}",
           lambda m: r"\includegraphics" + (m.group(1) or "") + "{figs/" + m.group(2) + ".png}", s)

aux = {k: v for k, v in re.findall(r"\\newlabel\{([^}]+)\}\{\{([^{}]*)\}", open(f"{d}/main.aux", encoding="utf-8").read())}

# ---------------------------------------------------------------- front matter
fm = re.search(r"\\begin\{frontmatter\}(.*?)\\end\{frontmatter\}", s, re.S)
f = fm.group(1)
title = re.search(r"\\title\{(.*?)\}\n", f).group(1)
authors = re.findall(r"\\author\[([a-z]+)\]\{([^{}\\]*)(\\corref\{[a-z]+\})?\}", f)
assert len(authors) == f.count(r"\author["), "author line not parsed"
corr = re.search(r"\\cortext\[[a-z]+\]\{(.*?)\}", f).group(1)
aff = re.search(r"\\affiliation\[([a-z]+)\]\{organization=\{(.*?)\},\s*city=\{(.*?)\},\s*country=\{(.*?)\}\}", f, re.S)
keys = {aff.group(1): "a"}
names = []
for key, name, cr in authors:
    mark = keys[key] + (",\\footnote{" + corr + "}" if cr else "")
    names.append(f"{name}\\textsuperscript{{{mark}}}")
abstract = re.search(r"\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}", f, re.S).group(1)
kw = re.search(r"\\begin\{keyword\}\s*(.*?)\s*\\end\{keyword\}", f, re.S).group(1).replace(r" \sep ", ", ")
front = "\n\n".join([
    "@@TITLE@@" + title,
    "@@AUTHORS@@" + ", ".join(names),
    "@@AFFIL@@\\textsuperscript{a}" + f"{aff.group(2)}, {aff.group(3)}, {aff.group(4)}",
    "@@ABSHEAD@@Abstract",
    "@@ABS@@" + abstract,
    "@@KW@@" + kw,
])
s = s[:fm.start()] + front + "\n\n" + s[fm.end():]
s = re.sub(r"\\journal\{[^\n]*\}\n", "", s)

# ---------------------------------------------------------------- headings numbered as elsarticle prints them
sec, sub = 0, 0


APPENDIX_AT = s.find("\\appendix")   # sections after this point are lettered as elsarticle prints them


def heading(m):
    global sec, sub
    kind, star, text = m.group(1), m.group(2), m.group(3)
    if star:
        return r"\paragraph*{@@H1U@@" + text + "}"
    if APPENDIX_AT >= 0 and m.start() > APPENDIX_AT:
        if kind == "section":
            sec, sub = (sec + 1 if isinstance(sec, int) and sec >= 100 else 100), 0
            return rf"\paragraph*{{@@H1@@Appendix {chr(ord('A') + sec - 100)}. {text}}}"
        sub += 1
        return rf"\paragraph*{{@@H2@@{chr(ord('A') + sec - 100)}.{sub}. {text}}}"
    if kind == "section":
        sec, sub = sec + 1, 0
        return rf"\paragraph*{{@@H1@@{sec}. {text}}}"
    sub += 1
    return rf"\paragraph*{{@@H2@@{sec}.{sub}. {text}}}"


s = re.sub(r"\\(section|subsection)(\*?)\{([^{}]*)\}", heading, s)
# layout commands of the appendix have no Word meaning
s = re.sub(r"\\appendix\n|\\sloppy\n|\\counterwithin\{[^}]*\}\{[^}]*\}\n|\\renewcommand\{\\thetable\}[^\n]*\n", "", s)
# check against LaTeX's own numbering
for lab, num in aux.items():
    if lab.startswith("sec:"):
        pos = s.find(r"\label{" + lab + "}")
        before = s[:pos].rsplit(r"\paragraph*{@@H", 1)[1]
        assert re.match(r"[12]@@" + re.escape(num) + r"\. ", before), (lab, num, before[:30])

# ---------------------------------------------------------------- floats: captions carry the number and the layout
def group_end(s, i):
    """Index just after the brace group that opens at s[i] == '{'."""
    depth = 0
    for k in range(i, len(s)):
        depth += {"{": 1, "}": -1}.get(s[k], 0)
        if depth == 0:
            return k + 1
    raise ValueError("unbalanced braces")


def count_columns(spec):
    """Columns of a tabular(x) specification: l, c, r, X, p{..}; >{..}, <{..}, @{..}, and *{n}{..} handled."""
    n, k = 0, 0
    while k < len(spec):
        ch = spec[k]
        if ch in "<>@":
            k = group_end(spec, k + 1)
        elif ch == "*":
            e1 = group_end(spec, k + 1)
            e2 = group_end(spec, e1)
            n += int(spec[k + 2:e1 - 1]) * count_columns(spec[e1 + 1:e2 - 1])
            k = e2
        elif ch in "pmb":
            n += 1
            k = group_end(spec, k + 1)
        elif ch in "lcrX":
            n += 1
            k += 1
        else:
            k += 1
    return n


def simple_columns(body):
    """tabularx with any column specification -> tabular with plain left-aligned columns (Word layout is set later);
    \\multicolumn specifications are simplified the same way."""
    key = r"\begin{tabularx}{\textwidth}"
    while key in body:
        i = body.index(key)
        j = group_end(body, i + len(key))
        n = count_columns(body[i + len(key) + 1:j - 1])
        body = body[:i] + r"\begin{tabular}{" + "l" * n + "}" + body[j:]
    out, k = [], 0
    for m in re.finditer(r"\\multicolumn\{(\d+)\}", body):
        if m.start() < k:
            continue
        e = group_end(body, m.end())
        out.append(body[k:m.end()] + "{l}")
        k = e
    return "".join(out) + body[k:]


def mark_float(m):
    env, body = m.group(1), m.group(2)
    label = re.search(r"\\label\{([^}]+)\}", body).group(1)
    if env == "table":
        tag = f"@@TAB:{aux[label]}@@"
        body = simple_columns(body)
        body = body.replace(r"\end{tabularx}", r"\end{tabular}")
    else:
        w = re.search(r"\\includegraphics\[width=([0-9.]*)\\textwidth\]", body)
        tag = f"@@FIG:{aux[label]}:{w.group(1) or '1'}@@"
    body = body.replace(r"\caption{", r"\caption{" + tag, 1)
    body = re.sub(r"\\small|\\footnotesize|\\centering", "", body)
    return "\\begin{" + env + "}" + body + "\\end{" + env + "}"


s = re.sub(r"\\begin\{(table|figure)\}\[[^\]]*\](.*?)\\end\{\1\}", mark_float, s, flags=re.S)
# floats stand alone (pandoc would otherwise put a figure inside the paragraph it follows)
s = re.sub(r"\n*(\\begin\{(?:table|figure)\})", r"\n\n\1", s)
s = re.sub(r"(\\end\{(?:table|figure)\})\n*", r"\1\n\n", s)

# ---------------------------------------------------------------- display equations: one per number
numbers = []


def equation(m):
    body, after = m.group(1), m.group(2)
    lab = re.search(r"\\label\{([^}]+)\}", body).group(1)
    numbers.append(aux[lab])
    body = re.sub(r"\\label\{[^}]+\}", "", body).strip().rstrip(",")
    cont = "" if re.match(r"[ \t]*\n[ \t]*\n", after) else "@@NOIND@@"
    return "\\[\n" + body + "\n\\]\n" + (cont + after.lstrip(" \t\n") if cont else after)


s = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}([ \t]*\n(?:[ \t]*\n)?)", equation, s, flags=re.S)
assert numbers == [str(i) for i in range(1, len(numbers) + 1)], numbers
s = re.sub(r"\\ref\{([^}]+)\}", lambda m: aux[m.group(1)], s)
s = s.replace(r"\textmu ", "µ").replace(r"\textmu", "µ")

for bad in (r"\tableinput", r"\input{", r"\ref{", r"\begin{equation}", r"\begin{frontmatter}", r"\begin{tabularx}", r"\section"):
    assert bad not in s, bad
open(out, "w", encoding="utf-8").write(s)
json.dump({"equations": len(numbers)}, open(out + ".json", "w"))
print("flattened", len(s), "characters;", len(numbers), "equation(s)")
