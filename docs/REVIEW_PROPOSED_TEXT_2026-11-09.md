# Proposed text for the findings of docs/REVIEW_FINDINGS_2026-11-09.md

Status: proposals only. Nothing here has been applied to docs/CONFIRM3_RESULTS.md, to the manuscript (draft3/), or to any frozen file. Each block names the place it would replace or extend, and the finding it answers. Numbers come from results/confirm3/verdicts3.md and results/confirm3/robust2_stage1.csv; the point differences marked "descriptive" were computed from the pooled levels and carry no interval. The wording follows the project's writing rules (no italics, labels with colons, serial comma, past tense for findings).

## 1. docs/CONFIRM3_RESULTS.md

### 1.1 Replace the last two sentences of Section 3 (after "The development estimate was therefore optimistic.") (A1)

The shares of the false-certificate rate by class of day (record only, receiver with CRC, sanity, and corroboration) explain the gap and show that the residual risk in docs/FRAME_SPEC_V2.md Section 5 is incomplete:
- Exactly the needed number of messages arrived: 58% of the rate at Q = 6 and 23% at Q = 12.
- Fewer messages arrived than needed, so only systematic units were used and nothing could be compared: 24% at Q = 6 and 41% at Q = 12 (false share on such days 0.17 and 0.19).
- Extra messages arrived but could not be compared: 18% at Q = 6 and 36% at Q = 12. All such false certificates occurred in blocks with one needed message that were not rejected, which suggests days whose record exceeded the quota and therefore had no parity (an inference; the number of units per day was not computed).
The development sample had 10 days with fewer messages than needed at Q = 12 (0.06% of its rows) against 401 (1.3%) in the cohort, so it did not contain the dominant failure mode. The limits were not changed.
H8 is conditional on one CRC-valid forgery. A longer CRC lowers the probability that a forgery passes (256-fold for CRC-24 by the stated model) but does not change this conditional share. It is therefore not a remedy for the failed hypothesis; corroboration for days with at most the needed number of messages, and for oversize days, would be. Neither was tested.

### 1.2 Add to Section 4 (caveats) (A2, A3, A4, A6, A8)

- Flags comparator: the flags design decides from its flags alone and does not use the record, even when the whole record arrives. At the unanticipated thresholds it therefore decided less than the record alone (0.275 against 0.546 under independent loss, 0.264 against 0.460 under Gilbert loss). The contrast of the 3b rule with the record alone (H5, second part: +0.260 and +0.245) is the fairer measure of the benefit of witnesses. Hybrid 1 exceeded the record alone at the unanticipated thresholds by 0.083 under independent loss and 0.097 under Gilbert loss (descriptive point differences of pooled levels).
- By construction: H7 and the configured and record parts of H9 hold by construction (flags are correct whenever a message arrives, and hybrid 1 merges the same flags at the same capacity). Only the unanticipated-threshold part of H9 and H2 to H5 are informative.
- Model scope: the design comparisons use an abstract slot model with slotted witnesses, not frame bytes. The byte-level checks (H1 round trip with all messages delivered, H8) cover the record and a layered group of four witnesses. Hosted witnesses, the conductance pair codes, flags, and decoding from a subset of messages had no byte-level test in the confirmation.
- Capacity: the 4.75-versus-4 modelling of flags also enlarges the spare room in which hybrid 1 hosts witnesses, so it favours hybrid 1 on the H9 alternative-threshold contrast (lower bound 0.248 against a limit of 0.20). The size of the effect was not measured.
- Forgery model: forgeries changed body bytes only, and "false" counts readings certified outside tolerance and witness codes that differ from the truth, not wrong decisions.
- Run record: the environment variables P3_TBAND, P3_UNKNOWN, and P3_MAXDAYS are read by the method code, were not set in the shell checked afterwards, and are not recorded in the log; the full-year round-trip count (3 x 10,095 blocks) rules out P3_MAXDAYS. Library versions were not recorded. The tag confirm3-freeze was created on commit a217e46 (12:33), docs/FREEZE3.md was written at 12:41 when the run started, and it was first committed at 16:57, after the run.
- Seeds: sites 03293500 and 04193500 share their random streams (same site number modulo 100000).

## 2. Manuscript

### 2.1 Abstract, replace the sentence beginning "Decision flags beat witnesses" (B1)

Decision flags beat witnesses on thresholds fixed at configuration time, but they decide from the flags alone. A hybrid that hosts witnesses in spare slots of the flag design cost nothing on configured thresholds and decided 0.083 and 0.097 more hard cases than the record alone on thresholds that nobody configured (descriptive), and 0.29 to 0.36 more than the flags.

### 2.2 Section 3.5 (Designs), replace the bullet "Decision flags" (B1, A4)

- Decision flags: the answers to the four configured queries, sent as 8 bits in every message. The server decides a configured query from the flags whenever any message arrives and decides an unanticipated threshold only by monotone implication from the configured answer; the recovered record is not used for decisions. The prototypes modelled the flags as 4.75 record values per message, against the integer 4 that frame version 2 allows, which favours the flags and also enlarges the spare room in which hybrid 1 hosts witnesses.

### 2.3 Section 4 (Study), new paragraph at the end of Section 4.2 (B3)

The comparison of designs used an abstract slot model, not the bytes of the frame: a message holds five value slots, a group of values over several columns is a systematic maximum-distance-separable code recovered from any k of the Q messages, and witnesses were applied with the slot of the extremum, whereas the frame carries the 13-bit code only. The byte-level tests (the round trip of H1 and the forgery study of H8) covered the record and a layered group of four witnesses; hosted witnesses, the conductance pair codes, the flags, and decoding from a subset of the messages were tested only in unit tests.

### 2.4 Section 5.2, H1 bullet, add after the sentence on the round trip (B5)

The round trip delivered all Q messages of 10,095 days at three plans each (30,285 blocks) and covered the record and a layered group of four witnesses.

### 2.5 Section 5.2, H4 bullet, replace the last clause (B4)

it held, and the upper bound of the loss was 0.105 under independent loss.

### 2.6 Section 5.2, H5 and H9 bullets, add after each (B1, A3)

- After H5: the flags design does not use the recovered record, so the first contrast is larger than the second; the contrast with the record alone is the fairer measure of the benefit of witnesses.
- After H9: the contrasts on configured hard-case decisions and on record recovery are zero by construction, because hybrid 1 uses the same flags at the same capacity, and only the unanticipated-threshold contrast tests the hybrid. Over the record alone it decided 0.083 (independent loss) and 0.097 (Gilbert loss) more hard cases at the unanticipated thresholds (descriptive point differences).

### 2.7 Section 5.3, bullet 4 (B4)

Send-on-delta and the tightened tolerance were below the record alone in record recovery and, with one exception, in hard-case decisions at this quota; the exception was the tolerance multiplied by 0.5 under Gilbert loss at the unanticipated thresholds (0.464 against 0.460).

### 2.8 Section 5.4, replace the last paragraph (B2)

Every cohort value was higher than the corresponding development value from six sites (0.027, 0.0004, 0.086, and 0.0029); the record-only value at Q = 12 was about 15 times higher. The false certificates came from three kinds of day, shown here for record only: days on which exactly the needed number of messages arrived (23% of the rate at Q = 12 and 58% at Q = 6), days on which fewer messages arrived than needed and only systematic units were used (41% and 24%), and days on which extra messages arrived but could not be compared, probably because the record exceeded the quota and had no parity (36% and 18%; an inference). Development had almost no days of the second kind at Q = 12. The forgeries are random-content forgeries conditional on a CRC pass, and they changed body bytes only. The unconditional rate of false certificates depends on the real error rate of the channel, which is unknown, and was not tested in the confirmation.

### 2.9 Discussion Section 6.2, replace the two bullets and the closing paragraph (B2)

- Corroboration: the corroboration rule compares surplus messages, so its value rises with Q, but it cannot act when no more messages arrive than are needed, when fewer arrive and only systematic units are used, or when the record exceeds the quota and carries no parity. At Q = 12 the last two cases carried most of the false-certificate rate.
- Sample: a sample of six sites held almost none of the days with fewer messages than needed, and it understated a conditional rate that depends on the mix of days.
The consequence for use is that the CRC-16 and the free receiver rules are not shown to be sufficient at the stated limits. A longer check (CRC-24) or a message authentication code lowers the probability that a corrupted message is accepted, and it does not change the conditional share of H8. To lower that share, the frame needs a check that spans the units of a day, so that days without spare messages can also be corroborated. Neither measure was tested.

### 2.10 Conclusion, replace the last sentence of the second paragraph (B2)

The hypothesis on false certificates after a forged message that passes the 16-bit check failed at twelve messages per day, and the failure points to days on which no message can be compared, which a longer check does not remove.

### 2.11 Discussion Section 6.1 and Introduction (B4)

- Replace "which flags cannot (H5)" by "which flags decided in 0.275 of hard cases by monotone implication (H5)".
- Replace "soundness that holds whatever the loss" by "soundness that holds whatever the loss pattern, provided the messages that arrive are uncorrupted".

### 2.12 Discussion Section 6.3 (Limits), replace the bullet on the 4.75 modelling and add bullets (A4, A6, A8, B5)

- Flags capacity: flags were modelled at 4.75 record values per message although the frame allows 4. This favours the flags, and it favours hybrid 1 more than the flags on the unanticipated-threshold contrast, because it enlarges the spare room for hosted witnesses; the size of the effect was not measured.
- Slot model: the design comparisons used an abstract slot model and slotted witnesses; hosted witnesses, the conductance pair codes, the flags, and decoding from a subset of messages had no byte-level test in the confirmation.
- Construction: the contrasts of H7 and the configured and record parts of H9 hold by construction.
- Integrity model: forgeries changed body bytes only; "false" counts readings certified outside tolerance and witness codes that differ from the truth, not wrong decisions.
- Run record: three environment variables of the method code (the 7DADM band, the unknown-history rule, and a day limit) and the library versions were not recorded, and the freeze record was committed after the run.

### 2.13 Section 3.2, Proposition 1, replace the sentence "Censored readings are outside the domain by definition." (B6)

Censored readings are outside the domain by definition. A censored reading that the server does not know to be censored receives the interval of a certified span; for the threshold queries this cannot produce a wrong answer, because the piecewise-linear reconstruction at such a position lies within the range of the neighbouring kept values, and the claim is not shown here for the conductance chain rule or for the daily maxima of the 7DADM.

### 2.14 Section 5.1, bullet "Targeting paid" (B4)

Replace "at a record-recovery cost of 0.001 to 0.005" by "at a record-recovery cost of 0.001 to 0.005 in the single-query prototype and 0.008 (0.004 to 0.013) for the generalised rule".

### 2.15 Section 4.3 (Procedure), add after "the sealed data were then opened once" (B5)

The tag was created on the commit of the experiments at the authors' instruction, the freeze record was written when the run started, and it was committed after the run; the checksums in it were verified by the run script before any analysis.

## 3. Other documents (A12)

- docs/CLAIMS_REGISTER_REV2.md, items 12 and 13: replace the development numbers by the cohort values (record only 0.0463 at Q = 6 and 0.0061 at Q = 12; layered k_w = 2 0.1050 and 0.0126) and mark H8 as failed.
- docs/REVIEW_BRIEF.md, Section 3 (Claims and priority): remove "Albanese 1996 was not read" or date it before 2026-11-09 17:00.
- docs/HANDOFF_2026-11-09.md, item 4: mark as done or superseded by docs/SEARCH_LOG_REV2.md.
- docs/HYBRID_RESULTS.md, caveat line: replace "favours both hyb1 and flags equally" by the text of 2.2.
- docs/FRAME_SPEC_V2.md Section 5, residual column of the first row: add the two classes of A1. This file is frozen and hashed; change it only in a new, non-confirmatory version.
- src/paper/make_figures5.py: move the legend of the forest plot off the H9 interval.
