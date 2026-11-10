# Review findings for method version 3, before the freeze (step 4 of docs/ROADMAP_V3.md)

Date: 2026-11-10. Label: in-project reading by a separate AI session (Claude Code), following docs/REVIEW_BRIEF_V3.md. It is not an outside review. Nothing in the repository was edited except this file. No file under data/clean/usgs_new4_2022 or data/raw was opened, listed, or summarised.

Checks were run on development data only: cohort 3 (data/clean/usgs_new3_2024, 31 sites) with the cached plans of results/rehearsal4, and the rehearsal outputs. The scripts and their outputs are in the session scratchpad (C:\Users\User\AppData\Local\Temp\claude\68e606a9f8e1c1c5\7459a2a8-d247-436b-b753-d281f477ea40\scratchpad: c1.py, run_fc4.py with eval_fc4.py, h4byte.py, slotless.py).

Severity labels:
- Fix before freeze: the run would test something other than what the plan claims, or a hypothesis cannot fail.
- Report as limit: the evidence is weaker than it reads, and the limit should be stated.
- Note: low consequence, or a check that held.

## Ranked list

| Rank | Finding | Severity |
|---|---|---|
| 1 | A1. The slot model charged the flags comparator one value slot that the CRC-24 frame does not use; H5 and the post-hoc adoption argument rest on this artefact | Fix before freeze |
| 2 | D1. H7 cannot fail: its ceiling with a conditional share of 1 is 0.084 per million against a limit of 0.5 | Fix before freeze |
| 3 | A2. H4 is tested on the slot model, which is known to be pessimistic for the 3b rule by 0.04 to 0.05; at byte level the drafted limits pass on cohort 3 | Fix before freeze |
| 4 | D2. Widening the H4 and H5 limits after the rehearsal (to -0.21, -0.13, and -0.10) would make the cost hypotheses uninformative | Fix before freeze (decide the limits) |
| 5 | A3. Byte-check decisions still use slotted witnesses from the encoder (previous finding A4, last bullet, not handled); measured effect nil on cohort 3 | Note (cheap fix recommended) |
| 6 | B1. The seal is not tied to the cohort folder | Fix before freeze |
| 7 | B2. Stale or reused stage outputs are accepted without a code stamp; a completed run can be re-run with new limits | Fix before freeze |
| 8 | B3. verify_freeze does not check that docs/FREEZE4.md is committed or that its commit equals the tag | Fix before freeze |
| 9 | D3. H8 (record only) and H6 hold by construction or nearly; H8 (3b rule) tests a known bias | Report as limit (relabel) |
| 10 | A4. Integrity forgeries still change body bytes only (previous finding A6) | Fix before freeze (one line) or report as limit |
| 11 | B4. A crash between the slot-model main file and its meta file is resumed silently | Note (cheap fix) |
| 12 | D4. The post-hoc adoption is missing from docs/V3_DEV_RESULTS.md and docs/ROADMAP_V3.md | Fix in text |
| 13 | E1 to E6. Documentation and code consistency | Note |

## A. Does the driver test what the plan says?

### A1. Flag capacity 3 on the CRC-24 frame is an artefact (Fix before freeze)

Where: src/p3v3/confirm4.py line 51 (SLOTS, FLAG_CAP = 4, 3.0); src/p3v3/patch_base4.py (the rule "flags take one slot"); docs/V3_DEV_RESULTS.md, Phase 2 follow-up; docs/METHOD_V3_PLAN.md Section 8 (adoption entry); docs/CONFIRM4_PLAN_DRAFT.md H2, H5, H6.

What was wrong:
- On frame version 2 (CRC-16) the record symbol had 144 bits, 5 values of 24 bits plus 24 bits of unit overhead, and 0 spare bits. A flag field therefore cost one value slot (5 to 4), which is why flag capacity 4 was correct there.
- On the D2 frame (CRC-24) the record symbol has 136 bits: 24 bits of overhead plus 4 values use 120 bits, leaving 16 spare bits per message (checked with frame3.record_unit_bits and values_per_unit, script c1.py). A flag byte placed outside the record symbol in every message leaves 128 bits, and values_per_unit(128) is still 4. Flags therefore cost no value slot on the D2 frame, and the correct flag capacity is 4, not 3.
- patch_base4.py carried the version 2 cost (SLOTS - 1) into the D2 frame without a byte-level argument. The frame has no flag field, so no byte test could have caught it.

Measured effect (cohort 3, development, 31 sites, same seeds and loss draws as results/rehearsal4/slot4; flagsrec re-run at flag capacity 4 with proto_base4.run_site; script run_fc4.py and eval_fc4.py):

| Contrast, lower bound in brackets | Q 6 independent | Q 6 Gilbert | Q 12 independent | Q 12 Gilbert |
|---|---|---|---|---|
| H5, 3b rule minus flagsrec, record recovered, capacity 3 (as drafted) | -0.026 (-0.058) | -0.023 (-0.049) | -0.045 (-0.066) | -0.038 (-0.057) |
| H5, same, capacity 4 | -0.142 (-0.177) | -0.118 (-0.148) | -0.069 (-0.097) | -0.073 (-0.098) |
| H2, 3b rule minus flagsrec, unanticipated, capacity 3 | +0.273 (+0.229) | +0.222 (+0.184) | +0.190 (+0.139) | +0.207 (+0.163) |
| H2, same, capacity 4 | +0.224 (+0.176) | +0.188 (+0.147) | +0.175 (+0.127) | +0.184 (+0.140) |
| H6, 3b rule minus flagsrec, configured | identical at both capacities (-0.045, -0.123) | | | |

- At capacity 4, flagsrec recovered the whole record exactly as often as the record only (difference +0.000 in all four conditions). H5 then equals H4 to the third decimal and adds nothing.
- The statement "against the fair comparator the 3b rule's record cost is only -0.010 and -0.012" (docs/V3_DEV_RESULTS.md) and the post-hoc re-reading of the adoption rule "against the fair comparator" (docs/METHOD_V3_PLAN.md Section 8; docs/CONFIRM4_PLAN_DRAFT.md Section 1) rest on flagsrec paying -0.119 for a flag field that the frame carries for free. The adoption decision is therefore not only post hoc but justified by a mis-modelled comparator.
- H2 still passed its limit at capacity 4 on cohort 3, with a smaller margin (lowest lower bound +0.127 against +0.10).

Failure scenario: the confirmatory run passes H5 and the paper reports a small record cost against the fair comparator; a reviewer who computes the frame capacity finds that the comparator was handicapped by one value in four.

Suggested fix:
- Set FLAG_CAP = 4.0 with SLOTS = 4 (or derive both from frame3 in code, with a unit test that values_per_unit(record_unit_bits(0) - 8) equals values_per_unit(record_unit_bits(0)) at CRCB = 3).
- Drop H5 (it duplicates H4) or restate it. Keep H2 and H6 against flagsrec at capacity 4.
- Re-state the adoption in docs/METHOD_V3_PLAN.md and docs/CONFIRM4_PLAN_DRAFT.md: the 3b rule misses the written record clause against both the record only and the correctly modelled fair comparator; the adoption is post hoc and cannot be defended by the comparator argument.
- Re-run the development evaluation of the D2 slot model (results/v3dev_eval_d2.txt) at capacity 4 so that the development column of the plan is consistent.

### A2. H4 is tested on a model known to be pessimistic for the 3b rule (Fix before freeze)

Where: src/p3v3/confirm4.py lines 353 to 357 (H4 from A[Q], the slot model); src/p3v3/proto_base4.py heur_groups (cw whole slots for the layered group).

What was wrong:
- The slot model gives the layered group cw = ceil(h / 2) whole value slots for h hard witness codes. The frame packs 13-bit codes into bytes. With 3 or 4 hard codes and kw = 2, the slot model leaves 2 record values per message, while the frame leaves 3 (record bits 104 or 96, values_per_unit 3). With 1 or 2 hard codes the two agree. Hosted codes also use different room in the two models.
- The bias was known before the rehearsal (docs/V3_DEV_RESULTS.md, Phase 1b: 0.03 to 0.04) and was converted into the H8 limit of 0.06, instead of being removed. That answers question A3 of the brief: the pessimism is a defect of the model, not a property of the method, and it should be fixed or bypassed rather than tested.
- H4 is the declared cost of the design, and it was measured on the model that overstates it.

Measured (cohort 3, results/rehearsal4/byte4, script h4byte.py; 3b rule minus record only, whole record recovered, site-clustered 95% interval, 1,000 resamples; byte draws are not paired across designs, see B5):

| Condition | Slot model (verdicts4.md) | Byte frame |
|---|---|---|
| Q 6 independent | -0.142 (-0.177 to -0.108) | -0.094 (-0.112 to -0.076) |
| Q 6 Gilbert | -0.118 (-0.148 to -0.091) | -0.076 (-0.090 to -0.062) |
| Q 12 independent | -0.069 (-0.097 to -0.043) | -0.028 (-0.040 to -0.016) |
| Q 12 Gilbert | -0.073 (-0.098 to -0.049) | -0.034 (-0.046 to -0.023) |

- At byte level, the drafted limits (-0.15 at Q 6, -0.10 at Q 12) were met on cohort 3 with margins of 0.04 and 0.05 or more, without widening.

Suggested fix (one of two):
- Preferred: test H3 and H4 at byte level (the real frame), with the loss masks drawn once per day, Q, and condition and reused for both designs (paired), and add flagsrec to the byte check as "record decisions from the decoded record, plus the configured flags when any message arrived" (no frame change is needed, by the capacity argument of A1). Then H2 to H6 are all byte-level and the slot model becomes a descriptive cross-check.
- Minimum: give heur_groups byte-exact capacities (values_per_unit(record_unit_bits(witness_bytes)) for the actual codes and kw), re-run the development evaluation, and tighten the H8 limit for the 3b rule to the record-only value (0.01).
- Either way, declare that the change was made after the cohort 3 rehearsal (cohort 3 is development data), with the argument that the bias was documented before the rehearsal.

### A3. Byte-check decisions still use slotted witnesses (Note; cheap fix recommended)

Where: src/p3v3/confirm4.py lines 206 to 209 (key built from witness names; pb.know adds witnesses from it["wit"]); src/p3v3/proto_base4.py lines 96 to 109 (add_min_witness(slot, code), add_rate_witness(slot_a, ...)); src/p3/certlang.py lines 94 to 147.

What was wrong:
- The byte check decodes the witnesses from real messages but uses only their names. The decision layer then takes the slot and the code from the encoder (it["wit"], it["tw"], it["ew"]) and calls the slotted methods, which also pin the witness reading (add_kept). The frame carries codes only, and certlang already has the slotless methods (add_min_witness_value, add_max_witness_value, add_rate_witness_values). Previous finding A4 (last bullet) is therefore still open, and the "decisions from decoded values" of the plan (Section 5, item 2) are not fully from decoded values.
- A forged or wrong witness code can never affect a byte-check decision either, because the decoded code is not used.

Measured (cohort 3, 31 sites, 3b rule, Q 6, independent loss, every second day, 10 draws per day, the same masks for both variants; script slotless.py): hard cases at the unanticipated thresholds decided correctly 0.7885 with slotted witnesses and 0.7885 with slotless witnesses from the decoded codes, over 60,120 hard day-queries; wrong decisions 0 in both. The difference was nil at this setting, so the defect does not move H2 or H3; it remains a gap in what "decisions from decoded values" means, and the slotless soundness check is worth having in the run.

Suggested fix: in byte_site, build the knowledge from the decoded record values and add the decoded witness codes with the slotless methods (cheap; it also makes the byte check exercise the decoded codes). If not changed, state the limit with the measured size (nil at Q 6, independent loss, cohort 3). Severity lowered to note after the measurement.

### A4. Body-only forgeries (Fix before freeze, one line, or report as limit)

Where: src/p3v3/integrity3.py lines 63 to 70 (forge: lo = 3 + CRCB, header bytes 0 to 2 never changed).

What was wrong: previous finding A6 was not handled. A random corruption that passes the check falls in the header in about 3 of 20 non-check bytes. With N at most K a forged index, K, or coded bit is not compared with anything. H7 cannot fail anyway (D1), so this affects the descriptive class shares only.

Suggested fix: choose the forged positions from range(0, 3) and range(3 + CRCB, len(b)); or state the limit.

### A5. Hypotheses checked against the plan (held)

- H1 to H8 in confirm4.verdicts match the drafted table in metric, design pair, Q, loss model, bound (lower for H2 to H5, upper for H6 and H7, absolute difference for H8), and limit. Comparisons are >= for lower bounds, < 0 for H6, <= for H7 and H8, as written.
- The bootstrap is site-clustered and paired: Agg draws one index matrix per Q and uses it for both designs of every contrast (confirm4.py lines 290 and 300 to 303). The point estimate is the pooled ratio.
- The slot model is paired across designs: masks are drawn once per day and condition before the design loop (proto_base4.py line 214).
- The development and rehearsal numbers in docs/CONFIRM4_PLAN_DRAFT.md matched docs/V3_DEV_RESULTS.md and results/rehearsal4/verdicts4.md (H2 to H8, 40,380 round-trip blocks = 4 x 10,095 days).

## B. Can the run go wrong silently?

### B1. The seal is not tied to the folder (Fix before freeze)

Where: src/p3v3/confirm4.py lines 467 to 472; src/data/seal.py verify.

What was wrong: seal.py verify checks the paths listed in the checksum file, wherever they are. The driver does not compare those paths with the CSV files of the folder it analyses. A seal of any other folder (for example cohort 3) verifies, and a file in the folder that is not in the seal (but is in the selection) is analysed unsealed.

Suggested fix: read the checksum file, normalise the paths, and refuse unless the set of sealed CSV paths equals the set of CSV files in the folder. Log the MD5 of the checksum file in RUN4.log, and commit the checksum file right after sealing, before the run.

### B2. Stale and reused outputs (Fix before freeze)

Where: confirm4.py lines 175 to 176, 239 to 240, 475 to 520; run_multiday.site_plans lines 34 to 35; proto_base4.run_site line 189.

What was wrong:
- Every stage skips a site whose output file exists, with no record of which code wrote it. The rehearsal relied on this (plans and the two-site outputs were reused).
- Scenario: the confirmatory run crashes on a cohort-4 data quirk; the code is fixed, re-tagged, and re-frozen; the restart reuses plans and slot-model files written by the old code. verify_freeze passes because it checks the new tag.
- Scenario: after a completed run, the limits in T are changed and the tag is moved; a re-run recomputes only the verdicts from cached outputs. Only git history would show it.

Suggested fix: on a confirmatory start, write the freeze commit into results/confirm4/RUN_ID; refuse to start if results/confirm4/done4.flag exists, or if any stage folder holds files while RUN_ID is missing or names another commit; log every reused site file.

### B3. The freeze record itself is not checked (Fix before freeze)

Where: confirm4.py verify_freeze lines 99 to 122.

What was wrong:
- docs/FREEZE4.md is not in the paths compared with git, so an uncommitted or regenerated record passes; its "Commit" line is not compared with the tag's commit. The plan's rule (record committed before the download) is enforced by nothing.
- git() returns "" when a command fails, so a failing git diff or git status reads as "no difference" (fail-open). It did not fail in any test, but the design is fragile.

Suggested fix: require git status of docs/FREEZE4.md to be clean, require the commit named in it to equal rev-list of the tag, and treat a non-zero return code of diff or status as a refusal. Optionally record library versions in FREEZE4.md and compare them at run time (only logged now).

### B4. Slot-model meta file written after the main file, not atomically (Note)

Where: proto_base4.py lines 325 to 327, resume check line 189.

What was wrong: a crash after os.replace of site_Q12.csv and during the meta write leaves a truncated meta file; the resume check sees the main files and skips the site; site_aggregate merges on the truncated meta and drops days from the hard-case metrics without an error.

Suggested fix: write the meta file first through a .tmp file and os.replace, and check both files in the resume condition (a new file in src/p3v3, so allowed).

### B5. Seeds and settings (held, one note)

- Seeds use the full site number (run_e2e.site_number returns int(name[:15])), so previous finding A7 is handled; slot, byte, and integrity streams are separate ([pb.SEED, Q, site], [SEED, 4, site], [SEED, 5, site]).
- Note: the byte check draws masks from one stream in sequence for rec, then heur, so the two designs see different losses. This does not matter for H8 (byte against slot is unpaired by design) but matters if H4 moves to byte level (A2): draw the masks once and reuse them.
- Module globals: frame3 is imported under one name ("frame3") by confirm4, integrity3, and receiver3, so CRCB = 3 set in check_environment reaches build, forge, and receive (the rehearsal log shows CRCB=3). proto_base4 receives DESIGNS, FLAG_CAP, and SLOTS in the job tuple. No stage could run with another setting, apart from the value of FLAG_CAP itself (A1).
- Environment: the only os.environ reads reachable from the driver are P3_TBAND and P3_UNKNOWN in src/p3/proto_queries.py (P3_DESIGNS, P3_MAXDAYS, P3_SITES are in src/p3/proto_base.py, which the driver does not import); the driver refuses any P3_* variable and checks both import-time values. python -I ignores PYTHON* variables. No other switch was found.

## C. Receiver hardening (finding A5 of the previous review)

- receiver3.receive wraps both _receive_body and _sanity in a catch-all, clears values, witnesses, bound, and last_pos on any exception, and counts non-bytes or wrong-length objects as failed messages. I found no input that raised. Rejected blocks contribute nothing in the driver: byte_site uses an empty value set when record_rejected and no witnesses when witness_rejected; integrity_site sees cleared fields.
- The fuzz tests (tests/v3/test_receiver3.py) cover header, body, descriptor, truncation, extension, CRC recomputation, injected exception types, and a malformed profile. That is adequate for "never raises".
- Gap: no test or run exercises the decision layer on forged decoded content, because the decision layer never reads decoded codes (A3) and the integrity stage computes no decisions. The declared limit (forged censored codes 0 or 8191 in record values remove readings from decisions) is stated correctly, but its consequence for wrong decisions is unmeasured. Adding a wrong-decision count to the forged draws of integrity_site (pb.decide on the decoded values) would measure it, descriptively.

## D. Are the hypotheses and limits sound?

### D1. H7 holds by construction (Fix before freeze)

Where: confirm4.py per_million line 273; tests/v3/test_confirm4.py test_h7_limit_on_upper_bound.

What was wrong: per_million(Q) is the expected false-certificate days per million for a conditional share of 1. It equals 0.042 at Q = 6 and 0.084 at Q = 12 (23-byte messages, bit-error rate 1e-3, pass probability 2^-24; script c1.py). The limit is 0.5, so H7 passes even if every forged message produced a false certificate. The unit test can make H7 fail only with an upper bound of the share of about 5.9, which is impossible for a share. This repeats the pattern of previous finding A3.
- Also by construction under a single forgery: the N > K class is 0 (a single wrong symbol cannot be consistent with an MDS codeword when a further symbol arrives), as the rehearsal shows (0.0000 in every block).
- The per-million formula multiplies the mean number of arrived messages by the mean conditional share; because the share is highest on days with few messages, this overstates the rate (conservative). The 2^-24 pass probability is also conservative for low-weight random errors, which a CRC-24 always detects. Both are notes.

Suggested fix: relabel H7 as an analytic bound (like H1), state the bound (at most 0.084 per million days at 1e-3 under random corruption, whatever the receiver does), and report the conditional shares by class descriptively. If a testable integrity hypothesis is wanted, use one whose outcome is not fixed by the CRC length, for example a wrong-decision share given one forgery, with a limit set from development data.

### D2. The H4 and H5 limits (Fix before freeze: decide)

The question of the brief: is widening to -0.21 and -0.13 (H4) and -0.10 (H5) after the rehearsal defensible?

- Cohort 3 is development data for version 3, so setting limits after looking at it is permitted if declared. The problem is informativeness: a limit chosen as "the rehearsal lower bound minus a margin" passes unless cohort 4 is worse than cohort 3. A cost of up to 0.21 in whole-record recovery at Q 6 is not a claim a reader can use. It is also measured on the model that overstates the cost (A2), so the widening compensates for a modelling defect rather than for site-to-site spread.
- H5 at -0.10 would test a contrast that is an artefact (A1); at the correct capacity H5 equals H4.

What I would pre-register instead:
- H4 at byte level, paired masks, with the drafted limits unchanged: lower bound at least -0.15 at Q 6 and -0.10 at Q 12, both loss models. Development byte values: 2023 points -0.089, -0.076, -0.028, -0.035; cohort 3 lower bounds -0.112, -0.090, -0.040, -0.046. The hypothesis can fail and has a usable reading ("the cost is below 15 points at Q 6 and 10 points at Q 12").
- Report against the original substantive margin as well: state that the byte-level point cost at Q 6 (about -0.09) is beyond the -0.08 of the written adoption rule, which is why the adoption is post hoc.
- Drop H5, or replace it with H5' = 3b rule minus flagsrec (capacity 4) on the whole record, which is then identical to H4 and should be stated as such.

### D3. Other hypotheses that cannot fail or are weak (Report as limit, relabel)

- H8, record only: the slot model of the record only is the frame's MDS code with the same 4 values per unit, so agreement is exact up to loss-draw noise (rehearsal: 0.000 in all four). It is a code check like H1.
- H8, 3b rule: tests the size of a known modelling bias (A2), not a property of the method. If A2 is fixed (byte-level contrasts or byte-exact capacities), H8 can become a single tight check or be dropped.
- H6: flagsrec decides configured hard cases at 0.96 to 1.00 because its flags come from the truth whenever a message arrives; H6 fails only if the 3b rule is almost perfect at the configured thresholds. It is a stated known limit; count it as such, not as support.
- Consequence: of the eight hypotheses, only H2, H3, and H4 are informative tests of the method; H5 is redundant at the correct capacity. The results document must not present "n of 8 held" without this.

### D4. Post-hoc adoption: where it is and is not declared (Fix in text)

- Declared: docs/CONFIRM4_PLAN_DRAFT.md Section 1; docs/METHOD_V3_PLAN.md Section 8; docs/HANDOFF_2026-11-10_V3.md.
- Not declared: docs/V3_DEV_RESULTS.md (ends at "This is a decision for the user and the Prof" and does not record the adoption); docs/ROADMAP_V3.md ("the fair comparison keeps the 3b rule ... at a record cost of 0.03 to 0.09" omits that the written clause was missed). The H4 row of the plan table calls it "the declared cost" without saying post hoc.
- After A1, the justification text ("re-read against the fair comparator") must change everywhere it appears.

### D5. Other points a reviewer at Environmental Modelling and Software would raise (Report as limit)

- The flags comparator decides from the truth (flag_decisions reads meta["truth"]), so flagsrec is an idealised node with perfect configured-threshold decisions; this is fair as a bound but should be stated.
- The unanticipated thresholds (alt1, alt2) and the hardness bands were fixed in version 2 and have been seen on every development cohort; they are not chosen after cohort 4, but they are analyst-chosen.
- H7 depends on an assumed bit-error rate and independent bit errors; stated in the plan.

## E. Other findings

- E1 (Note): src/p3v3/proto_base4.py was edited by hand after src/p3v3/patch_base4.py (cl3.max_bounds), so the patch script no longer reproduces the file. Either update the patch or state that the file is the source.
- E2 (Note): proto_base4.main's docstring names src/p3v3/proto_base3.py.
- E3 (Note): the limits in confirm4.T are said to be copied from docs/CONFIRM4_PLAN.md, but nothing checks it; a test that parses the plan's limit table and compares it with T would catch a mismatch at the freeze.
- E4 (Note): the rehearsal guard ("new4" or "2022" in the folder name) does not protect against other scripts (proto_base4.main, bytecheck2.py, integrity3.py) opening the cohort folder; the rule is procedural.
- E5 (Note): the confirmatory command ignores arguments after the seal; a missing selected site is logged but does not stop the run (as intended).
- E6 (Note): docs/REVIEW_BRIEF_V3.md mentions the recommended widened limits; docs/CONFIRM4_PLAN_DRAFT.md and confirm4.T still hold the drafted limits. Consistent for now; keep it that way until the authors decide (D2).

## Tried and found nothing

- An input to receiver3.receive that raises (reading of the code paths; the fuzz design).
- A second import of frame3 under another module name that would leave CRCB at 2 in one stage.
- An environment switch other than P3_TBAND and P3_UNKNOWN reachable from the driver.
- An unpaired bootstrap or a sign or bound error in H2 to H8.
- A seed collision between sites (full site numbers are used).
- A mismatch between the plan's development or rehearsal numbers and the result files.

## Not checked

- The full test suite was not run (it is the freeze script's job), and no mutation check was made.
- freeze4.py and verify_freeze were read, not executed against a real tag.
- The slotless-witness check (A3) used every second day at Q 6, independent loss, 10 draws per day.

## Verdict

Not ready to freeze. Ready to freeze after:
1. A1: flag capacity 4 on the D2 frame; H5 dropped or restated; adoption text corrected; development column re-run.
2. D1: H7 relabelled as an analytic bound (or replaced by a testable integrity hypothesis).
3. A2 with D2: H3 and H4 at byte level with paired masks (preferred), drafted limits kept (-0.15 and -0.10), the change declared as made after the cohort 3 rehearsal; no widening.
4. B1, B2, B3: seal tied to the folder, run stamp against stale outputs and re-runs, freeze record committed and matched to the tag.
5. Then a fresh 31-site rehearsal on cohort 3 and the full test suite.
Items A3, A4, B4, D3, D4, and E1 to E6 are cheap and should be done in the same pass. The authors decide every change; nothing above was applied.
