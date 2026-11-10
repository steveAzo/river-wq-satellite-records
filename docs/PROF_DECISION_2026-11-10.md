# Paper 3: where it stands and the decision needed

Date: 2026-11-10. Source of every number: docs/CONFIRM3_RESULTS.md, results/confirm3/verdicts3.md, and the in-project review (docs/REVIEW_FINDINGS_2026-11-09.md). The review was done by a separate AI session and is not an outside review.

## What was done

- The method was changed to certified threshold decisions: the server answers exceeded, not exceeded, or undetermined from the bytes that arrive, using an error-bounded record plus extremum witnesses.
- Nine hypotheses were frozen and run once on 31 sealed US rivers (2024). The run was clean, with no restart.
- Result: eight supported, one failed (H8, integrity under a forged message that passes the CRC-16, at twelve messages per day).
- The manuscript (v0.5, 33 pages) is written and reports the failure.

## What the review changed about how strong this is

- Most of the "eight of nine" is weaker than it sounds. H7 and most of H9 hold by construction, H1 cannot fail through assumption R, and H6 passed with large margins. The informative hypotheses are H2 to H5, the unanticipated-threshold part of H9, and H8.
- The decision-flags comparator ignores the recovered record. The fair benefit of witnesses is the contrast with the record alone: +0.26 (H5, second part), and for the adopted hybrid only +0.08 to +0.10 on unanticipated thresholds. The larger +0.29 to +0.36 is against flags that discard their record.
- Hybrid 1's gain is almost nil for conductance (+0.02 to +0.03) and +0.09 to +0.14 for the other kinds.
- H8 failed for a structural reason: false certificates concentrate on days where nothing can be compared (exactly or fewer than the needed messages, and oversize days with no parity). A longer CRC does not change that conditional share, so CRC-24 is not the remedy.
- All design comparisons come from a slot model, not frame bytes. Hosted witnesses, conductance pair codes, and flags had no byte-level test.

## Options

- Option A, submit v0.5 as an evidence paper. Keep the claim at generality and soundness, with the limits above stated. Risk: reviewers see a modest benefit and a failed integrity hypothesis; novelty is already thin against PET, Plato, and TREAT.
- Option B, build a version that fixes the cause. Add corroboration across a day's units (covering days with no spare messages and oversize days), test hosted witnesses and flags at byte level, and confirm on a new sealed cohort with a new freeze. Cost: new code, a new pre-registration, about a day to a week of work plus a multi-hour run. It would turn the failed hypothesis into a tested remedy.
- Option C, narrow the paper to the integrity finding and the certificate language only, as a shorter methods paper, and drop the design comparison. Lower cost; weaker contribution.

## Recommendation

Option B if the aim is a strong Q1 paper, since the current evidence does not carry a Q1 claim on benefit and the failure has an identified cause that can be repaired. Option A only if time matters more than strength. Before any submission, an outside review is required.

## Needed from the Prof

- Which option.
- If B: approval of a new third-cohort-style sealed cohort (a fourth), and of the new freeze.
