"""Write docs/FREEZE3.md: the commit and tag, the test result, and MD5 checksums of the method files, the plan, and the seals.
Run from Paper3/ after the authors have approved docs/CONFIRM3_PLAN.md and committed and tagged the repository:
python -I src/data/freeze3.py <tag name>
The script refuses to write the record if the tag is not HEAD, if tracked method files are uncommitted, or if the tests fail.
"""
import datetime
import glob
import subprocess
import sys

sys.path.insert(0, "src")
from data.seal import md5  # noqa: E402

FILES = (sorted(glob.glob("src/p3/*.py")) + sorted(glob.glob("src/data/*.py")) + sorted(glob.glob("tests/*.py"))
         + ["tools/mutation_check.py", "docs/CONFIRM3_PLAN.md", "docs/CERTIFICATE_SPEC.md", "docs/FRAME_SPEC_V2.md",
            "docs/REVISION2_PLAN.md", "results/confirm3/selection.csv", "data/raw/usgs_new3_2024.md5",
            "data/clean/usgs_new3_2024.md5"])


def main(tag):
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    tagged = subprocess.run(["git", "rev-list", "-n", "1", tag], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "tests", "tools", "docs/CONFIRM3_PLAN.md",
                            "docs/CERTIFICATE_SPEC.md", "docs/FRAME_SPEC_V2.md", "docs/REVISION2_PLAN.md",
                            "results/confirm3/selection.csv", "data/raw/usgs_new3_2024.md5", "data/clean/usgs_new3_2024.md5"],
                           capture_output=True, text=True).stdout.strip()
    if tagged != head or dirty:
        sys.exit(f"refusing to freeze: tag {tag} -> {tagged or 'missing'}, HEAD {head}, uncommitted: {bool(dirty)}")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"], capture_output=True, text=True)
    last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else "no output"
    if t.returncode != 0:
        sys.exit(f"refusing to freeze: the test suite fails ({last})")
    verify = subprocess.run([sys.executable, "-I", "src/data/seal.py", "verify", "data/clean/usgs_new3_2024.md5"],
                            capture_output=True, text=True)
    if verify.returncode != 0:
        sys.exit("refusing to freeze: the clean-data seal does not verify\n" + verify.stdout[-300:])
    lines = ["# Freeze record for the third confirmation", "",
             f"Written {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC. Commit {head}, tag `{tag}`.",
             f"Test suite at the freeze: {last}.", "Seal check at the freeze: data/clean/usgs_new3_2024.md5 verified.",
             "The sealed cohort had not been analysed when this record was written (the seal check hashes files and parses nothing).",
             "", "| File | MD5 |", "|---|---|"]
    lines += [f"| `{f}` | {md5(f)} |" for f in FILES]
    open("docs/FREEZE3.md", "w").write("\n".join(lines) + "\n")
    print(f"docs/FREEZE3.md written ({len(FILES)} files); commit it, then run: python -I src/p3/confirm3.py "
          f"data/clean/usgs_new3_2024 confirm3 data/clean/usgs_new3_2024.md5")


if __name__ == "__main__":
    main(sys.argv[1])
