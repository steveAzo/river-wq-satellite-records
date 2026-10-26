# Record model, definitions, and certificate correctness (revision Step 3; review M3, M7, maths audit)

Code: `src/p3/record.py`. Tests: `tests/test_record.py` (exhaustive over loss patterns). Frame: `docs/FRAME_SPEC.md`.

## 1. Objects

- Channel-day: parameter j of one site on one UTC day, readings x_j(t), t = 0, ..., n_j - 1, on the channel's
  native grid (n_j from the site profile), tolerances delta_j(t) > 0 (USGS TM 1-D3 "excellent", per value).
- Quantiser: code c = q_j(x) on 13 bits; dequantised value x~ = q_j^-1(c). Codes 0 and 8191 flag a reading
  outside the range. Such a reading is censored (Step 9): it is always planned, carried as its flag (x~ is then
  the range end), excluded from E(S), reported by the server as below or above range, and never certified.
- Plan S: the planned values of a record day, (j, s, c), listed in planned order (parameter T, DO, pH, EC; then
  slot) with positions 0, ..., m - 1. Every encoded channel has at least one planned value.
- Reconstruction rule R (identical at encoder and server): from any subset A of S and channel j with received
  slots s_1 < ... < s_k,
  - for t < s_1: x^_j(t; A) = x~(s_1) (self-contained; in chained mode, the line from the anchor at t = -1);
  - for s_i <= t <= s_i+1: the line between x~(s_i) and x~(s_i+1);
  - for t > s_k: x~(s_k).
- Received set A: the planned values recovered by the server from units that passed their CRC.

## 2. Quantities (kept separate, as the review asks)

| Symbol | Name | Definition | Who can evaluate it |
|---|---|---|---|
| E(S) | plan error | max over j, t of abs(x_j(t) - x^_j(t; S)) / delta_j(t) | encoder (exact) |
| b | bound flag | 1 if E(S) <= 1; sent in every segment | encoder, then server |
| E(S, A) | delivered error | as E(S) with x^(.; A); a channel with nothing received counts as failed | oracle only |
| F(S, A) | within tolerance | 1 if E(S, A) <= 1 | oracle only (not verifiable) |
| Fully reconstructed | | A = S | server (Corollary 1) |
| Cert(A) | certified readings | the readings marked by the rule of Section 3 | server, from A only |
| Phi(A) | fully certified | b = 1, the last position lambda is known, and positions 0..lambda are all in A | server |
| G_cert | share of fully certified site-days | E_A[Phi(A)] under a stated loss law | primary result |
| G_ok | share within tolerance | E_A[F(S, A)] | secondary (oracle) |
| c | certified reading share | E_A[abs(Cert(A)) / sum_j n_j] | server-side, averaged |

G_cert and G_ok are probabilities under an assumed stochastic loss model, not deterministic guarantees.
No design guarantees delivery over a one-way erasure channel. The deterministic statement is Proposition 1:
whatever the server certifies is within tolerance. The draft's G was G_ok; it counted days the server
could not have known to be within tolerance.

## 3. Certificate rule (server)

For each received position i with value (j, s):
1. Point: reading (j, s) is certified.
2. Span: if position i + 1 is received and belongs to channel j, the readings s..s' of channel j are certified (s' its slot).
3. Head: position i is known to be the first of channel j if i = 0, or position i - 1 is received and belongs
   to another channel. Then readings 0..s of channel j are certified (chained mode: only if the anchor is known, Section 5).
4. Tail: position i is known to be the last of channel j if i is the day's final position (the segment holding
   it carries last = 1), or position i + 1 is received and belongs to another channel. Then readings s..n_j - 1 are certified.

Nothing is certified when b = 0. The rule uses only A, the bound and last flags, and the site profile (n_j).
It never uses the planned set, which the server does not know.

## 4. Results

Lemma 1 (exact quantisation). The encoder evaluates every candidate span, head, tail, and point error with the
dequantised endpoint values x~ that the server will hold, and the server computes x~ from the same code by
the same arithmetic. Hence E(S) computed by the encoder is the server's error on S, and E(S) <= 1 includes
quantisation; no margin is needed. (The draft's 0.975 margin is withdrawn. A convexity bound on endpoint errors
holds in absolute terms but not relative to a value-dependent tolerance such as 3% of conductance, so the
exact evaluation is preferred.)

Lemma 2 (locality). Let positions i and i + 1 be consecutive in planned order, belong to the same channel j
with slots s < s', and both be in A. Then x^_j(t; A) = x^_j(t; S) for s <= t <= s'.
Proof: R on [s, s'] depends only on the received slots of channel j nearest to t on either side. No planned
slot of channel j lies strictly between s and s' (the positions are consecutive), so none is received, and the
nearest received slots are s and s', exactly as in S. The same argument gives equality on [0, s] when position
i is the first of channel j (the earliest received slot of j is then its earliest planned slot), and on
[s, n_j - 1] when it is the last.

Proposition 1 (soundness of certificates). Assume (a) b = 1; (b) every value in A is a planned value as
transmitted (its unit passed the CRC and contained no undetected error); (c) the block day was unwrapped
correctly (send-to-reception delay below 63 days, node clock within one day of UTC); (d) the site profile
gives the true n_j; and (e) each record day has one plan, fixed when the day is encoded (copies and parity
of it may be sent several times, but never a different plan for the same day). Then every certified reading satisfies abs(x_j(t) - x^_j(t; A)) <= delta_j(t).
(With censored readings, E(S) is taken over the readings that are not censored, and censored readings are never
certified; Lemma 2 is unchanged because a censored reading is a planned value like any other.)
Proof: by Section 3, a certified reading lies in a point, span, head, or tail whose defining positions are in A
and whose channel boundaries are established from A (rules 3 and 4 rely on the planned order: channels are
contiguous and ordered, so a received neighbour of another channel proves the boundary). By Lemma 2, on that
interval x^(t; A) = x^(t; S). Then abs(x - x^(t; A)) = abs(x - x^(t; S)) <= E(S) delta(t) <= delta(t) by (a) and Lemma 1.

Corollary 1 (full certification). Phi(A) = 1 if and only if b = 1 and A = S; then E(S, A) = E(S) <= 1.
Proof: positions are 0..m - 1 and lambda = m - 1, so 0..lambda in A means A = S. Conversely, with A = S every
channel's first and last positions are established by rules 3 and 4, so every reading is certified.

Remark (what is not claimed). An uncertified reading may still be within tolerance (it counts in G_ok), but the
server cannot know. Proposition 1 bounds the reconstruction relative to the sensor record x, not the true river
state; sensor accuracy (calibration, fouling, drift) is outside it. Assumption (b) fails with probability at most
the CRC's undetected-error rate (2^-16 for random corruption; every single- and double-bit error is detected in
the tests); this is a residual risk, not zero.

## 5. Anchors (review M3, E2)

Three head rules were implemented with the same encoder:
- oracle: the head starts from the true previous reading x_j(-1). This was the draft's model. No server holds
  this value: even after a perfect delivery the server holds the previous day's held last value, which may
  differ from x_j(-1) by up to one tolerance. A plan built on x_j(-1) can then violate the tolerance (test
  `test_oracle_anchor_is_not_what_the_server_holds`). The oracle is kept only as a reference for cost.
- chain: the head starts from the previous day's last planned value, dequantised. The encoder knows it exactly.
  The server holds it only if that value arrived and is known to be last. Head certification then also requires
  the previous day's tail certificate (cross-day dependency), and a lost final message of day d breaks day d + 1's
  head (burst across midnight; test `test_lost_anchor_breaks_a_chained_plan`).
- self (adopted): no anchor; the first planned value is held back to midnight. Every record day decodes and
  certifies on its own; buffering and losses do not propagate across days.

The price of self-containment (extra values per day relative to chain and oracle) is measured on 2023 data in
`results/dev/need_modes.csv` (Section 7).

## 6. Analytic check for the coded block (used in Step 5)

For a systematic MDS block with K data units, of which D <= K hold planned values, and Q messages:
Phi = 1 iff at least K messages arrive, or fewer than K arrive but all D value units arrive. Under independent
loss with probability p:
  P_full = sum_{i=K}^{Q} C(Q, i) (1-p)^i p^(Q-i) + [D < K] P(all D value units arrive and fewer than K in total).
Under the Gilbert channel, the same quantity follows from a forward recursion over (state, arrivals). Step 5
compares these with the simulated G_cert for every K and Q.

Implemented exactly in `src/p3/analytic.py` (forward recursions over the hidden channel state; checked against
brute-force enumeration of all arrival masks and against the byte pipeline: `tests/test_analytic.py`).

### Proposition 2 (record-first coding needs no channel knowledge)

Setting: a record day whose self-contained plan at tau = 1 occupies D1 units of frame v1 (every unit holds at
least one planned value), Q transmissions per day, and any erasure process (any joint law of the arrival mask,
including bursts and losses correlated across days). Consider the class of unit-level linear designs: each
transmitted message carries a GF(2^8)-linear combination of the D1 units (plus known constants). This class
contains repetition, the reliable-link design, and systematic MDS codes with any K.

Claim: for every design in the class, P(Phi = 1) <= P(N >= D1), where N is the number of arrivals. The
record-first MDS design (K = D1 data units and Q - D1 parity) attains equality. Hence it maximises the
fully-certified probability simultaneously for every channel, and needs no knowledge of the loss rate or
burst structure. K = D1 changes from day to day and travels in every header.

Proof: Phi = 1 requires every planned position, hence every one of the D1 units (each holds a planned value)
and the bound flag. Within the class, the server receives linear combinations of the D1 unknown units; recovering
all of them requires the received combinations to have rank D1, hence at least D1 arrivals. Any plan at
tau <= 1 with more values occupies at least D1 units, and a plan at tau > 1 has Phi = 0. A systematic MDS code
recovers all K = D1 units from any D1 of its Q messages (Cauchy generator), so its P(Phi = 1) = P(N >= D1).

Scope: the bound is within unit-level linear designs over the same frame; it does not exclude a different
encoding of the record into fewer bits. When D1 > Q, no design in the class can fully certify the day (the
record-first design then falls back to the reliable-link plan, which still yields partial certificates).
Days whose record needs D1 > Q units, and the frame overhead, are what limit G_cert at small Q.

## 7. Measured price of self-contained days (2023)

Source: `results/dev/need_modes.csv` (`src/p3/need_modes.py`, decimal quantiser grid; all 10,978 eligible
2023 site-days, 95% of them preceded by an eligible day, so chaining was possible). Values per site-day at tau = 1:

| Rule | Mean values | Four-parameter median bytes | Four-parameter days in one 23-B message | Step from the previous row |
|---|---|---|---|---|
| Draft (true anchor, empty channels allowed, unquantised) | 7.66 | 18 | 43.6% (at 5 values per message) | |
| Oracle anchor, at least one value per channel, quantised | 9.14 | 24 | 27.3% | +1.48: the draft sent nothing for 39% of channel-days (pH 65%), holding the true previous reading all day |
| Chained anchor (server-held previous value) | 9.64 | 24 | 23.0% | +0.50: the server holds the previous day's held value, not the true reading |
| Self-contained (adopted) | 9.89 | 27 | 20.3% | +0.25: the price of removing every cross-day dependency; zero on 49% of days |

Quantisation costs nothing on these data: on channel-days for which the draft sent values, the quantised
oracle needed exactly the same number (difference 0.000 for T, DO, and pH; -0.001 for EC). With the first,
non-decimal grid (`need_modes_grid_v0.csv`) the self-contained mean was 10.64.

Consequences for the paper:
- The headline cost rises. Four-parameter days need a median of 27 B (9 values) and a 99th percentile of 120 B
  for a self-contained, quantised, certifiable record, against the draft's 18 B. Because 5 values fit a message,
  the median four-parameter day needs 2 messages (p99 8, max 15).
- Self-containment costs 2.6% more values than chaining, which buys independence from cross-day losses.
- The oracle row must not be presented as achievable.

## 8. Tests

`tests/test_record.py`:
- min-# is feasible and minimal against brute force (12 series x 2 head rules x 3 levels, quantised);
- certificates are sound for every loss pattern of 10 random two-channel plans (6 to 12 planned values; up to
  4,095 patterns per plan; tens of thousands of certified readings checked);
- full certification holds if and only if everything arrived;
- the certificate is not vacuous (losses leave uncertified readings outside tolerance);
- unbound days are never certified;
- channel boundaries need the neighbouring position;
- chained heads need a known anchor; a lost anchor breaks a chained plan; the oracle anchor is not what the
  server holds;
- out-of-range readings are never endpoints.
