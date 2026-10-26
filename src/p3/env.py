"""Environmental decisions and statistics from delivered records (revision Step 8; plan: docs/STEP8_PLAN.md).

For one record day and the planned values the server received, `day_metrics` reconstructs every channel, certifies
it (record.certify), and evaluates the criteria of the plan against the full sensor record:
  two-valued decisions from the reconstruction (naive), and
  three-valued decisions (certainly yes / certainly no / undetermined) that use only certified readings and the
  server-side interval of record.interval; these cannot be wrong when Proposition 1 holds.
Daily statistics, peak timing, DO diel range, and rapid EC change are compared with the truth.
"""
import numpy as np

from . import frame, record
from .data import tolerance

DO_MIN = 5.0
PH_LO, PH_HI = 6.5, 9.0
T_7DADM = 20.0
EC_JUMP = 0.10


def reconstruct_all(rd, rx):
    out = {}
    for c in rd.channels:
        got = [(s, frame.dequantise(p, code)) for p, s, code in rx.values() if p == c.param]
        out[c.param] = (record.reconstruct(c.n, [g[0] for g in got], [g[1] for g in got]) if got
                        else np.full(c.n, np.nan))
    return out


def three_valued(param, xhat, cert, below=None, above=None):
    """Exceedance of `below` (some x < below) or `above` (some x > above) decided from certified readings only.
    Returns 1 (certainly exceeded), 0 (certainly not), or -1 (undetermined)."""
    if not cert.any():
        return -1
    L, U = record.interval(param, xhat[cert])
    yes = (below is not None and (U < below).any()) or (above is not None and (L > above).any())
    if yes:
        return 1
    if cert.all():
        ok = (below is None or (L >= below).all()) and (above is None or (U <= above).all())
        return 0 if ok else -1
    return -1


def one_hour_change(x, step):
    h = max(1, 60 // step)
    if len(x) <= h:
        return np.zeros(0)
    return np.abs(x[h:] - x[:-h]) / np.abs(x[:-h])


def day_metrics(rd, rx, bound, last):
    """Metrics of one delivered record day (rx: {position: (param, slot, code)})."""
    rec = reconstruct_all(rd, rx)
    cert, _ = record.certify(rx, rd.n_of, bound, last)
    ch = {c.param: c for c in rd.channels}
    m = {"have": {p: bool(np.isfinite(rec[p]).all()) for p in rec}}

    do, dohat = ch["DO"].x, rec["DO"]
    m["DO_true"] = bool(do.min() < DO_MIN)
    m["DO_naive"] = bool(m["have"]["DO"] and dohat.min() < DO_MIN)
    m["DO_3v"] = three_valued("DO", dohat, cert["DO"], below=DO_MIN)
    ph, phhat = ch["pH"].x, rec["pH"]
    m["pH_true"] = bool(ph.min() < PH_LO or ph.max() > PH_HI)
    m["pH_naive"] = bool(m["have"]["pH"] and (phhat.min() < PH_LO or phhat.max() > PH_HI))
    m["pH_3v"] = three_valued("pH", phhat, cert["pH"], below=PH_LO, above=PH_HI)

    # daily statistics, in tolerances at the true statistic
    for p, c in ch.items():
        for stat, f in (("min", np.min), ("max", np.max), ("mean", np.mean)):
            tv = f(c.x)
            tol = float(tolerance(p, [tv])[0])
            m[f"{p}_{stat}_err"] = abs(f(rec[p]) - tv) / tol if m["have"][p] else np.nan

    # peak timing (T, DO) where the true daily range exceeds two tolerances
    for p in ("T", "DO"):
        c = ch[p]
        if np.ptp(c.x) > 2 * np.median(c.tol) and m["have"][p]:
            m[f"{p}_peak_min"] = abs(int(np.argmax(rec[p])) - int(np.argmax(c.x))) * rd.steps[p]
        else:
            m[f"{p}_peak_min"] = np.nan
    m["DO_range_err"] = abs(np.ptp(dohat) - np.ptp(do)) if m["have"]["DO"] else np.nan

    # rapid EC change
    rt, rr_ = one_hour_change(ch["EC"].x, rd.steps["EC"]), one_hour_change(rec["EC"], rd.steps["EC"])
    m["EC_true"] = bool((rt > EC_JUMP).any())
    m["EC_naive"] = bool(m["have"]["EC"] and (rr_ > EC_JUMP).any())
    m["EC_jump_min"] = (abs(int(np.argmax(rr_)) - int(np.argmax(rt))) * rd.steps["EC"]
                        if m["EC_true"] and m["have"]["EC"] else np.nan)

    # daily maximum temperature and its certified bounds (for the 7DADM)
    t_hat, t_cert = rec["T"], cert["T"]
    m["Tmax_true"] = float(ch["T"].x.max())
    m["Tmax_hat"] = float(t_hat.max()) if m["have"]["T"] else np.nan
    if t_cert.any():
        L, U = record.interval("T", t_hat[t_cert])
        m["Tmax_lo"], m["Tmax_hi"] = float(L.max()), (float(U.max()) if t_cert.all() else np.inf)
    else:
        m["Tmax_lo"], m["Tmax_hi"] = -np.inf, np.inf
    m["certified_share"] = sum(v.sum() for v in cert.values()) / rd.raw_values
    return m


def seven_dadm(days, tmax):
    """days: sorted record days; tmax: {day: value}. Returns {last day of window: 7-day mean} for windows of
    seven consecutive days all present (non-NaN)."""
    out = {}
    for d in days:
        win = [tmax.get(d - k, np.nan) for k in range(7)]
        if not any(np.isnan(v) for v in win):
            out[d] = float(np.mean(win))
    return out
