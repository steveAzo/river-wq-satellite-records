"""Tests of the version 3 confirmation driver src/p3v3/confirm4.py and the freeze writer src/p3v3/freeze4.py (no cohort data used).
Run from Paper3/: python -m pytest -q -p no:cacheprovider tests/v3/test_confirm4.py"""
import os
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "src", "p3v3"))
import confirm4 as c4  # noqa: E402
import frame3 as f3  # noqa: E402
import freeze4 as fz  # noqa: E402


@pytest.fixture(autouse=True)
def reset_frame():
    yield
    f3.CRCB, f3.RECCRC = 2, False


# ------------------------------------------------------------------ settings and guards
def test_frozen_settings():
    assert (c4.CRCB, c4.RECCRC, c4.SLOTS, c4.FLAG_CAP) == (3, False, 4, 3.0)
    assert c4.DESIGNS == ("rec", "heur", "flags", "flagsrec")
    assert c4.T == {"H2_lower": 0.10, "H3_lower": 0.10, "H4_lower_q6": -0.15, "H4_lower_q12": -0.10, "H5_lower": -0.06,
                    "H6_upper": 0.0, "H7_per_million": 0.5, "H8_rec": 0.01, "H8_heur": 0.06}


def test_per_million_matches_development_formula():
    import integrity3_eval as ie
    for Q in (6, 12):
        assert c4.per_million(Q) == pytest.approx(Q * 0.7 * ie.pc(1e-3) * 2.0 ** -ie.BITS["D2"] * 1e6, rel=1e-12)


def test_environment_switch_refused(monkeypatch):
    monkeypatch.setenv("P3_TBAND", "2.0")
    with pytest.raises(SystemExit, match="environment switches"):
        c4.check_environment()


def test_environment_sets_frame():
    c4.check_environment()
    assert (f3.CRCB, f3.RECCRC) == (3, False)


def test_import_time_settings_checked(monkeypatch):
    monkeypatch.setattr(c4.pq, "T_BAND", 2.5)
    with pytest.raises(SystemExit, match="T_BAND"):
        c4.check_environment()


def run_main(monkeypatch, tmp_path, argv):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["confirm4.py"] + argv)
    with pytest.raises(SystemExit) as e:
        c4.main()
    return str(e.value)


def test_confirmatory_needs_seal(monkeypatch, tmp_path):
    assert "seal file" in run_main(monkeypatch, tmp_path, ["data/clean/usgs_new4_2022", "confirm4"])


def test_confirmatory_needs_freeze_record(monkeypatch, tmp_path):
    msg = run_main(monkeypatch, tmp_path, ["data/clean/usgs_new4_2022", "confirm4", "x.md5"])
    assert "FREEZE4.md is missing" in msg


@pytest.mark.parametrize("folder", ["data/clean/usgs_new4_2022", "data/clean/other_2022"])
def test_rehearsal_cannot_open_cohort4(monkeypatch, tmp_path, folder):
    assert "only be opened by the confirmatory tag" in run_main(monkeypatch, tmp_path, [folder, "rehearsal"])


def test_freeze_record_hash_mismatch_refused(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    os.makedirs("docs")
    open("a.txt", "w").write("x")
    open(c4.FREEZE_RECORD, "w").write("| `a.txt` | 00000000000000000000000000000000 |\n")
    monkeypatch.setattr(c4, "git", lambda *a: "abc" if a[0] == "rev-list" else "")
    with pytest.raises(SystemExit, match="a.txt"):
        c4.verify_freeze()
    from data.seal import md5
    open(c4.FREEZE_RECORD, "w").write(f"| `a.txt` | {md5('a.txt')} |\n")
    assert c4.verify_freeze() == 1
    monkeypatch.setattr(c4, "git", lambda *a: "abc" if a[0] == "rev-list" else ("src/x.py" if a[0] == "diff" else ""))
    with pytest.raises(SystemExit, match="differ from"):
        c4.verify_freeze()


def test_freeze_writer_refuses_without_plan(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="CONFIRM4_PLAN"):
        fz.main("confirm4-freeze")


def test_freeze_file_list_covers_v3():
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        fl = fz.files()
    finally:
        os.chdir(cwd)
    for f in ("src/p3v3/confirm4.py", "src/p3v3/receiver3.py", "src/p3v3/certlang3.py", "src/p3v3/frame3.py",
              "src/p3v3/proto_base4.py", "tests/v3/test_confirm4.py", "src/p3/certlang.py", "docs/CONFIRM4_PLAN.md",
              "results/confirm4/selection.csv"):
        assert f in fl, f


# ------------------------------------------------------------------ round trip on a synthetic day
def fake_item(n=14, hard_do=True):
    vals = [("T", i, 1000 + i) for i in range(n - 4)] + [("DO", i, 2000 + i) for i in range(4)]
    wit = {"DOmin": (None, 0, 2001), "pHmin": (None, 0, 3000), "pHmax": (None, 1, 3100)}
    return {"vals": vals, "bound": True, "d": 17, "wit": wit, "tw": (3, 1500), "ew": (0, 4000, 4, 4100, 0.2),
            "hard": {"DO": hard_do, "pH": False, "T": True, "EC": False}, "rd": SimpleNamespace(n_of={"T": 96, "DO": 96, "pH": 96, "EC": 96})}


@pytest.mark.parametrize("variant", ["rec", "heur"])
@pytest.mark.parametrize("Q", [6, 12])
@pytest.mark.parametrize("n", [6, 14, 30, 60])
def test_roundtrip_day(variant, Q, n):
    f3.CRCB, f3.RECCRC = 3, False
    assert c4.roundtrip_day(fake_item(n), Q, variant) in (True, None)


def test_roundtrip_detects_receiver_fault(monkeypatch):
    f3.CRCB, f3.RECCRC = 3, False
    it = fake_item(14)
    assert c4.roundtrip_day(it, 12, "heur") is True
    real = c4.r3.receive

    def drop_one(msgs, **kw):
        d = real(msgs, **kw)
        d.values.pop(max(d.values))
        return d
    monkeypatch.setattr(c4.r3, "receive", drop_one)
    assert c4.roundtrip_day(it, 12, "heur") is False


# ------------------------------------------------------------------ statistics and verdict logic
def agg_frame(rng, levels, sites=20, count=50):
    """levels: {(cond, design, metric): pooled level}; per-site sums drawn around the level."""
    rows = []
    for (cond, design, metric), p in levels.items():
        for s in range(sites):
            q = float(np.clip(p + rng.normal(0, 0.01), 0, 1))
            rows.append({"site": f"s{s:02d}", "cond": cond, "design": design, "metric": metric, "sum": q * count, "count": count})
    return pd.DataFrame(rows)


def test_agg_equals_confirm3_agg():
    from p3 import confirm3
    rng = np.random.default_rng(3)
    g = agg_frame(rng, {(c, d, "rec"): 0.5 + 0.1 * i for i, (c, d) in enumerate([("a", "x"), ("a", "y")])})
    a, b = c4.Agg(g, seed=confirm3.SEED), confirm3.Agg(g)
    assert a.diff("a", "x", "y", "rec") == b.diff("a", "x", "y", "rec")
    assert a.level("a", "x", "rec") == b.level("a", "x", "rec")


def scenario(alt_gain=0.25, rec_cost=-0.05, cfg_gap=-0.05, rec_vs_fr=-0.01):
    base = {"rec": 0.85, "hard_alt": 0.55, "hard_cfg": 0.9, "all_cfg": 0.95}
    lv = {}
    for c in c4.CONDS:
        for d in c4.DESIGNS:
            for m, v in base.items():
                lv[(c, d, m)] = v
        lv[(c, "heur", "hard_alt")] = base["hard_alt"] + alt_gain
        lv[(c, "heur", "rec")] = base["rec"] + rec_cost
        lv[(c, "flagsrec", "rec")] = base["rec"] + rec_cost - rec_vs_fr
        lv[(c, "heur", "hard_cfg")] = base["hard_cfg"] + cfg_gap
    return lv


def make_inputs(lv, wrong=0.0, rt_ok=(True, True, None), byte_wrong=0, h8_gap=0.0, integ_hi=0.0):
    rng = np.random.default_rng(9)
    A = {Q: c4.Agg(agg_frame(rng, lv)) for Q in c4.QS}
    byte = pd.DataFrame({"wrong": [byte_wrong], "mismatch": [0]})
    rt = pd.DataFrame({"ok": list(rt_ok)})
    integ = {(d, Q): (0.0, 0.0, integ_hi) for d in ("rec", "heur") for Q in c4.QS}
    h8 = {(Q, c, d): (0.8 + h8_gap, 0.8, 100) for Q in c4.QS for c in c4.CONDS for d in ("rec", "heur")}
    return A, wrong, byte, rt, integ, h8


def verdict_map(*args):
    v = c4.verdicts(*args)
    return dict(zip(v.id, v.supported))


def test_all_supported_in_a_clean_scenario():
    assert all(verdict_map(*make_inputs(scenario())).values())


def test_h1_fails_on_round_trip_mismatch_or_wrong_decision():
    assert not verdict_map(*make_inputs(scenario(), rt_ok=(True, False)))["H1"]
    assert not verdict_map(*make_inputs(scenario(), byte_wrong=1))["H1"]
    assert not verdict_map(*make_inputs(scenario(), wrong=0.001))["H1"]
    assert verdict_map(*make_inputs(scenario(), rt_ok=(None, None, True)))["H1"]


def test_h2_h3_fail_on_small_gain():
    v = verdict_map(*make_inputs(scenario(alt_gain=0.05)))
    assert not v["H2"] and not v["H3"]


def test_h4_uses_q_specific_limits():
    v = verdict_map(*make_inputs(scenario(rec_cost=-0.12)))       # within -0.15 at Q 6 but beyond -0.10 at Q 12
    assert not v["H4"]
    v = verdict_map(*make_inputs(scenario(rec_cost=-0.07)))
    assert v["H4"]


def test_h5_and_h6():
    assert not verdict_map(*make_inputs(scenario(rec_vs_fr=-0.10)))["H5"]
    assert not verdict_map(*make_inputs(scenario(cfg_gap=0.0)))["H6"]


def test_h7_limit_on_upper_bound():
    hi_ok = 0.5 / c4.per_million(12) * 0.99
    assert verdict_map(*make_inputs(scenario(), integ_hi=hi_ok))["H7"]
    assert not verdict_map(*make_inputs(scenario(), integ_hi=hi_ok * 1.05))["H7"]


def test_h8_limits():
    assert verdict_map(*make_inputs(scenario(), h8_gap=0.009))["H8"]
    assert not verdict_map(*make_inputs(scenario(), h8_gap=0.02))["H8"]       # record limit 0.01


def test_byte_vs_slot_same_days():
    byte = pd.DataFrame({"site": ["a", "a", "b"], "day": [1, 2, 1], "Q": 6, "cond": "iid_p0.3", "design": "rec", "full": [1.0, 0.5, 0.0]})
    slot = pd.DataFrame({"site": ["a", "a", "b", "b"], "day": [1, 2, 1, 9], "Q": 6, "cond": "iid_p0.3", "design": "rec",
                         "rec_full": [1.0, 1.0, 0.0, 1.0]})
    b, s, n = c4.byte_vs_slot(byte, slot)[(6, "iid_p0.3", "rec")]
    assert n == 3 and b == pytest.approx(0.5) and s == pytest.approx(2 / 3)
