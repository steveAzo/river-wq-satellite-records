"""RQ1 on the per-channel loader and the self-contained, quantised encoder (revision Step 4; review M10, M11).

For every record day: the planned values at tau = 1 and three size metrics, each with its denominator:
  value_share  kept values / raw readings                                   (count ratio)
  byte_share   kept values x 24 bit / raw readings x 13 bit                 (application bytes; raw time implicit)
  msgs, tx_B   ceil(kept / 5) messages of 23 B (frame v1, one record day per block), and msgs x 23 B
  raw_msgs     ceil(ceil(raw readings x 13 / 8) / 20): a LOWER bound for sending the raw readings in the same
               message size (no segment headers), so savings against it are conservative
One process per site (resumable: results/<tag>/need2/<site>.csv).
Run from Paper3/: python -I src/p3/need2.py <folder> <tag> [workers=3]
"""
import glob
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame, record  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

CAP = frame.unit_capacity(23)


def run_site(args):
    path, out = args
    if os.path.exists(out):
        return out
    rows = []
    for rd in load_site_records(path):
        plan = record.Encoder(rd.channels).plan_at(1.0)
        counts = {p: sum(v[0] == p for v in plan) for p in rd.params}
        rows.append({"site": rd.site, "day": str(rd.day.date()), "n_par": len(rd.channels),
                     "params": "|".join(rd.params), "steps": "|".join(str(rd.steps[p]) for p in rd.params),
                     "values": len(plan), "raw": rd.raw_values, **{f"v_{p}": c for p, c in counts.items()}})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def metrics(df):
    df = df.copy()
    df["value_share"] = df["values"] / df["raw"]
    df["byte_share"] = 24 * df["values"] / (13 * df["raw"])
    df["bytes"] = 3 * df["values"]
    df["msgs"] = np.ceil(df["values"] / CAP).astype(int)
    df["tx_B"] = 23 * df["msgs"]
    df["raw_msgs"] = np.ceil(np.ceil(13 * df["raw"] / 8) / 20).astype(int)
    return df


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(f"results/{tag}/need2", exist_ok=True)
    jobs = [(f, f"results/{tag}/need2/{os.path.basename(f)}") for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
    with Pool(workers) as pool:
        for out in pool.imap_unordered(run_site, jobs):
            print("done", out, flush=True)
    df = metrics(pd.concat([pd.read_csv(o, dtype={"site": str}) for _, o in jobs]))
    df.to_csv(f"results/{tag}/need2.csv", index=False)

    def line(d, label):
        print(f"  {label:38s} n={len(d):>6,}  bytes med {d.bytes.median():4.0f} p90 {d.bytes.quantile(.9):4.0f} "
              f"p99 {d.bytes.quantile(.99):4.0f} max {d.bytes.max():4.0f} | value_share {100 * d.value_share.median():.2f}% "
              f"byte_share {100 * d.byte_share.median():.2f}% | msgs med {d.msgs.median():.0f} p99 {d.msgs.quantile(.99):.0f} "
              f"max {d.msgs.max()} (raw >= {d.raw_msgs.median():.0f}) | one msg {(d.msgs <= 1).mean():.1%}")
    print(f"== {tag}: record days {len(df):,}, sites {df.site.nunique()} ==")
    four = df[df.n_par == 4]
    line(df, "all record days")
    line(four, "four-parameter days (primary)")
    line(df[df.n_par < 4], "fewer-parameter days")
    se = four.groupby("site")[["bytes", "value_share", "byte_share"]].median()
    print(f"  site-equal (four-parameter, median of site medians): bytes {se.bytes.median():.0f}, "
          f"value_share {100 * se.value_share.median():.2f}%, byte_share {100 * se.byte_share.median():.2f}%")
    single = four[~four.steps.str.contains(r"\|") | four.steps.map(lambda s: len(set(s.split("|"))) == 1)]
    for s, d in single.groupby(single.steps.str.split("|").str[0]):
        line(d, f"four-parameter, all channels {s} min")
    ex = 4 * 144
    print(f"  example: 10-min four-parameter node, {ex} readings/day: raw >= {int(np.ceil(13 * ex / 8))} B "
          f"(>= {int(np.ceil(np.ceil(13 * ex / 8) / 20))} messages)")


if __name__ == "__main__":
    main()
