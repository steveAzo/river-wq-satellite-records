"""E2: self-contained versus chained days under loss, with bursts across midnight (revision Step 4; review M3, E2).
2023 data only.

Pairs of consecutive four-parameter record days (d, d+1), up to N_PAIRS per site (seed 20261023). Both days use
the same design (MDS with the K tuned for G_cert in results/<tag>/e2e_tuning.json, or repetition with its tuned r)
at Q messages per day. The 2Q transmissions of the two days pass through ONE loss process in order, so a Gilbert
burst can span midnight.
  self:  day d+1 is planned without an anchor and certified on its own.
  chain: day d+1 is planned from anchors = day d's last planned value of each channel (dequantised; the encoder
         knows them). The server uses an anchor only if day d's received bytes prove it is that channel's last
         value (record.certify's rule 4); otherwise it holds the first value back and the head is not certified.
Reported for day d+1: G_cert, G_ok, the planned values, and (chain) the share of days that decoded completely but
lost certification because the anchor was missing.
Run from Paper3/: python -I src/p3/e2_anchor.py <folder> <tag> [Q=6] [n_pairs=10] [workers=3]
"""
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, frame, record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3.loader import RecordDay, load_site_records  # noqa: E402

DRAWS = 30


def known_last(rx, last):
    """{param: dequantised value} of values that the received positions prove to be their channel's last."""
    out = {}
    for i, (p, s, c) in rx.items():
        nxt = rx.get(i + 1)
        if i == last or (nxt is not None and nxt[0] != p):
            out[p] = float(frame.dequantise(p, c))
    return out


def build(rd, Q, fam, j, anchors=None):
    if anchors is not None:
        rd = RecordDay(rd.site, rd.day, [record.Channel(c.param, c.x, c.tol, anchors[c.param]) for c in rd.channels],
                       rd.steps)
    enc = record.Encoder(rd.channels)
    if fam == "mds":
        return rd, delivery.mds(rd, enc, Q, re2.mds_ks(Q)[j])
    return rd, delivery.repeat(rd, enc, Q, [r for r in re2.REPEATS if r <= Q][j])


def score_next(rd1, s1, mask1, anchors_known):
    """Day d+1: certificate and oracle error, given the anchors the server can prove (None = self)."""
    day = delivery.day_number(rd1.day)
    rx, last, bound, _ = delivery.receive([m for m, ok in zip(s1.msgs, mask1) if ok], day)
    if anchors_known is None:
        cert, full = record.certify(rx, rd1.n_of, bound, last)
        e = record.errors(rd1.channels, rx)
    else:
        cert, full = record.certify(rx, rd1.n_of, bound, last, anchor_ok={p: p in anchors_known for p in rd1.n_of})
        e = record.errors(rd1.channels, rx, anchors_known)
    worst = max(float(np.nanmax(v)) if np.isfinite(v).all() else np.inf for v in e.values())
    all_arrived = last is not None and all(i in rx for i in range(last + 1))
    return bool(full), worst <= 1 + 1e-9, all_arrived


def run_site(args):
    path, Q, n_pairs, tuning = args
    days = [d for d in load_site_records(path) if len(d.channels) == 4]
    pairs = [(a, b) for a, b in zip(days, days[1:]) if (b.day - a.day).days == 1]
    site_id = int(os.path.basename(path)[:-4][:15])
    rng = np.random.default_rng([re2.SEED, 3, site_id])
    if not pairs:
        return []
    pick = sorted(rng.choice(len(pairs), size=min(n_pairs, len(pairs)), replace=False))
    rows = []
    for i in pick:
        rd0, rd1 = pairs[i]
        for loss in re2.LOSS:
            best = tuning[f"Q{Q}_{loss}_p0.3"]
            for fam in ("mds", "repeat"):
                j = best[fam]
                _, s0 = build(rd0, Q, fam, j)
                _, s1_self = build(rd1, Q, fam, j)
                anchors = {p: float(frame.dequantise(p, [v for v in s0.planned if v[0] == p][-1][2])) for p in rd1.params}
                rd1c, s1_chain = build(rd1, Q, fam, j, anchors)
                acc = {"self": [], "chain": [], "chain_lost_anchor": []}
                for _ in range(DRAWS):
                    mask = re2.arrivals(loss, 2 * Q, 0.3, rng)
                    m0, m1 = mask[:len(s0.msgs)], mask[Q:Q + len(s1_self.msgs)]
                    rx0, last0, _, _ = delivery.receive([m for m, ok in zip(s0.msgs, m0) if ok], delivery.day_number(rd0.day))
                    acc["self"].append(score_next(rd1, s1_self, m1, None))
                    kl = known_last(rx0, last0)
                    c = score_next(rd1c, s1_chain, m1, kl)
                    acc["chain"].append(c)
                    acc["chain_lost_anchor"].append(c[2] and not c[0] and len(kl) < len(rd1.params))
                rows.append({"site": rd1.site, "day": str(rd1.day.date()), "loss": loss, "design": fam, "Q": Q,
                             "planned_self": len(s1_self.planned), "planned_chain": len(s1_chain.planned),
                             "bound_self": s1_self.bound, "bound_chain": s1_chain.bound,
                             "need_self": record.Encoder(rd1.channels).need(1.0), "need_chain": record.Encoder(rd1c.channels).need(1.0),
                             "Gcert_self": np.mean([a[0] for a in acc["self"]]), "Gok_self": np.mean([a[1] for a in acc["self"]]),
                             "Gcert_chain": np.mean([a[0] for a in acc["chain"]]), "Gok_chain": np.mean([a[1] for a in acc["chain"]]),
                             "chain_lost_anchor": np.mean(acc["chain_lost_anchor"])})
    return rows


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    Q = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    n_pairs = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    tuning = json.load(open(f"results/{tag}/e2e_tuning.json"))
    paths = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".csv")]
    with Pool(workers) as pool:
        rows = [r for rr in pool.imap_unordered(run_site, [(p, Q, n_pairs, tuning) for p in paths]) for r in rr]
    out = pd.DataFrame(rows)
    out.to_csv(f"results/{tag}/e2_anchor_Q{Q}.csv", index=False)
    print(f"E2 at Q = {Q}, p = 0.3: {out.day.nunique()} day pairs at {out.site.nunique()} sites")
    print(out.groupby(["loss", "design"])[["need_self", "need_chain", "Gcert_self", "Gcert_chain", "Gok_self",
                                          "Gok_chain", "chain_lost_anchor"]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
