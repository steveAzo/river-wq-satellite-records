"""RQ2 (temporal pooling with a buffer) and RQ4 (plan sizing from a pilot), on cached daily needs.

One-way buffer model (the node never learns what arrived, so it never resends):
  - each day's min-# set at tau = 1 (need from need.py) joins a FIFO backlog at the end of the day;
  - every day the node sends ONE coded block: K data messages + (Q - K) Reed-Solomon parity (23-B
    messages, V = 7 values each), filled oldest-first from the backlog; the block decodes iff >= K of its
    Q messages arrive (iid or Gilbert loss);
  - a day's record is guaranteed iff every block that carried any of its values decoded; its delay is
    (day its last block was sent) - (the day itself), so 1 = sent the next day, the minimum (0 only for
    days that need no values);
  - "guaranteed within D" = guaranteed and delay <= D days (D = 7 by default).
K per (Q, loss, p) comes from the development tuning (results/dev/dev_tuning.json); Q = 96 reuses the
K/Q ratio tuned at Q = 24.

RQ4: for each site, the tier is chosen from the first 28 days (pilot) as the smallest tier whose
simulated "guaranteed within 7 d" share on the pilot needs scaled by a safety factor s is >= 0.9
(assumed loss iid p = 0.3). The hindsight tier is the smallest tier reaching >= 0.9 on the rest of the
year. s is tuned on even-indexed sites and evaluated on odd-indexed sites.
Run from Paper3/: python -I src/p3/pooling.py <need_csv> <tag>
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import channel  # noqa: E402

V = 7
TIERS = (1, 6, 12, 24, 96)
SEED = 20261023


def K_for(Q, loss, p, tuning):
    def k_from(q):
        j = tuning[f"Q{q}_{loss}_p{p}"]["mds"]
        return 2 * (j + 1) if q == 24 else j + 1
    if Q in (1, 6, 12, 24):
        return k_from(Q)
    return max(1, round(Q * k_from(24) / 24))


def simulate(needs, Q, K, loss, p, rng, D=7):
    """needs: daily value counts (NaN = no data that day). Returns per-day (guaranteed, delay) for days with data."""
    queue = []  # [day index, remaining values]
    fate = {}   # day -> [all blocks decoded so far, last day sent]
    n = len(needs)
    for d in range(n + 60):  # flush period after the record ends
        cap = V * K
        decoded = None
        while cap > 0 and queue:
            day, rem = queue[0]
            take = min(cap, rem)
            if decoded is None:
                arr = channel.iid(Q, p, rng) if loss == "iid" else channel.gilbert(Q, p, 3, rng)
                decoded = arr.sum() >= K
            f = fate.setdefault(day, [True, d])
            f[0] = f[0] and decoded
            f[1] = d
            cap -= take
            queue[0][1] -= take
            if queue[0][1] == 0:
                queue.pop(0)
        if d < n and not np.isnan(needs[d]):
            if needs[d] > 0:
                queue.append([d, int(needs[d])])
            else:
                fate[d] = [True, d]
    out = []
    for d in range(n):
        if np.isnan(needs[d]):
            continue
        ok, last = fate.get(d, [False, n + 60])
        delay = last - d
        out.append((ok and delay <= D, ok, delay))
    return out


def site_series(df, site):
    g = df[df.site == site].copy()
    g["day"] = pd.to_datetime(g["day"])
    idx = pd.date_range(g.day.min(), g.day.max(), freq="D")
    return g.set_index("day")["values"].reindex(idx).to_numpy(float)


def share_within(needs, Q, K, loss, p, rng, scale=1.0):
    r = simulate(np.where(np.isnan(needs), np.nan, np.ceil(needs * scale)), Q, K, loss, p, rng)
    return float(np.mean([x[0] for x in r])) if r else np.nan


def main():
    need_csv, tag = sys.argv[1], sys.argv[2]
    df = pd.read_csv(need_csv, dtype={"site": str})
    tuning = json.load(open("results/dev/dev_tuning.json"))
    rng = np.random.default_rng(SEED)
    sites = sorted(df.site.unique())
    rows = []
    for site in sites:
        needs = site_series(df, site)
        for Q in TIERS:
            for loss in ("iid", "gilbert"):
                for p in (0.1, 0.3, 0.5):
                    K = K_for(Q, loss, p, tuning)
                    r = [simulate(needs, Q, K, loss, p, rng) for _ in range(5)]
                    g7 = np.mean([[x[0] for x in rr] for rr in r])
                    ge = np.mean([[x[1] for x in rr] for rr in r])
                    dl = np.concatenate([[x[2] for x in rr if x[1]] for rr in r]) if any(rr for rr in r) else np.array([np.nan])
                    rows.append({"site": site, "Q": Q, "K": K, "loss": loss, "p": p, "G7": g7, "G_eventual": ge,
                                 "delay_med": float(np.nanmedian(dl)) if len(dl) else np.nan,
                                 "delay_p95": float(np.nanpercentile(dl, 95)) if len(dl) else np.nan})
        print(site, flush=True)
    out = pd.DataFrame(rows)
    os.makedirs(f"results/{tag}", exist_ok=True)
    out.to_csv(f"results/{tag}/pooling.csv", index=False)
    print("\nRQ2: share of days guaranteed within 7 d, median over sites (iid loss):")
    print(out[out.loss == "iid"].pivot_table(index="Q", columns="p", values="G7", aggfunc="median").round(3).to_string())
    print("Sites with G7 >= 0.9 (iid, p = 0.3):",
          out[(out.loss == "iid") & (out.p == 0.3)].groupby("Q").G7.apply(lambda x: f"{(x >= 0.9).sum()}/{len(x)}").to_dict())
    print("Same, bursty loss:",
          out[(out.loss == "gilbert") & (out.p == 0.3)].groupby("Q").G7.apply(lambda x: f"{(x >= 0.9).sum()}/{len(x)}").to_dict())
    print("Median delay of guaranteed days (iid, p = 0.3):", out[(out.loss == "iid") & (out.p == 0.3)].groupby("Q").delay_med.median().to_dict())

    # ---- RQ4: pilot-based tier choice --------------------------------------------------------------
    def tier_from(needs, scale, K_of):
        for Q in TIERS:
            if share_within(needs, Q, K_of[Q], "iid", 0.3, rng, scale) >= 0.9:
                return Q
        return TIERS[-1]
    K_of = {Q: K_for(Q, "iid", 0.3, tuning) for Q in TIERS}
    pilot, hind = {}, {}
    for site in sites:
        needs = site_series(df, site)
        pilot[site], rest = needs[:28], needs[28:]
        hind[site] = tier_from(rest, 1.0, K_of)
    tune_sites, test_sites = sites[::2], sites[1::2]

    def evaluate(sset, s):
        ch = {x: tier_from(pilot[x], s, K_of) for x in sset}
        suff = np.mean([TIERS.index(ch[x]) >= TIERS.index(hind[x]) for x in sset])
        over1 = np.mean([TIERS.index(ch[x]) - TIERS.index(hind[x]) <= 1 for x in sset])
        return suff, over1, ch
    best_s = max((1.0, 1.25, 1.5, 2.0, 3.0), key=lambda s: (lambda r: (min(r[0], 0.8) + r[1]))(evaluate(tune_sites, s)))
    suff, over1, ch = evaluate(test_sites, best_s)
    print(f"\nRQ4: safety factor tuned on {len(tune_sites)} sites = {best_s}; on {len(test_sites)} test sites: "
          f"sufficient {suff:.2f}, over-provision <= 1 tier {over1:.2f}")
    pd.DataFrame([{"site": x, "pilot_tier": ch[x], "hindsight_tier": hind[x]} for x in test_sites]).to_csv(
        f"results/{tag}/sizing.csv", index=False)
    json.dump({"safety_factor": best_s}, open(f"results/{tag}/sizing_tuning.json", "w"))


if __name__ == "__main__":
    main()
