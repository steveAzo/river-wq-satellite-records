"""Revision 2, Step 3c prototype: all witnesses compete for the same slot columns. Pre-registration: docs/REVISION2_PLAN.md
("Step 3c"); solver: src/p3/allocate.py; certificates: src/p3/certlang.py.

Objects per day: DO (min witness), pH (min and max witnesses), T (max witness, for the 7DADM), EC (rate pair).
Designs (Q messages, five value slots each; same loss draws for all):
  rec      record only                         flat   all witnesses inside the record code
  pet2     all witnesses in one layered group over c = 2 columns (record c = 3)
  spare    witnesses in the padding of the record's last unit, fixed order DO, pH, T, EC
  heur     the Step 3b rule generalised: hard objects layered in one group (k <= 2), easy objects in spare slots
  randmix  the same pattern as heur, assigned to random days (control)
  ex05, ex1, ex2   exact solution of the allocation problem (allocate.solve) with lambda = 0.5, 1, 2
Queries: DO below 5 mg/L; pH outside 6.5 to 9.0; conductance change above 10% in an hour; 7DADM above 20 degC.
Output per site: results/<tag>/proto_j/<site>_Q<Q>.csv (kind in do, ph, ec, win7, day).
Run from Paper3/: python -I src/p3/proto_joint.py <folder> <tag> <Q> [workers] [sites]
"""
import glob
import os
import pickle
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import allocate as al  # noqa: E402
from p3 import certlang as cl  # noqa: E402
from p3 import delivery, frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402
from p3.proto_decision import BAND, CAP, CONDS, DO_THR, PH_HI, PH_LO, group_recover, witnesses  # noqa: E402
from p3.proto_queries import EC_FRAC, EC_HARD, T_BAND, T_NEAR, T_THR, UNKNOWN_HARD, ec_witness, t_witness  # noqa: E402

SEED = 20261106
DESIGNS = ("rec", "flat", "pet2", "spare", "heur", "randmix", "ex05", "ex1", "ex2")
LAMBDA = {"ex05": 0.5, "ex1": 1.0, "ex2": 2.0}
ORDER = ("DO", "pH", "T", "EC")


def obj_values(name):
    return {"DO": [("W", "DO")], "pH": [("W", "pHmin"), ("W", "pHmax")], "T": [("W", "T")],
            "EC": [("W", "ECa"), ("W", "ECb")]}[name]


def heur_groups(R, hard, present, spare_cap_fn):
    """Hard objects in one layered group with k <= 2; easy ones in the spare slots of the record group."""
    hv = [v for o in ORDER if o in present and hard[o] for v in obj_values(o)]
    if not hv:
        cR, layered = 5, []
    else:
        cw = min(4, -(-len(hv) // 2))
        cR, layered = 5 - cw, [(hv, cw)]
    cap = spare_cap_fn(cR)
    host = []
    for o in ORDER:
        if o in present and not hard[o] and len(obj_values(o)) <= cap - len(host):
            host += obj_values(o)
    return layered + [(R + host, cR)]


def build_groups(design, it, Q, hard, cache):
    vals = it["vals"]
    V = len(vals)
    R = [("R", p) for p in range(V)]
    present = [o for o in ORDER if o != "EC" or it["ew"] is not None]
    allW = [v for o in ORDER if o in present for v in obj_values(o)]

    def spare_cap(cR):
        return -(-V // cR) * cR - V

    if design == "rec":
        return [(R, 5)]
    if design == "flat":
        return [(allW + R, 5)]
    if design == "pet2":
        return [(allW, 2), (R, 3)]
    if design == "spare":
        return [(R + allW[:spare_cap(5)], 5)]
    if design in ("heur", "randmix"):
        return heur_groups(R, hard, present, spare_cap)
    lam = LAMBDA[design]
    objs = tuple(al.Obj(o, len(obj_values(o)), 1.0, float(it["dq"][o])) for o in present)
    key = (V, Q, objs, lam)
    if key not in cache:
        cache[key] = al.solve(V, Q, objs, lam)[1]
    cR, status, groups = cache[key]
    host = [v for o in present if status.get(o) == "spare" for v in obj_values(o)]
    out = [([v for o in names for v in obj_values(o)], c) for names, c in groups]
    return out + [(R + host, cR)]


def knowledge_sets(it, key, res):
    """(DO, pH, T bounds, EC) from the received items under the certificate rules."""
    rd, vals, bound = it["rd"], it["vals"], it["bound"]
    rx = {i: vals[i] for kind, i in key if kind == "R"}
    last = len(vals) - 1 if (len(vals) - 1) in rx else None
    cert, _ = record.certify(rx, rd.n_of, bound, last)
    ch = {c.param: c for c in rd.channels}

    def kn(p):
        return cl.knowledge_from_rx(p, ch[p].n, rx, cert[p], resolution=res.get(p))

    Kd = kn("DO")
    if ("W", "DO") in key:
        Kd.add_min_witness(*it["wit"]["DOmin"][1:3])
    do = cl.exceeds_below(Kd, DO_THR)
    Kp = kn("pH")
    if ("W", "pHmin") in key:
        Kp.add_min_witness(*it["wit"]["pHmin"][1:3])
    if ("W", "pHmax") in key:
        Kp.add_max_witness(*it["wit"]["pHmax"][1:3])
    a, b = cl.exceeds_below(Kp, PH_LO), cl.exceeds_above(Kp, PH_HI)
    ph = 1 if 1 in (a, b) else (0 if (a, b) == (0, 0) else -1)
    Kt = kn("T")
    if ("W", "T") in key:
        Kt.add_max_witness(it["tw"][0], it["tw"][1])
    tb = cl.max_bounds(Kt)
    ec = None
    if it["ew"] is not None:
        Ke = kn("EC")
        if ("W", "ECa") in key and ("W", "ECb") in key:
            a_, ca, b_, cb, _ = it["ew"]
            Ke.add_rate_witness(a_, ca, b_, cb, it["lag"])
        ec = cl.relative_change(Ke, it["lag"], EC_FRAC)
    return do, ph, tb, ec


def prepare_items(path, tag):
    """Days of one site with everything the encoder knows: plan, witnesses, hard flags, truth, and d (does the full record
    alone give a certain, correct decision?). Returns (site, items sorted by day, resolutions)."""
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    recs = [rd for rd in load_site_records(path) if len(rd.channels) == 4]
    res = {p: cl.infer_resolution(np.concatenate([next(c.x for c in rd.channels if c.param == p) for rd in recs]))
           for p in ("DO", "pH", "T")} if recs else {}
    items = []
    for rd in recs:
        d = delivery.day_number(rd.day)
        if d not in P:
            continue
        vals, bound = P[d]["plan"]
        wit = witnesses(rd)
        ch = {c.param: c for c in rd.channels}
        tw = t_witness(ch["T"])
        if len(wit) < 3 or tw is None:
            continue
        lag = max(1, 60 // rd.steps["EC"])
        ew = ec_witness(ch["EC"], lag) if ch["EC"].n > lag else None
        items.append({"rd": rd, "d": d, "vals": vals, "bound": bound, "wit": wit, "tw": tw, "ew": ew, "lag": lag,
                      "tmax": tw[2]})
    items.sort(key=lambda it: it["d"])
    for i, it in enumerate(items):
        w = items[i - 6:i + 1] if i >= 6 and items[i]["d"] - items[i - 6]["d"] == 6 else None
        it["win"] = w
        it["mean7"] = float(np.mean([x["tmax"] for x in w])) if w else None
        wt = it["wit"]
        it["hard"] = {
            "DO": bool(wt["DOmin"][5] or wt["DOmin"][4] <= BAND["DO"]),
            "pH": bool(wt["pHmin"][5] or wt["pHmax"][5] or wt["pHmin"][4] <= BAND["pH"] or wt["pHmax"][4] <= BAND["pH"]),
            "T": bool(UNKNOWN_HARD) if not w else bool(abs(it["mean7"] - T_THR) <= T_BAND),
            "EC": bool(it["ew"] and it["ew"][4] >= EC_HARD)}
        it["truth"] = {"DO": bool(wt["DOmin"][5]), "pH": bool(wt["pHmin"][5] or wt["pHmax"][5]),
                       "EC": bool(it["ew"] and it["ew"][4] > EC_FRAC)}
        full = frozenset(("R", p) for p in range(len(it["vals"])))
        do, ph, _tb, ec = knowledge_sets(it, full, res)
        it["dq"] = {"DO": float(do != -1 and do == int(it["truth"]["DO"])),
                    "pH": float(ph != -1 and ph == int(it["truth"]["pH"])),
                    "T": 0.0 if it["hard"]["T"] else 1.0,
                    "EC": float(ec is not None and ec != -1 and ec == int(it["truth"]["EC"]))}
    return site, items, res


def run_site(args):
    path, tag, Q, out = args
    if os.path.exists(out):
        return out
    site, items, res = prepare_items(path, tag)
    rng = np.random.default_rng([SEED, Q, re2.site_number(site) % 100000])
    n = len(items)
    perm = np.random.default_rng([SEED, 77, re2.site_number(site) % 100000]).permutation(n) if n else []
    rows, bnd, cache = [], {}, {}
    for i, it in enumerate(items):
        for cname, c, R in CONDS:
            masks = np.ones((1, Q), bool) if c is None else rr.sim_masks(c, Q, rng, draws=R)
            for dn in DESIGNS:
                hard = items[perm[i]]["hard"] if dn == "randmix" else it["hard"]
                g = build_groups(dn, it, Q, hard, cache)
                memo, dec, full = {}, [], []
                for mask in masks:
                    got = [x for items_, cc in [(group_recover(it_, cc, mask), cc) for it_, cc in g] for x in items_]
                    key = frozenset(got)
                    full.append(bool(it["bound"]) and all(("R", p) in key for p in range(len(it["vals"]))))
                    if key not in memo:
                        memo[key] = knowledge_sets(it, key, res)
                    dec.append(memo[key])
                bnd[(cname, dn, it["d"])] = np.array([m[2] for m in dec])
                rows.append({"kind": "day", "site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn,
                             "rec_full": float(np.mean(full))})
                for kind, q, idx in (("do", "DO", 0), ("ph", "pH", 1), ("ec", "EC", 3)):
                    if q == "EC" and it["ew"] is None:
                        continue
                    arr = np.array([m[idx] for m in dec])
                    t = it["truth"][q]
                    rows.append({"kind": kind, "site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn,
                                 "truth": t, "hard": it["hard"][q],
                                 "decided_correct": float(np.mean((arr != -1) & (arr == int(t)))),
                                 "wrong": float(np.mean((arr != -1) & (arr != int(t))))})
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


def main():
    folder, tag, Q = sys.argv[1], sys.argv[2], int(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else None
    os.makedirs(f"results/{tag}/proto_j", exist_ok=True)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    jobs = [(p, tag, Q, f"results/{tag}/proto_j/{os.path.basename(p)[:-4]}_Q{Q}.csv") for p in paths]
    with Pool(workers) as pool:
        for i, o in enumerate(pool.imap_unordered(run_site, jobs), 1):
            print(i, len(jobs), o, flush=True)


if __name__ == "__main__":
    main()
