# Response plan to the outside review of manuscript v1.0 (received 2026-11-11)

Written 2026-11-11 by the AI assistant for the authors. The review recommends major revision before submission. This plan triages its 14 points, states where we agree, and lists the work with a recommended action for each.

## The rule that constrains the response

- The confirmation (results/confirm4) is frozen and is not re-run or re-scored. Its verdicts stay as reported.
- Every new analysis the review asks for is exploratory: run after the confirmation, labelled post hoc in the paper, never presented as a test. Each is run on both development years first and on the sealed 2022 cohort second, so a reader sees whether the cohort behaves like development.
- No new method version: a change to the encoder, receiver, or decision rules would need a new sealed cohort (docs/ROADMAP_V3.md). Where the review points to a method fix, it is stated as a limit and future work.
- New exploratory code lives outside src/ (frozen): in paper_tools/ (re-analysis of existing outputs) and exploratory/ (new simulations reusing the frozen modules read-only).

## Triage

| # | Review point | Severity (review) | Our view | Action (recommended) | Kind |
|---|---|---|---|---|---|
| 1 | Proposition 1 broader than its proof (censored readings; conductance chain, 7DADM) | Fatal | Agree. The gap is also wider than stated: a censored kept neighbour can pull a reconstruction to the range edge for the threshold queries too | Restate Proposition 1 with its premise (valid knowledge) and a lemma giving the conditions under which unrecognised censored readings keep the knowledge valid; prove the 7DADM and chain cases under that lemma or narrow them; report the empirical scope: censored readings on 4 of 30,854 analysed days (DO, one 2022 site), each kept as a censored value | Proof and text; count done (paper_tools/censored_scope.py) |
| 2 | Assumption R inferred from the record | Fatal | Partly: conditional soundness is legitimate, but R must be operationally verifiable | Explain the inference precisely; state that in deployment R is a declared field of the site profile (instrument reporting precision), not inferred; report all results with R off; add a sensitivity run with a deliberately wrong (too coarse) resolution and count wrong decisions | Text; exploratory runs |
| 3 | CRC integrity vs malicious or structured corruption | Fatal | Agree on presentation; the paper already disclaims adversaries, but not prominently | Separate three guarantees (erasure robustness: proved; accidental corruption: conditional on a random-error model; adversarial integrity: not provided) in Model, Results, Discussion, and the abstract; justify the bit-error model and the per-million formula | Text |
| 4 | Post-hoc adoption vs a successful selection rule | Must fix | Agree | Timeline table (rule written, CRC-24 selected, adoption, comparator error found, H4 written, freeze, run); state the original adoption criterion failed; H4 described as a later evaluation; state that the 0.08 limit applied to the pooled point estimate (docs/METHOD_V3_PLAN.md, Section 8) | Text |
| 5 | Final version not compared with send-on-delta, tolerance x 0.5, random-day control, allocator, hybrids | Must fix | Agree for the strongest alternatives | Exploratory comparison at the D2 frame (4 values per message) of coded send-on-delta and tolerance x 0.5 against record only and the 3b rule, on both development years and the 2022 cohort, slot model with paired draws (byte level is not possible for send-on-delta without a frame variant; state this) | Exploratory runs |
| 6 | "Unanticipated thresholds" are analyst-chosen and nearby | Must fix | Agree; this is the most useful new result | Threshold sweep: share of hard cases decided as the threshold moves away from the configured one (DO, pH bounds, 7DADM, conductance change), byte level, paired draws; one figure per kind; rename "unanticipated" to "unconfigured" and define it | Exploratory runs; text |
| 7 | Loss models too narrow | Must fix | Agree | Sweep loss probability 0.1, 0.3, 0.5 and Gilbert burst length 3 and 6, byte level, H2 to H4 contrasts as descriptive curves | Exploratory runs |
| 8 | Whole-record recovery hides what is kept | Must fix | Agree | Add the share of readings certified within tolerance on days whose whole record was not recovered, and the share of readings certified overall; compute in the same harness as 6 and 7 | Exploratory runs |
| 9 | Statistical uncertainty | Must fix | Partly: intervals are valid; robustness not shown | Re-analyse existing outputs: 10,000 resamples; per-site effect distribution (figure); equal-site weighting; macro average over the four query kinds; define the estimand in Section 4.3 | Re-analysis (cheap) |
| 10 | Practical use case | Should fix | Agree | Concrete scenario from the 2022 data: a criterion revised after deployment (for example DO 5 to 6 mg/L, or a seasonal 7DADM), what each design lets the agency decide retrospectively; separate compliance from exploratory use | Text with one worked example |
| 11 | Related work: depth, Riva and Finochietto 2014, Growth Codes, semantic communication; categorical Table 1 | Should fix | Agree | Structured search (IEEE Xplore, ACM DL, Scopus or Web of Science, Google Scholar) with a logged query list; read the closest sources in full; rewrite Table 1 as capabilities compared; narrow the novelty statement to the review's formulation | Literature (needs database access) |
| 12 | Threshold justification | Should fix | Agree | Short paragraph: designated uses, regional variation, EPA sources as examples not universal criteria; justify the 10% per hour conductance change as a study-defined event criterion | Text |
| 13 | Reproducibility access | Should fix | Agree | Public repository and a Zenodo deposit of the frozen commit, data retrieval scripts, plans, freeze records, and result files before submission | Authors (outward-facing) |
| 14 | Abstract precision and terminology | Minor | Agree | Report 0.082 explicitly; "no wrong certain decision was observed in the tested configurations under the stated assumptions"; distinguish the two confirmations; define hard case, unconfigured threshold, witness, certificate, record recovery at first use | Text |

The review's closing suggestion (state the general principle: preserve information for the decisions a future receiver may need, not for reconstruction alone) is adopted for the introduction and conclusion, with the claims kept narrow.

## Order of work (recommended)

1. Proposition 1 repair (point 1) and the three-guarantee separation (point 3): the paper's credibility rests on them.
2. Cheap re-analysis (point 9) and the text items (4, 12, 14).
3. One exploratory harness for points 6, 7, and 8 (they share the byte-level decoder), then point 2 (R off, wrong R) and point 5 (baselines); development years first, then the 2022 cohort.
4. Literature (point 11) and the use case (point 10).
5. Manuscript v1.1, a short response-to-review document, and a second look by the same reviewer if possible.

## Decisions for the authors and the Prof

- Approve running exploratory analyses on the sealed 2022 cohort after its confirmation (labelled post hoc). Recommended: yes; without them the generality and loss questions can only be answered on development data.
- Database access for the literature search (point 11): the assistant can search the open web; IEEE Xplore, Scopus, or Web of Science need the university's access.
- Point 13 (public repository and Zenodo) is the authors' action.

## Progress (2026-11-11)

- Point 1 DONE: Proposition 1 restated in three parts with condition B and Lemma 2 (draft4/sec_model.tex); complete proofs of Propositions 1 and 2 in supplement Note S5; empirical scope counted (paper_tools/censored_scope.py): censored readings on 4 of 30,854 analysed days, all low-side dissolved oxygen at site 05576100 (2022), true answer yes on every DO query of those days, no conductance censoring; no reported decision depended on an uncovered case.
- Point 3 DONE: Discussion 6.3 now separates erasure robustness (proved), accidental-corruption detection (conditional, with the per-million formula explained), and adversarial integrity (not provided); abstract says the check guards against random corruption, not forgery.
- Point 4 DONE: Discussion 6.2 states the adoption criterion failed, that the 0.08 clause applied to the pooled point estimate, that H4 is a later evaluation; timeline table added (tab:timeline).
- Point 9 DONE: paper_tools/robust_stats.py (10,000 resamples, equal-site weighting, macro over kinds, per-site distribution; results/confirm4/robust_stats.csv); new Results subsection 5.4 and figure figs/sites.pdf; estimand defined in Section 4.3. All conclusions unchanged; every site favours the 3b rule in H2 and H3.
- Point 12 DONE: threshold justification paragraph in Section 4.2.
- Point 14 DONE: abstract rewritten (exact 0.082, scope of "no wrong decision", two confirmations separated, three guarantees); terms still to be defined at first use in the introduction (part of point 10).
- Remaining: points 2, 5, 6, 7, 8 (one exploratory harness; development years first), 10 (use case and definitions), 11 (literature, needs database access), 13 (authors).
