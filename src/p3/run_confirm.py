"""Confirmatory RQ3 run (study plan Section 8, step 5): frozen design parameters, no re-tuning.

Applies results/dev/dev_tuning.json (chosen candidate per design family, Q, loss model and p) to a
stratified sample of confirmation site-days (up to N_PER_SITE per site, same seed rule as development)
and reports every site-day in the sample. Reuses run_dev.py unchanged.
Output: results/confirm/<tag>_rq3.csv.
Run from Paper3/: python -I src/p3/run_confirm.py <folder> <tag> [n_per_site=20]
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import pla  # noqa: E402
from p3 import run_dev as rd  # noqa: E402
from p3.data import load_folder  # noqa: E402


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    tuning = json.load(open("results/dev/dev_tuning.json"))
    days = load_folder(folder, "excellent")
    rng = np.random.default_rng(rd.SEED)
    by_site = {}
    for sd in days:
        by_site.setdefault(sd.site, []).append(sd)
    sample = []
    for site, lst in sorted(by_site.items()):
        idx = rng.choice(len(lst), size=min(n_per, len(lst)), replace=False)
        sample += [lst[i] for i in sorted(idx)]
    print(f"{len(days)} site-days; sample {len(sample)}", flush=True)
    encs = [pla.Encoder(sd) for sd in sample]
    rows = []
    for Q in rd.QS:
        for kind in rd.LOSS:
            for p in rd.PS:
                best = tuning[f"Q{Q}_{kind}_p{p}"]
                for enc in encs:
                    cands = rd.candidates(enc, Q, rng)
                    chosen = {"raw_periodic": cands["raw_periodic"][0], "reliable_opt": cands["reliable_opt"][0]}
                    for fam, j in best.items():
                        if fam in cands and j < len(cands[fam]):
                            chosen[fam] = cands[fam][j]
                    for fam, pl in chosen.items():
                        g, c, w = rd.run_plan(enc.sd, pl, kind, p, rd.DRAWS_TEST, rng)
                        rows.append({"Q": Q, "loss": kind, "p": p, "design": fam, "variant": pl.name,
                                     "site": enc.sd.site, "day": str(enc.sd.day.date()), "G": g, "C": c, "worst": w})
                print(Q, kind, p, flush=True)
    os.makedirs("results/confirm", exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv(f"results/confirm/{tag}_rq3.csv", index=False)
    for kind in rd.LOSS:
        print(f"\nMean G, {kind} loss ({tag}):")
        print(out[out.loss == kind].pivot_table(index=["Q", "p"], columns="design", values="G").round(3).to_string())


if __name__ == "__main__":
    main()
