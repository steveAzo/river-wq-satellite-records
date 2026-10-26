"""Step 5/6 byte-level confirmation (docs/STEP5_PLAN.md, last item; review M14, E7). 2023 test days only.

Every design of the final comparison, built on bytes and decoded from the arriving bytes, under all 15 test
channels at Q = 1, 6, 12, 24, with 30 loss draws per test day. All designs of a day share the same loss masks
(common random numbers; designs that send fewer than Q messages use the first ones). Parametric designs use the
channel-blind (minimax-regret) parameters of results/<tag>/robust_choice.json.
Output: results/<tag>/robust_bytes.csv (one row per day x Q x channel x design: G_cert, G_ok, cert share).
Run from Paper3/: python -I src/p3/robust_bytes.py <folder> <tag> [n_per_site=20] [workers=3]
"""
import glob
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402

DRAWS = 30


def designs(rd, enc, Q, choice):
    c = choice.get(str(Q), {})
    out = {"mds_rec": delivery.mds_rec(rd, enc, Q), "rlnc_rec": delivery.rlnc_rec(rd, enc, Q),
           "rep_rec": delivery.rep_rec(rd, enc, Q), "rep_block_rec": delivery.rep_block_rec(rd, enc, Q),
           "tag_rec": delivery.tag_rec(rd, enc, Q, seed=re2.SEED),
           "reliable": delivery.reliable(rd, enc, Q), "every_k": delivery.every_k(rd, Q)}
    if "mds" in c:
        out["mds_fixed"] = delivery.mds(rd, enc, Q, re2.mds_ks(Q)[c["mds"]["minimax"]])
    if "repeat" in c:
        out["repeat_fixed"] = delivery.repeat(rd, enc, Q, [r for r in re2.REPEATS if r <= Q][c["repeat"]["minimax"]])
    if "tag" in c:
        j = c["tag"]["minimax"]
        out["tag"] = delivery.tag(rd, Q, re2.SHARES[j], seed=re2.SEED + j)
    return out


def run_site(args):
    path, n_per, choice, out = args
    if os.path.exists(out):
        return out
    rng = np.random.default_rng([re2.SEED, 6, int(os.path.basename(path)[:-4][:15])])
    rows = []
    for rd in re2.sample_site(path, n_per)[1::2]:
        enc = record.Encoder(rd.channels)
        for Q in re2.QS:
            ds = designs(rd, enc, Q, choice)
            for c in rr.CHANNELS:
                masks = rr.sim_masks(c, Q, rng, draws=DRAWS)
                for name, s in ds.items():
                    o = [delivery.outcome(rd, s, m[:len(s.msgs)]) for m in masks]
                    rows.append({"site": rd.site, "day": str(rd.day.date()), "Q": Q, "channel": rr.ch_name(c),
                                 "design": name, "variant": s.name, "bound": s.bound,
                                 "G_cert": np.mean([x["Phi"] for x in o]), "G_ok": np.mean([x["F"] for x in o]),
                                 "cert": np.mean([x["cert"] for x in o])})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    choice = json.load(open(f"results/{tag}/robust_choice.json"))
    os.makedirs(f"results/{tag}/robust_bytes", exist_ok=True)
    jobs = [(f, n_per, choice, f"results/{tag}/robust_bytes/{os.path.basename(f)}")
            for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
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
    df.to_csv(f"results/{tag}/robust_bytes.csv", index=False)
    print(f"{df[['site', 'day']].drop_duplicates().shape[0]} test days")
    for stat in ("G_cert", "G_ok", "cert"):
        print(f"\nQ = 6, {stat}:")
        print(df[df.Q == 6].pivot_table(index="design", columns="channel", values=stat)[
            ["iid_p0.1", "iid_p0.3", "iid_p0.5", "gilbert_p0.1_b3", "gilbert_p0.3_b3", "gilbert_p0.5_b3",
             "gilbert_p0.3_b6"]].round(3).to_string())


if __name__ == "__main__":
    main()
