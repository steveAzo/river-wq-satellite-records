# Response to the second review of manuscript v1.1

Review received 12 November 2026 (major revision). The same principle as in the first response applies: the confirmation on the sealed 2022 cohort is frozen and is not re-run or re-scored; the decoder and the decision code are frozen; new analyses are post hoc and labelled as such. Each point below says what changed and where.

## Concern 1. Extremum witnesses in the decision rules (critical)

The reviewer is right that the text was incomplete. The frozen decoder (src/p3/certlang.py) already uses both facts of a witness: the top of the minimum-witness cell decides "some reading below theta" (exceeds_below), the minimum and maximum intervals are intersected with the witness cells (min_bounds, max_bounds, and through them the 7DADM), and the rate witness decides the conductance query directly (relative_change). The manuscript wrote only the global bound. Therefore, this was an omission in the specification, not in the implementation, and no reported number changes.

- Section 3.2 now separates the two facts of each witness: the global bound on every reading, and the bound on the extremum itself, with the rate witness as a separate source.
- Eq. (4) has the witness term for the answer 1 (with the reviewer's own two-reading example), Eq. (5) the witness ends of the extremum intervals, and the conductance paragraph the rate-witness rule.
- Proposition 1, part 1, now includes every answer or interval end that a witness provides directly; the proof in Appendix A has a new item (iv).
- A check of agreement between text and code (paper_tools/spec_check.py, post hoc): the rules were implemented again from the manuscript text, independently of the decoder, and compared on 20,000 random small days: every answer and every extremum interval agreed, and on days with a known truth neither implementation gave a wrong certain answer (108,291 certain answers). Removing the witness term from the written rule makes the check fail, so it can detect the omission the reviewer found.

## Concern 2. Operational conditions for soundness

- Section 3.2 now states that the receiver can recognise the only case in which condition B can fail (a certified span bounded by a kept value with a censored code, which the receiver decoded), and that a receiver that withholds the part-2 answers on the affected side of such a day reports only answers covered by Proposition 1. The receiver of this study did not apply that rule; its empirical consequence (4 days, no reported decision affected) was already counted.
- A forged or corrupted censored code is an integrity matter (Section 6.3 and the limit "Censored codes"); the soundness theorem assumes correct and corroborated messages and an honest encoder, as Section 3.2 states.

## Concern 3. Generality of the unconfigured-threshold results

Agreed. The introduction already said that the unconfigured thresholds were chosen by the analysts and are close to the configured ones, and Section 6.1 gives the directional rule. In addition:
- The conclusion no longer says "generality"; it states the claim as more decisions on hard cases at thresholds the node was not configured for, chiefly thresholds more extreme than the configured ones.
- Section 5.7 and Appendix D (new Table D.5) report the contrasts over all day-queries, not only hard cases (see concern 5).

## Concern 4. The idealised comparator

Section 3.5 now separates the three things: the flags are computed from the node's full record, which a real node also holds (so the flag values themselves are not an oracle); the idealisations are that the frame does not implement the flag field and that the node's flag software is error-free; therefore, the comparator is an upper bound on a practical flag design at configured thresholds, and the comparison at unconfigured thresholds is conservative for the witness design.

## Concern 5. Hard-case bands, and the CRC

Hard-case bands (post hoc, Section 5.7, Table D.5): the scored population is now defined in Section 4.3 (it was implicit; the 7DADM windows are scored with a band of 2 degC, the node allocates with 3 degC). The contrasts at the unconfigured thresholds were recomputed with narrower and wider bands, without the event rule, and over all day-queries, on the three years; the node's allocation is unchanged (exploratory/explore4_bands.py; summary exploratory/out/bands_summary.txt). With the study bands the contrasts equal the confirmation's under independent loss and differ by at most 0.003 under Gilbert loss, whose draws were made separately. On the sealed cohort, the contrast against flags plus record was 0.306 to 0.378 with bands half as wide, 0.182 to 0.226 with the study bands, 0.059 to 0.090 with bands twice as wide, and 0.188 to 0.233 without the event rule; the development years showed the same pattern. The advantage therefore does not depend on the particular bands in the sense of changing sign, but its size does: it grows as the scored cases move closer to the threshold.

Over all day-queries at the unconfigured thresholds, on the sealed cohort, the 3b rule was within 0.05 of flags plus record (-0.049 to +0.020 across the four conditions) and above the record alone by 0.031 to 0.034. The advantage of the witnesses is therefore concentrated on hard cases, and over all day-queries their record cost and their gain roughly balance against flags plus record. The manuscript now says so in Section 5.7 and in the Discussion.

CRC: Section 6.3 now states that the check covers the header and the body, detects every burst of at most 24 bits, and that 2^-24 is the share of undetected patterns among all non-zero error patterns, used as a planning value; the undetected rate under independent bit errors depends on the weight distribution of the code at this length, which was not computed. The abstract and the conclusion make no integrity claim.

## Experimental points (A to C)

- A (hard-case definition): concern 5.
- B (site population): "rivers" was replaced by "monitoring sites" in the abstract, the highlights, the introduction, the Discussion, and the conclusion; the scope limit already names the nine regions and the one or two sites in three of them.
- C (loss models): the limits already separate the proved erasure guarantee from the simulated loss; Section 6.3 states the erasure guarantee as independent of the loss model, and the limit "Loss models" lists what was not modelled.

## Novelty (section 5 of the review)

Section 2.7 now answers the reviewer's question directly: an error-bounded record with interval rules and a Reed-Solomon code is the record-only design of this study, a baseline; the study adds the choice, at the node and before any loss is known, of which extrema and rate pairs to send and how to protect them. The difference from TREAT is stated: TREAT's reader retrieves and can request more coded bits; over a one-way link the receiver can request nothing.

## Presentation (section 6 of the review)

- Worked example: the reviewer's two-reading example is now in Section 3.2 (Eq. 4), next to the constructed illustration of Fig. 2. A longer walk-through of one day was not added, to keep Section 3 within length; it can be added if the editor asks.
- Repetition of the first confirmation and the adoption story: kept, because the first review asked that the timeline and the post-hoc adoption be stated where each result is interpreted; the abstract no longer carries the first confirmation.
- Terminology: sites, as above.
