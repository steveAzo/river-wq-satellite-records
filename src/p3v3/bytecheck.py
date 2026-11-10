"""Version 3, Phase 1b (docs/METHOD_V3_PLAN.md): does the slot model predict what the byte-level frame (src/p3/frame2.py) does?
For the record-only design and the 3b rule (hard objects in a layered group, easy objects hosted in the last record unit), every
sampled development day is encoded into real messages, messages are lost independently (p = 0.3), and the real receiver runs on the
survivors. Compared with the slot model on the same days: share of days with the whole record recovered, and share with the layered
witnesses decoded. DEVELOPMENT DATA ONLY. Not a confirmation.
Run from Paper3/: python -I src/p3v3/bytecheck.py <outname> <every n-th day> <draws> [sites...]"""
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame2 as f2  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

SEED = 20261111
P_LOSS = 0.3
TAG = "dev"
FOLDER = "data/clean/usgs"


def witness_dict(it):
    wt = it["wit"]
    out = {"DOmin": wt["DOmin"][2], "pHmin": wt["pHmin"][2], "pHmax": wt["pHmax"][2], "Tmax": it["tw"][1]}
    if it["ew"] is not None:
        out["ECa"], out["ECb"] = it["ew"][1], it["ew"][3]
    return out


def split(it):
    """Hard objects (layered) and easy objects (hosted), in the slot model's order."""
    W = witness_dict(it)
    names = {"DO": ("DOmin",), "pH": ("pHmin", "pHmax"), "T": ("Tmax",), "EC": ("ECa", "ECb")}
    lay, host = {}, {}
    for o, ns in names.items():
        if o == "EC" and it["ew"] is None:
            continue
        for n in ns:
            (lay if it["hard"][o] else host)[n] = W[n]
    return lay, host


def build(it, Q, design):
    vals, bound = it["vals"], it["bound"]
    if design == "rec":
        return f2.build_block(vals, bound, it["d"], Q), {}
    lay, host = split(it)
    kw = 2 if len(lay) > 1 else 1
    for h in (host, {}):                          # hosting may not fit; fall back to no hosting
        try:
            return f2.build_block(vals, bound, it["d"], Q, layered=lay or None, kw=kw, hosted=h or None), lay
        except (ValueError, AssertionError):
            continue
    raise ValueError("cannot build")


def run_site(path, every, draws, rng):
    site, items, _ = prepare_items(path, TAG)
    rows = []
    for it in items[::every]:
        for Q in (6, 12):
            for design in ("rec", "heur"):
                try:
                    blk, lay = build(it, Q, design)
                except ValueError:
                    rows.append((site, it["d"], Q, design, None, None, None))
                    continue
                n = len(it["vals"])
                full = wit = 0
                for _ in range(draws):
                    keep = [i for i in range(Q) if rng.random() >= P_LOSS]
                    d = f2.receive([blk.messages[i] for i in keep]) if keep else f2.Decoded()
                    ok = (not d.record_rejected) and len(d.values) == n and all(d.values.get(i) == it["vals"][i] for i in range(n))
                    full += bool(it["bound"]) and ok
                    wit += bool(lay) and (not d.witness_rejected) and all(d.witness.get(k) == v for k, v in lay.items())
                rows.append((site, it["d"], Q, design, full / draws, wit / draws if lay else None, blk.K))
    return rows


def slot_level(site, days, outdir):
    out = []
    for Q in (6, 12):
        f = f"{outdir}/{site}_Q{Q}.csv"
        try:
            z = pd.read_csv(f, dtype={"site": str})
        except Exception:
            continue
        z = z[(z.kind == "day") & (z.cond == "iid_p0.3") & z.day.isin(days)]
        out.append(z.assign(Q=Q, site=site))        # the merged files lost leading zeros of the site column
    return pd.concat(out) if out else pd.DataFrame()


def main():
    outname, every, draws = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    only = set(sys.argv[4:])
    os.makedirs("results/v3dev", exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows, slot = [], []
    for path in sorted(glob.glob(os.path.join(FOLDER, "*.csv"))):
        site = os.path.basename(path)[:-4]
        if only and site not in only:
            continue
        r = run_site(path, every, draws, rng)
        rows += r
        days = {x[1] for x in r}
        s = slot_level(site, days, "results/v3dev/dev_cap4all")
        if len(s):
            slot.append(s)
        print(site, len(r), flush=True)
    b = pd.DataFrame(rows, columns=["site", "day", "Q", "design", "byte_full", "byte_wit", "K"])
    b.to_csv(f"results/v3dev/bytecheck_{outname}.csv", index=False)
    s = pd.concat(slot)
    s.to_csv(f"results/v3dev/bytecheck_{outname}_slot.csv", index=False)
    print("\nlevel of whole-record recovery (days where the byte frame could build a block)")
    for Q in (6, 12):
        for d in ("rec", "heur"):
            z = b[(b.Q == Q) & (b.design == d) & b.byte_full.notna()]
            m = s[(s.Q == Q) & (s.design == d)].merge(z[["site", "day"]], on=["site", "day"])
            print(f"Q={Q} {d:5s} byte {z.byte_full.mean():.3f}  slot {m.rec_full.mean():.3f}  days {len(z)}  unbuildable {int(b[(b.Q == Q) & (b.design == d)].byte_full.isna().sum())}")
    z = b[(b.design == "heur") & b.byte_wit.notna()]
    print("\nlayered witnesses decoded (byte), by Q:", z.groupby("Q").byte_wit.mean().round(3).to_dict())


if __name__ == "__main__":
    main()
