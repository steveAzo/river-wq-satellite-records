#!/bin/sh
# Rebuild the Paper 3 draft from the results (run from Paper3/):  sh draft/build.sh
# 1. numbers and tables  2. figures (Fig. 1 from figs/arch.tex)  3. bibliography  4. checks
# 5. PDF (elsarticle, author-year)  6. Word copy (pandoc, then the PDF's layout by fix_word.py)
set -e
VER=v0.3
python -I src/paper/numbers3.py
python -I -W ignore src/paper/make_figures3.py
python -I src/paper/supplement.py
(cd draft/figs && pdflatex -interaction=nonstopmode arch.tex > /dev/null && pdftoppm -r 300 -png -singlefile arch.pdf arch \
  && rm -f arch.aux arch.log)
(cd draft/bib && python -I build_bib.py > /dev/null)
python -I src/paper/check_draft.py draft
cd draft
mkdir -p deliverables build
pdflatex -interaction=nonstopmode main.tex > build1.log
bibtex main > bib.log
pdflatex -interaction=nonstopmode main.tex > build2.log
pdflatex -interaction=nonstopmode main.tex > build3.log
if grep -q "^!" main.log; then echo "LaTeX errors: see draft/main.log"; exit 1; fi
if grep -qi "undefined" main.log; then echo "undefined references or citations: see draft/main.log"; grep -i undefined main.log | head; exit 1; fi
cp main.pdf deliverables/Paper3_draft_$VER.pdf
pdflatex -interaction=nonstopmode supplement.tex > supp1.log && pdflatex -interaction=nonstopmode supplement.tex > supp2.log
cp supplement.pdf deliverables/Paper3_supplement_$VER.pdf
# Word copy: the same sources flattened (numbers, tables, figures as PNG, references resolved from main.aux)
python -I ../src/paper/make_word.py . word_main.tex
pandoc word_main.tex -f latex -t docx --citeproc --bibliography=refs.bib --csl=elsevier-harvard.csl \
  --resource-path=. -M reference-section-title=References -o word_raw.docx
python -I ../src/paper/fix_word.py word_raw.docx deliverables/Paper3_draft_$VER.docx \
  "$(python -I -c 'import json; print(json.load(open("word_main.tex.json"))["equations"])')" \
  "Environmental Modelling & Software" "$(python -I -c 'import datetime; d = datetime.date.today(); print(d.strftime("%B ") + str(d.day) + d.strftime(", %Y"))')"
cp highlights.txt deliverables/Paper3_highlights_$VER.txt
rm -f word_main.tex word_main.tex.json word_raw.docx
mv -f *.aux *.bbl *.blg *.log *.out *.spl build/ 2>/dev/null || true
echo "built draft/deliverables/ ($VER), LaTeX intermediates in draft/build/"
