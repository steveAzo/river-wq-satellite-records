"""Tests added after the mutation check (results/mutation_check.md) found faults that no test caught (M04, M12, M13, M14, M17,
M18). Each test fails on the planted fault it was written for (tools/mutation_check.py runs this file first)."""
import os
import sys
from math import comb

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import allocate as al  # noqa: E402
from p3 import capacity as cp  # noqa: E402
from p3 import certlang as cl  # noqa: E402
from p3 import frame, sod  # noqa: E402
from p3 import frame2 as f2  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.record import Channel  # noqa: E402


# ---- M04: the conductance 'no' rule must not accept a possible change above the fraction --------------------------
@pytest.mark.parametrize("hi1", [115.0, 125.0])
def test_conductance_no_rule_rejects_a_possible_upward_change_above_the_fraction(hi1):
    """Two readings, so that only the pair (0, 1) decides: x1 may be up to 15% or 25% above x0, so 'no change above 10%' is
    not certain. (With three readings the second pair would trip the lower-side test and hide a lax upper-side rule.)"""
    K = cl.Knowledge("EC", 2)
    K.lo = np.array([100.0, 100.0])
    K.hi = np.array([100.0, hi1])
    assert cl.relative_change(K, 1, 0.10) != 0
    K.hi = np.array([100.0, 109.0])
    assert cl.relative_change(K, 1, 0.10) != 1                  # a possible change, never a certain one


def test_conductance_no_rule_rejects_a_possible_downward_change_above_the_fraction():
    K = cl.Knowledge("EC", 2)
    K.lo = np.array([100.0, 80.0])
    K.hi = np.array([100.0, 100.0])
    assert cl.relative_change(K, 1, 0.10) != 0
    K.lo = np.array([100.0, 99.0])
    K.hi = np.array([100.0, 101.0])
    assert cl.relative_change(K, 1, 0.10) == 0                  # and a tight box does give a certain 'no'


# ---- M12 and M13: the receiver's sanity rules ---------------------------------------------------------------------
N_OF = {"T": 96, "DO": 96, "pH": 96, "EC": 96}


def test_sanity_rule_rejects_a_slot_outside_the_site_profile():
    blk = f2.build_block([("T", 500, 2000)], True, 5, 6)
    assert f2.receive(blk.messages).values == {0: ("T", 500, 2000)}                  # without the profile it is accepted
    d = f2.receive(blk.messages, n_of=N_OF)
    assert d.record_rejected and d.values == {}


def test_sanity_rule_rejects_values_out_of_planned_order_and_keeps_valid_ones():
    bad = f2.build_block([("T", 10, 2000), ("T", 5, 2000)], True, 5, 6)
    assert f2.receive(bad.messages, n_of=N_OF).record_rejected
    good = f2.build_block([("T", 5, 2000), ("T", 10, 2000), ("DO", 3, 1700)], True, 5, 6)
    d = f2.receive(good.messages, n_of=N_OF)
    assert not d.record_rejected and len(d.values) == 3


@pytest.mark.parametrize("code", [0, 8191])
def test_witness_codes_that_flag_a_censored_reading_are_rejected(code):
    blk = f2.build_block([("T", 5, 2000)], True, 5, 6, layered={"DOmin": code}, kw=1)
    d = f2.receive(blk.messages, n_of=N_OF)
    assert d.witness == {} and d.witness_rejected
    ok = f2.build_block([("T", 5, 2000)], True, 5, 6, layered={"DOmin": 1700}, kw=1)
    assert f2.receive(ok.messages, n_of=N_OF).witness == {"DOmin": 1700}


# ---- M14: the objective of an explicit plan, including an easy object that is layered ------------------------------
def test_evaluate_matches_exact_enumeration_for_a_layered_object_the_record_already_decides():
    Q, p = 6, 0.3
    phi = al.phi_table(Q, (p,))
    objs = [al.Obj("DO", 1, 1.0, 1.0)]
    V, plan, lam = 10, (4, {}, [(("DO",), 1)]), 1.0                 # record k_R = 3 of 6; the witness group needs 1
    exact = 0.0
    for N in range(Q + 1):
        pmf = comb(Q, N) * (1 - p) ** N * p ** (Q - N)
        rec, got = N >= 3, N >= 1
        exact += pmf * (lam * rec + (1.0 if got else (1.0 if rec else 0.0)))
    assert al.evaluate(V, Q, objs, plan, lam, phi) == pytest.approx(exact)


# ---- M17: a hold never certifies a censored reading ---------------------------------------------------------------
def test_a_hold_does_not_certify_the_censored_reading_that_ends_it():
    x = np.array([8.0, 8.1, 90.0, 8.2, 8.1, 8.0])                    # 90 mg/L is above the DO range: censored
    ch = Channel("DO", x, tolerance("DO", x))
    pl = sod.plan([ch])
    assert any(frame.saturated(code) for _, _, code in pl)
    cert = sod.certify_hold(dict(enumerate(pl)), {"DO": 6}, len(pl) - 1)
    assert not cert["DO"][2] and cert["DO"][[0, 1, 3, 4, 5]].all()


# ---- M18: the bit budget agrees with the codec for every record size, byte-aligned or not -----------------------
def test_values_per_unit_matches_the_bit_budget_for_every_size():
    for bits in range(40, 150):
        assert f2.values_per_unit(bits) == (bits - cp.SEG_OVERHEAD) // cp.VALUE, bits
