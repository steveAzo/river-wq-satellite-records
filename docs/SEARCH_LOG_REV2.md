# Search log for revision 2 (prior art for a decision-certificate encoder)

This log records what was searched, what was opened, and what was not reachable. It supports statements of scope, never of absence. All searches were made by an AI assistant (Claude Code) with a general web search tool restricted to US results ("standard" mode unless marked "extended"); the results are search summaries (access: search-summary) until a paper was downloaded and opened. None of this is a systematic review, and none of it is peer review.

## Searches (all 2026-11-03)

| # | Query | Mode | What came back | Opened afterwards | Conclusion within reach |
|---|---|---|---|---|---|
| 1 | TREAT compression erasure coding IoT time series queries DEBS 2024 | standard | TREAT paper (Taurone et al.), DBLP and ACM entries | PDF 94 (read: abstract, method, predicate filtering section) | TREAT exists and filters predicates with possible-min/max bounds on compressed data |
| 2 | query-aware lossy compression sensor time series threshold exceedance guarantee certified decision bounded error | standard | CAMEO, Sprintz, patents, SIGMOD 2009 multi-sensor | PDF 92 CAMEO (abstract, contribution list) | no source found that certifies threshold decisions |
| 3 | goal-oriented semantic communication environmental monitoring threshold event preserving compression satellite IoT water quality | standard | goal-oriented IoT overview, underwater semantic survey | PDF 100 Zhang 2022 (abstract, introduction) | goal-oriented framing only |
| 4 | Environmental Modelling & Software journal impact factor 2025 CiteScore quartile Q1 | standard | aggregator sites with different values | none | quartile Q1, impact factor about 4.6 to 5.2, CiteScore 9.4 to 9.9 depending on the aggregator (search-summary only) |
| 5 | event-preserving lossy time series compression guaranteed threshold crossing extrema error bound | extended | CAMEO, pMSz, NeaTS, TerseTS, Cadence | PDFs 92, 95, 96 (first pages) | no codec found that guarantees threshold-crossing preservation |
| 6 | priority encoding transmission unequal error protection erasure code prioritized messages Albanese | standard | PET origin, patent US 5,617,541, prioritised LT codes | PDF 99 Boucheron and Salamatian (first page only, as an image) | PET and its extensions exist; Albanese 1996 itself not read |
| 7 | approximate query processing sensor data deterministic error guarantees min max threshold queries compressed summaries interval answers | standard | PlatoDB, Plato | PDFs 90, 91 (introduction, query model; text searched for MIN, MAX, threshold) | deterministic aggregate guarantees exist; threshold decisions not found in the text searched |
| 8 | LoRaWAN or satellite IoT water quality monitoring data reduction preserving exceedance alerts compression transmission 2024 2025 | standard | LoRa water-quality studies, vendor case study | none | nothing found that guarantees exceedance reporting over satellite links |
| 9 | value of information age of incorrect information threshold-based decision remote sensing communication budget semantic timeliness | standard | AoII and task-oriented AoI papers | none | scheduling literature, no certificates |
| 10 | M4 aggregation min max preserving time series downsampling error-free visualization extrema preserving piecewise linear | standard | downsampling libraries, one arXiv paper | none | min/max-preserving downsampling exists in practice (visualisation) |
| 11 | send-on-delta event-triggered sampling deadband telemetry hydrological river flood threshold alert data reduction guaranteed | standard | send-on-delta, ALERT flood systems | PDF 103 Diaz-Cacho 2017 (abstract, introduction) | deadband telemetry is standard; no loss guarantee found |
| 12 | certain answers three-valued logic incomplete information interval-valued sensor data threshold query soundness uncertain data streams | standard | certain answers, probabilistic threshold queries, AU-DBs | PDF 106 Cheng 2003 (abstract, introduction; text searched) | interval-bounded query answering is classical |
| 13 | Argos satellite tag data compression summary messages dive profile threshold event prioritisation transmitted within message limit | standard | tag compression (broken stick), message caps | none (earlier papers 84, 85, 87 already in the project) | tag practice sends abstracted profiles, no certificates found |
| 14 | task-oriented lossy compression of time series for threshold detection anomaly detection preserving bounded error guarantee Sensors IoT | standard | SHRINK, CAMEO, autoencoder-based work | PDF 93 SHRINK (abstract) | task-oriented compression without certificates |
| 15 | Environmental Modelling & Software sensor data transmission compression telemetry real-time water quality decision support low-bandwidth | standard | environmental compression and LoRa studies | PDFs 101, 102, 108 (abstract, introduction, text searched) | EMS publishes real-time monitoring and quality-control work; none on one-way byte-limited telemetry found |

## Opened and how far (access label read-directly unless stated)

PlatoDB (90) and Plato (91): introduction, query model, grep of the text. TREAT (94): abstract, method, predicate-filtering section. CAMEO (92) and SHRINK (93): abstract and contribution list. Boucheron and Salamatian (99): first page only (the text layer is garbled; read from a rendered image). Zhang 2022 (100), Twarog 2026 (101), Horsburgh 2015 (102), Diaz-Cacho 2017 (103), Cheng 2003 (106), Wong and Kerkez 2016 (108): abstract and introduction, plus text searches. Lin 2025 (105): abstract and introduction. Serf (104), Sun 2026 (107), Cadence (95), TerseTS (96): title page or first page only.

## Blocked or not done

- Albanese, Bloemer, Edmonds, Luby, Sudan 1996, "Priority encoding transmission": obtained by the user on 2026-11-09 (papers/pdf/Priority_encoding_transmission.pdf, first page checked) and read in part (introduction, Definitions 3.1 and 3.2, Theorems 3.3 and 3.5, start of Section IV); the proofs were not read. Before that it was NOT read. The file downloaded in Round 4 was a different article (Brassard, Crepeau, Santha, same issue of IEEE Trans. Inf. Theory); it was renamed and not used. Re-requested (papers/MANUAL_DOWNLOAD.md, Round 5).
- No direct search of Scopus, Web of Science, Google Scholar, DBLP, IEEE Xplore, ACM DL, or Elsevier indexes; the web search tool is a general engine limited to US results. The official Clarivate and Scopus values for the journal were not opened.
- No formal, reproducible nearest-neighbour search (query log with inclusion rules) has been run.
- Stopped: no search was cut off by a budget or a timeout; each search was ended by the assistant's choice after reading its results.

## Statement of scope (the only novelty sentence this evidence supports)

Searches 1 to 15, using a general web search engine limited to US results, and the papers listed above (opened as stated), found no earlier statement of a source-side encoder for a one-way lossy satellite link that, under a byte quota, selects an error-bounded record and feature-extremum witnesses and gives three-valued threshold decisions with soundness proved from received bytes. Albanese 1996 could not be read, the official journal indexes were not searched, and several papers were read only in part. This sentence does not claim that no such work exists.

## Reference checks (2026-11-09, after the manuscript draft)

- TREAT authors: Taurone, Feher, Sipos, Lucani (search summary naming the ACM reference; the PDF header showed only two names). Access: search-summary.
- Albanese et al. 1996 DOI: the search summary reported 10.1109/18.556670 (IEEE record); the doi.org link redirected to ieeexplore.ieee.org/document/556670, whose page did not load as text, so the search summary alone did not confirm it; the user then stated on 2026-11-09 that 10.1109/18.556670 is the actual DOI of the paper, and the manuscript bibliography carries it (user-supplied, not opened by the assistant) (volume, issue, and pages were checked against the PDF first page).
