# Paper 3 literature notes: closest prior art and positioning

Cards for the works that decide Paper 3's novelty claim, written after reading the PDFs in `pdf/` (2026-10-16). Numbers are file prefixes. "Ours" means scope A2 in `../PAPER3_SCOPING.md`.

**Rule (as in Papers 1 and 2):** every citation is verified from the PDF. Papers 1 and 2 must not be cited (both just submitted; user decision 2026-10-16).

---

## A. The allocation idea across sources: closest in spirit

**[74] Olston, Jiang & Widom, "Adaptive Filters for Continuous Queries over Distributed Data Streams", SIGMOD 2003.**
- **Setting:** sources push updates to a central stream processor. Each source keeps a filter, an interval [L, H] around its last reported value, and reports only when the value leaves it. Queries carry precision constraints.
- **Key idea:** allocate filter widths non-uniformly across sources. They show uniform allocation is correct but not best. Widths adapt by periodic shrinking and selective growing, to **minimise update traffic subject to a fixed precision**.
- **Relation to ours:** this is the precision-first dual of our budget-first water level, and the allocation-across-sources insight is theirs.
- **What they do not do:** a fixed, regulated byte budget; buffered history or a record; outages or backlogs; scarce downlink (their growth messages are on an elastic wired network); worst-case error minimisation under the budget; LPWAN constraints.
- **Must cite as the origin of non-uniform error allocation across sources.**

**[82] Gandhi, Nath, Suri & Liu, "GAMPS: Compressing Multi Sensor Data by Grouping and Amplitude Scaling", SIGMOD 2009.**
- **Setting:** offline archival. Approximate a *set* of sensor signals with the least space, so that every reading is within one given L∞ ε. Uses piecewise-constant buckets, grouping of correlated signals and amplitude scaling; an (ε, log)-approximation.
- **Relation to ours:** "one common L∞ ε across many signals, minimum total size" is the min-# side of our common-τ rule, applied to an archive.
- **What it does not do:** the budget-first dual; collection over a network (explicitly left to existing collection techniques); distributed nodes deciding locally; outages, budgets or downlink.

**[83] Deligiannakis, Kotidis & Roussopoulos, "Dissemination of compressed historical information in sensor networks", VLDB J. 16:439–461 (2007; online 2006)** (`pdf/s00778-005-0173-5.pdf`). Read 2026-10-23. **This is the closest prior art, and it pre-empts the core of scope A2.**
- **SBR:** nodes buffer multi-valued history, then compress it to a target bandwidth with a base signal plus piecewise linear projections, minimising SSE, relative error or (Section 4.6, Chebyshev regression) the **maximum absolute error**, with a "strict error bounds" mode.
- **Localized groups (Section 5):** a group leader shares a total bandwidth across members. Uniform allocation is called sub-optimal, and residual bandwidth goes repeatedly "to the node with the largest error". This is the water-level idea as a heuristic.
- **Assumes reliable delivery:** bandwidth includes retransmissions; multi-hop WSN.
- **What it does not do:** one-way or lossy links; regulated/priced satellite plans; an exact min-max optimum; environmental compliance tolerances.

**[75] Deligiannakis, Kotidis & Roussopoulos, "Hierarchical In-Network Data Aggregation with Quality Guarantees", EDBT 2004, LNCS 2992, pp. 658–675** (inside `pdf/b95855.pdf`, the full proceedings volume). Precision-first: it redistributes error thresholds in aggregation trees to minimise messages (extends [74]).

**SIGMOD 2004 SBR paper** (DOI 10.1145/1007568.1007628): not obtained; superseded by [83].

---

## B. Per-node optimal approximation: a classical component, not our novelty

**[80] Imai & Iri, "Polygonal Approximations of a Curve: Formulations and Algorithms", 1988.**
- Defines the **min-#** (fewest vertices for a given error) and **min-ε** (least error for a given number of vertices) problems.
- For a piecewise-linear function under the L∞ error, min-# is solvable in **O(n)** time (Theorem 2.1, convex-hull technique).
- Our per-node optimum (E7) is min-ε, and the common-τ rule uses min-#.
- On-device feasibility: O(n) per τ is trivial on an MCU.

**[81] Soroush, Wu & Pei, "Fast and Quality-Guaranteed Data Streaming in Resource-Constrained Sensor Networks", MobiHoc 2008** (arXiv 0811.4672).
- Online, linear-time, constant-space algorithms that are optimal in the number of segments for a pointwise L∞ bound (PLA-PointBound) and for a per-segment bound.
- Our node-side component could use their online form for live data and Imai–Iri for buffered data.

---

## C. Archival and multi-resolution storage in sensor networks

**[77] Desnoyers, Ganesan, Li, Li & Shenoy, "PRESTO: A Predictive Storage Architecture for Sensor Networks", HotOS 2005.**
- Proxy-centric. Sensors archive locally. The proxy builds models and pushes model parameters; sensors push only "unpredictable" data (model-driven push). The proxy pulls archived data on a cache miss (PAST queries).
- **Relation:** archive-at-node plus pull is a neighbour of buffered upload, but driven by query and prediction, not by a fixed budget. No min-max allocation across nodes.

**[79] Ganesan et al., "An Evaluation of Multi-resolution Storage for Sensor Networks" (DIMENSIONS), SenSys 2003.**
- Wavelet summaries at multiple resolutions, drill-down queries, progressive aging. Data-blind multiresolution, like [53] HIRE.

**[53] Barbarioli et al., HIRE, PACMMOD 2023.**
- Layered, max-error-bounded multiresolution time-series encoding for edge storage and transfer. Data-blind layers (E5a shows these lose the worst case).

---

## D. LPWAN bulk collection: the IoT-J precedent

**[70] Abdelfadeel, Zorbas, Cionca & Pesch, "FREE: Fine-Grained Scheduling for Reliable and Energy-Efficient Data Collection in LoRaWAN", IEEE IoT-J 2020**, and **[78] Zorbas et al., WF-IoT 2019.**
- Time-slotted scheduling of **bulk buffered data** (e.g. 1 KB per node) to minimise collection time and energy with near-100% delivery.
- Content-blind; assumes everything is delivered.
- **Our starting point:** what to send when everything cannot be delivered.

---

## E. Goal-oriented / VoI / AoI access: status, not record

- **[01] GO-IRSA** (Talli et al., arXiv Sept 2026): a broadcast VoI threshold for current-state MSE of independent Wiener processes, with an N-bit ACK every frame.
- **[02] GORA, [03] DELTA, [04] data sourcing RA, [05] spatio-temporal freshness, [07] threshold ALOHA, [08] AoII-RA.**
- **[06] Chen et al., INFOCOM 2021:** "the buffer size of every transmitter is one packet and new packets replace older undelivered packets".
- **[72] MobiHoc 2025:** throughput-AoI region; throughput counts packets.
- **Relation:** a threshold broadcast is common to GO-IRSA and to our water level. Theirs acts on the value of the *current state* under per-frame feedback; ours acts on the *buffered record's worst case*, with feedback at most 10 times a day.

---

## E2. Biologging satellite telemetry: one-way, tiny-message practice

- **[84] Boehme et al., "Technical Note: Animal-borne CTD-Satellite Relay Data Loggers for real-time oceanographic data collection", Ocean Sci. 5:685–695 (2009).**
  - Argos uplinks of at most 256 bits (228 usable), a minimum 40-s interval, and "no handshake required".
  - Each CTD profile is sent as 17 points (8 fixed depths plus 7 broken-stick piecewise-linear inflection points) in two messages.
  - A pseudo-random transmission schedule sends an unbiased sample of stored profiles; some messages are received more than once, which allows flipped bits to be corrected.
- **[85] Photopoulou et al., "The generalized data management and collection protocol for CTD-SRDLs", Animal Biotelemetry 3:21 (2015).**
  - Buffers of about 6–7.5 days per data type; the broken-stick model for abstraction.
  - "This lack of handshake creates the need for a stochastic transmission strategy of the information accumulated in the transmission buffer."
- **[87] Validation of abstracted dive profiles relayed via Argos (loggerhead turtle), Animal Biotelemetry 2022.**
- **Manual download:** Fedak et al. 2001, Marine Mammal Science (two approaches to compressing time-depth data); Fedak et al. 2002, Integrative and Comparative Biology (getting more useful data from smaller packages).
- **Relation to ours:** the established practice for one-way, quota-limited record delivery. It is heuristic (a fixed point count, not a guaranteed tolerance; data-blind random repetition), and it is the right "practice" baseline for a satellite version of Paper 3.

## F. Other relevant work

- **Satellite IoT MAC [28–35]:** packets are interchangeable; full-buffer assumption.
- **VoI queueing [69, 73] (Fiems group):** value depends on age, not content.
- **VoI review [14].**
- **Satellite contacts [25, 33].**
- **Prof Adu-Manu's Weija paper [65]:** WQM requires "timely reporting … and completeness"; Waspmote → Meshlium → 3G.

---

## Positioning paragraph (draft for the paper)

> Allocating approximation error non-uniformly across distributed sources is an established idea. Olston et al. [74] adapt per-source filter widths to minimise update traffic under query precision constraints, and GAMPS [82] minimises the archived size of many sensor signals under one L∞ bound. Optimal single-signal L∞ approximations are classical [80, 81]. These works fix the precision and minimise communication or space, over elastic links or offline archives. Remote environmental IoT faces the reverse situation. The uplink budget is fixed by regulation or by a service plan (for example, a community LoRaWAN airtime cap). Outages leave nodes with buffered backlogs, and downlink feedback is limited to a few messages a day. The question is then how to spend a fixed budget across nodes and their buffered records so that the worst reconstruction error is as small as possible. We show that the answer is a common-τ rule, coordinated by one broadcast number, and evaluate it on real river data and real outage records.
>
> *Superseded on 2026-10-23: [83] already does budget-first, max-error-capable, pooled allocation over buffered history (heuristically). See `../PAPER3_SCOPING.md` §F.*

---

## C. Revision 2 sweep (2026-11-03): prior art for a decision-aware certifiable encoder

Purpose: the novelty review (River_Water_Quality_Novelty_Review.docx) asks for a decision-aware encoder. Before building it, the nearest neighbours were searched (standard and extended web search, not a systematic review) and the open-access PDFs read (files 90-96 in `pdf/`, text in `txt/`). Items not yet read are in MANUAL_DOWNLOAD.md, Round 4.

**[90] Brito, Katsis, et al., "Efficient Approximate Query Answering over Sensor Data with Deterministic Error Guarantees", arXiv 1707.01414 (PlatoDB), and [91] Lin, Boursier, Papakonstantinou, "Plato: Approximate Analytics over Compressed Time Series with Tight Deterministic Error Guarantees", arXiv 1808.04876.**
- Setting: compressed time series stored in segment trees; aggregates (sum, average, correlation, linear time-series expressions) are answered with a deterministic error guarantee computed from per-segment error measures.
- Relation to ours: deterministic interval answers from a compressed representation are known. Our interval certificates for aggregates (daily min/max, 7DADM) therefore cannot be claimed as new in form.
- What they do not do (checked by search of the text): three-valued threshold decisions (exceeded, not exceeded, undetermined); a byte quota; a lossy one-way channel; selecting what to transmit for a decision.
- Must cite as the origin of deterministic-guarantee approximate analytics.

**[94] Taurone, Feher, Sipos, Lucani, "TREAT", DEBS 2024.**
- Setting: IoT time series in multi-cloud storage, generalised deduplication plus random linear network coding; queries use the compressed base bits to filter (possible minimum and maximum of a value from its base) before downloading deviations.
- Relation to ours: the nearest "compression plus erasure coding plus predicate evaluation" work. It uses possible-min/possible-max intervals to decide predicates, which is the same logical idea as our three-valued rule. Its setting (storage, reliable retrieval, lossless) and objective (fewer bytes downloaded) differ.

**[92] Muniz-Cuza, Boehm, Pedersen, "CAMEO", arXiv 2501.14432; [96] TerseTS, EDBT 2026; [93] Sun, Karras, Zhang, SHRINK direct analytics, arXiv 2503.13246.**
- Feature-preserving error-bounded compression: CAMEO bounds the ACF/PACF deviation; SHRINK supports outlier detection on a base representation. Both bound a statistic or a task accuracy empirically, with no certificates of a threshold decision and no loss model.
- Relation to ours: they show that pointwise error bounds are known to be insufficient for downstream analytics; our pH finding (tolerance hides near-threshold peaks, ENV_RESULTS.md) is a concrete case.

**Priority encoding transmission (Albanese, Bloemer, Edmonds, Luby, Sudan, IEEE Trans. Inf. Theory 1996; US 5,617,541).**
- Not yet read (paywalled; Round 4). Per the abstracts found: messages are split into priority levels, and each level gets its own redundancy so that higher priority data survive more loss. Prioritised LT codes and unequal-error-protection random linear codes extend it.
- Consequence for the plan: unequal protection of decision witnesses is PET applied. The proposed novelty cannot be "protect important bytes more". It has to be the selection of WHAT is important (which readings and witnesses certify a threshold decision) and the certificate semantics, with PET-style layering as a baseline.

**Event-triggered and send-on-delta telemetry (Miskowicz; ALERT flash-flood systems).**
- Deadband reporting is the standard hydrological way to guarantee that threshold changes are reported. It is a mandatory baseline ("send-on-delta with the same bytes"), and it needs a duplex or reliable link to be safe: a lost event message is silent. Not yet read in full.

**Goal-oriented communication (Zhang et al., IEEE IoT Magazine 2022; value-of-information and age-of-incorrect-information work).**
- Frames task-oriented compression, mostly with learned encoders, random access, or scheduling. No certificate semantics. Cite for framing only.

**Gap statement (to be verified by a formal search before any "first" claim).**
- No work found that combines (a) a byte quota on a one-way lossy link, (b) selection of readings and witnesses to maximise certified threshold decisions, and (c) a server-side soundness proof for undecided, exceeded, and not-exceeded outcomes on real river records.
- Consequence: the defensible novelty is the combination and the soundness plus evidence, with PET, PlatoDB-style intervals, and TREAT-style possible-min/max filters credited as ingredients.

### C2. Round 4 reading results (2026-11-03)

Files 99-108 were read from the PDFs (text, and a rendered page for 99, whose text layer is garbled). File 98 was the WRONG article (Brassard, Crepeau, Santha, "Oblivious transfers and intersecting codes", same issue of IEEE Trans. Inf. Theory; my DOI was wrong, as for Deligiannakis earlier). The original Albanese et al. paper is re-requested in MANUAL_DOWNLOAD.md, Round 5.

**[99] Boucheron and Salamatian, "About priority encoding transmission", IEEE Trans. Inf. Theory 46(2), 2000.**
- Formal definition of a PET code: message of m symbols, codelength n, and a non-decreasing priority function beta; the symbols of priority level i are recoverable from ANY beta(i) received code symbols. Feasibility: the sum over levels of (n R_i / beta^i) is at most 1 (Singleton-type bound for fixed-length codes).
- They show PET (time-sharing and interleaving of classical erasure codes) achieves the capacity region of the broadcast erasure channel with degraded message sets.
- Consequence: a layered record in which the certifying witnesses form level 1 and need only K1 of Q messages, while the remaining values need K2 > K1, is a PET code. It is the mandatory layered baseline, and optimality of layering over loss channels is classical. Our contribution cannot be the layering. It can be the choice of which values form level 1 so that threshold decisions are certified.

**[106] Cheng, Kalashnikov, Prabhakar, "Evaluating probabilistic queries over imprecise data", SIGMOD 2003.**
- Each stored sensor value carries an uncertainty interval; queries (including nearest-value and extremum-type queries) are answered over the intervals, with pruning of intervals that cannot affect the answer. Probabilistic, with interval bounds from the update policy.
- Consequence: answering threshold or extremum queries from bounded-uncertainty intervals is classical database work. Our three-valued rule is its deterministic special case. Cite with PlatoDB and TREAT.

**[103] Diaz-Cacho, Delgado, Barreiro, Falcon, "Basic send-on-delta sampling for signal tracking-error reduction", Sensors 17(2), 2017.**
- Send-on-delta (deadband) transmits a sample when the value departs from the last sent one by delta; they compute delta in real time for a desired mean transmission rate. Reduces tracking error against periodic sampling at the same rate.
- Consequence: the standard event-triggered baseline with a byte rate. Needs a reliable link for any guarantee; on a one-way lossy link, a lost event message is silent.

**[100] Zhang et al., "Goal-oriented communications for the IoT and application to data compression", IEEE IoT Magazine 2022.** Goal-oriented compression by learned or clustering methods; no deterministic certificates. Framing only.

**[108] Wong and Kerkez, "Real-time environmental sensor data: an application to water quality using web services", EMS 84, 2016.** Real-time water-quality architecture over IP and cellular links with adaptive sampling driven by events (duplex). Shows that EMS accepts real-time telemetry papers; it assumes a bidirectional link, which our one-way case removes.

**[101] Twarog, Hawro, Kwater, EMS 196, 106793 (2026)** is a BOD soft-sensor (state estimation), not telemetry. **[102] Horsburgh et al., EMS 70, 2015** is quality-control software for continuous sensor data. Both show the EMS audience and its software-and-QC emphasis; neither is a competitor. **[107] Sun et al., EMS 204, 107068 (2026)** (uncertainty review) was not read in depth. **[104] Serf** and **[105] Lin et al. 2025 (progressive bounded-error PLA)** are error-bounded compressors without decision certificates or loss models.

**Updated gap statement.**
- Known (credit): layered unequal protection (PET); interval answers from bounded-uncertainty or compressed data (Cheng 2003, Plato, TREAT); event-triggered sampling (send-on-delta); error-bounded piecewise-linear compression (Imai-Iri; Lin 2025).
- Not found: the joint problem of choosing, under a byte quota on a one-way lossy link, the readings and witnesses that maximise the share of environmental threshold decisions that the server can CERTIFY (exceeded, not exceeded), with soundness proved from received bytes only, and evaluated on real river records.
- This is a combination-and-evidence claim. It is defensible for EMS only if the measured gain over (a) the current record-first code, (b) a PET-layered record-first code, (c) send min/max, and (d) send-on-delta is material on near-threshold cases.
