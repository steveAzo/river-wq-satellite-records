"""Delivery designs for a one-way, quota-limited link (study plan, Section 5).

A design turns one site-day into a Plan: the data messages (each a list of (parameter, slot) values,
at most V per message), the transmission sequence (at most Q transmissions per day), and the decoding
rule. Messages are 23 B by default: 1 B header (day index, sequence) + V = 7 values x 3 B.

  raw_periodic : every k-th reading of every parameter, newest slot included; no guarantee.
  srdl_style   : satellite-tag practice: per parameter a fixed number of top-down broken-stick points
                 (absolute deviation), packed into D data messages; the Q transmissions pick data
                 messages pseudo-randomly with replacement (single-day model of SRDL buffer rotation).
  reliable_opt : min-# at the smallest common tau fitting V*Q values; every message once.
  repeat_r     : min-# at the smallest tau fitting V*floor(Q/r) values; copies sent round-robin.
  mds_K        : min-# at the smallest tau fitting V*K values in K data messages + (Q - K) Reed-Solomon
                 parity messages; any K arrivals decode everything (rs.py), else the arrived data messages.
Designs with a tau carry a guarantee (`tau`), which the server uses for certification.
"""
from dataclasses import dataclass, field

import numpy as np

V_DEFAULT = 7


@dataclass
class Plan:
    name: str
    planned: list                  # [(p, slot)] in planned order
    data: list                     # data messages: list of lists of (p, slot)
    tx: list                       # transmission sequence: data-message index, or ("parity", j)
    tau: float = None              # guarantee level of the planned set (None: no guarantee)
    K: int = None                  # MDS dimension (None: not coded)
    meta: dict = field(default_factory=dict)

    def delivered(self, arrived_mask):
        got = [t for t, ok in zip(self.tx, arrived_mask) if ok]
        if self.K is not None:
            if len(set(got)) >= self.K:
                return set(self.planned)
            idx = {t for t in got if not isinstance(t, tuple)}
        else:
            idx = set(got)
        return {v for i in idx for v in self.data[i]}


def chunk(values, V):
    return [values[i:i + V] for i in range(0, len(values), V)] or [[]]


def raw_periodic(sd, Q, V=V_DEFAULT):
    cap = V * Q
    for k in range(1, sd.n + 1):
        slots = list(range(sd.n - 1, -1, -k))[::-1]
        if sd.P * len(slots) <= cap:
            break
    vals = [(p, s) for p in range(sd.P) for s in slots]
    data = chunk(vals, V)
    return Plan("raw_periodic", vals, data, list(range(len(data))), meta={"stride": k})


def srdl_style(enc, Q, data_share=0.5, rng=None, V=V_DEFAULT):
    sd = enc.sd
    D = max(1, int(round(data_share * Q)))
    m = max(1, (V * D) // sd.P)
    vals = enc.topdown(m)
    data = chunk(vals, V)[:D]
    vals = [v for msg in data for v in msg]
    rng = rng or np.random.default_rng(0)
    tx = list(rng.integers(0, len(data), Q))
    return Plan("srdl_style", vals, data, tx, meta={"points_per_param": m, "D": len(data)})


def reliable_opt(enc, Q, V=V_DEFAULT):
    tau, vals = enc.fit(V * Q)
    data = chunk(vals, V)
    return Plan("reliable_opt", vals, data, list(range(len(data))), tau=tau)


def repeat_r(enc, Q, r, V=V_DEFAULT):
    m = max(1, Q // r)
    tau, vals = enc.fit(V * m)
    data = chunk(vals, V)
    tx = [i for _ in range(r) for i in range(len(data))][:Q]
    return Plan(f"repeat_{r}", vals, data, tx, tau=tau, meta={"r": r})


def mds_K(enc, Q, K, V=V_DEFAULT):
    tau, vals = enc.fit(V * K)
    data = chunk(vals, V)
    data += [[] for _ in range(K - len(data))]  # pad to K data messages (empty values)
    tx = list(range(K)) + [("parity", j) for j in range(Q - K)]
    return Plan(f"mds_{K}", vals, data, tx, tau=tau, K=K)
