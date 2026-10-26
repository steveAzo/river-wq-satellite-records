"""Deterministic synthetic record day for the delivery tests and golden vectors (no data files needed).
Regenerate the golden file (only on a deliberate frame change): python tests/golden_day.py"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import delivery, record  # noqa: E402
from p3.data import tolerance  # noqa: E402
from p3.loader import RecordDay  # noqa: E402

GOLDEN = os.path.join(os.path.dirname(__file__), "golden", "frame_v1.json")


def synthetic_day(n=96, seed=7, scale=1.0):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    x = {"T": np.round(20 + 2 * np.sin(2 * np.pi * (t - 30) / n) + scale * np.cumsum(rng.normal(0, 0.03, n)), 1),
         "DO": np.round(8 + 1.5 * np.sin(2 * np.pi * (t - 40) / n) + scale * np.cumsum(rng.normal(0, 0.03, n)), 1),
         "pH": np.round(7.6 + 0.3 * np.sin(2 * np.pi * (t - 40) / n), 1),
         "EC": np.round(450 + 30 * np.sin(2 * np.pi * t / n) + scale * np.cumsum(rng.normal(0, 2, n)))}
    chs = [record.Channel(p, x[p].astype(float), tolerance(p, x[p])) for p in ("T", "DO", "pH", "EC")]
    return RecordDay("golden", pd.Timestamp("2023-07-14"), chs, {p: 15 for p in x})


def golden_cases():
    rd = synthetic_day()
    enc = record.Encoder(rd.channels)
    return rd, {"mds_K4_Q6": delivery.mds(rd, enc, 6, 4), "repeat2_Q6": delivery.repeat(rd, enc, 6, 2),
                "every_k_Q6": delivery.every_k(rd, 6), "tag_Q6": delivery.tag(rd, 6, 0.5, seed=3)}


if __name__ == "__main__":
    rd, cases = golden_cases()
    out = {k: {"msgs": [m.hex() for m in s.msgs], "idx": [int(i) for i in s.idx], "bound": s.bound,
               "planned": [list(v) for v in s.planned]} for k, s in cases.items()}
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    json.dump(out, open(GOLDEN, "w"), indent=1)
    print("wrote", GOLDEN, {k: (len(v["msgs"]), len(v["planned"]), v["bound"]) for k, v in out.items()})
