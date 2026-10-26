"""Per-channel record-day loader (revision Step 4a; fixes the loader artefacts of docs/COHORT_AUDIT.md).

Each parameter keeps its own native interval, which may change during the year. For every UTC day and
channel: the interval is the most common spacing of that day's readings (one of 5, 10, 15, 20, 30, 60 min);
the day's grid starts at 00:00 UTC; a run of at most two missing readings with valid neighbours on both
sides is bridged linearly (neighbours may lie in the adjacent days); any other gap makes the channel-day
ineligible. A record day carries the channels that are eligible on that day (seasonal sensors and coarser
channels are no longer dropped for the whole year). Tolerances: data.tolerance (USGS TM 1-D3).
"""
import glob
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import COLUMN, PARAMS, tolerance
from .record import Channel

STEPS = (5, 10, 15, 20, 30, 60)
MARGIN = 3


@dataclass
class RecordDay:
    site: str
    day: pd.Timestamp           # UTC date
    channels: list              # [record.Channel] in planned order (T, DO, pH, EC)
    steps: dict = field(default_factory=dict)   # {param: native interval, min}

    @property
    def params(self):
        return tuple(c.param for c in self.channels)

    @property
    def n_of(self):
        return {c.param: c.n for c in self.channels}

    @property
    def raw_values(self):
        return sum(c.n for c in self.channels)


def bridge(v, max_run=2):
    """Fill NaN runs of length <= max_run that have finite values on both sides; others stay NaN."""
    v = v.copy()
    isn = np.isnan(v)
    i, n = 0, len(v)
    while i < n:
        if not isn[i]:
            i += 1
            continue
        j = i
        while j < n and isn[j]:
            j += 1
        if i > 0 and j < n and j - i <= max_run:
            v[i:j] = np.interp(np.arange(i, j), [i - 1, j], [v[i - 1], v[j]])
        i = j
    return v


def channel_days(s, tolset="excellent", param=None):
    """s: Series of readings indexed by UTC time (NaN dropped). Yields (day, status, values or None, step)."""
    if s.empty:
        return
    days = s.index.floor("D")
    for d, grp in s.groupby(days):
        if len(grp) < 2:
            yield d, "few", None, None
            continue
        diffs = np.diff(grp.index.asi8) / 6e10
        vals, cnt = np.unique(np.round(diffs).astype(int), return_counts=True)
        step = int(vals[np.argmax(cnt)])
        if step not in STEPS:
            yield d, "irregular", None, None
            continue
        n = 1440 // step
        grid = d + pd.to_timedelta(np.arange(-MARGIN, n + MARGIN) * step, unit="min")
        v = bridge(s.reindex(grid).to_numpy(float))[MARGIN:MARGIN + n]
        if np.isnan(v).any():
            yield d, "gap", None, step
        else:
            yield d, "eligible", v, step


def load_site_records(path, tolset="excellent", audit=None):
    """-> [RecordDay] (days with at least one eligible channel). audit: optional list collecting
    (site, day, param, status, step) for every channel-day seen."""
    site = os.path.basename(path)[:-4]
    df = pd.read_csv(path, parse_dates=["t"]).set_index("t").sort_index()
    df = df[~df.index.duplicated()]
    per_day = {}
    for p in PARAMS:
        if COLUMN[p] not in df:
            continue
        s = df[COLUMN[p]].dropna()
        for d, status, v, step in channel_days(s, tolset, p):
            if audit is not None:
                audit.append((site, str(d.date()), p, status, step))
            if status == "eligible":
                per_day.setdefault(d, []).append((p, v, step))
    out = []
    for d in sorted(per_day):
        chs = sorted(per_day[d], key=lambda c: PARAMS.index(c[0]))
        out.append(RecordDay(site, d.tz_localize(None) if d.tzinfo else d,
                             [Channel(p, v, tolerance(p, v, tolset)) for p, v, _ in chs],
                             {p: step for p, _, step in chs}))
    return out


def load_records(folder, tolset="excellent", audit=None):
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        out += load_site_records(f, tolset, audit)
    return out
