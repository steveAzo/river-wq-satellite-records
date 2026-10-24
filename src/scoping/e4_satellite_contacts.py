"""E4: real satellite-IoT contact windows over river sites (Kinéis constellation, TLE snapshot 2026-10-16).

Propagates every satellite in data/tle/kineis_2026-10-16.tle with SGP4 at 10-s steps for 7 days and
reports, per ground site, the passes above a minimum elevation: passes per day, pass duration, and the
gaps between passes (how long a node buffers between contacts). Sites: Weija intake (Ghana) and two
galamsey-affected rivers (Pra at Twifo Praso, Ankobra at Prestea), plus a mid-latitude USGS site for
contrast (Delaware at Trenton). Coordinates are approximate (to ~0.01 deg), which is ample at LEO scale.

Run from Paper3/: python -I src/scoping/e4_satellite_contacts.py [min_elev_deg=10]
Output: results/scoping/e4_contacts.csv (one row per pass) and a printed summary.
"""
import math
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sgp4.api import Satrec, jday

SITES = {
    "Weija intake (GH)": (5.565, -0.335),
    "Pra, Twifo Praso (GH)": (5.610, -1.550),
    "Ankobra, Prestea (GH)": (5.430, -2.140),
    "Delaware, Trenton (US)": (40.221, -74.778),
}
A, F = 6378.137, 1 / 298.257223563  # WGS-84


def ecef_site(lat, lon, h=0.0):
    la, lo = math.radians(lat), math.radians(lon)
    e2 = F * (2 - F)
    n = A / math.sqrt(1 - e2 * math.sin(la) ** 2)
    return np.array([(n + h) * math.cos(la) * math.cos(lo), (n + h) * math.cos(la) * math.sin(lo),
                     (n * (1 - e2) + h) * math.sin(la)])


def gmst(jd_ut1):
    t = (jd_ut1 - 2451545.0) / 36525.0
    g = 67310.54841 + (876600 * 3600 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t ** 3
    return math.radians((g % 86400) / 240.0)


def load_tle(path):
    lines = [l.rstrip() for l in open(path, encoding="utf-8") if l.strip()]
    return [(lines[i].strip(), Satrec.twoline2rv(lines[i + 1], lines[i + 2])) for i in range(0, len(lines) - 2, 3)]


def main():
    min_el = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    sats = load_tle("data/tle/kineis_2026-10-16.tle")
    t0 = datetime(2026, 10, 17, tzinfo=timezone.utc)
    step, days = 10, 7
    times = [t0 + timedelta(seconds=s) for s in range(0, days * 86400, step)]
    jd = np.array([sum(jday(t.year, t.month, t.day, t.hour, t.minute, t.second)) for t in times])
    theta = np.array([gmst(j) for j in jd])
    rows = []
    for sname, (lat, lon) in SITES.items():
        r_site = ecef_site(lat, lon)
        up = r_site / np.linalg.norm(r_site)
        for name, sat in sats:
            jd_i = np.floor(jd - 0.5) + 0.5
            fr = jd - jd_i
            err, r, _ = sat.sgp4_array(jd_i, fr)
            r = np.asarray(r)
            c, s = np.cos(theta), np.sin(theta)
            ecef = np.stack([c * r[:, 0] + s * r[:, 1], -s * r[:, 0] + c * r[:, 1], r[:, 2]], axis=1)  # TEME -> ~ECEF (PEF)
            d = ecef - r_site
            el = np.degrees(np.arcsin((d @ up) / np.linalg.norm(d, axis=1)))
            vis = (el >= min_el) & (np.asarray(err) == 0)
            edges = np.flatnonzero(np.diff(np.concatenate(([0], vis.astype(int), [0]))))
            for a, b in zip(edges[::2], edges[1::2]):
                rows.append({"site": sname, "sat": name, "start": times[a], "dur_s": (b - a) * step, "max_el": el[a:b].max()})
    out = pd.DataFrame(rows).sort_values(["site", "start"])
    os.makedirs("results/scoping", exist_ok=True)
    out.to_csv("results/scoping/e4_contacts.csv", index=False)
    print(f"Kinéis, {len(sats)} satellites, 7 days, elevation >= {min_el} deg")
    for sname, g in out.groupby("site"):
        # merge overlapping passes of different satellites into contact intervals
        iv = sorted((r.start, r.start + timedelta(seconds=r.dur_s)) for r in g.itertuples())
        merged = []
        for s0, e0 in iv:
            if merged and s0 <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e0)
            else:
                merged.append([s0, e0])
        gaps = np.array([(merged[i + 1][0] - merged[i][1]).total_seconds() / 3600 for i in range(len(merged) - 1)])
        dur = np.array([(e - s).total_seconds() / 60 for s, e in merged])
        print(f"\n{sname}: {len(g)/days:.1f} passes/day, {len(merged)/days:.1f} contacts/day; "
              f"contact min median {np.median(dur):.1f} (p10 {np.percentile(dur,10):.1f}); visible {dur.sum()/(days*1440)*100:.1f}% of time")
        print(f"   gap between contacts h: median {np.median(gaps):.2f}, p90 {np.percentile(gaps,90):.2f}, max {gaps.max():.2f}")


if __name__ == "__main__":
    main()
