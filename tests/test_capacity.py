"""Frame v2 bit budget (src/p3/capacity.py) against the slot model used by the prototypes."""
import itertools
import os
import sys
from math import ceil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import capacity as cp  # noqa: E402

VALS = {"DO": 1, "pH": 2, "T": 1, "EC": 2}


def test_record_only_is_five_values():
    assert cp.record_values_per_message([]) == 5


def test_frame_v2_never_holds_fewer_record_values_than_the_slot_model_at_equal_protection():
    for r in range(1, 5):
        for objs in itertools.combinations(VALS, r):
            hv = sum(VALS[o] for o in objs)
            c_w = min(4, ceil(hv / 2))
            k = ceil(hv / c_w)                      # the dimension the slot model gives the group
            exact = cp.record_values_per_message([(list(objs), k)])
            assert exact >= cp.slot_model_values(c_w), (objs, k, exact)


def test_single_do_witness_costs_one_value_only():
    assert cp.record_values_per_message([(["DO"], 1)]) == 4
    assert cp.group_message_bits(["DO"], 1) == 8 + 16      # one 13-bit code, rounded up to two bytes


def test_spare_bits_are_nonnegative_for_a_full_unit_and_positive_for_a_short_one():
    assert cp.spare_bits(5, []) >= 0
    assert cp.spare_bits(3, []) >= 2 * 24
