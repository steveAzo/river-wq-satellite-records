"""Packet-level multi-day replay (revision Step 7; review M9, E4; plan: docs/STEP7_PLAN.md).

A schedule is the list of daily blocks a node transmits over a site's year. Because the link is one-way, the
schedule depends only on the data, so it is built once on bytes and reused for every loss draw. Each block keeps,
for every unit it carries, the record days and planned positions inside it, so the server's recovery can be
replayed quickly from an arrival mask (decoding rule) and checked against real byte decoding (`check_bytes`).

Record days and blocks are numbered in days since 2000-01-01 (delivery.day_number).
"""
import math
from dataclasses import dataclass, field

import numpy as np

from . import delivery, frame, rs

W = 7          # tag / repetition buffer: record days d are eligible in blocks d+1 .. d+W
MAX_AGE = 63   # frame limit on the day offset


@dataclass
class Block:
    day: int
    coded: bool
    K: int
    tx: list                 # per transmission: message index (coded) or unit index (uncoded)
    msgs: list               # bytes per transmission
    content: list            # per unit index: [(record day, first, count, last, bound)]


@dataclass
class Schedule:
    name: str
    Q: int
    blocks: list
    backlog: dict = field(default_factory=dict)   # block day -> units still waiting after the block (buf_rec)
    dropped: set = field(default_factory=set)     # record days dropped by the 63-day limit before being sent


def _content(segs, b):
    return [(b - s.day_offset, s.first, len(s.values), s.last, s.bound) for s in segs]


def _coded_block(b, unit_segs, Q):
    K = len(unit_segs)
    hdr = [frame.Header(b, i, K) for i in range(Q)]
    units = [list(frame.encode_unit(s, hdr[i], i)) for i, s in enumerate(unit_segs)]
    coded = rs.encode(units, Q) if Q > K else units
    return Block(b, True, K, list(range(len(coded))), [frame.message(hdr[i], c) for i, c in enumerate(coded)],
                 [_content(s, b) for s in unit_segs])


def _uncoded_block(b, unit_segs, picks):
    """unit_segs: distinct units of the block; picks: unit index per transmission."""
    K = len(unit_segs)
    msgs = [frame.message(frame.Header(b, i, K, False), frame.encode_unit(s, frame.Header(b, i, K, False), i))
            for i, s in enumerate(unit_segs)]
    return Block(b, False, K, list(picks), [msgs[i] for i in picks], [_content(s, b) for s in unit_segs])


def buf_rec(plans, first, last, Q, rho):
    """FIFO backlog of record days; one block per day with K = min(units waiting, ceil(rho Q)) + Q - K parity."""
    cap = max(1, math.ceil(rho * Q))
    queue, blocks, backlog, dropped = [], [], {}, set()
    for b in range(first + 1, last + MAX_AGE + 2):
        if b - 1 in plans:
            vals, bound = plans[b - 1]
            queue.append([b - 1, vals, bound, 0])
        for it in [q for q in queue if b - q[0] > MAX_AGE]:
            dropped.add(it[0])
            queue.remove(it)
        items = [[b - d, vals, bound, nxt] for d, vals, bound, nxt in queue]
        units = frame.pack(items, cap)
        for q, it in zip(queue, items):
            q[3] = it[3]
        queue = [q for q in queue if q[3] < len(q[1])]
        backlog[b] = sum(-(-(len(q[1]) - q[3]) // frame.unit_capacity()) for q in queue)
        if units:
            blocks.append(_coded_block(b, units, Q))
        elif b > last + 1 and not queue:
            break
    return Schedule(f"buf_rec_{rho:.2f}", Q, blocks, backlog, dropped)


def daily_rec(plans, first, last, Q):
    """Record-first without a buffer: day d's record in the block of day d + 1 (K = D1) if it fits Q units;
    otherwise its first Q units, uncoded (partial certificates only)."""
    blocks = []
    for b in range(first + 1, last + 2):
        if b - 1 not in plans:
            continue
        vals, bound = plans[b - 1]
        units = frame.pack([[1, vals, bound, 0]], 10 ** 6)
        if len(units) <= Q:
            blocks.append(_coded_block(b, units, Q))
        else:
            blocks.append(_uncoded_block(b, units[:Q], list(range(Q))))
    return Schedule("daily_rec", Q, blocks)


def _day_units(plans):
    """Units of each record day packed alone (segments with a placeholder offset 0)."""
    return {d: frame.pack([[0, vals, bound, 0]], 10 ** 6) for d, (vals, bound) in plans.items()}


def _shift(segs, off):
    return [frame.Segment(off, s.first, s.values, s.last, s.bound) for s in segs]


def rotation(plans, first, last, Q, policy, seed=0, name=None):
    """7-day buffer of whole record days; Q daily transmissions cycle (policy 'cyclic') or pick pseudo-randomly
    with replacement (policy 'random', CTD-SRDL practice) among the buffered units; uncoded."""
    per_day = _day_units(plans)
    rng = np.random.default_rng(seed)
    blocks, ptr = [], 0
    for b in range(first + 1, last + W + 1):
        buf = [(d, u) for d in range(b - W, b) if d in per_day for u in range(len(per_day[d]))]
        if not buf:
            continue
        if policy == "cyclic":
            picks = [buf[(ptr + i) % len(buf)] for i in range(Q)]
            ptr = (ptr + Q) % len(buf)
        else:
            picks = [buf[i] for i in rng.integers(0, len(buf), Q)]
        distinct = sorted(set(picks))
        idx = {x: i for i, x in enumerate(distinct)}
        segs = [_shift(per_day[d][u], b - d) for d, u in distinct]
        blocks.append(_uncoded_block(b, segs, [idx[x] for x in picks]))
    return Schedule(name or f"rotation_{policy}", Q, blocks)


# ---------------------------------------------------------------- server replay
def recovered_units(block, arrived):
    """Decoding rule: unit indices the server recovers from the arrived transmissions of one block."""
    got = {i for i, ok in zip(block.tx, arrived) if ok}
    if block.coded:
        return set(range(block.K)) if len(got) >= block.K else {i for i in got if i < block.K}
    return got


def replay(sched, masks, record_days):
    """masks: (draws, total transmissions) arrival matrix over the schedule's transmissions in order.
    Returns completion[draw] = {record day: block day of full certification}."""
    out = []
    for m in masks:
        pos, last, bound, done, k = {}, {}, {}, {}, 0
        for blk in sched.blocks:
            n = len(blk.tx)
            for u in recovered_units(blk, m[k:k + n]):
                for d, first, cnt, is_last, bd in blk.content[u]:
                    if d in done:
                        continue
                    s = pos.setdefault(d, set())
                    s.update(range(first, first + cnt))
                    bound[d] = bd
                    if is_last:
                        last[d] = first + cnt - 1
                    if d in last and bound[d] and len(s) == last[d] + 1:
                        done[d] = blk.day
            k += n
        out.append(done)
    return out


def check_bytes(sched, mask):
    """Decode every block of one draw from its bytes and compare with the decoding rule. Returns mismatches."""
    bad, k = 0, 0
    for blk in sched.blocks:
        n = len(blk.tx)
        arr = mask[k:k + n]
        rule = {(d, first + j) for u in recovered_units(blk, arr) for d, first, cnt, _, _ in blk.content[u]
                for j in range(cnt)}
        got = delivery.receive_multi([msg for msg, ok in zip(blk.msgs, arr) if ok], blk.day)
        bytes_ = {(d, p) for d, (rx, _, _) in got.items() for p in rx}
        bad += rule != bytes_
        k += n
    return bad
