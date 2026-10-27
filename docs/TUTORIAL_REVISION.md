# Guide to the revised Paper 3 (v0.3)

A plain-language guide for the authors. It explains what the revised paper does, what changed after the review, and
where to look. The earlier guide (`docs/TUTORIAL_PAPER3.md`) describes the first-round method and is now out of date.

## 1. The problem in one paragraph

A river sensor measures four things (temperature, conductivity, dissolved oxygen, and pH) every few minutes, which is
hundreds of readings a day. A satellite service in a remote area sells a few messages a day, each with only 23 bytes,
and the node never learns whether a message arrived. The paper shows how to send a version of the day's record that is
guaranteed to stay within the accuracy the USGS demands of an excellent record, and how the receiving server can tell,
from what it received, exactly which readings it can vouch for.

## 2. The four ideas, in order

1. Send the fewest readings that keep the whole day within tolerance. The server draws straight lines between them;
   the encoder picks the points so that every line stays within the tolerance band of every reading in between. A
   typical day needs nine values (27 bytes, two messages) instead of hundreds of readings.
2. Make every day stand on its own. The first value of the day is held back to midnight, so the server never needs
   yesterday's data. (The draft started each day from yesterday's last true reading, which the server never actually
   has; the review was right to object.)
3. Protect the day's record as a whole. If the record needs D messages and the plan allows Q, the node sends the D
   data messages plus Q - D extra "parity" messages from an erasure code. Any D of the Q messages rebuild the record.
   The node does not need to know how often messages get lost; the paper proves this is the best any scheme of this
   kind can do (Proposition 2).
4. Let the server certify what it received. Every value carries its position in the day's list, so the server knows
   exactly what is missing. Between two received neighbouring values, the encoder's guarantee still holds, so those
   readings are certified (Proposition 1). A day with everything received is fully certified.

## 3. What a "certificate" buys an agency

For a rule such as "dissolved oxygen below 5 mg/L", the server can say: certainly yes, certainly no, or undetermined.
The first two are never wrong. Periodic readings or tag-style summaries can only guess. The record catches short
conductivity pulses that periodic readings miss. Its weakness: it cannot resolve details smaller than the tolerance,
such as a pH peak of 9.1 against a limit of 9.0 with a tolerance of 0.2.

## 4. How the evidence was produced

- Development: 39 USGS rivers, 2023. Everything was designed and tuned here.
- Freeze: the software, the eight hypotheses, and their thresholds were committed and tagged (confirm2-freeze), and
  the freeze record was committed before any new data were opened.
- Confirmation: 36 new USGS rivers in five regions not used before, 2024, chosen from site information only and sealed
  with checksums until the freeze.
- Every message was built as real bytes, lost at random (independent or bursty loss), decoded, and certified. For the
  proposed design, exact probabilities replaced simulation, and they agree with the byte-level simulation.

## 5. The results that matter

| Question | Answer (confirmation sites) |
|---|---|
| Cost of a day's record | Median 27 bytes, two messages |
| Days fully certified, 6 messages per day, 30% loss | 0.900 (repetition 0.799; fixed code 0.786; tag practice 0.030) |
| Same with 12 messages per day | 0.987 (independent loss), 0.966 (bursty loss) |
| Does buffering across days help? | No (development data) |
| Can a 28-day pilot choose the plan? | Yes for 83% of pilots; winter pilots underestimate summer |
| Hypotheses supported | Six of eight |

The two that failed:
- C1: the record cost 27 bytes as predicted, but its interval reached 33 bytes, above the 30-byte threshold.
- C2: at an extreme corruption level, one corrupted message slipped through the 16-bit integrity check after the
  receiver had tried several combinations, and 96 readings were certified wrongly. After the confirmation, the
  receiver was changed to double-check any decoding that needed retries; this removed the problem in an exploratory
  re-run at a small cost. Both failures are reported openly in the paper.

## 6. Where to find things

- The paper: `draft/deliverables/Paper3_draft_v0.3.pdf` (and `.docx`, supplement, highlights).
- What changed and why, item by item: `docs/RESPONSE_TO_REVIEW.md`.
- The full working record: `docs/REVISION_PLAN.md` and the `docs/*_RESULTS.md` files it links.
- How to rerun everything: `README.md`.
