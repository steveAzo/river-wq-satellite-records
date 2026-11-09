"""Revision 2, Step 3 go/no-go prototype: do decision witnesses raise the share of days with a CERTAIN CORRECT
threshold decision at equal bytes? (docs/REVISION2_PLAN.md; certificates: docs/CERTIFICATE_SPEC.md)

Model. A message has CAP = 5 value slots (one 20-byte unit). A GROUP of n values using c slot columns is a systematic
MDS code of dimension k = ceil(n / c) per column: value v sits at data position v // c (message index = position);
the whole group is recovered when at least k of the Q messages arrive; below that, the values whose own message
arrived are still usable (systematic). Positions >= Q are never sent. Columns of all groups sum to at most 5, so every
design uses exactly the same Q messages. The record group with c = 5 is the record-first code of Step 5.

Designs (Q messages per day):
  rec        record only (the current design)
  flat       3 witnesses (DO min, pH min, pH max) then the record, one group, c = 5   ("send min/max always")
  pet2       witnesses in their own group c = 2 (k = 2), record in a group c = 3      (priority layering)
  pet1       witnesses in a group c = 1 (k = 3), record in a group c = 4
  spare      witnesses ride in the padding slots of the record's last unit (fixed order); the record is unchanged
  adapt      decision-aware: witnesses of HARD queries (event, or within the near band) get their own protected column
             group (c = 1 for up to 2, else 2); easy witnesses ride in padding; the record keeps the other columns
  spare_adapt  as spare, but the witnesses nearest their thresholds get the spare slots first (decision-aware)
Rules: 'old' = span-only (tolerance interval of every certified reading, no cells, no witnesses; the Step 8 rule with the
same float padding); 'new' = certlang (kept values by quantiser cell, witnesses); 'grid' = new plus the reporting-resolution
assumption R (intervals snapped inward to the decimal grid of the site profile). Queries: DO below 5 mg/L; pH outside 6.5 to 9.0.
Outputs one CSV per site (resumable). Run from Paper3/: python -I src/p3/proto_decision.py <folder> <tag> <Q> [workers] [sites] [designs,comma,separated]
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
from p3 import delivery, env, frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

CAP = 5
SEED = 20261103
CONDS = [("perfect", None, 1), ("iid_p0.3", ("iid", 0.3, 0), 20), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3), 20)]
DO_THR, PH_LO, PH_HI = 5.0, 6.5, 9.0
DESIGNS = ("rec", "flat", "pet2", "pet1", "spare", "spare_adapt", "adapt")   # plus the control "randmix" (run separately)
BAND = {"DO": 0.6, "pH": 0.4}                # near-threshold band (2 tolerances at the threshold)


def witnesses(rd):
    """Honest witnesses over the uncensored readings: {name: (param, slot, code, kind, margin)}; margin is the
    distance of the extremum from the nearest threshold of its query (smaller = harder to decide from the record)."""
    ch = {c.param: c for c in rd.channels}
    out = {}
    for name, p, kind, thr in (("DOmin", "DO", "min", DO_THR), ("pHmin", "pH", "min", PH_LO),
                               ("pHmax", "pH", "max", PH_HI)):
        codes = frame.quantise(p, ch[p].x)
        idx = np.flatnonzero(~frame.saturated(codes))
        if not len(idx):
            continue
        s = int(idx[np.argmin(ch[p].x[idx])] if kind == "min" else idx[np.argmax(ch[p].x[idx])])
        v = float(ch[p].x[s])
        out[name] = (p, s, int(codes[s]), kind, abs(v - thr), (v < thr) if kind == "min" else (v > thr))
    return out


def group_recover(items, c, mask):
    """Items recovered from one group under the arrival mask of the Q messages."""
    Q = len(mask)
    n = len(items)
    k = -(-n // c)
    if int(mask.sum()) >= k and k <= Q:
        return list(items)
    return [it for v, it in enumerate(items) if (v // c) < Q and mask[v // c]]


def design_groups(name, wit, vals):
    names = list(wit)
    W = [("W", n) for n in names]
    R = [("R", p) for p in range(len(vals))]
    spare = -(-len(vals) // CAP) * CAP - len(vals)
    if name == "rec":
        return [(R, 5)]
    if name == "flat":
        return [(W + R, 5)]
    if name == "pet2":
        return [(W, 2), (R, 3)]
    if name == "pet1":
        return [(W, 1), (R, 4)]
    if name == "spare":                       # witnesses ride in the padding of the record's last unit, fixed order
        return [(R + W[:spare], 5)]
    if name == "spare_adapt":                 # the witnesses nearest their thresholds get the spare slots first
        order = sorted(names, key=lambda n: (wit[n][4] if wit[n] else 0.0))
        return [(R + [("W", n) for n in order[:spare]], 5)]
    if name == "adapt":                       # decision-aware: protect witnesses only where the record cannot decide
        hard = [n for n in names if wit[n] and (wit[n][5] or wit[n][4] <= BAND[wit[n][0]])]
        easy = [n for n in names if n not in hard]
        c = 0 if not hard else (1 if len(hard) <= 2 else 2)
        cols = CAP - c
        sp = -(-len(vals) // cols) * cols - len(vals)
        g = [(R + [("W", n) for n in easy[:sp]], cols)]
        return ([(([("W", n) for n in hard]), c)] if hard else []) + g
    raise ValueError(name)


def decisions(rd, vals, bound, got, wit, rule, res):
    """(DO_decision, pH_decision) in {1, 0, -1} from the received items `got` under the given rule."""
    rx = {i: vals[i] for kind, i in got if kind == "R"}
    last = len(vals) - 1 if (len(vals) - 1) in rx else None
    cert, _ = record.certify(rx, rd.n_of, bound, last)
    out = []
    for p in ("DO", "pH"):
        ch = next(c for c in rd.channels if c.param == p)
        K = cl.knowledge_from_rx(p, ch.n, rx, cert[p], use_cells=(rule != "old"),
                                 resolution=res.get(p) if rule == "grid" else None)
        for kind, name in got:
            if kind == "W" and name in wit and wit[name][0] == p:
                _, s, code, wk, _m, _e = wit[name]
                (K.add_min_witness if wk == "min" else K.add_max_witness)(s, code)
        if p == "DO":
            out.append(cl.exceeds_below(K, DO_THR))
        else:
            a, b = cl.exceeds_below(K, PH_LO), cl.exceeds_above(K, PH_HI)
            out.append(1 if 1 in (a, b) else (0 if (a, b) == (0, 0) else -1))
    return out


def run_site(args):
    path, tag, Q, out, designs = args
    if os.path.exists(out):
        return out
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng([SEED, Q, re2.site_number(site) % 100000])
    rows = []
    recs = [rd for rd in load_site_records(path) if len(rd.channels) == 4]
    res = {p: cl.infer_resolution(np.concatenate([next(c.x for c in rd.channels if c.param == p) for rd in recs]))
           for p in ("DO", "pH")} if recs else {}
    items = []
    for rd in recs:
        d = delivery.day_number(rd.day)
        if len(rd.channels) != 4 or d not in P:
            continue
        vals, bound = P[d]["plan"]
        wit = witnesses(rd)
        if len(wit) < 3:
            continue
        items.append((rd, d, vals, bound, wit))
    # control 'randmix': the same hardness pattern as 'adapt' (so the same cost profile), but assigned to random days
    perm = np.random.default_rng([SEED, 77, re2.site_number(site) % 100000]).permutation(len(items)) if items else []
    for i, (rd, d, vals, bound, wit) in enumerate(items):
        other = items[perm[i]][4]
        wit_rand = {n: (*wit[n][:4], other[n][4], other[n][5]) for n in wit}
        ch = {c.param: c for c in rd.channels}
        live = {p: ~frame.saturated(frame.quantise(p, ch[p].x)) for p in ("DO", "pH")}
        do, ph = ch["DO"].x[live["DO"]], ch["pH"].x[live["pH"]]
        truth = {"DO": bool((do < DO_THR).any()), "pH": bool((ph < PH_LO).any() or (ph > PH_HI).any())}
        near = {"DO": bool(abs(do.min() - DO_THR) <= 0.6), "pH": bool(min(abs(ph.min() - PH_LO), abs(ph.max() - PH_HI)) <= 0.4)}
        for cname, c, R in CONDS:
            masks = np.ones((1, Q), bool) if c is None else rr.sim_masks(c, Q, rng, draws=R)
            for dn in designs:
                groups = design_groups("adapt" if dn == "randmix" else dn, wit_rand if dn == "randmix" else wit, vals)
                for rule in (("old", "new", "grid") if dn == "rec" else (("grid",) if dn in ("adapt", "randmix") else ("new", "grid"))):
                    cache, acc, full = {}, [], []
                    for mask in masks:
                        got = [it for items, cc in groups for it in group_recover(items, cc, mask)]
                        full.append(bool(bound) and all(("R", p) in set(got) for p in range(len(vals))))
                        key = frozenset(got)
                        if key not in cache:
                            cache[key] = decisions(rd, vals, bound, got, wit, rule, res)
                        acc.append(cache[key])
                    acc = np.array(acc)
                    for qi, q in enumerate(("DO", "pH")):
                        dec = acc[:, qi]
                        dcorr = float(np.mean((dec != -1) & (dec == int(truth[q]))))
                        rows.append({"site": site, "day": d, "Q": Q, "cond": cname, "design": dn, "rule": rule,
                                     "query": q, "truth": truth[q], "near": near[q], "res": res.get(q),
                                     "decided_correct": dcorr, "wrong": float(np.mean((dec != -1) & (dec != int(truth[q])))),
                                     "undetermined": float(np.mean(dec == -1)), "rec_full": float(np.mean(full)), "draws": len(dec)})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag, Q = sys.argv[1], sys.argv[2], int(sys.argv[3])
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else None
    designs = tuple(sys.argv[6].split(",")) if len(sys.argv) > 6 else DESIGNS
    sub = "proto" if designs == DESIGNS else "proto_" + "_".join(designs)
    os.makedirs(f"results/{tag}/{sub}", exist_ok=True)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    jobs = [(p, tag, Q, f"results/{tag}/{sub}/{os.path.basename(p)[:-4]}_Q{Q}.csv", designs) for p in paths]
    with Pool(workers) as pool:
        for i, o in enumerate(pool.imap_unordered(run_site, jobs), 1):
            print(i, len(jobs), o, flush=True)


if __name__ == "__main__":
    main()
