"""Step 5, phase 2: channel-blind selection, regret, mismatch, and pilot estimation (docs/STEP5_PLAN.md).
Offline, from results/<tag>/robust_exact.csv. Outputs in results/<tag>/: robust_summary.csv (G_cert of every
design and rule under every true channel, test days), robust_regret.csv, robust_mismatch.csv (Fig. C),
robust_pilot.csv, robust_choice.json (channel-blind parameters for the byte-level confirmation).
Run from Paper3/: python -I src/p3/robust_eval.py <tag>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import run_robust as rr  # noqa: E402

PARAMETRIC = ("mds", "repeat", "tag")
FIXED = ("mds_rec", "rep_rec", "rep_block_rec", "tag_rec", "reliable", "every_k")
CH = [rr.ch_name(c) for c in rr.CHANNELS]
TUNE = [rr.ch_name(c) for c in rr.TUNE_CHANNELS]
PILOT_DAYS, PILOT_REPS = 28, 1000


def table(df, split):
    return df[df.split == split].groupby(["Q", "fam", "j"])[CH].mean()


def choose(T, Q, fam):
    t = T.loc[(Q, fam)]
    oracle = {c: int(t[c].idxmax()) for c in CH}
    regret = pd.concat([t[c].max() - t[c] for c in TUNE], axis=1).max(axis=1)
    return {"oracle": oracle, "minimax": int(regret.idxmin()), "mean": int(t[TUNE].mean(axis=1).idxmax())}


def nearest_tune(p_hat, bursty):
    p = min((0.1, 0.3, 0.5), key=lambda x: abs(x - p_hat))
    return f"gilbert_p{p}_b3" if bursty else f"iid_p{p}"


def pilot_choice(c, Q, rng):
    """Server-side estimate from PILOT_DAYS x Q message indices -> nearest tuning channel."""
    m = rr.sim_masks(c, PILOT_DAYS * Q, rng, draws=1)[0]
    p_hat = 1 - m.mean()
    lost = ~m
    runs, run = [], 0
    for x in lost:
        if x:
            run += 1
        elif run:
            runs.append(run)
            run = 0
    if run:
        runs.append(run)
    mean_run = np.mean(runs) if runs else 0.0
    iid_run = 1 / (1 - p_hat) if p_hat < 1 else np.inf
    return nearest_tune(p_hat, mean_run > (iid_run + 3) / 2)


def main():
    tag = sys.argv[1]
    df = pd.read_csv(f"results/{tag}/robust_exact.csv", dtype={"site": str})
    T, S = table(df, "tune"), table(df, "test")
    rng = np.random.default_rng(20261025)
    rows, regret, mism, pilot, choice = [], [], [], [], {}
    for Q in sorted(df.Q.unique()):
        choice[int(Q)] = {}
        for fam in FIXED:
            for c in CH:
                rows.append({"Q": Q, "design": fam, "rule": "none", "channel": c, "G_cert": S.loc[(Q, fam, 0), c]})
        for fam in PARAMETRIC:
            if (Q, fam) not in T.index.droplevel(2):
                continue
            ch = choose(T, Q, fam)
            choice[int(Q)][fam] = {"minimax": ch["minimax"], "mean": ch["mean"]}
            for c in CH:
                for rule in ("minimax", "mean"):
                    rows.append({"Q": Q, "design": fam, "rule": rule, "channel": c, "j": ch[rule],
                                 "G_cert": S.loc[(Q, fam, ch[rule]), c]})
                rows.append({"Q": Q, "design": fam, "rule": "oracle", "channel": c, "j": ch["oracle"][c],
                             "G_cert": S.loc[(Q, fam, ch["oracle"][c]), c]})
                rows.append({"Q": Q, "design": fam, "rule": "hindsight", "channel": c,
                             "j": int(S.loc[(Q, fam)][c].idxmax()), "G_cert": S.loc[(Q, fam)][c].max()})
                for assumed in TUNE:
                    mism.append({"Q": Q, "design": fam, "assumed": assumed, "true": c, "j": ch["oracle"][assumed],
                                 "G_cert": S.loc[(Q, fam, ch["oracle"][assumed]), c]})
            for c_tuple in rr.CHANNELS:
                c = rr.ch_name(c_tuple)
                g = [S.loc[(Q, fam, ch["oracle"][pilot_choice(c_tuple, Q, rng)]), c] for _ in range(PILOT_REPS)]
                pilot.append({"Q": Q, "design": fam, "channel": c, "G_cert_pilot": float(np.mean(g)),
                              "G_cert_oracle": S.loc[(Q, fam, ch["oracle"][c]), c]})
    out = pd.DataFrame(rows)
    os.makedirs(f"results/{tag}", exist_ok=True)
    out.to_csv(f"results/{tag}/robust_summary.csv", index=False)
    pd.DataFrame(mism).to_csv(f"results/{tag}/robust_mismatch.csv", index=False)
    pd.DataFrame(pilot).to_csv(f"results/{tag}/robust_pilot.csv", index=False)
    json.dump(choice, open(f"results/{tag}/robust_choice.json", "w"), indent=1)

    # regret of each design/rule against the best fixed-K code tuned for the true channel (oracle mds)
    ref = out[(out.design == "mds") & (out.rule == "oracle")].set_index(["Q", "channel"]).G_cert
    out["regret_vs_oracle_mds"] = ref.reindex(pd.MultiIndex.from_frame(out[["Q", "channel"]])).to_numpy() - out.G_cert
    out.to_csv(f"results/{tag}/robust_regret.csv", index=False)
    print(f"test days: {df[df.split == 'test'][['site', 'day']].drop_duplicates().shape[0]}, "
          f"tuning days: {df[df.split == 'tune'][['site', 'day']].drop_duplicates().shape[0]}")
    pd.set_option("display.width", 250)
    for Q in sorted(df.Q.unique()):
        o = out[out.Q == Q]
        piv = o[o.rule.isin(["none", "minimax", "oracle"])].pivot_table(index=["design", "rule"], columns="channel",
                                                                          values="G_cert")[CH]
        print(f"\n== Q = {Q}: G_cert on test days (rows: design, rule; columns: true channel) ==")
        print(piv.round(3).to_string())
        r = o[o.rule.isin(["none", "minimax", "mean"])].groupby(["design", "rule"]).regret_vs_oracle_mds.agg(["max", "mean"])
        print("regret vs the fixed-K code tuned for the true channel (max, mean over 15 channels):")
        print(r.round(3).to_string())
        print("chosen parameters:", choice[int(Q)])
    pl = pd.DataFrame(pilot)
    print("\npilot-estimated configuration, mean G_cert loss vs oracle (max over channels):")
    print((pl.G_cert_oracle - pl.G_cert_pilot).groupby([pl.Q, pl.design]).max().round(3).to_string())

    # analytic vs byte-level simulation (Step 4 run, same test days)
    e2e = f"results/{tag}/e2e_results.csv"
    if os.path.exists(e2e):
        e = pd.read_csv(e2e, dtype={"site": str})
        print("\nexact vs byte-simulated mean G_cert, same test days and variants (Step 4 run):")
        for (Q, loss, p), g in e[e.design.isin(["mds", "repeat", "reliable", "every_k"])].groupby(["Q", "loss", "p"]):
            c = f"iid_p{p}" if loss == "iid" else f"gilbert_p{p}_b3"
            for _, x in g.groupby("design"):
                var = x.variant.iloc[0]
                ex = df[(df.split == "test") & (df.Q == Q) & (df.variant == var)].merge(x[["site", "day"]], on=["site", "day"])[c]
                if len(ex) and Q in (6, 12) and p == 0.3:
                    print(f"  Q {Q:2d} {loss:7s} p {p} {var:9s} exact {ex.mean():.3f}  bytes {x.Phi.mean():.3f}  (n = {len(x)})")


if __name__ == "__main__":
    main()
