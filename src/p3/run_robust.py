"""Step 5, phase 1: exact G_cert of every candidate design on every channel (docs/STEP5_PLAN.md). 2023 only.

For each sampled four-parameter day (run_e2e.sample_site; even = tuning, odd = test), each tier Q, and each
candidate design, the plan is built on bytes and its probability of full certification is computed exactly
(analytic.py) under the 15 test channels: bound x P(full delivery). Orders with more than 16 distinct units that
repeat some unit fall back to 20,000 vectorised draws (column exact = False).
Output: results/<tag>/robust_exact.csv. Per site in parallel (resumable: results/<tag>/robust/<site>.csv).
Run from Paper3/: python -I src/p3/run_robust.py <folder> <tag> [n_per_site=20] [workers=3]
"""
import glob
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import analytic, delivery, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402

PS_TEST = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
CHANNELS = [("iid", p, 0) for p in PS_TEST] + [("gilbert", p, 3) for p in PS_TEST] + [("gilbert", 0.3, 6)]
TUNE_CHANNELS = [("iid", p, 0) for p in (0.1, 0.3, 0.5)] + [("gilbert", p, 3) for p in (0.1, 0.3, 0.5)]
MAX_EXACT_UNITS = 16
MC_DRAWS = 20000


def ch_name(c):
    kind, p, b = c
    return f"{kind}_p{p}" + (f"_b{b}" if kind == "gilbert" else "")


def ch_model(c):
    kind, p, b = c
    return analytic.iid(p) if kind == "iid" else analytic.gilbert(p, b)


def sim_masks(c, n, rng, draws=MC_DRAWS):
    kind, p, b = c
    if kind == "iid":
        return rng.random((draws, n)) >= p
    b2g, g2b = 1.0 / b, p / (b * (1 - p))
    bad = rng.random(draws) < p
    out = np.empty((draws, n), bool)
    for i in range(n):
        out[:, i] = ~bad
        u = rng.random(draws)
        bad = np.where(bad, u >= b2g, u < g2b)
    return out


def p_full(s, c, rng):
    """(probability of full delivery, exact?)"""
    if "K" in s.meta:
        return analytic.p_mds(s.meta["K"], s.meta["D"], len(s.msgs), ch_model(c)), True
    order = list(s.idx)
    units = sorted(set(order))
    if set(range(s.meta["units"])) - set(units):     # a unit that is never sent: full delivery impossible
        return 0.0, True
    if len(units) == len(order):
        return analytic.p_mask([True] * len(order), ch_model(c)), True
    if len(units) <= MAX_EXACT_UNITS:
        return analytic.p_units(order, ch_model(c), s.meta["units"]), True
    m = sim_masks(c, len(order), rng)
    got = np.zeros((len(m), len(units)), bool)
    pos = {u: j for j, u in enumerate(units)}
    for i, u in enumerate(order):
        got[:, pos[u]] |= m[:, i]
    return float(got.all(axis=1).mean()), False


def candidates(rd, enc, Q):
    out = re2.candidates(rd, enc, Q)
    out["mds_rec"] = [delivery.mds_rec(rd, enc, Q)]
    out["rep_rec"] = [delivery.rep_rec(rd, enc, Q)]
    out["rep_block_rec"] = [delivery.rep_block_rec(rd, enc, Q)]
    out["tag_rec"] = [delivery.tag_rec(rd, enc, Q, seed=re2.SEED)]
    return out


def run_site(args):
    path, n_per, out = args
    if os.path.exists(out):
        return out
    rng = np.random.default_rng([re2.SEED, 5, int(os.path.basename(path)[:-4][:15])])
    rows = []
    for k, rd in enumerate(re2.sample_site(path, n_per)):
        enc = record.Encoder(rd.channels)
        D1 = delivery.record_units(enc)[1]
        for Q in re2.QS:
            for fam, lst in candidates(rd, enc, Q).items():
                for j, s in enumerate(lst):
                    row = {"site": rd.site, "day": str(rd.day.date()), "split": "tune" if k % 2 == 0 else "test",
                           "Q": Q, "fam": fam, "j": j, "variant": s.name, "bound": s.bound, "planned": len(s.planned),
                           "D1": D1, "n_tx": len(s.msgs), "K": s.meta.get("K"), "exact": True}
                    for c in CHANNELS:
                        pf, ex = p_full(s, c, rng) if s.bound else (0.0, True)
                        row[ch_name(c)] = s.bound * pf
                        row["exact"] &= ex
                    rows.append(row)
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    os.makedirs(f"results/{tag}/robust", exist_ok=True)
    jobs = [(f, n_per, f"results/{tag}/robust/{os.path.basename(f)}") for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
    with Pool(workers) as pool:
        for o in pool.imap_unordered(run_site, jobs):
            print("done", o, flush=True)
    parts = []
    for _, _, o in jobs:
        try:
            parts.append(pd.read_csv(o, dtype={"site": str}))
        except pd.errors.EmptyDataError:   # a site without four-parameter days
            print("no four-parameter days:", o)
    df = pd.concat(parts)
    df.to_csv(f"results/{tag}/robust_exact.csv", index=False)
    print(f"{len(df):,} rows; days {df.groupby('split').day.size().to_dict()}; inexact rows {(~df.exact).sum()}")


if __name__ == "__main__":
    main()
