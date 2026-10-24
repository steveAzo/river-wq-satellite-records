"""Server side: reconstruction, the day's guarantee, and certification without feedback.

Certification: the node sends the values of a planned set in a fixed order (parameter, then time), and
each value's position in that order is known to the server from the message sequence (message j carries
planned positions j*V .. j*V + V - 1). The server therefore knows which planned values are missing, even
though it never learns their slots. A span between two consecutive PLANNED values that both arrived
(the anchor counts as arrived) is certified: the encoder guaranteed every value in it within tau x
tolerance. The tail after the last planned value is certified if that value arrived. The certified
share is the share of (parameter, slot) values inside certified spans; it is computed with the true
planned slots, which is what the server's knowledge implies.
"""
import numpy as np

from .pla import reconstruct_one


def picture(sd, delivered):
    """Normalised error |x - xhat| / tol for every parameter and slot; delivered = iterable of (p, slot)."""
    kept = [[] for _ in range(sd.P)]
    for p, s in set(delivered):
        kept[p].append(s)
    return np.stack([np.abs(sd.X[p] - reconstruct_one(sd.X[p], sd.anchor[p], kept[p])) / sd.tol[p]
                     for p in range(sd.P)])


def certified_share(sd, planned, arrived):
    """planned: [(p, slot)] of the encoded set; arrived: set of (p, slot) that reached the server."""
    arrived = set(arrived)
    cert = np.zeros((sd.P, sd.n), bool)
    for p in range(sd.P):
        slots = sorted(s for q, s in planned if q == p)
        prev, prev_ok = -1, True  # the anchor
        for s in slots:
            ok = (p, s) in arrived
            if prev_ok and ok:
                cert[p, prev + 1:s + 1] = True
            elif ok:
                cert[p, s] = True
            prev, prev_ok = s, ok
        if prev_ok:
            cert[p, prev + 1:] = True
            if prev >= 0:
                cert[p, prev] = True
    return float(cert.mean())


def score(sd, delivered):
    e = picture(sd, delivered)
    return {"guaranteed": bool(e.max() <= 1 + 1e-9), "worst": float(e.max()), "mean": float(e.mean()),
            "within": float((e <= 1 + 1e-9).mean())}
