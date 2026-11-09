# Message frame specification, version 2 (revision 2, Step 6 design)

Date: 2026-11-06. Status: DESIGN with a verified bit budget (`src/p3/capacity.py`, `tests/test_capacity.py`). The byte-level codec (`frame2.py`), golden vectors, and the corruption experiment are still to be written (Step 6b). Everything in the prototypes (Steps 3 to 4) used the slot model; Section 4 shows that frame v2 is never worse than that model at equal protection.

## 1. Why a second version

- Review items 5.1 and 5.6 ask for an end-to-end audit of integrity and for the real bytes that carry decision witnesses.
- Root cause of the failed hypothesis C2: in version 1 the CRC-16 is inside each erasure-coded data unit, so a parity message is never checked on its own. The server rebuilds a unit from parity, then tests the unit's CRC; every retry over another combination of parity messages is another 2^-16 chance for a corrupted message to pass. The post-confirmation rule B (corroborate retried decodings) removed the false certificates but is a patch (docs/POSTHOC_C2.md).
- Witnesses need a second section in each message. With a CRC per unit, each section would carry its own check and header. A single check per transmitted message avoids this and removes the retry problem by construction.

## 2. Layout

Message = header (3 bytes, not erasure-coded) + body (20 bytes = 160 bits), as the KIM1 user payload of 23 bytes.

| Part | Bits | Content |
|---|---|---|
| Header | 2 | version = 2 |
| | 6 | block day modulo 64 (unwrapped from the operator's reception time as in version 1) |
| | 7 | message index i (0 to K-1 data, K to Q-1 parity) |
| | 7 | K, record data units |
| | 1 | coded flag |
| | 1 | witness-group flag (1: a descriptor and a witness symbol follow the CRC) |
| Body | 16 | CRC-16/CCITT-FALSE over the header and the rest of the body, of every transmitted message (data or parity) |
| | 8 | witness descriptor, only if the flag is set: k_w (3 bits, 1 to 6 data units) and presence mask (5 bits: DO minimum, pH minimum, pH maximum, T maximum, conductance rate pair) |
| | 8 x s_w | witness symbol, s_w = ceil(ceil(13 x codes / k_w) / 8) bytes; codes = number of 13-bit codes in mask order (the rate pair has two) |
| | rest | record symbol (a whole number of bytes), one Reed-Solomon symbol of the record data units |

Record data unit (before coding): segment count (2 bits), up to three segments as in version 1 (21-bit header, 24-bit values), a hosted-witness flag (1 bit) followed, when set, by a 5-bit presence mask and 13-bit codes, and zero padding. Without witnesses the unit has 144 bits, which is exactly 2 + 21 + 1 + 5 x 24 = 144: the record-only capacity of five values per message is unchanged.
Witness data unit j: bits j x 8 s_w ... of the concatenated 13-bit codes. Message i < k_w carries witness data unit i; i >= k_w carries the Reed-Solomon (GF(2^8)) parity of the k_w witness units. Both codes are over the same Q messages, so every recovery event is a threshold on the number N of accepted messages.
A witness is the quantised extremum only (13-bit code of the parameter's grid). Its slot is not carried because no decision rule uses it (certlang `add_*_witness_value`; for the opposite side the slotted witness gave one extra pinned reading, which no design asks for; tests/test_certlang.py).

## 3. Receiver rules

1. Accept a message only if its CRC passes. Duplicates (same index and block) are dropped; a block is identified by (site from the operator, unwrapped block day, K, k_w).
2. Decode the record from any K accepted messages and the witness group from any k_w accepted messages. With CRC on every message there is no retry over parity combinations.
3. Corroboration when more messages arrive than are needed: re-encode the decoded units and compare with every other accepted message. Any mismatch means an accepted message is corrupt; the block's record (or witness group) is then rejected and nothing is certified from it. Witness groups with k_w = 1 are copies: all accepted copies must agree.
4. Hosted witnesses are part of the record data unit and are covered by rules 2 and 3 with it.
5. Certificates are produced by the rules of `docs/CERTIFICATE_SPEC.md` from accepted, corroborated content only.

## 4. Bit budget (src/p3/capacity.py)

- Record only: 5 values per message.
- One DO witness, k_w = 1: 8 + 16 bits per message; record 4 values per message.
- Four witness objects with k_w = 2: 8 + 40 bits; record 3 values per message.
- At the same protection (the dimension k that the slot model gives each group) the frame v2 record capacity is at least the slot model's for all 15 subsets of the four witness objects (test `test_frame_v2_never_holds_fewer_record_values_than_the_slot_model_at_equal_protection`); it is larger for the three-object subsets with five or six slot-model values (for example all four objects: 3 against 2 values). The prototype results are therefore conservative with respect to bytes.
- Decision flags (8 bits per message): record 4 values per message (floor), not the 4.75 used in the running Step 4 run; that run favours the flags design.
- A CRC-32 instead of the CRC-16 would cost 16 more bits per message and leave 4 values per message: one value per message, about 20% of the record capacity.

## 5. Threat model

| Threat | Mechanism in the frame | Residual |
|---|---|---|
| Random bit errors, bursts | CRC-16 per message; corroboration when N > K | A corrupted message passes with probability about 2^-16; a false certificate then needs that message to be used with no corroborating message (N = K exactly, or k_w copies without a second agreeing copy) |
| Corrupted header (index, K, k_w, day) | Header covered by the CRC | As above |
| Duplicates, reordering | Index in the header; duplicates dropped; decoding is order-free | None |
| Stale or misassociated block | Day modulo 64 unwrapped with reception time; K and day in the CRC; device identity from the operator | Operator error is out of scope |
| Sensor glitches | Out-of-range readings are censored and excluded; witnesses are over uncensored readings only | In-range glitches are the sensor's, not the telemetry's (outside the bound) |
| Dishonest encoder or tampering | None: a witness or a flag rests on the node's honesty | Out of scope; a MAC would cost 16 bits per message, the same as the CRC |
| Clock error over half a slot | Not a frame property | Outside the reconstruction bound (Step 9) |

Soundness claim to be stated (not an unconditional guarantee): decisions are sound under correct, corroborated messages, an honest encoder, the site profile (including the reporting resolution when assumption R is used), and the quantiser range; the probability of a false certificate under random corruption is bounded by the CRC false-accept rate times the probability of an uncorroborated use, which Step 6b measures with a byte-level corruption experiment on development and then new data.

## 6. Still to do (Step 6b)

- `frame2.py`: encode and decode of the layout above, golden byte vectors, tests (round trip for every design, header corruption, truncation, duplicates).
- Corruption experiment E5: bit error rates 1e-4 to 1e-2, 10% of messages hit, header corruption, stale blocks, duplicates; wrong-certificate counts with denominators; version 1 (frozen failure, rule B) against version 2 (CRC per message, with and without corroboration); byte and capacity cost.
- The frozen C2 failure and the post-confirmation rule stay reported as they are.
