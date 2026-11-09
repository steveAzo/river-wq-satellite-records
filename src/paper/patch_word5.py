"""Create src/paper/make_word5.py from make_word.py with the changes that draft3 needs (figure and table names with digits,
float placement options, the long hypothesis table turned into an ordinary table for Word). Run from Paper3/."""
s = open("src/paper/make_word.py", encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b)


rep(r'(tables/[a-z_]+\.tex)', r'(tables/[a-z_0-9]+\.tex)')
rep('s = re.sub(r"\\\\tableinput', 's = re.sub(r"\\\\input\\{(tables/[a-z_0-9]+\\.tex)\\}", lambda m: open(f"{d}/{m.group(1)}", encoding="utf-8").read(), s)\ns = re.sub(r"\\\\tableinput')
rep(r'figs/([a-z_]+)\.pdf', r'figs/([a-z_0-9]+)\.pdf')
rep(r'\\begin\{(table|figure)\}\[t\](.*?)\\end\{\1\}', r'\\begin\{(table|figure)\}\[[^\]]*\](.*?)\\end\{\1\}')
rep(r'body = re.sub(r"\\small|\\centering", "", body)', r'body = re.sub(r"\\small|\\footnotesize|\\centering", "", body)')
rep('s = s.replace("$-$", "\\u2212")', '''# the long hypothesis table becomes an ordinary table for Word
s = re.sub(r"\\{\\\\footnotesize\\s*\\\\begin\\{longtable\\}\\{[^\\n]*\\}\\s*\\\\caption\\{(.*?)\\}\\\\label\\{(tab:hyp)\\}\\\\\\\\(.*?)\\\\endfoot\\s*(.*?)\\\\end\\{longtable\\}\\s*\\}",
           lambda m: "\\\\begin{table}[t]\\n\\\\caption{" + m.group(1) + "}\\n\\\\label{" + m.group(2) + "}\\n\\\\begin{tabularx}{\\\\textwidth}{lllll}\\n\\\\toprule\\nID & Statement & Limit & Result (95\\\\% interval) & Outcome \\\\\\\\\\n\\\\midrule\\n" + m.group(4) + "\\\\bottomrule\\n\\\\end{tabularx}\\n\\\\end{table}",
           s, flags=re.S)
s = s.replace("$-$", "\\u2212")''')
rep('Usage (from Paper3/draft): python -I ../src/paper/make_word.py . word_main.tex', 'Usage (from Paper3/draft3): python -I ../src/paper/make_word5.py . word_main.tex')
open("src/paper/make_word5.py", "w", encoding="utf-8").write(s)
print("written")
