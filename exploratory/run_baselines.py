"""Point 5 of the outside review (POST HOC): the final frame (4 value slots per message) in the slot model, with the record only, the 3b
rule, tolerance x 0.5 (tight50), and coded send-on-delta (sod_mds), identical loss draws (independent and Gilbert loss 0.3), Q = 6 and 12.
The slot model is pessimistic for the 3b rule (whole slots for the witness group); the byte-level 3b numbers are in the confirmation.
Run from Paper3/: python -I -W ignore exploratory/run_baselines.py <folder> <tag>"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "src", "p3v3"))
import base_slots as bs  # noqa: E402
import confirm4 as c4  # noqa: E402

folder, tag = sys.argv[1], sys.argv[2]
c4.check_environment()
outdir = os.path.join(HERE, "out", f"{tag}_baselines")
os.makedirs(outdir, exist_ok=True)
paths = [p for p in sorted(glob.glob(os.path.join(folder, "*.csv")))
         if os.path.exists(f"results/{tag}/plans/{os.path.basename(p)[:-4]}.pkl")]
paths = c4.analysis_sites(paths, tag)
for i, p in enumerate(paths, 1):
    bs.run_site((p, tag, outdir, ("rec", "heur", "tight50", "sod_mds"), 4.0, 4))
    print(f"{i}/{len(paths)} {os.path.basename(p)[:-4]}", flush=True)
