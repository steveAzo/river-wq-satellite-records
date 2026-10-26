"""Tests of the per-channel loader (src/p3/loader.py). Run from Paper3/: python -m pytest tests -q"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from p3 import loader  # noqa: E402

nan = np.nan


def test_bridge_fills_short_inner_runs_only():
    v = np.array([1.0, nan, 3.0, nan, nan, 6.0, nan, nan, nan, 10.0, nan])
    out = loader.bridge(v)
    assert out[:6].tolist() == [1, 2, 3, 4, 5, 6]
    assert np.isnan(out[6:9]).all()          # a run of three is not partly filled
    assert np.isnan(out[10])                 # no right neighbour


def write(tmp_path, frame):
    p = tmp_path / "site01.csv"
    frame.reset_index().to_csv(p, index=False)
    return str(p)


def series(start, end, step, value=10.0):
    idx = pd.date_range(start, end, freq=f"{step}min", tz="UTC", inclusive="left")
    return pd.Series(value + 0.01 * np.arange(len(idx)), index=idx)


def test_mixed_intervals_and_seasonal_channel(tmp_path):
    T = series("2023-06-01", "2023-06-04", 5)                    # 5-min temperature
    DO = series("2023-06-01", "2023-06-04", 15, 8.0)             # 15-min DO
    pH = series("2023-06-02", "2023-06-04", 15, 7.5)             # pH installed on 2 June
    df = pd.DataFrame({"T": T}).join(pd.DataFrame({"DO_mgL": DO, "pH": pH}), how="outer")
    df.index.name = "t"
    days = loader.load_site_records(write(tmp_path, df))
    assert [str(d.day.date()) for d in days] == ["2023-06-01", "2023-06-02", "2023-06-03"]
    assert days[0].params == ("T", "DO") and days[1].params == ("T", "DO", "pH")
    assert days[1].steps == {"T": 5, "DO": 15, "pH": 15}
    assert days[1].n_of == {"T": 288, "DO": 96, "pH": 96}
    assert np.allclose(days[1].channels[0].x[:2], T.loc["2023-06-02"].iloc[:2])


def test_gap_across_midnight_is_not_bridged(tmp_path):
    T = series("2023-06-01", "2023-06-04", 15)
    T = T.drop(T.index[(T.index >= "2023-06-01 23:30") & (T.index < "2023-06-02 00:15")])  # 23:30, 23:45, 00:00
    df = pd.DataFrame({"T": T})
    df.index.name = "t"
    audit = []
    days = loader.load_site_records(write(tmp_path, df), audit=audit)
    status = {(d, s) for _, d, _, s, _ in audit}
    assert ("2023-06-02", "gap") in status and ("2023-06-01", "gap") in status
    assert [str(d.day.date()) for d in days] == ["2023-06-03"]


def test_two_missing_across_midnight_are_bridged(tmp_path):
    T = series("2023-06-01", "2023-06-04", 15)
    T = T.drop(T.index[(T.index >= "2023-06-01 23:45") & (T.index < "2023-06-02 00:15")])  # 23:45, 00:00
    df = pd.DataFrame({"T": T})
    df.index.name = "t"
    days = loader.load_site_records(write(tmp_path, df))
    d2 = next(d for d in days if str(d.day.date()) == "2023-06-02")
    full = series("2023-06-01", "2023-06-04", 15)
    assert np.isclose(d2.channels[0].x[0], full.loc["2023-06-02 00:00"])   # linear bridge is exact here


def test_interval_change_midyear(tmp_path):
    T = pd.concat([series("2023-06-01", "2023-06-02", 15), series("2023-06-02", "2023-06-03", 5)])
    df = pd.DataFrame({"T": T})
    df.index.name = "t"
    days = loader.load_site_records(write(tmp_path, df))
    assert [d.steps["T"] for d in days] == [15, 5]
