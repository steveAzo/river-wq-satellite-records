"""Step 9 experiments (docs/STEP9_PLAN.md): corruption of arriving bytes and injected sensor glitches. 2023 only.

Run from Paper3/: python -I src/p3/robustness.py <folder> <tag> [workers=3]
Outputs: results/<tag>/robust9/<site>_{corrupt,glitch}.csv (resumable) -> results/<tag>/robust9_{corrupt,glitch}.csv
"""
import glob
import os
import pickle
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import RecordDay  # noqa: E402

QS = (6, 12)
DRAWS = 20
SEED = 20261023
SLACK = 1 + 1e-9
CORRUPTION = [("none", 0.0, 0.0), ("ber_1e-4", 1e-4, 0.0), ("ber_1e-3", 1e-3, 0.0), ("ber_1e-2", 1e-2, 0.0),
              ("msg_10pct", 0.0, 0.10)]
GLITCH = {"T": 90.0, "DO": -1.0, "pH": 17.0, "EC": 200000.0}


def designs(rd, plan, Q):
    D1 = -(-len(plan) // frame.unit_capacity())
    if D1 > Q:
        return {}
    code = delivery.mds(rd, None, Q, D1, planned=(1.0, plan))
    rep = delivery._uncoded("rep_rec", rd, plan, 23, delivery.cyclic(D1, Q), tau=1.0)
    return {"rec_code": code, "rec_rep": rep}


def corrupt(m, ber, p_msg, rng):
    bits = 8 * len(m)
    if ber:
        flips = np.flatnonzero(rng.random(bits) < ber)
    elif p_msg and rng.random() < p_msg:
        flips = rng.choice(bits, size=int(rng.integers(1, 9)), replace=False)
    else:
        return m
    b = bytearray(m)
    for f in flips:
        b[f // 8] ^= 0x80 >> (f % 8)
    return bytes(b)


def evaluate(rd, msgs, day):
    rx, last, bound, fails, st = delivery.receive(msgs, day, with_stats=True)
    cert, full = record.certify(rx, rd.n_of, bound, last)
    err = record.errors(rd.channels, rx)
    false_cert = sum(int((err[p][cert[p]] > SLACK).sum()) for p in cert)
    return {"Phi": full, "cert": sum(c.sum() for c in cert.values()) / rd.raw_values, "false_cert": false_cert,
            "crc_fails": fails, "header_rejects": st["header_rejects"], "decode_tries": st["decode_tries"]}


def glitched(rd, rng, k, kind):
    chs = [record.Channel(c.param, c.x.copy(), c.tol.copy()) for c in rd.channels]
    for _ in range(k):
        c = chs[int(rng.integers(len(chs)))]
        t = int(rng.integers(c.n))
        c.x[t] = GLITCH[c.param] if kind == "out" else c.x[t] + 10 * c.tol[t]
    return RecordDay(rd.site, rd.day, chs, rd.steps)


def run_site(args):
    path, tag, out_c, out_g = args
    if os.path.exists(out_g):
        return out_g
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng([SEED, 9, int(site[:15]) % 100000])
    rc, rg = [], []
    for rd in re2.sample_site(path, 20)[1::2]:
        day = delivery.day_number(rd.day)
        plan = P[day]["plan"][0]
        for Q in QS:
            ds = designs(rd, plan, Q)
            masks = rr.sim_masks(("iid", 0.3, 0), Q, rng, draws=DRAWS)
            for cname, ber, pm in CORRUPTION:
                for name, s in ds.items():
                    acc = []
                    for mask in masks:
                        arrived = [corrupt(m, ber, pm, rng) for m, ok in zip(s.msgs, mask[:len(s.msgs)]) if ok]
                        acc.append(evaluate(rd, arrived, day))
                    a = pd.DataFrame(acc)
                    rc.append({"site": site, "day": day, "Q": Q, "corruption": cname, "design": name,
                               **a.mean().to_dict(), "false_cert_total": int(a.false_cert.sum())})
        clean = len(plan)
        for kind in ("out", "in"):
            for k in (1, 3):
                g = glitched(rd, rng, k, kind)
                gplan = record.Encoder(g.channels).plan_at(1.0)
                if gplan is None:
                    rg.append({"site": site, "day": day, "kind": kind, "k": k, "planned": False})
                    continue
                rx = dict(enumerate(gplan))
                bound = delivery.plan_error(g.channels, gplan) <= SLACK
                cert, full = record.certify(rx, g.n_of, bound, len(gplan) - 1)
                err = record.errors(g.channels, rx)
                cen = sum(int(frame.saturated(c).sum()) for _, _, c in gplan)
                rg.append({"site": site, "day": day, "kind": kind, "k": k, "planned": True, "bound": bound,
                           "full": full, "extra_values": len(gplan) - clean, "censored": cen,
                           "cert": sum(c.sum() for c in cert.values()) / g.raw_values,
                           "false_cert": sum(int((err[p][cert[p]] > SLACK).sum()) for p in cert)})
    pd.DataFrame(rc).to_csv(out_c, index=False)
    pd.DataFrame(rg).to_csv(out_g + ".tmp", index=False)
    os.replace(out_g + ".tmp", out_g)
    return out_g


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(f"results/{tag}/robust9", exist_ok=True)
    jobs = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        site = os.path.basename(f)[:-4]
        if os.path.exists(f"results/{tag}/plans/{site}.pkl") and re2.sample_site(f, 2):
            jobs.append((f, tag, f"results/{tag}/robust9/{site}_corrupt.csv", f"results/{tag}/robust9/{site}_glitch.csv"))
    with Pool(workers) as pool:
        for o in pool.imap_unordered(run_site, jobs):
            print("done", o, flush=True)
    c = pd.concat([pd.read_csv(j[2], dtype={"site": str}) for j in jobs])
    g = pd.concat([pd.read_csv(j[3], dtype={"site": str}) for j in jobs])
    c.to_csv(f"results/{tag}/robust9_corrupt.csv", index=False)
    g.to_csv(f"results/{tag}/robust9_glitch.csv", index=False)
    pd.set_option("display.width", 200)
    print(f"days: {c[['site', 'day']].drop_duplicates().shape[0]}")
    print("\nCorruption (independent erasure p = 0.3), means per day and draw; false_cert_total summed:")
    print(c.groupby(["Q", "design", "corruption"]).agg(G_cert=("Phi", "mean"), cert=("cert", "mean"),
                                                         crc_fails=("crc_fails", "mean"),
                                                         header_rejects=("header_rejects", "mean"),
                                                         decode_tries=("decode_tries", "mean"),
                                                         false_cert=("false_cert_total", "sum")).round(4).to_string())
    print("\nGlitches (perfect delivery):")
    print(g.groupby(["kind", "k"]).agg(days=("day", "size"), planned=("planned", "mean"), bound=("bound", "mean"),
                                       full=("full", "mean"), extra_values=("extra_values", "mean"),
                                       censored=("censored", "mean"), cert=("cert", "mean"),
                                       false_cert=("false_cert", "sum")).round(3).to_string())


if __name__ == "__main__":
    main()
