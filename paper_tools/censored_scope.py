"""Scope of review finding Fatal 1 (outside review, 2026-11-11): how often does a channel-day contain a censored reading (a reading
outside the quantiser range, code 0 or 8191), and how often is a censored reading kept in the plan (so that it can pull a
reconstruction to the range edge)? Counts only; reads the cleaned records and cached plans. Post-hoc, descriptive.
Run from Paper3/: python -I paper_tools/censored_scope.py <folder> <tag> [<folder> <tag> ...]"""
import glob
import os
import sys

import numpy as np

sys.path.insert(0, "src")
from p3 import frame  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402

for folder, tag in zip(sys.argv[1::2], sys.argv[2::2]):
    days = cens_days = kept_cens_days = 0
    per_param = {}
    sites_with = set()
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        if not os.path.exists(f"results/{tag}/plans/{os.path.basename(path)[:-4]}.pkl"):
            continue
        site, items, _ = prepare_items(path, tag)
        for it in items:
            days += 1
            any_c = any_k = False
            for c in it["rd"].channels:
                sat = frame.saturated(frame.quantise(c.param, c.x))
                if sat.any():
                    any_c = True
                    per_param[c.param] = per_param.get(c.param, 0) + 1
            if any(frame.saturated(code) for _p, _s, code in it["vals"]):
                any_k = True
            cens_days += any_c
            kept_cens_days += any_k
            if any_c:
                sites_with.add(site)
    print(f"{folder} ({tag}): {days} analysed days; days with a censored reading {cens_days} "
          f"({cens_days / max(days, 1):.4f}); days with a censored kept value {kept_cens_days}; "
          f"channel-days by parameter {per_param}; sites {len(sites_with)}")
