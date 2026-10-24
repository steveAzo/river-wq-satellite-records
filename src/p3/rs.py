"""Systematic erasure code across messages (Reed-Solomon / MDS over GF(2^8)).

K data messages of L bytes are extended with Q - K parity messages; ANY K of the Q messages recover
all K data messages. Parity rows come from a Cauchy matrix, so every K x K submatrix of the generator
[I; C] is invertible (the MDS property). Field: GF(256) with polynomial x^8+x^4+x^3+x^2+1 (0x11d).
Pure Python; small enough for a microcontroller port (Q <= 96, L = 22).
"""
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def mul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def inv(a):
    if a == 0:
        raise ZeroDivisionError
    return EXP[255 - LOG[a]]


def cauchy(rows, K):
    """rows x K Cauchy matrix with x_i = K + i, y_j = j (all distinct, x_i ^ y_j != 0)."""
    return [[inv((K + i) ^ j) for j in range(K)] for i in range(rows)]


def encode(data, Q):
    """data: list of K equal-length byte lists. Returns Q messages (data first, then parity)."""
    K, L = len(data), len(data[0])
    C = cauchy(Q - K, K)
    parity = []
    for row in C:
        out = [0] * L
        for j, coef in enumerate(row):
            if coef:
                for t in range(L):
                    out[t] ^= mul(coef, data[j][t])
        parity.append(out)
    return [list(d) for d in data] + parity


def _invert(M):
    n = len(M)
    A = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(M)]
    for c in range(n):
        piv = next(r for r in range(c, n) if A[r][c])
        A[c], A[piv] = A[piv], A[c]
        ic = inv(A[c][c])
        A[c] = [mul(ic, v) for v in A[c]]
        for r in range(n):
            if r != c and A[r][c]:
                f = A[r][c]
                A[r] = [v ^ mul(f, w) for v, w in zip(A[r], A[c])]
    return [row[n:] for row in A]


def decode(received, K, Q):
    """received: dict {message index: bytes}; needs >= K entries. Returns the K data messages."""
    if len(received) < K:
        raise ValueError("fewer than K messages")
    C = cauchy(Q - K, K)
    idx = sorted(received)[:K]
    G = [[1 if i == j else 0 for j in range(K)] if i < K else C[i - K] for i in idx]
    Ginv = _invert(G)
    L = len(received[idx[0]])
    return [[_dot(Ginv[r], [received[i][t] for i in idx]) for t in range(L)] for r in range(K)]


def _dot(row, col):
    out = 0
    for a, b in zip(row, col):
        out ^= mul(a, b)
    return out
