"""Confirmation of method version 3 (cohort 4): run ONCE on the sealed cohort after the freeze.
Pre-registration: docs/CONFIRM4_PLAN.md (the limits in T below must equal its machine-read LIMITS line; checked at start).
Counterpart of the frozen src/p3/confirm3.py. Revised 2026-11-10 after the in-project review docs/REVIEW_FINDINGS_V3.md.

Stages (each resumable per site; outputs under results/<tag>/):
  1. plans of every record day (plans/)
  2. analysis population: sites with at least MIN_DAYS four-parameter days
  3. slot model (proto_base4, 4 slots, flag capacity 4; designs rec, heur, flags, flagsrec): descriptive cross-check only (slot4/)
  4. byte check (byte4/): the hypotheses' data. Real frame3 messages (CRC-24 per message, setting D2) for the record only and the
     3b rule; loss masks drawn ONCE per day, Q, and condition and shared by every design (paired); the hardened receiver; knowledge
     and decisions built ONLY from decoded values and decoded witness codes (slotless witnesses); flagsrec = the record-only blocks
     plus the configured decision flags whenever a message arrived (the flag field fits in the 16 spare bits of the CRC-24 record
     symbol, so it costs no record value). Output in the slot model's format (<site>_Q<Q>.csv and _meta.csv), including 7DADM
     windows. Also a lossless round trip of every analysed day (<site>_roundtrip.csv).
  5. integrity (integ4/): forced CRC-valid forgery of one arrived message (header or body bytes, check recomputed); descriptive
     classes, false certificates, and wrong decisions given a forgery; the per-million figure is an analytic bound, not a test.
  6. verdicts (verdicts4.md, verdicts4.csv) and descriptive tables.
Guards: no P3_* environment variables; the confirmatory tag needs the freeze tag, clean method files equal to it, a committed
docs/FREEZE4.md naming the tag's commit with every MD5 unchanged, a seal that verifies and covers exactly the folder's CSV files,
only selected sites, limits equal to the plan, and a run stamp (results/<tag>/RUN_ID) so stale outputs or a re-run are refused.

Usage (from Paper3/):
  python -I src/p3v3/confirm4.py <folder> confirm4 <seal file>       confirmatory run
  python -I src/p3v3/confirm4.py <folder> <other tag> [site ...]     rehearsal on development data (NOT confirmatory)
"""
import datetime
import glob
import os
import platform
import re
import subprocess
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import frame3 as f3  # noqa: E402
import integrity3 as i3  # noqa: E402
import proto_base4 as pb  # noqa: E402
import receiver3 as r3  # noqa: E402
from p3 import certlang as cl  # noqa: E402
from p3 import proto_base_eval as pe  # noqa: E402
from p3 import proto_queries as pq  # noqa: E402
from p3 import record  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402
from p3.run_multiday import site_plans  # noqa: E402

# ---- frozen settings (docs/CONFIRM4_PLAN.md)
CONFIRM_TAG = "confirm4"
FREEZE_TAG = "confirm4-freeze"
FREEZE_RECORD = "docs/FREEZE4.md"
PLAN = "docs/CONFIRM4_PLAN.md"
SELECTION = "results/confirm4/selection.csv"
CRCB, RECCRC = 3, False               # frame setting D2: CRC-24 per message, no record CRC
SLOTS = 4                             # slot model of the D2 frame: 4 value slots per message
FLAG_CAP = 4.0                        # flags fit in the 16 spare bits of the D2 record symbol (review finding A1)
DESIGNS = ("rec", "heur", "flags", "flagsrec")          # slot model (descriptive)
BYTE_DESIGNS = ("rec", "heur", "flagsrec")              # byte check (hypotheses)
MIN_DAYS = 100                        # analysis population: sites with at least this many four-parameter days
B = 1000                              # bootstrap resamples (site-clustered)
SEED = 20261115                       # bootstrap, byte-check, and integrity seed (slot model keeps proto_base4.SEED)
BYTE_DRAWS = 20                       # byte check: loss draws per day, Q, and condition (every analysed day)
INT_EVERY, INT_DRAWS = 3, 8           # integrity: every n-th analysed day, forged draws per day and block
P_LOSS = 0.3                          # integrity: independent loss before the forgery
BER = 1e-3                            # integrity: assumed bit-error rate (no channel was measured)
T_BAND_EXPECTED, UNKNOWN_EXPECTED = 3.0, True     # src/p3/proto_queries.py defaults; the run refuses other values
CONDS = ("iid_p0.3", "gilbert_p0.3_b3")
BYTE_CONDS = (("iid_p0.3", ("iid", 0.3, None)), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3)))
QS = (6, 12)
T = {"H2_lower": 0.10, "H3_lower": 0.10, "H4_lower_q6": -0.15, "H4_lower_q12": -0.10, "H6_upper": 0.0, "H8_rec": 0.01}
KINDS = (("do", 0), ("ph", 1), ("ec", 2))
VARIANT = {"rec": "record", "heur": "3b"}
STAGE_DIRS = ("plans", "slot4", "byte4", "integ4")


# ------------------------------------------------------------------ guards and log
class Log:
    def __init__(self, path):
        self.path = path

    def __call__(self, text):
        line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {text}"
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def check_environment():
    """No environment switches: refuse if any P3_* variable is set, and check the import-time settings of proto_queries."""
    bad = sorted(k for k in os.environ if k.upper().startswith("P3_"))
    if bad:
        sys.exit("refusing to run: environment switches are set: " + ", ".join(bad))
    if pq.T_BAND != T_BAND_EXPECTED or pq.UNKNOWN_HARD != UNKNOWN_EXPECTED:
        sys.exit(f"refusing to run: proto_queries settings T_BAND={pq.T_BAND}, UNKNOWN_HARD={pq.UNKNOWN_HARD}")
    f3.CRCB, f3.RECCRC = CRCB, RECCRC


def git(*args):
    """Output of a git command; '' when it fails (logging only)."""
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def git_strict(*args):
    """Output of a git command; a failing command refuses the run (no fail-open)."""
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"refusing to run: git {' '.join(args)} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def plan_limits(path):
    """The machine-read limits line of the plan: 'LIMITS: H2_lower=0.10 ...' -> dict."""
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*`?LIMITS:\s*(.+?)`?\s*$", line)
        if m:
            return {k: float(v) for k, v in (x.split("=") for x in m.group(1).split())}
    return None


def verify_freeze():
    """The code that runs is the code that was approved (review findings A8 and B3): the tag exists; method files are clean and
    equal to the tag; the freeze record is tracked, committed, names the tag's commit, and every MD5 in it is unchanged."""
    from data.seal import md5
    if not os.path.exists(FREEZE_RECORD):
        sys.exit(f"refusing to run: {FREEZE_RECORD} is missing (run src/p3v3/freeze4.py after the authors tag the repository)")
    commit = git_strict("rev-list", "-n", "1", FREEZE_TAG)
    if not commit:
        sys.exit(f"refusing to run: tag {FREEZE_TAG} does not exist")
    paths = ["src", "tests", "tools", PLAN, SELECTION]
    diff = git_strict("diff", "--name-only", FREEZE_TAG, "--", *paths)
    dirty = git_strict("status", "--porcelain", "--", *paths, FREEZE_RECORD)
    if diff or dirty:
        sys.exit(f"refusing to run: method files or the freeze record differ from {FREEZE_TAG} or are uncommitted:\n{diff}\n{dirty}")
    git_strict("ls-files", "--error-unmatch", FREEZE_RECORD)
    text = open(FREEZE_RECORD, encoding="utf-8").read()
    m = re.search(r"Commit ([0-9a-f]{40})", text)
    if not m or m.group(1) != commit:
        sys.exit(f"refusing to run: {FREEZE_RECORD} names commit {m.group(1) if m else 'none'}, tag {FREEZE_TAG} is {commit}")
    bad, n = [], 0
    for line in text.splitlines():
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(parts) == 2 and parts[0].startswith("`") and len(parts[1]) == 32:
            n += 1
            f = parts[0].strip("`")
            if not os.path.exists(f) or md5(f) != parts[1]:
                bad.append(f)
    if bad or not n:
        sys.exit("refusing to run: files differ from the freeze record: " + (", ".join(bad) or "no hashed files listed"))
    return n, commit


def _norm(p):
    return os.path.normcase(os.path.abspath(p))


def check_seal_covers(seal, folder):
    """The seal must list exactly the CSV files of the analysed folder (review finding B1)."""
    sealed = set()
    for line in open(seal, encoding="utf-8"):
        if line.strip():
            sealed.add(_norm(line.split(" *", 1)[1].strip()))
    sealed_csv = {p for p in sealed if p.endswith(".csv")}
    present = {_norm(f) for f in glob.glob(os.path.join(folder, "*.csv"))}
    if not present or sealed_csv != present:
        sys.exit(f"refusing to run: the seal does not cover exactly the folder's CSV files "
                 f"({len(sealed_csv - present)} sealed but absent, {len(present - sealed_csv)} present but unsealed)")


def check_stamp(tag, ident, strict):
    """Run stamp (review finding B2): results/<tag>/RUN_ID names the code the outputs came from. Strict (confirmatory): refuse a
    finished run, or existing outputs without a stamp or with another stamp. Rehearsal: return a warning instead."""
    base = f"results/{tag}"
    done = os.path.exists(f"{base}/done4.flag")
    rid = f"{base}/RUN_ID"
    has = any(os.path.isdir(f"{base}/{d}") and os.listdir(f"{base}/{d}") for d in STAGE_DIRS)
    old = open(rid, encoding="utf-8").read().strip() if os.path.exists(rid) else None
    problem = None
    if done:
        problem = f"{base}/done4.flag exists: the run has finished and may not be re-run"
    elif old is not None and old != ident:
        problem = f"outputs in {base} come from '{old}', this code is '{ident}'"
    elif old is None and has:
        problem = f"stage outputs exist in {base} without a run stamp"
    if problem and strict:
        sys.exit("refusing to run: " + problem)
    if old is None and not done:
        os.makedirs(base, exist_ok=True)
        open(rid, "w", encoding="utf-8").write(ident + "\n")
    return problem


def selected_sites():
    s = pd.read_csv(SELECTION, dtype={"site_no": str})
    return set(s.loc[s.selected.astype(str).str.lower() == "true", "site_no"])


def run_record(log, folder, tag, seal):
    import scipy
    from data.seal import md5
    log(f"command: {' '.join([sys.executable] + sys.argv)}")
    log(f"python {platform.python_version()} ({platform.platform()}); numpy {np.__version__}; pandas {pd.__version__}; scipy {scipy.__version__}")
    log(f"git HEAD {git('rev-parse', 'HEAD') or 'unknown'}; freeze tag {FREEZE_TAG} -> {git('rev-list', '-n', '1', FREEZE_TAG) or 'missing'}")
    log(f"folder {folder}; tag {tag}; seal {seal or 'none (rehearsal)'}" + (f" (MD5 of the seal file {md5(seal)})" if seal else ""))
    log(f"frame3 CRCB={f3.CRCB} RECCRC={f3.RECCRC}; slot model SLOTS={SLOTS} FLAG_CAP={FLAG_CAP} designs={DESIGNS} seed={pb.SEED}; "
        f"byte designs={BYTE_DESIGNS}")
    log(f"proto_queries T_BAND={pq.T_BAND} UNKNOWN_HARD={pq.UNKNOWN_HARD}; MIN_DAYS={MIN_DAYS} B={B} SEED={SEED}")
    log(f"byte check every day, {BYTE_DRAWS} paired draws; integrity every {INT_EVERY} day(s), {INT_DRAWS} draws, loss {P_LOSS}, "
        f"bit-error rate {BER:g}; limits {T}")


# ------------------------------------------------------------------ stage 2: population
def analysis_sites(paths, tag):
    keep = []
    for f in paths:
        site = os.path.basename(f)[:-4]
        P = pd.read_pickle(f"results/{tag}/plans/{site}.pkl")
        if sum(1 for v in P.values() if v["four"]) >= MIN_DAYS:
            keep.append(f)
    return keep


# ------------------------------------------------------------------ decoded knowledge (slotless witnesses, review finding A3)
def decoded_knowledge(it, d, res):
    """Knowledge objects (DO, pH, T, EC) built only from what the receiver decoded: record values, bound, last position, and witness
    codes (slotless: the frame carries codes, not slots). A rejected record or witness group contributes nothing."""
    rd = it["rd"]
    ch = {c.param: c for c in rd.channels}
    rx = {} if d.record_rejected else dict(d.values)
    cert, _ = record.certify(rx, rd.n_of, d.bound, d.last_pos)

    def kn(p):
        return cl.knowledge_from_rx(p, ch[p].n, rx, cert[p], resolution=res.get(p))
    Kd, Kp, Kt = kn("DO"), kn("pH"), kn("T")
    Ke = kn("EC") if it["ew"] is not None else None
    w = {} if d.witness_rejected else d.witness
    if "DOmin" in w:
        Kd.add_min_witness_value(w["DOmin"])
    if "pHmin" in w:
        Kp.add_min_witness_value(w["pHmin"])
    if "pHmax" in w:
        Kp.add_max_witness_value(w["pHmax"])
    if "Tmax" in w:
        Kt.add_max_witness_value(w["Tmax"])
    if Ke is not None and "ECa" in w and "ECb" in w:
        Ke.add_rate_witness_values(w["ECa"], w["ECb"], it["lag"])
    return Kd, Kp, Kt, Ke


def decode_key(d):
    return (None if d.record_rejected else frozenset(d.values.items()), d.bound, d.last_pos,
            None if d.witness_rejected else frozenset(d.witness.items()))


def merge_flags(dec, fd, anyflag):
    """flagsrec: the certificate decides when certain, otherwise the configured flag (when any message arrived)."""
    out = {}
    for v, tup in dec.items():
        a = list(tup)
        for i in range(3):
            if a[i] == -1 and anyflag and fd[v][i] is not None:
                a[i] = fd[v][i]
        out[v] = tuple(a)
    return out


# ------------------------------------------------------------------ stage 4: byte check and round trip
def roundtrip_day(it, Q, variant):
    """All Q messages of one block through receiver3. Returns None (not buildable) or True when everything decodes exactly."""
    try:
        blk, lay, host = i3.build(it, Q, VARIANT[variant])
    except ValueError:
        return None
    vals = it["vals"]
    d = r3.receive(blk.messages, n_of=it["rd"].n_of)
    ok = not d.record_rejected and not d.witness_rejected and d.crc_failed == 0 and d.accepted == Q
    ok = ok and all(d.values.get(i) == vals[i] for i in d.values)
    ok = ok and (not blk.coded or len(d.values) == len(vals))
    # hosted codes travel in the last record unit, which an uncoded block (K > Q) never sends
    ok = ok and d.witness == ({**lay, **host} if blk.coded else dict(lay))
    return bool(ok)


def _outs(outdir, site):
    return [f"{outdir}/{site}_Q{Q}{s}.csv" for Q in QS for s in ("", "_meta")] + [f"{outdir}/{site}_roundtrip.csv"]


def _write(df, path):
    df.to_csv(path + ".tmp", index=False)
    os.replace(path + ".tmp", path)


def byte_site(path, tag, outdir):
    """Byte check of one site (stage 4). Returns (site, reused)."""
    site = os.path.basename(path)[:-4]
    if all(os.path.exists(o) for o in _outs(outdir, site)):
        return site, True
    rng = np.random.default_rng([SEED, 4, re2.site_number(site)])
    site, items, res = prepare_items(path, tag)
    rts = []
    for it in items:
        it["meta"] = pb.day_meta(it)
        it["fd"] = pb.flag_decisions(it["meta"])
        for variant in ("rec", "heur"):
            for Q in QS:
                rts.append((site, it["d"], variant, Q, roundtrip_day(it, Q, variant)))
    for Q in QS:
        rows, metas, bnd = [], [], {}
        for it in items:
            d0, n, vals, bound = it["d"], len(it["vals"]), it["vals"], it["bound"]
            metas.append({"site": site, "day": d0, "Q": Q,
                          **{f"truth_{k}_{v}": it["meta"]["truth"][v][k] for v in pb.VAR for k in ("do", "ph", "ec", "win7")},
                          **{f"hard_{k}_{v}": it["meta"]["hard"][v][k] for v in pb.VAR for k in ("do", "ph", "ec", "win7")}})
            blocks = {}
            for variant in ("rec", "heur"):
                try:
                    blocks[variant] = i3.build(it, Q, VARIANT[variant])[0]
                except ValueError:
                    blocks[variant] = None
            for cname, c in BYTE_CONDS:
                masks = rr.sim_masks(c, Q, rng, draws=BYTE_DRAWS)          # drawn once: every design sees the same losses
                res_d = {dn: {"decs": [], "full": [], "bs": [], "mm": 0, "err": 0} for dn in BYTE_DESIGNS}
                for variant in ("rec", "heur"):
                    blk = blocks[variant]
                    if blk is None:
                        continue
                    memo = {}
                    for m in masks:
                        keep = [i for i in range(Q) if m[i]]
                        d = r3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else f3.Decoded()
                        if not d.record_rejected:
                            res_d[variant]["mm"] += sum(1 for p, v in d.values.items() if p >= n or v != vals[p])
                        full = bool(bound) and not d.record_rejected and len(d.values) == n and all(d.values.get(i) == vals[i] for i in range(n))
                        k = decode_key(d)
                        if k not in memo:
                            try:
                                memo[k] = (pb.decide(it, decoded_knowledge(it, d, res)), 0)
                            except Exception:                       # noqa: BLE001  (counted; H1 requires none)
                                memo[k] = (({v: (-1, -1, None) for v in pb.VAR}, (-cl.INF, cl.INF)), 1)
                        (dec, mb), err = memo[k]
                        res_d[variant]["err"] += err
                        res_d[variant]["decs"].append(dec)
                        res_d[variant]["full"].append(full)
                        res_d[variant]["bs"].append(mb)
                        if variant == "rec":
                            anyflag = bool(keep)
                            res_d["flagsrec"]["decs"].append(merge_flags(dec, it["fd"], anyflag))
                            res_d["flagsrec"]["full"].append(full)
                            res_d["flagsrec"]["bs"].append((mb, anyflag))
                    if variant == "rec":
                        res_d["flagsrec"]["mm"], res_d["flagsrec"]["err"] = res_d["rec"]["mm"], res_d["rec"]["err"]
                for dn in BYTE_DESIGNS:
                    R = res_d[dn]
                    if not R["decs"]:
                        continue
                    bnd[(cname, dn, d0)] = R["bs"]
                    row0 = {"site": site, "day": d0, "Q": Q, "cond": cname, "design": dn, "rec_full": float(np.mean(R["full"]))}
                    rows.append({**row0, "kind": "day", "mismatch": R["mm"], "dec_error": R["err"]})
                    for kind, idx in KINDS:
                        r = {**row0, "kind": kind}
                        wrong = 0.0
                        for v in pb.VAR:
                            t = it["meta"]["truth"][v][kind]
                            if t is None:
                                r[f"dc_{v}"] = np.nan
                                continue
                            arr = np.array([(-1 if x[v][idx] is None else x[v][idx]) for x in R["decs"]])
                            r[f"dc_{v}"] = float(np.mean((arr != -1) & (arr == int(t))))
                            wrong = max(wrong, float(np.mean((arr != -1) & (arr != int(t)))))
                        r["wrong"] = wrong
                        rows.append(r)
        for it in items:                                    # 7DADM windows, as in proto_base4
            if not it["win"]:
                continue
            for cname, _c in BYTE_CONDS:
                for dn in BYTE_DESIGNS:
                    if any((cname, dn, x["d"]) not in bnd for x in it["win"]):
                        continue
                    r = {"site": site, "day": it["d"], "Q": Q, "cond": cname, "design": dn, "kind": "win7", "rec_full": np.nan}
                    wrong = 0.0
                    for v, th in pb.VAR.items():
                        t = it["meta"]["truth"][v]["win7"]
                        if dn == "flagsrec":
                            parts = [[b[0] for b in bnd[(cname, dn, x["d"])]] for x in it["win"]]
                        else:
                            parts = [bnd[(cname, dn, x["d"])] for x in it["win"]]
                        rn = min(len(p) for p in parts)
                        arr = np.array([cl.rolling_mean_decision([tuple(p[k]) for p in parts], th["T"]) for k in range(rn)])
                        if dn == "flagsrec":
                            avail = np.array([b[1] for b in bnd[(cname, dn, it["d"])]][:rn])
                            arr = np.where((arr == -1) & avail, it["fd"][v][3], arr)
                        r[f"dc_{v}"] = float(np.mean((arr != -1) & (arr == int(t))))
                        wrong = max(wrong, float(np.mean((arr != -1) & (arr != int(t)))))
                    r["wrong"] = wrong
                    rows.append(r)
        _write(pd.DataFrame(metas), f"{outdir}/{site}_Q{Q}_meta.csv")       # meta first: the main file marks completion
        _write(pd.DataFrame(rows), f"{outdir}/{site}_Q{Q}.csv")
    _write(pd.DataFrame(rts, columns=["site", "day", "design", "Q", "ok"]), f"{outdir}/{site}_roundtrip.csv")
    return site, False


# ------------------------------------------------------------------ stage 5: integrity
def forge4(raw, rng):
    """One to three bytes of the header or body changed at random, check recomputed (review finding A4: headers included)."""
    b = bytearray(raw)
    lo = 3 + f3.CRCB
    pos_all = np.r_[0:3, lo:len(b)]
    for pos in rng.choice(pos_all, size=int(rng.integers(1, 4)), replace=False):
        b[int(pos)] ^= int(rng.integers(1, 256))
    crc = f3.msg_crc(bytes(b[:3]) + bytes(b[lo:]))
    b[3:lo] = crc.to_bytes(f3.CRCB, "big")
    return bytes(b)


def wrong_decisions(it, dec):
    """Number of decided-but-wrong day queries (DO, pH, conductance; all threshold sets)."""
    n = 0
    for v in pb.VAR:
        for kind, idx in KINDS:
            t, x = it["meta"]["truth"][v][kind], dec[v][idx]
            if t is not None and x is not None and x != -1 and x != int(t):
                n += 1
    return n


def integrity_site(path, tag, outdir):
    """Forced CRC-valid forgery of one arrived message, D2 frame, receiver3 with sanity and corroboration; record only and the 3b
    rule, Q = 6 and 12. Returns (site, reused)."""
    site = os.path.basename(path)[:-4]
    out = f"{outdir}/{site}.csv"
    if os.path.exists(out):
        return site, True
    rng = np.random.default_rng([SEED, 5, re2.site_number(site)])
    site, items, res = prepare_items(path, tag)
    rows = []
    for it in items[::INT_EVERY]:
        truth = i3.witness_dict(it)
        it["meta"] = pb.day_meta(it)
        for variant in ("rec", "heur"):
            for Q in QS:
                try:
                    blk, _lay, _host = i3.build(it, Q, VARIANT[variant])
                except ValueError:
                    continue
                need = max(blk.K if blk.coded else 1, blk.kw)
                for _ in range(INT_DRAWS):
                    arrive = [i for i in range(Q) if rng.random() >= P_LOSS]
                    if not arrive:
                        continue
                    j = int(rng.choice(arrive))
                    msgs = [blk.messages[i] if i != j else forge4(blk.messages[i], rng) for i in arrive]
                    d = r3.receive(msgs, n_of=it["rd"].n_of)
                    bad = i3.false_certified(it, d)
                    wbad = sum(1 for k, c in d.witness.items() if truth.get(k) is not None and c != truth[k])
                    try:
                        wd, derr = wrong_decisions(it, pb.decide(it, decoded_knowledge(it, d, res))[0]), 0
                    except Exception:                               # noqa: BLE001  (counted, descriptive)
                        wd, derr = 0, 1
                    N = len(arrive)
                    cls = "uncoded" if not blk.coded else ("N=K" if N == need else ("N<K" if N < need else "N>K"))
                    rows.append((site, it["d"], variant, Q, N, need, cls, int(bool(bad or wbad)),
                                 int(bool(d.record_rejected or d.witness_rejected)), int(wd > 0), derr))
    _write(pd.DataFrame(rows, columns=["site", "day", "design", "Q", "arrived", "need", "cls", "day_false", "rejected",
                                       "day_wrong_decision", "dec_error"]), out)
    return site, False


def per_million(Q):
    """Expected false-certificate days per million days for a conditional share of 1: expected arrived messages x P(a message
    is corrupted at BER) x P(a corrupted message passes the CRC-24). An analytic ceiling: no receiver can exceed it."""
    return Q * (1 - P_LOSS) * (1 - (1 - BER) ** (8 * (f3.HEADER_BYTES + f3.BODY_BYTES))) * 2.0 ** -(8 * CRCB) * 1e6


# ------------------------------------------------------------------ stage 6: statistics
class Agg:
    """Per-site sums and counts on one site list, one set of bootstrap resamples (as src/p3/confirm3.Agg)."""

    def __init__(self, g, seed=SEED):
        self.sites = sorted(g.site.unique())
        pos = {s: i for i, s in enumerate(self.sites)}
        self.S, self.C = {}, {}
        for key, z in g.groupby(["cond", "design", "metric"]):
            s, c = np.zeros(len(self.sites)), np.zeros(len(self.sites))
            for r in z.itertuples():
                s[pos[r.site]] += r.sum
                c[pos[r.site]] += r.count
            self.S[key], self.C[key] = s, c
        self.idx = np.random.default_rng(seed).integers(0, len(self.sites), (B, len(self.sites)))

    def point(self, cond, design, metric):
        s, c = self.S[(cond, design, metric)], self.C[(cond, design, metric)]
        return s.sum() / max(c.sum(), 1)

    def _boot(self, cond, design, metric):
        s, c = self.S[(cond, design, metric)], self.C[(cond, design, metric)]
        return s[self.idx].sum(1) / np.maximum(c[self.idx].sum(1), 1)

    def diff(self, cond, a, b, metric):
        est = self.point(cond, a, metric) - self.point(cond, b, metric)
        bs = self._boot(cond, a, metric) - self._boot(cond, b, metric)
        return est, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

    def level(self, cond, design, metric):
        bs = self._boot(cond, design, metric)
        return self.point(cond, design, metric), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def clustered(df, col, seed):
    """Pooled share of `col` with a site-clustered 95% interval."""
    g = df.groupby("site")[col].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(g), (B, len(g)))
    bs = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
    return s.sum() / max(c.sum(), 1), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def fmt(t):
    return f"{t[0]:+.3f} ({t[1]:+.3f} to {t[2]:+.3f})"


def byte_vs_slot(byte_day, slot_day):
    """Whole-record recovery, byte frame against slot model, on the same (site, day) set, per (Q, cond, design)."""
    out = {}
    for (Q, cond, dsg), z in byte_day.groupby(["Q", "cond", "design"]):
        s = slot_day[(slot_day.Q == Q) & (slot_day.cond == cond) & (slot_day.design == dsg)]
        m = z.merge(s[["site", "day", "rec_full"]], on=["site", "day"], how="inner", suffixes=("_byte", "_slot"))
        if len(m):
            out[(int(Q), cond, dsg)] = (float(m.rec_full_byte.mean()), float(m.rec_full_slot.mean()), len(m))
    return out


def verdicts(AB, checks, rt, integ, h8):
    """AB: {Q: Agg of the byte check}. checks: counts for H1. rt: round-trip rows. integ: {(design, Q): clustered false share}.
    h8: byte_vs_slot output. Columns: type of statement (test, known limit, code check, analytic bound) and verdict."""
    rows = []

    def add(hid, kind, text, value, ok):
        rows.append({"id": hid, "type": kind, "statement": text, "result": value,
                     "verdict": "not a test" if ok is None else ("pass" if ok else "fail")})

    rt_bad = int((rt.ok == False).sum())          # noqa: E712  (None = not buildable, not a mismatch)
    rt_n = int(rt.ok.notna().sum())
    ok1 = checks["byte_wrong"] == 0 and checks["slot_wrong"] == 0 and checks["mismatch"] == 0 and checks["dec_error"] == 0 and rt_bad == 0
    add("H1", "code check (holds by construction under assumption R)",
        "no wrong decision (byte check and slot model, Q 6 and 12, both loss models), no decoded value that differs from the plan, "
        "no decision-layer error, and no byte round-trip mismatch on any analysed day",
        f"byte wrong max {checks['byte_wrong']:.3f}; slot wrong max {checks['slot_wrong']:.3f}; value mismatches {checks['mismatch']}; "
        f"decision-layer errors {checks['dec_error']}; round trip {rt_bad} mismatches in {rt_n} blocks "
        f"({int(rt.ok.isna().sum())} not buildable); byte days without a 3b block {checks['unbuilt']}", ok1)
    cells = [(Q, c) for Q in QS for c in CONDS]
    d = [AB[Q].diff(c, "heur", "flagsrec", "hard_alt") for Q, c in cells]
    add("H2", "test", f"byte level: 3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= {T['H2_lower']} "
                      "(Q 6 and 12, both loss models)", " / ".join(fmt(x) for x in d), all(x[1] >= T["H2_lower"] for x in d))
    d = [AB[Q].diff(c, "heur", "rec", "hard_alt") for Q, c in cells]
    add("H3", "test", f"byte level: 3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= {T['H3_lower']} "
                      "(all four)", " / ".join(fmt(x) for x in d), all(x[1] >= T["H3_lower"] for x in d))
    d = [AB[Q].diff(c, "heur", "rec", "rec") for Q, c in cells]
    lim = [T["H4_lower_q6"] if Q == 6 else T["H4_lower_q12"] for Q, c in cells]
    add("H4", "test", f"byte level: cost of the post-hoc adopted design, 3b rule minus record only, whole record recovered, lower "
                      f"bound >= {T['H4_lower_q6']} (Q 6) and >= {T['H4_lower_q12']} (Q 12), both loss models",
        " / ".join(fmt(x) for x in d), all(x[1] >= m for x, m in zip(d, lim)))
    d = [AB[6].diff(c, "heur", "flagsrec", "hard_cfg") for c in CONDS]
    add("H6", "known limit (flags are exact at the configured thresholds by construction)",
        f"byte level: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus flagsrec) "
        f"< {T['H6_upper']} (Q 6, both loss models)", " / ".join(fmt(x) for x in d), all(x[2] < T["H6_upper"] for x in d))
    parts = []
    for (dsg, Q), (p, lo, hi) in sorted(integ.items()):
        f = per_million(Q)
        parts.append(f"{dsg} Q{Q}: {f * p:.4f} (upper {f * hi:.4f}; ceiling {f:.3f})")
    add("H7", "analytic bound (cannot fail: the ceiling with a conditional share of 1 is below any useful limit)",
        f"expected false-certificate days per million days at bit-error rate {BER:g} under random corruption",
        "; ".join(parts), None)
    parts, ok = [], True
    for (Q, c, dsg), (b, s, n) in sorted(h8.items()):
        if dsg != "rec":
            continue
        parts.append(f"Q{Q} {c}: byte {b:.3f}, slot {s:.3f}, |diff| {abs(b - s):.3f} ({n} days)")
        ok &= abs(b - s) <= T["H8_rec"]
    ok &= len(parts) == 4
    add("H8", "code check (the slot model of the record only is the frame's code)",
        f"record only: byte frame and slot model agree in whole-record recovery, |difference| <= {T['H8_rec']} (Q 6 and 12, both loss models)",
        "; ".join(parts), ok)
    return pd.DataFrame(rows)


def kind_table(dirname, Q, seed, designs, label):
    """Descriptive: hard cases at unanticipated and configured thresholds per kind (DO, pH, conductance, 7DADM window)."""
    parts = []
    for f in sorted(glob.glob(f"{dirname}/*_Q{Q}.csv")):
        if f.endswith("_meta.csv") or os.path.getsize(f) < 10:
            continue
        d = pd.read_csv(f, dtype={"site": str})
        m = pd.read_csv(f.replace(f"_Q{Q}.csv", f"_Q{Q}_meta.csv"), dtype={"site": str})
        for kind in pe.KINDS:
            z = d[d.kind == kind]
            for v in pe.SCEN:
                h = m[["site", "day", f"hard_{kind}_{v}"]].rename(columns={f"hard_{kind}_{v}": "hard"})
                t = z[["site", "day", "cond", "design", f"dc_{v}"]].rename(columns={f"dc_{v}": "dc"}).merge(h, on=["site", "day"])
                t = t[t.dc.notna() & t.hard.notna()]
                t = t[t.hard.astype(bool)]
                g = t.groupby(["site", "cond", "design"]).dc.agg(["sum", "count"]).reset_index()
                g["metric"] = f"{kind}_{'cfg' if v == 'cfg' else 'alt'}"
                parts.append(g)
    g = pd.concat(parts).groupby(["site", "cond", "design", "metric"])[["sum", "count"]].sum().reset_index()
    a = Agg(g, seed)
    lines = [f"\n{label}, Q = {Q}: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)"]
    for c in CONDS:
        for kind in pe.KINDS:
            for which in ("alt", "cfg"):
                met = f"{kind}_{which}"
                if (c, "heur", met) not in a.S or (c, "flagsrec", met) not in a.S:
                    continue
                lv = " / ".join(f"{dn} {a.point(c, dn, met):.3f}" for dn in designs if (c, dn, met) in a.S)
                lines.append(f"  {c} {met:9s} {lv}; 3b minus flagsrec {fmt(a.diff(c, 'heur', 'flagsrec', met))}; "
                             f"3b minus record {fmt(a.diff(c, 'heur', 'rec', met))}")
    return lines


def secondary(AB, AS, bytedir, slotdir, integ_df, h8, res_count, n_sites):
    lines = ["", "## Descriptive results (no verdict)", "",
             f"Assumption R (reporting resolution inferred from the record): {res_count[0]} of {n_sites} analysed sites have an inferred "
             f"resolution for at least one of DO, pH, temperature; per parameter: {res_count[1]}."]
    for label, A, designs in (("Byte check (hypotheses)", AB, BYTE_DESIGNS), ("Slot model (cross-check)", AS, DESIGNS)):
        for Q in QS:
            for c in CONDS:
                lines.append(f"\n{label}, Q = {Q}, {c}: pooled level (record recovered / hard configured / hard unanticipated / all configured)")
                for dn in designs:
                    lines.append(f"  {dn:9s} " + " / ".join(f"{A[Q].point(c, dn, m):.3f}" for m in ("rec", "hard_cfg", "hard_alt", "all_cfg")))
    for Q in QS:
        lines += kind_table(bytedir, Q, SEED + 10 + Q, BYTE_DESIGNS, "Byte check")
    lines.append("\nWhole-record recovery, byte frame against slot model (the slot model gives the layered group whole slots, so it is "
                 "pessimistic for the 3b rule):")
    for (Q, c, dsg), (b, s, n) in sorted(h8.items()):
        lines.append(f"  Q={Q:2d} {c:16s} {dsg:9s} byte {b:.3f}, slot {s:.3f}, difference {b - s:+.3f} ({n} days)")
    lines.append("\nIntegrity, given one CRC-valid forgery (header or body): classes of day (share of draws / false-certificate share in "
                 "class); rejected share; day with a wrong decision (point, site-clustered 95% interval); decision-layer errors")
    for (dsg, Q), z in integ_df.groupby(["design", "Q"]):
        wd = clustered(z, "day_wrong_decision", SEED + 2)
        lines.append(f"  {dsg:5s} Q={Q:2d}: " + "; ".join(f"{c} {len(y) / len(z):.2f}/{y.day_false.mean():.4f}" for c, y in z.groupby("cls"))
                     + f"; rejected {z.rejected.mean():.3f}; wrong decision {wd[0]:.4f} ({wd[1]:.4f} to {wd[2]:.4f}); "
                     f"errors {int(z.dec_error.sum())}")
    return lines


def resolution_count(files, tag):
    n, per = 0, {"DO": 0, "pH": 0, "T": 0}
    for f in files:
        _s, _items, res = prepare_items(f, tag)
        n += any(v is not None for v in res.values())
        for p in per:
            per[p] += res.get(p) is not None
    return n, per


# ------------------------------------------------------------------ main
def stage(log, name, files, fn, tag, outdir):
    os.makedirs(outdir, exist_ok=True)
    t0, reused = time.time(), 0
    for i, f in enumerate(files, 1):
        s, was = fn(f, tag, outdir)
        reused += was
        log(f"{name} {i}/{len(files)} {s}" + (" (existing output reused)" if was else ""))
    log(f"{name} done in {(time.time() - t0) / 60:.1f} min; {reused} site outputs reused")


def slot_site(f, tag, outdir):
    site = os.path.basename(f)[:-4]
    was = all(os.path.exists(f"{outdir}/{site}_Q{Q}{s}.csv") for Q in QS for s in ("", "_meta"))
    pb.run_site((f, tag, outdir, DESIGNS, FLAG_CAP, SLOTS))
    return site, was


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    folder, tag = sys.argv[1], sys.argv[2]
    confirm = tag == CONFIRM_TAG
    seal = sys.argv[3] if confirm and len(sys.argv) > 3 else None
    only = set(sys.argv[3:]) if not confirm else set()
    check_environment()
    if confirm:
        if not seal:
            sys.exit("refusing to run: the confirmatory tag requires the seal file as the third argument")
        n_hashed, commit = verify_freeze()
        limits = plan_limits(PLAN)
        if limits != T:
            sys.exit(f"refusing to run: limits in the code {T} differ from the plan's LIMITS line {limits}")
        check_seal_covers(seal, folder)
        if subprocess.run([sys.executable, "-I", "src/data/seal.py", "verify", seal]).returncode:
            sys.exit("refusing to run: the seal does not verify")
        names = {os.path.basename(f)[:-4] for f in glob.glob(os.path.join(folder, "*.csv"))}
        extra = names - selected_sites()
        if extra:
            sys.exit("refusing to run: the cohort folder holds sites outside the selection: " + ", ".join(sorted(extra)))
        check_stamp(tag, f"freeze {commit}", strict=True)
    elif "new4" in folder or "2022" in folder:
        sys.exit("refusing to run: the cohort-4 folder may only be opened by the confirmatory tag")
    os.makedirs(f"results/{tag}/plans", exist_ok=True)
    log = Log(f"results/{tag}/RUN4.log")
    log("=" * 20 + (" CONFIRMATORY RUN" if confirm else " REHEARSAL (not confirmatory)"))
    if confirm:
        log(f"freeze verified against tag {FREEZE_TAG} ({commit}): {n_hashed} hashed files unchanged; limits equal the plan; "
            f"seal {seal} covers the folder and verifies; run stamp ok")
        log(f"cohort sites present: {len(names)} of {len(selected_sites())} selected; missing: {sorted(selected_sites() - names)}")
    else:
        warn = check_stamp(tag, f"rehearsal {git('rev-parse', 'HEAD') or 'unknown'}", strict=False)
        if warn:
            log("WARNING (rehearsal): " + warn)
    run_record(log, folder, tag, seal)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if only:
        paths = [p for p in paths if os.path.basename(p)[:-4] in only]
    t0 = time.time()
    for i, f in enumerate(paths, 1):
        cache = f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl"
        was = os.path.exists(cache)
        site_plans(f, cache)
        log(f"plans {i}/{len(paths)} {os.path.basename(f)[:-4]}" + (" (existing output reused)" if was else ""))
    log(f"plans done in {(time.time() - t0) / 60:.1f} min")
    files = analysis_sites(paths, tag)
    log(f"{len(files)} sites in the analysis population (at least {MIN_DAYS} four-parameter days): "
        + ", ".join(os.path.basename(f)[:-4] for f in files))
    if not files:
        sys.exit("no site in the analysis population")
    slotdir, bytedir = f"results/{tag}/slot4", f"results/{tag}/byte4"
    stage(log, "slot model", files, slot_site, tag, slotdir)
    f3.CRCB, f3.RECCRC = CRCB, RECCRC
    stage(log, "byte check", files, byte_site, tag, bytedir)
    stage(log, "integrity", files, integrity_site, tag, f"results/{tag}/integ4")
    names = [os.path.basename(f)[:-4] for f in files]
    rt = pd.concat([pd.read_csv(f"{bytedir}/{s}_roundtrip.csv", dtype={"site": str}) for s in names])
    integ_df = pd.concat([pd.read_csv(f"results/{tag}/integ4/{s}.csv", dtype={"site": str}) for s in names])
    cols = ["site", "day", "Q", "cond", "design", "kind", "rec_full"]
    slot_day = pd.concat([pd.read_csv(f"{slotdir}/{s}_Q{Q}.csv", dtype={"site": str}, usecols=cols) for s in names for Q in QS])
    byte_all = pd.concat([pd.read_csv(f"{bytedir}/{s}_Q{Q}.csv", dtype={"site": str}) for s in names for Q in QS])
    byte_day = byte_all[byte_all.kind == "day"]
    GB = {Q: pe.load_agg(tag, Q, "byte4") for Q in QS}
    GS = {Q: pe.load_agg(tag, Q, "slot4") for Q in QS}
    AB = {Q: Agg(GB[Q]) for Q in QS}
    AS = {Q: Agg(GS[Q], SEED + 3) for Q in QS}
    n_rec = byte_day[byte_day.design == "rec"].groupby(["Q", "cond"]).size()
    n_heur = byte_day[byte_day.design == "heur"].groupby(["Q", "cond"]).size()
    checks = {"byte_wrong": max(float(GB[Q].query("metric == 'wrong'")["sum"].max()) for Q in QS),
              "slot_wrong": max(float(GS[Q].query("metric == 'wrong'")["sum"].max()) for Q in QS),
              "mismatch": int(byte_day.mismatch.sum()), "dec_error": int(byte_day.dec_error.sum()),
              "unbuilt": int((n_rec - n_heur.reindex(n_rec.index, fill_value=0)).sum())}
    integ = {(dsg, int(Q)): clustered(z, "day_false", SEED + 1) for (dsg, Q), z in integ_df.groupby(["design", "Q"])}
    h8 = byte_vs_slot(byte_day, slot_day[slot_day.kind == "day"])
    v = verdicts(AB, checks, rt, integ, h8)
    v.to_csv(f"results/{tag}/verdicts4.csv", index=False)
    head = "# Verdicts of the version 3 confirmation" + ("" if confirm else " (REHEARSAL on development data, not confirmatory)")
    text = head + "\n\n" + v.to_markdown(index=False) + "\n" + "\n".join(
        secondary(AB, AS, bytedir, slotdir, integ_df, h8, resolution_count(files, tag), len(files)))
    open(f"results/{tag}/verdicts4.md", "w", encoding="utf-8").write(text + "\n")
    print(text)
    tests = v[v.type == "test"]
    log(f"verdicts written: results/{tag}/verdicts4.md; tests passed {int((tests.verdict == 'pass').sum())} of {len(tests)} "
        f"(H2, H3, H4); all rows: {dict(zip(v.id, v.verdict))}")
    open(f"results/{tag}/done4.flag", "w").write(datetime.datetime.now().isoformat() + "\n")


if __name__ == "__main__":
    main()
