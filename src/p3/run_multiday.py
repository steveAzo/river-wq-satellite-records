"""Step 7 run: packet-level multi-day replay of every site's 2023 year (docs/STEP7_PLAN.md).

Per site: plans of every record day (self-contained record at tau = 1, and broken-stick contents for tag
practice), cached in results/<tag>/plans/<site>.pkl; schedules (multiday.py) for every design and tier; 30 loss
draws per channel; replay with the decoding rule; byte check of draw 0 on three channels (independent p = 0.3,
Gilbert p = 0.3 bursts 3 and 6). Output: results/<tag>/multiday/<site>.csv (resumable) -> results/<tag>/multiday.csv.
Run from Paper3/: python -I src/p3/run_multiday.py <folder> <tag> [workers=3]
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
from p3 import multiday as md  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

QS = (1, 6, 12, 24, 96)
RHOS = (1 / 3, 1 / 2, 2 / 3, 1.0)
MS = (2, 3, 4, 6)
DRAWS = 30
SEED = 20261023
BYTE_CHECK = ("iid_p0.3", "gilbert_p0.3_b3", "gilbert_p0.3_b6")
PILOT = 28


def site_plans(path, cache):
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    out = {}
    for rd in load_site_records(path):
        plan = record.Encoder(rd.channels).plan_at(1.0)
        if plan is None:
            continue
        sticks = {}
        for m in MS:
            v = [(c.param, s, int(frame.quantise(c.param, c.x[s]))) for c in rd.channels
                 for s in delivery.broken_stick(c, m)]
            sticks[m] = (v, delivery.plan_error(rd.channels, v) <= delivery.SLACK)
        out[delivery.day_number(rd.day)] = {"plan": (plan, delivery.plan_error(rd.channels, plan) <= delivery.SLACK),
                                            "four": len(rd.channels) == 4, "sticks": sticks}
    pickle.dump(out, open(cache + ".tmp", "wb"))
    os.replace(cache + ".tmp", cache)
    return out


def schedules(P, first, last, Q, site_seed):
    plans = {d: v["plan"] for d, v in P.items()}
    out = [("buf_rec", f"{r:.2f}", md.buf_rec(plans, first, last, Q, r)) for r in RHOS]
    out.append(("daily_rec", "-", md.daily_rec(plans, first, last, Q)))
    out.append(("rep_multi_rec", "-", md.rotation(plans, first, last, Q, "cyclic")))
    out.append(("tag_multi_rec", "-", md.rotation(plans, first, last, Q, "random", seed=site_seed)))
    for m in MS:
        sp = {d: v["sticks"][m] for d, v in P.items()}
        out.append(("tag_multi", str(m), md.rotation(sp, first, last, Q, "random", seed=site_seed + m)))
    return out


def metrics(done_list, days, first):
    """done_list: per draw {record day: completion block day}; days: {record day: four?}."""
    four = [d for d in days if days[d]]
    pilot = [d for d in days if d < first + PILOT]
    rest = [d for d in days if d >= first + PILOT]

    def share(ds, D):
        return float(np.mean([np.mean([d in dn and dn[d] - d <= D for d in ds]) for dn in done_list])) if ds else np.nan
    delays = [dn[d] - d for dn in done_list for d in four if d in dn]
    return {"n_four": len(four), "n_all": len(days),
            "G1": share(four, 1), "G2": share(four, 2), "G7": share(four, 7), "Gev": share(four, 10 ** 6),
            "G7_all": share(list(days), 7), "G7_pilot": share(pilot, 7), "G7_rest": share(rest, 7),
            "delay_med": float(np.median(delays)) if delays else np.nan,
            "delay_p95": float(np.percentile(delays, 95)) if delays else np.nan}


def run_site(args):
    path, tag, out = args
    if os.path.exists(out):
        return out
    site = os.path.basename(path)[:-4]
    P = site_plans(path, f"results/{tag}/plans/{site}.pkl")
    if not any(v["four"] for v in P.values()):
        open(out, "w").close()
        return out
    first, last = min(P), max(P)
    days = {d: v["four"] for d, v in P.items()}
    site_seed = int(site[:15]) % 100000
    rng = np.random.default_rng([SEED, 7, site_seed])
    rows = []
    for Q in QS:
        for design, variant, s in schedules(P, first, last, Q, site_seed):
            n_tx = sum(len(b.tx) for b in s.blocks)
            bl = np.array(list(s.backlog.values())) if s.backlog else np.array([0])
            for c in rr.CHANNELS:
                name = rr.ch_name(c)
                masks = rr.sim_masks(c, n_tx, rng, draws=DRAWS)
                mism = md.check_bytes(s, masks[0]) if name in BYTE_CHECK else -1
                if mism > 0:
                    raise RuntimeError(f"byte mismatch {site} {design} {variant} Q{Q} {name}")
                rows.append({"site": site, "Q": Q, "design": design, "variant": variant, "channel": name,
                             **metrics(md.replay(s, masks, days), days, first),
                             "backlog_med": float(np.median(bl)), "backlog_p95": float(np.percentile(bl, 95)),
                             "backlog_max": float(bl.max()), "dropped": len(s.dropped), "tx": n_tx,
                             "byte_checked": mism == 0})
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return out


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    for sub in ("plans", "multiday"):
        os.makedirs(f"results/{tag}/{sub}", exist_ok=True)
    jobs = [(f, tag, f"results/{tag}/multiday/{os.path.basename(f)}") for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
    with Pool(workers) as pool:
        for o in pool.imap_unordered(run_site, jobs):
            print("done", o, flush=True)
    parts = [pd.read_csv(o, dtype={"site": str}) for *_, o in jobs if os.path.getsize(o) > 0]
    df = pd.concat(parts)
    df.to_csv(f"results/{tag}/multiday.csv", index=False)
    print(f"{df.site.nunique()} sites; byte-checked rows {int(df.byte_checked.sum())}, all without mismatch")


if __name__ == "__main__":
    main()
