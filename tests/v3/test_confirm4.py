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

N_OF = {"T": 96, "DO": 96, "pH": 96, "EC": 96}


@pytest.fixture(autouse=True)
def reset_frame():
    yield
    f3.CRCB, f3.RECCRC = 2, False


# ------------------------------------------------------------------ settings
def test_frozen_settings():
    assert (c4.CRCB, c4.RECCRC, c4.SLOTS, c4.FLAG_CAP) == (3, False, 4, 4.0)
    assert c4.DESIGNS == ("rec", "heur", "flags", "flagsrec") and c4.BYTE_DESIGNS == ("rec", "heur", "flagsrec")
    assert c4.T == {"H2_lower": 0.10, "H3_lower": 0.10, "H4_lower_q6": -0.15, "H4_lower_q12": -0.10, "H6_upper": 0.0, "H8_rec": 0.01}


def test_flag_field_costs_no_record_value_on_d2_frame():
    """Review finding A1: a flag byte fits in the spare bits of the CRC-24 record symbol (but not of the CRC-16 one)."""
    f3.CRCB = 3
    assert f3.values_per_unit(f3.record_unit_bits(0) - 8) == f3.values_per_unit(f3.record_unit_bits(0)) == c4.SLOTS == c4.FLAG_CAP
    f3.CRCB = 2
    assert f3.values_per_unit(f3.record_unit_bits(0) - 8) == f3.values_per_unit(f3.record_unit_bits(0)) - 1


def test_plan_limits_equal_code():
    """Review finding E3: the plan's machine-read LIMITS line equals the limits in the code."""
    plan = os.path.join(ROOT, "docs", "CONFIRM4_PLAN.md")
    if not os.path.exists(plan):
        plan = os.path.join(ROOT, "docs", "CONFIRM4_PLAN_DRAFT.md")
    assert c4.plan_limits(plan) == c4.T


def test_plan_limits_parser(tmp_path):
    p = tmp_path / "p.md"
    p.write_text("x\n`LIMITS: A=0.1 B=-0.2`\n")
    assert c4.plan_limits(str(p)) == {"A": 0.1, "B": -0.2}
    p.write_text("no line\n")
    assert c4.plan_limits(str(p)) is None


def test_per_million_matches_development_formula_and_is_a_ceiling():
    import integrity3_eval as ie
    for Q in (6, 12):
        assert c4.per_million(Q) == pytest.approx(Q * 0.7 * ie.pc(1e-3) * 2.0 ** -ie.BITS["D2"] * 1e6, rel=1e-12)
    assert c4.per_million(12) < 0.09                        # review finding D1: no conditional share can reach 0.5 per million


# ------------------------------------------------------------------ guards
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
    assert "FREEZE4.md is missing" in run_main(monkeypatch, tmp_path, ["data/clean/usgs_new4_2022", "confirm4", "x.md5"])


@pytest.mark.parametrize("folder", ["data/clean/usgs_new4_2022", "data/clean/other_2022"])
def test_rehearsal_cannot_open_cohort4(monkeypatch, tmp_path, folder):
    assert "only be opened by the confirmatory tag" in run_main(monkeypatch, tmp_path, [folder, "rehearsal"])


SHA = "a" * 40


def fake_git(diff="", status="", fail=None):
    def g(*a):
        if fail and a[0] == fail:
            sys.exit(f"refusing to run: git {a[0]} failed")
        return {"rev-list": SHA, "diff": diff, "status": status}.get(a[0], "")
    return g


def freeze_setup(tmp_path, commit=SHA, good=True):
    from data.seal import md5
    os.makedirs(tmp_path / "docs", exist_ok=True)
    (tmp_path / "a.txt").write_text("x")
    h = md5(str(tmp_path / "a.txt")) if good else "0" * 32
    (tmp_path / "docs" / "FREEZE4.md").write_text(f"Written now. Commit {commit}, tag `confirm4-freeze`.\n\n| `a.txt` | {h} |\n")


def test_verify_freeze_accepts_matching_record(monkeypatch, tmp_path):
    freeze_setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(c4, "git_strict", fake_git())
    assert c4.verify_freeze() == (1, SHA)


def test_verify_freeze_refuses_hash_mismatch(monkeypatch, tmp_path):
    freeze_setup(tmp_path, good=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(c4, "git_strict", fake_git())
    with pytest.raises(SystemExit, match="a.txt"):
        c4.verify_freeze()


def test_verify_freeze_refuses_record_of_another_commit(monkeypatch, tmp_path):
    freeze_setup(tmp_path, commit="b" * 40)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(c4, "git_strict", fake_git())
    with pytest.raises(SystemExit, match="names commit"):
        c4.verify_freeze()


@pytest.mark.parametrize("kw,msg", [({"diff": "src/x.py"}, "differ from"), ({"status": " M docs/FREEZE4.md"}, "uncommitted"),
                                    ({"fail": "diff"}, "git diff failed")])
def test_verify_freeze_refuses_changes_and_git_failures(monkeypatch, tmp_path, kw, msg):
    freeze_setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(c4, "git_strict", fake_git(**kw))
    with pytest.raises(SystemExit, match=msg):
        c4.verify_freeze()


def test_git_strict_fails_closed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)                             # not a repository: git fails
    with pytest.raises(SystemExit, match="failed"):
        c4.git_strict("rev-parse", "--verify", "no-such-ref-xyz")


def seal_setup(tmp_path, names, sealed):
    folder = tmp_path / "cohort"
    folder.mkdir()
    for n in names:
        (folder / f"{n}.csv").write_text("x")
    seal = tmp_path / "cohort.md5"
    seal.write_text("".join(f"{'0' * 32} *{os.path.relpath(str(p), str(tmp_path)).replace(os.sep, '/')}\n" for p in sealed(folder)))
    return str(folder), str(seal)


def test_seal_covers_folder(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    folder, seal = seal_setup(tmp_path, ["a", "b"], lambda f: [f / "a.csv", f / "b.csv"])
    c4.check_seal_covers(seal, folder)


@pytest.mark.parametrize("sealed", [lambda f: [f / "a.csv"], lambda f: [f.parent / "other" / "a.csv", f.parent / "other" / "b.csv"],
                                    lambda f: [f / "a.csv", f / "b.csv", f / "c.csv"]])
def test_seal_of_another_folder_or_subset_refused(monkeypatch, tmp_path, sealed):
    monkeypatch.chdir(tmp_path)
    folder, seal = seal_setup(tmp_path, ["a", "b"], sealed)
    with pytest.raises(SystemExit, match="seal does not cover"):
        c4.check_seal_covers(seal, folder)


def test_stamp(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert c4.check_stamp("t", "freeze X", strict=True) is None            # fresh: stamp written
    os.makedirs("results/t/byte4")
    open("results/t/byte4/s.csv", "w").write("x")
    assert c4.check_stamp("t", "freeze X", strict=True) is None            # resume with the same code
    with pytest.raises(SystemExit, match="come from"):
        c4.check_stamp("t", "freeze Y", strict=True)                       # other code
    assert "come from" in c4.check_stamp("t", "freeze Y", strict=False)
    open("results/t/done4.flag", "w").write("x")
    with pytest.raises(SystemExit, match="finished"):
        c4.check_stamp("t", "freeze X", strict=True)                       # no re-run of a finished run


def test_stamp_refuses_unstamped_outputs(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    os.makedirs("results/t/plans")
    open("results/t/plans/s.pkl", "w").write("x")
    with pytest.raises(SystemExit, match="without a run stamp"):
        c4.check_stamp("t", "freeze X", strict=True)


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


# ------------------------------------------------------------------ synthetic day: round trip, decoded knowledge, forgery
def fake_item(n=14, hard_do=True):
    vals = [("T", i, 1000 + i) for i in range(n - 4)] + [("DO", i, 2000 + i) for i in range(4)]
    wit = {"DOmin": (None, 0, 2001), "pHmin": (None, 0, 3000), "pHmax": (None, 1, 3100)}
    rd = SimpleNamespace(n_of=dict(N_OF), channels=[SimpleNamespace(param=p, n=96) for p in ("T", "DO", "pH", "EC")])
    return {"vals": vals, "bound": True, "d": 17, "wit": wit, "tw": (3, 1500), "ew": (0, 4000, 4, 4100, 0.2), "lag": 4,
            "hard": {"DO": hard_do, "pH": False, "T": True, "EC": False}, "rd": rd}


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


def test_decoded_knowledge_uses_decoded_codes_only():
    """Review finding A3: witnesses enter as slotless codes from the decoder; a rejected block contributes nothing."""
    f3.CRCB, f3.RECCRC = 3, False
    it = fake_item(14)
    blk, lay, host = c4.i3.build(it, 12, "3b")
    d = c4.r3.receive(blk.messages, n_of=N_OF)
    Kd, Kp, Kt, Ke = c4.decoded_knowledge(it, d, {})
    assert set(d.witness) == set(lay) | (set(host) if blk.coded else set()) and {"DOmin", "Tmax"} <= set(d.witness)
    assert Kd.wmin is not None and Kt.wmax is not None
    assert (Kp.wmin is not None) == ("pHmin" in d.witness) and (Ke.rate_cells is not None) == ("ECa" in d.witness)
    assert np.isfinite(Kt.eff()[1][:10]).all() and Kt.hi[0] < c4.cl.base_range("T")[1]
    d.record_rejected = d.witness_rejected = True
    Kd, Kp, Kt, Ke = c4.decoded_knowledge(it, d, {})
    assert Kd.wmin is None and Kt.wmax is None and (Kt.hi == c4.cl.base_range("T")[1]).all()


def test_merge_flags_and_decode_key():
    fd = {"cfg": (1, 0, None, 1)}
    assert c4.merge_flags({"cfg": (-1, -1, -1)}, fd, True) == {"cfg": (1, 0, -1)}
    assert c4.merge_flags({"cfg": (-1, 1, 0)}, fd, False) == {"cfg": (-1, 1, 0)}
    a, b = c4.f3.Decoded(), c4.f3.Decoded()
    assert c4.decode_key(a) == c4.decode_key(b)
    b.witness = {"Tmax": 5}
    assert c4.decode_key(a) != c4.decode_key(b)


def test_forge4_reaches_header_and_keeps_crc_valid():
    f3.CRCB, f3.RECCRC = 3, False
    blk = f3.build_block([("T", i, 100 + i) for i in range(8)], True, 3, 6)
    rng = np.random.default_rng(2)
    head = 0
    for _ in range(400):
        m = blk.messages[0]
        x = c4.forge4(m, rng)
        assert x != m and len(x) == len(m)
        assert f3.msg_crc(x[:3] + x[3 + f3.CRCB:]) == int.from_bytes(x[3:3 + f3.CRCB], "big")
        head += x[:3] != m[:3]
    assert 50 < head < 400


# ------------------------------------------------------------------ statistics and verdict logic
def agg_frame(rng, levels, sites=20, count=50):
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


def scenario(alt_gain=0.25, rec_cost=-0.05, cfg_gap=-0.05):
    base = {"rec": 0.85, "hard_alt": 0.55, "hard_cfg": 0.9, "all_cfg": 0.95}
    lv = {}
    for c in c4.CONDS:
        for d in c4.BYTE_DESIGNS:
            for m, v in base.items():
                lv[(c, d, m)] = v
        lv[(c, "heur", "hard_alt")] = base["hard_alt"] + alt_gain
        lv[(c, "heur", "rec")] = base["rec"] + rec_cost
        lv[(c, "heur", "hard_cfg")] = base["hard_cfg"] + cfg_gap
    return lv


def make_inputs(lv, rt_ok=(True, True, None), h8_gap=0.0, **checks):
    rng = np.random.default_rng(9)
    AB = {Q: c4.Agg(agg_frame(rng, lv)) for Q in c4.QS}
    ck = {"byte_wrong": 0.0, "slot_wrong": 0.0, "mismatch": 0, "dec_error": 0, "unbuilt": 0, **checks}
    rt = pd.DataFrame({"ok": list(rt_ok)})
    integ = {(d, Q): (0.0, 0.0, 0.01) for d in ("rec", "heur") for Q in c4.QS}
    h8 = {(Q, c, d): (0.8 + (h8_gap if d == "rec" else 0.05), 0.8, 100) for Q in c4.QS for c in c4.CONDS for d in ("rec", "heur")}
    return AB, ck, rt, integ, h8


def verdict_map(*args):
    v = c4.verdicts(*args)
    return dict(zip(v.id, v.verdict))


def test_clean_scenario():
    v = verdict_map(*make_inputs(scenario()))
    assert v == {"H1": "pass", "H2": "pass", "H3": "pass", "H4": "pass", "H6": "pass", "H7": "not a test", "H8": "pass"}


def test_types():
    v = c4.verdicts(*make_inputs(scenario()))
    assert list(v[v.type == "test"].id) == ["H2", "H3", "H4"]


@pytest.mark.parametrize("kw", [{"rt_ok": (True, False)}, {"byte_wrong": 0.01}, {"slot_wrong": 0.01}, {"mismatch": 1}, {"dec_error": 1}])
def test_h1_fails(kw):
    assert verdict_map(*make_inputs(scenario(), **kw))["H1"] == "fail"


def test_h1_not_buildable_is_not_a_mismatch():
    assert verdict_map(*make_inputs(scenario(), rt_ok=(None, None, True)))["H1"] == "pass"


def test_h2_h3_fail_on_small_gain():
    v = verdict_map(*make_inputs(scenario(alt_gain=0.05)))
    assert v["H2"] == v["H3"] == "fail"


def test_h4_uses_q_specific_limits():
    assert verdict_map(*make_inputs(scenario(rec_cost=-0.12)))["H4"] == "fail"     # inside -0.15 at Q 6, beyond -0.10 at Q 12
    assert verdict_map(*make_inputs(scenario(rec_cost=-0.07)))["H4"] == "pass"


def test_h6_upper_bound():
    assert verdict_map(*make_inputs(scenario(cfg_gap=0.0)))["H6"] == "fail"


def test_h8_record_only_and_ignores_3b_gap():
    assert verdict_map(*make_inputs(scenario(), h8_gap=0.009))["H8"] == "pass"     # the 3b gap of 0.05 is descriptive
    assert verdict_map(*make_inputs(scenario(), h8_gap=0.02))["H8"] == "fail"


def test_byte_vs_slot_same_days():
    byte = pd.DataFrame({"site": ["a", "a", "b"], "day": [1, 2, 1], "Q": 6, "cond": "iid_p0.3", "design": "rec", "rec_full": [1.0, 0.5, 0.0]})
    slot = pd.DataFrame({"site": ["a", "a", "b", "b"], "day": [1, 2, 1, 9], "Q": 6, "cond": "iid_p0.3", "design": "rec",
                         "rec_full": [1.0, 1.0, 0.0, 1.0]})
    b, s, n = c4.byte_vs_slot(byte, slot)[(6, "iid_p0.3", "rec")]
    assert n == 3 and b == pytest.approx(0.5) and s == pytest.approx(2 / 3)
