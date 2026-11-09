"""Third (final) confirmation of the decision-certificate method: run ONCE on the sealed cohort after the freeze.
Pre-registration: docs/CONFIRM3_PLAN.md (the thresholds below are copied from it and frozen with the code).

Steps: verify the cohort seal; plans of every record day; baseline and witness designs on identical loss draws
(src/p3/proto_base.py); byte-level round trip of frame v2 on every analysed day; forced-forgery integrity study
(src/p3/robust2.py); verdicts on H1 to H8 with site-clustered bootstrap intervals; descriptive secondary results.
Usage (from Paper3/):
  python -I src/p3/confirm3.py <folder> <tag> <seal file>        confirmatory run
  python -I src/p3/confirm3.py <folder> rehearsal3                rehearsal on development data (no seal; NOT confirmatory)
Every step is resumable per site; nothing in the verdict logic reads the cohort before the freeze.
"""
import glob
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import frame2 as f2  # noqa: E402
from p3 import proto_base_eval as pe  # noqa: E402
from p3 import robust2  # noqa: E402
from p3.proto_joint import prepare_items  # noqa: E402
from p3.run_multiday import site_plans  # noqa: E402

ADOPT_HYBRID = True               # authors' decision before the freeze (docs/CONFIRM3_PLAN.md, Section 7): adds hyb1 and H9
DESIGNS = ("rec", "heur", "ex1", "tight50", "sod_mds", "sod_once", "flags", "randmix") + (("hyb1", "hyb2") if ADOPT_HYBRID else ())
MIN_DAYS = 100                    # analysis population: sites with at least this many four-parameter days
B = 1000
SEED = 20261107
# ---- frozen thresholds (docs/CONFIRM3_PLAN.md, Section 4)
T = {"H2_lower": 0.15, "H3_lower": 0.05, "H4_lower": -0.12, "H5_flags_lower": 0.10, "H5_rec_lower": 0.10,
     "H6_margin": 0.005, "H9_alt_lower": 0.20, "H9_cfg_lower": -0.01, "H9_rec_lower": -0.01, "H8_record_q6": 0.06, "H8_record_q12": 0.01, "H8_layered_q6": 0.15, "H8_layered_q12": 0.02}
CONDS = ("iid_p0.3", "gilbert_p0.3_b3")


def run(cmd, env=None):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, env=dict(os.environ, **(env or {})))
    if r.returncode:
        sys.exit(f"step failed: {' '.join(cmd)}")


def analysis_sites(folder, tag):
    """Sites with at least MIN_DAYS four-parameter days with a plan."""
    keep = []
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        site = os.path.basename(f)[:-4]
        P = pd.read_pickle(f"results/{tag}/plans/{site}.pkl")
        if sum(1 for v in P.values() if v["four"]) >= MIN_DAYS:
            keep.append(f)
    return keep


def roundtrip(files, tag):
    """H1b: frame v2 byte-level round trip. Returns (days checked, mismatches)."""
    days = bad = 0
    for f in files:
        site, items, _ = prepare_items(f, tag)
        for it in items:
            vals, bound = it["vals"], it["bound"]
            truth_w = robust2.witness_codes(it)
            for Q, kw in ((12, 0), (6, 0), (12, 2)):
                lay = dict(truth_w) if kw else None
                try:
                    blk = f2.build_block(vals, bound, it["d"], Q, layered=lay, kw=kw or 1)
                except ValueError:
                    continue
                d = f2.receive(blk.messages)
                days += 1
                ok = all(d.values.get(i) == vals[i] for i in d.values) and (not blk.coded or len(d.values) == len(vals))
                ok = ok and (not lay or d.witness == lay) and not d.record_rejected and not d.witness_rejected
                ok = ok and d.crc_failed == 0
                bad += (not ok)
    return days, bad


class Agg:
    """Per-site sums and counts, aligned on a common site list, with one set of bootstrap resamples."""

    def __init__(self, g):
        self.sites = sorted(g.site.unique())
        pos = {s: i for i, s in enumerate(self.sites)}
        self.S, self.C = {}, {}
        for (cond, design, metric), z in g.groupby(["cond", "design", "metric"]):
            s = np.zeros(len(self.sites))
            c = np.zeros(len(self.sites))
            for r in z.itertuples():
                s[pos[r.site]] += r.sum
                c[pos[r.site]] += r.count
            self.S[(cond, design, metric)], self.C[(cond, design, metric)] = s, c
        rng = np.random.default_rng(SEED)
        self.idx = rng.integers(0, len(self.sites), (B, len(self.sites)))

    def point(self, cond, design, metric):
        s, c = self.S[(cond, design, metric)], self.C[(cond, design, metric)]
        return s.sum() / max(c.sum(), 1)

    def _boot(self, cond, design, metric):
        s, c = self.S[(cond, design, metric)], self.C[(cond, design, metric)]
        return s[self.idx].sum(1) / np.maximum(c[self.idx].sum(1), 1)

    def diff(self, cond, a, b, metric):
        """(estimate, lower, upper) of pooled(a) - pooled(b), site-clustered bootstrap."""
        est = self.point(cond, a, metric) - self.point(cond, b, metric)
        bs = self._boot(cond, a, metric) - self._boot(cond, b, metric)
        return est, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

    def level(self, cond, design, metric):
        est = self.point(cond, design, metric)
        bs = self._boot(cond, design, metric)
        return est, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def integrity_levels(df):
    """Conditional false-certificate day share per (variant, Q) for the adopted receiver, site-clustered upper bound."""
    out = {}
    rng = np.random.default_rng(SEED + 1)
    z = df[df.receiver == "CRC + sanity + corroboration"]
    for (variant, Q), w in z.groupby(["variant", "Q"]):
        g = w.groupby("site").day_false.agg(["sum", "count"])
        s, c = g["sum"].to_numpy(), g["count"].to_numpy()
        idx = rng.integers(0, len(g), (B, len(g)))
        bs = s[idx].sum(1) / c[idx].sum(1)
        out[(variant, int(Q))] = (s.sum() / c.sum(), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))
    return out


def verdicts(tag, subdir, rt, integ):
    rows = []

    def add(hid, text, value, ok):
        rows.append({"id": hid, "statement": text, "result": value, "supported": bool(ok)})

    f = lambda t: f"{t[0]:+.3f} ({t[1]:+.3f} to {t[2]:+.3f})"
    A = {Q: Agg(pe.load_agg(tag, Q, subdir)) for Q in (6, 12)}
    a6 = A[6]
    wrong = max(float(pe.load_agg(tag, Q, subdir).query("metric == 'wrong' and design != 'flags'")["sum"].max()) for Q in (6, 12))
    add("H1", "no wrong certificate decision in any certificate design (Q 6 and 12, both loss models) and no frame v2 round-trip mismatch",
        f"wrong decisions max {wrong:.3f}; round trip: {rt[1]} mismatches in {rt[0]} blocks", wrong == 0 and rt[1] == 0)
    d = [a6.diff(c, "heur", "rec", "hard_cfg") for c in CONDS]
    add("H2", f"3b rule minus record only, hard-case decisions at the configured thresholds, lower bound >= {T['H2_lower']} (Q = 6, both loss models)",
        " / ".join(f(x) for x in d), all(x[1] >= T["H2_lower"] for x in d))
    d = [a6.diff(c, "heur", "randmix", "hard_cfg") for c in CONDS]
    add("H3", f"3b rule minus the same layering on random days, hard-case decisions, lower bound >= {T['H3_lower']} (Q = 6, both)",
        " / ".join(f(x) for x in d), all(x[1] >= T["H3_lower"] for x in d))
    d = [a6.diff(c, "heur", "rec", "rec") for c in CONDS]
    add("H4", f"record recovered, 3b rule minus record only, lower bound >= {T['H4_lower']} (Q = 6, both)",
        " / ".join(f(x) for x in d), all(x[1] >= T["H4_lower"] for x in d))
    d1 = [a6.diff(c, "heur", "flags", "hard_alt") for c in CONDS]
    d2 = [a6.diff(c, "heur", "rec", "hard_alt") for c in CONDS]
    add("H5", f"unanticipated thresholds: 3b rule minus flags >= {T['H5_flags_lower']} and minus record only >= {T['H5_rec_lower']} (lower bounds, Q = 6, both)",
        "flags: " + " / ".join(f(x) for x in d1) + "; record only: " + " / ".join(f(x) for x in d2),
        all(x[1] >= T["H5_flags_lower"] for x in d1) and all(x[1] >= T["H5_rec_lower"] for x in d2))
    notdom, det = True, []
    for c in CONDS:
        for b in ("sod_mds", "tight50"):
            dom = (a6.point(c, b, "rec") >= a6.point(c, "heur", "rec") - T["H6_margin"]
                   and a6.point(c, b, "hard_cfg") >= a6.point(c, "heur", "hard_cfg") + T["H6_margin"])
            notdom &= not dom
            det.append(f"{b}/{c}: {'dominates' if dom else 'no'}")
    add("H6", "neither coded send-on-delta nor tolerance x 0.5 dominates the 3b rule on (record recovered, hard-case decisions), Q = 6, both",
        "; ".join(det), notdom)
    d = a6.diff("iid_p0.3", "flags", "heur", "hard_cfg")
    add("H7", "known limit: decision flags exceed the 3b rule in hard-case decisions at the configured thresholds (lower bound > 0, Q = 6, independent loss)",
        f(d), d[1] > 0)
    if integ:
        g = lambda v, q: integ.get((v, q))
        parts, ok = [], True
        for v, q, lim in (("record", 6, T["H8_record_q6"]), ("record", 12, T["H8_record_q12"]),
                          ("layered k2", 6, T["H8_layered_q6"]), ("layered k2", 12, T["H8_layered_q12"])):
            x = g(v, q)
            parts.append(f"{v} Q{q}: {x[0]:.4f} (upper {x[2]:.4f}, limit {lim})")
            ok &= x[2] <= lim
        add("H8", "conditional false-certificate day share given one CRC-valid forgery (CRC + sanity + corroboration), upper bound within limits",
            "; ".join(parts), ok)
    if ADOPT_HYBRID:
        da = [a6.diff(c, "hyb1", "flags", "hard_alt") for c in CONDS]
        dc = [a6.diff(c, "hyb1", "flags", "hard_cfg") for c in CONDS]
        dr = [a6.diff(c, "hyb1", "flags", "rec") for c in CONDS]
        add("H9", f"hybrid 1 (flags with all witnesses hosted in spare slots) minus flags, Q = 6, both: unanticipated thresholds lower bound >= {T['H9_alt_lower']}; "
                  f"configured hard-case decisions and record recovered lower bounds >= {T['H9_cfg_lower']}",
            "alt: " + " / ".join(f(x) for x in da) + "; cfg: " + " / ".join(f(x) for x in dc) + "; record: " + " / ".join(f(x) for x in dr),
            all(x[1] >= T["H9_alt_lower"] for x in da) and all(x[1] >= T["H9_cfg_lower"] for x in dc)
            and all(x[1] >= T["H9_rec_lower"] for x in dr))
    v = pd.DataFrame(rows)
    v.to_csv(f"results/{tag}/verdicts3.csv", index=False)
    return v, A


def secondary(tag, subdir, A):
    lines = ["", "## Descriptive secondary results (no verdict)"]
    for Q in (6, 12):
        a = A[Q]
        for c in CONDS:
            lines.append(f"\nQ = {Q}, {c}: pooled level (record recovered / hard configured / hard alternative / all configured)")
            for dn in DESIGNS:
                try:
                    lines.append(f"  {dn:9s} " + " / ".join(f"{a.point(c, dn, m):.3f}" for m in ("rec", "hard_cfg", "hard_alt", "all_cfg")))
                except KeyError:
                    pass
            lines.append("  exact lambda 1 minus 3b rule: " + " / ".join(
                f"{m} {a.diff(c, 'ex1', 'heur', m)[0]:+.3f}" for m in ("rec", "hard_cfg", "hard_alt", "all_cfg")))
    return "\n".join(lines)


FREEZE_TAG = "confirm3-freeze"


def verify_freeze():
    """The code that runs must be the code that was approved: the tag exists, the tracked method files equal the tag, and every
    file hashed in docs/FREEZE3.md still has its recorded MD5."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from data.seal import md5
    if not os.path.exists("docs/FREEZE3.md"):
        sys.exit("refusing to run: docs/FREEZE3.md is missing (run src/data/freeze3.py after the authors tag the repository)")
    tag = subprocess.run(["git", "rev-list", "-n", "1", FREEZE_TAG], capture_output=True, text=True).stdout.strip()
    if not tag:
        sys.exit(f"refusing to run: tag {FREEZE_TAG} does not exist")
    diff = subprocess.run(["git", "diff", "--name-only", FREEZE_TAG, "--", "src", "tests", "tools", "docs/CONFIRM3_PLAN.md"],
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "tests", "tools", "docs/CONFIRM3_PLAN.md"],
                           capture_output=True, text=True).stdout.strip()
    if diff or dirty:
        sys.exit(f"refusing to run: method files differ from {FREEZE_TAG}:\n{diff}\n{dirty}")
    bad = []
    for line in open("docs/FREEZE3.md", encoding="utf-8"):
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(parts) == 2 and parts[0].startswith("`") and len(parts[1]) == 32:
            f = parts[0].strip("`")
            if not os.path.exists(f) or md5(f) != parts[1]:
                bad.append(f)
    if bad:
        sys.exit("refusing to run: files differ from docs/FREEZE3.md: " + ", ".join(bad))
    print(f"freeze verified against tag {FREEZE_TAG}", flush=True)


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    seal = sys.argv[3] if len(sys.argv) > 3 else None
    if not seal and (tag == "confirm3" or "new3" in folder):
        sys.exit("refusing to run: the confirmatory tag or cohort requires the seal file as the third argument")
    if seal:
        verify_freeze()
        run([sys.executable, "-I", "src/data/seal.py", "verify", seal])
    else:
        print("REHEARSAL: no seal given; this run is not confirmatory", flush=True)
    os.makedirs(f"results/{tag}/plans", exist_ok=True)
    for f in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        site_plans(f, f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl")
    files = analysis_sites(folder, tag)
    print(f"{len(files)} sites in the analysis population (at least {MIN_DAYS} four-parameter days)", flush=True)
    names = [os.path.basename(f)[:-4] for f in files]
    run([sys.executable, "-I", "src/p3/proto_base.py", folder, tag, "1"],
        env={"P3_DESIGNS": ",".join(DESIGNS), "P3_SITES": ",".join(names)})
    subdir = "proto_b_" + "_".join(DESIGNS)
    rt = roundtrip(files, tag)
    cache = f"results/{tag}/robust2_stage1.csv"
    if os.path.exists(cache):
        df = pd.read_csv(cache, dtype={"site": str})
    else:
        df = robust2.run(folder, tag, 999, 3, only=set(names))
        df.to_csv(cache, index=False)
    integ = integrity_levels(df)
    v, A = verdicts(tag, subdir, rt, integ)
    text = "# Verdicts of the third confirmation" + ("" if seal else " (REHEARSAL, not confirmatory)") + "\n\n" + v.to_markdown(index=False)
    text += "\n" + secondary(tag, subdir, A)
    open(f"results/{tag}/verdicts3.md", "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
