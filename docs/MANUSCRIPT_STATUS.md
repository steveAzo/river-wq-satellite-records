# Manuscript status (Step 8 of docs/REVISION2_PLAN.md; kept here because that plan is frozen)

Last updated: 2026-11-09. This file is not in the freeze (docs/FREEZE3.md).

## State

- Manuscript v0.5 is in draft3/ (LaTeX; PDF and Word copies are generated). First draft written 2026-11-09 from results/confirm3 (docs/CONFIRM3_RESULTS.md).
- In-project review by a separate AI session: docs/REVIEW_FINDINGS_2026-11-09.md and docs/REVIEW_PROPOSED_TEXT_2026-11-09.md. The proposed text was applied to the manuscript and to docs/CONFIRM3_RESULTS.md the same day, except the items listed below. This is not an outside review.
- Checks: src/paper/check_draft.py draft3 (references, writing rules, abstract length) and src/paper/check_numbers5.py (every decimal in the prose occurs in a source file; it does not show that a number is attached to the right claim).

## Not applied, and why

- docs/FRAME_SPEC_V2.md Section 5 (residual-risk column): frozen and hashed; change only in a new, non-confirmatory version.
- Receiver hardening (finding A5: wider except clause, guards in min_bounds and max_bounds): a post-freeze code change, so it belongs to a new version and a new cohort.
- Assumption R count for the 31 confirmation sites (finding B5): computed by the run but not printed; getting it means reopening the plans.

## Open decisions

- Whether to submit this version, or to build the version with corroboration across a day's units (the remedy for H8) and confirm it on a new sealed cohort. For the Prof.
- A sensitivity run of hybrid 1 with the flag capacity set to 4 (finding A4): development data first, labelled non-confirmatory.

## 2026-11-10: option B chosen

- Plan: docs/METHOD_V3_PLAN.md (draft, awaiting user and Prof approval; nothing built or downloaded).
- Correction applied the same day: a record-level check cannot verify units that never arrived, so the remedy text in the Discussion, the Conclusion, and docs/CONFIRM3_RESULTS.md was rewritten (only the exactly-needed class benefits; the other classes need more check bits and an unconditional metric).
