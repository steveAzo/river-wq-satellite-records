"""Record model, quantisation-exact encoder, server reconstruction and certificates (revision Step 3).
Definitions and proofs: docs/RECORD_MODEL.md.

A channel-day is one parameter's readings x(0..n-1) on its native grid with tolerances d(t) > 0.
The server holds dequantised values xq(s) = q(x(s)) of the kept slots it received, and reconstructs:
  head  t < s_1          xq(s_1) held backward ("self"), or the line from the anchor at t = -1 ("anchor")
  span  s_i <= t <= s_i+1 the line between xq(s_i) and xq(s_i+1)
  tail  t > s_m           xq(s_m) held forward
Modes: "self" (no anchor; every day decodes alone), "chain" (anchor = previous day's last planned value,
dequantised; valid only if that value reached the server), "oracle" (anchor = true previous reading: the
draft's model, which no real server has; a reference only).

The encoder measures every error against xq, so a plan feasible at level tau keeps every reading within
tau x tolerance exactly, quantisation included (no margin).
"""
from dataclasses import dataclass

import numpy as np

from . import frame

INF = np.inf
PARAM_ORDER = ("T", "DO", "pH", "EC")


@dataclass
class Channel:
    param: str
    x: np.ndarray        # readings, native grid of the day
    tol: np.ndarray      # per-reading tolerance (> 0)
    anchor: float = None  # mode "chain"/"oracle" only: the value the head starts from (at t = -1)

    @property
    def n(self):
        return len(self.x)


def channels_from_siteday(sd, mode="self", prev_last=None):
    """SiteDay -> [Channel] in planned order. mode "oracle" uses sd.anchor (true previous reading);
    "chain" uses prev_last[param] (previous day's last planned value, dequantised) when given."""
    out = []
    for p in sorted(range(sd.P), key=lambda i: PARAM_ORDER.index(sd.params[i])):
        name = sd.params[p]
        a = None
        if mode == "oracle":
            a = float(sd.anchor[p])
        elif mode == "chain" and prev_last is not None and name in prev_last:
            a = prev_last[name]
        out.append(Channel(name, np.asarray(sd.X[p], float), np.asarray(sd.tol[p], float), a))
    return out


# ---------------------------------------------------------------- encoder tables
def censored_weights(ch, codes):
    """(censored mask, weight 1/tolerance or 0 for censored readings, readings with censored ones replaced).
    A reading is censored when its code flags it outside the quantiser range (or missing); it is always kept,
    carried as its flag, and excluded from the tolerance requirement (Step 9)."""
    cen = frame.saturated(codes)
    w = np.zeros(len(codes))
    np.divide(1.0, ch.tol, out=w, where=~cen)
    x = np.where(cen, frame.dequantise(ch.param, codes), ch.x)
    return cen, w, x


def tables(ch):
    """Error tables against dequantised endpoints (normalised by tolerance):
    seg[a, b]  worst error strictly between kept slots a < b (line between xq[a] and xq[b])
    head[b]    worst error before b if b is the first kept slot
    tail[a]    worst error after a if a is the last kept slot
    pt[s]      error at a kept slot itself (quantisation).
    Censored readings (outside the quantiser range) add no error but may not be skipped: a span, head, or tail
    that would pass over one is infeasible (INF), so every censored reading is kept."""
    n = ch.n
    codes = frame.quantise(ch.param, ch.x)
    xq = frame.dequantise(ch.param, codes)
    cen, w, x = censored_weights(ch, codes)
    ncen = np.concatenate(([0], np.cumsum(cen)))          # ncen[k] = censored readings among 0..k-1
    pt = np.abs(x - xq) * w
    seg = np.zeros((n, n))
    for a in range(n - 1):
        b = np.arange(a + 2, n)
        if len(b) == 0:
            continue
        worst = np.zeros(len(b))
        for t in range(a + 1, n - 1):
            ends = b > t
            if not ends.any():
                break
            line = xq[a] + (xq[b[ends]] - xq[a]) * (t - a) / (b[ends] - a)
            worst[ends] = np.maximum(worst[ends], np.abs(x[t] - line) * w[t])
        worst[ncen[b] - ncen[a + 1] > 0] = INF
        seg[a, b] = worst
    tail = np.array([np.max(np.abs(x[a + 1:] - xq[a]) * w[a + 1:]) if a < n - 1 else 0.0 for a in range(n)])
    tail[ncen[n] - ncen[np.arange(n) + 1] > 0] = INF
    return {"seg": seg, "head": head_table(ch, xq, ch.anchor), "tail": tail, "pt": pt, "codes": codes, "xq": xq,
            "censored": cen}


def head_table(ch, xq, anchor):
    """head[b] for a given anchor (None: hold xq[b] backward). Separate so modes can share seg/tail/pt."""
    n = ch.n
    cen, w, x = censored_weights(ch, frame.quantise(ch.param, ch.x))
    head = np.zeros(n)
    t_all = np.arange(n)
    for b in range(1, n):
        if anchor is None:
            head[b] = np.max(np.abs(x[:b] - xq[b]) * w[:b])
        else:
            line = anchor + (xq[b] - anchor) * (t_all[:b] + 1) / (b + 1)
            head[b] = np.max(np.abs(x[:b] - line) * w[:b])
        if cen[:b].any():
            head[b] = INF
    return head


def with_anchor(tab, ch, anchor):
    """Copy of a table set with the head recomputed for another anchor."""
    return {**tab, "head": head_table(ch, tab["xq"], anchor)}


def min_set(tab, eps):
    """Fewest kept slots keeping every reading within eps (exact DP over the tables); None if infeasible.
    Ties: fewest slots, then the earliest last slot."""
    seg, head, tail, pt = tab["seg"], tab["head"], tab["tail"], tab["pt"]
    n = len(pt)
    tol = eps + 1e-12
    f = np.full(n, np.iinfo(np.int64).max // 2)
    back = np.full(n, -1)
    for b in range(n):
        if pt[b] > tol:
            continue
        if head[b] <= tol:
            f[b] = 1
            continue
        ok = np.flatnonzero(seg[:b, b] <= tol)
        if len(ok):
            a = ok[np.argmin(f[ok])]
            if f[a] < f[b] - 1:
                f[b], back[b] = f[a] + 1, a
    ends = [a for a in range(n) if tail[a] <= tol and pt[a] <= tol and f[a] < np.iinfo(np.int64).max // 2]
    if not ends:
        return None
    a = min(ends, key=lambda q: (f[q], q))
    kept = []
    while a >= 0:
        kept.append(a)
        a = back[a]
    return kept[::-1]


class Encoder:
    """Per record-day encoder over channels in planned order: smallest common level tau whose min-# sets
    fit a value budget. A plan is 'bound' when tau <= 1 (every reading within its tolerance)."""

    def __init__(self, channels):
        self.ch = channels
        self.tabs = [tables(c) for c in channels]
        vals = [np.array([0.0])]
        for t in self.tabs:
            iu = np.triu_indices_from(t["seg"], 2)
            vals += [t["seg"][iu], t["head"], t["tail"], t["pt"]]
        c = np.unique(np.concatenate(vals))
        self.cands = c[np.isfinite(c)]
        self._count = {}

    def count(self, i):
        if i not in self._count:
            sets = [min_set(t, self.cands[i]) for t in self.tabs]
            self._count[i] = INF if any(s is None for s in sets) else sum(len(s) for s in sets)
        return self._count[i]

    def plan_at(self, tau):
        """Planned values [(param, slot, code)] in planned order, or None if infeasible at tau."""
        out = []
        for c, t in zip(self.ch, self.tabs):
            s = min_set(t, tau)
            if s is None:
                return None
            out += [(c.param, int(k), int(t["codes"][k])) for k in s]
        return out

    def need(self, tau=1.0):
        p = self.plan_at(tau)
        return None if p is None else len(p)

    def fit(self, k):
        """(tau, planned values) with the smallest tau whose plan has <= k values; None if no tau fits."""
        lo, hi = 0, len(self.cands) - 1
        if self.count(hi) > k:
            return None
        while lo < hi:
            mid = (lo + hi) // 2
            if self.count(mid) <= k:
                hi = mid
            else:
                lo = mid + 1
        tau = float(self.cands[lo])
        return tau, self.plan_at(tau)


# ---------------------------------------------------------------- server
def reconstruct(n, slots, values, anchor=None):
    """Server reconstruction of one channel from received (slot, dequantised value) pairs."""
    if len(slots) == 0:
        return np.full(n, np.nan)
    o = np.argsort(slots)
    s, v = np.asarray(slots)[o], np.asarray(values, float)[o]
    if anchor is not None:
        s, v = np.concatenate(([-1], s)), np.concatenate(([anchor], v))
    return np.interp(np.arange(n), s, v)  # np.interp holds the end values outside [s_1, s_m]


def certify(received, n_of, bound, last_pos=None, anchor_ok=None):
    """Certificate of one record day from received planned values only.

    received:  {position: (param, slot, code)} decoded from units that passed their CRC
    n_of:      {param: readings per day} (site profile: native interval)
    bound:     the day's bound flag (from any received segment)
    last_pos:  position of the day's final planned value, if a segment with last = 1 was received
    anchor_ok: mode "chain" only: {param: True if the previous day's last value of param is known}; heads
               are then certified only where the anchor is known. None = self-contained mode.
    Returns ({param: boolean array of certified readings}, fully_certified)."""
    cert = {p: np.zeros(n, bool) for p, n in n_of.items()}
    if not bound or not received:
        return cert, False
    for i, (p, s, _) in received.items():
        c = cert[p]
        c[s] = True
        nxt = received.get(i + 1)
        prv = received.get(i - 1)
        if nxt is not None and nxt[0] == p:
            c[s:nxt[1] + 1] = True
        is_first = i == 0 or (prv is not None and prv[0] != p)
        is_last = i == last_pos or (nxt is not None and nxt[0] != p)
        if is_first and (anchor_ok is None or anchor_ok.get(p, False)):
            c[:s + 1] = True
        if is_last:
            c[s:] = True
    censored = {p: np.zeros(n, bool) for p, n in n_of.items()}
    for p, s, code in received.values():
        if frame.saturated(code):            # carried as a flag: reported as censored, never certified
            cert[p][s] = False
            censored[p][s] = True
    full = last_pos is not None and all(i in received for i in range(last_pos + 1))
    if full:
        present = {p for p, _, _ in received.values()}
        full = all((cert[p] | censored[p]).all() for p in present)
    return cert, full


def errors(channels, received, anchors=None):
    """Oracle evaluation (not available to the server): normalised error of every reading of every
    channel under the server's reconstruction. Channels with nothing received are all NaN."""
    out = {}
    for c in channels:
        got = [(s, frame.dequantise(p, code)) for p, s, code in received.values() if p == c.param]
        a = None if anchors is None else anchors.get(c.param)
        rec = reconstruct(c.n, [g[0] for g in got], [g[1] for g in got], a)
        cen = frame.saturated(frame.quantise(c.param, c.x))
        e = np.zeros(c.n)
        np.divide(np.abs(np.where(cen, 0.0, c.x) - rec), c.tol, out=e, where=~cen)
        e[cen & np.isnan(rec)] = np.nan          # nothing received: unknown, like any other reading
        out[c.param] = e
    return out


def interval(param, xhat, tolset="excellent"):
    """Server-side bounds on the true reading x of a certified reading with reconstruction xhat.
    Certification gives |x - xhat| <= delta(x) with delta(x) = max(a, r |x|) (data.TOLSETS), which depends on the
    unknown x. For x >= 0: x <= max(xhat + a, xhat / (1 - r)) and x >= min(xhat - a, xhat / (1 + r))."""
    from .data import TOLSETS
    a, r = TOLSETS[tolset][param]
    xhat = np.asarray(xhat, float)
    return np.minimum(xhat - a, xhat / (1 + r)), np.maximum(xhat + a, xhat / (1 - r))
