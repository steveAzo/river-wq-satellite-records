"""Version 3, Phase 1b (completion): byte-level recovery AND decisions on the CRC-24 frame (frame3 with CRCB = 3), both loss models.
Real messages are built (record only, and the 3b rule with hard objects layered and easy objects hosted), lost under independent loss and
Gilbert bursts (p = 0.3), decoded by the real receiver; the decoded record values and witnesses are turned into the same knowledge objects
and decisions as in the slot model (proto_base4.know and decide), so only the recovery step differs from the slot model. Compared on the
slot-model run results/v3dev/dev_d2 (4 slots per message; levels over all days, read with src/p3v3/eval3.py): whole record recovered, and the
share of hard cases at the two alternative threshold sets decided correctly (kinds DO, pH, conductance), plus wrong decisions. DEVELOPMENT DATA ONLY.
Run from Paper3/: python -I src/p3v3/bytecheck2.py <outname> <every n-th day> <draws> [sites...]"""
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import frame3 as f3  # noqa: E402
import integrity3 as i3  # noqa: E402
import proto_base4 as pb  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

SEED = 20261114
CONDS = (("iid_p0.3", ("iid", 0.3, None)), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3)))
WMAP = {"DOmin": ("W", "DO"), "pHmin": ("W", "pHmin"), "pHmax": ("W", "pHmax"), "Tmax": ("W", "T"), "ECa": ("W", "ECa"), "ECb": ("W", "ECb")}
KINDS = (("do", 0), ("ph", 1), ("ec", 2))
ALT = ("alt1", "alt2")


def run_site(path, every, draws, rng, tag="dev"):
    f3.CRCB, f3.RECCRC = 3, False
    site, items, res = prepare_items(path, tag)
    rows = []
    for it in items[::every]:
        it["meta"] = pb.day_meta(it)
        vals, bound, n = it["vals"], it["bound"], len(it["vals"])
        for variant in ("rec", "heur"):
            for Q in (6, 12):
                try:
                    blk, lay, _h = i3.build(it, Q, "record" if variant == "rec" else "3b")
                except ValueError:
                    continue
                for cname, c in CONDS:
                    masks = rr.sim_masks(c, Q, rng, draws=draws)
                    memo = {}
                    full = ok_alt = n_alt = wrong = 0
                    for m in masks:
                        keep = [i for i in range(Q) if m[i]]
                        d = f3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else f3.Decoded()
                        good = {p for p, v in d.values.items() if p < n and v == vals[p]} if not d.record_rejected else set()
                        key = {("R", p) for p in good} | {WMAP[k] for k in d.witness if not d.witness_rejected}
                        full += bool(bound) and len(good) == n
                        key = frozenset(key)
                        if key not in memo:
                            memo[key] = pb.decide(it, pb.know(it, vals, bound, key, res, "pla", 1.0))[0]
                        dec = memo[key]
                        for v in ALT:
                            for kind, idx in KINDS:
                                t = it["meta"]["truth"][v][kind]
                                h = it["meta"]["hard"][v][kind]
                                if t is None or h is None:
                                    continue
                                x = dec[v][idx]
                                if x != -1 and x != int(t):
                                    wrong += 1
                                if h:
                                    n_alt += 1
                                    ok_alt += int(x != -1 and x == int(t))
                    rows.append((site, it["d"], Q, cname, variant, full / draws, ok_alt, n_alt, wrong))
    f3.CRCB, f3.RECCRC = 2, False
    return rows


def main():
    outname, every, draws = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    only = set(sys.argv[4:])
    rng = np.random.default_rng(SEED)
    R = []
    for path in sorted(glob.glob(os.path.join(i3.FOLDER, "*.csv"))):
        site = os.path.basename(path)[:-4]
        if only and site not in only:
            continue
        R += run_site(path, every, draws, rng)
        print(site, len(R), flush=True)
    b = pd.DataFrame(R, columns=["site", "day", "Q", "cond", "design", "full", "ok_alt", "n_alt", "wrong"])
    b.to_csv(f"results/v3dev/bytecheck2_{outname}.csv", index=False)
    print("\nbyte level (CRC-24 frame): whole record recovered | hard cases at alternative thresholds decided correctly | wrong decisions")
    for (Q, cond, dsg), z in b.groupby(["Q", "cond", "design"]):
        print(f"Q={Q:2d} {cond:16s} {dsg:5s} {z.full.mean():.3f} | {z.ok_alt.sum() / z.n_alt.sum():.3f} | wrong {int(z.wrong.sum())} (days {len(z)})")


if __name__ == "__main__":
    main()
