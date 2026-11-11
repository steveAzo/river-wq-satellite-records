# Paper 3: scoping analysis (proposal 3, "channel-aware priority queuing over congested IoT gateways")

**Status:** scoping, third pass, 2026-10-16. The Prof accepted scope A2 "if we stand a chance at the top journal". The third pass (§T below) changes the *framing* he approved, on new evidence, and needs his confirmation. The second-pass text from §0 onward is kept as the record.

---

## §F. Fourth pass (2026-10-23): the closest prior art read; honest novelty verdict

### F.1 What the round-3 papers showed
- **Deligiannakis, Kotidis & Roussopoulos, VLDB J. 16:439–461 (2007; online 2006), "Dissemination of compressed historical information in sensor networks"** (`papers/pdf/s00778-005-0173-5.pdf`). It already contains the core of scope A2:
  - **Budget-first compression of buffered history:** "the sensor nodes wait till enough data has been gathered and only then is the data compressed"; SBR minimises a chosen error metric "given a target bandwidth constraint", where the bandwidth includes retransmissions.
  - **Maximum absolute error:** a Chebyshev-regression variant (Section 4.6), with an explicit "strict error bounds" mode.
  - **Pooled allocation across nodes:** a group leader shares a total bandwidth B among the members of its cluster. "Uniform allocation of bandwidth among the sensors will be sub-optimal", so it "continuously allocates to the node with the largest error additional bandwidth" (Section 5.2). That is our water-level idea, as a heuristic, published 2006.
- **EDBT 2004 chapter** (`b95855.pdf`, LNCS 2992, pp. 658–675): precision-first redistribution of error thresholds in aggregation trees (the Olston line). It adds no new threat.
- **Biologging satellite telemetry** (new search, 2026-10-23): Boehme et al., Ocean Sci. 2009 [84]; Photopoulou et al., Animal Biotelemetry 2015 [85]; validation [87]; Fedak et al. 2001/2002 (manual). Animal-borne CTD loggers use one-way Argos ("no handshake"), messages of at most 256 bits, broken-stick piecewise-linear compression with a fixed point count, and a transmission buffer with pseudo-random scheduling and duplicates. One-way, quota-limited record delivery therefore has a long-standing (heuristic) practice.

### F.2 E13 and E13b: one-way loss on a 6 × 19 B/day satellite plan (USGS-Excellent, 100 test site-days)
P(whole day within tolerance):

| Loss p | Loss-oblivious optimum (A2/SBR-style) | Value-aware layering (mine) | Tuned repetition | MDS code across messages |
|---|---|---|---|---|
| 0.1 | 0.70 | 0.84 | 0.92 (r = 2) | **0.94** (K = 4) |
| 0.3 | 0.37 | 0.70 | 0.80 (r = 3) | **0.88** (K = 3) |
| 0.5 | 0.21 | 0.53 | 0.67 (r = 3) | **0.75** (K = 2) |

- **Reading:** designs for reliable links collapse on a one-way link, which is a real point. But blind repetition is a strong practice baseline, my value-aware layering loses to it, and a textbook erasure code adds only +2 to +9 points.
- Scripts: `e13_oneway_loss.py`, `e13b_mds.py`.

### F.3 Verdict
Every mechanism scope A2/A3 relies on now has a precedent:

| Mechanism | Precedent |
|---|---|
| Priority by class | Crowded |
| Progressive order | HIRE |
| Value order | Strong data-blind baseline |
| Optimal per-node L∞ | Imai–Iri; Soroush |
| Budget-first pooled allocation toward the largest error | **SBR, VLDB J. 2006** |
| One-way tiny-message record delivery | **SRDL biologging practice** |
| Protection against loss | Repetition and erasure codes (textbook) |

**What remains unoccupied:** the integrated question for *environmental compliance monitoring over byte-priced satellite IoT*, namely what a regulatory-grade (USGS-Excellent) record costs and how to deliver it with a guarantee, together with its evidence:
- E11: median 36 B/day (3% of raw), p99 288;
- E12: six 19-B messages a day suffice at 38 of 39 rivers with a buffer;
- E13/E13b: under one-way loss the right design roughly doubles to quadruples the guarantee rate over a reliable-link design.

This is systems and application novelty with strong real-data evidence, **not** algorithmic novelty.

**Honest odds:** at IEEE IoT-J a reviewer who knows SBR, PET-style coding or SRDL practice will call the method incremental. The submission would rest on the setting, the guarantee semantics and the evidence. Realistic acceptance odds are modest, not good; a fair estimate is clearly below even. At a Q1 environmental-informatics journal (e.g. Environmental Modelling & Software), the same content answers a question practitioners actually have, and the odds are better.

---

## §T. Third pass (2026-10-16, after the Prof's decisions, round-2 reading, and E11–E12)

### T.1 Decisions recorded (user, 2026-10-16)
1. **Scope A2:** accepted, on condition that it can compete at IEEE IoT-J.
2. **Framing:** "go with the recommendation" (then: LoRaWAN plus outage recovery). **The evidence below argues for changing it**; to confirm.
3. **Papers 1 and 2 must not be cited** (just submitted). Consequences:
   - Tolerances: Paper 1's L2 is replaced by **USGS TM 1-D3 "Excellent"** (Wagner et al. 2006, Table 18): T ±0.2 °C, SC ±3%, DO ±0.3 mg/L or ±5% (whichever is greater), pH ±0.2. The PDF is in `papers/standards/`.
   - Event detection is defined from Page (1954) CUSUM, not Paper 1's detector.
   - Outage records are used only as inputs, citing the original datasets; Paper 2's findings (two regimes and so on) must not be re-presented.
4. **No lab deployment:** the evaluation is trace-driven. On-device cost comes from Imai–Iri's O(n) min-# plus an MCU cost estimate (optionally run on an emulator).

### T.2 E11–E12 change the framing
**E11** (`e11_need_distribution.py`, 10,977 site-days, USGS-Excellent): the exact bytes a site-day needs for a fully guaranteed record (min-# at τ = 1, 3 B/value), scaled to a 10-minute, 4-parameter node:

| Median | p90 | p99 | Max | Raw data |
|---|---|---|---|---|
| **36 B/day** (3.1% of raw) | 108 | 288 | 594 | 1,296 B/day |

- **The TTN budget is never the limit for a node that sends the right bytes:** even SF12 (510 B/day) exceeds the need on essentially every site-day. **The LoRaWAN-plus-outage framing therefore collapses** (a reviewer would say "just compress"). LoRaWAN becomes a negative control.
- Per-site median need ranges from 0 to 198 B/day; p99/median within a site is 2.7. High-need days co-occur within a chain only on Illinois (2.1× chance) and Klamath (2.5×); elsewhere at or below chance. Pooling across nodes has room.

**Satellite micro-plans are where budgets truly bind.** Kinéis, the constellation of E4 (service pages dated 2024; **to verify**), uses 19-byte messages, with plans of 1, 6 or 24 messages a day (maximum 96).

**E12** (`e12_time_pooling.py`): a daily backlog queue on the E11 need:

| Plan | Days over budget (no buffer) | With a buffer: sites whose long-run need exceeds the plan | Median share of days with backlog | Longest wait (median / max) |
|---|---|---|---|---|
| 1 msg/day (19 B) | 0.69 | **33/39** (τ must be relaxed) | 0.98 | 242 / 360 d |
| **6 msg/day (114 B)** | 0.086 | **1/39** | 0.005 | 1 / 360 d |
| 12 msg/day (228 B) | 0.022 | 0/39 | 0.000 | 0 / 98 d |
| 24 msg/day (456 B) | 0.001 | 0/39 | 0.000 | 0 / 5 d |

**Headline candidate:** *six 19-byte satellite messages a day are enough for a USGS-Excellent record on 38 of 39 rivers, if the node sends the right bytes.* Raw periodic reporting needs 1,296 B/day, about 68 messages, more than the Hourly tier. Data-blind orders do not keep the worst case even at 3× the bytes (E5a-usgs: at 10% of raw, whole day within tolerance on 92% of site-days with value-aware selection vs 35% for the best data-blind order).

USGS-Excellent re-runs of E5–E7c (outputs with suffix `_usgs`):
- **Within a node, at 10% / 5%:** whole day within tolerance 0.92 / 0.53 (value order) vs 0.35 / 0.12 (stride_nf).
- **Chain pools at 10%:** whole pool within tolerance 0.93 (pooled greedy) / 0.69 (equal greedy) / 0.12 (equal data-blind).
- **Exact optimum (E7c-usgs) at 10%:** 0.97 (pooled common-τ) vs 0.92 (equal shares, each optimal); the nested-greedy price stays at 1.34×.
- **The pooling gain is larger at tighter budgets**: 31-site pools at 5%: worst error 1.06 vs 3.6× tolerance.

### T.3 Revised recommendation: lead with satellite IoT micro-plans; LoRaWAN as the control
**Framing:** byte-budgeted, store-and-forward telemetry for remote rivers that only satellite IoT reaches (e.g. Ghana's galamsey-affected Pra/Offin/Ankobra). The budget is a priced message quota. The link is uplink-dominant with little or no feedback, so the node cannot know which messages arrived.

**Contributions (refined):**
1. **The cost of a guaranteed record:** the first quantification of the bytes a river site needs to keep a USGS-Excellent record, and how it varies across 39 sites and a year (E11). A design table per satellite plan tier (E12).
2. **Budget-first min-max allocation over nodes and time:** common-τ min-# is exact for a known budget (water-level proposition). The buffer extends the water level across days, which is temporal pooling under a delay bound. A gateway with one satellite modem pools across its local nodes. For plans too small for τ = 1 (1 msg/day), choose the smallest feasible τ.
3. **One-way-link robustness:** with no ACKs, silent loss and repetitions (Kinéis repeats messages) break the node's mirror of the server. Design a value-aware redundancy rule, and measure the price of nestedness (about 1.35–1.4×) when delivery is uncertain.
4. **Negative control and honest limits:** on LoRaWAN, budgets do not bind for smart senders. Data-blind orders are fine on average but fail the worst case.
5. **Trace-driven evaluation:** 39 USGS sites (6 chains), InWaterSense (noisy counter-case), Weija; real satellite contact windows (E4); plan tiers; injected events; energy per message from module datasheets.

**Positioning:** see `papers/LITERATURE_NOTES.md`. In short:
- Olston 2003 and GAMPS 2009 own "non-uniform error allocation" and "common L∞ across signals" in the *precision-first* direction; Imai–Iri and Soroush own per-node optimality.
- **Our claim is the budget-first, record-oriented problem on byte-priced, feedback-poor IoT links, its exact one-number solution, and the evidence and design rules.**
- **Deligiannakis et al. (SIGMOD 2004; VLDB J. 2006) must be read before the claim is final.** It may already do budget-first compression of buffered history per node, and possibly allocation across nodes.

### T.4 Honest chance assessment for IEEE IoT-J
- **For:** a timely setting (satellite IoT and NTN); a concrete, cost-anchored finding ("6 × 19 B/day"); an exact, simple, implementable rule with a provable core; large real-data evidence (about 11,000 site-days, 39 sites, 6 chains, plus two low-cost deployments); careful negative results. IoT-J regularly publishes trace-driven protocol papers of this shape.
- **Against:**
  - The algorithmic components are known (min-#, non-uniform allocation), so reviewers may call the method simple.
  - No hardware or deployment.
  - A single domain (rivers).
  - Satellite plan facts come from vendor pages.
  - Deligiannakis may pre-empt part of the claim.
- **What raises the odds most:**
  1. Reading Deligiannakis and positioning precisely.
  2. The one-way-link robustness study (contribution 3): the part with no database precedent and the most "IoT".
  3. Temporal pooling with delay bounds.
  4. A second domain for generality (e.g. a public air-quality or soil-moisture network), optional.
  5. An MCU cost estimate.
- **Assessment:** a credible IoT-J submission if items 1–3 come through. It is not a sure accept; no honest scoping can promise that.

### T.5 Next steps
1. **The user/Prof:** confirm the satellite-first framing (T.3); provide Deligiannakis 2004 (correct DOI 10.1145/1007568.1007628) and the VLDB J. 2006 version (`papers/MANUAL_DOWNLOAD.md`, round 3).
2. Verify Kinéis plan terms (message size, tiers, repetitions, downlink availability) and one other provider (e.g. Myriota or Astrocast).
3. Write and freeze the pre-registered evaluation plan (replacing `docs/E9_PLAN_DRAFT.md`): satellite tiers × pools × one-way loss, plus the LoRaWAN control.
4. Only then implement.

---
**Starting point:** `../proposals.md` §3, *"A Channel-Aware Priority-Queuing Framework for Multi-Parameter Telemetry Streaming over Congested IoT Gateways"*.
**Target venue:** IEEE Internet of Things Journal (Q1; the user, 2026-10-16). Papers 1 and 2 went to IJDSN (Q2).
**Rules:** the title is a statement, not a question; top novelty comes first, so scoping gets more time than implementation.

> **History.** The first pass (same day) recommended "anytime" value-ordered upload within one node. The second pass found two things.
> - **Prior art for the encoding:** HIRE (PACMMOD 2023) already gives a layered, progressive time-series encoding with a max-error bound per layer, so the encoding cannot be the novelty.
> - **A strong baseline that closes most of the gap:** a data-blind order, newest slot first and then progressive (`stride_nf`), comes within 1–4 points of value ordering on *average* fidelity.
>
> The scope is therefore re-centred on what the evidence says data-awareness really buys: **the worst case of the record, and allocation across the nodes that share one scarce uplink** (§2.4–2.6). The first-pass text is superseded where it conflicts.

---

## 0. Bottom line

1. **Proposal 3's premises fail as written** (§1):
   - there is no congestion at a water-quality node;
   - InWaterSense records no channel state;
   - a fixed parameter-class priority (temperature "stable", DO "volatile") is rejected by the data (E1).
2. **Its instinct survives in a sharper form.** Several nodes sit behind one gateway or uplink whose capacity is fixed by regulation or by a plan, not by congestion. That capacity is scarce in three measured situations (§3):
   - edge-of-coverage LoRaWAN (TTN fair use at SF11–12 allows only 39–75% of a 4-parameter, 10-minute node's data);
   - **draining the backlog after an outage** (Paper 2's heavy-tailed outages push the share of the backlog that can be sent to about 0.2);
   - gateways with a satellite or quota-limited backhaul.
3. **What data-awareness really buys is the worst case, not the average** (E2b, E5, E6). With 10% of a day's bytes:
   - **Average fidelity:** the best data-blind order and value ordering keep 94% and 97% of values within tolerance.
   - **Guaranteed record within one node:** the whole day's record is within tolerance on **69%** of site-days with value ordering vs **15%** with the best data-blind order (34% vs 93% at 20%).
   - **Within real river chains of 2–5 sites sharing one budget:** a **pooled "water-level" rule** keeps the entire pool within tolerance on **66%** of chain-days, vs **28%** with equal shares and value ordering, and **2.5%** with equal shares and data-blind order (93% / 79% / 6% at 20%).
   - **Exact optimum (E7c):** the pooled optimum is **"common-τ min-#"**: every node sends its fewest-values set that keeps its whole record within τ × tolerance, with τ set to fit the budget. It keeps the whole pool within tolerance on **85%** of chain-days at 10% (**100%** at 20%). A single broadcast number τ implements it.
   - **Nesting has a price:** nested ("anytime") orders, greedy or bottom-up, are about **1.4×** worse in worst-case error than the per-budget optimum (E7, E7b). Design rule: send the optimal set when the budget is known (TTN daily airtime, a planned post-outage drain), and a nested order only when truncation is unpredictable.
4. **The gap (§4).** Every neighbouring literature solves a different problem:
   - AoI/VoI and goal-oriented access keep only the latest sample of a synthetic process;
   - bulk LoRaWAN collection (FREE, IoT-J 2020) delivers all bytes, content-blind;
   - progressive encodings (HIRE) are data-blind storage formats;
   - precision allocation in sensor databases (Olston 2003; Deligiannakis 2004; PRESTO) minimises communication for a *given* precision, on causal streams or on-demand pulls.

   **The budget-first dual, the smallest achievable worst-case error of the buffered record across nodes under a regulated, scarce uplink, is open**, and it is the case that remote environmental IoT actually faces.
5. **Recommended scope (§5):** budget-first, min-max scheduling of buffered multi-parameter telemetry over scarce shared uplinks. The optimum is common-τ min-#, a provable water-level rule needing one broadcast number. A nested fallback covers uncertain truncation. Outage recovery is the main stress case.
   - **The per-node algorithm is not new** (Imai–Iri; Soroush et al., MobiHoc 2008). **Novelty rests on:**
     - the formulation (regulated budget, buffered record, network-wide worst case);
     - the exact pooled rule and its one-number protocol;
     - the price-of-nestedness design rule;
     - evidence that every standard practice misses the guarantee by large factors on real data.
   - Working titles in §6; checks still open before freezing in §7.

---

## 1. Premise audit of proposal 3 (unchanged from the first pass)

| Premise | Evidence | Source |
|---|---|---|
| Severe congestion at the node's cellular backhaul | ~100 B per 10 min over GPRS: utilisation ~10⁻⁵. Real losses are outages (Paper 2), not congestion. | `data/clean/inws_cycles.csv`; Ahmedi 2022 |
| "Channel-aware" | InWaterSense has no channel fields. UVA LoRaWAN has RSSI/SNR but is 99.9% SF7. | raw files; UVA parquet |
| Temperature stable, DO volatile, so a fixed class priority works | **Rejected (E1):** T produces more news than DO in 54% of site-months; the leader changes month to month at 36 of 39 sites; 5.6× swings within a site | `src/scoping/e1_class_priority.py` |
| Buffer low priority, dedicate capacity to anomalies | Sound in spirit; needs a principled rule (this document) | §2 |
| Background papers | Do not exist (OpenAlex) | Paper 2 title check |

What survives is proposal 3's *setting*: **multi-parameter telemetry over congested (scarce) IoT gateways**. InWaterSense and Weija both have several sensing nodes behind one gateway with one cellular backhaul (Ahmedi 2022; Adu-Manu et al. 2020 [65]: Libelium Waspmote → Meshlium → 3G/GPRS).

---

## 2. Experiments (all on 39 USGS sites, 2023, plus InWaterSense; Paper 1 L2 tolerances)

Common setting (E2, E5–E7):
- A node holds a 24 h backlog (6 h also tested) of all its parameters.
- The uplink delivers a byte budget equal to a fraction f of the full backlog.
- The server interpolates between delivered values and holds the last one.
- "Within tolerance" means |error| ≤ the L2 tolerance.
- Data-aware orders pay 3 B per value (value + index); data-blind orders pay 2 B.

### 2.1 E1: a fixed class priority is wrong
See §1. Script `e1_class_priority.py`; output `results/scoping/e1_sod_rates.csv`.

### 2.2 E2 / E2b: order matters, and the strongest data-blind order nearly matches on average
Median over 39 USGS sites, 24 h backlog. Each cell gives **record** (share of all values within tolerance) | **status** (newest value within tolerance):

| f | FIFO | Newest-first (AoI-optimal) | Class (proposal 3) | Progressive (stride) | **Newest + progressive (stride_nf)** | Value order (greedy) |
|---|---|---|---|---|---|---|
| 5% | 0.60 \| 0.53 | 0.69 \| 1.00 | 0.70 \| 0.67 | 0.86 \| 0.59 | 0.85 \| 1.00 | 0.88 \| 0.89 |
| 10% | 0.62 \| 0.53 | 0.70 \| 1.00 | 0.70 \| 0.67 | 0.93 \| 0.67 | **0.94 \| 1.00** | 0.97 \| 0.97 |
| 20% | 0.66 \| 0.49 | 0.73 \| 1.00 | 0.71 \| 0.67 | 0.97 \| 0.81 | 0.98 \| 1.00 | 1.00 \| 1.00 |

**Reading:**
- FIFO (what store-and-forward and bulk collection do), newest-first (what AoI theory prescribes) and class priority (proposal 3) all lose 25–35 points of the record.
- A progressive order fixes the record, and putting the newest slot first fixes the status.
- **On average fidelity, value ordering adds only 1–4 points** over `stride_nf` (it wins at 74–100% of sites; mean error is 1.1–1.3× lower at f ≤ 20%).
- This rules out "value ordering improves average fidelity" as a headline.
- InWaterSense (noisy): the same ordering; greedy and stride tie at small budgets.

Scripts and outputs: `e2_upload_order.py`; `results/scoping/e2_upload_order_W{24,6}.csv`, `e2_W24.log`, `e2_W6.log`.

### 2.3 Lemma (status is bounded by the record)
The newest value is part of the record. Any order that drives the record's **maximum** error below ε therefore also has status error ≤ ε. A worst-case objective covers status automatically; an average objective does not (that is why plain `stride` failed status).

### 2.4 E5a: within one node, data-awareness buys the worst case
Median over 39 sites of the share of site-days whose **whole record** is within tolerance, with the median daily maximum error in tolerance units in brackets:

| f | stride_nf (best data-blind) | **Value order** |
|---|---|---|
| 5% | 0.03 (2.97) | **0.21** (1.53) |
| 10% | 0.15 (1.84) | **0.69** (0.92) |
| 20% | 0.34 (1.17) | **0.93** (0.50) |

Script `e5_worstcase_pooled.py`; output `results/scoping/e5a_worstcase.csv`.

### 2.5 E5b and E6: across nodes, pooling the budget by need buys the network-wide worst case
**Schemes:**
- **equal shares:** each node gets F/N bytes, with data-blind (`stride_nf`) or value order;
- **pooled:** one greedy across all nodes' buffered values.

Pooled greedy is equivalent to a **common threshold τ**: every node sends all values whose normalised error exceeds τ, with τ set so the total fills the budget.

**E5b, about 31 sites per day from five states (364 days).** Mean over days:

| f | Network worst error, equal data-blind / equal value / **pooled** | Site-days fully within tolerance |
|---|---|---|
| 10% | 14.1 / 3.2 / **1.06** × tolerance | 0.26 / 0.65 / 0.73 |
| 20% | 11.1 / 1.7 / **0.57** | 0.38 / 0.89 / **1.00** |

**E6, realistic gateway pools: one river chain of 2–5 sites** (6 chains, about 360 days each):

| f | Pool fully within tolerance: equal data-blind / equal value / **pooled** | Median pool worst error per chain (pooled) |
|---|---|---|
| 5% | – | mean pool max 7.3 / 3.3 / **1.9** |
| 10% | 0.025 / 0.28 / **0.66** | 0.87–1.01 × tolerance in every chain (equal value: 0.98–1.92) |
| 20% | 0.06 / 0.79 / **0.93** | – |

**Reading:**
- Pooling pays even in small, same-river pools, though less than across five states.
- The min-max objective lowers the worst node. At very small budgets (5%) it can leave *more* nodes slightly over tolerance than equal shares do (E5b: 0.18 vs 0.34 fully clean). The objective must be stated as min-max, and that trade-off reported.

Scripts: `e5_worstcase_pooled.py`, `e6_pooled_chains.py`; outputs `results/scoping/e5b_pooled.csv`, `e6_pooled_chains.csv`, `e6.log`.

### 2.6 E7, E7b, E7c: nested orders vs the exact optimum; the pooled optimum is "common-τ min-#"

**E7 (300 random site-days):** greedy vs the exact per-budget optimum of the worst-case record error. The optimum is a min-ε polygonal approximation, computed by dynamic program plus binary search.

| f | Optimum: median worst error / whole day within tolerance | Greedy | Greedy/optimum (median, p90) |
|---|---|---|---|
| 5% | 1.00 / 0.50 | 1.50 / 0.30 | 1.44, 1.83 |
| 10% | 0.66 / 0.78 | 0.96 / 0.60 | 1.43, 1.76 |
| 20% | 0.38 / 0.93 | 0.51 / 0.87 | 1.40, 1.72 |

**Greedy's worst-error curve is non-monotone in 294/300 site-days.** The median largest single-step rise is 0.91 tolerance units, driven by quantisation: pH is reported in steps of 0.1, which equals its L2 tolerance.

**E7b (same sample):** a bottom-up nested order (remove the least harmful value first; upload in reverse) is no better. It is 1.43× the optimum at 10%, still non-monotone (98.7%), with smaller rises (median 0.36). **Nesting itself costs about 1.4× in worst-case error** (the "price of nestedness"), whichever nested heuristic is used.

**Consequence for the design:**
- The per-node optimum curve ε*_n(k) *is* non-increasing in k, so the water-level argument (§2.9) holds exactly on optimal curves.
- The pooled min-max optimum is therefore **common-τ min-#**: every node sends its fewest-values set that keeps its whole record within τ × tolerance, and τ is the smallest value at which the pool fits the budget. One broadcast number suffices.
- **A known budget calls for the optimal set; uncertain truncation calls for a nested order, at a price of about 1.4×.** TTN daily airtime and a planned post-outage drain are known budgets.

**E7c (60 random chain-days, pools of 2–5 sites on one river):** share of chain-days with the whole pool within tolerance, with the median pool worst error in brackets:

| f | **Common-τ min-# (pooled optimum)** | Equal shares, each node optimal | Pooled nested greedy (E6) | Equal shares, data-blind (E6, all days) |
|---|---|---|---|---|
| 10% | **0.85 (0.65)** | 0.70 (0.91) | 0.63 (0.92) | 0.025 |
| 20% | **1.00 (0.33)** | 0.90 (0.50) | 0.90 (0.47) | 0.06 |

Pooling and optimal per-node sets each contribute about equally, and together they take the network-wide guarantee from about 0.03 (data-blind equal shares, close to practice) to 0.85 at 10% of the bytes.

Scripts `e7_greedy_vs_optimal.py`, `e7b_bottomup_order.py`, `e7c_pooled_optimal.py`; outputs in `results/scoping/` (`e7*.csv`, `e7.log`, `e7c.log`).

**Prior art for the per-node component:** optimal minimum-segment line approximation with an L∞ bound is classical (Imai & Iri 1988) and has optimal online versions for sensor streams (Soroush, Wu & Pei, MobiHoc 2008 [81]). GAMPS (SIGMOD 2009) compresses many sensor series under one L∞ bound. The per-node algorithm is therefore **not** our novelty. The novelty is the budget-first pooled formulation, its one-number protocol, and the regime and evidence around them.

### 2.9 Water-level proposition (to prove properly in the paper)
- **Statement:** let each node's achievable worst error e_n(k) be non-increasing in k (true for the per-node optimum). Allocating a total of K values by repeatedly serving the node with the largest current e_n, equivalently choosing the smallest common τ with Σ_n m_n(τ) ≤ K, minimises max_n e_n(k_n).
- **Sketch:** let ε* be the optimum and k*_n = m_n(ε*). Then Σ k*_n ≤ K, and the rule never spends on a node at or below ε* while another node is above it.
- **Corollaries:**
  1. With greedy (non-monotone) curves the guarantee does not hold, which is why E6's pooled greedy trails the optimum.
  2. Status error ≤ τ (§2.3).
  3. With τ = 1 and no budget, the rule reduces to "send exactly what is needed for the tolerance", the buffered and optimal counterpart of send-on-delta.

### 2.7 E4: real satellite contacts over Ghana (corrects a first-pass premise)
- **Data:** Kinéis (25 satellites, TLE snapshot 2026-10-16), SGP4, 7 days.
- **Contacts:** Weija, Pra and Ankobra get **59–61 contacts/day** at ≥ 10° elevation (median gap 0.26 h, max 1.6 h), or 37–38/day at ≥ 25° (max gap 2.6 h). Trenton (US) gets 69/day.
- **Correction:** the first pass's claim that "equatorial sites starve for contacts" is **false** for a full modern constellation. Satellite scarcity comes from **message quotas and size limits** (tens of bytes per message, plan caps) and collisions, not from waiting. Long gaps only occur with sparse constellations (2–3 h revisits; Capez 2022 [33]).

Script `e4_satellite_contacts.py`; output `results/scoping/e4_contacts.csv`.

### 2.8 E8: TTN fair-use daily budget vs a node's data
A 4-parameter, 10-minute node needs 1,296 B/day. Under 30 s of airtime a day, with full frames:

| SF | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|
| Bytes/day | 17,982 | 9,990 | 5,060 | 2,142 | 969 | 510 |
| Share of need | 13.9× | 7.7× | 3.9× | 1.65× | **0.75** | **0.39** |

- **Steady state:** scarcity binds only at SF11–12. In urban London (LoED, 16,376 devices) **7.6% of devices sit at SF11–12** and 12.7% of uplink frames are SF12. Remote rivers should skew higher (an inference, to verify).
- **After an outage of D days**, the backlog competes with live data for the same airtime. At SF10–12 the share of the backlog that can be sent falls to about 0.1–0.4. **This outage-recovery drain is the most common deep-scarcity regime**, and it ties directly to Paper 2's measured heavy-tailed outages.

Script `e8_ttn_budget.py`.

---

## 3. Where capacity is scarce (premises)

| Regime | Evidence | Status |
|---|---|---|
| Edge-of-coverage LoRaWAN on TTN | E8; LoED SF mix; TTN fair use 30 s/day uplink, 10 downlinks/day including ACKs | TTN figures from forum and course sources; **fetch the official TTN documentation** |
| Outage recovery (backlog drain) | Paper 2 records: InWaterSense ~51% of lost data in outages ≥ 1 day; Weija 71–100%; UVA 83% of system down-time ≥ 1 day | Records to copy into Paper3 (cite the original data sources) |
| Shared gateway backhaul | InWaterSense (2 nodes, 1 GPRS gateway), Weija (Waspmote → Meshlium → 3G) | Architecture facts from the dataset papers |
| Satellite IoT | Contacts are plentiful (E4); quotas and message sizes are the limit (Swarm 750 × 192 B/month, now closed; Astrocast < 160 B; Myriota ≤ 250 B, ≤ 20 kB/day); SALSA [29] gives at most one uplink per device per pass | **Per-vendor figures to verify** |

---

## 4. Literature map and the gap (all 67 papers in `papers/pdf/`, plus 4 fetched later)

| Line | Representative work | What it optimises | Why it does not cover our problem |
|---|---|---|---|
| Goal-oriented / VoI / AoI access | GO-IRSA [01] (Sept 2026), GORA [02], DELTA [03], data-sourcing RA [04], spatio-temporal freshness [05], error-based thinning [06], threshold ALOHA [07], AoII-RA [08], VoI scheduling [12, 13] | Freshness or error of the **current** state of synthetic processes (Wiener, AR, Markov) | Only the latest sample is kept. Chen et al. [06]: "buffer size of every transmitter is one packet and new packets replace older undelivered packets". GO-IRSA uses an N-bit ACK every frame. |
| Freshness vs throughput | MobiHoc 2025 [72] | AoI vs delivery rate | Throughput counts packets, not record fidelity |
| Satellite IoT with semantics | [21–26] | AoI, VAoI, a GoT metric, pricing | Status metrics; Ramachandran [25] models buffered data as a fluid |
| DtS-IoT MAC | SALSA [29], uplink policies [28], multichannel [30], RESS-IoT [35] | Collisions, fairness, slots | Packets are interchangeable: "full-buffer assumption, same priority" [30] |
| Bulk LoRaWAN collection | FREE (IoT-J 2020) [70], Zorbas WF-IoT 2019 | Time and energy to deliver **all** buffered data | Content-blind; assumes everything fits |
| Priority/QoS in LoRaWAN/WSN | [42–47] | Class or application priority | Priority by traffic class (rejected for WQ by E1) |
| Progressive / multiresolution data | HIRE [53], PIVOT [54], DIMENSIONS, MMS burst selection [56], 3-D meshes [55] | Storage/retrieval at multiple precisions; science-data selection | Data-blind layers (HIRE) give a good average but a poor worst case (E5a). No uplink, budget or multi-node model. |
| Precision allocation in sensor databases | Olston et al. SIGMOD 2003; Deligiannakis et al. EDBT 2004 and SIGMOD 2004; PRESTO 2005 | **Minimise communication subject to a precision bound** (adaptive filter widths; on-demand pulls of archived data) | The dual problem, on causal streams or pulls, with elastic communication. Not "budget fixed by regulation, minimise the worst error of the buffered record across nodes, with scarce downlink and outages". **Closest prior art: credit explicitly** (PDFs requested). |
| VoI in queues | De Cuypere/Patil/Fiems [69, 73] | Transmit-or-wait to a mobile sink | Value is a function of age, not content |
| Submodular selection | Krause/Guestrin [57], Kalman sensor selection [58, 59] | Average (MSE/MI) objectives | Our objective is the worst case; greedy guarantees for MSE do not transfer (E7: greedy is about 1.4× the optimum) |
| Optimal L∞ line approximation | Imai & Iri 1988; Soroush et al. MobiHoc 2008 [81]; GAMPS SIGMOD 2009 (requested) | Fewest segments/space for a given L∞ bound, per stream or over many streams | The per-node component of our optimum. Not the budget-first pooled dual, not uplink scheduling, no protocol or regime |

**Gap statement (to defend).** When the uplink of a group of environmental sensors is capped by regulation, plan or post-outage drain, the question is *which buffered readings, from which node, should go first*, so that the server's **record** (with status and alarms as special cases) meets a **network-wide worst-case error bound** at the smallest budget, and degrades gracefully below it. No prior work formulates this budget-first, min-max, record-oriented problem, and no prior work evaluates it on real environmental data with real capacity regimes. The mechanism needed, a shared value threshold, sits between Paper 1's send-on-delta (a fixed δ per node) and the GO-IRSA family (a broadcast threshold on current-state value).

---

## 5. Candidate scopes (revised)

### Option A2 (recommended): min-max value scheduling of buffered telemetry over scarce shared uplinks
- **Question:** a gateway or uplink with a regulated or plan-limited budget serves N multi-parameter nodes that buffer readings, and outages create backlogs. What should each node send, and in what order, to minimise the network-wide worst-case error of the server's record (status and alarms included), and how close to optimal can a one-number broadcast protocol get?
- **Mechanism:**
  1. The server broadcasts a water level τ (a few bytes, rarely; fits TTN's 10 downlinks/day).
  2. **Known budget:** each node sends its min-# set for τ × tolerance (exact, by dynamic program; feasible on an MCU for 1-day buffers).
  3. **Uncertain truncation:** each node sends a nested value order instead, at a price of about 1.4×.
  4. Events go first.
  5. Nodes piggy-back m_n(τ) or their residual worst error (1–2 B) so the server can set the next τ.
- **Contributions** (evidence exists for 1–3; 4–5 to build):
  1. **Problem and regimes:** the budget-first, record-oriented min-max problem, with measured scarcity regimes (E8, LoED, E4, Paper 2-type outage records). Status is bounded by the record (lemma).
  2. **Single node:** the full set of baselines (FIFO, newest-first, class, HIRE-style progressive, newest + progressive). The average is a near-tie, reported honestly; the **worst case** differs by large margins (E5a). The price of nestedness is about 1.4× (E7, E7b).
  3. **Multi-node: common-τ min-# is the exact pooled min-max optimum** (water-level proposition, §2.9; per-node optimum curves are monotone, greedy curves are not). Whole pool within tolerance: 85% vs 2.5% for data-blind equal shares at 10% of bytes (E6, E7c).
  4. **Robust protocol:** τ updates with scarce downlink; silent losses (unconfirmed uplinks, about 10%) desynchronise the node's mirror, so design and test a fix (e.g. value-weighted repetition, periodic digest). Uncertain capacity: the value order is nested, so any truncation still gives a min-max-good prefix.
  5. **Evaluation on real data and regimes:** 39 USGS sites (6 chains), InWaterSense, Weija; outage-recovery drains replayed from the real outage records; TTN SF10–12 budgets; a gateway-backhaul quota; energy per delivered guarantee.
- **Why it suits IoT-J:**
  - a practical IoT protocol problem with a clean formal core (min-max, water level);
  - large effects on the metric that matters (the record guarantee);
  - real multi-site data and real capacity regimes;
  - honest negatives (average fidelity is a near-tie; noisy sites);
  - a trilogy with Papers 1–2 that stays standalone in its question.
- **Risks** (§7): the algorithmic pieces are simple, so a reviewer may call them obvious; this must be met with the formulation, the exact optimality, and the scale of the evidence. Real pools are small (E6: the gain holds but shrinks); silent loss may erode the mirror; per-device TTN budgets cannot be pooled, so pooling claims are limited to shared uplinks (gateway backhaul, pass slots, pooled plans); overlap with Olston/Deligiannakis must be argued carefully once their PDFs are read.

### Option A (first pass): "anytime" value-ordered upload within one node
- **Superseded.** Its average-fidelity case collapses against `stride_nf`, and its encoding overlaps HIRE. It survives as contribution 2 of A2.

### Option B: value-aware random access
- **Not recommended alone:** that is GO-IRSA's and GORA's ground. A2's water level is a scheduling rule; its random-access variant could be a future extension.

### Options C, D, E
- **Unchanged:** post-outage storms become A2's main regime; proposal 3 as written is not viable; importance-aware SF/replication becomes one robustness knob in A2.4.

---

## 6. Working titles (statements)

1. *Guaranteeing the Record: Min-Max Scheduling of Buffered Environmental Telemetry over Scarce Shared IoT Uplinks*
2. *Water-Level Scheduling for Bounded-Error Environmental Records over Budget-Limited LPWAN Uplinks*
4. *One Number Is Enough: Network-Wide Error Bounds for Buffered Water-Quality Telemetry under Uplink Budgets*
3. *Bounded-Error Telemetry Records under Uplink Budgets: Value-Ordered Store-and-Forward for Multi-Node Water-Quality Monitoring*

---

## 7. Before freezing (in order)

1. ~~E7~~ done: greedy and bottom-up are about 1.4× the optimum and non-monotone, so the design switched to common-τ min-# (E7c). Still open: a nested order with smaller price, or a hybrid (send the optimal set for a conservative budget first, then a nested refinement). Also the MCU cost of the min-# dynamic program for 1–7-day buffers.
2. **Read the round-2 prior art** (Olston 2003, Deligiannakis 2004 ×2, PRESTO, DIMENSIONS, Zorbas 2019) and write a precise differentiation paragraph.
3. **E9, outage-recovery drain on real records:** replay InWaterSense, Weija and UVA outages; TTN SF10–12 daily budgets plus live traffic. Metrics: time until the record is back within tolerance, and the worst error during the drain. Pre-register hypotheses (as in Paper 2).
4. **E10, silent loss and scarce downlink:** unconfirmed losses at 5–20% and τ updated once a day. Measure mirror drift and repair cost.
5. **Theory:** write out the water-level proposition (§2.9) with its tie and integrality details; bound the price of nestedness if possible (the empirical value is about 1.4×).
6. **Verify facts:** the official TTN fair-use page; satellite plan quotas and message sizes (Kinéis, Myriota, Astrocast); whether pooled data plans exist for satellite IoT.

---

## 8. Open decisions for the Prof

1. **Scope A2** as recommended (multi-node, min-max, outage recovery as the lead regime)?
2. **Framing:** lead with LPWAN edge coverage plus outage recovery (strong evidence, Paper 2 continuity) or with satellite backhaul (fashionable, but E4 shows contacts are not the bottleneck; quotas are)?
3. **May Paper 3 cite Papers 1 and 2** (under review at IJDSN), or must it stay standalone? The water-level rule is naturally presented as the budget-first dual of Paper 1's send-on-delta.
4. **Ghana deployment:** any planned LoRaWAN or satellite site, so we could measure even one real budget or outage trace?

---

## 9. Files

- `src/lit/`: `oa_search.py`, `arxiv_search.py`, `retry_downloads.py`.
- `src/scoping/`: `e1_class_priority.py`, `e2_upload_order.py`, `e4_satellite_contacts.py`, `e5_worstcase_pooled.py`, `e6_pooled_chains.py`, `e7_greedy_vs_optimal.py`, `e7b_bottomup_order.py`, `e7c_pooled_optimal.py`, `e8_ttn_budget.py`.
- `docs/E9_PLAN_DRAFT.md`: draft plan for the outage-recovery experiment (not frozen).
- `results/scoping/`: all outputs and logs.
- `data/clean/` (USGS, InWaterSense, Weija; copied from Paper 2), `data/tle/` (Kinéis TLEs).
- `papers/`: 71 PDFs in `pdf/`, `txt/`, `txt_flow/`, `search/`, `download_list.tsv`, `MANUAL_DOWNLOAD.md` (round 2 at the bottom).
