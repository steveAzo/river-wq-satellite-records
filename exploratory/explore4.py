"""Exploratory analyses requested by the outside review (docs/OUTSIDE_REVIEW_RESPONSE_PLAN.md, points 2, 6, 7, 8). POST HOC: run
after the frozen confirmation; nothing here is a test, and nothing changes a confirmatory verdict. It reuses the frozen version 3 code
read-only (src/p3v3/confirm4.py: frame3 with CRC-24, receiver3, decoded-only knowledge, flags-plus-record merge).

Per site, at byte level, with loss masks drawn once per day, Q, and condition and shared by the three designs (rec, heur, flagsrec):
  point 7  loss sweep: independent loss 0.1, 0.3, 0.5; Gilbert loss 0.3 with bursts of 3 and 6, and 0.5 with bursts of 3;
  point 6  threshold sweep: decisions at a grid of thresholds per query kind (DO below; pH below; pH above; conductance change;
           7DADM above), all days and days that are hard at that threshold (same bands as the study);
  point 8  record utility: share of readings certified (within tolerance) per draw, overall and on draws whose whole record was lost;
  point 2  assumption R: at Q = 6 under independent loss 0.3 only, decisions at the configured and alternative thresholds with the
           inferred resolution, with R off, and with a deliberately wrong resolution (ten times too coarse; 0.1 where none was
           inferred), counting correct and wrong certain decisions.
Output per site: exploratory/out/<tag>/<site>.csv (aggregated sums; resumable). Summaries: exploratory/summarise4.py.
Run from Paper3/: python -I -W ignore exploratory/explore4.py <folder> <tag> [site ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "src", "p3v3"))
import confirm4 as c4  # noqa: E402
from p3 import certlang as cl  # noqa: E402
from p3 import frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

SEED = 20261112
DRAWS = 20
QS = (6, 12)
CONDS = {"iid_0.1": ("iid", 0.1, None), "iid_0.3": ("iid", 0.3, None), "iid_0.5": ("iid", 0.5, None),
         "gil_0.3_b3": ("gilbert", 0.3, 3), "gil_0.3_b6": ("gilbert", 0.3, 6), "gil_0.5_b3": ("gilbert", 0.5, 3)}
GRID = {"do": (2.0, 3.0, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0),
        "ph_low": (5.5, 6.0, 6.3, 6.5, 6.7, 7.0),
        "ph_high": (8.0, 8.5, 8.8, 9.0, 9.2, 9.5),
        "ec": (0.025, 0.05, 0.10, 0.20, 0.30),
        "win7": (16.0, 18.0, 19.0, 20.0, 21.0, 22.0, 24.0)}
CFG = {"do": 5.0, "ph_low": 6.5, "ph_high": 9.0, "ec": 0.10, "win7": 20.0}
BAND = {"do": 0.6, "ph_low": 0.4, "ph_high": 0.4, "win7": 2.0}
DESIGNS = ("rec", "heur", "flagsrec")


def day_truth(it):
    ch = {c.param: c for c in it["rd"].channels}
    live = lambda p: ch[p].x[~frame.saturated(frame.quantise(p, ch[p].x))]
    do, ph = live("DO"), live("pH")
    # Computed quantities are rounded before comparison: a decimal mean of exactly 22.0 can come out as 22.000000000000004 in
    # floating point and would make the truth "above 22" (found on 2023 development data, site 03075070, day 8682). Readings are
    # compared as they are.
    rate = round(float(it["ew"][4]), 9) if it["ew"] is not None else None
    mean7 = round(float(it["mean7"]), 9) if it["mean7"] is not None else None
    t, h = {}, {}
    for th in GRID["do"]:
        t[("do", th)] = bool(do.min() < th)
        h[("do", th)] = bool(t[("do", th)] or abs(do.min() - th) <= BAND["do"])
    for th in GRID["ph_low"]:
        t[("ph_low", th)] = bool(ph.min() < th)
        h[("ph_low", th)] = bool(t[("ph_low", th)] or abs(ph.min() - th) <= BAND["ph_low"])
    for th in GRID["ph_high"]:
        t[("ph_high", th)] = bool(ph.max() > th)
        h[("ph_high", th)] = bool(t[("ph_high", th)] or abs(ph.max() - th) <= BAND["ph_high"])
    for th in GRID["ec"]:
        t[("ec", th)] = None if rate is None else bool(rate > th)
        h[("ec", th)] = None if rate is None else bool(rate >= 0.4 * th)
    for th in GRID["win7"]:
        t[("win7", th)] = None if mean7 is None else bool(mean7 > th)
        h[("win7", th)] = None if mean7 is None else bool(abs(mean7 - th) <= BAND["win7"])
    cfg = {k: t.get((k, CFG[k])) for k in CFG}
    return t, h, cfg


def flag_answer(kind, th, cfg_truth):
    """Configured answer carried as a flag, applied to threshold th by monotone implication (else -1)."""
    y = cfg_truth[kind]
    if y is None:
        return -1
    c = CFG[kind]
    if th == c:
        return int(y)
    if kind in ("do", "ph_low"):                       # "some reading below th"
        return 1 if (th > c and y) else (0 if (th < c and not y) else -1)
    if kind == "ph_high":                              # "some reading above th"
        return 1 if (th < c and y) else (0 if (th > c and not y) else -1)
    if kind == "ec":                                   # "some change above th"
        return 1 if (th < c and y) else (0 if (th > c and not y) else -1)
    return -1


def decide_grid(it, Ks):
    """Certificate answers at every grid threshold (day queries) and the day-maximum interval of temperature."""
    Kd, Kp, Kt, Ke = Ks
    out = {}
    for th in GRID["do"]:
        out[("do", th)] = cl.exceeds_below(Kd, th)
    for th in GRID["ph_low"]:
        out[("ph_low", th)] = cl.exceeds_below(Kp, th)
    for th in GRID["ph_high"]:
        out[("ph_high", th)] = cl.exceeds_above(Kp, th)
    for th in GRID["ec"]:
        out[("ec", th)] = cl.relative_change(Ke, it["lag"], th) if Ke is not None else -1
    return out, c4.pb.cl3.max_bounds(Kt)               # guarded day-maximum interval (certlang3)


def certified_share(it, d):
    rd = it["rd"]
    rx = {} if d.record_rejected else dict(d.values)
    cert, _ = record.certify(rx, rd.n_of, d.bound, d.last_pos)
    tot = sum(rd.n_of.values())
    return sum(int(c.sum()) for c in cert.values()) / tot


def r_variants(res):
    wrong = {}
    for p in ("DO", "pH", "T"):
        wrong[p] = res[p] * 10 if res.get(p) else 0.1
    return {"inferred": res, "off": {}, "wrong": wrong}


def run_site(path, tag, outdir):
    site = os.path.basename(path)[:-4]
    out = f"{outdir}/{site}.csv"
    if os.path.exists(out):
        return site
    site, items, res = prepare_items(path, tag)
    rng = np.random.default_rng([SEED, re2.site_number(site)])
    acc = {}                                           # key -> [sum_correct, count, sum_wrong]

    def add(key, correct, wrong, n=1):
        a = acc.setdefault(key, [0.0, 0, 0.0])
        a[0] += correct
        a[1] += n
        a[2] += wrong

    for it in items:
        it["meta"] = c4.pb.day_meta(it)
        it["fd"] = c4.pb.flag_decisions(it["meta"])
        it["tg"], it["hg"], it["cfgt"] = day_truth(it)
    for Q in QS:
        bnd = {}
        for it in items:
            vals, n, bound = it["vals"], len(it["vals"]), it["bound"]
            blocks = {}
            for variant in ("rec", "heur"):
                try:
                    blocks[variant] = c4.i3.build(it, Q, c4.VARIANT[variant])[0]
                except ValueError:
                    blocks[variant] = None
            if blocks["heur"] is None or blocks["rec"] is None:
                continue
            for cname, c in CONDS.items():
                masks = rr.sim_masks(c, Q, rng, draws=DRAWS)
                for variant in ("rec", "heur"):
                    blk, memo, bs = blocks[variant], {}, []
                    for m in masks:
                        keep = [i for i in range(Q) if m[i]]
                        d = c4.r3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else c4.f3.Decoded()
                        full = bool(bound) and not d.record_rejected and len(d.values) == n and all(d.values.get(i) == vals[i] for i in range(n))
                        k = c4.decode_key(d)
                        if k not in memo:
                            memo[k] = (decide_grid(it, c4.decoded_knowledge(it, d, res)), certified_share(it, d))
                        (dec, mb), cs = memo[k]
                        anyflag = bool(keep)
                        designs = [(variant, dec, mb)] + ([("flagsrec", dec, (mb, anyflag))] if variant == "rec" else [])
                        for dn, dd, b in designs:
                            add((Q, cname, dn, "rec_full", "", ""), float(full), 0.0)
                            add((Q, cname, dn, "cert_share", "", "all"), cs, 0.0)
                            if not full:
                                add((Q, cname, dn, "cert_share", "", "not_full"), cs, 0.0)
                            bs_key = (cname, dn, it["d"])
                            bnd.setdefault(bs_key, []).append(b)
                            for (kind, th), x in dd.items():
                                t, h = it["tg"][(kind, th)], it["hg"][(kind, th)]
                                if t is None:
                                    continue
                                if dn == "flagsrec" and x == -1 and anyflag:
                                    x = flag_answer(kind, th, it["cfgt"])
                                corr, wr = float(x != -1 and x == int(t)), float(x != -1 and x != int(t))
                                add((Q, cname, dn, kind, th, "all"), corr, wr)
                                if h:
                                    add((Q, cname, dn, kind, th, "hard"), corr, wr)
            # point 2: assumption R variants, Q = 6, independent loss 0.3, configured and alternative thresholds
            if Q == 6:
                masks = rr.sim_masks(CONDS["iid_0.3"], Q, rng, draws=DRAWS)
                for variant in ("rec", "heur"):
                    blk = blocks[variant]
                    for rname, rres in r_variants(res).items():
                        memo = {}
                        for m in masks:
                            keep = [i for i in range(Q) if m[i]]
                            d = c4.r3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else c4.f3.Decoded()
                            k = c4.decode_key(d)
                            if k not in memo:
                                memo[k] = c4.pb.decide(it, c4.decoded_knowledge(it, d, rres))[0]
                            dec = memo[k]
                            for v in c4.pb.VAR:
                                for kind, idx in c4.KINDS:
                                    t = it["meta"]["truth"][v][kind]
                                    if t is None:
                                        continue
                                    x = dec[v][idx]
                                    x = -1 if x is None else x
                                    add((Q, "iid_0.3", variant, f"R_{rname}", v, kind), float(x != -1 and x == int(t)), float(x != -1 and x != int(t)))
        # 7DADM windows over the grid
        for it in items:
            if not it["win"]:
                continue
            for cname in CONDS:
                for dn in DESIGNS:
                    if any((cname, dn, x["d"]) not in bnd for x in it["win"]):
                        continue
                    parts = [bnd[(cname, dn, x["d"])] for x in it["win"]]
                    if dn == "flagsrec":
                        avail = [b[1] for b in parts[-1]]
                        parts = [[b[0] for b in p] for p in parts]
                    rn = min(len(p) for p in parts)
                    for th in GRID["win7"]:
                        t, h = it["tg"][("win7", th)], it["hg"][("win7", th)]
                        if t is None:
                            continue
                        for k in range(rn):
                            x = cl.rolling_mean_decision([tuple(p[k]) for p in parts], th)
                            if dn == "flagsrec" and x == -1 and avail[k]:
                                y = it["cfgt"]["win7"]
                                x = int(y) if th == 20.0 else (1 if (th < 20.0 and y) else (0 if (th > 20.0 and not y) else -1))
                            corr, wr = float(x != -1 and x == int(t)), float(x != -1 and x != int(t))
                            add((Q, cname, dn, "win7", th, "all"), corr, wr)
                            if h:
                                add((Q, cname, dn, "win7", th, "hard"), corr, wr)
    rows = [(site, *k, *v) for k, v in acc.items()]
    df = pd.DataFrame(rows, columns=["site", "Q", "cond", "design", "metric", "theta", "subset", "sum", "count", "wrong"])
    df.to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return site


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    c4.check_environment()                             # frame3 CRC-24, no environment switches
    outdir = os.path.join(ROOT, "exploratory", "out", tag)
    os.makedirs(outdir, exist_ok=True)
    paths = [p for p in sorted(glob.glob(os.path.join(folder, "*.csv")))
             if os.path.exists(f"results/{tag}/plans/{os.path.basename(p)[:-4]}.pkl")]
    paths = c4.analysis_sites(paths, tag)
    if only:
        paths = [p for p in paths if os.path.basename(p)[:-4] in only]
    for i, p in enumerate(paths, 1):
        s = run_site(p, tag, outdir)
        print(f"{i}/{len(paths)} {s}", flush=True)


if __name__ == "__main__":
    main()
