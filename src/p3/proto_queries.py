"""Revision 2, Step 3b prototype: witnesses for the two queries where simple min/max does not suffice, tested one at a time.
Criteria: docs/REVISION2_PLAN.md ("Step 3b criteria"). Certificates: docs/CERTIFICATE_SPEC.md (rate witness in certlang).

  7DADM  seven-day mean of daily maximum temperature above 20 degC. Witness: the day's maximum temperature (one kept
         value). Per day and draw the server holds an interval for the daily maximum (certlang.max_bounds); a window
         combines seven days with independent loss, draw by draw (rolling_mean_decision).
  EC     some pair of conductance readings one hour apart changes by more than 10%. Witness: the pair of kept values
         that realises the day's largest hourly relative change (two values; certlang.add_rate_witness).

Message model, designs and the control are those of proto_decision.py (five value slots per message; a group of n values
over c columns is a systematic MDS code of dimension ceil(n / c)); designs: rec, flat, pet1, pet2, spare, adapt (witness
columns only on hard days, else spare slots), randmix (the adapt pattern on random days).
Output per site: results/<tag>/proto_q/<site>_Q<Q>.csv with kind in {win7, ec, day} (day = record recovery per design).
Run from Paper3/: python -I src/p3/proto_queries.py <folder> <tag> <Q> [workers] [sites]
"""
import glob
import os
import pickle
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import certlang as cl  # noqa: E402
from p3 import delivery, frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402
from p3.proto_decision import CAP, CONDS, group_recover  # noqa: E402

SEED = 20261104
DESIGNS = ("rec", "flat", "pet1", "pet2", "spare", "adapt", "randmix")
T_THR = 20.0
T_BAND = float(os.environ.get("P3_TBAND", "3.0"))          # hardness band of the allocation (window metrics keep 2.0); tuned on development data
T_NEAR = 2.0
UNKNOWN_HARD = os.environ.get("P3_UNKNOWN", "1") == "1"      # without a full seven-day history the node cannot rule out a near window
EC_FRAC, EC_HARD = 0.10, 0.04


def groups(design, W, vals, hard):
    R = [("R", p) for p in range(len(vals))]
    spare = -(-len(vals) // CAP) * CAP - len(vals)
    if design == "rec":
        return [(R, 5)]
    if design == "flat":
        return [(W + R, 5)]
    if design == "pet1":
        return [(W, 1), (R, 4)]
    if design == "pet2":
        return [(W, 2), (R, 3)]
    if design == "spare":
        return [(R + W[:spare], 5)]
    if design in ("adapt", "randmix"):
        return [(W, 1), (R, 4)] if hard else [(R + W[:spare], 5)]
    raise ValueError(design)


def t_witness(ch):
    codes = frame.quantise("T", ch.x)
    idx = np.flatnonzero(~frame.saturated(codes))
    if not len(idx):
        return None
    s = int(idx[np.argmax(ch.x[idx])])
    return s, int(codes[s]), float(ch.x[s])


def ec_witness(ch, lag):
    codes = frame.quantise("EC", ch.x)
    ok = ~frame.saturated(codes)
    best, arg = -1.0, None
    for t in range(ch.n - lag):
        if ok[t] and ok[t + lag] and ch.x[t] > 0:
            r = abs(ch.x[t + lag] - ch.x[t]) / ch.x[t]
            if r > best:
                best, arg = r, t
    if arg is None:
        return None
    return arg, int(codes[arg]), arg + lag, int(codes[arg + lag]), best


def known(rd, vals, bound, got, param, res):
    rx = {i: vals[i] for kind, i in got if kind == "R"}
    last = len(vals) - 1 if (len(vals) - 1) in rx else None
    cert, _ = record.certify(rx, rd.n_of, bound, last)
    ch = next(c for c in rd.channels if c.param == param)
    return cl.knowledge_from_rx(param, ch.n, rx, cert[param], resolution=res)


def run_site(args):
    path, tag, Q, out = args
    if os.path.exists(out):
        return out
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng([SEED, Q, re2.site_number(site) % 100000])
    recs = [rd for rd in load_site_records(path) if len(rd.channels) == 4]
    allT = [next(c.x for c in rd.channels if c.param == "T") for rd in recs]
    resT = cl.infer_resolution(np.concatenate(allT)) if recs else None
    items = []
    for rd in recs:
        d = delivery.day_number(rd.day)
        if d not in P:
            continue
        vals, bound = P[d]["plan"]
        ch = {c.param: c for c in rd.channels}
        tw = t_witness(ch["T"])
        lag = max(1, 60 // rd.steps["EC"])
        ew = ec_witness(ch["EC"], lag) if ch["EC"].n > lag else None
        if tw is None:
            continue
        items.append({"rd": rd, "d": d, "vals": vals, "bound": bound, "tw": tw, "ew": ew, "lag": lag, "tmax": tw[2]})
    items.sort(key=lambda it: it["d"])
    n = len(items)
    # seven-day windows of consecutive days; the node knows the trailing mean at the end of each day
    for i, it in enumerate(items):
        w = items[i - 6:i + 1] if i >= 6 and items[i]["d"] - items[i - 6]["d"] == 6 else None
        it["win"] = w
        it["mean7"] = float(np.mean([x["tmax"] for x in w])) if w else None
        it["hard7"] = bool(UNKNOWN_HARD) if not w else bool(abs(it["mean7"] - T_THR) <= T_BAND)
        it["hard_ec"] = bool(it["ew"] and it["ew"][4] >= EC_HARD)
    perm = np.random.default_rng([SEED, 77, re2.site_number(site) % 100000]).permutation(n) if n else []
    rows, bnd = [], {}
    for i, it in enumerate(items):
        rd, vals, bound = it["rd"], it["vals"], it["bound"]
        Wt = [("W", "Tmax")]
        Wec = [("W", "ECa"), ("W", "ECb")]
        for cname, c, R in CONDS:
            masks = np.ones((1, Q), bool) if c is None else rr.sim_masks(c, Q, rng, draws=R)
            for dn in DESIGNS:
                h7 = items[perm[i]]["hard7"] if dn == "randmix" else it["hard7"]
                hec = items[perm[i]]["hard_ec"] if dn == "randmix" else it["hard_ec"]
                for kind, W, hard in (("t", Wt, h7), ("ec", Wec, hec)):
                    if kind == "ec" and it["ew"] is None:
                        continue
                    g = groups(dn, W, vals, hard)
                    cache, dec, full = {}, [], []
                    for mask in masks:
                        got = [x for items_, cc in groups_recover(g, mask) for x in items_]
                        key = frozenset(got)
                        full.append(bool(bound) and all(("R", p) in key for p in range(len(vals))))
                        if key not in cache:
                            if kind == "t":
                                K = known(rd, vals, bound, got, "T", resT)
                                if ("W", "Tmax") in key:
                                    K.add_max_witness(it["tw"][0], it["tw"][1])
                                cache[key] = cl.max_bounds(K)
                            else:
                                K = known(rd, vals, bound, got, "EC", None)
                                if ("W", "ECa") in key and ("W", "ECb") in key:
                                    a, ca, b, cb, _ = it["ew"]
                                    K.add_rate_witness(a, ca, b, cb, it["lag"])
                                cache[key] = cl.relative_change(K, it["lag"], EC_FRAC)
                        dec.append(cache[key])
                    if kind == "t":
                        bnd[(cname, dn, it["d"])] = np.array(dec)
                        rows.append({"kind": "day", "site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn,
                                     "rec_full": float(np.mean(full))})
                    else:
                        truth = bool(it["ew"][4] > EC_FRAC)
                        dec = np.array(dec)
                        rows.append({"kind": "ec", "site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn,
                                     "truth": truth, "hard": it["hard_ec"],
                                     "decided_correct": float(np.mean((dec != -1) & (dec == int(truth)))),
                                     "wrong": float(np.mean((dec != -1) & (dec != int(truth)))),
                                     "rec_full": float(np.mean(full))})
    for it in items:
        if not it["win"]:
            continue
        truth = bool(it["mean7"] > T_THR)
        for cname, c, R in CONDS:
            for dn in DESIGNS:
                arrs = [bnd.get((cname, dn, x["d"])) for x in it["win"]]
                if any(a is None for a in arrs):
                    continue
                r_n = min(len(a) for a in arrs)
                dec = np.array([cl.rolling_mean_decision([tuple(a[r]) for a in arrs], T_THR) for r in range(r_n)])
                rows.append({"kind": "win7", "site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn,
                             "truth": truth, "hard": bool(abs(it["mean7"] - T_THR) <= T_NEAR),
                             "decided_correct": float(np.mean((dec != -1) & (dec == int(truth)))),
                             "wrong": float(np.mean((dec != -1) & (dec != int(truth))))})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def groups_recover(g, mask):
    return [(group_recover(items_, cc, mask), cc) for items_, cc in g]


def main():
    folder, tag, Q = sys.argv[1], sys.argv[2], int(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else None
    sub = "proto_q" if (T_BAND == 3.0 and UNKNOWN_HARD) else f"proto_q_b{T_BAND:g}" + ("_u" if UNKNOWN_HARD else "")
    os.makedirs(f"results/{tag}/{sub}", exist_ok=True)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    jobs = [(p, tag, Q, f"results/{tag}/{sub}/{os.path.basename(p)[:-4]}_Q{Q}.csv") for p in paths]
    with Pool(workers) as pool:
        for i, o in enumerate(pool.imap_unordered(run_site, jobs), 1):
            print(i, len(jobs), o, flush=True)


if __name__ == "__main__":
    main()
