"""Tests of src/p3v3/prepare_cohort4.py with fake fetch and clean functions (no network, no cohort data).
Run from Paper3/: python -m pytest -q -p no:cacheprovider tests/v3/test_prepare_cohort4.py"""
import json
import os
import subprocess
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "src", "p3v3"))
import confirm4 as c4  # noqa: E402
import prepare_cohort4 as pc  # noqa: E402


def test_settings():
    assert (pc.START, pc.END) == ("2022-01-01", "2022-12-31")
    assert pc.OUT == "data/clean/usgs_new4_2022" and pc.CLEAN_SEAL == pc.OUT + ".md5"
    assert pc.SELECTION == c4.SELECTION and pc.FREEZE_TAG == c4.FREEZE_TAG and pc.FREEZE_RECORD == c4.FREEZE_RECORD


def test_refuses_before_freeze(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)                             # no repository, no tag
    with pytest.raises(SystemExit, match="freeze comes first"):
        pc.check_frozen()


def test_refuses_without_committed_record(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    run = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True)
    run("init", "-q")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
    run("tag", "confirm4-freeze")
    with pytest.raises(SystemExit, match="freeze comes first"):
        pc.check_frozen()                                   # tag present, record missing
    os.makedirs("docs")
    open("docs/FREEZE4.md", "w").write("x")
    run("add", "docs/FREEZE4.md")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "freeze")
    pc.check_frozen()                                       # passes
    open("docs/FREEZE4.md", "w").write("changed")
    with pytest.raises(SystemExit, match="freeze comes first"):
        pc.check_frozen()                                   # uncommitted change


def test_main_fetches_cleans_and_seals_exactly_the_folder(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    os.makedirs("results/confirm4")
    pd.DataFrame({"site_no": ["0001", "0002", "0003", "0004"], "selected": [True, True, False, True]}).to_csv(pc.SELECTION, index=False)
    fetched = []

    def fetch(site, start, end):
        fetched.append(site)
        os.makedirs("data/raw/usgs", exist_ok=True)
        rows = [] if site == "0004" else [("2022-01-01T00:00", "temp_c", 1.0, "A", "")]
        pd.DataFrame(rows, columns=["time", "param", "value", "qualifiers", "method"]).to_csv(
            f"data/raw/usgs/{site}_{start}_{end}.csv", index=False)

    def clean(raw):
        return pd.DataFrame({"t": [1]}), {"file": raw.name, "raw_values": 1, "approved_values": 1, "timestamps": 1, "median_step_min": 15}
    pc.main(fetch, clean)
    assert fetched == ["0001", "0002", "0004"]
    assert sorted(os.listdir(pc.OUT)) == ["0001.csv", "0002.csv"]
    assert len(open(pc.RAW_SEAL).read().splitlines()) == 3
    c4.check_seal_covers(pc.CLEAN_SEAL, pc.OUT)             # the driver's folder check accepts the clean seal
    from data.seal import verify
    assert verify(pc.CLEAN_SEAL) and verify(pc.RAW_SEAL)
    q = json.loads(open(pc.QUALITY).read())
    assert q["excluded_no_data"] == ["0004"] and len(q["files"]) == 2
    pc.main(fetch, clean)                                   # resumable: no second download
    assert fetched == ["0001", "0002", "0004"]
