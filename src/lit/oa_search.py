"""OpenAlex literature search for Paper 3 scoping.

Usage: python -I src/lit/oa_search.py <out.jsonl> [--n 15] [--since 2015] "query 1" "query 2" ...
Prints one line per hit (year, cites, venue, title, doi, open PDF) and appends
each hit, with its reconstructed abstract, to <out.jsonl>.
"""
import json
import sys
import time
import urllib.parse
import urllib.request


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = [(i, word) for word, idx in inv.items() for i in idx]
    return " ".join(word for _, word in sorted(pos))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    out, n, since = args.pop(0), 15, None
    while args and args[0].startswith("--"):
        flag = args.pop(0)
        if flag == "--n":
            n = int(args.pop(0))
        elif flag == "--since":
            since = args.pop(0)
    with open(out, "a", encoding="utf-8") as fh:
        for q in args:
            params = {"search": q, "per-page": n, "mailto": "preciousstick15@gmail.com"}
            if since:
                params["filter"] = f"from_publication_date:{since}-01-01"
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
            try:
                r = json.load(urllib.request.urlopen(url, timeout=60))
            except Exception as e:  # noqa: BLE001 - report and continue
                print("ERR", q, e)
                continue
            print(f"\n### {q}  (total {r['meta']['count']})")
            for w in r["results"]:
                src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
                pdf = (w.get("best_oa_location") or {}).get("pdf_url")
                print(f"- [{w['publication_year']}] c={w['cited_by_count']} | {(w['display_name'] or '')[:130]} | {src} | {w.get('doi')} | pdf={'Y' if pdf else '-'}")
                fh.write(json.dumps({"q": q, "id": w["id"], "title": w["display_name"], "year": w["publication_year"],
                                     "venue": src, "cites": w["cited_by_count"], "doi": w.get("doi"), "pdf": pdf,
                                     "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:6],
                                     "abstract": abstract(w)}) + "\n")
            time.sleep(0.25)


if __name__ == "__main__":
    main()
