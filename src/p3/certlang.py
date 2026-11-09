"""Certificate language for environmental decisions (revision 2, Step 2). Specification and proofs:
docs/CERTIFICATE_SPEC.md.

A channel-day is summarised on the SERVER by a Knowledge object: for every reading t a closed interval [lo(t), hi(t)]
that is guaranteed to contain the true reading, plus the set of readings known to be censored (outside the quantiser
range; they are not part of any decision). All sources of information are expressed as intervals:
  base range      every uncensored reading lies in the quantiser range of its parameter;
  kept value      the reading at a kept slot lies in the quantiser cell of its code;
  certified span  |x - xhat| <= delta(x) gives the exact interval of `interval()` around the reconstruction xhat;
  extremum witness  a kept value that is declared the minimum (maximum) of the day's uncensored readings: its cell
                  bounds that reading and, for every other reading, x >= cell lower bound (x <= cell upper bound).
The decision rules read only the intervals, so they are independent of the codec. Soundness (Proposition 1 of the
specification) holds whenever every interval is valid.
"""
from dataclasses import dataclass, field

import numpy as np

from . import frame
from .data import TOLSETS

INF = np.inf
REL = 1e-9          # float slack applied to every interval (conservative: intervals only grow)


def base_range(param):
    """Closed range that contains every UNCENSORED reading of the parameter."""
    lo, step, hi, log = frame._grid(param)
    if log:
        return 10 ** (lo - step / 2), 10 ** (hi + step / 2)
    return lo - step / 2, hi + step / 2


def cell(param, code):
    """Quantiser cell: the readings that quantise to `code` (nearest rounding)."""
    lo, step, _, log = frame._grid(param)
    v = lo + (int(code) - 1) * step
    if log:
        return 10 ** (v - step / 2), 10 ** (v + step / 2)
    return v - step / 2, v + step / 2


def interval(param, xhat, tolset="excellent", scale=1.0):
    """Exact interval of the true readings x with |x - xhat| <= max(a, r |x|), for x >= 0 and r < 1.
    The solution set is the union of {|x - xhat| <= a} and {|x - xhat| <= r x}; both contain xhat, so it is an
    interval with the endpoints below (tight, not only a bound)."""
    a, r = TOLSETS[tolset][param]
    a, r = a * scale, r * scale                # a tightened record certifies scale x tolerance
    xhat = np.asarray(xhat, float)
    return np.minimum(xhat - a, xhat / (1 + r)), np.maximum(xhat + a, xhat / (1 - r))


def _pad(lo, hi):
    return lo - REL * np.maximum(1.0, np.abs(lo)), hi + REL * np.maximum(1.0, np.abs(hi))


@dataclass
class Knowledge:
    param: str
    n: int
    lo: np.ndarray = None
    hi: np.ndarray = None
    excluded: np.ndarray = None          # known censored readings (outside every decision)
    resolution: float = None             # site-profile fact: every uncensored reading is a multiple of this (decimal)
    g_lo: float = -INF                   # global lower bound for every uncensored reading (min witness)
    g_hi: float = INF                    # global upper bound (max witness)
    rate_hi: float = None                # global bound on the relative change over `rate_lag` slots (rate witness)
    rate_lag: int = None
    wmin: tuple = None                   # cell of the day's minimum (slotless min witness)
    wmax: tuple = None
    rate_cells: tuple = None             # (La, Ua, Lb, Ub): cells of the pair that realises the largest relative change
    notes: list = field(default_factory=list)

    def __post_init__(self):
        b = base_range(self.param)
        self.lo = np.full(self.n, b[0])
        self.hi = np.full(self.n, b[1])
        self.excluded = np.zeros(self.n, bool)

    # ---- information sources (each narrows intervals; none widens)
    def add_kept(self, slot, code):
        if frame.saturated(code):
            self.excluded[slot] = True
            return
        a, b = _pad(*cell(self.param, code))
        self.lo[slot], self.hi[slot] = max(self.lo[slot], a), min(self.hi[slot], b)

    def add_span(self, mask, xhat, tolset="excellent", scale=1.0):
        """Readings in `mask` are certified: |x - xhat| <= delta(x) (Proposition 1 of the frame specification)."""
        a, b = _pad(*interval(self.param, np.asarray(xhat, float)[mask], tolset, scale))
        self.lo[mask] = np.maximum(self.lo[mask], a)
        self.hi[mask] = np.minimum(self.hi[mask], b)

    def add_min_witness(self, slot, code):
        """Declared: x(slot) is the minimum of the uncensored readings of the day."""
        self.add_kept(slot, code)
        self.g_lo = max(self.g_lo, self.lo[slot])

    def add_max_witness(self, slot, code):
        self.add_kept(slot, code)
        self.g_hi = min(self.g_hi, self.hi[slot])

    def add_rate_witness(self, slot_a, code_a, slot_b, code_b, lag):
        """Declared: the pair (slot_a, slot_b = slot_a + lag) realises the day's largest relative change
        |x(t + lag) - x(t)| / x(t) over pairs of uncensored readings. Every pair is then bounded by the witness ratio."""
        self.add_kept(slot_a, code_a)
        self.add_kept(slot_b, code_b)
        La, Ua, Lb, Ub = self.lo[slot_a], self.hi[slot_a], self.lo[slot_b], self.hi[slot_b]
        if La > 0 and Ua > 0:
            hi = max(Ub / La - 1.0, 1.0 - Lb / Ua)
            self.rate_hi = hi if self.rate_hi is None else min(self.rate_hi, hi)
            self.rate_lag = lag

    # ---- slotless witnesses (frame v2): the decision rules use only the witness cell, never its slot
    def _snap(self, a, b):
        if self.resolution:
            rho = self.resolution
            a = float(np.round(np.ceil(a / rho - 1e-6) * rho, 12))
            b = float(np.round(np.floor(b / rho + 1e-6) * rho, 12))
        return a, b

    def add_min_witness_value(self, code):
        """Declared: the minimum of the uncensored readings of the day quantises to `code`."""
        if frame.saturated(code):
            return
        a, b = _pad(*cell(self.param, code))
        self.wmin = (a, b) if self.wmin is None else (max(a, self.wmin[0]), min(b, self.wmin[1]))
        self.g_lo = max(self.g_lo, a)

    def add_max_witness_value(self, code):
        if frame.saturated(code):
            return
        a, b = _pad(*cell(self.param, code))
        self.wmax = (a, b) if self.wmax is None else (max(a, self.wmax[0]), min(b, self.wmax[1]))
        self.g_hi = min(self.g_hi, b)

    def add_rate_witness_values(self, code_a, code_b, lag):
        """Declared: some pair of uncensored readings `lag` apart, with values in the cells of code_a and code_b, realises the
        day's largest relative change."""
        if frame.saturated(code_a) or frame.saturated(code_b):
            return
        (La, Ua), (Lb, Ub) = _pad(*cell(self.param, code_a)), _pad(*cell(self.param, code_b))
        if La > 0 and Ua > 0:
            self.rate_cells = (La, Ua, Lb, Ub)
            hi = max(Ub / La - 1.0, 1.0 - Lb / Ua)
            self.rate_hi = hi if self.rate_hi is None else min(self.rate_hi, hi)
            self.rate_lag = lag

    # ---- effective intervals
    def eff(self):
        lo = np.maximum(self.lo, self.g_lo)
        hi = np.minimum(self.hi, self.g_hi)
        if self.resolution:
            # Assumption R (grid): readings are integer multiples of the reporting resolution, so every interval can
            # be moved inward to the nearest grid points. The 1e-6 grid-unit tolerance exceeds the float padding.
            rho = self.resolution
            # Rounding to 12 places gives the double nearest to the decimal grid point, the same double that a decimal
            # literal (a threshold, a CSV reading) parses to, so comparisons at exact grid points are exact.
            lo = np.round(np.ceil(lo / rho - 1e-6) * rho, 12)
            hi = np.round(np.floor(hi / rho + 1e-6) * rho, 12)
        return lo, hi

    def live(self):
        return ~self.excluded


# ---------------------------------------------------------------- decisions: 1 yes, 0 no, -1 undetermined
def exceeds_below(K, theta):
    """Some uncensored reading is < theta."""
    lo, hi = K.eff()
    m = K.live()
    if not m.any():
        return -1
    if (hi[m] < theta).any() or (K.wmin is not None and K._snap(*K.wmin)[1] < theta):
        return 1
    return 0 if (lo[m] >= theta).all() else -1


def exceeds_above(K, theta):
    """Some uncensored reading is > theta."""
    lo, hi = K.eff()
    m = K.live()
    if not m.any():
        return -1
    if (lo[m] > theta).any() or (K.wmax is not None and K._snap(*K.wmax)[0] > theta):
        return 1
    return 0 if (hi[m] <= theta).all() else -1


def min_bounds(K):
    """Interval of the day's minimum over uncensored readings."""
    lo, hi = K.eff()
    m = K.live()
    a, b = float(lo[m].min()), float(hi[m].min())
    if K.wmin is not None:
        wa, wb = K._snap(*K.wmin)
        a, b = max(a, wa), min(b, wb)
    return a, b


def max_bounds(K):
    lo, hi = K.eff()
    m = K.live()
    a, b = float(lo[m].max()), float(hi[m].max())
    if K.wmax is not None:
        wa, wb = K._snap(*K.wmax)
        a, b = max(a, wa), min(b, wb)
    return a, b


def relative_change(K, lag, frac=0.10):
    """Is there a pair of uncensored readings `lag` slots apart with |x_b - x_a| / x_a > frac?  Returns 1, 0, or -1.
    Exact on the interval model: 'no' iff every pair is certainly within frac; 'yes' iff no assignment of readings
    inside their intervals keeps every pair within frac (forward propagation along each of the `lag` chains)."""
    lo, hi = K.eff()
    live = K.live()
    if lag < 1 or K.n <= lag or (lo[live] <= 0).any():
        return -1
    if K.rate_hi is not None and K.rate_lag == lag and K.rate_hi <= frac:
        return 0                              # the day's largest relative change is certainly within frac
    if K.rate_cells is not None and K.rate_lag == lag:
        La, Ua, Lb, Ub = K.rate_cells
        if Lb / Ua > 1 + frac or Ub / La < 1 - frac:
            return 1                          # the witness pair itself certainly changes by more than frac
    certain_no = True
    for r in range(lag):
        reach = None                          # reachable interval of the current reading under all-no
        prev = None
        for t in range(r, K.n, lag):
            if not live[t]:
                reach, prev = None, None
                continue
            if prev is not None:
                if hi[t] > (1 + frac) * lo[prev] or lo[t] < (1 - frac) * hi[prev]:
                    certain_no = False
                a, b = (1 - frac) * reach[0], (1 + frac) * reach[1]
                cur = (max(lo[t], a), min(hi[t], b))
                if cur[0] > cur[1]:
                    return 1                  # no assignment avoids a change: certainly yes
                reach = cur
            else:
                reach = (lo[t], hi[t])
            prev = t
    return 0 if certain_no else -1


def rolling_mean_decision(bounds, threshold):
    """bounds: seven (lo, hi) daily-maximum intervals, (-inf, inf) for a day with no information.
    Is the mean of the seven values above threshold?  Returns 1, 0, or -1."""
    lo = sum(b[0] for b in bounds) / len(bounds)
    hi = sum(b[1] for b in bounds) / len(bounds)
    if lo > threshold:
        return 1
    return 0 if hi <= threshold else -1


def day_max_bounds(K):
    """Daily maximum interval for the rolling statistic; an information-free day gives the base range."""
    return max_bounds(K)


def knowledge_from_rx(param, n, rx, cert_mask, use_cells=True, resolution=None, scale=1.0):
    """Server knowledge of one channel-day from the received planned values `rx` ({position: (param, slot, code)})
    and the certified-reading mask of record.certify. use_cells=False reproduces the span-only rule of Step 8
    (every certified reading, kept or not, gets the tolerance interval; censored flags are still honoured)."""
    from . import record
    K = Knowledge(param, n, resolution=resolution)
    got = [(s, code) for p, s, code in rx.values() if p == param]
    for s, code in got:
        if use_cells or frame.saturated(code):
            K.add_kept(s, code)
    if got and cert_mask.any():
        xhat = record.reconstruct(n, [g[0] for g in got], frame.dequantise(param, [g[1] for g in got]))
        K.add_span(cert_mask, xhat, scale=scale)
    return K


RESOLUTIONS = (1.0, 0.5, 0.1, 0.05, 0.01, 0.005, 0.001)


def infer_resolution(values):
    """Coarsest decimal resolution of which every finite value is a multiple (None if none of RESOLUTIONS fits).
    In deployment this is a declared field of the site profile; here it is read from the record."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return None
    for rho in RESOLUTIONS:
        q = v / rho
        if np.allclose(q, np.rint(q), atol=1e-6, rtol=0):
            return rho
    return None


def witness_consistent(K0, kind, code):
    """Cross-check of a received witness against the record (K0: Knowledge built from the record only, no witness).
    A minimum witness contradicts the record if some reading's upper bound lies below the witness cell, or if every
    reading's lower bound lies above it; a maximum witness symmetrically. An honest witness is never contradicted (its cell
    contains the true extremum, which lies between the readings' bounds), so the check only ever rejects."""
    if frame.saturated(code):
        return False
    a, b = K0._snap(*_pad(*cell(K0.param, code)))
    lo, hi = K0.eff()
    m = K0.live()
    if not m.any():
        return True
    if kind == "min":
        return not ((hi[m] < a).any() or lo[m].min() > b)
    return not ((lo[m] > b).any() or hi[m].max() < a)
