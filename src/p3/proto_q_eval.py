"""Evaluation of Step 3b (src/p3/proto_queries.py): decisive-correct share by design for 7DADM windows and conductance
pulses, by stratum, record recovery by design, and paired site-clustered contrasts.
Run from Paper3/: python -I src/p3/proto_q_eval.py <tag> <Q> [Q2 ...]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

B = 1000
NAMES = {"rec": "record only", "flat": "flat (witness in record code)", "pet1": "PET c=1", "pet2": "PET c=2",
         "spare": "spare slots", "adapt": "decision-aware (hard days layered)", "randmix": "control: random days"}


def read(pattern):
    return pd.concat([pd.read_csv(f, dtype={"site": str}) for f in glob.glob(pattern) if os.path.getsize(f) > 10])


def ci(z, col, rng):
    g = z.groupby("site")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), (B, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return f"{s.sum() / c.sum():.3f} ({np.percentile(bs, 2.5):.3f} to {np.percentile(bs, 97.5):.3f})"


def site_means(z, col):
    return z.groupby("site")[col].mean()


def contrast(parts, x, y, rng):
    out = []
    for name, (zx, zy, col) in parts.items():
        a, b = site_means(zx[zx.design == x], col), site_means(zy[zy.design == y], col)
        v = (a - b).dropna().to_numpy()
        if not len(v):
            continue
        bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
        out.append(f"{name} {v.mean():+.3f} ({np.percentile(bs, 2.5):+.3f} to {np.percentile(bs, 97.5):+.3f})")
    return "; ".join(out)


def report(d, kind, cond, rec_rows, label, strata, rng):
    z = d[(d.kind == kind) & (d.cond == cond)].copy()
    z["hard"], z["truth"] = z["hard"].astype(bool), z["truth"].astype(bool)
    z = z.reset_index(drop=True)
    rr_ = rec_rows[rec_rows.cond == cond]
    rows = []
    for dn, nm in NAMES.items():
        zz = z[z.design == dn]
        if zz.empty:
            continue
        row = {"design": nm, "record recovered": ci(rr_[rr_.design == dn], "rec_full", rng)}
        for sname, mask in strata.items():
            row[sname] = ci(zz[mask(zz)], "decided_correct", rng)
        rows.append(row)
    print(f"\n### {label}, {cond}\n" + pd.DataFrame(rows).to_markdown(index=False))
    parts = {"record": (rr_, rr_, "rec_full"), "decisions, hard": (z[z.hard], z[z.hard], "decided_correct"),
             "decisions, all": (z, z, "decided_correct")}
    print(f"\nPaired differences, {label}, {cond} (sites resampled, 95% interval):")
    for x, y in (("adapt", "randmix"), ("adapt", "flat"), ("adapt", "pet1"), ("adapt", "rec"), ("flat", "rec")):
        print(f"  {x} minus {y}: " + contrast(parts, x, y, rng))


def main():
    tag = sys.argv[1]
    rng = np.random.default_rng(5)
    for Q in map(int, sys.argv[2:]):
        d = read(f"results/{tag}/proto_q/*_Q{Q}.csv")
        print(f"\n## Q = {Q}: {d.site.nunique()} sites; wrong decisions max {d.wrong.max():.3f}; "
              f"7DADM windows {d[(d.kind == 'win7') & (d.cond == 'perfect') & (d.design == 'rec')].shape[0]}; "
              f"conductance days {d[(d.kind == 'ec') & (d.cond == 'perfect') & (d.design == 'rec')].shape[0]}")
        day = d[d.kind == "day"]
        ec = d[d.kind == "ec"]
        s7 = {"all windows": lambda z: pd.Series(True, index=z.index), "near (within 2 degC)": lambda z: z.hard,
              "event (mean above 20)": lambda z: z.truth, "non-event": lambda z: ~z.truth}
        se = {"all days": lambda z: pd.Series(True, index=z.index), "hard (rate at least 4%)": lambda z: z.hard,
              "event (above 10%)": lambda z: z.truth, "non-event": lambda z: ~z.truth}
        for cond in ("perfect", "iid_p0.3", "gilbert_p0.3_b3"):
            report(d, "win7", cond, day, "7DADM", s7, rng)
            report(d, "ec", cond, ec, "Conductance pulse", se, rng)


if __name__ == "__main__":
    main()
