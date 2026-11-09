# Certificate language for environmental decisions (revision 2, Step 2)

Date: 2026-11-03. Code: `src/p3/certlang.py`. Tests: `tests/test_certlang.py` (80 cases), `tests/test_partial_soundness.py` (20 cases).
Purpose: state exactly what the server may claim about a threshold decision from the bytes it received, and prove that the claim is sound. The language is independent of the codec: every source of information becomes an interval on a reading. Step 3 will choose WHICH information to send; this document fixes what each piece of information is worth.

## 1. Setting and notation

- A channel-day has readings x(0), ..., x(n-1) of one parameter on its native grid. Readings outside the quantiser range are censored: they are carried as flags and are not part of any decision (Section 6 states the consequence).
- The decision domain is the set of uncensored readings. Truth statements below refer to the sensor record, not to the river (the sensor accuracy is outside the language).
- The tolerance is delta(x) = max(a, r |x|) with the constants of Table 1 of the paper (USGS excellent).
- The server holds a Knowledge object: closed intervals [lo(t), hi(t)] for every reading, a set of readings known to be censored, and optional global bounds g_lo and g_hi.
- Knowledge is valid when x(t) is in [lo(t), hi(t)] for every uncensored t, and every global bound holds for every uncensored reading.

## 2. Sources of information

| Source | Interval it gives | Valid when |
|---|---|---|
| Base range | quantiser range of the parameter | the reading is uncensored (by definition of censoring) |
| Kept value with code c | quantiser cell of c | the code was produced by nearest rounding of the reading |
| Certified span | the tolerance interval around the reconstruction (Lemma 1) | the day's bound flag is true and the span's bounding values arrived (Proposition 1 of the frame specification) |
| Minimum witness at slot s | cell of the kept value at s for x(s); every uncensored reading is at least the lower end of that cell | the encoder declared x(s) the minimum of the uncensored readings of the day |
| Maximum witness at slot s | the symmetric statement | as above |

Lemma 1 (tolerance interval, tight). For r < 1 and x >= 0, the set {x : |x - xhat| <= max(a, r x)} is the interval [min(xhat - a, xhat/(1 + r)), max(xhat + a, xhat/(1 - r))].
Proof: the set is the union of {|x - xhat| <= a} and {|x - xhat| <= r x}. Both contain xhat. The first is [xhat - a, xhat + a]. The second, for x >= 0, is xhat/(1 + r) <= x <= xhat/(1 - r). A union of two intervals that share a point is an interval whose endpoints are the extreme endpoints. The test `test_interval_is_the_exact_solution_set` confirms the endpoints and the absence of gaps on a fine grid for all four parameters.

Lemma 2 (cell). The nearest-rounding quantiser maps x to code c only if x is within half a step of the dequantised value: |x - xtilde(c)| <= step/2 on the linear grids, and a factor of 10^(step/2) on the logarithmic grid (specific conductance). Intervals carry a relative slack of 1e-9 so that floating-point error can only widen them.

Remark (kept values). The existing implementation certified a kept reading with the tolerance interval. The cell is much narrower (0 to 0.0025 units for temperature, dissolved oxygen, and pH on decimal data; 0.07% for conductance), so a kept value decides more thresholds than a span value.

## 3. Queries and three-valued answers

An answer is 1 (certainly yes), 0 (certainly no), or -1 (undetermined).

| Query | Definition on the sensor record | Rule |
|---|---|---|
| Exceeds below theta (low DO, low pH) | some uncensored x(t) < theta | 1 if some hi(t) < theta; 0 if every lo(t) >= theta; else -1 |
| Exceeds above theta (high pH) | some uncensored x(t) > theta | 1 if some lo(t) > theta; 0 if every hi(t) <= theta; else -1 |
| Day minimum, maximum | min or max over uncensored readings | minimum in [min lo, min hi]; maximum in [max lo, max hi] |
| Relative change (conductance) | some pair x(t), x(t + h) of uncensored readings with \|x(t + h) - x(t)\| / x(t) > 0.10 | Section 4 |
| Rolling mean of daily maxima (7DADM) | mean of seven consecutive daily maxima above 20 degC | Section 5 |

Here lo and hi are the effective intervals: lo_eff(t) = max(lo(t), g_lo) and hi_eff(t) = min(hi(t), g_hi). A reading with no information has the base range, so it blocks a certain no.

## 4. Conductance change: exact rule

For a pair with intervals [L_a, U_a] and [L_b, U_b], L_a > 0, the ratio x_b / x_a lies in [L_b / U_a, U_b / L_a], and both ends are attained.
- Certain no for the day: for every pair, U_b <= 1.1 L_a and L_b >= 0.9 U_a. The day is the conjunction over pairs of "for all readings, no change", and a universal quantifier distributes over the conjunction, so the pair test is exact.
- Certain yes for the day: no assignment of readings inside their intervals keeps every pair within 10%. For one lag h the pairs form h chains. Along a chain, if x_t is in [a, b] then every x_{t+h} with |x_{t+h} - x_t| <= 0.1 x_t lies in [0.9 a, 1.1 b] (the sets [0.9 x, 1.1 x] overlap continuously, so the union is an interval). Intersecting with the next reading's interval and repeating gives the set of readings reachable under "all pairs within 10%". The day is a certain yes exactly when this set becomes empty on some chain. Censored readings break a chain.
- The rule "some single pair is certainly changed" is sound but incomplete: with x_0 = 100, x_1 in [100, 130], x_2 = 130, every assignment has a change (x_1 <= 110 changes against x_2, x_1 > 110 against x_0), but no single pair is certain. The test `test_pairwise_rule_is_incomplete_but_the_exact_rule_decides` verifies this example, and `test_relative_change_matches_brute_force` compares the exact rule with a dense grid on 60 random boxes (certain yes, certain no, and undetermined all occur).

## 5. Rolling mean with missing days

For seven days with daily-maximum intervals [m_d, M_d], the mean of the maxima lies in [mean m_d, mean M_d]. Answer 1 if the lower mean exceeds the threshold, 0 if the upper mean does not, else -1. A day with no information contributes the base range of the parameter, never zero and never omission. One missing day therefore blocks a certain no (its upper end is the top of the range) but does not block a certain yes when the other six days already force the mean above the threshold (`test_rolling_mean_with_missing_day_is_undetermined_until_bounded`).

## 6. Propositions

Proposition 1 (soundness). If the knowledge is valid, every answer 1 or 0 of every rule in Sections 3 to 5 equals the answer on the sensor record.
Proof: each rule evaluates the query on a set that contains the true record. For the threshold queries, a reading with hi(t) < theta forces x(t) < theta, and every lo(t) >= theta forces every reading to be at least theta. The extremum intervals follow because min over readings is at least min of lower ends and at most the upper end of any reading. The ratio rule is the exact image of the box under the query (Section 4). The rolling mean is monotone in each daily maximum. Censored readings are outside the domain by definition: a reading that is censored but not yet known to the server lies outside its base interval or is excluded, and in both cases is not in the domain of the truth. Exhaustive checks: for every subset of arrived values on small days (including prefixes, as on oversize days), with and without each witness, no interval excluded the truth and no answer was wrong (`test_every_subset_is_valid_and_sound`).

Proposition 2 (exactness on the interval model, WITHOUT witnesses). For the threshold queries and the day extrema, when no witness has arrived, the rule returns an answer other than -1 exactly when the query has the same value on all records consistent with the knowledge, and the extremum bounds are attained.
Proof: for "exists t with x(t) < theta", the largest value of min x over the consistent set is min hi, and its smallest value is min lo; the query is constant exactly in the cases that the rule tests. The ratio rule is exact on the box relaxation (Section 4).
Correction (review, 2026-11-09): with a witness the rules are sound (Proposition 1) but NOT exact. The witness also asserts that some uncensored reading lies inside its cell, and the box model uses only the half-space x(t) >= g_lo. Counterexample: reading 1 in [3, 10], reading 2 in [4.5, 4.6], minimum-witness cell [4.0, 4.01]. Reading 2 cannot be the minimum, so reading 1 lies in [4.0, 4.01] and "some reading above 5" is certainly false; the rule returns -1. The decisions reported in the paper are therefore a lower bound on what the witness could decide (`tests/test_review_fixes.py`).

Proposition 3 (identifiability limit). Let b be the bytes received. If two records consistent with b have different answers to a query, no sound decoder can decide that query from b. The tolerance makes this concrete:
- from a certified span alone, a threshold theta is decidable at a reading only when the reconstruction is farther than the interval half-width from theta (0.2 pH units, 0.2 degC, 3% of conductance, and max(0.3 mg/L, 5%) for dissolved oxygen);
- a reading closer to the threshold than that can be decided only if the value itself is carried (a kept value or witness), because its cell is orders of magnitude narrower.
This is the formal reason why a record within USGS tolerance misses near-threshold pH peaks (docs/ENV_RESULTS.md: 37% missed by the naive reconstruction) and why more bytes spent near the threshold, not everywhere, is the right target for Step 3.

Proposition 4 (truncated days). A day whose record exceeds the quota is a subset of the planned values; its knowledge is valid and the rules are sound, by Proposition 1 and the exhaustive subset test. A parameter with no arrived value has only the base range and decides nothing, unless a witness arrived.

## 7. What a witness is worth (basis for Step 3)

- One minimum witness for dissolved oxygen (a 13-bit code in frame version 2, docs/FRAME_SPEC_V2.md; 24 bits as a kept value in the first prototypes) certifies "no value below 5 mg/L" when the minimum is at least 5.0025 mg/L, whatever else was lost. The record-based rule needs every dissolved-oxygen reading covered (all planned values arrived).
- The same witness certifies "some value below 5" when the minimum is below 4.9975, again without the record.
- A witness cannot decide a threshold inside its cell (about 0.005 units), so the decision band left undecided shrinks from the tolerance width (0.4 units for pH) to the cell width.
- Cost in frame version 2: 13 bits per witness code plus an 8-bit descriptor for a layered group, or free when hosted in spare record bits, against a median record need of 27 bytes. Step 3 asked which witnesses to send per day and where to place them in the erasure code; the mandatory baselines are send-min/max-always, PET-layered, and send-on-delta.

## 8. Limits stated, not hidden

- Truth means the sensor record; sensor calibration, fouling, and drift are outside.
- Witness soundness needs an honest encoder and an uncorrupted unit; the integrity model is Step 6.
- The base range is a validity assumption: a reading outside it is censored and excluded.
- Decisions that need readings of several days (rolling mean) require each day's association to be correct.
- No hardware or satellite trace is involved; all evidence is trace-driven.
