"""RQ1: values (and bytes) a site-day needs for a guaranteed record, per tolerance set.

For each site-day of a folder: the min-# count per parameter at tau = 1 (whole day within tolerance),
the total, and the raw count (all values). Bytes are reported both as 3 B per value and as whole 23-B
messages (7 values each). Output: results/<tag>/need_<tolset>.csv.
Run from Paper3/: python -I src/p3/need.py <folder> <tag> [excellent|good]
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import pla  # noqa: E402
from p3.data import load_folder  # noqa: E402

V = 7


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    tolset = sys.argv[3] if len(sys.argv) > 3 else "excellent"
    days = load_folder(folder, tolset)
    rows = []
    for i, sd in enumerate(days):
        tabs = [pla.tables(sd.X[p], sd.anchor[p], sd.tol[p]) for p in range(sd.P)]
        counts = [len(pla.min_set(s, t, 1.0)) for s, t in tabs]
        m = sum(counts)
        rows.append({"site": sd.site, "day": str(sd.day.date()), "step_min": sd.step_min, "n_par": sd.P,
                     "params": "|".join(sd.params), "values": m, "raw_values": sd.P * sd.n,
                     "messages": -(-m // V), **{f"v_{q}": c for q, c in zip(sd.params, counts)}})
        if i % 500 == 0:
            print(i, len(days), flush=True)
    out = pd.DataFrame(rows)
    os.makedirs(f"results/{tag}", exist_ok=True)
    out.to_csv(f"results/{tag}/need_{tolset}.csv", index=False)
    out["bytes"] = 3 * out["values"]
    out["share"] = out["values"] / out["raw_values"]
    print(f"{len(out)} site-days, {out.site.nunique()} sites, tolerance {tolset}")
    print("bytes/day: median %.0f p90 %.0f p99 %.0f max %.0f; share of raw: median %.3f p90 %.3f"
          % (out.bytes.median(), out.bytes.quantile(.9), out.bytes.quantile(.99), out.bytes.max(),
             out.share.median(), out.share.quantile(.9)))
    print("23-B messages/day: median %.0f p90 %.0f p99 %.0f max %.0f"
          % (out.messages.median(), out.messages.quantile(.9), out.messages.quantile(.99), out.messages.max()))


if __name__ == "__main__":
    main()
