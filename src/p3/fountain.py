"""Systematic random linear (fountain-style) code over GF(2^8) (revision Step 6; review M14).

K data units are sent first; every further message carries a random GF(2^8) combination of the K units. The
coefficients of message i are drawn from a generator seeded with (block day, K, i), so the server regenerates
them from the header and no coefficient bytes are sent. The day is recovered when the received rows have rank K
(rateless: any number of extra messages can be added). Field arithmetic: rs.py.
"""
import numpy as np

from .rs import inv, mul


def coefficients(day, K, i):
    if i < K:
        return [1 if j == i else 0 for j in range(K)]
    return [int(c) for c in np.random.default_rng([int(day), int(K), int(i)]).integers(0, 256, K)]


def encode(data, Q, day):
    """data: K equal-length byte lists -> Q messages (data first, then random combinations)."""
    K, L = len(data), len(data[0])
    out = [list(d) for d in data]
    for i in range(K, Q):
        row = coefficients(day, K, i)
        msg = [0] * L
        for j, c in enumerate(row):
            if c:
                for t in range(L):
                    msg[t] ^= mul(c, data[j][t])
        out.append(msg)
    return out


def decode(received, K, day):
    """received: {index: bytes}. Returns the K data units, or None if the received rows have rank < K."""
    rows = [coefficients(day, K, i) + list(m) for i, m in sorted(received.items())]
    n = len(rows)
    r = 0
    for c in range(K):
        piv = next((k for k in range(r, n) if rows[k][c]), None)
        if piv is None:
            return None
        rows[r], rows[piv] = rows[piv], rows[r]
        ic = inv(rows[r][c])
        rows[r] = [mul(ic, v) for v in rows[r]]
        for k in range(n):
            if k != r and rows[k][c]:
                f = rows[k][c]
                rows[k] = [v ^ mul(f, w) for v, w in zip(rows[k], rows[r])]
        r += 1
    return [rows[j][K:] for j in range(K)]
