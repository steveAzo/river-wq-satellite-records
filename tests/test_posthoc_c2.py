"""Post-confirmation regression for the C2 failure (docs/POSTHOC_C2.md). Run from Paper3/: python -m pytest tests -q

With K = 1, a Reed-Solomon parity message is a fixed GF(2^8) multiple of the data unit, so a corrupted parity
payload can be forged that decodes to a different unit with a valid CRC. In the confirmation, such a message was
accepted on the fourth decoding attempt; here the first attempt uses a corrupted parity message (rejected by its CRC)
and the forged one is the retry."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import delivery, frame, rs  # noqa: E402
from p3.frame import Header, Segment  # noqa: E402

DAY, Q = 9000, 5


def unit(values):
    return list(frame.encode_unit([Segment(0, 0, values, True, True)], Header(DAY, 0, 1), 0))


TRUE = unit([("DO", 10, 2000), ("DO", 50, 1800), ("DO", 90, 1900)])
FAKE = unit([("DO", 10, 2000), ("DO", 50, 900), ("DO", 90, 1900)])       # one value wrong, CRC valid
TRUE_VALUES = [("DO", 10, 2000), ("DO", 50, 1800), ("DO", 90, 1900)]


def msgs(intact_spare=True):
    rows = rs.encode([TRUE], Q)
    rows[1] = [b ^ 0x5A for b in rows[1]]                                 # first attempt: corrupted, fails CRC
    coef = rs.cauchy(Q - 1, 1)[1][0]
    rows[2] = [rs.mul(coef, b) for b in FAKE]                              # retry: forged, decodes to FAKE
    if not intact_spare:
        rows[3] = [b ^ 0x33 for b in rows[3]]
        rows[4] = [b ^ 0x0F for b in rows[4]]
    return [frame.message(Header(DAY, i, 1), r) for i, r in enumerate(rows) if i != 0]   # data message lost


def received_values(m):
    rx, _, _, _ = delivery.receive(m, DAY)
    return [rx[i] for i in sorted(rx)]


def test_frozen_receiver_accepts_the_forgery_on_a_retry():
    delivery.CORROBORATE = False
    try:
        assert received_values(msgs()) == [("DO", 10, 2000), ("DO", 50, 900), ("DO", 90, 1900)]
    finally:
        delivery.CORROBORATE = True


def test_corroboration_rejects_the_forgery_and_keeps_the_true_unit():
    assert received_values(msgs()) == TRUE_VALUES


def test_without_an_intact_spare_a_retried_decoding_is_not_accepted():
    assert received_values(msgs(intact_spare=False)) == []


def test_a_first_attempt_is_accepted_without_corroboration():
    rows = rs.encode([TRUE], Q)
    m = [frame.message(Header(DAY, i, 1), r) for i, r in enumerate(rows) if i in (3,)]    # one parity, no spare
    assert received_values(m) == TRUE_VALUES
