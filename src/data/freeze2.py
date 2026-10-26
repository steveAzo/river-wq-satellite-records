"""Write docs/FREEZE2.md: the commit and tag, and MD5 checksums of the method files, the plan, and the seals.
Run from Paper3/ after the authors have approved docs/CONFIRM2_PLAN.md and committed and tagged the repository:
python -I src/data/freeze2.py <tag name>
"""
import datetime
import glob
import subprocess
import sys

sys.path.insert(0, "src")
from data.seal import md5  # noqa: E402

FILES = (sorted(glob.glob("src/p3/*.py")) + sorted(glob.glob("src/data/*.py")) + ["docs/CONFIRM2_PLAN.md",
         "results/dev/robust_choice.json", "results/dev/stats_rq4.csv", "data/raw/usgs_new2024.md5",
         "data/clean/usgs_new2024.md5"])


def main(tag):
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    tagged = subprocess.run(["git", "rev-list", "-n", "1", tag], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "docs/CONFIRM2_PLAN.md"],
                           capture_output=True, text=True).stdout.strip()
    if tagged != head or dirty:
        sys.exit(f"refusing to freeze: tag {tag} -> {tagged or 'missing'}, HEAD {head}, uncommitted: {bool(dirty)}")
    lines = ["# Freeze record for the second confirmation", "",
             f"Written {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC. Commit {head}, tag `{tag}`.",
             "The sealed cohort had not been read when this record was written.", "", "| File | MD5 |", "|---|---|"]
    lines += [f"| `{f}` | {md5(f)} |" for f in FILES]
    open("docs/FREEZE2.md", "w").write("\n".join(lines) + "\n")
    print(f"docs/FREEZE2.md written ({len(FILES)} files); commit it, then run the confirmation.")


if __name__ == "__main__":
    main(sys.argv[1])
