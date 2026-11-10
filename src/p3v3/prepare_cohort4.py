"""Fetch, clean, and seal cohort 4 (docs/CONFIRM4_PLAN.md, Section 2; step 6 of docs/ROADMAP_V3.md). No value is analysed here.
Counterpart of src/data/prepare_cohort3.py with the same frozen functions (src/data/fetch_usgs.main, src/data/clean_usgs.clean_file,
src/data/seal.md5): reads results/confirm4/selection.csv (metadata only), downloads the 2022 instantaneous values of each selected site
into data/raw/usgs (resumable), cleans each file with the rules of every other cohort into data/clean/usgs_new4_2022, writes counts only to
results/confirm4/usgs_quality.json, and seals both sets (data/raw/usgs_new4_2022.md5, data/clean/usgs_new4_2022.md5). Prints counts,
never values. The freeze comes first: the script refuses to run unless the tag confirm4-freeze exists and docs/FREEZE4.md is committed.
Run from Paper3/: python -I src/p3v3/prepare_cohort4.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "data"))
import clean_usgs  # noqa: E402
import fetch_usgs  # noqa: E402
from seal import md5  # noqa: E402

START, END = "2022-01-01", "2022-12-31"
SELECTION = "results/confirm4/selection.csv"
OUT = "data/clean/usgs_new4_2022"
RAW_SEAL, CLEAN_SEAL = "data/raw/usgs_new4_2022.md5", "data/clean/usgs_new4_2022.md5"
QUALITY = "results/confirm4/usgs_quality.json"
FREEZE_TAG, FREEZE_RECORD = "confirm4-freeze", "docs/FREEZE4.md"


def check_frozen():
    """Download only after the freeze: the tag exists and the freeze record is tracked and committed."""
    def ok(*a):
        r = subprocess.run(["git", *a], capture_output=True, text=True)
        return r.returncode == 0, r.stdout.strip()
    tag_ok, commit = ok("rev-list", "-n", "1", FREEZE_TAG)
    tracked, _ = ok("ls-files", "--error-unmatch", FREEZE_RECORD)
    st_ok, dirty = ok("status", "--porcelain", "--", FREEZE_RECORD)
    if not (tag_ok and commit and tracked and st_ok and not dirty):
        sys.exit(f"refusing to download: the freeze comes first (tag {FREEZE_TAG} and a committed {FREEZE_RECORD} are required)")


def seal_lines(paths):
    return "".join(f"{md5(str(p))} *{str(p).replace(os.sep, '/')}\n" for p in paths)


def main(fetch=fetch_usgs.main, clean=clean_usgs.clean_file):
    sel = pd.read_csv(SELECTION, dtype={"site_no": str})
    sites = sorted(sel.loc[sel.selected.astype(str).str.lower() == "true", "site_no"])
    print(f"{len(sites)} selected sites", flush=True)
    Path(OUT).mkdir(parents=True, exist_ok=True)
    infos, raw_files, excluded = [], [], []
    for site in sites:
        raw = Path(f"data/raw/usgs/{site}_{START}_{END}.csv")
        if not raw.exists():
            fetch(site, START, END)
        raw_files.append(raw)
        if pd.read_csv(raw, nrows=1).empty:
            excluded.append(site)
            print({"file": raw.name, "excluded": "no data for this year"}, flush=True)
            continue
        w, info = clean(raw)
        w.to_csv(f"{OUT}/{site}.csv", index=False)
        infos.append(info)
        print({k: info[k] for k in ("file", "raw_values", "approved_values", "timestamps", "median_step_min") if k in info}, flush=True)
    os.makedirs(os.path.dirname(QUALITY), exist_ok=True)
    Path(QUALITY).write_text(json.dumps({"excluded_no_data": excluded, "files": infos}, indent=2, default=str))
    Path(RAW_SEAL).write_text(seal_lines(raw_files))
    clean_files = sorted(Path(OUT).glob("*.csv"))
    Path(CLEAN_SEAL).write_text(seal_lines(clean_files))
    print(f"sealed {len(raw_files)} raw and {len(clean_files)} clean files; excluded (no data): {excluded}", flush=True)
    print(f"next: commit {RAW_SEAL} and {CLEAN_SEAL}, then run: python -I src/p3v3/confirm4.py {OUT} confirm4 {CLEAN_SEAL}")


if __name__ == "__main__":
    check_frozen()
    main()
