# Response to the outside review of manuscript v1.0

Manuscript: Certified threshold decisions from error-bounded river water-quality records over one-way satellite IoT links (version 1.1, draft4/). Review received 11 November 2026. We thank the reviewer for a careful and constructive reading. Below, each point is answered with what changed and where.

One principle governed the response. The confirmation on the sealed 2022 cohort was frozen before the data were downloaded, and its verdicts are not re-run or re-scored. Every new analysis the review asked for was run after the confirmation, is labelled post hoc in the manuscript, and was run on the two development years first and on the sealed cohort second. No part of the method was changed; where the review points to a method change, it is stated as a limit.

## Fatal 1. Proposition 1 broader than its proof

We agree, and the gap was slightly wider than stated: a censored kept value next to an unrecognised censored reading can pull the reconstruction to the edge of the quantiser range, which can affect the threshold queries on that side as well as the conductance chain and the 7DADM.

- Proposition 1 is restated in three parts (Section 3.2): answers that hold over any superset of readings (all answers 0, the outer ends of the extremum intervals); answers that need condition B (every unrecognised censored reading has an interval that reaches genuine readings on both sides), which covers all answers 1 of the threshold rules, both ends of the extremum intervals, and the 7DADM; and the conductance rule's answer 1, which needs no unrecognised censored conductance reading.
- Lemma 2 gives the condition under which B holds (the span is bounded by kept values with uncensored codes) and the side on which it can fail.
- Complete proofs of Propositions 1 and 2 are in the supplement (Note S5).
- Empirical scope, counted after the confirmation: censored readings occurred on 4 of 30,854 analysed days in the three cohorts, all small negative dissolved-oxygen values at one 2022 site, each kept as a censored value; no conductance reading was censored. On those days condition B could fail on the low side only, and the true answer to every dissolved-oxygen query was yes; a low-side failure can only add a spurious yes. No reported decision depended on an uncovered case.

## Fatal 2. Assumption R

We agree that the condition must be operationally verifiable, and we have measured what it costs.

- The inference is stated precisely (Section 3.2): the coarsest decimal resolution of which every value of the site's record is a multiple; it was inferred for 26 of the 35 cohort sites.
- Post hoc, on all three years (Section 5.7, Table S6): with R off, the share of correct certain decisions fell by 0.003 to 0.006 and no decision was wrong; with a resolution ten times too coarse, 1.3% to 2.3% of decisions were certain but wrong.
- The Discussion now states the operational rule: in deployment the resolution is a declared field of the site profile, taken from the instrument's reporting precision and checked against the logger configuration; a site without a verified resolution runs with R off. H1 is described as a code check conditional on R.

## Fatal 3. CRC integrity and adversaries

We agree. Section 6.3 now separates three guarantees: erasure robustness (proved), detection of accidental corruption (conditional on a random bit-error model; the per-million figure and its assumptions are explained, and it is called a planning value, not a measurement), and adversarial integrity (not provided; a message authentication code would be needed). The abstract says that the check guards against random corruption, not deliberate forgery.

## Must fix 4. Post-hoc adoption

We agree with the distinction. Section 6.2 now states that the design failed its own adoption criterion, that the 0.08 clause applied to the pooled point estimate (the benefit clause used an interval bound), that H4 is a later evaluation of the adopted design and not a retrospective satisfaction of the rule, and that H2 and H3 are confirmatory evidence for the frozen design whatever the route by which it was chosen. A timeline table (Table 10) lists the order of events. The abstract gives the exact 0.082.

## Must fix 5. Final-version comparisons

We agree that the strongest alternatives had to be compared with the final design. Post hoc, coded send-on-delta (the strongest event-triggered alternative) and the record at half the tolerance (the strongest accuracy-first alternative) were run against the record alone and the 3b rule on the final frame (four value slots per message), on the sealed cohort, in the slot model; send-on-delta has no byte-level frame, and the slot model understates the 3b rule by about 0.03 in whole-record recovery (Section 5.7, Table S7). Send-on-delta was the weakest design in every condition (at six messages per day under independent loss: whole record 0.449, hard cases at unconfigured thresholds 0.302, against 0.842 and 0.525 for the record alone). The half-tolerance record lost whole-record recovery in every condition and decided more hard cases than the record alone only at twelve messages per day (0.731 against 0.647), still below the 3b rule (0.820). The 3b rule decided the most hard cases in every condition. We do not claim it is the best possible strategy; among the alternatives tested, none matched its decisions or preserved the record better than the record alone. The control for targeting, the exact allocator, and the hybrids were not re-run (stated as a limit). The flags-plus-record comparator is now described as idealised and modelled (Section 3.5).

## Must fix 6. Unconfigured thresholds

We agree, and the threshold sweep the reviewer proposed is now the main exploratory result (Section 5.7, Fig. 6). "Unanticipated" is renamed "unconfigured" and defined in the introduction. The witness design degraded in one direction only: toward more extreme thresholds than the configured one it kept deciding 0.93 to 0.99 of hard cases (for example dissolved oxygen below 2 to 4.5 mg/L, conductance changes above 20% and 30%), while flags plus record fell to the record-alone level; toward less extreme thresholds all designs were similar (for example dissolved oxygen below 6 mg/L: 0.740, 0.716, 0.687). The targeting rule explains the asymmetry, and the Discussion turns it into a configuration rule.

## Must fix 7. Loss models

Post hoc, on all three years (Section 5.7, Table S4): independent loss 0.1, 0.3, 0.5; Gilbert loss 0.3 with bursts of 3 and 6 and 0.5 with bursts of 3; six and twelve messages per day. The contrast with flags plus record stayed between 0.139 and 0.248 (every lower bound at least 0.114), and with the record alone between 0.174 and 0.356. Longer bursts reduced the gain most. The record cost grew with loss, to at most 0.096 on the cohort.

## Must fix 8. What is lost with the whole record

Post hoc (Section 5.7, Table S5): on days whose whole record was not recovered, 0.42 to 0.43 of readings were still certified within tolerance at loss 0.3. Over all days the witnesses cost 0.046 of certified readings against 0.082 of whole-record recovery.

## Must fix 9. Statistical uncertainty

Re-analysed from the run's per-site outputs (Section 5.4, Fig. 4): 10,000 resamples changed no interval end by more than 0.002; equal-site weighting and equal weighting of the four query kinds left every lower bound above the pre-registered limits (lowest 0.125); all 35 sites individually favoured the witness design in H2 and H3 in all four conditions. The estimand is defined in Section 4.3.

## Should fix 10. Practical use

Section 6.1 now has a worked use case on the sealed cohort (a dissolved-oxygen criterion revised from 5 to 4 or to 6 mg/L), separates compliance with a fixed criterion (flags are better; an undetermined answer triggers retrieval of the stored record) from retrospective and exploratory use (the witness design keeps more decisions available), and gives the configuration rule implied by the threshold sweep.

## Should fix 11. Related work

The related-work section was rewritten (Section 2, Table 1). New sources: suppression and model-based monitoring under message failure (Silberstein et al. 2006 and 2007, Tulone and Madden 2006, Deshpande et al. 2004), filtering for type-threshold functions (Riva and Finochietto 2014), data persistence (Kamra et al. 2006), certain answers over incomplete information (Imielinski and Lipski 1984) and interval answers in sensor databases (Cheng and Prabhakar 2003), online error-bounded approximation (Elmeleegy et al. 2009), and semantic communication (Zhang et al. 2023). Table 1 now compares what each line of work shares with this study and where its setting differs. The novelty statement is narrowed to the reviewer's formulation and states which databases were not searched. Table S2 records how far each source was read.

## Should fix 12. Thresholds

Section 4.2 now states that the criteria are examples, not universal standards, and justifies the 10% per hour conductance change as a study-defined event criterion, well beyond the 3% measurement tolerance.

## Should fix 13. Reproducibility

The authors will make the repository public and deposit the frozen commit, the data retrieval scripts, the plans, the freeze records, and the result files on Zenodo before submission.

## Minor 14. Abstract and terminology

The abstract was rewritten (exact 0.082; "no certain decision was wrong in the tested configurations"; the two confirmations separated; the check's scope stated), and five key terms are defined in the introduction. The reviewer's closing suggestion, the general principle of keeping the information that a future receiver's decisions need, is stated in the introduction with the claims kept narrow.

## A further point found while answering

While running the threshold sweep, a first version reported 215 wrong 7DADM decisions at 22 °C on one development site. They came from the evaluation: a seven-day mean that is exactly 22.0 in decimal arithmetic was 22.000000000000004 in floating point, so the computed truth was "above 22"; the certificate was right. The exploratory code now rounds computed quantities before evaluating the truth. The confirmation evaluated 19, 20, and 21 °C and found no such tie. This is reported in Section 5.7.
