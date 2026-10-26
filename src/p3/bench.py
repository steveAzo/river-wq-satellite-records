"""Step 10: encoder equivalence on all 2023 record days, and resource measurements (review M12, E8).

Part A (all sites, parallel): the table-free encoder (stream.py) must reproduce every cached plan of Step 7
exactly; per channel-day it records the number of window updates and the time.
Part B (one process): time and peak memory (tracemalloc) of the table encoder (record.Encoder.plan_at) and the
table-free encoder per sampling interval, on up to 20 four-parameter days per interval; 10-min days are made by
taking every second reading of 5-min days. Part C: Reed-Solomon encoding cost per block.
Host measurements on this PC (Python); microcontroller figures are estimates from the operation counts.
Outputs: results/<tag>/bench_equiv.csv, bench_resources.csv, bench_rs.csv.
Run from Paper3/: python -I src/p3/bench.py <folder> <tag> [workers=3]
"""
import glob
import os
import pickle
import sys
import time
import tracemalloc
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, record, rs, stream  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.loader import RecordDay, load_site_records  # noqa: E402


def equiv_site(args):
    path, tag = args
    site = os.path.basename(path)[:-4]
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rows = []
    for rd in load_site_records(path):
        d = delivery.day_number(rd.day)
        if d not in P:
            continue
        ops, t0 = [], time.perf_counter()
        plan = stream.plan(rd.channels, count=ops)
        dt = time.perf_counter() - t0
        rows.append({"site": site, "day": d, "same": plan == P[d]["plan"][0], "values": len(plan),
                     "n_total": rd.raw_values, "n_max": max(c.n for c in rd.channels), "channels": len(rd.channels),
                     "ops": sum(ops), "ops_max_channel": max(ops), "seconds": dt})
    return rows


def subsample(rd, k):
    chs = [record.Channel(c.param, c.x[::k], tolerance(c.param, c.x[::k])) for c in rd.channels]
    return RecordDay(rd.site, rd.day, chs, {p: s * k for p, s in rd.steps.items()})


def measure(fn):
    tracemalloc.start()
    t0 = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t0
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return out, dt, peak


def resources(folder):
    groups = {}
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        for rd in load_site_records(f):
            if len(rd.channels) != 4 or len(set(rd.steps.values())) != 1:
                continue
            step = next(iter(rd.steps.values()))
            groups.setdefault(step, []).append(rd)
            if step == 5:
                groups.setdefault(10, []).append(subsample(rd, 2))
    rng = np.random.default_rng(20261025)
    rows = []
    for step in sorted(groups):
        days = groups[step]
        for i in rng.choice(len(days), size=min(20, len(days)), replace=False):
            rd = days[i]
            a, ta, ma = measure(lambda: record.Encoder(rd.channels).plan_at(1.0))
            ops = []
            b, tb, mb = measure(lambda: stream.plan(rd.channels, count=ops))
            assert a == b
            rows.append({"step_min": step, "n": rd.channels[0].n, "values": len(a),
                         "table_s": ta, "table_peak_B": ma, "stream_s": tb, "stream_peak_B": mb, "ops": sum(ops)})
    return pd.DataFrame(rows)


def rs_cost():
    rows = []
    rng = np.random.default_rng(1)
    for Q in (6, 12, 24, 96):
        for K in sorted({1, 2, 3, 5, min(Q, 10)}):
            if K >= Q:
                continue
            data = [list(rng.integers(0, 256, 20)) for _ in range(K)]
            t0 = time.perf_counter()
            for _ in range(20):
                rs.encode(data, Q)
            rows.append({"Q": Q, "K": K, "gf_mults": (Q - K) * K * 20, "seconds": (time.perf_counter() - t0) / 20})
    return pd.DataFrame(rows)


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    jobs = [(f, tag) for f in sorted(glob.glob(os.path.join(folder, "*.csv")))
            if os.path.exists(f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl")]
    with Pool(workers) as pool:
        eq = pd.DataFrame([r for rows in pool.imap_unordered(equiv_site, jobs) for r in rows])
    eq.to_csv(f"results/{tag}/bench_equiv.csv", index=False)
    print(f"Part A: {len(eq):,} record days at {eq.site.nunique()} sites; identical plans: {int(eq.same.sum()):,} "
          f"({eq.same.mean():.4%}); window updates per channel-day: median "
          f"{(eq.ops / eq.channels).median():.0f}, max {eq.ops_max_channel.max():,}", flush=True)
    res = resources(folder)
    res.to_csv(f"results/{tag}/bench_resources.csv", index=False)
    print("\nPart B (host, Python; four-parameter days; medians, max of ops):")
    print(res.groupby("step_min").agg(days=("n", "size"), n=("n", "first"), table_s=("table_s", "median"),
                                      table_peak_kB=("table_peak_B", lambda x: x.median() / 1024),
                                      stream_s=("stream_s", "median"),
                                      stream_peak_kB=("stream_peak_B", lambda x: x.median() / 1024),
                                      ops_med=("ops", "median"), ops_max=("ops", "max")).round(4).to_string())
    rc = rs_cost()
    rc.to_csv(f"results/{tag}/bench_rs.csv", index=False)
    print("\nPart C (Reed-Solomon parity per block, host):")
    print(rc.to_string(index=False))


if __name__ == "__main__":
    main()
