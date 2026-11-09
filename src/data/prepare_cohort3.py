"""Fetch, clean, and seal the third confirmation cohort (docs/CONFIRM3_PLAN.md, Section 2). No value is analysed here.

Reads results/confirm3/selection.csv (written by select_cohort3.py from metadata only), downloads the 2024 instantaneous values of
each selected site into data/raw/usgs (resumable), cleans each file with the same rules as every other cohort
(src/data/clean_usgs.clean_file) into data/clean/usgs_new3_2024, writes counts only to results/confirm3/usgs_quality.json, and
seals both sets with MD5 checksums (data/raw/usgs_new3_2024.md5, data/clean/usgs_new3_2024.md5). Prints counts, never values.
Run from Paper3/: python -I src/data/prepare_cohort3.py
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clean_usgs  # noqa: E402
import fetch_usgs  # noqa: E402
from seal import md5  # noqa: E402

START, END = "2024-01-01", "2024-12-31"
OUT = "data/clean/usgs_new3_2024"


def main():
    sel = pd.read_csv("results/confirm3/selection.csv", dtype={"site_no": str})
    sites = sorted(sel[sel.selected].site_no)
    print(f"{len(sites)} selected sites", flush=True)
    Path(OUT).mkdir(parents=True, exist_ok=True)
    infos, raw_files = [], []
    for site in sites:
        raw = Path(f"data/raw/usgs/{site}_{START}_{END}.csv")
        if not raw.exists():
            fetch_usgs.main(site, START, END)
        raw_files.append(raw)
        if pd.read_csv(raw, nrows=1).empty:
            print({"file": raw.name, "excluded": "no data for this year"}, flush=True)
            continue
        w, info = clean_usgs.clean_file(raw)
        w.to_csv(f"{OUT}/{site}.csv", index=False)
        infos.append(info)
        print({k: info[k] for k in ("file", "raw_values", "approved_values", "timestamps", "median_step_min")}, flush=True)
    os.makedirs("results/confirm3", exist_ok=True)
    Path("results/confirm3/usgs_quality.json").write_text(json.dumps(infos, indent=2))
    with open("data/raw/usgs_new3_2024.md5", "w") as f:
        for p in raw_files:
            f.write(f"{md5(str(p))} *{str(p).replace(os.sep, '/')}\n")
    with open("data/clean/usgs_new3_2024.md5", "w") as f:
        for p in sorted(Path(OUT).glob("*.csv")):
            f.write(f"{md5(str(p))} *{str(p).replace(os.sep, '/')}\n")
    print(f"sealed {len(raw_files)} raw and {len(list(Path(OUT).glob('*.csv')))} clean files", flush=True)


if __name__ == "__main__":
    main()
