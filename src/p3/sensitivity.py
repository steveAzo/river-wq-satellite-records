"""Sensitivity analyses of the daily need (study plan Section 8, step 6; run after confirmation).

For every 2024 USGS site-day (and the low-cost days), values needed for a guaranteed record under:
  v_exc        min-# within the USGS "excellent" tolerance (the main result; tau = 1)
  v_exc_q      min-# within 0.975 x tolerance: the margin that absorbs the 13-bit reading quantiser
               (worst half-step 2.3% of the conductance tolerance, below 1.4% for the others), so the guarantee holds for transmitted values
  v_exc_half   min-# within 0.5 x tolerance: half of the error budget left for the sensor itself
  v_good       min-# within the USGS "good" tolerance
  v_greedy     greedy online segmentation (extend each segment as far as the tolerance allows, then keep its
               end reading; the swinging-door family used by process historians), same reconstruction
  v_deadband   report-by-exception: send a reading when it leaves the tolerance band of the last sent value;
               the server holds the last sent value (deadband reporting, common in SCADA)
  v_exc_x2/x4  min-# after keeping every 2nd / 4th reading (coarser sampling interval), excellent tolerance
Exploratory: none of these were pre-registered as hypotheses.
Output: results/sens/need_sensitivity_<tag>.csv
Run from Paper3/: python -I src/p3/sensitivity.py <folder> <tag> [workers=8]
"""
import glob
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import pla  # noqa: E402
from p3.data import SiteDay, load_site, tolerance  # noqa: E402

TAU_Q = 0.975


def greedy_count(seg, tail):
    """Greedy online segmentation: from the last kept position, keep the farthest reachable reading."""
    n1 = seg.shape[0]
    a, kept = 0, 0
    while tail[a] > 1 + 1e-12:
        b = a + 1
        while b + 1 < n1 and seg[a, b + 1] <= 1 + 1e-12:
            b += 1
        a, kept = b, kept + 1
    return kept


def deadband_count(x, anchor, tol):
    last, sent = anchor, 0
    for v, d in zip(x, tol):
        if abs(v - last) > d + 1e-12:
            last, sent = v, sent + 1
    return sent


def sub(sd, k):
    """Keep every k-th reading, ending at the day's last reading (the anchor stays k steps before it)."""
    X = sd.X[:, k - 1::k]
    return SiteDay(sd.site, sd.day, sd.params, X, sd.anchor, sd.tol[:, k - 1::k], sd.step_min * k)


def tables(x, anchor, tol):
    """Same seg/tail tables as pla.tables (the frozen module), vectorised over (t, b) for each start a.
    Equality with pla.tables is checked in main() on sample days before the run."""
    n = len(x)
    xs = np.concatenate(([anchor], x))
    ts = np.concatenate(([np.inf], tol))
    seg = np.zeros((n + 1, n + 1))
    for a in range(n - 1):
        t = np.arange(a + 1, n)[:, None]                 # interior positions
        b = np.arange(a + 2, n + 1)[None, :]             # end positions
        line = xs[a] + (xs[b] - xs[a]) * (t - a) / (b - a)
        err = np.abs(xs[t] - line) / ts[t]
        err[t >= b] = 0.0
        seg[a, a + 2:] = err.max(axis=0)
    tail = np.array([np.max(np.abs(xs[q + 1:] - xs[q]) / ts[q + 1:]) if q < n else 0.0 for q in range(n + 1)])
    return seg, tail


def mins(sd, eps):
    return sum(len(pla.min_set(*tables(sd.X[p], sd.anchor[p], sd.tol[p]), eps)) for p in range(sd.P))


def one(sd):
    row = {"site": sd.site, "day": str(sd.day.date()), "step_min": sd.step_min, "n_par": sd.P,
           "params": "|".join(sd.params), "raw_values": sd.P * sd.n}
    tabs = [tables(sd.X[p], sd.anchor[p], sd.tol[p]) for p in range(sd.P)]
    row["v_exc"] = sum(len(pla.min_set(s, t, 1.0)) for s, t in tabs)
    row["v_exc_q"] = sum(len(pla.min_set(s, t, TAU_Q)) for s, t in tabs)
    row["v_exc_half"] = sum(len(pla.min_set(s, t, 0.5)) for s, t in tabs)
    row["v_greedy"] = sum(greedy_count(s, t) for s, t in tabs)
    row["v_deadband"] = sum(deadband_count(sd.X[p], sd.anchor[p], sd.tol[p]) for p in range(sd.P))
    good = np.stack([tolerance(q, sd.X[i], "good") for i, q in enumerate(sd.params)])
    row["v_good"] = mins(SiteDay(sd.site, sd.day, sd.params, sd.X, sd.anchor, good, sd.step_min), 1.0)
    for k in (2, 4):
        if sd.n % k == 0 and sd.n // k >= 12:
            s2 = sub(sd, k)
            row[f"v_exc_x{k}"] = mins(s2, 1.0)
            row[f"raw_x{k}"] = s2.P * s2.n
    return row


def site_part(job):
    """All site-days of one site file, saved as one part (so that an interrupted run resumes)."""
    path, part = job
    if not os.path.exists(part):
        rows = [one(sd) for sd in load_site(path, "excellent")]
        pd.DataFrame(rows).to_csv(part + ".tmp", index=False)
        os.replace(part + ".tmp", part)
    return path


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    parts = f"results/sens/parts_{tag}"
    os.makedirs(parts, exist_ok=True)
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))  # the order of load_folder, hence of need.py
    jobs = [(f, os.path.join(parts, os.path.basename(f))) for f in files]
    for sd in load_site(files[0], "excellent")[:5]:                # fast tables == frozen tables
        for p in range(sd.P):
            a, b = pla.tables(sd.X[p], sd.anchor[p], sd.tol[p]), tables(sd.X[p], sd.anchor[p], sd.tol[p])
            assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    with Pool(workers, maxtasksperchild=1) as pool:
        for i, f in enumerate(pool.imap_unordered(site_part, jobs)):
            print(i + 1, len(jobs), os.path.basename(f), flush=True)
    out = pd.concat([pd.read_csv(p, dtype={"site": str}) for _, p in jobs], ignore_index=True)
    os.makedirs("results/sens", exist_ok=True)
    out.to_csv(f"results/sens/need_sensitivity_{tag}.csv", index=False)
    cols = [c for c in out if c.startswith("v_")]
    print((3 * out[cols]).describe(percentiles=[.5, .9, .99]).round(1).to_string())


if __name__ == "__main__":
    main()
