"""Exact probability that a record day is fully delivered (revision Step 5; review maths audit, M8).

A loss channel is a Markov chain over hidden states: an initial distribution, a per-state arrival probability,
and a transition matrix applied after each message. Independent loss is one state with arrival 1 - p. The
Gilbert channel (channel.gilbert) has a good state (always arrives) and a bad state (never), starts in its
stationary distribution, and leaves the bad state with probability 1 / burst.

  p_mds(K, D, Q, ch)        systematic MDS block: full iff >= K of Q arrive, or all D value units (the
                            first D transmissions) arrive
  p_units(order, ch)        uncoded: full iff every unit in `order` arrives at least once
Both are exact forward recursions. A fully certified day has probability bound x this.
"""
import numpy as np


def iid(p):
    return np.array([1.0]), np.array([1 - p]), np.array([[1.0]])


def gilbert(p, burst=3):
    if p <= 0:
        return iid(0.0)
    b2g = 1.0 / burst
    g2b = p / (burst * (1 - p))
    return np.array([1 - p, p]), np.array([1.0, 0.0]), np.array([[1 - g2b, g2b], [b2g, 1 - b2g]])


def _step(dist, arrive, T, update):
    """dist: {key: vector over hidden states}; update(key, arrived) -> new key."""
    out = {}
    for key, v in dist.items():
        for arrived, w in ((True, v * arrive), (False, v * (1 - arrive))):
            if not w.any():
                continue
            k2 = update(key, arrived)
            out[k2] = out.get(k2, 0) + w @ T
    return out


def p_mds(K, D, Q, ch):
    init, arrive, T = ch
    dist = {(0, True): init.copy()}
    for i in range(Q):
        dist = _step(dist, arrive, T, lambda k, a, i=i: (min(K, k[0] + a), k[1] and (a or i >= D)))
    return float(sum(v.sum() for (n, all_d), v in dist.items() if n >= K or all_d))


def p_units(order, ch, n_units=None):
    """Forward recursion over (subset of units received, hidden state), vectorised over the subsets:
    v[s, h] = probability of having received exactly the units in s and being in hidden state h.
    n_units: the units that must all arrive are 0..n_units-1 (default: those in `order`); a unit that is never
    transmitted makes full delivery impossible."""
    init, arrive, T = ch
    units = sorted(set(order))
    if n_units is not None and set(range(n_units)) - set(units):
        return 0.0
    bit = {u: 1 << j for j, u in enumerate(units)}
    n_sub = 1 << len(units)
    idx = np.arange(n_sub)
    v = np.zeros((n_sub, len(init)))
    v[0] = init
    for u in order:
        b = bit[u]
        got = (v * arrive) @ T
        new = (v * (1 - arrive)) @ T
        has = (idx & b) != 0
        new[has] += got[has]                 # unit already received: subset unchanged
        new[idx[~has] | b] += got[~has]      # first copy of this unit: subset gains it
        v = new
    return float(v[n_sub - 1].sum())


def p_mask(mask, ch):
    """Probability of one exact arrival mask (for brute-force checks)."""
    init, arrive, T = ch
    v = init.copy()
    for a in mask:
        v = (v * (arrive if a else 1 - arrive)) @ T
    return float(v.sum())
