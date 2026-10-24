"""Retry failed downloads through alternative open copies.

For each file in download_list.tsv that is missing from pdf/, look up its DOI (via OpenAlex search hits
in search/*.jsonl, matched by the publisher URL), then try in order:
  1. every Unpaywall OA location's PDF URL;
  2. Europe PMC render of the PMC copy (MDPI Sensors etc.);
  3. an arXiv paper whose title matches (case-insensitive, punctuation stripped).
A download counts only if the file starts with %PDF. Prints what is still missing.
Usage (from Paper3/papers): python -I ../src/lit/retry_downloads.py
"""
import glob
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
MAIL = "preciousstick15@gmail.com"


def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def try_pdf(url, path):
    try:
        data = get(url, 90)
    except Exception:  # noqa: BLE001
        return False
    if data[:5] == b"%PDF-":
        open(path, "wb").write(data)
        return True
    return False


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    hits = {}
    for f in glob.glob("search/*.jsonl"):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r.get("pdf"):
                hits[r["pdf"]] = r
    still = []
    for row in open("download_list.tsv", encoding="utf-8"):
        name, url = row.rstrip("\n").split("\t")
        path = f"pdf/{name}"
        try:
            if open(path, "rb").read(5) == b"%PDF-":
                continue
        except FileNotFoundError:
            pass
        r = hits.get(url, {})
        doi = (r.get("doi") or "").replace("https://doi.org/", "")
        title = r.get("title", "")
        done = False
        if doi:
            try:
                u = json.loads(get(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAIL}"))
                for loc in u.get("oa_locations") or []:
                    for cand in (loc.get("url_for_pdf"), loc.get("url")):
                        if cand and cand != url and try_pdf(cand, path):
                            done = True
                            print("unpaywall", name, cand)
                            break
                    if done:
                        break
            except Exception:  # noqa: BLE001
                pass
            if not done:
                try:
                    q = json.loads(get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
                        {"query": f'DOI:"{doi}"', "format": "json"})))
                    for res in q.get("resultList", {}).get("result", []):
                        if res.get("pmcid") and try_pdf(f"https://europepmc.org/articles/{res['pmcid']}?pdf=render", path):
                            done = True
                            print("europepmc", name)
                            break
                except Exception:  # noqa: BLE001
                    pass
        if not done and title:
            try:
                words = " AND ".join(f'ti:"{w}"' for w in re.findall(r"[A-Za-z]{5,}", title)[:6])
                root = ET.fromstring(get("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
                    {"search_query": words, "max_results": 5})))
                ns = {"a": "http://www.w3.org/2005/Atom"}
                for e in root.findall("a:entry", ns):
                    if norm(e.find("a:title", ns).text)[:60] == norm(title)[:60]:
                        aid = e.find("a:id", ns).text.rsplit("/abs/", 1)[-1]
                        if try_pdf(f"https://arxiv.org/pdf/{aid}", path):
                            done = True
                            print("arxiv", name, aid)
                            break
                time.sleep(3)
            except Exception:  # noqa: BLE001
                pass
        if not done:
            still.append((name, f"https://doi.org/{doi}" if doi else url))
    print(f"\nStill missing ({len(still)}):")
    for n, u in still:
        print(f"{n}\t{u}")


if __name__ == "__main__":
    main()
