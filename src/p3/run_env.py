"""Step 8 run: environmental decisions from delivered records (docs/STEP8_PLAN.md). 2023 four-parameter days.

Designs at Q = 6 and 12: record-first code (rec_code), record-first interleaved repetition (rec_rep), every k-th
reading (every_k), satellite-tag practice (tag, channel-blind share of results/<tag>/robust_choice.json).
Conditions: perfect delivery, independent p = 0.3, Gilbert p = 0.3 (bursts of 3); 20 draws under loss, shared by
all designs of a day. Recovery uses the decoding rule checked on bytes in Steps 4 to 7. Record plans come from
the Step 7 cache (results/<tag>/plans/<site>.pkl).
Outputs: results/<tag>/env/<site>_days.csv and <site>_7dadm.csv (resumable) -> results/<tag>/env_days.csv,
env_7dadm.csv. Run from Paper3/: python -I src/p3/run_env.py <folder> <tag> [workers=3]
"""
import glob
import json
import os
import pickle
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, env  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

QS = (6, 12)
CONDS = [("perfect", None, 1), ("iid_p0.3", ("iid", 0.3, 0), 20), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3), 20)]
SEED = 20261023
CAP = 5


def designs(rd, plan, Q, choice):
    vals, bound = plan
    D1 = -(-len(vals) // CAP)
    out = {}
    if D1 <= Q:
        out["rec_code"] = (vals, bound, True, D1, list(range(Q)))
        out["rec_rep"] = (vals, bound, False, D1, delivery.cyclic(D1, Q))
    else:                                           # does not fit: the first Q units once (partial certificates)
        out["rec_code"] = out["rec_rep"] = (vals, bound, False, Q, list(range(Q)))
    s = delivery.every_k(rd, Q)
    out["every_k"] = (s.planned, s.bound, False, s.meta["units"], list(s.idx))
    j = choice[str(Q)]["tag"]["minimax"]
    s = delivery.tag(rd, Q, re2.SHARES[j], seed=re2.SEED + j)
    out["tag"] = (s.planned, s.bound, False, s.meta["units"], list(s.idx))
    return out


def recovered(coded, K, tx, mask):
    got = {u for u, ok in zip(tx, mask) if ok}
    if coded:
        return frozenset(range(K)) if len(got) >= K else frozenset(u for u in got if u < K)
    return frozenset(got)


def received(vals, units):
    rx = {p: vals[p] for u in units for p in range(CAP * u, min(CAP * u + CAP, len(vals)))}
    last = len(vals) - 1 if (len(vals) - 1) // CAP in units else None
    return rx, last


DAY_KEYS = ("DO_FN", "DO_FP", "DO_decided", "DO_wrong", "pH_FN", "pH_FP", "pH_decided", "pH_wrong",
            "EC_FN", "EC_FP")


def summarise(m):
    out = {"DO_true": m["DO_true"], "pH_true": m["pH_true"], "EC_true": m["EC_true"],
           "DO_FN": m["DO_true"] and not m["DO_naive"], "DO_FP": m["DO_naive"] and not m["DO_true"],
           "DO_decided": m["DO_3v"] != -1, "DO_wrong": m["DO_3v"] != -1 and m["DO_3v"] != int(m["DO_true"]),
           "pH_FN": m["pH_true"] and not m["pH_naive"], "pH_FP": m["pH_naive"] and not m["pH_true"],
           "pH_decided": m["pH_3v"] != -1, "pH_wrong": m["pH_3v"] != -1 and m["pH_3v"] != int(m["pH_true"]),
           "EC_FN": m["EC_true"] and not m["EC_naive"], "EC_FP": m["EC_naive"] and not m["EC_true"],
           "certified_share": m["certified_share"], "have_all": all(m["have"].values())}
    for k, v in m.items():
        if k.endswith(("_err", "_min")) and k not in out:
            out[k] = v
            if k.endswith(("_min_err", "_max_err", "_mean_err")):
                out[k.replace("_err", "_within")] = bool(np.isfinite(v) and v <= 1 + 1e-9)
    return out


def run_site(args):
    path, tag, choice, out_days, out_7 = args
    if os.path.exists(out_days):
        return out_days
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng([SEED, 8, int(site[:15]) % 100000])
    rows, tmax = [], {}
    for rd in load_site_records(path):
        d = delivery.day_number(rd.day)
        if len(rd.channels) != 4 or d not in P:
            continue
        for Q in QS:
            ds = designs(rd, P[d]["plan"], Q, choice)
            for cname, c, R in CONDS:
                masks = np.ones((1, Q), bool) if c is None else rr.sim_masks(c, Q, rng, draws=R)
                for name, (vals, bound, coded, K, tx) in ds.items():
                    cache, acc = {}, []
                    for r, mask in enumerate(masks):
                        units = recovered(coded, K, tx, mask[:len(tx)])
                        if units not in cache:
                            rx, last = received(vals, units)
                            m = env.day_metrics(rd, rx, bound, last)
                            cache[units] = (summarise(m), (m["Tmax_true"], m["Tmax_hat"], m["Tmax_lo"], m["Tmax_hi"]))
                        s, t = cache[units]
                        acc.append(s)
                        tmax.setdefault((Q, cname, name, r), {})[d] = t
                    df = pd.DataFrame(acc)
                    rows.append({"site": site, "day": d, "Q": Q, "cond": cname, "design": name, "draws": len(acc),
                                 **df.mean(numeric_only=True).to_dict()})
    pd.DataFrame(rows).to_csv(out_days + ".tmp", index=False)
    seven = []
    for (Q, cname, name, r), td in tmax.items():
        days = sorted(td)
        tr = env.seven_dadm(days, {d: v[0] for d, v in td.items()})
        hat = env.seven_dadm(days, {d: v[1] for d, v in td.items()})
        lo = env.seven_dadm(days, {d: v[2] for d, v in td.items()})
        hi = env.seven_dadm(days, {d: v[3] for d, v in td.items()})
        for d, v in tr.items():
            truth = v > env.T_7DADM
            naive = d in hat and hat[d] > env.T_7DADM
            tv = 1 if lo.get(d, -np.inf) > env.T_7DADM else (0 if hi.get(d, np.inf) <= env.T_7DADM else -1)
            seven.append({"site": site, "Q": Q, "cond": cname, "design": name, "draw": r, "window_end": d,
                          "true": truth, "FN": truth and not naive, "FP": naive and not truth,
                          "decided": tv != -1, "wrong": tv != -1 and tv != int(truth)})
    s7 = pd.DataFrame(seven)
    if len(s7):
        s7 = s7.groupby(["site", "Q", "cond", "design", "window_end"]).mean(numeric_only=True).reset_index()
    s7.to_csv(out_7, index=False)
    os.replace(out_days + ".tmp", out_days)
    return out_days


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    choice = json.load(open(f"results/{tag}/robust_choice.json"))
    os.makedirs(f"results/{tag}/env", exist_ok=True)
    jobs = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        site = os.path.basename(f)[:-4]
        if os.path.exists(f"results/{tag}/plans/{site}.pkl"):
            jobs.append((f, tag, choice, f"results/{tag}/env/{site}_days.csv", f"results/{tag}/env/{site}_7dadm.csv"))
    with Pool(workers) as pool:
        for o in pool.imap_unordered(run_site, jobs):
            print("done", o, flush=True)
    days = pd.concat([pd.read_csv(j[3], dtype={"site": str}) for j in jobs if os.path.getsize(j[3]) > 5])
    days.to_csv(f"results/{tag}/env_days.csv", index=False)
    s7 = pd.concat([pd.read_csv(j[4], dtype={"site": str}) for j in jobs if os.path.getsize(j[4]) > 5])
    s7.to_csv(f"results/{tag}/env_7dadm.csv", index=False)
    print(f"{days[['site', 'day']].drop_duplicates().shape[0]} days at {days.site.nunique()} sites; "
          f"{s7[['site', 'window_end']].drop_duplicates().shape[0]} 7-day windows")


if __name__ == "__main__":
    main()
