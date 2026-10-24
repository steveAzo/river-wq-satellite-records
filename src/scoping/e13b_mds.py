"""E13b: does an erasure code across messages beat blind repetition on the one-way link?

Same 200 site-days, split, Q = 6 messages of 19 B and loss probabilities as E13.
mds_K: the min-# set at the smallest tau fitting 6K values is split into K systematic messages and
protected by Q - K parity messages of an MDS (e.g. Reed-Solomon over messages) code, so ANY K of the Q
messages recover all values. If fewer than K arrive, only the systematic messages that arrived are used.
K is tuned per loss probability on the tuning half (even site-days); results on the test half.
Compared with E13's repeat_r (tuned r) and oblivious. Run from Paper3/: python -I src/scoping/e13b_mds.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

here = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("e13", os.path.join(here, "e13_oneway_loss.py"))
e13 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e13)
Q, VPM = 6, e13.VPM


def mds_eval(sd, K, p, rng, draws=40):
    _, v = sd.set_for_budget(VPM * K)
    sys_msgs = [v[i:i + VPM] for i in range(0, len(v), VPM)]
    out = []
    for _ in range(draws):
        arrived = rng.random(Q) > p
        if arrived.sum() >= K:
            got = v
        else:
            got = [x for j, m in enumerate(sys_msgs) if j < Q and arrived[j] for x in m]
        out.append(sd.worst(got))
    out = np.array(out)
    return float((out <= 1).mean()), float(out.mean())


def main():
    e13.e5.TOLSET = "usgs"
    days = e13.e5.load_days()
    items = [(d, s) for d, sites in days.items() for s in sites]
    rng = np.random.default_rng(20261023)
    pick = rng.choice(len(items), size=200, replace=False)  # same sample as E13
    sds = [e13.SiteDay(*days[items[i][0]][items[i][1]]) for i in pick]
    tune, test = sds[::2], sds[1::2]
    rows = []
    for p in (0.1, 0.3, 0.5):
        bestK = max(range(1, Q + 1), key=lambda K: np.mean([mds_eval(sd, K, p, rng, 15)[0] for sd in tune]))
        bestR = max((1, 2, 3, 6), key=lambda r: np.mean([e13.evaluate(sd, e13.messages(sd.set_for_budget(VPM * Q // r)[1], r)[:Q], p, rng, 15)[0] for sd in tune]))
        for sd in test:
            ok, mw = mds_eval(sd, bestK, p, rng)
            rows.append({"p": p, "strategy": f"mds (K={bestK})", "p_ok": ok, "mean_worst": mw})
            ok, mw = e13.evaluate(sd, e13.messages(sd.set_for_budget(VPM * Q // bestR)[1], bestR)[:Q], p, rng)
            rows.append({"p": p, "strategy": f"repeat (r={bestR})", "p_ok": ok, "mean_worst": mw})
        print(p, "K", bestK, "r", bestR, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("results/scoping/e13b_mds.csv", index=False)
    print(out.groupby(["p", "strategy"])[["p_ok", "mean_worst"]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
