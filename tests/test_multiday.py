"""Packet-level multi-day replay (src/p3/multiday.py). Run from Paper3/: python -m pytest tests -q"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import multiday as md  # noqa: E402


def vals(n):
    """n planned values over two channels, in planned order."""
    a = n // 2
    return [("T", s, 1000 + s) for s in range(a)] + [("DO", s, 2000 + s) for s in range(n - a)]


def plans_of(sizes, start=9000):
    return {start + i: (vals(n), True) for i, n in enumerate(sizes) if n}


def all_arrive(s):
    return np.ones((1, sum(len(b.tx) for b in s.blocks)), bool)


def test_buf_rec_delivers_each_position_once_in_fifo_order():
    plans = plans_of([3, 12, 40, 7, 0, 5])
    s = md.buf_rec(plans, 9000, 9005, Q=6, rho=0.5)
    seen = {}
    for blk in s.blocks:
        assert blk.K <= 3 and len(blk.tx) == 6
        for unit in blk.content:
            for d, first, cnt, last, bound in unit:
                for p in range(first, first + cnt):
                    assert (d, p) not in seen
                    seen[(d, p)] = blk.day
    assert set(seen) == {(d, p) for d, (v, _) in plans.items() for p in range(len(v))}
    done = md.replay(s, all_arrive(s), plans)[0]
    assert set(done) == set(plans)
    assert all(done[d] >= d + 1 for d in done)
    order = sorted(plans)
    assert [done[d] for d in order] == sorted(done[d] for d in order)       # FIFO: completion in order


def test_rho_one_equals_daily_record_first_when_days_fit():
    plans = plans_of([3, 12, 9, 7, 5])
    a = md.replay(md.buf_rec(plans, 9000, 9004, 6, 1.0), np.ones((1, 10 ** 4), bool), plans)[0]
    b = md.replay(md.daily_rec(plans, 9000, 9004, 6), np.ones((1, 10 ** 4), bool), plans)[0]
    assert a == b == {d: d + 1 for d in plans}


def test_big_day_is_split_and_later_days_wait():
    plans = plans_of([60, 3, 3])          # 12 units on day 0 at Q = 6, rho = 1/2 -> 3 units per block
    done = md.replay(md.buf_rec(plans, 9000, 9002, 6, 0.5), np.ones((1, 10 ** 4), bool), plans)[0]
    assert done[9000] == 9004 and done[9001] == 9005 and done[9002] == 9005


def test_days_older_than_63_are_dropped_and_never_certified():
    plans = plans_of([40] * 80)           # 8 units a day at Q = 1: the backlog grows without bound
    s = md.buf_rec(plans, 9000, 9079, 1, 1.0)
    assert s.dropped
    done = md.replay(s, all_arrive(s), plans)[0]
    assert not (set(done) & s.dropped)


def test_cyclic_rotation_delivers_within_the_window():
    plans = plans_of([12, 3, 20, 7])
    s = md.rotation(plans, 9000, 9003, 6, "cyclic")
    done = md.replay(s, all_arrive(s), plans)[0]
    assert set(done) == set(plans) and all(1 <= done[d] - d <= md.W for d in done)


def test_a_lost_block_loses_its_content_for_good():
    plans = plans_of([3, 3, 3])
    s = md.buf_rec(plans, 9000, 9002, 6, 1.0)
    m = all_arrive(s)
    m[0, :6] = False                      # the whole first block (record day 9000) is lost
    done = md.replay(s, m, plans)[0]
    assert 9000 not in done and done[9001] == 9002


@pytest.mark.parametrize("which", ["buf", "daily", "cyclic", "random"])
def test_decoding_rule_matches_byte_decoding(which):
    plans = plans_of([3, 12, 40, 7, 0, 5, 18])
    s = {"buf": md.buf_rec(plans, 9000, 9006, 6, 0.5), "daily": md.daily_rec(plans, 9000, 9006, 6),
         "cyclic": md.rotation(plans, 9000, 9006, 6, "cyclic"),
         "random": md.rotation(plans, 9000, 9006, 6, "random", seed=4)}[which]
    rng = np.random.default_rng(1)
    n = sum(len(b.tx) for b in s.blocks)
    for _ in range(20):
        assert md.check_bytes(s, rng.random(n) >= 0.4) == 0


def test_node_outages_do_not_change_any_other_days_bytes():
    """Step 9: with the daily record-first design, removing record days (node or sensor outage) leaves the
    transmitted bytes of every remaining day unchanged, so outages do not propagate."""
    plans = plans_of([3, 12, 9, 7, 5, 20, 4, 6])
    full = {b.day: b.msgs for b in md.daily_rec(plans, 9000, 9007, 6).blocks}
    for gone in ({9001}, {9002, 9003}, {9000, 9007}, {9004, 9005, 9006}):
        part = {d: v for d, v in plans.items() if d not in gone}
        got = {b.day: b.msgs for b in md.daily_rec(part, 9000, 9007, 6).blocks}
        assert set(got) == {d + 1 for d in part}
        assert all(got[b] == full[b] for b in got)
