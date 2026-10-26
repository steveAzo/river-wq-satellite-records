"""Price of self-contained days (revision Step 3; review M3, E2). Development data only.

For every eligible site-day, the need at tau = 1 (quantisation-exact encoder, record.py) under three
head rules, at the same per-value tolerances:
  self    no anchor: the first kept value is held back to midnight (every day decodes alone)
  chain   anchor = previous calendar day's last planned value (chain plan, dequantised), if that day was
          eligible; otherwise the channel starts as in "self"
  oracle  anchor = the true previous reading (the draft's model; no server holds it)
One process per site (resumable: results/<tag>/modes/<site>.csv).
Run from Paper3/: python -I src/p3/need_modes.py <folder> <tag> [workers=3]
"""
import glob
import os
import sys
from multiprocessing import Pool

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame, record  # noqa: E402
from p3.data import load_site  # noqa: E402


def run_site(args):
    path, out = args
    if os.path.exists(out):
        return out
    rows, prev_day, prev_last = [], None, {}
    for sd in load_site(path):
        chs = record.channels_from_siteday(sd)
        chained = prev_day is not None and (sd.day - prev_day).days == 1
        row = {"site": sd.site, "day": str(sd.day.date()), "step_min": sd.step_min, "n_par": sd.P,
               "chained": chained}
        last = {}
        for ch, (pi, name) in zip(chs, [(sd.params.index(c.param), c.param) for c in chs]):
            tab = record.tables(ch)
            s_self = record.min_set(tab, 1.0)
            anchor = prev_last.get(name) if chained else None
            s_chain = s_self if anchor is None else record.min_set(record.with_anchor(tab, ch, anchor), 1.0)
            s_orc = record.min_set(record.with_anchor(tab, ch, float(sd.anchor[pi])), 1.0)
            row[f"self_{name}"], row[f"chain_{name}"], row[f"oracle_{name}"] = len(s_self), len(s_chain), len(s_orc)
            last[name] = float(frame.dequantise(name, tab["codes"][s_chain[-1]]))
        for m in ("self", "chain", "oracle"):
            row[m] = sum(v for k, v in row.items() if k.startswith(m + "_"))
        rows.append(row)
        prev_day, prev_last = sd.day, last
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(f"results/{tag}/modes", exist_ok=True)
    jobs = [(f, f"results/{tag}/modes/{os.path.basename(f)}") for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
    with Pool(workers) as pool:
        for out in pool.imap_unordered(run_site, jobs):
            print("done", out, flush=True)
    df = pd.concat([pd.read_csv(o, dtype={"site": str}) for _, o in jobs])
    df.to_csv(f"results/{tag}/need_modes.csv", index=False)
    four = df[df.n_par == 4]
    for name, d in (("all", df), ("four-parameter", four)):
        print(f"\n{name} site-days: {len(d)}")
        for m in ("oracle", "chain", "self"):
            b = 3 * d[m]
            print(f"  {m:7s} bytes/day median {b.median():5.1f} mean {b.mean():6.1f} p99 {b.quantile(.99):6.1f} max {b.max():5.0f}"
                  f"  one 23-B message (<= 5 values) {(d[m] <= 5).mean():.1%}")
        print(f"  self - chain values/day: mean {(d.self - d.chain).mean():.2f}, median {(d.self - d.chain).median():.0f}, "
              f"days with no extra cost {(d.self == d.chain).mean():.1%}")


if __name__ == "__main__":
    main()
