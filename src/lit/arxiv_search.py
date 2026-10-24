"""arXiv API search for Paper 3 scoping (recent preprints that OpenAlex may lag on).

Usage: python -I src/lit/arxiv_search.py <out.jsonl> [--n 15] "query 1" "query 2" ...
Queries use arXiv syntax, e.g. 'abs:"satellite" AND abs:"age of information"'.
Results are sorted by submission date (newest first).
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    out, n = args.pop(0), 15
    if args and args[0] == "--n":
        args.pop(0)
        n = int(args.pop(0))
    with open(out, "a", encoding="utf-8") as fh:
        for q in args:
            url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
                {"search_query": q, "max_results": n, "sortBy": "submittedDate", "sortOrder": "descending"})
            try:
                root = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
            except Exception as e:  # noqa: BLE001
                print("ERR", q, e)
                continue
            entries = root.findall("a:entry", NS)
            print(f"\n### {q}  ({len(entries)} shown)")
            for e in entries:
                title = " ".join(e.find("a:title", NS).text.split())
                aid = e.find("a:id", NS).text.rsplit("/", 1)[-1]
                date = e.find("a:published", NS).text[:10]
                authors = [a.find("a:name", NS).text for a in e.findall("a:author", NS)]
                summ = " ".join(e.find("a:summary", NS).text.split())
                print(f"- [{date}] {aid} | {title[:140]} | {authors[0] if authors else ''}{' et al.' if len(authors) > 1 else ''}")
                fh.write(json.dumps({"q": q, "arxiv": aid, "date": date, "title": title,
                                     "authors": authors[:6], "abstract": summ}) + "\n")
            time.sleep(3)  # arXiv asks for >= 3 s between calls


if __name__ == "__main__":
    main()
