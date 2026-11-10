"""One-off patch script that derives src/p3v3/proto_base3.py (version 3, Phase 1a) from the frozen src/p3/proto_base.py.
Kept so that the difference between the two files is auditable. Run from Paper3/: python -I src/p3v3/patch_base3.py"""
s = open("src/p3/proto_base.py", encoding="utf-8").read()


def rep(a, b, count=1):
    global s
    assert s.count(a) >= 1, a[:70]
    s = s.replace(a, b, count)


rep('"""Revision 2, Step 4: baselines against the witness designs. Pre-registration: docs/REVISION2_PLAN.md ("Step 4").',
    '"""Version 3, Phase 1a (docs/METHOD_V3_PLAN.md): derived from src/p3/proto_base.py by src/p3v3/patch_base3.py. DEVELOPMENT DATA ONLY.\n'
    'Changes: designs and flag capacity are command-line arguments (no environment switches); new design flagsrec (decision flags that\n'
    'also use the recovered record: the certificate decides when certain, otherwise the flag, no witnesses); hybrid 1 hosts its witnesses in\n'
    'the spare room of the flag capacity given; seeds use the full site number; environment variables are not read.\n'
    'Original header: Revision 2, Step 4: baselines against the witness designs.')
rep('SEED = 20261106', 'SEED = 20261110')
rep('ONLY = os.environ.get("P3_DESIGNS")                 # e.g. "hyb1,hyb2": run only these designs (exploratory hybrids)\n'
    'if ONLY:\n'
    '    DESIGNS = tuple(ONLY.split(","))\n', '')
rep('FLAG_CAP = 4.75', 'FLAG_CAP = 4.0                                      # set from the command line (frame version 2 allows 4)')
# seeds: full site number
rep('rng = np.random.default_rng([SEED, Q, re2.site_number(site) % 100000])', 'rng = np.random.default_rng([SEED, Q, re2.site_number(site)])')
rep('perm = np.random.default_rng([SEED, 77, re2.site_number(site) % 100000]).permutation(len(items)) if items else []',
    'perm = np.random.default_rng([SEED, 77, re2.site_number(site)]).permutation(len(items)) if items else []')
# no debugging env switch
rep('    if os.environ.get("P3_MAXDAYS"):\n        items = items[:int(os.environ["P3_MAXDAYS"])]       # debugging only\n', '')
# hybrid branch: flagsrec and capacity-aware spare room
rep('                    elif dn in ("hyb1", "hyb2"):                            # exploratory hybrids (flags + witnesses)',
    '                    elif dn in ("hyb1", "hyb2", "flagsrec"):                # hybrids and the fair flags comparator')
rep('''                        def spare_f(cR, V=V):
                            cc = cR - 0.25
                            return int(-(-V // cc) * cc - V + 1e-9)
                        if dn == "hyb1":
                            host = []
                            for o in ORDER:
                                if o in present and len(obj_values(o)) <= spare_f(5) - len(host):
                                    host += obj_values(o)
                            g = [(Rl + host, FLAG_CAP)]
                        else:
                            g = heur_groups(Rl, it["hard"], present, spare_f)
                            g = g[:-1] + [(g[-1][0], g[-1][1] - 0.25)]''',
    '''                        def spare_f(cR, V=V):
                            cc = cR - (5 - FLAG_CAP)
                            return int(-(-V // cc) * cc - V + 1e-9)
                        if dn == "flagsrec":
                            g = [(Rl, FLAG_CAP)]
                        elif dn == "hyb1":
                            host = []
                            for o in ORDER:
                                if o in present and len(obj_values(o)) <= spare_f(5) - len(host):
                                    host += obj_values(o)
                            g = [(Rl + host, FLAG_CAP)]
                        else:
                            g = heur_groups(Rl, it["hard"], present, spare_f)
                            g = g[:-1] + [(g[-1][0], g[-1][1] - (5 - FLAG_CAP))]''')
rep('fd = flag_decisions(it["meta"]) if dn in ("flags", "hyb1", "hyb2") else None', 'fd = flag_decisions(it["meta"]) if dn in ("flags", "hyb1", "hyb2", "flagsrec") else None')
rep('else (recover_coded(items_, cc, mask) if dn in ("flags", "hyb1", "hyb2")', 'else (recover_coded(items_, cc, mask) if dn in ("flags", "hyb1", "hyb2", "flagsrec")')
rep('                        if dn in ("hyb1", "hyb2"):                           # certificate when certain, else the flag',
    '                        if dn in ("hyb1", "hyb2", "flagsrec"):               # certificate when certain, else the flag')
rep('                        elif dn in ("hyb1", "hyb2"):\n                            parts =', '                        elif dn in ("hyb1", "hyb2", "flagsrec"):\n                            parts =')
# command line
rep('''def main():
    folder, tag = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
    outdir = f"results/{tag}/proto_b" + (("_" + "_".join(DESIGNS)) if ONLY else "")
    os.makedirs(outdir, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    if os.environ.get("P3_SITES"):                       # restrict to the analysis population (confirm3.py)
        keep = set(os.environ["P3_SITES"].split(","))
        paths = [x for x in paths if os.path.basename(x)[:-4] in keep]
    with Pool(workers) as pool:''',
    '''def main():
    """Usage: python -I src/p3v3/proto_base3.py <folder> <tag> <designs comma list> <flag capacity> <outname> [sites]"""
    global DESIGNS, FLAG_CAP, HEAVY
    folder, tag = sys.argv[1], sys.argv[2]
    DESIGNS = tuple(sys.argv[3].split(","))
    FLAG_CAP = float(sys.argv[4])
    outname = sys.argv[5]
    limit = int(sys.argv[6]) if len(sys.argv) > 6 else None
    HEAVY = any(d in DESIGNS for d in ("tight50", "tight25", "sod_once", "sod_mds"))
    workers = 1
    outdir = f"results/v3dev/{tag}_{outname}"
    os.makedirs(outdir, exist_ok=True)
    open(f"{outdir}/RUN.txt", "w").write(f"designs={DESIGNS} flag_cap={FLAG_CAP} seed={SEED} folder={folder}\\n")
    paths = sorted(glob.glob(os.path.join(folder, "*.csv")))[:limit]
    with Pool(workers) as pool:''')
rep('[(p, tag, outdir) for p in paths]', '[(p, tag, outdir, DESIGNS, FLAG_CAP) for p in paths]')
rep('def run_site(args):' + chr(10) + '    path, tag, outdir = args' + chr(10),
    'def run_site(args):' + chr(10) + '    global DESIGNS, FLAG_CAP, HEAVY' + chr(10) + '    path, tag, outdir, DESIGNS, FLAG_CAP = args  # a spawned worker re-imports the module, so the settings travel in the job' + chr(10) + '    HEAVY = any(d in DESIGNS for d in ("tight50", "tight25", "sod_once", "sod_mds"))' + chr(10))
open("src/p3v3/proto_base3.py", "w", encoding="utf-8").write(s)
print("written")
