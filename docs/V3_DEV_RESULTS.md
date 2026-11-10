# Version 3, Phase 1a results (development data, slot model)

Date: 2026-11-10. Status of every number: numerical, trace-driven simulation on USGS 2023 development data (38 sites with four-parameter days), slot model (five value slots per message, maximum-distance-separable group recovery), identical loss draws for all designs, paired site-clustered 95% intervals (1,000 resamples). Not a confirmation, not byte-level. Code: src/p3v3/proto_base3.py (derived from the frozen src/p3/proto_base.py), src/p3v3/eval3.py. Raw printout: results/v3dev_eval.txt; per-site files results/v3dev/dev_cap4 and dev_cap475. Written by an AI assistant; no outside reviewer has read it. Wrong decisions: maximum 0.000 in every design, plan, and loss model.

## Designs and what changed against version 2

- Flag capacity 4 values per message (the frame's real value, run cap4) and 4.75 (the earlier modelling, run cap475, for the sensitivity of review finding A4).
- New fair comparator flagsrec: decision flags that also use the recovered record (the certificate decides when certain, otherwise the flag).
- Seeds use the full site number (review finding A7), so levels differ slightly from the frozen runs.
- Not yet run in version 3: hybrid 2 (flags plus the 3b rule), the exact allocator, send-on-delta, tolerance x 0.5.

## Q = 6, independent loss (levels: record recovered / hard configured / hard unanticipated)

| Design | Capacity 4 | Capacity 4.75 |
|---|---|---|
| Record only | 0.904 / 0.675 / 0.571 | same |
| Flags (record discarded) | 0.845 / 0.999 / 0.217 | 0.888 / 0.999 / 0.217 |
| Flags plus record (flagsrec) | 0.845 / 0.999 / 0.572 | 0.888 / 0.999 / 0.596 |
| Hybrid 1 (flagsrec plus hosted witnesses) | 0.845 / 0.999 / 0.599 | 0.888 / 0.999 / 0.632 |
| 3b rule (layered witnesses) | 0.824 / 0.967 / 0.783 | same |

## Contrasts that matter (Q = 6, capacity 4; independent loss, then Gilbert loss)

| Contrast | Independent | Gilbert |
|---|---|---|
| Hybrid 1 minus flagsrec, unanticipated | +0.027 (+0.022 to +0.033) | +0.023 (+0.018 to +0.028) |
| Hybrid 1 minus record only, unanticipated | +0.028 (+0.015 to +0.041) | +0.048 (+0.036 to +0.060) |
| 3b rule minus flagsrec, unanticipated | +0.210 (+0.185 to +0.236) | +0.176 (+0.156 to +0.196) |
| 3b rule minus record only, unanticipated | +0.211 (+0.180 to +0.244) | +0.201 (+0.176 to +0.228) |
| 3b rule minus flagsrec, configured hard cases | -0.033 (-0.041 to -0.025) | -0.113 (-0.128 to -0.101) |
| 3b rule minus flagsrec, record recovered | -0.021 (-0.038 to -0.006) | -0.012 (-0.026 to 0.000) |
| Flagsrec minus record only, record recovered | -0.060 (-0.076 to -0.045) | -0.055 (-0.065 to -0.046) |

At Q = 12 the pattern is the same at higher levels: hybrid 1 minus flagsrec is +0.025 and +0.025 on the unanticipated thresholds, and the 3b rule minus flagsrec is +0.152 and +0.165.

## Findings

1. The hosted witnesses of hybrid 1 add little once the comparator uses its record: +0.02 to +0.04 over flagsrec at both capacities, far below the +0.29 to +0.36 reported in version 2 against flags that discard the record, and below the stop-rule size of +0.10 proposed in docs/METHOD_V3_PLAN.md. Hybrid 1 is not a design that carries the paper.
2. The targeted layered design (the 3b rule) keeps a large benefit on thresholds nobody configured: about +0.21 over both the record alone and flagsrec at Q = 6, and +0.15 at Q = 12, which meets the proposed size. Its costs are 0.01 to 0.02 of record recovery and 0.03 (independent loss) to 0.11 (Gilbert loss) of configured-threshold hard-case decisions, relative to flagsrec.
3. The modelling choice of 4.75 hid a real cost of flags. At the frame's capacity of 4, the flags designs recover the whole record 0.06 less often than the record alone (0.845 against 0.904), against 0.016 at 4.75. This cost applies to flagsrec and hybrid 1 equally and narrows the gap to the 3b rule: at 4.75 the 3b rule minus flagsrec in record recovery was -0.064, at 4 it is -0.021.
4. The 4.75 modelling inflated hybrid 1 over flagsrec by about 0.01 (0.036 against 0.027) and the flags designs' record recovery by 0.04; the review's concern (finding A4) was real in direction and small in the hybrid contrast.

## Consequences for the plan

- The stop rule of Section 6 of the plan is not met by hybrid 1 and is met by the 3b rule. The design to carry into Phases 2 and 3 is therefore the layered one (the 3b rule, or hybrid 2, which was not run here), not hybrid 1. This is a development finding and changes the adoption decision of version 2.
- Open question for the next run: whether hybrid 2 (flags plus the 3b rule) at the real capacity combines the flags' configured-threshold level with the 3b rule's unanticipated-threshold level at an acceptable record cost. In version 2 it cost 0.094 in record recovery against flags at capacity 4.75; at capacity 4 the comparison changes. Its adoption rule must be written before it is run on the confirmation-stage design.
- Limits: slot model, slotted witnesses, development data, analyst-chosen alternative thresholds, hard-case bands tuned on this development year.

## Second run: hybrid 2 and the exact allocator (capacity 4, same seeds and loss draws)

Output: results/v3dev/dev_cap4b (new designs) merged with dev_cap4 into dev_cap4all by concatenating per-site files; evaluator src/p3v3/eval3.py (pair list extended); printout results/v3dev_eval_b.txt. Wrong decisions: 0.000 in every row. The adoption rule was written in docs/METHOD_V3_PLAN.md before the run.

| Contrast (unanticipated thresholds unless stated) | Q = 6 independent | Q = 6 Gilbert | Q = 12 independent | Q = 12 Gilbert |
|---|---|---|---|---|
| 3b rule minus flagsrec | +0.210 | +0.176 | +0.152 | +0.165 |
| 3b rule minus record only, record recovered | -0.080 | -0.067 | -0.027 | -0.031 |
| Hybrid 2 minus flagsrec | +0.192 | +0.178 | +0.144 | +0.158 |
| Hybrid 2 minus record only, record recovered | -0.189 | -0.164 | -0.072 | -0.081 |
| Exact allocator minus flagsrec | +0.155 | +0.116 | +0.059 | +0.062 |
| Exact allocator minus record only, record recovered | -0.067 | -0.069 | -0.014 | -0.014 |

Applying the rule (at least +0.10 over flagsrec in all four conditions, and record recovery no more than 0.08 below the record alone):
- 3b rule: passes, but the Q = 6 independent record cost is exactly at the limit (-0.080).
- Hybrid 2: fails on record recovery (-0.19 at Q = 6). It reaches the flags' configured level (hard cases 1.000) but pays the record cost twice.
- Exact allocator: fails the benefit at Q = 12 (+0.059), although its record cost is the smallest.
- Therefore the 3b rule is the only design that passes. Its configured-threshold cost against flagsrec (-0.03 independent, -0.11 Gilbert at Q = 6) remains.

Reading: no design gets the flags' configured level and the layered unanticipated level without a large record cost. The paper's claim has to be a trade-off with the 3b rule, stated against the fair comparators. Still the slot model, development data, analyst-chosen thresholds.

## Phase 1b (partial): byte-level check of the record and the 3b rule

Code: src/p3v3/bytecheck.py; log results/v3dev_bytecheck.log; per-day files results/v3dev/bytecheck_full.csv and bytecheck_full_slot.csv. Every fourth development day (2,598 days, 38 sites), 20 independent-loss draws per day (p = 0.3), real messages of frame version 2 (hard objects in a layered group with k_w of 1 or 2, easy objects hosted in the last record unit) and the real receiver (CRC, corroboration). Slot figures are the same days from the slot-model run (different loss draws, so the comparison is of levels, not paired). No day was unbuildable. Wrong decisions were not measured here (no decision layer in this check).

| Whole record recovered | Byte frame | Slot model |
|---|---|---|
| Q = 6, record only | 0.904 | 0.902 |
| Q = 6, 3b rule | 0.824 | 0.822 |
| Q = 12, record only | 0.990 | 0.991 |
| Q = 12, 3b rule | 0.965 | 0.961 |

Layered witnesses decoded in the byte frame, when the day had any: 0.993 at Q = 6 and 1.000 at Q = 12.

Reading: the slot model reproduces the byte frame within 0.004 for the record and the 3b rule under independent loss, so the 3b-rule numbers in this document are not an artefact of slot modelling. Not yet byte-level: the decision layer (hard-case decisions from the decoded values), Gilbert loss, and the flags comparator (the frame has no flag field; a flagsrec byte design would need one). The comparison is a level check on a 1-in-4 sample of days.

## Phase 2: integrity study (development data, byte-level, rules written before the run)

Code: src/p3v3/frame3.py (derived from the frozen frame2.py by src/p3v3/patch_frame3.py; tests/v3/test_frame3.py), src/p3v3/integrity3.py, src/p3v3/integrity3_eval.py. Printout: results/v3dev_integrity3_eval.txt; draws: results/v3dev/integrity3_full.csv and integrity3_full_rec.csv. 38 development sites (2023), every third day, 8 draws per day and block, 442,946 forged draws, independent loss 0.3, forced CRC-valid forgery of one arrived message, receiver with sanity and corroboration. Status: numerical; the bit-error rate is a modelling assumption (no channel was measured); D4 not simulated (equivalent to D2 under random corruption).

Expected false-certificate days per million days at a bit-error rate of 1e-3 (point / upper end of the site-clustered 95% interval); limit 0.5 on the upper end:

| Design | Record Q=6 | Record Q=12 | 3b rule Q=6 | 3b rule Q=12 |
|---|---|---|---|---|
| D0 (frame v2) | 0.46 / 0.57 | 0.058 / 0.090 | 0.80 / 0.96 | 0.18 / 0.27 |
| D1 (plus record CRC-32) | 0.22 / 0.30 | 0.028 / 0.045 | 0.57 / 0.72 | 0.13 / 0.19 |
| D2 (CRC-24) | 0.0029 / 0.0034 | 0.0005 / 0.0007 | 0.0039 / 0.0045 | 0.0011 / 0.0015 |
| D3 (both) | 0.0016 / 0.0021 | 0.0003 / 0.0004 | 0.0028 / 0.0034 | 0.0007 / 0.0011 |

Whole-record recovery, independent loss 0.3 (point):

| Design | Record Q=6 | 3b rule Q=6 | Record Q=12 | 3b rule Q=12 |
|---|---|---|---|---|
| D0 | 0.904 | 0.824 | 0.989 | 0.967 |
| D1 | 0.874 | 0.752 | 0.988 | 0.956 |
| D2 | 0.843 | 0.756 | 0.978 | 0.951 |
| D3 | 0.818 | 0.687 | 0.977 | 0.938 |

Conditional shares (given one CRC-valid forgery) by class of day, D0 record Q=6: N<K 0.16, N=K 0.25, N>K 0.000, uncoded 0.20. The record CRC-32 (D1) removes the N=K class (0.249 to 0.000) and leaves N<K and uncoded unchanged; CRC-24 (D2) leaves the conditional shares unchanged (it lowers the probability that a forgery passes, by a factor of 256).

Result of the pre-written rule: D0 and D1 fail the limit (3b rule at Q=6, upper bounds 0.96 and 0.72); D2 and D3 pass with a margin of over 100; the selected design is D2 (CRC-24 per message), the simpler of the two.

Consequences to carry into Phase 3:
- The price is record recovery: D2 against D0 is -0.061 (record only, Q=6) and -0.068 (3b rule, Q=6). Within D2 the 3b rule is 0.087 below the record only at Q=6, which is above the 0.08 limit of the Phase 1a adoption rule (that rule was applied to the capacity of D0, where the difference was 0.080). The adoption rule has to be re-applied to the D2 frame before pre-registration; with the limit as written it would fail narrowly.
- The result is sensitive to the limit: a limit of 1.0 per million would let D0 pass (upper 0.96). The limit of 0.5 was written before the run and is not changed; the margin of D2 (about 100 times) says the byte-granular CRC-24 is larger than the limit needs, but a shorter check does not save capacity because the record symbol changes in whole bytes.
- The conditional shares do not fall under D2; the safety comes from the pass probability, under a random-corruption model. A structured fault (a stuck bus, repeated frames) could defeat that assumption, which is a limit to state.

## Phase 2 follow-up: layered design on the CRC-24 frame (slot model with 4 slots per message)

Code: src/p3v3/proto_base4.py (derived from proto_base3.py by src/p3v3/patch_base4.py; SLOTS = 4, flags take one slot, so flag capacity 3); designs rec, heur (the 3b rule), flags, flagsrec; same 38 development sites and loss draws; evaluator src/p3v3/eval3.py; printout results/v3dev_eval_d2.txt. Wrong decisions 0.000 everywhere. Status: numerical, slot model, development data.

| Contrast | Q=6 independent | Q=6 Gilbert | Q=12 independent | Q=12 Gilbert |
|---|---|---|---|---|
| 3b rule minus flagsrec, unanticipated thresholds | +0.244 | +0.198 | +0.161 | +0.180 |
| 3b rule minus record only, record recovered | -0.129 | -0.109 | -0.061 | -0.065 |
| 3b rule minus flagsrec, record recovered | -0.010 | -0.012 | -0.035 | -0.028 |
| 3b rule minus flagsrec, configured hard cases | -0.035 | -0.114 | -0.018 | -0.031 |
| Flagsrec minus record only, record recovered | -0.119 | -0.097 | -0.026 | -0.036 |

Application of the Phase 1a adoption rule, unchanged (at least +0.10 over flagsrec in all four conditions; record recovery no more than 0.08 below record only):
- Benefit clause: met in all four conditions (+0.16 to +0.24).
- Record clause: NOT met at Q = 6 (-0.129 and -0.109), met at Q = 12 (-0.061 and -0.065). The slot model is more pessimistic than the byte frame for the layered group (byte level, same frame: 3b rule 0.756, record only 0.843, difference -0.087 at Q = 6, independent loss, Phase 2 table), but the byte level also exceeds 0.08.
- By the letter of the rule the 3b rule is therefore not adopted on the CRC-24 frame at Q = 6. The fair comparator (flagsrec) pays about as much record recovery (-0.119 against record only), so against it the 3b rule's record cost is only -0.010 and -0.012 at Q = 6.
- This is a decision for the user and the Prof. Re-reading the record clause against the fair comparator instead of the record only would pass, but it would be a change made after seeing these numbers and must be recorded as such, not as a pre-registered rule.

## Phase 1b completed: byte-level recovery and decisions on the CRC-24 frame, both loss models

Code: src/p3v3/bytecheck2.py (real frame3 messages with CRCB = 3, real receiver, then the slot model's own knowledge and decision code on what was decoded); printout results/v3dev_bytecheck2.log; per-day file results/v3dev/bytecheck2_full.csv. 2,598 development days (every fourth), 20 loss draws per day and condition. Slot figures are the all-day levels of results/v3dev_eval_d2.txt (levels, not paired). Wrong decisions: 0 in every row.

| Condition | Design | Record recovered, byte (slot) | Hard cases at alternative thresholds, byte (slot) |
|---|---|---|---|
| Q=6 independent | record only | 0.844 (0.845) | 0.505 (0.523) |
| Q=6 independent | 3b rule | 0.755 (0.715) | 0.773 (0.761) |
| Q=6 Gilbert | record only | 0.781 (0.780) | 0.467 (0.448) |
| Q=6 Gilbert | 3b rule | 0.705 (0.671) | 0.713 (0.670) |
| Q=12 independent | record only | 0.980 (0.980) | 0.608 (0.652) |
| Q=12 independent | 3b rule | 0.952 (0.919) | 0.815 (0.805) |
| Q=12 Gilbert | record only | 0.954 (0.954) | 0.584 (0.611) |
| Q=12 Gilbert | 3b rule | 0.919 (0.889) | 0.801 (0.787) |

Reading:
- Record only: the slot model matches the byte frame within 0.003 on recovery.
- 3b rule: the slot model is pessimistic about recovery by 0.03 to 0.04 (the byte frame packs witnesses more compactly than whole slots); decisions differ by up to 0.04 in either direction, which is within what a 1-in-4 sample of days and unpaired draws can produce.
- Byte-level contrasts (3b rule minus record only): record recovered -0.089, -0.076 (Q=6), -0.028, -0.035 (Q=12); hard cases at alternative thresholds +0.268, +0.246 (Q=6), +0.207, +0.217 (Q=12). The record cost at Q=6 is therefore -0.089 and -0.076 at byte level, still beyond the -0.08 limit in one of two conditions, and the decision gain is slightly larger than in the slot model.
- Consequence for the pre-registration: the agreement limit for the 3b rule in H8 cannot be 0.02 (development gap 0.03 to 0.04). It is set from this development result in docs/CONFIRM4_PLAN_DRAFT.md.
