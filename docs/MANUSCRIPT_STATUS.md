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

## 2026-11-11: manuscript v1.0 (version 3, second confirmation)

- Draft folder draft4/ (copied from draft3/ v0.5 and rewritten): abstract, introduction contributions, model (frame with CRC-24, hardened receiver, designs), data and design (two rounds, freeze-before-download, hypothesis types), results (development, first confirmation and revision, second confirmation, descriptive, integrity), discussion (post-hoc adoption and the comparator error stated in the text), conclusion; supplement S1 (cohort 4 sites), S3 (first confirmation in full), S4 (files and reproduction).
- Deliverables: draft4/deliverables/Paper3_draft_v1.0.pdf (34 pages), Paper3_draft_v1.0.docx, Paper3_supplement_v1.0.pdf.
- Generated from results only by paper_tools/make_v1.py (tables and figures) and paper_tools/make_word_v1.py (Word flattener); src/ is frozen (docs/FREEZE4.md), so new paper scripts live in paper_tools/.
- Checks: src/paper/check_draft.py draft4 passes; paper_tools/check_numbers_v1.py finds every typed number in a source except the constructed example 7.01/7.03 (assumption R illustration).
- Not yet done: highlights file; related-work section unchanged from v0.5 (check it still matches the version 3 claims); the four small table overflows (4 to 5 pt); an outside review (step 9 of docs/ROADMAP_V3.md) before any preprint or submission.
- 2026-11-11 (after the user's commit): related-work section updated for version 3 (three sentences); highlights written (draft4/highlights.txt, all within 85 characters); table overflows removed (the PDF builds with none); Word copy rebuilt; outside-review brief written (docs/OUTSIDE_REVIEW_BRIEF.md). Remaining: the authors read v1.0; find an outside reviewer and send the brief with the PDF and supplement.
- 2026-11-11: superseded material moved to archive/ (draft/ -> archive/manuscript_v0.3, draft3/ -> archive/manuscript_v0.5, results/rehearsal4 and smoke4 -> archive/results_superseded, early reviews -> archive/early_reviews); README.md rewritten for version 3; outside-review request written as a shareable doc (claude.ai artifact RSLZQ5yqdXwywBJP96ecqW), with docs/OUTSIDE_REVIEW_BRIEF.md as the in-repository copy.
