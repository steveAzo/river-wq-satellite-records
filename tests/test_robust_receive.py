"""Hardened receiver (delivery.recover_units; Step 9, review M18). Run from Paper3/: python -m pytest tests -q"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from p3 import delivery, frame, record  # noqa: E402
from golden_day import synthetic_day  # noqa: E402

SLACK = 1 + 1e-9
RD = synthetic_day()
ENC = record.Encoder(RD.channels)
DAY = delivery.day_number(RD.day)


def flip(m, bit):
    b = bytearray(m)
    b[bit // 8] ^= 0x80 >> (bit % 8)
    return bytes(b)


def full(msgs):
    rx, last, bound, _ = delivery.receive(msgs, DAY)
    cert, ok = record.certify(rx, RD.n_of, bound, last)
    return ok


def code(Q=8):
    s = delivery.mds_rec(RD, ENC, Q)
    assert s.meta["K"] < Q - 1
    return s


def test_corrupted_header_k_is_outvoted():
    s = code()
    msgs = list(s.msgs)
    msgs[0] = flip(msgs[0], 21)                    # a bit of the K field of message 0
    assert frame.parse_header(msgs[0], DAY).K != s.meta["K"]
    assert full(msgs)


def test_corrupted_block_day_is_outvoted():
    s = code()
    msgs = list(s.msgs)
    msgs[3] = flip(msgs[3], 5)                     # block day field
    assert frame.parse_header(msgs[3], DAY).block_day != DAY
    _, _, _, _, st = delivery.receive(msgs, DAY, with_stats=True)
    assert st["header_rejects"] == 1 and full(msgs)


def test_corrupted_parity_is_retried_around():
    s = code()
    K = s.meta["K"]
    msgs = [m for i, m in enumerate(s.msgs) if i != 0]          # data unit 0 lost
    j = next(i for i, m in enumerate(msgs) if frame.parse_header(m, DAY).index == K)
    msgs[j] = flip(msgs[j], 8 * 10 + 3)                         # first parity message corrupted
    _, _, _, _, st = delivery.receive(msgs, DAY, with_stats=True)
    assert st["decode_tries"] >= 2 and full(msgs)


def test_corrupted_systematic_unit_is_rebuilt_from_parity():
    s = code()
    msgs = list(s.msgs)
    msgs[1] = flip(msgs[1], 8 * 12)
    _, _, _, fails, _ = delivery.receive(msgs, DAY, with_stats=True)
    assert fails == 1 and full(msgs)


def test_random_corruption_never_produces_a_false_certificate():
    rng = np.random.default_rng(7)
    designs = [code(), delivery.rep_rec(RD, ENC, 8), delivery.every_k(RD, 8), delivery.tag(RD, 8, 0.5, seed=1)]
    false_cert = checked = 0
    for _ in range(400):
        for s in designs:
            msgs = []
            for m in s.msgs:
                if rng.random() < 0.3:
                    continue
                if rng.random() < 0.3:                               # 30% of messages corrupted
                    for b in rng.choice(8 * len(m), size=int(rng.integers(1, 9)), replace=False):
                        m = flip(m, int(b))
                msgs.append(m)
            rx, last, bound, _ = delivery.receive(msgs, DAY)
            cert, _ = record.certify(rx, RD.n_of, bound, last)
            err = record.errors(RD.channels, rx)
            for p in cert:
                checked += int(cert[p].sum())
                false_cert += int((err[p][cert[p]] > SLACK).sum())
    assert checked > 10000 and false_cert == 0
