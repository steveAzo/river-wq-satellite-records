"""Table-free exact encoder for the self-contained record at level eps (revision Step 10; review M12, E8).

Same objective and result as record.Encoder.plan_at (per-reading tolerances, dequantised endpoints, first value
held back to midnight, last value held to the end, censored readings always kept), without the n x n error table:

  - For a fixed start a, the span a -> b keeps every reading t in (a, b) within tolerance exactly when the slope
    (xq[b] - xq[a]) / (b - a) lies in the intersection of the windows
    [(x[t] - D[t] - xq[a]) / (t - a), (x[t] + D[t] - xq[a]) / (t - a)], D = (eps + 1e-12) * tolerance.
    The intersection only shrinks as b grows, so it is updated in O(1) per step and the scan stops when it is empty
    or when it reaches a censored reading (which may not be skipped).
  - Head (hold back) and tail (hold forward) feasibility are prefix / suffix interval tests.
Time O(n^2) in the worst case (much less when windows empty early), memory O(n). `ops` counts window updates.
Ties are broken as in record.min_set (fewest values, then the earliest last value, then the earliest predecessor).
"""
import numpy as np

from . import frame

INF = np.iinfo(np.int64).max // 2


def min_set(ch, eps=1.0, count=None):
    x0, n = ch.x, ch.n
    codes = frame.quantise(ch.param, x0)
    xq = frame.dequantise(ch.param, codes)
    cen = frame.saturated(codes)
    x = np.where(cen, xq, x0)
    D = (eps + 1e-12) * ch.tol
    lo_t = np.where(cen, -np.inf, x - D)
    hi_t = np.where(cen, np.inf, x + D)
    pt_ok = cen | (np.abs(x - xq) <= D)
    # prefix (readings before b) and suffix (readings after a) intervals, and censored counts
    pre_lo = np.concatenate(([-np.inf], np.maximum.accumulate(lo_t)[:-1]))
    pre_hi = np.concatenate(([np.inf], np.minimum.accumulate(hi_t)[:-1]))
    pre_cen = np.concatenate(([0], np.cumsum(cen)[:-1]))
    suf_lo = np.concatenate((np.maximum.accumulate(lo_t[::-1])[::-1][1:], [-np.inf]))
    suf_hi = np.concatenate((np.minimum.accumulate(hi_t[::-1])[::-1][1:], [np.inf]))
    suf_cen = np.concatenate((np.cumsum(cen[::-1])[::-1][1:], [0]))
    head_ok = (pre_cen == 0) & (pre_lo <= xq) & (xq <= pre_hi)
    tail_ok = (suf_cen == 0) & (suf_lo <= xq) & (xq <= suf_hi)

    f = np.full(n, INF)
    back = np.full(n, -1)
    f[pt_ok & head_ok] = 1
    ops = 0
    for a in range(n):
        if f[a] >= INF:
            continue
        lo, hi = -np.inf, np.inf
        for b in range(a + 1, n):
            if b >= a + 2:
                t = b - 1
                if cen[t]:
                    break
                ops += 1
                lo = max(lo, (x[t] - D[t] - xq[a]) / (t - a))
                hi = min(hi, (x[t] + D[t] - xq[a]) / (t - a))
                if lo > hi:
                    break
            if pt_ok[b] and f[a] + 1 < f[b]:
                s = (xq[b] - xq[a]) / (b - a)
                if lo <= s <= hi:
                    f[b], back[b] = f[a] + 1, a
    if count is not None:
        count.append(ops)
    ends = [a for a in range(n) if tail_ok[a] and pt_ok[a] and f[a] < INF]
    if not ends:
        return None
    a = min(ends, key=lambda q: (f[q], q))
    kept = []
    while a >= 0:
        kept.append(int(a))
        a = back[a]
    return kept[::-1], codes


def plan(channels, eps=1.0, count=None):
    """Planned values [(param, slot, code)] in planned order, or None if infeasible (as record.Encoder.plan_at)."""
    out = []
    for c in channels:
        r = min_set(c, eps, count)
        if r is None:
            return None
        kept, codes = r
        out += [(c.param, k, int(codes[k])) for k in kept]
    return out
