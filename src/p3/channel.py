"""One-way message-loss channels (the node never learns which messages arrived).

iid(p):              each message lost independently with probability p.
gilbert(p, burst):   two-state Gilbert channel; every message in the bad state is lost, none in the
                     good state. Mean burst length `burst` messages, stationary loss share p:
                     P(bad -> good) = 1 / burst, P(good -> bad) = p / (burst (1 - p)).
Each returns a boolean arrival mask for a sequence of transmissions.
"""
import numpy as np


def iid(n, p, rng):
    return rng.random(n) >= p


def gilbert(n, p, burst, rng):
    if p <= 0:
        return np.ones(n, bool)
    b2g = 1.0 / burst
    g2b = p / (burst * (1 - p))
    bad = rng.random() < p  # start in the stationary distribution
    out = np.empty(n, bool)
    for i in range(n):
        out[i] = not bad
        bad = (rng.random() >= b2g) if bad else (rng.random() < g2b)
    return out
