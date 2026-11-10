"""Confirmation of method version 3 (cohort 4): run ONCE on the sealed cohort after the freeze.
Pre-registration: docs/CONFIRM4_PLAN.md (the limits in T below are copied from it and frozen with the code).
Counterpart of the frozen src/p3/confirm3.py; differences: frame3 with CRC-24 per message (setting D2), slot model with 4 slots
(src/p3v3/proto_base4.py, designs rec, heur, flags, flagsrec), hardened receiver (src/p3v3/receiver3.py), guarded bounds
(src/p3v3/certlang3.py), no environment switches (the run refuses to start if any P3_* variable is set), a run log with library
versions and every setting, and per-site resumable stages.

Stages (every one resumable per site; outputs under results/<tag>/):
  1. plans of every record day (plans/)                      4. byte check: real messages, losses, receiver3, decisions (byte4/)
  2. analysis population (at least MIN_DAYS days)            5. integrity: forced CRC-valid forgery of one message (integ4/)
  3. slot model, identical loss draws for all designs (slot4/)  6. verdicts H1 to H8 and descriptive tables (verdicts4.md, .csv)
Byte round trip (H1): every analysed day, record only and the 3b rule, Q = 6 and 12, all messages, must decode exactly.

Usage (from Paper3/):
  python -I src/p3v3/confirm4.py <folder> confirm4 <seal file>       confirmatory run (needs the freeze tag and docs/FREEZE4.md)
  python -I src/p3v3/confirm4.py <folder> <other tag> [site ...]     rehearsal on development data (NOT confirmatory)
Nothing in this file reads the cohort before stage 1 of the confirmatory run.
"""
import datetime
import glob
import os
import platform
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
from p3 import proto_base_eval as pe  # noqa: E402
from p3 import proto_queries as pq  # noqa: E402
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
SLOTS, FLAG_CAP = 4, 3.0              # slot model of the D2 frame: 4 value slots per message, flags take one
DESIGNS = ("rec", "heur", "flags", "flagsrec")
MIN_DAYS = 100                        # analysis population: sites with at least this many four-parameter days
B = 1000                              # bootstrap resamples (site-clustered)
SEED = 20261115                       # bootstrap and byte-check seed (slot model keeps proto_base4.SEED)
BYTE_EVERY, BYTE_DRAWS = 1, 20        # byte check: every n-th analysed day, loss draws per day and condition
INT_EVERY, INT_DRAWS = 3, 8           # integrity: every n-th analysed day, forged draws per day and block
P_LOSS = 0.3                          # integrity: independent loss before the forgery
BER = 1e-3                            # integrity: assumed bit-error rate (no channel was measured)
T_BAND_EXPECTED, UNKNOWN_EXPECTED = 3.0, True     # src/p3/proto_queries.py defaults; the run refuses other values
CONDS = ("iid_p0.3", "gilbert_p0.3_b3")
BYTE_CONDS = (("iid_p0.3", ("iid", 0.3, None)), ("gilbert_p0.3_b3", ("gilbert", 0.3, 3)))
QS = (6, 12)
T = {"H2_lower": 0.10, "H3_lower": 0.10, "H4_lower_q6": -0.15, "H4_lower_q12": -0.10, "H5_lower": -0.06,
     "H6_upper": 0.0, "H7_per_million": 0.5, "H8_rec": 0.01, "H8_heur": 0.06}
WMAP = {"DOmin": ("W", "DO"), "pHmin": ("W", "pHmin"), "pHmax": ("W", "pHmax"), "Tmax": ("W", "T"), "ECa": ("W", "ECa"), "ECb": ("W", "ECb")}
KINDS = (("do", 0), ("ph", 1), ("ec", 2))
ALT = ("alt1", "alt2")
VARIANT = {"rec": "record", "heur": "3b"}


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
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def verify_freeze():
    """The code that runs is the code that was approved: the tag exists, tracked method files equal the tag and are clean, and
    every file hashed in the freeze record still has its recorded MD5."""
    from data.seal import md5
    if not os.path.exists(FREEZE_RECORD):
        sys.exit(f"refusing to run: {FREEZE_RECORD} is missing (run src/p3v3/freeze4.py after the authors tag the repository)")
    if not git("rev-list", "-n", "1", FREEZE_TAG):
        sys.exit(f"refusing to run: tag {FREEZE_TAG} does not exist")
    paths = ["src", "tests", "tools", PLAN, SELECTION]
    diff = git("diff", "--name-only", FREEZE_TAG, "--", *paths)
    dirty = git("status", "--porcelain", "--", *paths)
    if diff or dirty:
        sys.exit(f"refusing to run: method files differ from {FREEZE_TAG}:\n{diff}\n{dirty}")
    bad, n = [], 0
    for line in open(FREEZE_RECORD, encoding="utf-8"):
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(parts) == 2 and parts[0].startswith("`") and len(parts[1]) == 32:
            n += 1
            f = parts[0].strip("`")
            if not os.path.exists(f) or md5(f) != parts[1]:
                bad.append(f)
    if bad or not n:
        sys.exit("refusing to run: files differ from the freeze record: " + (", ".join(bad) or "no hashed files listed"))
    return n


def selected_sites():
    s = pd.read_csv(SELECTION, dtype={"site_no": str})
    return set(s.loc[s.selected.astype(str).str.lower() == "true", "site_no"])


def run_record(log, folder, tag, seal):
    import scipy
    log(f"command: {' '.join([sys.executable] + sys.argv)}")
    log(f"python {platform.python_version()} ({platform.platform()}); numpy {np.__version__}; pandas {pd.__version__}; scipy {scipy.__version__}")
    log(f"git HEAD {git('rev-parse', 'HEAD') or 'unknown'}; freeze tag {FREEZE_TAG} -> {git('rev-list', '-n', '1', FREEZE_TAG) or 'missing'}")
    log(f"folder {folder}; tag {tag}; seal {seal or 'none (rehearsal)'}")
    log(f"frame3 CRCB={f3.CRCB} RECCRC={f3.RECCRC}; slot model SLOTS={SLOTS} FLAG_CAP={FLAG_CAP} designs={DESIGNS} seed={pb.SEED}")
    log(f"proto_queries T_BAND={pq.T_BAND} UNKNOWN_HARD={pq.UNKNOWN_HARD}; MIN_DAYS={MIN_DAYS} B={B} SEED={SEED}")
    log(f"byte check every {BYTE_EVERY} day(s), {BYTE_DRAWS} draws; integrity every {INT_EVERY} day(s), {INT_DRAWS} draws, "
        f"loss {P_LOSS}, bit-error rate {BER:g}; limits {T}")


# ------------------------------------------------------------------ stage 2: population
def analysis_sites(paths, tag):
    keep = []
    for f in paths:
        site = os.path.basename(f)[:-4]
        P = pd.read_pickle(f"results/{tag}/plans/{site}.pkl")
        if sum(1 for v in P.values() if v["four"]) >= MIN_DAYS:
            keep.append(f)
    return keep


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


def byte_site(path, tag, outdir):
    """Byte check of one site: round trip on every analysed day; recovery and decisions under loss on every BYTE_EVERY-th day."""
    site = os.path.basename(path)[:-4]
    out = f"{outdir}/{site}.csv"
    out_rt = f"{outdir}/{site}_roundtrip.csv"
    if os.path.exists(out) and os.path.exists(out_rt):
        return site
    rng = np.random.default_rng([SEED, 4, re2.site_number(site)])
    site, items, res = prepare_items(path, tag)
    rows, rts = [], []
    for k, it in enumerate(items):
        for variant in ("rec", "heur"):
            for Q in QS:
                rts.append((site, it["d"], variant, Q, roundtrip_day(it, Q, variant)))
        if k % BYTE_EVERY:
            continue
        it["meta"] = pb.day_meta(it)
        vals, bound, n = it["vals"], it["bound"], len(it["vals"])
        for variant in ("rec", "heur"):
            for Q in QS:
                try:
                    blk, _lay, _host = i3.build(it, Q, VARIANT[variant])
                except ValueError:
                    continue
                for cname, c in BYTE_CONDS:
                    masks = rr.sim_masks(c, Q, rng, draws=BYTE_DRAWS)
                    memo = {}
                    full = ok_alt = n_alt = wrong = mismatch = 0
                    for m in masks:
                        keep = [i for i in range(Q) if m[i]]
                        d = r3.receive([blk.messages[i] for i in keep], n_of=it["rd"].n_of) if keep else f3.Decoded()
                        if d.record_rejected:
                            good = set()
                        else:
                            good = {p for p, v in d.values.items() if p < n and v == vals[p]}
                            mismatch += len(d.values) - len(good)
                        key = frozenset({("R", p) for p in good} | ({WMAP[w] for w in d.witness} if not d.witness_rejected else set()))
                        full += bool(bound) and len(good) == n
                        if key not in memo:
                            memo[key] = pb.decide(it, pb.know(it, vals, bound, key, res, "pla", 1.0))[0]
                        dec = memo[key]
                        for v in pb.VAR:
                            for kind, idx in KINDS:
                                t = it["meta"]["truth"][v][kind]
                                x = dec[v][idx]
                                if t is not None and x is not None and x != -1 and x != int(t):
                                    wrong += 1
                        for v in ALT:
                            for kind, idx in KINDS:
                                t, h = it["meta"]["truth"][v][kind], it["meta"]["hard"][v][kind]
                                if t is None or h is None or not h:
                                    continue
                                x = dec[v][idx]
                                n_alt += 1
                                ok_alt += int(x is not None and x != -1 and x == int(t))
                    rows.append((site, it["d"], Q, cname, variant, full / BYTE_DRAWS, ok_alt, n_alt, wrong, mismatch))
    pd.DataFrame(rts, columns=["site", "day", "design", "Q", "ok"]).to_csv(out_rt + ".tmp", index=False)
    pd.DataFrame(rows, columns=["site", "day", "Q", "cond", "design", "full", "ok_alt", "n_alt", "wrong", "mismatch"]).to_csv(out + ".tmp", index=False)
    os.replace(out_rt + ".tmp", out_rt)
    os.replace(out + ".tmp", out)
    return site


# ------------------------------------------------------------------ stage 5: integrity
def integrity_site(path, tag, outdir):
    """Forced CRC-valid forgery of one arrived message (body bytes, check recomputed), D2 frame, receiver3 with sanity and
    corroboration; record only and the 3b rule, Q = 6 and 12 (as src/p3v3/integrity3.py, design D2)."""
    site = os.path.basename(path)[:-4]
    out = f"{outdir}/{site}.csv"
    if os.path.exists(out):
        return site
    rng = np.random.default_rng([SEED, 5, re2.site_number(site)])
    site, items, _ = prepare_items(path, tag)
    rows = []
    for it in items[::INT_EVERY]:
        truth = i3.witness_dict(it)
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
                    msgs = [blk.messages[i] if i != j else i3.forge(blk.messages[i], rng) for i in arrive]
                    d = r3.receive(msgs, n_of=it["rd"].n_of)
                    bad = i3.false_certified(it, d)
                    wbad = sum(1 for k, c in d.witness.items() if truth.get(k) is not None and c != truth[k])
                    N = len(arrive)
                    cls = "uncoded" if not blk.coded else ("N=K" if N == need else ("N<K" if N < need else "N>K"))
                    rows.append((site, it["d"], variant, Q, N, need, cls, int(bool(bad or wbad)), int(bool(d.record_rejected or d.witness_rejected))))
    pd.DataFrame(rows, columns=["site", "day", "design", "Q", "arrived", "need", "cls", "day_false", "rejected"]).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    return site


def per_million(Q):
    """Expected false-certificate days per million days per unit of conditional share: expected arrived messages x P(a message
    is corrupted at BER) x P(a corrupted message passes the CRC-24)."""
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


def byte_vs_slot(byte, slot_day):
    """H8: whole-record recovery, byte frame against slot model, on the same (site, day) set, per (Q, cond, design)."""
    out = {}
    for (Q, cond, dsg), z in byte.groupby(["Q", "cond", "design"]):
        s = slot_day[(slot_day.Q == Q) & (slot_day.cond == cond) & (slot_day.design == dsg)]
        m = z.merge(s[["site", "day", "rec_full"]], on=["site", "day"], how="inner")
        out[(int(Q), cond, dsg)] = (float(m.full.mean()), float(m.rec_full.mean()), len(m))
    return out


def verdicts(A, wrong_slot, byte, rt, integ, h8):
    rows = []

    def add(hid, text, value, ok):
        rows.append({"id": hid, "statement": text, "result": value, "supported": bool(ok)})

    rt_bad = int((rt.ok == False).sum())          # noqa: E712  (None = not buildable, not a mismatch)
    rt_n = int(rt.ok.notna().sum())
    wb, mm = int(byte.wrong.sum()), int(byte.mismatch.sum())
    add("H1", "no wrong decision in any design (slot model: Q 6 and 12, both loss models; byte check), no decoded value that "
              "differs from the plan, and no byte round-trip mismatch on any analysed day",
        f"slot model wrong max {wrong_slot:.3f}; byte check wrong {wb}, value mismatches {mm}; round trip {rt_bad} mismatches in "
        f"{rt_n} blocks ({int(rt.ok.isna().sum())} not buildable)", wrong_slot == 0 and wb == 0 and mm == 0 and rt_bad == 0)
    cells = [(Q, c) for Q in QS for c in CONDS]
    d = [A[Q].diff(c, "heur", "flagsrec", "hard_alt") for Q, c in cells]
    add("H2", f"3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= {T['H2_lower']} (Q 6 and 12, both loss models)",
        " / ".join(fmt(x) for x in d), all(x[1] >= T["H2_lower"] for x in d))
    d = [A[Q].diff(c, "heur", "rec", "hard_alt") for Q, c in cells]
    add("H3", f"3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= {T['H3_lower']} (all four)",
        " / ".join(fmt(x) for x in d), all(x[1] >= T["H3_lower"] for x in d))
    d = [A[Q].diff(c, "heur", "rec", "rec") for Q, c in cells]
    lim = [T["H4_lower_q6"] if Q == 6 else T["H4_lower_q12"] for Q, c in cells]
    add("H4", f"declared cost: 3b rule minus record only, whole record recovered, lower bound >= {T['H4_lower_q6']} (Q 6) and "
              f">= {T['H4_lower_q12']} (Q 12), both loss models",
        " / ".join(fmt(x) for x in d), all(x[1] >= m for x, m in zip(d, lim)))
    d = [A[Q].diff(c, "heur", "flagsrec", "rec") for Q, c in cells]
    add("H5", f"3b rule minus flagsrec, whole record recovered, lower bound >= {T['H5_lower']} (all four)",
        " / ".join(fmt(x) for x in d), all(x[1] >= T["H5_lower"] for x in d))
    d = [A[6].diff(c, "heur", "flagsrec", "hard_cfg") for c in CONDS]
    add("H6", f"known limit: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus "
              f"flagsrec) < {T['H6_upper']} (Q 6, both loss models)",
        " / ".join(fmt(x) for x in d), all(x[2] < T["H6_upper"] for x in d))
    parts, ok = [], len(integ) == 4
    for (dsg, Q), (p, lo, hi) in sorted(integ.items()):
        f = per_million(Q)
        parts.append(f"{dsg} Q{Q}: {f * p:.4f} (upper {f * hi:.4f})")
        ok &= f * hi <= T["H7_per_million"]
    add("H7", f"integrity: expected false-certificate days per million days at bit-error rate {BER:g}, upper bound <= "
              f"{T['H7_per_million']} (record only and 3b rule, Q 6 and 12)", "; ".join(parts), ok)
    parts, ok = [], len(h8) == 8
    for (Q, c, dsg), (b, s, n) in sorted(h8.items()):
        lim = T["H8_rec"] if dsg == "rec" else T["H8_heur"]
        parts.append(f"{dsg} Q{Q} {c}: byte {b:.3f}, slot {s:.3f}, |diff| {abs(b - s):.3f} (limit {lim}, {n} days)")
        ok &= abs(b - s) <= lim
    add("H8", f"byte frame reproduces the slot model in whole-record recovery: |difference| <= {T['H8_rec']} (record only) and "
              f"<= {T['H8_heur']} (3b rule), Q 6 and 12, both loss models", "; ".join(parts), ok)
    return pd.DataFrame(rows)


def kind_table(slotdir, Q, seed):
    """Descriptive: hard cases at unanticipated and configured thresholds per kind (DO, pH, conductance, 7DADM window)."""
    parts = []
    for f in sorted(glob.glob(f"{slotdir}/*_Q{Q}.csv")):
        if f.endswith("_meta.csv") or os.path.getsize(f) < 10:
            continue
        d = pd.read_csv(f, dtype={"site": str})
        m = pd.read_csv(f.replace(f"_Q{Q}.csv", f"_Q{Q}_meta.csv"), dtype={"site": str})
        for kind in pe.KINDS:
            z = d[d.kind == kind]
            for v in pe.SCEN:
                h = m[["site", "day", f"hard_{kind}_{v}"]].rename(columns={f"hard_{kind}_{v}": "hard"})
                t = z[["site", "day", "cond", "design", f"dc_{v}"]].rename(columns={f"dc_{v}": "dc"}).merge(h, on=["site", "day"])
                t = t[t.dc.notna() & t.hard.notna() & t.hard.astype(bool)]
                g = t.groupby(["site", "cond", "design"]).dc.agg(["sum", "count"]).reset_index()
                g["metric"] = f"{kind}_{'cfg' if v == 'cfg' else 'alt'}"
                parts.append(g)
    g = pd.concat(parts).groupby(["site", "cond", "design", "metric"])[["sum", "count"]].sum().reset_index()
    a = Agg(g, seed)
    lines = [f"\nQ = {Q}: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)"]
    for c in CONDS:
        for kind in pe.KINDS:
            for which in ("alt", "cfg"):
                met = f"{kind}_{which}"
                if (c, "heur", met) not in a.S:
                    continue
                lv = " / ".join(f"{dn} {a.point(c, dn, met):.3f}" for dn in DESIGNS if (c, dn, met) in a.S)
                lines.append(f"  {c} {met:9s} {lv}; 3b minus flagsrec {fmt(a.diff(c, 'heur', 'flagsrec', met))}; "
                             f"3b minus record {fmt(a.diff(c, 'heur', 'rec', met))}")
    return lines


def secondary(A, slotdir, integ_df, byte, res_count, n_sites):
    lines = ["", "## Descriptive results (no verdict)", "",
             f"Assumption R (reporting resolution inferred from the record): {res_count[0]} of {n_sites} analysed sites have an inferred "
             f"resolution for at least one of DO, pH, temperature; per parameter: {res_count[1]}."]
    for Q in QS:
        for c in CONDS:
            lines.append(f"\nQ = {Q}, {c}: pooled level (record recovered / hard configured / hard unanticipated / all configured)")
            for dn in DESIGNS:
                lines.append(f"  {dn:9s} " + " / ".join(f"{A[Q].point(c, dn, m):.3f}" for m in ("rec", "hard_cfg", "hard_alt", "all_cfg")))
    for Q in QS:
        lines += kind_table(slotdir, Q, SEED + 10 + Q)
    lines.append("\nByte check: hard cases at unanticipated thresholds decided correctly (pooled), record recovered")
    for (Q, c, dsg), z in byte.groupby(["Q", "cond", "design"]):
        lines.append(f"  Q={Q:2d} {c:16s} {dsg:5s} {z.ok_alt.sum() / max(z.n_alt.sum(), 1):.3f}, {z.full.mean():.3f} ({len(z)} days)")
    lines.append("\nIntegrity: classes of day among forged draws (share of draws / false share in class)")
    for (dsg, Q), z in integ_df.groupby(["design", "Q"]):
        lines.append(f"  {dsg:5s} Q={Q:2d}: " + "; ".join(f"{c} {len(y) / len(z):.2f}/{y.day_false.mean():.4f}" for c, y in z.groupby("cls"))
                     + f"; rejected {z.rejected.mean():.3f}")
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
    t0 = time.time()
    for i, f in enumerate(files, 1):
        s = fn(f, tag, outdir)
        log(f"{name} {i}/{len(files)} {s}")
    log(f"{name} done in {(time.time() - t0) / 60:.1f} min")


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
        n_hashed = verify_freeze()
        if subprocess.run([sys.executable, "-I", "src/data/seal.py", "verify", seal]).returncode:
            sys.exit("refusing to run: the seal does not verify")
        names = {os.path.basename(f)[:-4] for f in glob.glob(os.path.join(folder, "*.csv"))}
        extra = names - selected_sites()
        if extra:
            sys.exit("refusing to run: the cohort folder holds sites outside the selection: " + ", ".join(sorted(extra)))
    elif "new4" in folder or "2022" in folder:
        sys.exit("refusing to run: the cohort-4 folder may only be opened by the confirmatory tag")
    os.makedirs(f"results/{tag}/plans", exist_ok=True)
    log = Log(f"results/{tag}/RUN4.log")
    log("=" * 20 + (" CONFIRMATORY RUN" if confirm else " REHEARSAL (not confirmatory)"))
    if confirm:
        log(f"freeze verified against tag {FREEZE_TAG}: {n_hashed} hashed files unchanged; seal {seal} verified")
        log(f"cohort sites present: {len(names)} of {len(selected_sites())} selected; missing: {sorted(selected_sites() - names)}")
    run_record(log, folder, tag, seal)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if only:
        paths = [p for p in paths if os.path.basename(p)[:-4] in only]
    t0 = time.time()
    for i, f in enumerate(paths, 1):
        site_plans(f, f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl")
        log(f"plans {i}/{len(paths)} {os.path.basename(f)[:-4]}")
    log(f"plans done in {(time.time() - t0) / 60:.1f} min")
    files = analysis_sites(paths, tag)
    log(f"{len(files)} sites in the analysis population (at least {MIN_DAYS} four-parameter days): "
        + ", ".join(os.path.basename(f)[:-4] for f in files))
    if not files:
        sys.exit("no site in the analysis population")
    slotdir = f"results/{tag}/slot4"
    stage(log, "slot model", files, lambda f, tg, od: pb.run_site((f, tg, od, DESIGNS, FLAG_CAP, SLOTS)), tag, slotdir)
    f3.CRCB, f3.RECCRC = CRCB, RECCRC                     # pb.run_site does not touch the frame; reassert anyway
    stage(log, "byte check", files, byte_site, tag, f"results/{tag}/byte4")
    stage(log, "integrity", files, integrity_site, tag, f"results/{tag}/integ4")
    names = [os.path.basename(f)[:-4] for f in files]
    byte = pd.concat([pd.read_csv(f"results/{tag}/byte4/{s}.csv", dtype={"site": str}) for s in names])
    rt = pd.concat([pd.read_csv(f"results/{tag}/byte4/{s}_roundtrip.csv", dtype={"site": str}) for s in names])
    integ_df = pd.concat([pd.read_csv(f"results/{tag}/integ4/{s}.csv", dtype={"site": str}) for s in names])
    slot_day = pd.concat([pd.read_csv(f"{slotdir}/{s}_Q{Q}.csv", dtype={"site": str}, usecols=["site", "day", "Q", "cond", "design", "kind", "rec_full"])
                          for s in names for Q in QS])
    slot_day = slot_day[slot_day.kind == "day"]
    G = {Q: pe.load_agg(tag, Q, "slot4") for Q in QS}
    A = {Q: Agg(G[Q]) for Q in QS}
    wrong_slot = max(float(G[Q].query("metric == 'wrong'")["sum"].max()) for Q in QS)
    integ = {(dsg, int(Q)): clustered(z, "day_false", SEED + 1) for (dsg, Q), z in integ_df.groupby(["design", "Q"])}
    h8 = byte_vs_slot(byte, slot_day)
    v = verdicts(A, wrong_slot, byte, rt, integ, h8)
    v.to_csv(f"results/{tag}/verdicts4.csv", index=False)
    head = "# Verdicts of the version 3 confirmation" + ("" if confirm else " (REHEARSAL on development data, not confirmatory)")
    text = head + "\n\n" + v.to_markdown(index=False) + "\n" + "\n".join(
        secondary(A, slotdir, integ_df, byte, resolution_count(files, tag), len(files)))
    open(f"results/{tag}/verdicts4.md", "w", encoding="utf-8").write(text + "\n")
    print(text)
    log(f"verdicts written: results/{tag}/verdicts4.md; supported {int(v.supported.sum())} of {len(v)}")
    open(f"results/{tag}/done4.flag", "w").write(datetime.datetime.now().isoformat() + "\n")


if __name__ == "__main__":
    main()
