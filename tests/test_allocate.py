"""Tests of the exact allocation solver (src/p3/allocate.py)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import allocate as al  # noqa: E402

OBJS = [al.Obj("DO", 1, 1.0, 1.0), al.Obj("pH", 2, 1.0, 0.0), al.Obj("T", 1, 1.0, 0.0), al.Obj("EC", 2, 1.0, 0.0)]


def test_phi_table_is_monotone_and_bounded():
    phi = al.phi_table(6)
    assert phi[0] == pytest.approx(1.0) and phi[7] == 0.0
    assert (np.diff(phi) <= 1e-12).all() and (phi >= 0).all()
    # independent loss p = 0.3 alone: P(N >= 2) at Q = 6
    assert al.phi_table(6, (0.3,))[2] == pytest.approx(1 - 0.3 ** 6 - 6 * 0.7 * 0.3 ** 5)


def test_set_partitions_counts_are_bell_numbers():
    for n, bell in ((0, 1), (1, 1), (2, 2), (3, 5), (4, 15)):
        assert sum(1 for _ in al.set_partitions(range(n))) == bell


def test_solver_matches_random_search_and_is_feasible():
    rng = np.random.default_rng(1)
    for Q in (6, 12):
        phi = al.phi_table(Q)
        for V in (3, 5, 8, 13, 22):
            for lam in (0.5, 1.0, 2.0):
                objs = [al.Obj(o.name, o.n, 1.0, float(rng.random() < 0.5)) for o in OBJS]
                J, plan = al.solve(V, Q, objs, lam, phi)
                assert al.evaluate(V, Q, objs, plan, lam, phi) == pytest.approx(J)
                for _ in range(400):                          # no random feasible plan beats the optimum
                    cR = int(rng.integers(1, 6))
                    names = [o.name for o in objs]
                    rng.shuffle(names)
                    status, groups, left = {}, [], 5 - cR
                    i = 0
                    while i < len(names):
                        r = rng.random()
                        if r < 0.3:
                            status[names[i]] = "omit"; i += 1
                        elif r < 0.5:
                            status[names[i]] = "spare"; i += 1
                        elif left > 0:
                            m = int(rng.integers(1, len(names) - i + 1))
                            c = int(rng.integers(1, left + 1))
                            groups.append((tuple(names[i:i + m]), c)); left -= c; i += m
                        else:
                            status[names[i]] = "omit"; i += 1
                    val = al.evaluate(V, Q, objs, (cR, status, groups), lam, phi)
                    if val is not None:
                        assert val <= J + 1e-9


def test_limits_of_lambda():
    phi = al.phi_table(6)
    V = 8
    J, plan = al.solve(V, 6, OBJS, 1e6, phi)                  # the record dominates: its recovery probability is the maximum
    kR = -(-V // plan[0])
    assert al.phi_table(6)[kR] == pytest.approx(phi[-(-V // 5)])
    hard = [al.Obj("DO", 1, 1.0, 0.0), al.Obj("pH", 2, 1.0, 0.0)]
    low = al.solve(8, 6, hard, 0.0, phi)[1]                   # decisions only, record worthless: everything layered
    assert sum(len(n) for n, _ in low[2]) == 2


def test_spare_versus_layer_follow_the_numbers():
    phi = al.phi_table(6)
    objs = [al.Obj("DO", 1, 1.0, 0.0)]
    for V in (7, 9, 10):
        cands = {}
        for cR in range(1, 6):
            for st in ("omit", "spare"):
                v = al.evaluate(V, 6, objs, (cR, {"DO": st}, []), 1.0, phi)
                if v is not None:
                    cands[(cR, st)] = v
            for c in range(1, 6 - cR):
                v = al.evaluate(V, 6, objs, (cR, {}, [(("DO",), c)]), 1.0, phi)
                if v is not None:
                    cands[(cR, "layer", c)] = v
        assert al.solve(V, 6, objs, 1.0, phi)[0] == pytest.approx(max(cands.values()))
    # V = 9: the single spare slot beats a column that would raise the record's k from 2 to 3
    assert al.solve(9, 6, objs, 1.0, phi)[1][1].get("DO") == "spare"
    # V = 7: a column costs the record nothing (k stays 2), so layering with k = 1 beats the spare slot
    assert al.solve(7, 6, objs, 1.0, phi)[1][2] == [(("DO",), 1)]


def test_objective_equals_exact_enumeration_over_the_arrival_count():
    """For one loss probability, J must equal the sum over N of P(N) times the per-N value of the plan."""
    from math import comb
    Q, p = 6, 0.3
    phi = al.phi_table(Q, (p,))
    rng = np.random.default_rng(3)
    for _ in range(40):
        V = int(rng.integers(2, 20))
        objs = [al.Obj(o.name, o.n, 1.0, float(rng.random() < 0.5)) for o in OBJS]
        lam = float(rng.choice([0.5, 1.0, 2.0]))
        J, plan = al.solve(V, Q, objs, lam, phi)
        cR, status, groups = plan
        kR = -(-V // cR)
        byname = {o.name: o for o in objs}
        exact = 0.0
        for N in range(Q + 1):
            pmf = comb(Q, N) * (1 - p) ** N * p ** (Q - N)
            rec = N >= kR
            val = lam * rec
            for n, st in status.items():
                o = byname[n]
                val += o.u * (rec * (1.0 if st == "spare" else o.d))
            for names, c in groups:
                k = -(-sum(byname[n].n for n in names) // c)
                for n in names:
                    o = byname[n]
                    got = N >= k
                    val += o.u * (1.0 if got else (o.d if rec else 0.0))
            exact += pmf * val
        assert J == pytest.approx(exact)


def test_easy_witness_is_not_worth_a_column():
    phi = al.phi_table(6)
    objs = [al.Obj("DO", 1, 1.0, 1.0)]                        # the record alone always decides it
    _, plan = al.solve(10, 6, objs, 1.0, phi)
    assert plan[2] == []                                      # no column is spent on it
    hard = [al.Obj("DO", 1, 1.0, 0.0)]
    _, planh = al.solve(10, 6, hard, 1.0, phi)
    assert [n for n, _ in planh[2]] == [("DO",)]              # a hard query gets a protected column
