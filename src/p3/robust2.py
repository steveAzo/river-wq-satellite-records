"""Revision 2, Step 6b: integrity experiment E5 for frame version 2 (docs/FRAME_SPEC_V2.md).

A corrupted message passes the per-message CRC-16 with probability about 2^-16, so a direct simulation would need millions of
days. Two stages instead:
  Stage 1 (conditional): in real development days, built into byte-level blocks, one arrived message is replaced by a CRC-VALID
    forgery (random bytes changed, CRC recomputed). Receivers: v2 with corroboration and v2 without. Outcomes: readings
    certified outside tolerance, witness codes accepted that differ from the truth, and the share of days in which the forged
    message could be corroborated (more accepted messages than needed).
  Stage 2 (rates): expected CRC-passing corruptions per day for bit-error rates 1e-4, 1e-3, 1e-2 (and 10% of messages hit),
    from the arrival model and 2^-16 per corrupted message (an upper bound for burst errors up to 16 bits, which CRC-16
    always detects), multiplied by the Stage 1 conditional false-certificate probability.
Also checked directly: every single-bit and burst error of up to 16 bits is detected (tests/test_frame2.py).
Run from Paper3/: python -I src/p3/robust2.py <folder> <tag> [sites=4] [draws=10]
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame2 as f2  # noqa: E402
from p3 import record  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

SEED = 20261106
BERS = (1e-4, 1e-3, 1e-2)
CRC_PASS = 2.0 ** -16
RECEIVERS = (("CRC only", False, False, False), ("CRC + sanity", False, True, False),
             ("CRC + corroboration", True, False, False), ("CRC + sanity + corroboration", True, True, False),
             ("CRC + sanity + corroboration + cross-check", True, True, True))
WITNESS_CHECK = {"DOmin": ("DO", "min"), "pHmin": ("pH", "min"), "pHmax": ("pH", "max"), "Tmax": ("T", "max")}


def cross_check(it, d):
    """Drop witnesses that contradict the decoded record (certlang.witness_consistent)."""
    from p3 import certlang as cl
    rd = it["rd"]
    if not d.witness:
        return
    cert, _ = record.certify(d.values, rd.n_of, d.bound, d.last_pos) if d.values else ({p: np.zeros(n, bool) for p, n in rd.n_of.items()}, False)
    for name in list(d.witness):
        if name not in WITNESS_CHECK:                      # a witness the node does not send (forged descriptor)
            del d.witness[name]
            d.witness_rejected = True
            continue
        p, kind = WITNESS_CHECK[name]
        n = rd.n_of[p]
        K0 = cl.knowledge_from_rx(p, n, d.values, cert[p])
        if not cl.witness_consistent(K0, kind, d.witness[name]):
            del d.witness[name]
            d.witness_rejected = True


def forge(raw, rng):
    b = bytearray(raw)
    # distinct body bytes after the CRC (bytes 3 and 4 are rewritten below, so changing them would be a no-op); a header forgery
    # changes identity and is checked separately
    for pos in rng.choice(np.arange(5, len(b)), size=int(rng.integers(1, 4)), replace=False):
        b[int(pos)] ^= int(rng.integers(1, 256))
    crc = f2.crc16(bytes(b[:3]) + bytes(b[5:]))
    b[3], b[4] = crc >> 8, crc & 0xFF
    return bytes(b)


def false_certified(it, dec):
    """(readings certified although their error exceeds the tolerance, readings certified)."""
    rd = it["rd"]
    if any(p not in rd.n_of or sl >= rd.n_of[p] for p, sl, _ in dec.values.values()):
        return 1, 0                                      # a value outside the site profile was accepted: counted as false
    cert, _ = record.certify(dec.values, rd.n_of, dec.bound, dec.last_pos)
    err = record.errors(rd.channels, dec.values)
    bad = tot = 0
    for p, c in cert.items():
        e = np.nan_to_num(err[p], nan=np.inf)
        bad += int((c & (e > 1 + 1e-9)).sum())
        tot += int(c.sum())
    return bad, tot


def witness_codes(it):
    wt = it["wit"]
    return {"DOmin": wt["DOmin"][2], "pHmin": wt["pHmin"][2], "pHmax": wt["pHmax"][2], "Tmax": it["tw"][1]}


def run(folder, tag, nsites, draws, only=None):
    rng = np.random.default_rng(SEED)
    rows = []
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if only is not None:
        paths = [x for x in paths if os.path.basename(x)[:-4] in only]
    for path in paths[:nsites]:
        site, items, res = prepare_items(path, tag)
        for it in items:
            vals, bound = it["vals"], it["bound"]
            truth_w = witness_codes(it)
            for variant, kw in (("record", 0), ("layered k1", 1), ("layered k2", 2)):
                for Q in (6, 12):
                    lay = {n: truth_w[n] for n in truth_w} if kw else None
                    try:
                        blk = f2.build_block(vals, bound, it["d"], Q, layered=lay, kw=kw or 1)
                    except ValueError:
                        continue
                    for r in range(draws):
                        arrive = [i for i in range(Q) if rng.random() >= 0.3]
                        if not arrive:
                            continue
                        j = int(rng.choice(arrive))
                        msgs = [blk.messages[i] if i != j else forge(blk.messages[i], rng) for i in arrive]
                        need = max(blk.K if blk.coded else 1, blk.kw)
                        for rx_name, corr, prof, xchk in RECEIVERS:
                            d = f2.receive(msgs, corroborate=corr, n_of=it["rd"].n_of if prof else None)
                            if xchk:
                                cross_check(it, d)
                            bad, tot = false_certified(it, d)
                            wbad = sum(1 for n, c in d.witness.items() if truth_w.get(n) is not None and c != truth_w[n])
                            rows.append({"site": site, "day": it["d"], "variant": variant, "Q": Q, "receiver": rx_name,
                                         "arrived": len(arrive), "need": need, "forged_index": j,
                                         "false_readings": bad, "certified_readings": tot, "false_witnesses": wbad,
                                         "witnesses_accepted": len(d.witness),
                                         "rejected": bool(d.record_rejected or d.witness_rejected),
                                         "day_false": bool(bad or wbad)})
        print(site, flush=True)
    return pd.DataFrame(rows)


def summary(df):
    out = []
    for (variant, Q, rx), z in df.groupby(["variant", "Q", "receiver"]):
        out.append({"variant": variant, "Q": Q, "receiver": rx, "forged days": len(z),
                    "false day share": z.day_false.mean(), "false readings": int(z.false_readings.sum()),
                    "false witnesses": int(z.false_witnesses.sum()), "rejected share": z.rejected.mean(),
                    "extra messages share": float((z.arrived > z.need).mean())})
    return pd.DataFrame(out)


def rates(df, Q):
    """Stage 2: expected false-certificate events per million days under bit-error rates (independent loss 0.3)."""
    p_arrive = 0.7
    n_bits = 8 * 23
    lines = []
    for ber in BERS + ("10% hit",):
        pc = 0.10 if ber == "10% hit" else 1 - (1 - ber) ** n_bits
        for variant in ("record", "layered k1", "layered k2"):
            for rx_name, _c, _p, _x in RECEIVERS:
                z = df[(df.variant == variant) & (df.Q == Q) & (df.receiver == rx_name)]
                if z.empty:
                    continue
                forge_rate = Q * p_arrive * pc * CRC_PASS            # expected CRC-passing corruptions per day
                lines.append({"corruption": ber, "variant": variant, "Q": Q, "receiver": rx_name,
                              "P(false cert | one forgery)": z.day_false.mean(),
                              "CRC-passing corruptions per day": forge_rate,
                              "false-certificate days per million": 1e6 * forge_rate * z.day_false.mean()})
    return pd.DataFrame(lines)


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    nsites = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    draws = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    df = run(folder, tag, nsites, draws)
    df.to_csv(f"results/{tag}/robust2_stage1.csv", index=False)
    s = summary(df)
    print("\nStage 1 (one CRC-valid forgery per day)\n" + s.to_markdown(index=False, floatfmt=".4f"))
    for Q in (6, 12):
        print(f"\nStage 2 (Q = {Q}, independent loss 0.3)\n" + rates(df, Q).to_markdown(index=False, floatfmt=".3g"))


if __name__ == "__main__":
    main()
