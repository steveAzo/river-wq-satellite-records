# Review brief for method version 3, before the freeze (step 4 of docs/ROADMAP_V3.md)

Written 2026-11-10 by the AI session that built the code. The reviewer is a DIFFERENT AI session, in this project, with no memory of how the code was built. Its job is to find what is wrong before the freeze, not to confirm that it works.

## Rules for the reviewer

- Read only; do not edit any file outside docs/REVIEW_FINDINGS_V3.md (your output). The authors decide what is applied.
- Never open, list, plot, or summarise anything under data/clean/usgs_new4_2022 or data/raw (cohort 4 may not exist yet; if it does, do not read it). Development data (data/clean/usgs, data/clean/usgs_new3_2024, results/rehearsal4, results/v3dev) may be used.
- Frozen code (src/p3, src/data, tests/*.py, tools) must not change; version 3 code is in src/p3v3 and tests/v3.
- PC limits: 3.7 GB RAM; one heavy job at a time; run Python as `python -I` from Paper3/; foreground sleep is blocked.
- Report each finding with: file and line, what is wrong, a concrete failure scenario, severity (fix before freeze / report as limit / note), and a suggested fix. Also list what you tried that found nothing.
- Writing rules for the findings file: no italics, bullets for lists, "Label:" colons, sentence-case titles, past tense for findings.

## What to read (in this order)

1. docs/ROADMAP_V3.md, docs/HANDOFF_2026-11-10_V3.md
2. docs/CONFIRM4_PLAN_DRAFT.md (the pre-registration draft: hypotheses H1 to H8, limits, rehearsal table)
3. docs/METHOD_V3_PLAN.md (why version 3 exists; Section 8 logs the rules written before each development run)
4. docs/V3_DEV_RESULTS.md (development numbers the limits came from)
5. docs/REVIEW_FINDINGS_2026-11-09.md (the previous review; check its findings are handled: A4, A5, A7, A8, A9, B5)
6. Code: src/p3v3/confirm4.py (the driver), freeze4.py, receiver3.py, certlang3.py, frame3.py, integrity3.py, proto_base4.py; tests in tests/v3/
7. Rehearsal output: results/rehearsal4/verdicts4.md and RUN4.log (31 cohort-3 sites)

## Questions to answer

### A. Does the driver test what the plan says?
- For each of H1 to H8: does confirm4.verdicts compute exactly the contrast, metric, conditions, and limit stated in the plan? Any mismatch in sign, bound (lower or upper), Q, or loss model?
- Is the pooled, site-clustered bootstrap correct and paired (same resamples for both designs of a contrast)?
- H8 compares byte and slot recovery on the same days but with different loss draws: is the limit meaningful, and is the slot model's pessimism for the 3b rule a defect to fix rather than a hypothesis to test?
- H7 multiplies a conditional share by a pass probability (per_million): are the assumptions stated, and is body-only forgery (integrity3.forge) adequate (previous finding A6)?

### B. Can the run go wrong silently?
- Resumability: can a crash leave a partial or stale per-site file that is later read as complete (results/<tag>/slot4, byte4, integ4)?
- Module globals: frame3.CRCB and RECCRC, proto_base4 DESIGNS, FLAG_CAP, SLOTS. Can any stage run with the wrong setting?
- Seeds: are loss draws independent across sites and stages, and identical across designs where the plan requires pairing?
- The freeze check (verify_freeze) and freeze4.py: can the run start on code that differs from the tagged code? Is the freeze-before-download order sound (the seal is verified at run time only)?
- Environment: are there other import-time switches besides P3_TBAND and P3_UNKNOWN?

### C. Is the receiver hardening (finding A5) complete?
- receiver3.receive and certlang3: any input that still raises, or any path where a rejected block still contributes values or witnesses to a decision?
- Are the fuzz tests strong enough (tests/v3/test_receiver3.py)? Is the remaining limit (forged censored codes in record values) correctly stated?

### D. Are the hypotheses and limits sound?
- Which hypotheses are true by construction (the previous review found H7 and parts of H9 were)? H1 wrong decisions is declared as by construction; any others?
- The rehearsal on cohort 3 shows H4 and H5 would fail with the drafted limits (Section 5, item 2 of the plan). The building session recommended widening them (H4 -0.21 at Q 6 and -0.13 at Q 12; H5 -0.10), declared as set after the rehearsal. Is that defensible, or does it make the cost hypotheses uninformative? Propose what you would pre-register instead.
- Is the post-hoc adoption of the 3b rule on the CRC-24 frame stated honestly everywhere it matters?
- Is anything a reviewer at Environmental Modelling and Software would call circular, cherry-picked, or untestable?

### E. Anything else
- Bugs, dead code, misleading comments or docstrings, numbers in the docs that do not match result files.

## Output

docs/REVIEW_FINDINGS_V3.md with sections A to E, findings ranked by severity, and a short verdict: ready to freeze after which fixes.
