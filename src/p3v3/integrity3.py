"""Version 3, Phase 2 (docs/METHOD_V3_PLAN.md, Section 8, rules written before this run): integrity study on DEVELOPMENT data.
Designs D0 (frame v2), D1 (plus record CRC-32), D2 (CRC-24 per message), D3 (D1 plus D2), built with src/p3v3/frame3.py.
Per development day (every n-th): record-only and 3b-rule blocks (hard objects layered, easy objects hosted) at Q = 6 and 12; independent
loss 0.3; (a) forced CRC-valid forgery of one arrived message (content random, check recomputed), receiver with sanity and corroboration;
(b) unforged draws for whole-record recovery (the capacity cost). Output: results/v3dev/integrity3_<name>.csv (forgery draws) and
integrity3_<name>_rec.csv (recovery draws). No verdict is written here; src/p3v3/integrity3_eval.py applies the rules.
Run from Paper3/: python -I src/p3v3/integrity3.py <name> <every n-th day> <draws> [sites...]"""
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import frame3 as f3  # noqa: E402
from p3 import record  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

SEED = 20261112
P_LOSS = 0.3
TAG = "dev"
FOLDER = "data/clean/usgs"
DESIGNS = {"D0": (2, False), "D1": (2, True), "D2": (3, False), "D3": (3, True)}
NAMES = {"DO": ("DOmin",), "pH": ("pHmin", "pHmax"), "T": ("Tmax",), "EC": ("ECa", "ECb")}


def witness_dict(it):
    wt = it["wit"]
    out = {"DOmin": wt["DOmin"][2], "pHmin": wt["pHmin"][2], "pHmax": wt["pHmax"][2], "Tmax": it["tw"][1]}
    if it["ew"] is not None:
        out["ECa"], out["ECb"] = it["ew"][1], it["ew"][3]
    return out


def split(it):
    W = witness_dict(it)
    lay, host = {}, {}
    for o, ns in NAMES.items():
        if o == "EC" and it["ew"] is None:
            continue
        for n in ns:
            (lay if it["hard"][o] else host)[n] = W[n]
    return lay, host


def build(it, Q, variant):
    vals, bound = it["vals"], it["bound"]
    if variant == "record":
        return f3.build_block(vals, bound, it["d"], Q), {}, {}
    lay, host = split(it)
    kw = 2 if len(lay) > 1 else 1
    for h in (host, {}):
        try:
            return f3.build_block(vals, bound, it["d"], Q, layered=lay or None, kw=kw, hosted=h or None), lay, (h if h else {})
        except (ValueError, AssertionError):
            continue
    raise ValueError("cannot build")


def forge(raw, rng):
    b = bytearray(raw)
    lo = 3 + f3.CRCB
    for pos in rng.choice(np.arange(lo, len(b)), size=int(rng.integers(1, 4)), replace=False):
        b[int(pos)] ^= int(rng.integers(1, 256))
    crc = f3.msg_crc(bytes(b[:3]) + bytes(b[lo:]))
    b[3:lo] = crc.to_bytes(f3.CRCB, "big")
    return bytes(b)


def false_certified(it, dec):
    rd = it["rd"]
    if any(p not in rd.n_of or sl >= rd.n_of[p] for p, sl, _ in dec.values.values()):
        return 1
    cert, _ = record.certify(dec.values, rd.n_of, dec.bound, dec.last_pos)
    err = record.errors(rd.channels, dec.values)
    bad = 0
    for p, c in cert.items():
        e = np.nan_to_num(err[p], nan=np.inf)
        bad += int((c & (e > 1 + 1e-9)).sum())
    return bad


def run_site(path, every, draws, rng):
    site, items, _ = prepare_items(path, TAG)
    frows, rrows = [], []
    for it in items[::every]:
        truth = {**witness_dict(it)}
        n = len(it["vals"])
        for dname, (crcb, rc) in DESIGNS.items():
            f3.CRCB, f3.RECCRC = crcb, rc
            for variant in ("record", "3b"):
                for Q in (6, 12):
                    try:
                        blk, lay, host = build(it, Q, variant)
                    except ValueError:
                        continue
                    need = max(blk.K if blk.coded else 1, blk.kw)
                    for _ in range(draws):                                   # unforged: recovery
                        keep = [i for i in range(Q) if rng.random() >= P_LOSS]
                        d = f3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else f3.Decoded()
                        ok = (not d.record_rejected) and len(d.values) == n and all(d.values.get(i) == it["vals"][i] for i in range(n))
                        rrows.append((site, it["d"], dname, variant, Q, int(bool(it["bound"]) and ok), blk.K, int(blk.coded)))
                    for _ in range(draws):                                   # forged: one arrived message
                        arrive = [i for i in range(Q) if rng.random() >= P_LOSS]
                        if not arrive:
                            continue
                        j = int(rng.choice(arrive))
                        msgs = [blk.messages[i] if i != j else forge(blk.messages[i], rng) for i in arrive]
                        d = f3.receive(msgs, n_of=it["rd"].n_of)
                        bad = false_certified(it, d)
                        wbad = sum(1 for k, c in d.witness.items() if truth.get(k) is not None and c != truth[k])
                        N = len(arrive)
                        cls = "uncoded" if not blk.coded else ("N=K" if N == need else ("N<K" if N < need else "N>K"))
                        frows.append((site, it["d"], dname, variant, Q, N, need, cls, int(bool(bad or wbad)), int(bool(d.record_rejected or d.witness_rejected))))
    f3.CRCB, f3.RECCRC = 2, False
    return frows, rrows


def main():
    name, every, draws = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    only = set(sys.argv[4:])
    os.makedirs("results/v3dev", exist_ok=True)
    rng = np.random.default_rng(SEED)
    F, R = [], []
    for path in sorted(glob.glob(os.path.join(FOLDER, "*.csv"))):
        site = os.path.basename(path)[:-4]
        if only and site not in only:
            continue
        f, r = run_site(path, every, draws, rng)
        F += f
        R += r
        print(site, len(f), flush=True)
    pd.DataFrame(F, columns=["site", "day", "design", "variant", "Q", "arrived", "need", "cls", "day_false", "rejected"]).to_csv(
        f"results/v3dev/integrity3_{name}.csv", index=False)
    pd.DataFrame(R, columns=["site", "day", "design", "variant", "Q", "full", "K", "coded"]).to_csv(
        f"results/v3dev/integrity3_{name}_rec.csv", index=False)


if __name__ == "__main__":
    main()
