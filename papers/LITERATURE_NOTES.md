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
