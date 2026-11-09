"""Send-on-delta (deadband) baseline with hold reconstruction (revision 2, Step 4).

The node sends a reading whenever it differs from the last SENT (quantised) value by more than the tolerance at that
reading; the first reading of the day and every censored reading are always sent. The server holds each sent value until
the next sent slot, so every uncensored reading is within the tolerance of the held value (quantisation included), the same
guarantee as the piecewise-linear record, with a different (zero-order) selection rule. Planned values use the record's unit
format, so the same frame, quota and loss designs apply.
Certification (hold): readings from a received value up to the slot before the NEXT PLANNED value are certified when that
next planned value also arrived (adjacent planned positions of the same parameter); the last planned value of a parameter
is held to the end of the day when it is known to be last.
"""
import numpy as np

from . import frame

SLACK = 1 + 1e-9


def select(ch, scale=1.0):
    """Slots sent for one channel-day."""
    codes = frame.quantise(ch.param, ch.x)
    cen = frame.saturated(codes)
    deq = frame.dequantise(ch.param, codes)
    kept, held = [], None
    for t in range(ch.n):
        if cen[t]:
            kept.append(t)
            held = None
        elif held is None or abs(ch.x[t] - held) > scale * ch.tol[t] * SLACK:
            kept.append(t)
            held = float(deq[t])
    return kept, codes


def plan(channels, scale=1.0):
    """Planned values [(param, slot, code)] in planned order (channels already in planned order)."""
    out = []
    for ch in channels:
        kept, codes = select(ch, scale)
        out += [(ch.param, int(s), int(codes[s])) for s in kept]
    return out


def reconstruct_hold(n, slots, values):
    """Held value at every reading; NaN before the first received slot."""
    out = np.full(n, np.nan)
    if len(slots) == 0:
        return out
    o = np.argsort(slots)
    s, v = np.asarray(slots)[o], np.asarray(values, float)[o]
    for i, si in enumerate(s):
        end = s[i + 1] if i + 1 < len(s) else n
        out[si:end] = v[i]
    return out


def certify_hold(received, n_of, last_pos=None):
    """Certified-reading masks from received planned values {position: (param, slot, code)}."""
    cert = {p: np.zeros(n, bool) for p, n in n_of.items()}
    for i, (p, s, code) in received.items():
        if frame.saturated(code):
            continue
        c = cert[p]
        c[s] = True
        nxt = received.get(i + 1)
        if nxt is not None and nxt[0] == p:
            c[s:nxt[1]] = True
        if i == last_pos or (nxt is not None and nxt[0] != p):
            c[s:] = True
    return cert


def knowledge_hold(param, n, rx, cert_mask, resolution=None):
    """certlang.Knowledge of one channel from received hold values."""
    from . import certlang as cl
    K = cl.Knowledge(param, n, resolution=resolution)
    got = [(s, code) for p, s, code in rx.values() if p == param]
    for s, code in got:
        K.add_kept(s, code)
    if got and cert_mask.any():
        # a censored kept value ends the hold of the value before it only through the planned-position rule above
        slots = [g[0] for g in got if not frame.saturated(g[1])]
        vals = frame.dequantise(param, [g[1] for g in got if not frame.saturated(g[1])])
        xhat = reconstruct_hold(n, slots, vals)
        m = cert_mask & np.isfinite(xhat)
        if m.any():
            K.add_span(m, xhat)
    return K
