"""Byte-level delivery designs and server (revision Step 4b; review M4, M6, E1).

Every design turns one record day into the actual messages it transmits (docs/FRAME_SPEC.md), in order.
The server sees only the bytes that arrive: it parses the headers, decodes Reed-Solomon when it can, checks
each unit's CRC, collects planned positions, reconstructs, and certifies (record.certify). Nothing from the
plan reaches the server except through those bytes.

Designs (Q messages per day, c = values per unit, 5 at 23 B):
  every_k   every k-th reading of each channel, newest included, k as small as fits c*Q; uncoded, once each
  tag       satellite-tag practice: per channel a fixed number of broken-stick points (endpoints first, then
            largest absolute deviation) in D = share*Q units; the Q transmissions pick units pseudo-randomly
  reliable  min-# at the smallest tau that fits c*Q values; every unit once
  repeat_r  min-# fitting c*floor(Q/r) values; units cycled round robin until all Q messages are used
  mds_K     min-# fitting c*K values in K data units (empty units pad to K) + Q-K Reed-Solomon parity
  record-first (no channel parameter; Step 5): the day's record at tau = 1 needs D1 = ceil(need / c) units.
  mds_rec   D1 <= Q: K = D1 data units + Q - D1 parity (K travels in each header); else reliable
  rep_rec   D1 <= Q: the D1 units cycled round robin over all Q messages; else reliable
Every design sets the bound flag when its planned set keeps every reading within tolerance (E(S) <= 1),
so baselines are certified whenever they deserve it.
"""
import itertools
from collections import Counter
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import fountain, frame, record, rs

EPOCH = pd.Timestamp("2000-01-01")
SLACK = 1 + 1e-9


def day_number(day):
    """UTC day -> days since 2000-01-01."""
    t = pd.Timestamp(day)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return (t.normalize() - EPOCH).days


@dataclass
class Sent:
    name: str
    planned: list           # [(param, slot, code)] in planned order
    bound: bool
    msgs: list              # bytes, in transmission order
    idx: list               # message index of each transmission (copies share it)
    tau: float = None
    meta: dict = field(default_factory=dict)
    cache: dict = field(default_factory=dict, repr=False)


def plan_error(channels, planned):
    """E(S): worst normalised error of the full plan, with each channel's head rule (anchor if set)."""
    anchors = {c.param: c.anchor for c in channels if c.anchor is not None}
    e = record.errors(channels, dict(enumerate(planned)), anchors or None)
    return max(float(np.nanmax(v)) if np.isfinite(v).any() else np.inf for v in e.values())


def _units(planned, bound, payload):
    return frame.pack([[0, planned, bound, 0]], 10 ** 6, payload)


def _uncoded(name, rd, planned, payload, order=None, tau=None, meta=None):
    bound = plan_error(rd.channels, planned) <= SLACK
    segs = _units(planned, bound, payload)
    day = day_number(rd.day)
    K = len(segs)
    units = [frame.message(frame.Header(day, i, K, False), frame.encode_unit(s, frame.Header(day, i, K, False), i, payload))
             for i, s in enumerate(segs)]
    order = list(range(K)) if order is None else order
    return Sent(name, planned, bound, [units[i] for i in order], list(order), tau, {**(meta or {}), "units": K})


def every_k(rd, Q, payload=23):
    cap = frame.unit_capacity(payload) * Q
    for k in range(1, max(c.n for c in rd.channels) + 1):
        planned = [(c.param, s, int(frame.quantise(c.param, c.x[s])))
                   for c in rd.channels for s in range(c.n - 1, -1, -k)[::-1]]
        if len(planned) <= cap:
            return _uncoded("every_k", rd, planned, payload, meta={"k": k})
    raise ValueError("no stride fits")


def broken_stick(ch, m):
    """Endpoints first, then the reading of largest absolute deviation from the current polyline."""
    kept = [ch.n - 1] if m == 1 else [0, ch.n - 1]
    while len(kept) < m:
        xq = frame.roundtrip(ch.param, ch.x[kept])
        err = np.abs(ch.x - record.reconstruct(ch.n, kept, xq))
        err[kept] = -1
        i = int(np.argmax(err))
        if err[i] <= 0:
            break
        kept.append(i)
    return sorted(kept)


def tag(rd, Q, share=0.5, seed=0, payload=23):
    c = frame.unit_capacity(payload)
    D = max(1, int(round(share * Q)))
    m = max(1, (c * D) // len(rd.channels))
    planned = [(ch.param, s, int(frame.quantise(ch.param, ch.x[s])))
               for ch in rd.channels for s in broken_stick(ch, m)][:c * D]
    D = -(-len(planned) // c)
    order = list(np.random.default_rng(seed).integers(0, D, Q))
    return _uncoded("tag", rd, planned, payload, order, meta={"D": D, "share": share, "points": m})


def reliable(rd, enc, Q, payload=23):
    tau, planned = enc.fit(frame.unit_capacity(payload) * Q)
    return _uncoded("reliable", rd, planned, payload, tau=tau)


def repeat(rd, enc, Q, r, payload=23):
    m = max(1, Q // r)
    tau, planned = enc.fit(frame.unit_capacity(payload) * m)
    K = -(-len(planned) // frame.unit_capacity(payload))
    return _uncoded(f"repeat_{r}", rd, planned, payload, cyclic(K, Q), tau=tau, meta={"r": r})


def cyclic(K, Q):
    """Round-robin transmission order of K units over Q messages (copies as equal as possible)."""
    return [i % K for i in range(Q)]


def record_units(enc, payload=23):
    """(planned record at tau = 1, D1 = units it needs)."""
    planned = enc.plan_at(1.0)
    return planned, -(-len(planned) // frame.unit_capacity(payload))


def mds_rec(rd, enc, Q, payload=23):
    planned, D1 = record_units(enc, payload)
    if D1 > Q:
        s = reliable(rd, enc, Q, payload)
        s.name, s.meta["fallback"] = "mds_rec", True
        return s
    s = mds(rd, enc, Q, D1, payload, planned=(1.0, planned))
    s.name = "mds_rec"
    return s


def rep_rec(rd, enc, Q, payload=23):
    planned, D1 = record_units(enc, payload)
    if D1 > Q:
        s = reliable(rd, enc, Q, payload)
        s.name, s.meta["fallback"] = "rep_rec", True
        return s
    return _uncoded("rep_rec", rd, planned, payload, cyclic(D1, Q), tau=1.0, meta={"D1": D1})


def block_order(K, Q):
    """Copies kept together (0,0,1,1,...): the non-interleaved order, to measure what interleaving buys."""
    c = [Q // K + (1 if i < Q % K else 0) for i in range(K)]
    return [i for i in range(K) for _ in range(c[i])]


def rep_block_rec(rd, enc, Q, payload=23):
    planned, D1 = record_units(enc, payload)
    if D1 > Q:
        s = reliable(rd, enc, Q, payload)
        s.name, s.meta["fallback"] = "rep_block_rec", True
        return s
    return _uncoded("rep_block_rec", rd, planned, payload, block_order(D1, Q), tau=1.0, meta={"D1": D1})


def tag_rec(rd, enc, Q, seed=0, payload=23):
    """Tag transmission policy (units picked pseudo-randomly with replacement) carrying the record's units:
    separates the effect of the tag's content from that of its policy."""
    planned, D1 = record_units(enc, payload)
    if D1 > Q:
        s = reliable(rd, enc, Q, payload)
        s.name, s.meta["fallback"] = "tag_rec", True
        return s
    order = [int(i) for i in np.random.default_rng(seed).integers(0, D1, Q)]
    return _uncoded("tag_rec", rd, planned, payload, order, tau=1.0, meta={"D1": D1})


def rlnc_rec(rd, enc, Q, payload=23):
    """Record-first systematic random linear (fountain-style) code: K = D1 data units + Q - D1 random combinations."""
    planned, D1 = record_units(enc, payload)
    if D1 > Q:
        s = reliable(rd, enc, Q, payload)
        s.name, s.meta["fallback"] = "rlnc_rec", True
        return s
    bound = plan_error(rd.channels, planned) <= SLACK
    segs = _units(planned, bound, payload)
    day = day_number(rd.day)
    hdr = [frame.Header(day, i, D1, True, fountain=True) for i in range(Q)]
    units = [list(frame.encode_unit(seg, hdr[i], i, payload)) for i, seg in enumerate(segs)]
    coded = fountain.encode(units, Q, day)
    msgs = [frame.message(hdr[i], c) for i, c in enumerate(coded)]
    return Sent("rlnc_rec", planned, bound, msgs, list(range(Q)), 1.0, {"D1": D1, "fountain": True})


def mds(rd, enc, Q, K, payload=23, planned=None):
    tau, planned = planned if planned is not None else enc.fit(frame.unit_capacity(payload) * K)
    bound = plan_error(rd.channels, planned) <= SLACK
    segs = _units(planned, bound, payload)
    segs += [[] for _ in range(K - len(segs))]
    day = day_number(rd.day)
    units = [list(frame.encode_unit(s, frame.Header(day, i, K), i, payload)) for i, s in enumerate(segs)]
    coded = rs.encode(units, Q)
    msgs = [frame.message(frame.Header(day, i, K), c) for i, c in enumerate(coded)]
    n_value_units = sum(1 for s in segs if s)
    return Sent(f"mds_{K}", planned, bound, msgs, list(range(Q)), tau, {"K": K, "D": n_value_units})


# ---------------------------------------------------------------- server
MAX_DECODE_TRIES = 64


def recover_units(msgs, rx_day):
    """Hardened decoding of the messages of one block that arrived (Step 9; review M18).

    1. Parse headers; drop impossible ones (other version, K = 0).
    2. Keep the majority header (block day, K, coded, fountain); drop messages that disagree with it.
    3. Data units (index < K): accept a received payload only if its CRC passes (any intact copy will do).
    4. Coded block with data units still missing and enough messages: decode from the verified data units plus
       parity rows, trying further parity combinations (at most MAX_DECODE_TRIES) until every recovered unit
       passes its CRC.
    Returns ({unit index: segments}, (block day, K, coded), stats); only CRC-verified units are returned."""
    stats = {"header_rejects": 0, "crc_fails": 0, "decode_tries": 0}
    parsed = []
    for m in msgs:
        h = frame.parse_header(m, rx_day)
        if h.version != frame.VERSION or h.K == 0:
            stats["header_rejects"] += 1
            continue
        parsed.append((h, bytes(m[frame.HEADER_BYTES:])))
    if not parsed:
        return {}, None, stats
    keys = Counter((h.block_day, h.K, h.coded, h.fountain) for h, _ in parsed)
    (day, K, coded, fnt), _ = keys.most_common(1)[0]
    cands = {}
    for h, pl in parsed:
        if (h.block_day, h.K, h.coded, h.fountain) != (day, K, coded, fnt):
            stats["header_rejects"] += 1
            continue
        lst = cands.setdefault(h.index, [])
        if pl not in lst:
            lst.append(pl)
    verified = {}
    for i in sorted(i for i in cands if i < K):
        for pl in cands[i]:
            segs = frame.decode_unit(pl, frame.Header(day, i, K, coded), i)
            if segs is None:
                stats["crc_fails"] += 1
            else:
                verified[i] = (pl, segs)
                break
    if coded and len(verified) < K:
        parity = sorted(i for i in cands if i >= K)
        need = K - len(verified)
        done = False
        for combo in itertools.combinations(parity, need) if len(parity) >= need else []:
            for choice in itertools.product(*[cands[j] for j in combo]):
                if stats["decode_tries"] >= MAX_DECODE_TRIES:
                    break
                stats["decode_tries"] += 1
                rows = {i: list(v[0]) for i, v in verified.items()}
                rows.update({j: list(pl) for j, pl in zip(combo, choice)})
                full = fountain.decode(rows, K, day) if fnt else rs.decode(rows, K, max(max(rows) + 1, K))
                if full is None:
                    continue
                segs = [frame.decode_unit(bytes(u), frame.Header(day, i, K, coded), i) for i, u in enumerate(full)]
                if all(sg is not None for sg in segs):
                    verified = {i: (bytes(u), sg) for i, (u, sg) in enumerate(zip(full, segs))}
                    done = True
                    break
            if done or stats["decode_tries"] >= MAX_DECODE_TRIES:
                break
    return {i: sg for i, (_, sg) in verified.items()}, (day, K, coded), stats


def receive(msgs, rx_day, with_stats=False):
    """Bytes that arrived (any order) -> (received positions, last position or None, bound, crc failures).
    Single record day per block (day offset 0); multi-day blocks: receive_multi."""
    units, hdr, stats = recover_units(msgs, rx_day)
    received, last, bound = {}, None, False
    for i in sorted(units):
        for s in units[i]:
            bound = s.bound
            for k, v in enumerate(s.values):
                received[s.first + k] = v
            if s.last:
                last = s.first + len(s.values) - 1
    out = (received, last, bound, stats["crc_fails"])
    return out + (stats,) if with_stats else out


def outcome(rd, sent, arrived):
    """arrived: boolean mask over transmissions. Returns dict with Phi (fully certified), cert (certified
    reading share), F (oracle: within tolerance), worst (oracle). Decoding runs on the bytes once per
    distinct set of arrived message indices (deterministic, so cached)."""
    key = frozenset(i for i, ok in zip(sent.idx, arrived) if ok)
    if key not in sent.cache:
        got = {}
        for i, m, ok in zip(sent.idx, sent.msgs, arrived):
            if ok:
                got[i] = m
        day = day_number(rd.day)
        rx, last, bound, fails = receive(list(got.values()), day)
        cert, full = record.certify(rx, rd.n_of, bound, last)
        e = record.errors(rd.channels, rx)
        worst = max(float(np.nanmax(v)) if np.isfinite(v).all() else np.inf for v in e.values())
        sent.cache[key] = {"Phi": bool(full), "cert": sum(c.sum() for c in cert.values()) / rd.raw_values,
                           "F": worst <= SLACK, "worst": worst, "crc_fail": fails}
    return sent.cache[key]


def receive_multi(msgs, rx_day):
    """Bytes of ONE block that arrived -> {record day: (positions {pos: value}, last position or None, bound)}.
    Segments carry the record day as an offset from the block day (Step 7); decoding as in recover_units."""
    units, hdr, _ = recover_units(msgs, rx_day)
    out = {}
    for i in sorted(units):
        for s in units[i]:
            rx, last, _ = out.get(hdr[0] - s.day_offset, ({}, None, False))
            for k, v in enumerate(s.values):
                rx[s.first + k] = v
            if s.last:
                last = s.first + len(s.values) - 1
            out[hdr[0] - s.day_offset] = (rx, last, s.bound)
    return out
