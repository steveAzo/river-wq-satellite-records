"""Tolerance-normalised piecewise-linear selection (min-# / min-epsilon; Imai & Iri, 1988).

Positions: q = 0 is the anchor (known to the server), q = 1..n are the day's slots 0..n-1.
The server's picture is the straight line between consecutive kept positions, and the last kept value
held to the end of the day. Errors are normalised by the per-value tolerance, so "within tolerance"
means normalised error <= 1 and a set "within tau" keeps every value within tau x tolerance.

seg[a, b] (a < b): worst normalised error of the values strictly between kept positions a and b.
tail[q]:           worst normalised error of the values after q when q is the last kept position.
These O(n^2) tables make min-# an O(n^2) dynamic program; on a node the O(n) Imai-Iri algorithm can be
used instead (same result).
"""
import numpy as np

INF = 10 ** 9


def tables(x, anchor, tol):
    n = len(x)
    xs = np.concatenate(([anchor], x))
    ts = np.concatenate(([np.inf], tol))
    seg = np.zeros((n + 1, n + 1))
    for a in range(n + 1):
        b = np.arange(a + 2, n + 1)
        if len(b) == 0:
            continue
        # for every end b, the worst error over a < t < b; built cumulatively along t
        worst = np.zeros(len(b))
        for t in range(a + 1, n):
            ends = b > t
            if not ends.any():
                break
            line = xs[a] + (xs[b[ends]] - xs[a]) * (t - a) / (b[ends] - a)
            worst[ends] = np.maximum(worst[ends], np.abs(xs[t] - line) / ts[t])
        seg[a, b] = worst
    tail = np.array([np.max(np.abs(xs[q + 1:] - xs[q]) / ts[q + 1:]) if q < n else 0.0 for q in range(n + 1)])
    return seg, tail


def min_set(seg, tail, eps):
    """Fewest kept slots (0-based) keeping every value within eps; ties broken by earliest predecessor."""
    n1 = seg.shape[0]
    f = np.full(n1, INF)
    back = np.full(n1, -1)
    f[0] = 0
    for b in range(1, n1):
        ok = np.flatnonzero(seg[:b, b] <= eps + 1e-12)
        if len(ok):
            a = ok[np.argmin(f[ok])]
            f[b], back[b] = f[a] + 1, a
    ends = [q for q in range(n1) if tail[q] <= eps + 1e-12 and f[q] < INF]
    q = min(ends, key=lambda q: (f[q], q))
    kept = []
    while q > 0:
        kept.append(q - 1)
        q = back[q]
    return kept[::-1]


class Encoder:
    """Per site-day encoder: smallest common tau whose min-# sets fit a value budget."""

    def __init__(self, sd):
        self.sd = sd
        self.tabs = [tables(sd.X[p], sd.anchor[p], sd.tol[p]) for p in range(sd.P)]
        self.cands = np.unique(np.concatenate([np.concatenate((s[np.triu_indices_from(s, 2)], t))
                                               for s, t in self.tabs] + [np.array([0.0])]))
        self._count = {}

    def count(self, i):
        if i not in self._count:
            eps = self.cands[i]
            self._count[i] = sum(len(min_set(s, t, eps)) for s, t in self.tabs)
        return self._count[i]

    def need(self, tau=1.0):
        """Values needed to keep the whole day within tau x tolerance."""
        return sum(len(min_set(s, t, tau)) for s, t in self.tabs)

    def fit(self, k):
        """(tau, values) with the smallest tau whose total min-# fits k values; values = [(p, slot), ...]
        ordered by parameter then time (the planned order the server uses for certification)."""
        lo, hi = 0, len(self.cands) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.count(mid) <= k:
                hi = mid
            else:
                lo = mid + 1
        tau = float(self.cands[lo])
        vals = [(p, s) for p, (sg, tl) in enumerate(self.tabs) for s in min_set(sg, tl, tau)]
        return tau, vals

    def topdown(self, m):
        """Broken-stick style (SRDL practice): per parameter, m points chosen top-down by largest
        ABSOLUTE deviation (not tolerance-normalised), equal count per parameter."""
        out = []
        for p in range(self.sd.P):
            x, a = self.sd.X[p], self.sd.anchor[p]
            kept = []
            for _ in range(m):
                rec = reconstruct_one(x, a, kept)
                err = np.abs(x - rec)
                err[kept] = -1
                i = int(np.argmax(err))
                if err[i] <= 0:
                    break
                kept.append(i)
            out += [(p, s) for s in sorted(kept)]
        return out


def reconstruct_one(x, anchor, kept):
    n = len(x)
    if len(kept) == 0:
        return np.full(n, float(anchor))
    k = np.sort(np.asarray(kept))
    return np.interp(np.arange(n), np.concatenate(([-1], k)), np.concatenate(([anchor], x[k])))
