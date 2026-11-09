"""Write docs/INTEGRITY_RESULTS.md and results/dev/robust2_summary.csv from results/dev/robust2_stage1.csv (src/p3/robust2.py).
Every number in the document is generated from the results file (the superseded run is read from
results/dev/robust2_summary_forge_noop_bug.csv for the correction paragraph). Run from Paper3/: python -I src/p3/integrity_report.py
"""
import os
import sys

import numpy as np
import pandas as pd

ORDER = ["CRC only", "CRC + sanity", "CRC + corroboration", "CRC + sanity + corroboration",
         "CRC + sanity + corroboration + cross-check"]
B = 500


def summarise(d, rng):
    rows = []
    for (v, Q, r), z in d.groupby(["variant", "Q", "receiver"]):
        g = z.groupby(["site", "day"]).day_false.agg(["sum", "count"])
        s, c = g["sum"].to_numpy(), g["count"].to_numpy()
        idx = rng.integers(0, len(g), (B, len(g)))
        bs = s[idx].sum(1) / c[idx].sum(1)
        rows.append((v, int(Q), r, s.sum() / c.sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5),
                     int(z.false_witnesses.sum()), int(z.false_readings.sum()), len(z)))
    return pd.DataFrame(rows, columns=["variant", "Q", "receiver", "false_day", "lo", "hi", "false_wit", "false_readings", "draws"])


def main():
    d = pd.read_csv("results/dev/robust2_stage1.csv", dtype={"site": str})
    old = pd.read_csv("results/dev/robust2_summary_forge_noop_bug.csv") if os.path.exists("results/dev/robust2_summary_forge_noop_bug.csv") else None
    t = summarise(d, np.random.default_rng(1))
    t.to_csv("results/dev/robust2_summary.csv", index=False)
    cell = lambda v, Q, r: t[(t.variant == v) & (t.Q == Q) & (t.receiver == r)].iloc[0]
    n_sites, n_days, min_draws = d.site.nunique(), d[["site", "day"]].drop_duplicates().shape[0], int(t.draws.min())

    s1 = ["| Block | Q | " + " | ".join(ORDER) + " |", "|---|---|" + "---|" * len(ORDER)]
    for (v, Q), z in t.groupby(["variant", "Q"]):
        z = z.set_index("receiver")
        s1.append(f"| {v} | {Q} | " + " | ".join(f"{z.loc[o, 'false_day']:.4f} ({z.loc[o, 'lo']:.4f} to {z.loc[o, 'hi']:.4f})" for o in ORDER) + " |")
    s2 = ["| Corruption | Block | Q | CRC-16, CRC only | CRC-16, sanity + corroboration | CRC-24, sanity + corroboration |", "|---|---|---|---|---|---|"]
    for name, pc in (("bit errors 1e-4", 1 - (1 - 1e-4) ** 184), ("bit errors 1e-3", 1 - (1 - 1e-3) ** 184),
                     ("bit errors 1e-2", 1 - (1 - 1e-2) ** 184), ("10% of messages hit", 0.10)):
        for (v, Q), _ in t.groupby(["variant", "Q"]):
            lam = Q * 0.7 * pc * 2.0 ** -16
            a = 1e6 * lam * cell(v, Q, "CRC only").false_day
            b = 1e6 * lam * cell(v, Q, "CRC + sanity + corroboration").false_day
            s2.append(f"| {name} | {v} | {Q} | {a:.3g} | {b:.3g} | {b / 256:.2g} |")
    best = "CRC + sanity + corroboration"
    r6, r12 = cell("record", 6, best), cell("record", 12, best)
    k16, k112 = cell("layered k1", 6, best), cell("layered k1", 12, best)
    k26, k212 = cell("layered k2", 6, best), cell("layered k2", 12, best)
    c6, c12 = cell("record", 6, "CRC only"), cell("record", 12, "CRC only")
    san6 = cell("record", 6, "CRC + sanity")
    lam3 = 6 * 0.7 * (1 - (1 - 1e-3) ** 184) * 2.0 ** -16
    corr = ""
    if old is not None:
        m = old.merge(t, on=["variant", "Q", "receiver"], suffixes=("_old", "_new"))
        m["ratio"] = m.false_day_new / m.false_day_old
        rng_ = lambda r: m[m.receiver == r].ratio
        fmt = lambda r: f"{rng_(r).min():.2f} to {rng_(r).max():.2f}"
        corr = f"""
## Correction (2026-11-09): the first version of this study had a defective forgery function

The in-project review of 2026-11-09 found that the forgery function of the first run could choose the two CRC bytes (positions 3 and 4) among the bytes to change; the CRC is then recomputed, so some "forgeries" changed nothing and could never produce a false certificate. The review also tightened the receiver for the corroborating variants (a witness descriptor that differs between messages, or two CRC-valid copies of one message that disagree, now reject the block). This document replaces the earlier numbers; the superseded run is kept (results/dev/robust2_stage1_forge_noop_bug.csv, results/dev/robust2_summary_forge_noop_bug.csv, results/INTEGRITY_RESULTS_before_review_fix.md).
The two changes act in opposite directions, and the effect of the forgery fix alone can be read from the receivers that the new receiver rules do not touch. Ratio of the corrected to the superseded conditional share, over the six blocks (variant and Q): CRC only {fmt("CRC only")}; CRC + sanity {fmt("CRC + sanity")} (the superseded shares were therefore mostly understated by the defective forgery; part of the difference is sampling noise because the random draws changed). For the corroborating receivers the stricter rules lower the shares: CRC + corroboration {fmt("CRC + corroboration")}; CRC + sanity + corroboration (the adopted receiver) {fmt("CRC + sanity + corroboration")}. Any figure quoted from the earlier version (the claims register, the pre-registration, the review brief) was updated in the same change.
"""
    doc = f"""# Integrity study for frame v2 (revision 2, Step 6b), development data only

Date: 2026-11-09 (rerun after the in-project review; first version 2026-11-06). Code: `src/p3/frame2.py` (codec), `src/p3/robust2.py` (experiment), `src/p3/integrity_report.py` (this document), `src/p3/certlang.py` (`witness_consistent`), `src/p3/capacity.py`. Specification and threat model: docs/FRAME_SPEC_V2.md. Results: `results/dev/robust2_stage1.csv`, `results/dev/robust2_summary.csv`, printout `results/robust2_stage12.txt`.
Command (from Paper3/): `python -I src/p3/robust2.py data/clean/usgs dev 6 10`, then `python -I src/p3/integrity_report.py`.
Status of every number: numerical (conditional on forced forgeries, random content, six development sites) or model-based (Stage 2). An AI assistant wrote and ran the code; a separate in-project AI reading found the forgery defect; no outside reviewer has read it.

## Method

- A corrupted message passes the per-message CRC-16 with probability about 2^-16 (an upper bound for random errors; every single-bit error and every burst of up to 16 bits is detected). A direct simulation would need millions of days, so the study has two stages.
- Stage 1 (measured): {n_sites} development sites, {n_days:,} days, byte-level blocks (record only; record with a layered witness group of k_w = 1 or 2 carrying DO minimum, pH minimum and maximum, T maximum), Q = 6 and 12, independent loss 0.3. In each draw one arrived message is replaced by a CRC-valid forgery (1 to 3 distinct body bytes after the CRC changed by a nonzero XOR, CRC recomputed, so the message always differs from the original). At least {min_draws:,} draws per cell. A day is false if any reading is certified outside tolerance, any witness code differs from the truth, or a value outside the site profile is accepted.
- Stage 2 (model): expected CRC-passing corruptions per day = Q x 0.7 x P(message corrupted) x 2^-16, times the Stage 1 conditional probability.
- Receivers: CRC only; plus the sanity rule (values inside the site profile and in planned order; censored witness codes rejected); plus corroboration (re-encode and compare when more messages arrive than needed; a mismatch rejects the block; a descriptor that differs between messages, or two CRC-valid copies of one message that disagree, also reject the block); both; both plus the witness-versus-record cross-check.

## Stage 1: share of days with a false certificate, given one CRC-valid forgery (day-clustered 95% bootstrap interval)

{chr(10).join(s1)}

## Stage 2: expected days with a false certificate per million days (independent loss 0.3)

{chr(10).join(s2)}

The CRC-24 column divides by 256 (2^-8 more bits) and ignores the change in the Stage 1 conditional; its cost is in the findings.

## Findings

1. A per-message CRC with sanity rules and corroboration lowers the conditional false-certificate probability for record-only days from {c6.false_day:.1%} (CRC only) to {r6.false_day:.1%} at Q = 6, and from {c12.false_day:.1%} to {r12.false_day:.2%} at Q = 12.
2. The sanity rule alone (no extra bits) brings the Q = 6 record-only share to {san6.false_day:.1%}; corroboration (free when extra messages arrive) removes most of the rest. Neither helps when exactly the needed number of messages arrives, which is the structural residual.
3. Layered witness groups raise the conditional risk (Q = 6: {k16.false_day:.1%} for k_w = 1 and {k26.false_day:.1%} for k_w = 2, against {r6.false_day:.1%} record only; Q = 12: {k112.false_day:.2%} and {k212.false_day:.2%}), because a smaller record unit needs more messages and leaves fewer for corroboration, and a forged witness is a global claim. k_w = 2 is safer than k_w = 1 in this respect.
4. The witness-versus-record cross-check is sound (honest witnesses are never contradicted; tested over every subset) but changes little (false witnesses {int(cell('layered k1', 6, best).false_wit)} against {int(cell('layered k1', 6, ORDER[-1]).false_wit)} for k_w = 1 at Q = 6); in most residual cases no record arrived to check against. It is not part of the receiver in the pre-registration.
5. At a bit-error rate of 1e-3 the expected rate with CRC-16, sanity and corroboration is {1e6 * lam3 * r6.false_day:.2g} false-certificate days per million for record-only blocks at Q = 6 and {1e6 * 12 * 0.7 * (1 - (1 - 1e-3) ** 184) * 2.0 ** -16 * r12.false_day:.2g} at Q = 12; with CRC only it is {1e6 * lam3 * c6.false_day:.2g} at Q = 6 (tables above). These are model estimates built on an upper bound for the CRC pass rate and on random-content forgeries.
6. The alternative is a longer check. CRC-24 cuts the forgery rate 256-fold and leaves 4 values per message instead of 5 (src/p3/capacity.py); fully recovered records fall from 0.915 to 0.862 at Q = 6 and from 0.992 to 0.982 at Q = 12 under independent loss (0.850 to 0.800 and 0.972 to 0.957 under bursts; computed by the capacity argument on the development plans, 2026-11-06). Which point is right depends on the real channel error rate, which is not known here.

## Limits

- Forgeries change body bytes only; a header forgery changes the block identity and is rejected when accepted messages disagree on it (unit-tested for single cases, not sampled at scale).
- Random-content forgeries are not adversarial; an adversary (tampering) needs authentication, which is out of scope.
- The conditional probabilities come from {n_sites} development sites; the arrival model is independent loss 0.3 (Gilbert loss changes how often corroboration is possible).
- This is development data. The confirmation run repeats the study on new data with the receiver rules frozen as above.
- The frozen C2 failure (96 readings, frame v1) and the post-confirmation rule B stay reported as they are; frame v2 is a new design, not a re-evaluation of the confirmed one.
{corr}"""
    open("docs/INTEGRITY_RESULTS.md", "w", encoding="utf-8").write(doc)
    print(f"docs/INTEGRITY_RESULTS.md written; record Q6 {r6.false_day:.4f}, Q12 {r12.false_day:.4f}, k2 Q6 {k26.false_day:.4f}, k2 Q12 {k212.false_day:.4f}")


if __name__ == "__main__":
    main()
