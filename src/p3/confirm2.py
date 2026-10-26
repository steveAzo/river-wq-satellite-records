"""Second confirmation runner (docs/CONFIRM2_PLAN.md): one pass over a sealed folder, then the C1 to C8 verdicts.

Steps: verify the seal; copy the frozen development parameters (results/dev/robust_choice.json); plans; RQ1
(need2.py); exact full-cohort G_cert (cohort_exact.py); sampled days with fixed-K and reliable designs
(run_robust.py); environmental decisions (run_env.py); corruption and glitches (robustness.py); statistics in
confirmation mode (stats.py confirm); verdicts. Each script is the frozen development script, run unchanged.
Run from Paper3/: python -I src/p3/confirm2.py <folder> <tag> [seal file]
"""
import glob
import os
import shutil
import subprocess
import sys
from multiprocessing import Pool

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import run_multiday as rm  # noqa: E402

PY = [sys.executable, "-I"]


def plan_site(args):
    path, cache = args
    rm.site_plans(path, cache)
    return cache


def run(cmd):
    print(">>", " ".join(cmd), flush=True)
    subprocess.run(PY + cmd, check=True)


def verdicts(tag):
    r1 = pd.read_csv(f"results/{tag}/stats_rq1.csv")
    r3 = pd.read_csv(f"results/{tag}/stats_rq3.csv")
    r4 = pd.read_csv(f"results/{tag}/stats_rq4.csv")
    ev = pd.read_csv(f"results/{tag}/stats_env.csv")
    cor = pd.read_csv(f"results/{tag}/robust9_corrupt.csv", dtype={"site": str})
    gl = pd.read_csv(f"results/{tag}/robust9_glitch.csv", dtype={"site": str})
    ed = pd.read_csv(f"results/{tag}/env_days.csv", dtype={"site": str})
    e7 = pd.read_csv(f"results/{tag}/env_7dadm.csv", dtype={"site": str})

    def row(df, **kw):
        m = df
        for k, v in kw.items():
            m = m[m[k] == v]
        assert len(m) == 1, kw
        return m.iloc[0]
    out = []

    def add(cid, text, est, lo, hi, ok):
        out.append({"id": cid, "hypothesis": text, "estimate": est, "lo": lo, "hi": hi, "pass": bool(ok)})
    x = row(r1, outcome="median bytes per day")
    add("C1", "median record bytes, upper bound <= 30", x.estimate, x.lo, x.hi, x.hi <= 30)
    wrong = (int(cor.false_cert_total.sum()) + int(gl.false_cert.sum()) + int((ed.DO_wrong * ed.draws).sum())
             + int((ed.pH_wrong * ed.draws).sum()) + int(e7.wrong.sum()))
    add("C2", "false certificates and wrong three-valued decisions == 0", wrong, wrong, wrong, wrong == 0)
    x = row(r3, Q=6, channel="iid_p0.3", contrast="rec_code - rec_rep")
    add("C3", "code - repetition, lower bound >= 0.03", x.estimate, x.lo, x.hi, x.lo >= 0.03)
    x = row(r3, Q=6, channel="iid_p0.3", contrast="rec_code - fixed_K")
    add("C4", "code - channel-blind fixed K, lower bound >= 0.05", x.estimate, x.lo, x.hi, x.lo >= 0.05)
    a = row(r3, Q=6, channel="iid_p0.3", contrast="rec_code - tag")
    b = row(r3, Q=6, channel="iid_p0.3", contrast="rec_code - every_k")
    add("C5", "code - tag and code - every k-th, lower bounds >= 0.5", f"{a.estimate:.3f} / {b.estimate:.3f}",
        f"{a.lo:.3f} / {b.lo:.3f}", f"{a.hi:.3f} / {b.hi:.3f}", a.lo >= 0.5 and b.lo >= 0.5)
    a = row(r3, Q=12, channel="iid_p0.3", contrast="rec_code")
    b = row(r3, Q=12, channel="gilbert_p0.3_b3", contrast="rec_code")
    add("C6", "Q = 12 G_cert >= 0.95 (iid / bursty), lower bounds", f"{a.estimate:.3f} / {b.estimate:.3f}",
        f"{a.lo:.3f} / {b.lo:.3f}", f"{a.hi:.3f} / {b.hi:.3f}", a.lo >= 0.95 and b.lo >= 0.95)
    a = row(ev, cond="perfect", outcome="EC miss rate, code - every_k")
    b = row(ev, cond="perfect", outcome="DO decided share, code - every_k")
    add("C7", "EC pulses missed (upper <= -0.3) and DO days decided (lower >= 0.3), code - every k-th",
        f"{a.estimate:.3f} / {b.estimate:.3f}", f"{a.lo:.3f} / {b.lo:.3f}", f"{a.hi:.3f} / {b.hi:.3f}",
        a.hi <= -0.3 and b.lo >= 0.3)
    x = row(r4, planning_channel="iid_p0.3")
    add("C8", "28-day pilot sufficient >= 0.75 (point estimate)", x.sufficient, x.suff_lo, x.suff_hi,
        x.sufficient >= 0.75)
    v = pd.DataFrame(out)
    v.to_csv(f"results/{tag}/verdicts.csv", index=False)
    print(v.to_string(index=False))
    return v


def main():
    folder, tag = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        run(["src/data/seal.py", "verify", sys.argv[3]])
    os.makedirs(f"results/{tag}/plans", exist_ok=True)
    shutil.copy("results/dev/robust_choice.json", f"results/{tag}/robust_choice.json")
    jobs = [(f, f"results/{tag}/plans/{os.path.basename(f)[:-4]}.pkl") for f in sorted(glob.glob(os.path.join(folder, "*.csv")))]
    with Pool(3) as pool:
        for o in pool.imap_unordered(plan_site, jobs):
            print("plans", o, flush=True)
    run(["src/p3/need2.py", folder, tag, "3"])
    run(["src/p3/cohort_exact.py", folder, tag, "3"])
    run(["src/p3/run_robust.py", folder, tag, "20", "3"])
    run(["src/p3/run_env.py", folder, tag, "3"])
    run(["src/p3/robustness.py", folder, tag, "3"])
    run(["src/p3/stats.py", tag, "confirm"])
    verdicts(tag)


if __name__ == "__main__":
    main()
