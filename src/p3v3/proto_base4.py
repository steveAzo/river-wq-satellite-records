"""Version 3, Phase 1a (docs/METHOD_V3_PLAN.md): derived from src/p3/proto_base.py by src/p3v3/patch_base3.py. DEVELOPMENT DATA ONLY.
Changes: designs and flag capacity are command-line arguments (no environment switches); new design flagsrec (decision flags that
also use the recovered record: the certificate decides when certain, otherwise the flag, no witnesses); hybrid 1 hosts its witnesses in
the spare room of the flag capacity given; seeds use the full site number; environment variables are not read.
Original header: Revision 2, Step 4: baselines against the witness designs.
Designs (Q messages, five value slots each, identical loss draws):
  rec        record only (piecewise-linear record-first code)        heur   Step 3b rule generalised
  ex1        exact allocation, lambda 1                              tight50, tight25   record at 0.5 / 0.25 of the tolerance
  sod_once   send-on-delta (hold), each unit once, no redundancy     sod_mds   send-on-delta values in the record-first code
  flags      decision flags (answers to the configured queries) in every message; record capacity 4.75 values per message
Threshold scenarios: cfg (DO 5, pH 6.5 and 9.0, 7DADM 20, conductance 10%), alt1 (4.5; 6.3, 9.2; 21; 20%), alt2 (5.5; 6.7, 8.8; 19; 5%).
Output per site and Q: results/<tag>/proto_b/<site>_Q<Q>.csv (design rows, columns dc_<scenario> = decisive-correct share,
wrong = share of wrong decisions over all scenarios, rec_full) and <site>_Q<Q>_meta.csv (truth and hard flags per day,
values per design). Run from Paper3/: python -I src/p3/proto_base.py <folder> <tag> [workers] [sites]
"""
import glob
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import certlang as cl  # noqa: E402
from p3 import frame, record, sod  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.proto_decision import CONDS, group_recover  # noqa: E402
from p3.proto_joint import ORDER, obj_values, prepare_items  # noqa: E402


SLOTS = 5                                           # value slots per message; set from the command line


def heur_groups(R, hard, present, spare_cap_fn):
    """Hard objects in one layered group with k <= 2; easy ones in the spare slots of the record group (SLOTS per message)."""
    hv = [v for o in ORDER if o in present and hard[o] for v in obj_values(o)]
    if not hv:
        cR, layered = SLOTS, []
    else:
        cw = min(SLOTS - 1, -(-len(hv) // 2))
        cR, layered = SLOTS - cw, [(hv, cw)]
    cap = spare_cap_fn(cR)
    host = []
    for o in ORDER:
        if o in present and not hard[o] and len(obj_values(o)) <= cap - len(host):
            host += obj_values(o)
    return layered + [(R + host, cR)]

SEED = 20261110
QS = (6, 12)
DESIGNS = ("rec", "heur", "ex1", "tight50", "tight25", "sod_once", "sod_mds", "flags")
HEAVY = any(d in DESIGNS for d in ("tight50", "tight25", "sod_once", "sod_mds"))
VAR = {"cfg": dict(DO=5.0, pH=(6.5, 9.0), T=20.0, EC=0.10),
       "alt1": dict(DO=4.5, pH=(6.3, 9.2), T=21.0, EC=0.20),
       "alt2": dict(DO=5.5, pH=(6.7, 8.8), T=19.0, EC=0.05)}
BANDS = {"DO": 0.6, "pH": 0.4}
FLAG_CAP = 4.0                                      # set from the command line (frame version 2 allows 4)


def recover_coded(items, c, mask):
    """group_recover for a fractional capacity c (values per message), as for the flags design."""
    Q = len(mask)
    k = -(-len(items) // c)
    if int(mask.sum()) >= k and k <= Q:
        return list(items)
    return [it for v, it in enumerate(items) if int(v // c) < Q and mask[int(v // c)]]


def recover_uncoded(items, c, mask):
    Q = len(mask)
    return [it for v, it in enumerate(items) if (v // c) < Q and mask[int(v // c)]]


def know(it, vals, bound, key, res, codec, scale):
    """Knowledge objects (DO, pH, T, EC) from the received R items (and witnesses) under the given codec."""
    rd = it["rd"]
    rx = {i: vals[i] for kind, i in key if kind == "R"}
    last = len(vals) - 1 if (len(vals) - 1) in rx else None
    ch = {c.param: c for c in rd.channels}
    if codec == "sod":
        cert = sod.certify_hold(rx, rd.n_of, last)
    else:
        cert, _ = record.certify(rx, rd.n_of, bound, last)

    def kn(p):
        if codec == "sod":
            return sod.knowledge_hold(p, ch[p].n, rx, cert[p], res.get(p))
        return cl.knowledge_from_rx(p, ch[p].n, rx, cert[p], resolution=res.get(p), scale=scale)

    Kd, Kp, Kt = kn("DO"), kn("pH"), kn("T")
    if ("W", "DO") in key:
        Kd.add_min_witness(*it["wit"]["DOmin"][1:3])
    if ("W", "pHmin") in key:
        Kp.add_min_witness(*it["wit"]["pHmin"][1:3])
    if ("W", "pHmax") in key:
        Kp.add_max_witness(*it["wit"]["pHmax"][1:3])
    if ("W", "T") in key:
        Kt.add_max_witness(it["tw"][0], it["tw"][1])
    Ke = None
    if it["ew"] is not None:
        Ke = kn("EC")
        if ("W", "ECa") in key and ("W", "ECb") in key:
            a_, ca, b_, cb, _ = it["ew"]
            Ke.add_rate_witness(a_, ca, b_, cb, it["lag"])
    return Kd, Kp, Kt, Ke


def decide(it, Ks):
    Kd, Kp, Kt, Ke = Ks
    out = {}
    for v, th in VAR.items():
        do = cl.exceeds_below(Kd, th["DO"])
        a, b = cl.exceeds_below(Kp, th["pH"][0]), cl.exceeds_above(Kp, th["pH"][1])
        ph = 1 if 1 in (a, b) else (0 if (a, b) == (0, 0) else -1)
        ec = cl.relative_change(Ke, it["lag"], th["EC"]) if Ke is not None else None
        out[v] = (do, ph, ec)
    return out, cl.max_bounds(Kt)


def flag_decisions(meta):
    """Decisions of the flags design when a message arrived: exact at cfg, monotone implications at alt thresholds."""
    out = {}
    t0 = VAR["cfg"]
    for v, th in VAR.items():
        # DO: below
        y = meta["truth"]["cfg"]["do"]
        do = y if th["DO"] == t0["DO"] else (1 if (th["DO"] > t0["DO"] and y) else (0 if (th["DO"] < t0["DO"] and not y) else -1))
        # pH: outside a range
        y = meta["truth"]["cfg"]["ph"]
        lo, hi = th["pH"]
        if (lo, hi) == t0["pH"]:
            ph = int(y)
        elif lo >= t0["pH"][0] and hi <= t0["pH"][1]:
            ph = 1 if y else -1
        elif lo <= t0["pH"][0] and hi >= t0["pH"][1]:
            ph = 0 if not y else -1
        else:
            ph = -1
        # EC: relative change above frac
        y = meta["truth"]["cfg"]["ec"]
        if y is None:
            ec = None
        elif th["EC"] == t0["EC"]:
            ec = int(y)
        else:
            ec = 1 if (th["EC"] < t0["EC"] and y) else (0 if (th["EC"] > t0["EC"] and not y) else -1)
        # T window (decided at the window level)
        y = meta["truth"]["cfg"]["win7"]
        if y is None:
            w = -1
        elif th["T"] == t0["T"]:
            w = int(y)
        else:
            w = 1 if (th["T"] < t0["T"] and y) else (0 if (th["T"] > t0["T"] and not y) else -1)
        out[v] = (do, ph, ec, w)
    return out


def day_meta(it):
    rd = it["rd"]
    ch = {c.param: c for c in rd.channels}
    live = lambda p: ~frame.saturated(frame.quantise(p, ch[p].x))
    do, ph = ch["DO"].x[live("DO")], ch["pH"].x[live("pH")]
    rate = it["ew"][4] if it["ew"] is not None else None
    truth, hard = {}, {}
    for v, th in VAR.items():
        lo, hi = th["pH"]
        truth[v] = {"do": bool(do.min() < th["DO"]), "ph": bool(ph.min() < lo or ph.max() > hi),
                    "ec": None if rate is None else bool(rate > th["EC"]),
                    "win7": None if it["mean7"] is None else bool(it["mean7"] > th["T"])}
        hard[v] = {"do": bool(truth[v]["do"] or abs(do.min() - th["DO"]) <= BANDS["DO"]),
                   "ph": bool(truth[v]["ph"] or abs(ph.min() - lo) <= BANDS["pH"] or abs(ph.max() - hi) <= BANDS["pH"]),
                   "ec": None if rate is None else bool(rate >= 0.4 * th["EC"]),
                   "win7": None if it["mean7"] is None else bool(abs(it["mean7"] - th["T"]) <= 2.0)}
    return {"truth": truth, "hard": hard}


def run_site(args):
    global DESIGNS, FLAG_CAP, HEAVY, SLOTS
    path, tag, outdir, DESIGNS, FLAG_CAP, SLOTS = args  # a spawned worker re-imports the module, so the settings travel in the job
    HEAVY = any(d in DESIGNS for d in ("tight50", "tight25", "sod_once", "sod_mds"))
    site = os.path.basename(path)[:-4]
    outs = {Q: f"{outdir}/{site}_Q{Q}.csv" for Q in QS}
    if all(os.path.exists(o) for o in outs.values()):
        return site
    site, items, res = prepare_items(path, tag)
    for it in items:
        ch = it["rd"].channels
        # a plan at tolerance s x tol and level 1 is the plan at level s on the same error tables: build them once
        if HEAVY:
            enc = record.Encoder(ch)
            it["t50"], it["t25"] = enc.plan_at(0.5), enc.plan_at(0.25)
            it["sod"] = sod.plan(ch)
        else:
            it["t50"] = it["t25"] = it["sod"] = []
        it["meta"] = day_meta(it)
    for Q in QS:
        rng = np.random.default_rng([SEED, Q, re2.site_number(site)])
        rows, metas, bnd, cache = [], [], {}, {}
        # control "randmix": the hardness pattern of heur assigned to random days (same cost profile, no targeting)
        perm = np.random.default_rng([SEED, 77, re2.site_number(site)]).permutation(len(items)) if items else []
        for i, it in enumerate(items):
            d = it["d"]
            metas.append({"site": site, "day": d, "Q": Q, "V_pla": len(it["vals"]), "V_sod": len(it["sod"]),
                          "V_t50": len(it["t50"]), "V_t25": len(it["t25"]),
                          **{f"truth_{k}_{v}": it["meta"]["truth"][v][k] for v in VAR for k in ("do", "ph", "ec", "win7")},
                          **{f"hard_{k}_{v}": it["meta"]["hard"][v][k] for v in VAR for k in ("do", "ph", "ec", "win7")}})
            for cname, c, R in CONDS:
                masks = np.ones((1, Q), bool) if c is None else rr.sim_masks(c, Q, rng, draws=R)
                for dn in DESIGNS:
                    codec, scale, vals, bound = "pla", 1.0, it["vals"], it["bound"]
                    if dn == "heur":
                        Rh = [("R", p) for p in range(len(vals))]
                        pres = [o for o in ORDER if o != "EC" or it["ew"] is not None]
                        g = heur_groups(Rh, it["hard"], pres, lambda cR, V=len(vals): -(-V // cR) * cR - V)
                        mode = "coded"
                    elif dn == "rec":
                        g, mode = [([("R", p) for p in range(len(vals))], SLOTS)], "coded"
                    elif dn in ("tight50", "tight25"):
                        vals, scale, bound = it["t50" if dn == "tight50" else "t25"], (0.5 if dn == "tight50" else 0.25), True
                        g, mode = [([("R", p) for p in range(len(vals))], 5)], "coded"
                    elif dn in ("sod_once", "sod_mds"):
                        codec, vals, bound = "sod", it["sod"], True
                        g = [([("R", p) for p in range(len(vals))], 5)]
                        mode = "uncoded" if dn == "sod_once" else "coded"
                    elif dn in ("hyb1", "hyb2", "flagsrec"):                # hybrids and the fair flags comparator
                        V = len(vals)
                        Rl = [("R", p) for p in range(V)]
                        present = [o for o in ORDER if o != "EC" or it["ew"] is not None]

                        def spare_f(cR, V=V):
                            cc = cR - (SLOTS - FLAG_CAP)
                            return int(-(-V // cc) * cc - V + 1e-9)
                        if dn == "flagsrec":
                            g = [(Rl, FLAG_CAP)]
                        elif dn == "hyb1":
                            host = []
                            for o in ORDER:
                                if o in present and len(obj_values(o)) <= spare_f(SLOTS) - len(host):
                                    host += obj_values(o)
                            g = [(Rl + host, FLAG_CAP)]
                        else:
                            g = heur_groups(Rl, it["hard"], present, spare_f)
                            g = g[:-1] + [(g[-1][0], g[-1][1] - (SLOTS - FLAG_CAP))]
                        mode = "coded"
                    else:                                                   # flags
                        g, mode = [([("R", p) for p in range(len(vals))], FLAG_CAP)], "coded"
                    memo, decs, full, bs = {}, [], [], []
                    fd = flag_decisions(it["meta"]) if dn in ("flags", "hyb1", "hyb2", "flagsrec") else None
                    for mask in masks:
                        rec_items = [x for items_, cc in g for x in (recover_uncoded(items_, cc, mask) if mode == "uncoded"
                                                                        else (recover_coded(items_, cc, mask) if dn in ("flags", "hyb1", "hyb2", "flagsrec")
                                                                              else group_recover(items_, cc, mask)))]
                        key = frozenset(rec_items)
                        full.append(bool(bound) and all(("R", p) in key for p in range(len(vals))))
                        if dn == "flags":
                            decs.append(fd if mask.any() else None)
                            bs.append(bool(mask.any()))
                            continue
                        if key not in memo:
                            memo[key] = decide(it, know(it, vals, bound, key, res, codec, scale))
                        if dn in ("hyb1", "hyb2", "flagsrec"):               # certificate when certain, else the flag
                            anyflag = bool(mask.any())
                            merged = {}
                            for v, tup in memo[key][0].items():
                                a = list(tup)
                                for i in range(3):
                                    if a[i] == -1 and anyflag and fd[v][i] is not None:
                                        a[i] = fd[v][i]
                                merged[v] = tuple(a)
                            decs.append(merged)
                            bs.append((memo[key][1], anyflag))
                            continue
                        decs.append(memo[key][0])
                        bs.append(memo[key][1])
                    bnd[(cname, dn, d)] = bs
                    row0 = {"site": site, "day": d, "Q": Q, "cond": cname, "design": dn, "rec_full": float(np.mean(full))}
                    rows.append({**row0, "kind": "day"})
                    for kind, idx in (("do", 0), ("ph", 1), ("ec", 2)):
                        r = {**row0, "kind": kind}
                        wrong = 0.0
                        for v in VAR:
                            t = it["meta"]["truth"][v][kind]
                            if t is None:
                                r[f"dc_{v}"] = np.nan
                                continue
                            arr = np.array([(-1 if x is None else x[v][idx]) for x in decs])
                            r[f"dc_{v}"] = float(np.mean((arr != -1) & (arr == int(t))))
                            wrong = max(wrong, float(np.mean((arr != -1) & (arr != int(t)))))
                        r["wrong"] = wrong
                        rows.append(r)
        # windows
        for it in items:
            if not it["win"]:
                continue
            for cname, c, R in CONDS:
                for dn in DESIGNS:
                    r = {"site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn, "kind": "win7", "rec_full": np.nan}
                    wrong = 0.0
                    for v, th in VAR.items():
                        t = it["meta"]["truth"][v]["win7"]
                        if dn == "flags":
                            fdw = flag_decisions(it["meta"])[v][3]
                            arr = np.array([fdw if a else -1 for a in bnd[(cname, "flags", it["d"])]])
                        elif dn in ("hyb1", "hyb2", "flagsrec"):
                            parts = [[b[0] for b in bnd[(cname, dn, x["d"])]] for x in it["win"]]
                            rn = min(len(p) for p in parts)
                            arr = np.array([cl.rolling_mean_decision([tuple(p[k]) for p in parts], th["T"]) for k in range(rn)])
                            fdw = flag_decisions(it["meta"])[v][3]
                            avail = np.array([b[1] for b in bnd[(cname, dn, it["d"])]][:rn])
                            arr = np.where((arr == -1) & avail, fdw, arr)
                        else:
                            parts = [bnd[(cname, dn, x["d"])] for x in it["win"]]
                            rn = min(len(p) for p in parts)
                            arr = np.array([cl.rolling_mean_decision([tuple(p[k]) for p in parts], th["T"]) for k in range(rn)])
                        r[f"dc_{v}"] = float(np.mean((arr != -1) & (arr == int(t))))
                        wrong = max(wrong, float(np.mean((arr != -1) & (arr != int(t)))))
                    r["wrong"] = wrong
                    rows.append(r)
        pd.DataFrame(rows).to_csv(outs[Q] + ".tmp", index=False)
        os.replace(outs[Q] + ".tmp", outs[Q])
        pd.DataFrame(metas).to_csv(outs[Q].replace(".csv", "_meta.csv"), index=False)
    return site


def main():
    """Usage: python -I src/p3v3/proto_base3.py <folder> <tag> <designs comma list> <flag capacity> <outname> <slots> [limit]"""
    global DESIGNS, FLAG_CAP, HEAVY, SLOTS
    folder, tag = sys.argv[1], sys.argv[2]
    DESIGNS = tuple(sys.argv[3].split(","))
    FLAG_CAP = float(sys.argv[4])
    outname = sys.argv[5]
    SLOTS = int(sys.argv[6])
    assert all(d in ("rec", "heur", "flags", "flagsrec", "hyb1", "hyb2") for d in DESIGNS)
    limit = int(sys.argv[7]) if len(sys.argv) > 7 else None
    HEAVY = any(d in DESIGNS for d in ("tight50", "tight25", "sod_once", "sod_mds"))
    workers = 1
    outdir = f"results/v3dev/{tag}_{outname}"
    os.makedirs(outdir, exist_ok=True)
    open(f"{outdir}/RUN.txt", "w").write(f"designs={DESIGNS} flag_cap={FLAG_CAP} slots={SLOTS} seed={SEED} folder={folder}\n")
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    with Pool(workers) as pool:
        for i, s in enumerate(pool.imap_unordered(run_site, [(p, tag, outdir, DESIGNS, FLAG_CAP, SLOTS) for p in paths]), 1):
            print(i, len(paths), s, flush=True)


if __name__ == "__main__":
    main()
