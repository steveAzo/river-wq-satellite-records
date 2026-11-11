# Cover note for the authors (internal; not for submission) — draft v0.3, 2026-10-27

## What changed since v0.2
The manuscript was rebuilt after the pre-submission review (`Environmental_Modelling_Software_Critical_Editorial_Review.docx`).
The point-by-point response is in `docs/RESPONSE_TO_REVIEW.md`; the full record of the work is in `docs/REVISION_PLAN.md`.

- New title (the review's preferred wording); "regulatory-grade" and unconditional "guaranteed" removed.
- New method: byte-level frame, self-contained quantisation-exact encoder, record-first erasure code (optimal without
  channel knowledge), server certificate from received bytes, censoring, hardened receiver.
- New evidence: second confirmation on 36 sealed USGS sites in five other regions, with software and hypotheses
  frozen (commit 86f662b, tag confirm2-freeze); environmental decision analysis; robustness and resource analyses;
  site-clustered intervals throughout; exploratory low-cost re-analysis.
- Honest outcomes: six of eight hypotheses held. C1 (record size interval) and C2 (zero false certificates at a
  bit-error rate of 1e-2) failed; both are explained in the paper. Buffering, which v0.2 relied on, no longer helps.
  The headline cost rose from 15 B to 27 B per day.

## Authors must still do
1. Read the whole manuscript and the response; the Prof should confirm the framing of the two failed hypotheses.
2. Confirm with Kinéis: the 23-byte raw payload, device identifier, reception time, and the raw distribution format
   without an integrity flag (taken from public help-centre text; the pages are behind a sign-in).
3. Supply the corresponding author's e-mail address.
4. Archive a new Zenodo version of the repository for the revision and update `azongo2026code` (DOI) if it changes.
5. Add the generative-AI declaration (removed earlier at the user's request; the authors add it).
6. Decide whether to submit to Environmental Modelling & Software (recommended: the decision analysis and the
   reproducibility record address the review's main concern) or to Elsevier Internet of Things.
7. Check the Word copy layout against the PDF before sending it to anyone.

## Files
- `draft/deliverables/Paper3_draft_v0.3.pdf`, `.docx`, `Paper3_supplement_v0.3.pdf`, `Paper3_highlights_v0.3.txt`.
- Rebuild everything: `sh draft/build.sh` from `Paper3/`.
