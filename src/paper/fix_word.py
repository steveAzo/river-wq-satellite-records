"""Give the pandoc Word copy of the Paper 3 draft the layout of the elsarticle PDF (run by draft/build.sh).

  - US Letter, the PDF's text block (110.9-pt side margins, 388.6-pt text width);
  - Times New Roman throughout (the PDF uses Times through newtx): 12-pt body on a 14.45-pt line pitch,
    17.5-pt paragraph indent, justified; 17-pt centred title, 12-pt authors, small italic affiliation;
  - the abstract between two rules, with "Keywords:" in italics, and the corresponding-author note as a "*" footnote;
  - bold numbered section headings ("1. Introduction"), italic subsection headings ("2.1. ..."), bold unnumbered
    back-matter headings;
  - "Figure 1:" below figures and "Table 1:" above sentence-case table captions (no caps: the supervisor's rule),
    10-pt captions, booktabs-style rules and 11-pt text in tables;
  - the display equation centred with its number at the right margin;
  - references with a hanging indent; no number on page 1, a centred page number on later pages (as in the PDF).
Layout markers (@@...@@) come from src/paper/make_word.py; every marker must be consumed.
Usage: python -I src/paper/fix_word.py in.docx out.docx n_equations journal date
"""
import re
import sys

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree

src, dst, n_eq, journal, date = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
doc = docx.Document(src)
body = doc.element.body
FONT = "Times New Roman"
PAGE_W, PAGE_H = 12240, 15840                 # US Letter (twips)
MARGIN_LR = 2218                              # 110.9 pt, as in the PDF
MARGIN_T, MARGIN_B = 2420, 2160
TEXT_W = PAGE_W - 2 * MARGIN_LR               # 388.6 pt
LINE = 289                                    # 14.45-pt line pitch of the 12-pt body
INDENT = 350                                  # 17.5-pt paragraph indent
EMU_PER_TWIP = 635
MATH = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"

ORDER = {
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
           "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd "
           "snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment "
           "textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
    "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid "
           "vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs "
           "em lang eastAsianLayout specVanish oMath",
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing "
             "tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription",
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark",
    "sectPr": "headerReference footerReference footnotePr endnotePr type pgSz pgMar paperSrc pgBorders lnNumType "
              "pgNumType cols formProt vAlign noEndnote titlePg textDirection bidi rtlGutter docGrid printerSettings",
}
ORDER = {k: v.split() for k, v in ORDER.items()}


def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


def child(parent, tag, **attrs):
    """Replace parent's <tag> with a new one carrying attrs, inserted at its schema position."""
    old = parent.find(qn(tag))
    if old is not None:
        parent.remove(old)
    new = el(tag, **attrs)
    seq = ORDER.get(parent.tag.split("}")[1])
    if seq is None:
        parent.append(new)
        return new
    pos = seq.index(tag.split(":")[1])
    for i, c in enumerate(parent):
        name = c.tag.split("}")[1] if "}" in c.tag else c.tag
        if name in seq and seq.index(name) > pos:
            parent.insert(i, new)
            return new
    parent.append(new)
    return new


def get_rpr(r):
    rp = r.find(qn("w:rPr"))
    if rp is None:
        rp = el("w:rPr")
        r.insert(0, rp)
    return rp


def ppr(p):
    pp = p.find(qn("w:pPr"))
    if pp is None:
        pp = el("w:pPr")
        p.insert(0, pp)
    return pp


def ptext(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def take_marker(p, pattern):
    """Remove a leading @@...@@ marker from paragraph p and return its regex match."""
    ts = list(p.iter(qn("w:t")))
    m = re.match(pattern, ts[0].text or "")
    assert m, (pattern, ptext(p)[:60])
    ts[0].text = ts[0].text[m.end():]
    return m


def run(text, bold=False, italic=False, size=None, sup=False):
    r = el("w:r")
    rp = el("w:rPr")
    if bold:
        rp.append(el("w:b"))
    if italic:
        rp.append(el("w:i"))
    if size:
        rp.append(el("w:sz", val=size))
        rp.append(el("w:szCs", val=size))
    if sup:
        rp.append(el("w:vertAlign", val="superscript"))
    r.append(rp)
    for i, part in enumerate(text.split("\t")):
        if i:
            r.append(el("w:tab"))
        if part:
            t = el("w:t")
            t.text = part
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            r.append(t)
    return r


def insert_first_run(p, r):
    pp = p.find(qn("w:pPr"))
    (pp.addnext(r) if pp is not None else p.insert(0, r))


def size_runs(p, size):
    for r in p.iter(qn("w:r")):
        rp = get_rpr(r)
        child(rp, "w:sz", val=size)
        child(rp, "w:szCs", val=size)
    mark = child(ppr(p), "w:rPr")
    mark.append(el("w:sz", val=size))
    mark.append(el("w:szCs", val=size))


def para(p, style=None, jc=None, before=None, after=None, first=None, left=None, hanging=None, keep=False, line=LINE):
    pp = ppr(p)
    if style:
        child(pp, "w:pStyle", val=style)
    if keep:
        child(pp, "w:keepNext")
    sp = {}
    if before is not None:
        sp["before"] = before
    if after is not None:
        sp["after"] = after
    if line:
        sp.update(line=line, lineRule="exact" if line == LINE else "auto")
    if sp:
        child(pp, "w:spacing", **sp)
    ind = {}
    if first is not None:
        ind["firstLine"] = first
    if left is not None:
        ind["left"] = left
    if hanging is not None:
        ind["hanging"] = hanging
    if ind:
        child(pp, "w:ind", **ind)
    if jc:
        child(pp, "w:jc", val=jc)


# ---------------------------------------------------------------- styles
def fonts(rpr):
    f = rpr.find(qn("w:rFonts"))
    if f is not None:
        rpr.remove(f)
    rpr.insert(0, el("w:rFonts", ascii=FONT, hAnsi=FONT, cs=FONT, eastAsia=FONT))


def style(name, size=24, bold=False, italic=False, jc="both", before=0, after=0, first=None, left=None,
          hanging=None, keep=False, line=LINE):
    try:
        st = doc.styles[name]
    except KeyError:
        return
    rpr = st.element.get_or_add_rPr()
    fonts(rpr)
    child(rpr, "w:b", val=int(bold))
    child(rpr, "w:bCs", val=int(bold))
    child(rpr, "w:i", val=int(italic))
    child(rpr, "w:iCs", val=int(italic))
    child(rpr, "w:color", val="000000")
    child(rpr, "w:u", val="none")
    if name == "Hyperlink":                     # links (DOIs) keep the size of the text around them
        for tag in ("w:sz", "w:szCs"):
            e = rpr.find(qn(tag))
            if e is not None:
                rpr.remove(e)
        return
    child(rpr, "w:sz", val=size)
    child(rpr, "w:szCs", val=size)
    pf = st.element.get_or_add_pPr()
    if keep:
        child(pf, "w:keepNext")
    sp = dict(before=before, after=after)
    if line:
        sp.update(line=line, lineRule="exact" if line == LINE else "auto")
    child(pf, "w:spacing", **sp)
    ind = {}
    if first is not None:
        ind["firstLine"] = first
    if left is not None:
        ind["left"] = left
    if hanging is not None:
        ind["hanging"] = hanging
    child(pf, "w:ind", **(ind or {"firstLine": 0}))
    if jc:
        child(pf, "w:jc", val=jc)


dd = doc.styles.element.find(qn("w:docDefaults"))
drpr = dd.find(qn("w:rPrDefault")).find(qn("w:rPr"))
fonts(drpr)
for tag in ("w:sz", "w:szCs"):
    child(drpr, tag, val=24)
dppr = dd.find(qn("w:pPrDefault"))
if dppr is not None and dppr.find(qn("w:pPr")) is not None:
    child(dppr.find(qn("w:pPr")), "w:spacing", before=0, after=0, line=LINE, lineRule="exact")

style("Normal")
style("Body Text", first=INDENT)
style("First Paragraph", first=INDENT)
style("Compact")
for h in ("Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5"):
    style(h, bold=True, jc="left", before=360, after=180, keep=True)
style("Table Caption", size=20, jc="center", before=280, after=100, keep=True, line=240)
style("Image Caption", size=20, before=100, after=240, line=240)
style("Captioned Figure", jc="center", before=240, keep=True, line=None)
style("Figure", jc="center", before=240, keep=True, line=None)
style("Bibliography", left=234, hanging=234, after=200)
style("Footnote Text", size=20, line=240)
style("Hyperlink")

# ---------------------------------------------------------------- front matter, headings, continuation lines
foot_ids = []
for p in list(body.iter(qn("w:p"))):
    t = ptext(p)
    if t.startswith("@@TITLE@@"):
        take_marker(p, r"@@TITLE@@")
        para(p, style="Normal", jc="center", before=0, after=360, line=240, first=0)
        size_runs(p, 34)
    elif t.startswith("@@AUTHORS@@"):
        take_marker(p, r"@@AUTHORS@@")
        para(p, style="Normal", jc="center", after=160, first=0)
        refs = list(p.iter(qn("w:footnoteReference")))
        assert len(refs) == 1, "expected one corresponding-author footnote"
        refs[0].set(qn("w:customMarkFollows"), "1")
        foot_ids.append(refs[0].get(qn("w:id")))
        refs[0].getparent().addnext(run("∗", sup=True))
    elif t.startswith("@@AFFIL@@"):
        take_marker(p, r"@@AFFIL@@")
        para(p, style="Normal", jc="center", after=560, first=0, line=240)
        for r in p.iter(qn("w:r")):
            child(get_rpr(r), "w:i")
        size_runs(p, 16)
    elif t.startswith("@@ABSHEAD@@"):
        take_marker(p, r"@@ABSHEAD@@")
        para(p, style="Normal", jc="left", after=160, first=0, keep=True)
        bd = child(ppr(p), "w:pBdr")
        bd.append(el("w:top", val="single", sz=6, space=8, color="000000"))
        for r in p.iter(qn("w:r")):
            child(get_rpr(r), "w:b")
    elif t.startswith("@@ABS@@"):
        take_marker(p, r"@@ABS@@")
        para(p, style="Normal", jc="both", after=160, first=0)
    elif t.startswith("@@KW@@"):
        take_marker(p, r"@@KW@@")
        para(p, style="Normal", jc="left", after=400, first=0)
        insert_first_run(p, run("Keywords: ", italic=True))
        bd = child(ppr(p), "w:pBdr")
        bd.append(el("w:bottom", val="single", sz=6, space=8, color="000000"))
        # the body starts on a new page, as in the PDF
        nxt = p.getnext()
        while nxt is not None and nxt.tag != qn("w:p"):
            nxt = nxt.getnext()
        child(ppr(nxt), "w:pageBreakBefore")
    elif t.startswith("@@H1U@@") or t.startswith("@@H1@@") or t.startswith("@@H2@@"):
        m = take_marker(p, r"@@(H1U|H1|H2)@@")
        italic = m.group(1) == "H2"
        para(p, style="Normal", jc="left", before=360 if not italic else 240, after=180 if not italic else 120,
             first=0, keep=True)
        for r in p.iter(qn("w:r")):
            rp = get_rpr(r)
            child(rp, "w:b", val=int(not italic))
            child(rp, "w:i", val=int(italic))
    elif t.startswith("@@NOIND@@"):
        take_marker(p, r"@@NOIND@@")
        child(ppr(p), "w:ind", firstLine=0)

# the corresponding-author note: "*" instead of a number
fpart = next(r.target_part for r in doc.part.rels.values() if r.reltype.endswith("/footnotes"))
froot = fpart.element if hasattr(fpart, "element") else etree.fromstring(fpart.blob)
for fn in froot.findall(qn("w:footnote")):
    if fn.get(qn("w:id")) in foot_ids:
        for mark in list(fn.iter(qn("w:footnoteRef"))):
            r = mark.getparent()
            r.addprevious(run("∗", sup=True))
            r.getparent().remove(r)
        for t in fn.iter(qn("w:t")):
            if t.text and t.text.strip() and t.text != "∗":
                t.text = t.text.lstrip()
                break
if not hasattr(fpart, "element"):
    fpart._blob = etree.tostring(froot, xml_declaration=True, encoding="UTF-8", standalone=True)

# ---------------------------------------------------------------- tables
n_tab = 0
for tbl in list(body.iter(qn("w:tbl"))):
    cap = tbl.getprevious()
    m = re.match(r"@@TAB:(\d+)@@", ptext(cap) if cap is not None else "")
    assert m, "table without a numbered caption"
    take_marker(cap, r"@@TAB:\d+@@")
    insert_first_run(cap, run(f"Table {m.group(1)}: "))
    n_tab += 1
    tp = tbl.find(qn("w:tblPr"))
    child(tp, "w:tblW", w=5000, type="pct")
    child(tp, "w:jc", val="center")
    b = child(tp, "w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b.append(el("w:" + side, val="single", sz=8, space=0, color="000000") if side in ("top", "bottom")
                 else el("w:" + side, val="nil"))
    mar = child(tp, "w:tblCellMar")
    mar.append(el("w:left", w=60, type="dxa"))
    mar.append(el("w:right", w=60, type="dxa"))
    rows = tbl.findall(qn("w:tr"))
    head = [r for r in rows if r.find(qn("w:trPr") + "/" + qn("w:tblHeader")) is not None] or rows[:1]
    for i, r in enumerate(head):
        for tc in r.findall(qn("w:tc")):
            span = tc.find(qn("w:tcPr") + "/" + qn("w:gridSpan"))
            if i == len(head) - 1 or (span is not None and int(span.get(qn("w:val"))) > 1 and ptext(tc).strip()):
                tcp = tc.find(qn("w:tcPr"))
                if tcp is None:
                    tcp = el("w:tcPr")
                    tc.insert(0, tcp)
                bd = child(tcp, "w:tcBorders")
                bd.append(el("w:bottom", val="single", sz=4, space=0, color="000000"))
    for r in rows:                              # keep each table in one piece, as LaTeX floats are
        trp = r.find(qn("w:trPr"))
        if trp is None:
            trp = el("w:trPr")
            r.insert(0, trp)
        if trp.find(qn("w:cantSplit")) is None:
            trp.insert(0, el("w:cantSplit"))
        if r is not rows[-1]:
            for p in r.iter(qn("w:p")):
                child(ppr(p), "w:keepNext")
    for tc in tbl.iter(qn("w:tc")):            # short entries (numbers, "p = 0.1") stay on one line
        if len(ptext(tc).strip()) <= 9:
            tcp = tc.find(qn("w:tcPr"))
            if tcp is None:
                tcp = el("w:tcPr")
                tc.insert(0, tcp)
            child(tcp, "w:noWrap")
    for p in tbl.iter(qn("w:p")):
        para(p, before=30, after=30, first=0, line=250)
        size_runs(p, 22)
        for r in p.iter(MATH + "r"):
            rp = el("w:rPr")
            rp.append(el("w:sz", val=22))
            rp.append(el("w:szCs", val=22))
            mrp = r.find(MATH + "rPr")
            (mrp.addnext(rp) if mrp is not None else r.insert(0, rp))
    # space after the table, as LaTeX leaves below a float
    after = tbl.getnext()
    if after is not None and after.tag == qn("w:p"):
        child(ppr(after), "w:spacing", before=240, line=LINE, lineRule="exact")

# ---------------------------------------------------------------- figures
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
n_fig = 0
for p in list(body.iter(qn("w:p"))):
    m = re.match(r"@@FIG:(\d+):([0-9.]+)@@", ptext(p))
    if not m:
        continue
    take_marker(p, r"@@FIG:\d+:[0-9.]+@@")
    insert_first_run(p, run(f"Figure {m.group(1)}: "))
    n_fig += 1
    fig = p.getprevious()
    assert fig is not None and fig.find(".//" + qn("w:drawing")) is not None, "caption without a figure"
    # a figure line must grow with the picture (the body's exact line pitch would crop it to one line)
    child(ppr(fig), "w:spacing", before=240, after=0, line=240, lineRule="auto")
    child(ppr(fig), "w:ind", firstLine=0)
    child(ppr(fig), "w:jc", val="center")
    width = round(TEXT_W * float(m.group(2))) * EMU_PER_TWIP
    ext = fig.find(".//" + WP + "extent")
    cx, cy = int(ext.get("cx")), int(ext.get("cy"))
    h = round(cy * width / cx)
    ext.set("cx", str(width))
    ext.set("cy", str(h))
    for e in fig.iter(A + "ext"):
        if e.get("cx"):
            e.set("cx", str(width))
            e.set("cy", str(h))

# ---------------------------------------------------------------- display equations: centred, number at the right
eqs = [p for p in body.iter(qn("w:p")) if p.find(MATH + "oMathPara") is not None]
assert len(eqs) == n_eq, (len(eqs), n_eq)
NUM_W, PAD_W = 600, 600
widths = (PAD_W, TEXT_W - PAD_W - NUM_W, NUM_W)
for k, p in enumerate(eqs, 1):
    tbl = el("w:tbl")
    tp = el("w:tblPr")
    tp.append(el("w:tblW", w=TEXT_W, type="dxa"))
    tp.append(el("w:jc", val="center"))
    nob = el("w:tblBorders")
    for side_ in ("top", "left", "bottom", "right", "insideH", "insideV"):
        nob.append(el("w:" + side_, val="nil"))
    tp.append(nob)
    tp.append(el("w:tblLayout", type="fixed"))
    mar = el("w:tblCellMar")
    mar.append(el("w:left", w=0, type="dxa"))
    mar.append(el("w:right", w=0, type="dxa"))
    tp.append(mar)
    tbl.append(tp)
    grid = el("w:tblGrid")
    for w in widths:
        grid.append(el("w:gridCol", w=w))
    tbl.append(grid)
    tr = el("w:tr")
    tr.append(el("w:trPr"))
    tr[0].append(el("w:cantSplit"))
    tbl.append(tr)
    for i, w in enumerate(widths):
        tc = el("w:tc")
        tcp = el("w:tcPr")
        tcp.append(el("w:tcW", w=w, type="dxa"))
        cb = el("w:tcBorders")
        for side_ in ("top", "left", "bottom", "right"):
            cb.append(el("w:" + side_, val="nil"))
        tcp.append(cb)
        tcp.append(el("w:vAlign", val="center"))
        tc.append(tcp)
        q = el("w:p")
        qp = el("w:pPr")
        qp.append(el("w:pStyle", val="Normal"))
        qp.append(el("w:spacing", before=120, after=120, line=240, lineRule="auto"))
        qp.append(el("w:jc", val=("center", "center", "right")[i]))
        q.append(qp)
        if i == 1:
            q.append(p.find(MATH + "oMathPara"))
        elif i == 2:
            q.append(run(f"({k})"))
        tc.append(q)
        tr.append(tc)
    p.addprevious(tbl)
    p.getparent().remove(p)

# ---------------------------------------------------------------- page, first-page preprint line, page numbers
final = body.find(qn("w:sectPr"))
for c in list(final):
    if c.tag.split("}")[1] in ("pgSz", "pgMar", "cols", "titlePg"):
        final.remove(c)
child(final, "w:pgSz", w=PAGE_W, h=PAGE_H)
child(final, "w:pgMar", top=MARGIN_T, right=MARGIN_LR, bottom=MARGIN_B, left=MARGIN_LR, header=720, footer=1300, gutter=0)
child(final, "w:cols", num=1, space=0)
child(final, "w:titlePg")
sec = doc.sections[0]
sec.different_first_page_header_footer = True
fp = sec.first_page_footer.paragraphs[0]._p     # page 1 has no footer line or number, as in the PDF
child(ppr(fp), "w:ind", firstLine=0)
del journal, date                                 # kept in the call for a preprint line if one is wanted
op = sec.footer.paragraphs[0]._p
fld = el("w:fldSimple", instr="PAGE")
fld.append(run("2"))
op.append(fld)
child(ppr(op), "w:jc", val="center")
child(ppr(op), "w:ind", firstLine=0)

left = [ptext(p)[:50] for p in body.iter(qn("w:p")) if "@@" in ptext(p)]
assert not left, f"unconsumed layout markers: {left}"
doc.save(dst)
print(f"Word layout: elsarticle preprint, {n_tab} tables, {n_fig} figures, {n_eq} equation(s), saved {dst}")
