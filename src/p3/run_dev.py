"""Development run (2023 USGS only; study plan Section 8, step 3).

Stratified sample of site-days (up to N_PER_SITE per site, seed 20261023). Even-indexed site-days tune
the design parameters (repeat r, MDS K, SRDL data share) per (Q, loss model, p); odd-indexed site-days
report. Output: results/dev/dev_tuning.json and results/dev/dev_results.csv.
Run from Paper3/: python -I src/p3/run_dev.py [n_per_site=20]
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import channel, designs, pla, server  # noqa: E402
from p3.data import load_folder  # noqa: E402

QS = (1, 6, 12, 24)
PS = (0.1, 0.3, 0.5)
LOSS = ("iid", "gilbert")
DRAWS_TUNE, DRAWS_TEST = 12, 30
SEED = 20261023


def arrivals(kind, n, p, rng):
    return channel.iid(n, p, rng) if kind == "iid" else channel.gilbert(n, p, 3, rng)


def run_plan(sd, plan, kind, p, draws, rng):
    g, c, w = [], [], []
    for _ in range(draws):
        got = plan.delivered(arrivals(kind, len(plan.tx), p, rng))
        s = server.score(sd, got)
        g.append(s["guaranteed"])
        w.append(s["worst"])
        c.append(server.certified_share(sd, plan.planned, got) if plan.tau is not None and plan.tau <= 1 else 0.0)
    return float(np.mean(g)), float(np.mean(c)), float(np.mean(w))


def candidates(enc, Q, rng):
    out = {"raw_periodic": [designs.raw_periodic(enc.sd, Q)], "reliable_opt": [designs.reliable_opt(enc, Q)]}
    out["repeat"] = [designs.repeat_r(enc, Q, r) for r in (2, 3, 4, 6) if r <= Q]
    out["mds"] = [designs.mds_K(enc, Q, K) for K in range(1, Q + 1) if Q <= 24 and (Q <= 12 or K % 2 == 0)]
    out["srdl_style"] = [designs.srdl_style(enc, Q, share, rng=np.random.default_rng(SEED + i))
                         for i, share in enumerate((0.25, 0.5, 0.75, 1.0))]
    return {k: v for k, v in out.items() if v}


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    days = load_folder("data/clean/usgs", "excellent")
    rng = np.random.default_rng(SEED)
    by_site = {}
    for sd in days:
        by_site.setdefault(sd.site, []).append(sd)
    sample = []
    for site, lst in sorted(by_site.items()):
        idx = rng.choice(len(lst), size=min(n_per, len(lst)), replace=False)
        sample += [lst[i] for i in sorted(idx)]
    print(f"{len(days)} dev site-days; sample {len(sample)}", flush=True)
    encs = []
    for i, sd in enumerate(sample):
        encs.append(pla.Encoder(sd))
        if i % 100 == 0:
            print("encoded", i, flush=True)
    tune, test = encs[::2], encs[1::2]
    tuning = {}
    rows = []
    for Q in QS:
        for kind in LOSS:
            for p in PS:
                key = f"Q{Q}_{kind}_p{p}"
                best = {}
                for fam in ("repeat", "mds", "srdl_style"):
                    scores = {}
                    for enc in tune:
                        for j, pl in enumerate(candidates(enc, Q, rng).get(fam, [])):
                            scores.setdefault(j, []).append(run_plan(enc.sd, pl, kind, p, DRAWS_TUNE, rng)[0])
                    if scores:
                        best[fam] = int(max(scores, key=lambda j: np.mean(scores[j])))
                tuning[key] = best
                for enc in test:
                    cands = candidates(enc, Q, rng)
                    chosen = {"raw_periodic": cands["raw_periodic"][0], "reliable_opt": cands["reliable_opt"][0]}
                    for fam, j in best.items():
                        chosen[fam] = cands[fam][j]
                    for fam, pl in chosen.items():
                        g, c, w = run_plan(enc.sd, pl, kind, p, DRAWS_TEST, rng)
                        rows.append({"Q": Q, "loss": kind, "p": p, "design": fam, "variant": pl.name,
                                     "site": enc.sd.site, "day": str(enc.sd.day.date()), "G": g, "C": c, "worst": w,
                                     "tx": len(pl.tx)})
                print(key, best, flush=True)
    os.makedirs("results/dev", exist_ok=True)
    json.dump(tuning, open("results/dev/dev_tuning.json", "w"), indent=1)
    out = pd.DataFrame(rows)
    out.to_csv("results/dev/dev_results.csv", index=False)
    print("\nMean G (share of test site-days fully within tolerance), iid loss:")
    print(out[out.loss == "iid"].pivot_table(index=["Q", "p"], columns="design", values="G").round(3).to_string())
    print("\nMean G, bursty (Gilbert, mean burst 3) loss:")
    print(out[out.loss == "gilbert"].pivot_table(index=["Q", "p"], columns="design", values="G").round(3).to_string())


if __name__ == "__main__":
    main()
