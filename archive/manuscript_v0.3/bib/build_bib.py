"""Build draft/refs.bib: DOI entries fetched from doi.org (publisher metadata), plus hand-written entries
for works without a DOI (each checked against the document in papers/).
Run from Paper3/draft/bib: python -I build_bib.py   (needs network; caches responses in cache/)
"""
import json
import os
import re
import time
import urllib.request

DOIS = {
    "soroush2008": "10.1145/1374618.1374670",
    "deligiannakis2007": "10.1007/s00778-005-0173-5",
    "deligiannakis2004": "10.1007/978-3-540-24741-8_38",
    "olston2003": "10.1145/872757.872825",
    "ganesan2003": "10.1145/958491.958502",
    "barbarioli2023": "10.1145/3588953",
    "boehme2009": "10.5194/os-5-685-2009",
    "photopoulou2015": "10.1186/s40317-015-0053-8",
    "centenaro2021": "10.1109/COMST.2021.3078433",
    "capez2022": "10.1109/TAES.2022.3185970",
    "tondo2021": "10.3390/s21217099",
    "alvarez2022": "10.1109/ACCESS.2022.3189647",
    "afhamisis2022": "10.1109/ACCESS.2022.3146021",
    "abdelfadeel2020": "10.1109/JIOT.2019.2949918",
    "ahmedi2022": "10.1016/j.dib.2022.108486",
    "ahmedi2022data": "10.17632/krzv3g6d5f.1",
    "adumanu2020": "10.1155/2020/8897126",
    "adumanu2017": "10.1145/3005719",
    "yates2021": "10.1109/JSAC.2021.3065072",
    "chen2021": "10.1109/INFOCOM42981.2021.9488702",
    "reed1960": "10.1137/0108018",
    "gilbert1960": "10.1002/j.1538-7305.1960.tb03959.x",
    "elliott1963": "10.1002/j.1538-7305.1963.tb00955.x",
    "duncan2020": "10.1155/2020/2378560",
    "albanese1996": "10.1109/18.556670",
    "talli2026": "10.48550/arXiv.2609.20569",
    "ramachandran2026": "10.48550/arXiv.2609.37995",
    "rathi2025": "10.48550/arXiv.2501.11984",
    "gandhi2009": "10.1145/1559845.1559926",
    # added in the revision (2026-10-26; each DOI checked against its title)
    "campbell2013": "10.1525/bio.2013.63.7.10",
    "horsburgh2015": "10.1016/j.envsoft.2015.04.002",
    "jakeman2006": "10.1016/j.envsoft.2006.01.004",
    "hutton2016": "10.1002/2016WR019285",
    "rode2016": "10.1021/acs.est.6b02155",
    "appling2018": "10.1002/2017JG004140",
    "luby2002": "10.1109/SFCS.2002.1181950",
    "ho2006": "10.1109/TIT.2006.881746",
    "field2007": "10.1111/j.1467-9868.2007.00593.x",
    "orourke1981": "10.1145/358746.358758",
    "zordan2014": "10.1145/2629660",
    # added at the final check (2026-10-27; each DOI checked against its title)
    "lin2019": "10.3390/en12132523",
    "lin2025": "10.3390/s25010145",
    "chaubey2022": "10.1109/TII.2022.3192966",
    "essawy2020": "10.1016/j.envsoft.2020.104753",
    "choi2021": "10.1016/j.envsoft.2020.104888",
}

MANUAL = r"""
@techreport{wagner2006,
  author      = {Wagner, Richard J. and Boulger, Jr., Robert W. and Oblinger, Carolyn J. and Smith, Brett A.},
  title       = {Guidelines and standard procedures for continuous water-quality monitors: station operation, record computation, and data reporting},
  institution = {{U.S. Geological Survey}},
  type        = {Techniques and Methods},
  number      = {1-D3},
  address     = {Reston, VA, USA},
  year        = {2006},
  doi         = {10.3133/tm1D3}
}

@techreport{epa1986gold,
  author      = {{U.S. Environmental Protection Agency}},
  title       = {Quality criteria for water 1986},
  institution = {Office of Water Regulations and Standards},
  number      = {EPA 440/5-86-001},
  address     = {Washington, DC, USA},
  year        = {1986}
}

@techreport{epa1986do,
  author      = {{U.S. Environmental Protection Agency}},
  title       = {Ambient water quality criteria for dissolved oxygen},
  institution = {Office of Water Regulations and Standards},
  number      = {EPA 440/5-86-003},
  address     = {Washington, DC, USA},
  year        = {1986}
}

@techreport{epa2003temp,
  author      = {{U.S. Environmental Protection Agency}},
  title       = {{EPA} Region 10 guidance for Pacific Northwest state and tribal temperature water quality standards},
  institution = {Region 10 Office of Water},
  number      = {EPA 910-B-03-002},
  address     = {Seattle, WA, USA},
  year        = {2003}
}

@misc{kineis2024formats,
  author       = {{Kin\'eis}},
  title        = {Distribution formats: {JSON} formats (help centre)},
  howpublished = {\url{https://kineis.helpjuice.com/distribution-formats/json-formats}},
  year         = {2024},
  note         = {Accessed 25 October 2026}
}

@misc{usgs2016nwis,
  author       = {{U.S. Geological Survey}},
  title        = {National Water Information System data available on the World Wide Web ({USGS} Water Data for the Nation)},
  year         = {2016},
  doi          = {10.5066/F7P55KJN},
  note         = {Instantaneous values for 2023 and 2024, accessed October 2026}
}
@incollection{imai1988,
  author    = {Imai, Hiroshi and Iri, Masao},
  title     = {Polygonal approximations of a curve: formulations and algorithms},
  booktitle = {Computational Morphology},
  editor    = {Toussaint, Godfried T.},
  publisher = {North-Holland},
  address   = {Amsterdam},
  year      = {1988},
  pages     = {71--86}
}


@misc{kineis2023kim1,
  author       = {{Kin\'eis}},
  title        = {{KIM1} {Kin\'eis} module: product datasheet ({KINEIS-MU-22-0032})},
  howpublished = {Kin\'eis, Ramonville-Saint-Agne, France},
  year         = {2023},
  note         = {Accessed 23 October 2026}
}

@misc{azongo2026code,
  author       = {Azongo, Stephen Kwaku and Adu-Manu, Kofi Sarpong},
  title        = {river-wq-satellite-records, version v2.0.0: code, data, and results},
  howpublished = {Zenodo, software},
  year         = {2026},
  doi          = {10.5281/zenodo.23711183}
}

"""


def fetch(doi):
    os.makedirs("cache", exist_ok=True)
    path = os.path.join("cache", re.sub(r"[^A-Za-z0-9]", "_", doi) + ".bib")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    req = urllib.request.Request(f"https://doi.org/{doi}", headers={"Accept": "application/x-bibtex; charset=utf-8",
                                                                     "User-Agent": "Paper3-bib (mailto:knana4196@gmail.com)"})
    txt = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    open(path, "w", encoding="utf-8").write(txt)
    time.sleep(0.5)
    return txt


PROPER = {"Kosovo", "Ghana", "Ashanti", "Fena", "Argos", "Reed", "Solomon", "Kalman", "GF", "Aloha", "ALOHA"}
ARXIV_NOTES = {
    "rathi2025": "Presented at the IEEE International Conference on Advanced Networks and Telecommunications Systems (ANTS 2024); arXiv preprint arXiv:2501.11984",
}
# corrections to publisher metadata (each checked against the document in papers/)
FIXES = {
    "benson1984": [("atmosphere1", "atmosphere")],              # footnote mark in the Crossref title
    "deligiannakis2007": [("year={2006}", "year={2007}")],     # online 2006; issue 16(4) is 2007
    "deligiannakis2004": [("@inbook{", "@incollection{"),      # so that the book title is printed
                          ("publisher={Springer", "series={Lecture Notes in Computer Science}, volume={2992}, "
                           "address={Berlin, Heidelberg}, publisher={Springer")],
}


def protect_title(bib):
    """Brace acronyms, mixed-case words, and proper nouns in the title so that the Harvard style's
    sentence-casing keeps them (LoRaWAN, IoT, CTD, Kosovo, ...)."""
    m = re.search(r"(\btitle\s*=\s*\{)(.+?)(\},)", bib, re.S)
    if not m:
        return bib

    def keep(part):
        return sum(c.isupper() for c in part) >= 2 or part in PROPER

    def fix(word):
        core = word.strip(":,;.()")
        if not core or "{" in core:
            return word
        parts = core.split("-")
        if not any(keep(p) for p in parts):
            return word
        return word.replace(core, "-".join("{" + p + "}" if keep(p) else p for p in parts))
    title = " ".join(fix(w) for w in m.group(2).split(" "))
    return bib[:m.start(2)] + title + bib[m.end(2):]


def main():
    out, report = [], {}
    for key, doi in DOIS.items():
        try:
            bib = fetch(doi).strip()
        except Exception as e:  # noqa: BLE001
            print("FAILED", key, doi, e)
            continue
        bib = re.sub(r"^@(\w+)\{[^,]*,", lambda m: f"@{m.group(1)}{{{key},", bib, count=1)
        bib = re.sub(r"\s*url\s*=\s*\{[^}]*\},?", "", bib)
        bib = bib.replace("$FREE$ —", "{FREE}: ").replace("—", "---").replace("–", "--")
        bib = bib.replace("‘", "`").replace("’", "'").replace("“", "``").replace("”", "''")
        bib = bib.replace("&amp;", "&")
        bib = bib.replace("author = {{Lule Ahmedi}}", "author = {Ahmedi, Lule}")  # DataCite gives a literal name
        bib = re.sub(r"(?<!\\)&", lambda m: "\\&", bib)  # a bare & is a LaTeX alignment character
        for a, b in FIXES.get(key, []):
            assert a in bib, (key, a)
            bib = bib.replace(a, b)
        bib = protect_title(bib)
        if "arxiv" in doi.lower():
            note = ARXIV_NOTES.get(key, "arXiv preprint arXiv:" + doi.split("arXiv.")[-1])
            bib = bib.rstrip().rstrip("}").rstrip().rstrip(",") + f", note={{{note}}} }}"
        if key == "photopoulou2015" and "pages" not in bib:
            bib = bib.rstrip().rstrip("}").rstrip().rstrip(",") + ", pages={21} }"
        out.append(bib)
        title = re.search(r"title\s*=\s*\{(.+?)\},", bib, re.S)
        report[key] = title.group(1)[:90] if title else "?"
    out.append(MANUAL.strip())
    open("../refs.bib", "w", encoding="utf-8").write("\n\n".join(out) + "\n")
    for k, t in report.items():
        print(f"{k:18s} {t}")


if __name__ == "__main__":
    main()
