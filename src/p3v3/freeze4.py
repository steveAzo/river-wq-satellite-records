"""Write docs/FREEZE4.md: commit and tag, test result, and MD5 checksums of the method files, the plan, and the cohort selection.
Run from Paper3/ after the authors have approved docs/CONFIRM4_PLAN.md and committed and tagged the repository:
  python -I src/p3v3/freeze4.py confirm4-freeze
The freeze comes BEFORE the cohort is downloaded (docs/ROADMAP_V3.md, steps 5 and 6), so the record pins the selection and the
download, cleaning, and seal code, not the seal files; src/p3v3/confirm4.py verifies the seal and the site list at run time.
The script refuses to write the record if the tag is not HEAD, if method files are uncommitted, if the plan is missing, or if the
tests fail.
"""
import datetime
import glob
import os
import subprocess
import sys

sys.path.insert(0, "src")
from data.seal import md5  # noqa: E402

PLAN = "docs/CONFIRM4_PLAN.md"
DOCS = [PLAN, "docs/CERTIFICATE_SPEC.md", "docs/FRAME_SPEC_V2.md", "docs/METHOD_V3_PLAN.md", "results/confirm4/selection.csv"]
TRACKED = ["src", "tests", "tools"] + DOCS
RECORD = "docs/FREEZE4.md"
COHORT = "data/clean/usgs_new4_2022"


def files():
    out = []
    for pat in ("src/p3/*.py", "src/p3v3/*.py", "src/data/*.py", "tests/*.py", "tests/v3/*.py", "tools/*.py"):
        out += sorted(glob.glob(pat))
    return [f.replace("\\", "/") for f in out] + DOCS


def main(tag):
    missing = [f for f in DOCS if not os.path.exists(f)]
    if missing:
        sys.exit("refusing to freeze: missing " + ", ".join(missing))
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    tagged = subprocess.run(["git", "rev-list", "-n", "1", tag], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *TRACKED], capture_output=True, text=True).stdout.strip()
    if tagged != head or dirty:
        sys.exit(f"refusing to freeze: tag {tag} -> {tagged or 'missing'}, HEAD {head}, uncommitted: {bool(dirty)}")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], capture_output=True, text=True)
    last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else "no output"
    if t.returncode != 0:
        sys.exit(f"refusing to freeze: the test suite fails ({last})")
    cohort = "not present (to be downloaded after this record is committed)" if not os.path.exists(COHORT) else \
        f"PRESENT at {COHORT} when the record was written; it must not have been analysed"
    fl = files()
    lines = ["# Freeze record for the version 3 confirmation (cohort 4)", "",
             f"Written {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC. Commit {head}, tag `{tag}`.",
             f"Test suite at the freeze: {last}.", f"Cohort data: {cohort}.",
             "After this record is committed nothing in the files below changes, whatever the run shows.",
             "", "| File | MD5 |", "|---|---|"]
    lines += [f"| `{f}` | {md5(f)} |" for f in fl]
    open(RECORD, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{RECORD} written ({len(fl)} files). Commit it BEFORE the download and the run; the run is:\n"
          f"  python -I src/p3v3/confirm4.py {COHORT} confirm4 {COHORT}.md5")


if __name__ == "__main__":
    main(sys.argv[1])
