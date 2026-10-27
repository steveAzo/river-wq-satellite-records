"""End-to-end development run on bytes (revision Step 4c; review M4, M6, E1). 2023 data only.

Record days from the per-channel loader; primary cohort = four-parameter days. Stratified sample of up to
N_PER_SITE days per site (seed 20261023); even-indexed days tune each family's parameter (repeat r, MDS K,
tag share) for the mean fully-certified share G_cert per (Q, loss, p); odd-indexed days report. This is the
draft's matched-channel protocol, kept so that the byte-level results can be compared with the draft's
mask-based ones; Step 5 replaces it with a channel-blind choice.
Every outcome comes from the transmitted bytes (delivery.outcome). Per site in parallel (<= 3 workers).
Outputs: results/<tag>/e2e_tuning.json, e2e_results.csv.
Run from Paper3/: python -I src/p3/run_e2e.py <folder> <tag> [n_per_site=20] [workers=3]
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import channel, delivery, record  # noqa: E402
from p3.loader import load_site_records  # noqa: E402

QS = (1, 6, 12, 24)
PS = (0.1, 0.3, 0.5)
LOSS = ("iid", "gilbert")
DRAWS_TUNE, DRAWS_TEST = 12, 30
SEED = 20261023
REPEATS = (2, 3, 4, 6)
SHARES = (0.25, 0.5, 0.75, 1.0)


def arrivals(kind, n, p, rng):
    return channel.iid(n, p, rng) if kind == "iid" else channel.gilbert(n, p, 3, rng)


def mds_ks(Q):
    return [K for K in range(1, Q + 1) if Q <= 12 or K % 2 == 0]


def candidates(rd, enc, Q):
    out = {"every_k": [delivery.every_k(rd, Q)], "reliable": [delivery.reliable(rd, enc, Q)],
           "repeat": [delivery.repeat(rd, enc, Q, r) for r in REPEATS if r <= Q],
           "mds": [delivery.mds(rd, enc, Q, K) for K in mds_ks(Q)],
           "tag": [delivery.tag(rd, Q, s, seed=SEED + i) for i, s in enumerate(SHARES)]}
    return {k: v for k, v in out.items() if v}


def evaluate(rd, sent, kind, p, draws, rng):
    o = [delivery.outcome(rd, sent, arrivals(kind, len(sent.msgs), p, rng)) for _ in range(draws)]
    return {k: float(np.mean([x[k] for x in o])) for k in ("Phi", "cert", "F")} | \
        {"worst": float(np.median([x["worst"] for x in o]))}


def site_number(name):
    """Seed component of a site: its USGS number, or a checksum of the name for other sources (low-cost nodes)."""
    import zlib
    return int(name[:15]) if name[:15].isdigit() else zlib.crc32(name.encode())


def sample_site(path, n_per):
    days = [d for d in load_site_records(path) if len(d.channels) == 4]
    rng = np.random.default_rng([SEED, int(os.path.basename(path)[:-4][:15])])
    idx = sorted(rng.choice(len(days), size=min(n_per, len(days)), replace=False)) if days else []
    return [days[i] for i in idx]


def tune_site(args):
    path, n_per = args
    rng = np.random.default_rng([SEED, 1, int(os.path.basename(path)[:-4][:15])])
    rows = []
    for rd in sample_site(path, n_per)[::2]:
        enc = record.Encoder(rd.channels)
        for Q in QS:
            cands = candidates(rd, enc, Q)
            for kind in LOSS:
                for p in PS:
                    for fam, lst in cands.items():
                        if fam in ("every_k", "reliable"):
                            continue
                        for j, s in enumerate(lst):
                            rows.append({"Q": Q, "loss": kind, "p": p, "fam": fam, "j": j,
                                         "Phi": evaluate(rd, s, kind, p, DRAWS_TUNE, rng)["Phi"]})
    return rows


def test_site(args):
    path, n_per, tuning = args
    rng = np.random.default_rng([SEED, 2, int(os.path.basename(path)[:-4][:15])])
    rows = []
    for rd in sample_site(path, n_per)[1::2]:
        enc = record.Encoder(rd.channels)
        need = enc.need(1.0)
        for Q in QS:
            cands = candidates(rd, enc, Q)
            for kind in LOSS:
                for p in PS:
                    best = tuning[f"Q{Q}_{kind}_p{p}"]
                    chosen = {"every_k": cands["every_k"][0], "reliable": cands["reliable"][0]}
                    for fam, j in best.items():
                        chosen[fam] = cands[fam][j]
                    for fam, s in chosen.items():
                        rows.append({"Q": Q, "loss": kind, "p": p, "design": fam, "variant": s.name,
                                     "site": rd.site, "day": str(rd.day.date()), "need": need,
                                     "planned": len(s.planned), "bound": s.bound, "tau": s.tau,
                                     **evaluate(rd, s, kind, p, DRAWS_TEST, rng)})
    return rows


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    files = sorted(f for f in os.listdir(folder) if f.endswith(".csv"))
    paths = [os.path.join(folder, f) for f in files]
    os.makedirs(f"results/{tag}", exist_ok=True)
    t0 = time.time()
    with Pool(workers) as pool:
        tune_rows = [r for rows in pool.imap_unordered(tune_site, [(p, n_per) for p in paths]) for r in rows]
    tdf = pd.DataFrame(tune_rows)
    tuning = {}
    for (Q, kind, p), g in tdf.groupby(["Q", "loss", "p"]):
        tuning[f"Q{Q}_{kind}_p{p}"] = {fam: int(gg.groupby("j").Phi.mean().idxmax()) for fam, gg in g.groupby("fam")}
    json.dump(tuning, open(f"results/{tag}/e2e_tuning.json", "w"), indent=1)
    print(f"tuned in {time.time() - t0:.0f} s", flush=True)
    with Pool(workers) as pool:
        rows = [r for rs_ in pool.imap_unordered(test_site, [(p, n_per, tuning) for p in paths]) for r in rs_]
    out = pd.DataFrame(rows)
    out.to_csv(f"results/{tag}/e2e_results.csv", index=False)
    print(f"done in {time.time() - t0:.0f} s; {out.day.nunique()} test days x settings")
    for stat in ("Phi", "F"):
        for kind in LOSS:
            print(f"\nMean {stat} ({'fully certified' if stat == 'Phi' else 'within tolerance, oracle'}), {kind} loss:")
            print(out[out.loss == kind].pivot_table(index=["Q", "p"], columns="design", values=stat).round(3).to_string())


if __name__ == "__main__":
    main()
