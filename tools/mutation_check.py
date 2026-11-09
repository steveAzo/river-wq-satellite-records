"""Mutation check of the revision-2 tests (research-integrity rule 4: a check must be able to fail).

Copies src/ and tests/ to a scratch directory, plants one fault at a time (at every occurrence of its anchor), runs the named test files, and records whether the
tests catch it. A mutation that no test catches means that part of the code has no test power for that fault.
Run from Paper3/: python tools/mutation_check.py [scratch_dir] [M04,M12,...]    (full run about 40 minutes on the project PC;
writes results/mutation_check.md; with a list of ids it re-runs only those and writes results/mutation_check_rerun.md)
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "mutation_scratch")
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None

CL = ["tests/test_certlang.py"]
# (id, file, old, new, test files, why the tests must fail)
MUTATIONS = [
    ("M01", "src/p3/certlang.py", "    a, r = a * scale, r * scale", "    a, r = a * scale * 0.5, r * scale", CL,
     "tolerance interval half as wide: unsound"),
    ("M02", "src/p3/certlang.py", "    if (hi[m] < theta).any() or (K.wmin", "    if (hi[m] < theta + 0.5).any() or (K.wmin", CL,
     "'yes' below threshold made too eager"),
    ("M03", "src/p3/certlang.py", "    return 0 if (lo[m] >= theta).all() else -1", "    return 0 if (lo[m] >= theta - 0.5).all() else -1", CL,
     "'no' below threshold made too eager"),
    ("M04", "src/p3/certlang.py", "if hi[t] > (1 + frac) * lo[prev] or", "if hi[t] > (1 + 2 * frac) * lo[prev] or", ["tests/test_mutation_gaps.py"] + CL,
     "conductance 'no' rule too lax"),
    ("M05", "src/p3/certlang.py", "    lo = sum(b[0] for b in bounds) / len(bounds)", "    lo = sum(b[1] for b in bounds) / len(bounds)", CL,
     "rolling mean lower bound uses the upper ends"),
    ("M06", "src/p3/certlang.py", "            lo = np.round(np.ceil(lo / rho - 1e-6) * rho, 12)", "            lo = np.round(np.floor(lo / rho - 1e-6) * rho, 12)", CL,
     "grid snapping moves the lower end outward instead of inward"),
    ("M07", "src/p3/certlang.py", "        return not ((hi[m] < a).any() or lo[m].min() > b)", "        return not ((hi[m] < a).any() or lo[m].min() > b + 5)", CL,
     "witness cross-check no longer rejects a minimum above the record"),
    ("M08", "src/p3/certlang.py", "        self.wmin = (a, b) if self.wmin is None else (max(a, self.wmin[0]), min(b, self.wmin[1]))\n        self.g_lo = max(self.g_lo, a)",
     "        self.wmin = (a, b) if self.wmin is None else (max(a, self.wmin[0]), min(b, self.wmin[1]))\n        self.g_lo = max(self.g_lo, b)", CL,
     "slotless minimum witness raises the global lower bound to the cell top"),
    ("M09", "src/p3/certlang.py", "            hi = max(Ub / La - 1.0, 1.0 - Lb / Ua)", "            hi = max(Ub / La - 1.0, 0.0)", CL,
     "rate witness ignores downward changes"),
    ("M10", "src/p3/frame2.py", "    if crc16(bytes(head) + bytes(rest)) != crc:", "    if crc16(bytes(head) + bytes(rest)) == crc:", ["tests/test_frame2.py"],
     "CRC test inverted"),
    ("M11", "src/p3/frame2.py", "                if any(full[i] != recs[i] for i in recs):", "                if False:", ["tests/test_frame2.py"],
     "record corroboration disabled"),
    ("M12", "src/p3/frame2.py", "            if p not in n_of or s >= n_of[p]:", "            if p not in n_of:", ["tests/test_mutation_gaps.py", "tests/test_frame2.py"],
     "sanity rule no longer checks the slot against the profile"),
    ("M13", "src/p3/frame2.py", "    if any(c in (0, 8191) for c in out.witness.values()):", "    if any(c in (-1,) for c in out.witness.values()):", ["tests/test_mutation_gaps.py", "tests/test_frame2.py"],
     "censored witness codes accepted"),
    ("M14", "src/p3/allocate.py", "J += o.u * (Pg + o.d * max(0.0, PhiR - Pg))", "J += o.u * (Pg + o.d * (PhiR - Pg))", ["tests/test_mutation_gaps.py", "tests/test_allocate.py"],
     "layered term allowed to go negative"),
    ("M15", "src/p3/allocate.py", "        tail = np.cumsum(pmf[::-1])[::-1]", "        tail = np.cumsum(pmf)", ["tests/test_allocate.py"],
     "recovery probability uses the lower tail"),
    ("M16", "src/p3/sod.py", "        elif held is None or abs(ch.x[t] - held) > scale * ch.tol[t] * SLACK:", "        elif held is None or abs(ch.x[t] - held) > 2 * scale * ch.tol[t] * SLACK:", ["tests/test_sod.py"],
     "send-on-delta deadband twice the tolerance"),
    ("M17", "src/p3/sod.py", "            c[s:nxt[1]] = True", "            c[s:nxt[1] + 1] = True", ["tests/test_mutation_gaps.py", "tests/test_sod.py"],
     "hold certified one reading too far"),
    ("M18", "src/p3/capacity.py", "SEG_OVERHEAD = 2 + 21 + 1 ", "SEG_OVERHEAD = 2 + 21 ", ["tests/test_mutation_gaps.py", "tests/test_capacity.py", "tests/test_frame2.py"],
     "bit budget forgets the hosted flag"),
    ("M19", "src/p3/frame2.py", '(m["rest"][0] >> 5, m["rest"][0] & 31) != (kw, mask) and corroborate:', '(m["rest"][0] >> 5, m["rest"][0] & 31) != (kw, mask) and False:', ["tests/test_review_fixes.py"],
     "a witness descriptor that differs between messages no longer rejects the block"),
    ("M20", "src/p3/frame2.py", 'if corroborate and first_seen["rest"] != m["rest"]:', 'if False and first_seen["rest"] != m["rest"]:', ["tests/test_review_fixes.py"],
     "conflicting CRC-valid copies of one message no longer reject the block"),
    ("M21", "src/p3/robust2.py", "np.arange(5, len(b))", "np.arange(3, len(b))", ["tests/test_review_fixes.py"],
     "the forgery may change only the CRC bytes (a no-op forgery)"),
]


def run_tests(files):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    t = time.time()
    r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"] + files, cwd=SCRATCH,
                       capture_output=True, text=True, env=env, timeout=1500)
    return r.returncode, time.time() - t, r.stdout[-300:]


def main():
    if os.path.exists(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    for d in ("src", "tests"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(SCRATCH, d), ignore=shutil.ignore_patterns("__pycache__"))
    chosen = [m for m in MUTATIONS if ONLY is None or m[0] in ONLY]
    base_files = sorted({f for m in chosen for f in m[4]})
    rc, sec, out = run_tests(base_files)
    print(f"clean tree: rc={rc} ({sec:.0f} s)", flush=True)
    if rc != 0:
        print("the unmutated tests fail; stop:\n" + out)
        sys.exit(1)
    lines = ["| id | file | planted fault | tests | caught | seconds |", "|---|---|---|---|---|---|"]
    caught = 0
    for mid, f, old, new, files, why in chosen:
        path = os.path.join(SCRATCH, f)
        src = open(path, encoding="utf-8").read()
        if src.count(old) < 1:
            lines.append(f"| {mid} | {f} | {why} | - | NOT APPLIED (anchor not found) | - |")
            print(mid, "anchor problem", flush=True)
            continue
        open(path, "w", encoding="utf-8").write(src.replace(old, new))
        rc, sec, out = run_tests(files)
        open(path, "w", encoding="utf-8").write(src)
        hit = rc != 0
        caught += hit
        lines.append(f"| {mid} | {f} | {why} | {', '.join(os.path.basename(x) for x in files)} | {'yes' if hit else 'NO'} | {sec:.0f} |")
        print(mid, "caught" if hit else "NOT CAUGHT", f"{sec:.0f}s", flush=True)
    applied = sum(1 for l in lines[2:] if "NOT APPLIED" not in l)
    body = ("# Mutation check of the revision-2 tests\n\nFaults planted one at a time in a scratch copy; a test run that fails is a catch. "
            f"Caught {caught} of {applied} applied mutations ({len(chosen)} run, {len(MUTATIONS)} defined).\n\n" + "\n".join(lines) + "\n")
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    out_name = "mutation_check.md" if ONLY is None else "mutation_check_rerun.md"
    open(os.path.join(ROOT, "results", out_name), "w", encoding="utf-8").write(body)
    print(body)


if __name__ == "__main__":
    main()
