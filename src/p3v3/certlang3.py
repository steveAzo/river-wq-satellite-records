"""Version 3 guarded decision bounds (finding A5 of docs/REVIEW_FINDINGS_2026-11-09.md). New file; src/p3/certlang.py is frozen
and unchanged.

certlang.min_bounds and certlang.max_bounds take the minimum or maximum over the uncensored readings and raise ValueError when
every reading of the channel-day is flagged censored (an empty set). This is reachable by a forged record that covers every slot
with censored codes, and in principle by a day whose readings are all censored. The day's minimum and maximum over uncensored
readings are then undefined, so the guarded versions return the information-free interval (-inf, inf), which every decision rule
treats as undetermined (rolling_mean_decision gives -1). A witness received for such a day contradicts the record and is
ignored for the same reason. With at least one uncensored reading the result equals certlang's, bit for bit.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.join(HERE, "..") not in sys.path:
    sys.path.insert(0, os.path.join(HERE, ".."))
from p3 import certlang as cl  # noqa: E402

INF = cl.INF
UNDEFINED = (-INF, INF)


def min_bounds(K):
    """Interval of the day's minimum over uncensored readings; (-inf, inf) when there is none."""
    if not K.live().any():
        return UNDEFINED
    return cl.min_bounds(K)


def max_bounds(K):
    """Interval of the day's maximum over uncensored readings; (-inf, inf) when there is none."""
    if not K.live().any():
        return UNDEFINED
    return cl.max_bounds(K)


def day_max_bounds(K):
    """Daily maximum interval for the rolling statistic (7DADM); (-inf, inf) for a day without an uncensored reading."""
    return max_bounds(K)
