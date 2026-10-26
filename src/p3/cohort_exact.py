"""Step 11: exact G_cert of every four-parameter day of a year (full cohort, not a sample; review M17).

Record-first code and record-first interleaved repetition need only each day's record size D1 (Step 7 plan cache);
every k-th reading and tag practice (channel-blind share of Step 5) are planned on bytes. Probabilities are exact
(analytic.py via run_robust.p_full). Output: results/<tag>/cohort_exact.csv (one row per day x tier x design, one
column per channel). Run from Paper3/: python -I src/p3/cohort_exact.py <folder> <tag> [workers=3]
"""
import glob
import json
import os
import pickle
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import analytic, delivery, frame  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

QS = (1, 6, 12, 24)
CH = rr.CHANNELS


@lru_cache(maxsize=None)
def p_code(D1, Q, c):
    return analytic.p_mds(D1, D1, Q, rr.ch_model(c)) if D1 <= Q else 0.0


@lru_cache(maxsize=None)
def p_rep(D1, Q, c):
    return analytic.p_units(delivery.cyclic(D1, Q), rr.ch_model(c), D1) if D1 <= Q else 0.0


def run_site(args):
    path, tag, choice, out = args
    if os.path.exists(out):
        return out
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng(0)
    rows = []
    for rd in load_site_records(path):
        d = delivery.day_number(rd.day)
        if len(rd.channels) != 4 or d not in P:
            continue
        vals, bound = P[d]["plan"]
        D1 = -(-len(vals) // frame.unit_capacity())
        month = int(rd.day.month)
        for Q in QS:
            base = {"site": site, "day": d, "month": month, "Q": Q, "D1": D1}
            rows.append({**base, "design": "rec_code", **{rr.ch_name(c): bound * p_code(D1, Q, c) for c in CH}})
            rows.append({**base, "design": "rec_rep", **{rr.ch_name(c): bound * p_rep(D1, Q, c) for c in CH}})
            s = delivery.every_k(rd, Q)
            rows.append({**base, "design": "every_k",
                         **{rr.ch_name(c): (s.bound * rr.p_full(s, c, rng)[0] if s.bound else 0.0) for c in CH}})
            j = choice[str(Q)]["tag"]["minimax"]
            s = delivery.tag(rd, Q, re2.SHARES[j], seed=re2.SEED + j)
            rows.append({**base, "design": "tag",
                         **{rr.ch_name(c): (s.bound * rr.p_full(s, c, rng)[0] if s.bound else 0.0) for c in CH}})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    choice = json.load(open(f"results/{tag}/robust_choice.json"))
    os.makedirs(f"results/{tag}/cohort_exact", exist_ok=True)
    jobs = [(f, tag, choice, f"results/{tag}/cohort_exact/{os.path.basename(f)}")
            for f in sorted(glob.glob(os.path.join(folder, "*.csv")))
            if os.path.exists(f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl")]
    with Pool(workers) as pool:
        for o in pool.imap_unordered(run_site, jobs):
            print("done", o, flush=True)
    parts = []
    for *_, o in jobs:
        try:
            parts.append(pd.read_csv(o, dtype={"site": str}))
        except pd.errors.EmptyDataError:
            pass
    df = pd.concat(parts)
    df.to_csv(f"results/{tag}/cohort_exact.csv", index=False)
    print(f"{df[['site', 'day']].drop_duplicates().shape[0]:,} four-parameter days at {df.site.nunique()} sites")


if __name__ == "__main__":
    main()
