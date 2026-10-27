"""Post-confirmation diagnosis of the C2 failure (exploratory; does not change any confirmatory result).

Replays robustness.run_site for one site with the same seed and loop order, and reports every draw in which a
reading was certified outside its tolerance: the day, tier, corruption level, the receiver statistics, and whether
the accepted units came straight from CRC-checked data messages or from an erasure decoding that was retried.
Run from Paper3/: python -I src/p3/diagnose_c2.py <folder> <tag> <site>
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from p3 import delivery, frame, record  # noqa: E402
from p3 import robustness as rb  # noqa: E402
from p3 import run_e2e as re2  # noqa: E402
from p3 import run_robust as rr  # noqa: E402


def main():
    folder, tag, site = sys.argv[1], sys.argv[2], sys.argv[3]
    path = os.path.join(folder, f"{site}.csv")
    P = pickle.load(open(f"results/{tag}/plans/{site}.pkl", "rb"))
    rng = np.random.default_rng([rb.SEED, 9, int(site[:15]) % 100000])
    events = 0
    for rd in re2.sample_site(path, 20)[1::2]:
        day = delivery.day_number(rd.day)
        plan = P[day]["plan"][0]
        for Q in rb.QS:
            ds = rb.designs(rd, plan, Q)
            masks = rr.sim_masks(("iid", 0.3, 0), Q, rng, draws=rb.DRAWS)
            for cname, ber, pm in rb.CORRUPTION:
                for name, s in ds.items():
                    for r, mask in enumerate(masks):
                        arrived = [rb.corrupt(m, ber, pm, rng) for m, ok in zip(s.msgs, mask[:len(s.msgs)]) if ok]
                        rx, last, bound, fails, st = delivery.receive(arrived, day, with_stats=True)
                        cert, _ = record.certify(rx, rd.n_of, bound, last)
                        err = record.errors(rd.channels, rx)
                        bad = sum(int((err[p][cert[p]] > rb.SLACK).sum()) for p in cert)
                        if bad:
                            events += 1
                            intact = sum(m == o for m, o in zip(arrived, [x for x, ok in zip(s.msgs, mask[:len(s.msgs)]) if ok]))
                            wrong_pos = [i for i, v in rx.items() if i >= len(plan) or v != plan[i]]
                            print(f"day {rd.day.date()} Q {Q} {cname} {name} draw {r}: {bad} readings falsely certified; "
                                  f"arrived {len(arrived)} (intact {intact}), K {s.meta.get('K')}, stats {st}; "
                                  f"positions received {len(rx)}, of which wrong or invented {len(wrong_pos)}")
        for kind in ("out", "in"):          # the glitch part of run_site draws from the same generator
            for k in (1, 3):
                rb.glitched(rd, rng, k, kind)
    print("events:", events)


if __name__ == "__main__":
    main()
