"""Sensitivity of RQ3 to the message size (study plan Section 8, step 6; exploratory).

Repeats the confirmatory RQ3 run (run_confirm.py: same sample, seed, frozen tuning) with V values per
message instead of 7. V = 6 is the 19-byte "standard message" (1 B header + 6 x 3 B). The design
parameters tuned on 2023 with 23-byte messages are kept unchanged, which is conservative for the tuned designs.
Output: results/sens/<tag>_rq3_V<V>.csv
Run from Paper3/: python -I src/p3/sens_rq3.py <folder> <tag> <V> [Q list, e.g. 6]
"""
import functools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import designs  # noqa: E402
from p3 import run_confirm, run_dev  # noqa: E402


def main():
    folder, tag, V = sys.argv[1], sys.argv[2], int(sys.argv[3])
    if len(sys.argv) > 4:                     # optional plan sizes, e.g. "6" (the paper reports 6 messages/day)
        run_dev.QS = tuple(int(q) for q in sys.argv[4].split(","))
    for name in ("raw_periodic", "srdl_style", "reliable_opt", "repeat_r", "mds_K"):
        setattr(designs, name, functools.partial(getattr(designs, name), V=V))
    sys.argv = [sys.argv[0], folder, f"{tag}_V{V}"]
    out = f"results/confirm/{tag}_V{V}_rq3.csv"
    run_confirm.main()
    os.makedirs("results/sens", exist_ok=True)
    os.replace(out, f"results/sens/{tag}_rq3_V{V}.csv")


if __name__ == "__main__":
    main()
