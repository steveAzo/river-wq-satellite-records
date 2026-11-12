#!/bin/sh
# Build the manuscript deliverables (PDF, Word, highlights) into draft4/deliverables/ as Paper3_*_$VER.
# Usage, from Paper3/: sh paper_tools/build_v1.sh v1.1
# One file: the appendices are part of main.tex (no separate supplement since v1.1).
set -e
VER=${1:?version, e.g. v1.1}
python -I -W ignore exploratory/summarise4.py rehearsal4_2023 rehearsal4v2 confirm4 > /dev/null
cd draft4
pdflatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null || true
cp refs.bib build/
(cd build && bibtex main > /dev/null)
pdflatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null || true
pdflatex -interaction=nonstopmode -output-directory=build main.tex > /dev/null || true
if grep -q "^!\|undefined\|multiply defined" build/main.log; then grep -n "^!\|undefined\|multiply defined" build/main.log; exit 1; fi
cd ..
python -I paper_tools/check_draft_v1.py draft4 | tail -1
python -I paper_tools/check_numbers_v1.py
cd draft4
cp build/main.aux main.aux
python -I -W ignore ../paper_tools/make_word_v1.py . word_main.tex
pandoc word_main.tex -f latex -t docx --citeproc --bibliography=refs.bib --csl=elsevier-harvard.csl \
  --resource-path=. -M reference-section-title=References -o build/word_raw.docx
NEQ=$(python -I -c 'import json; print(json.load(open("word_main.tex.json"))["equations"])')
DATE=$(python -I -c 'import datetime; d = datetime.date.today(); print(d.strftime("%B ") + str(d.day) + d.strftime(", %Y"))')
python -I ../paper_tools/fix_word_v1.py build/word_raw.docx "deliverables/Paper3_draft_$VER.docx" "$NEQ" "Environmental Modelling & Software" "$DATE"
cp build/main.pdf "deliverables/Paper3_draft_$VER.pdf"
cp highlights.txt "deliverables/Paper3_highlights_$VER.txt"
rm -f word_main.tex word_main.tex.json main.aux build/word_raw.docx
ls -la deliverables
