"""Exact joint allocation of decision witnesses over the slot columns of one day (revision 2, Step 3c).
Problem statement and criteria: docs/REVISION2_PLAN.md ("Step 3c").

A message has `cols` = 5 value slots (columns). A group of n values over c columns is a systematic MDS code of dimension
k = ceil(n / c): it is recovered whenever at least k of the Q messages arrive. The record (V values) is one group over
c_R columns; its padding (c_R k_R - V slots, the spare slots) can host witnesses at no extra cost, and those are then
recovered exactly when the record is. Every witness object is omitted, spare, or layered (in a group of its own columns).
Objective, per day (maximised):
    J = lam Phi(k_R) + sum over objects of
          omit   u d Phi(k_R)                                   (the record alone decides with probability d)
          spare  u Phi(k_R)                                     (the witness decides whenever it arrives, with the record)
          layer  u [ Phi(k_g) + d max(0, Phi(k_R) - Phi(k_g)) ]  (witness group recovered; else, if k_R <= N < k_g, the record decides)
where Phi(k) = P(N >= k), N the number of the Q messages that arrive (all groups are codes over the same messages, so
every recovery event is a threshold on the same N and Phi is nonincreasing), u the weight of the query and d in [0, 1] the probability that the full
record alone gives a certain correct decision for it (known to the encoder). Phi(k) = 0 when k > Q.
solve() enumerates c_R, the options of every object, the set partitions of the layered objects and their column splits;
the family is finite, so the result is the exact optimum of this objective (tests/test_allocate.py).
"""
import itertools
from dataclasses import dataclass
from math import ceil, comb

import numpy as np

COLS = 5
PRIOR_P = (0.1, 0.2, 0.3, 0.4, 0.5)        # channel-blind prior over the independent loss probability


def phi_table(Q, ps=PRIOR_P):
    """phi[k] = mean over p of P(Binomial(Q, 1 - p) >= k), for k = 0..Q + 1 (phi[Q + 1] = 0)."""
    out = np.zeros(Q + 2)
    for p in ps:
        q = 1.0 - p
        pmf = np.array([comb(Q, j) * q ** j * p ** (Q - j) for j in range(Q + 1)])
        tail = np.cumsum(pmf[::-1])[::-1]
        out[:Q + 1] += tail
    return out / len(ps)


@dataclass(frozen=True)
class Obj:
    name: str
    n: int            # values it occupies (they travel together)
    u: float = 1.0    # query weight
    d: float = 0.0    # probability that the full record alone decides it correctly


def set_partitions(items):
    items = list(items)
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in set_partitions(rest):
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]
        yield [[first]] + part


def column_splits(g, total):
    """All vectors of g positive integers with sum at most `total`."""
    if g == 0:
        yield ()
        return
    for head in range(1, total - (g - 1) + 1):
        for tail in column_splits(g - 1, total - head):
            yield (head,) + tail


def _phi(phi, k, Q):
    return float(phi[k]) if 0 <= k <= Q else 0.0


def evaluate(V, Q, objs, plan, lam, phi, cols=COLS):
    """J of an explicit plan = (c_R, {name: 'omit' | 'spare'}, [(names, c), ...]); None if infeasible."""
    cR, status, groups = plan
    if cR < 1 or cR + sum(c for _, c in groups) > cols:
        return None
    kR = ceil(V / cR) if V > 0 else 0
    PhiR = _phi(phi, kR, Q)
    spare = cR * kR - V
    byname = {o.name: o for o in objs}
    used = sum(byname[n].n for n, s in status.items() if s == "spare")
    if used > spare:
        return None
    layered = [n for names, _ in groups for n in names]
    if sorted(layered + list(status)) != sorted(byname):
        return None
    J = lam * PhiR
    for n, s in status.items():
        o = byname[n]
        J += o.u * PhiR * (1.0 if s == "spare" else o.d)
    for names, c in groups:
        k = ceil(sum(byname[n].n for n in names) / c)
        Pg = _phi(phi, k, Q)
        for n in names:
            o = byname[n]
            J += o.u * (Pg + o.d * max(0.0, PhiR - Pg))
    return J


def solve(V, Q, objs, lam, phi=None, cols=COLS):
    """Exact optimum of J. Returns (J, plan) with plan = (c_R, {name: status}, [(names, c)])."""
    phi = phi_table(Q) if phi is None else phi
    objs = list(objs)
    best = (-np.inf, None)
    for cR in range(1, cols + 1):
        kR = ceil(V / cR) if V > 0 else 0
        PhiR = _phi(phi, kR, Q)
        spare = cR * kR - V
        free = cols - cR
        for assign in itertools.product(("omit", "spare", "layer"), repeat=len(objs)):
            if sum(o.n for o, a in zip(objs, assign) if a == "spare") > spare:
                continue
            L = [o for o, a in zip(objs, assign) if a == "layer"]
            if L and free < 1:
                continue
            base = lam * PhiR
            for o, a in zip(objs, assign):
                if a == "omit":
                    base += o.u * PhiR * o.d
                elif a == "spare":
                    base += o.u * PhiR
            status = {o.name: a for o, a in zip(objs, assign) if a != "layer"}
            if not L:
                if base > best[0] + 1e-12:
                    best = (base, (cR, status, []))
                continue
            for part in set_partitions([o.name for o in L]):
                if len(part) > free:
                    continue
                for split in column_splits(len(part), free):
                    J = base
                    for names, c in zip(part, split):
                        k = ceil(sum(o.n for o in L if o.name in names) / c)
                        Pg = _phi(phi, k, Q)
                        for o in L:
                            if o.name in names:
                                J += o.u * (Pg + o.d * max(0.0, PhiR - Pg))
                    if J > best[0] + 1e-12:
                        best = (J, (cR, status, [(tuple(p), c) for p, c in zip(part, split)]))
    return best
