"""Hard-case band sensitivity (second outside review, 2026-11-12). POST HOC: nothing here is a test, and nothing changes a
confirmatory verdict. It reuses explore4.py and the frozen version 3 code read-only.

The node's allocation is unchanged (the frozen bands choose which days carry protected witnesses). Only the scored population
changes: hard day-queries are re-defined on the sensor record with narrower and wider bands than the study's, at the configured
and the two alternative threshold sets, in the four confirmation conditions (Q = 6 and 12; independent loss 0.3 and Gilbert loss
0.3 with bursts of 3). The loss masks are drawn exactly as in explore4.py (every condition and the assumption-R masks are drawn
in the same order, and unused ones are discarded), so the "study" band reproduces explore4.py and the confirmation.

Bands (a day-query is hard when the event is true or the true statistic is within the band of the threshold;
7DADM windows by the band only, as in the study):
  narrow  dissolved oxygen 0.3 mg/L, pH 0.2, conductance rate >= 0.7 x threshold, 7DADM 1 degC
  study   dissolved oxygen 0.6 mg/L, pH 0.4, conductance rate >= 0.4 x threshold, 7DADM 2 degC (as scored in the confirmation)
  wide    dissolved oxygen 1.2 mg/L, pH 0.8, conductance rate >= 0.2 x threshold, 7DADM 4 degC
  near    the study band without the event rule (event days far from the threshold are not counted)
Output: exploratory/out/<tag>_bands/<site>.csv (resumable). Run from Paper3/:
  python -I -W ignore exploratory/explore4_bands.py <folder> <tag> [site ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore4 as e4  # noqa: E402

c4, cl, rr, re2 = e4.c4, e4.cl, e4.rr, e4.re2
KEEP = ("iid_0.3", "gil_0.3_b3")
THETAS = {"do": (4.5, 5.0, 5.5), "ph_low": (6.3, 6.5, 6.7), "ph_high": (8.8, 9.0, 9.2), "ec": (0.05, 0.10, 0.20),
          "win7": (19.0, 20.0, 21.0)}
BANDS = {"narrow": (0.3, 0.2, 0.7, 1.0, True), "study": (0.6, 0.4, 0.4, 2.0, True), "wide": (1.2, 0.8, 0.2, 4.0, True),
         "near": (0.6, 0.4, 0.4, 2.0, False)}


def hard_sets(it, t):
    """For every band, the set of (kind, theta) that are hard on this day."""
    ch = {c.param: c for c in it["rd"].channels}
    live = lambda p: ch[p].x[~e4.frame.saturated(e4.frame.quantise(p, ch[p].x))]
    do, ph = live("DO"), live("pH")
    rate = round(float(it["ew"][4]), 9) if it["ew"] is not None else None
    mean7 = round(float(it["mean7"]), 9) if it["mean7"] is not None else None
    out = {}
    for name, (bdo, bph, fec, bt, ev) in BANDS.items():
        h = set()
        for th in THETAS["do"]:
            if (ev and t[("do", th)]) or abs(do.min() - th) <= bdo:
                h.add(("do", th))
        for th in THETAS["ph_low"]:
            if (ev and t[("ph_low", th)]) or abs(ph.min() - th) <= bph:
                h.add(("ph_low", th))
        for th in THETAS["ph_high"]:
            if (ev and t[("ph_high", th)]) or abs(ph.max() - th) <= bph:
                h.add(("ph_high", th))
        for th in THETAS["ec"]:
            if rate is not None and ((ev and t[("ec", th)]) or rate >= fec * th):
                h.add(("ec", th))
        for th in THETAS["win7"]:
            if mean7 is not None and abs(mean7 - th) <= bt:            # windows: band only, as scored in the study
                h.add(("win7", th))
        out[name] = h
    return out


def run_site(path, tag, outdir):
    site = os.path.basename(path)[:-4]
    out = f"{outdir}/{site}.csv"
    if os.path.exists(out):
        return site
    site, items, res = e4.prepare_items(path, tag)
    rng = np.random.default_rng([e4.SEED, re2.site_number(site)])
    acc = {}

    def add(key, correct, wrong):
        a = acc.setdefault(key, [0.0, 0, 0.0])
        a[0] += correct
        a[1] += 1
        a[2] += wrong

    for it in items:
        it["meta"] = c4.pb.day_meta(it)
        it["tg"], _, it["cfgt"] = e4.day_truth(it)
        it["hs"] = hard_sets(it, it["tg"])
    for Q in e4.QS:
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
            for cname, c in e4.CONDS.items():
                masks = rr.sim_masks(c, Q, rng, draws=e4.DRAWS)     # drawn for every condition to keep the stream
                if cname not in KEEP:
                    continue
                for variant in ("rec", "heur"):
                    blk, memo = blocks[variant], {}
                    for m in masks:
                        keep = [i for i in range(Q) if m[i]]
                        d = c4.r3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else c4.f3.Decoded()
                        k = c4.decode_key(d)
                        if k not in memo:
                            memo[k] = e4.decide_grid(it, c4.decoded_knowledge(it, d, res))
                        dec, mb = memo[k]
                        anyflag = bool(keep)
                        designs = [(variant, dec, mb)] + ([("flagsrec", dec, (mb, anyflag))] if variant == "rec" else [])
                        for dn, dd, b in designs:
                            bnd.setdefault((cname, dn, it["d"]), []).append(b)
                            for kind, ths in THETAS.items():
                                if kind == "win7":
                                    continue
                                for th in ths:
                                    t = it["tg"][(kind, th)]
                                    if t is None:
                                        continue
                                    x = dd[(kind, th)]
                                    if dn == "flagsrec" and x == -1 and anyflag:
                                        x = e4.flag_answer(kind, th, it["cfgt"])
                                    corr, wr = float(x != -1 and x == int(t)), float(x != -1 and x != int(t))
                                    for bname, hs in it["hs"].items():
                                        if (kind, th) in hs:
                                            add((Q, cname, dn, kind, th, bname), corr, wr)
            if Q == 6:
                rr.sim_masks(e4.CONDS["iid_0.3"], Q, rng, draws=e4.DRAWS)   # the assumption-R masks of explore4.py
        for it in items:
            if not it["win"]:
                continue
            for cname in KEEP:
                for dn in e4.DESIGNS:
                    if any((cname, dn, x["d"]) not in bnd for x in it["win"]):
                        continue
                    parts = [bnd[(cname, dn, x["d"])] for x in it["win"]]
                    if dn == "flagsrec":
                        avail = [b[1] for b in parts[-1]]
                        parts = [[b[0] for b in p] for p in parts]
                    rn = min(len(p) for p in parts)
                    for th in THETAS["win7"]:
                        t = it["tg"][("win7", th)]
                        if t is None:
                            continue
                        for k in range(rn):
                            x = cl.rolling_mean_decision([tuple(p[k]) for p in parts], th)
                            if dn == "flagsrec" and x == -1 and avail[k]:
                                y = it["cfgt"]["win7"]
                                x = int(y) if th == 20.0 else (1 if (th < 20.0 and y) else (0 if (th > 20.0 and not y) else -1))
                            corr, wr = float(x != -1 and x == int(t)), float(x != -1 and x != int(t))
                            for bname, hs in it["hs"].items():
                                if ("win7", th) in hs:
                                    add((Q, cname, dn, "win7", th, bname), corr, wr)
    rows = [(site, *k, *v) for k, v in acc.items()]
    df = pd.DataFrame(rows, columns=["site", "Q", "cond", "design", "metric", "theta", "subset", "sum", "count", "wrong"])
    df.to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return site


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    c4.check_environment()
    outdir = os.path.join(e4.ROOT, "exploratory", "out", tag + "_bands")
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
