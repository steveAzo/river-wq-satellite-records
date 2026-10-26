"""Step 6 baselines: fountain code, interleaving, tag policy with record content (src/p3/fountain.py, delivery.py).
Run from Paper3/: python -m pytest tests -q"""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from p3 import analytic, delivery, fountain, frame, record  # noqa: E402
from golden_day import synthetic_day  # noqa: E402

SLACK = 1 + 1e-9


def test_fountain_round_trip_and_rank_deficiency():
    rng = np.random.default_rng(0)
    data = [list(rng.integers(0, 256, 20)) for _ in range(4)]
    msgs = fountain.encode(data, 10, day=9000)
    assert msgs[:4] == data                                            # systematic
    assert fountain.decode({i: msgs[i] for i in (4, 5, 6, 7, 8)}, 4, 9000) == data
    assert fountain.decode({i: msgs[i] for i in (0, 1, 2)}, 4, 9000) is None   # too few rows
    dup = {0: msgs[0], 1: msgs[1], 2: msgs[2]}
    dup[5] = msgs[0]                                                   # a row equal to row 0 has rank 3 with it
    assert fountain.decode({0: msgs[0], 1: msgs[1], 2: msgs[2], 3: msgs[3]}, 4, 9000) == data


def test_fountain_coefficients_are_regenerated_from_the_header():
    assert fountain.coefficients(9000, 4, 7) == fountain.coefficients(9000, 4, 7)
    assert fountain.coefficients(9000, 4, 7) != fountain.coefficients(9001, 4, 7)
    assert fountain.coefficients(9000, 4, 2) == [0, 0, 1, 0]


def test_fountain_header_flag_round_trips():
    h = frame.Header(9000, 5, 3, True, fountain=True)
    assert frame.parse_header(h.to_bytes(), 9000).fountain
    assert not frame.parse_header(frame.Header(9000, 5, 3).to_bytes(), 9000).fountain


def test_rlnc_never_beats_mds_and_its_certificates_are_sound():
    """Proposition 2 on bytes: for every arrival mask, fountain success implies MDS success."""
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    Q = 8
    m, f = delivery.mds_rec(rd, enc, Q), delivery.rlnc_rec(rd, enc, Q)
    assert m.planned == f.planned and f.bound
    day = delivery.day_number(rd.day)
    deficient = 0
    for mask in itertools.product([False, True], repeat=Q):
        mask = np.array(mask)
        om, of = delivery.outcome(rd, m, mask), delivery.outcome(rd, f, mask)
        assert of["Phi"] <= om["Phi"]
        deficient += om["Phi"] and not of["Phi"]
        rx, last, bound, _ = delivery.receive([x for x, ok in zip(f.msgs, mask) if ok], day)
        cert, _ = record.certify(rx, rd.n_of, bound, last)
        err = record.errors(rd.channels, rx)
        assert all((err[p][cert[p]] <= SLACK).all() for p in cert)
    assert deficient < 2 ** Q * 0.05                                   # rank deficiency is rare over GF(256)


def test_block_order_and_interleaving_under_bursts():
    assert delivery.block_order(3, 7) == [0, 0, 0, 1, 1, 2, 2]
    ch = analytic.gilbert(0.3, 3)
    assert analytic.p_units(delivery.cyclic(3, 6), ch) > analytic.p_units(delivery.block_order(3, 6), ch)
    i = analytic.iid(0.3)
    assert abs(analytic.p_units(delivery.cyclic(3, 6), i) - analytic.p_units(delivery.block_order(3, 6), i)) < 1e-12


def test_tag_policy_with_record_content_is_never_better_than_cyclic_repetition_under_iid():
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    for seed in range(5):
        t, r = delivery.tag_rec(rd, enc, 6, seed=seed), delivery.rep_rec(rd, enc, 6)
        assert t.planned == r.planned
        i = analytic.iid(0.3)
        assert analytic.p_units(t.idx, i, t.meta["units"]) <= analytic.p_units(r.idx, i, r.meta["units"]) + 1e-12


def test_exact_path_equals_byte_enumeration_for_every_design():
    """For each design, sum over all 2^Q masks of P(mask) x Phi(bytes) equals the exact path used in Step 5
    (run_robust.p_full). Covers tag orders that skip a unit (the Step 6 regression)."""
    from p3 import run_robust as rr
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    Q = 6
    designs = [delivery.mds_rec(rd, enc, Q), delivery.rep_rec(rd, enc, Q), delivery.rep_block_rec(rd, enc, Q),
               delivery.reliable(rd, enc, Q), delivery.every_k(rd, Q), delivery.repeat(rd, enc, Q, 2),
               delivery.mds(rd, enc, Q, 4)]
    designs += [delivery.tag_rec(rd, enc, Q, seed=s) for s in range(4)]
    designs += [delivery.tag(rd, Q, sh, seed=s) for sh in (0.5, 1.0) for s in range(3)]
    rng = np.random.default_rng(0)
    for c in [("iid", 0.3, 0), ("gilbert", 0.3, 3)]:
        ch = rr.ch_model(c)
        for s in designs:
            by_bytes = sum(analytic.p_mask(m, ch) * delivery.outcome(rd, s, np.array(m))["Phi"]
                           for m in itertools.product([False, True], repeat=len(s.msgs)))
            exact = s.bound * rr.p_full(s, c, rng)[0] if s.bound else 0.0
            assert abs(by_bytes - exact) < 1e-12, (s.name, s.idx)
