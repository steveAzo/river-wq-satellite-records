# Response to the pre-submission review (Environmental Modelling & Software)

Review: `Environmental_Modelling_Software_Critical_Editorial_Review.docx`. Revised manuscript: `draft/` (v0.3).
Each item states what was done, where it is in the manuscript, and the supporting record in `docs/`.

## Major comments

| Item | Response | Manuscript | Record |
|---|---|---|---|
| M1 "Regulatory-grade" not demonstrated | Removed from the title, abstract, and text. The tolerance is described as the USGS excellent-record accuracy, relative to the sensor record; sensor accuracy is stated as outside the bound. | Title; abstract; Sections 1, 3.1, 6.3 | — |
| M2 Contribution is integration | Contribution matrix added (established, adapted, new); the algorithms are credited as established; new elements are the certificate, the record-first code with its optimality, and the evaluation. Workflow figure added. | Table 1 (contributions); Fig. 1 | — |
| M3 Previous-day anchor assumed | Days are now self-contained (first value held back to midnight); a chained alternative was measured under loss, including bursts across midnight; self-contained days were certified more often although they cost 0.25 values per day more. | Section 3.1 | `RECORD_MODEL.md`, `E2E_RESULTS.md` |
| M4 No end-to-end on-wire implementation | Byte-level frame, quantiser, packing, Reed-Solomon, fountain code, erasure, header parsing, decoding, CRC, reconstruction, and certification implemented; golden byte vectors; every primary result computed on bytes or with exact probabilities proven equal to the byte pipeline. | Sections 3.3 to 3.6; 4.5 | `FRAME_SPEC.md`, `E2E_RESULTS.md` |
| M5 Packet semantics underspecified | Complete frame layout with version, block day and rollover, message index, K, code type, CRC-16 with context, segments with day offset, positions, and flags; worked example; operator metadata separated from the payload; capacity after overhead (5 values per 23 B). | Table 2 (frame); Section 3.3 | `FRAME_SPEC.md` |
| M6 Results not on quantised packets | Encoder made quantisation-exact (no margin); decimal quantiser grid; all results on the quantised byte path. | Sections 3.2 to 3.3 | `RECORD_MODEL.md` |
| M7 Guarantee terminology conflated | Record error, full certification, oracle within-tolerance share, and G_cert defined separately; certificate built from received positions only; Propositions 1 and 2. | Section 3.5 | `RECORD_MODEL.md` |
| M8 Channel parameters used as tuning inputs | Record-first code needs no channel knowledge (Proposition 2); channel-blind baselines; mismatch grid; regret against per-channel oracles; pilot-estimation scenario. | Section 5.2; Fig. 4 | `ROBUST_RESULTS.md` |
| M9 Buffered results on a coarse model | Packet-level multi-day replay on bytes with date tags, FIFO, deadlines, and server-side delay; buffering found not to help; seven-day rotation compared at equal delay. | Section 5.3; Fig. 5 | `MULTIDAY_RESULTS.md` |
| M10 Eligibility and parameter counts mixed | Per-channel loader (native intervals, seasonal sensors); four-parameter primary cohort; flow and per-site tables; results by interval; days with fewer than four parameters and site-equal medians reported. | Sections 4.1, 5.1; Table 4; Supplementary Tables S1 to S3 | `COHORT_AUDIT.md` |
| M11 Compression denominator ambiguous | Value share, byte share, and transmitted messages reported with denominators; intro example rebuilt on one serialisation. | Sections 1, 5.1 | `COHORT_AUDIT.md` |
| M12 Complexity insufficiently established | Linear-time claim withdrawn; table-free exact encoder (O(n^2) time, O(n) memory) identical to the reference on all 12,674 development days; measured times and memory; microcontroller estimates labelled. | Sections 3.2, 5.6 | `RESOURCES_RESULTS.md` |
| M13 Temporal, not independent-site, validation | New sealed cohort of 36 sites in five other regions; the 2024 data of the development sites reported as a temporal re-test. | Sections 4.1, 4.4, 5.7 | `CONFIRM2_PLAN.md`, `CONFIRM2_RESULTS.md` |
| M14 Baselines partly unlike field practice | Multi-day tag rotation; interleaved and block repetition; fountain code; channel-blind fixed redundancy; equal payload, quota, and delay; content and policy separated. | Sections 5.2, 5.3; Tables 3 and 6 | `BASELINES_RESULTS.md`, `MULTIDAY_RESULTS.md` |
| M15 Pre-registration overstated | Described as pre-specified and checksum-frozen with a committed freeze record (commit and tag) before opening; eight hypotheses with thresholds; exploratory analyses labelled. | Section 4.4; Table 5 | `CONFIRM2_PLAN.md`, `FREEZE2.md` |
| M16 Environmental usefulness inferred | Decision analysis: low DO, pH range, 7DADM, conductance pulses; three-valued certified decisions; missed events; daily statistics; peak timing; diel range. Limits reported (near-threshold pH, diel shape). | Sections 4.3, 5.4; Table 7; Fig. 6 | `STEP8_PLAN.md`, `ENV_RESULTS.md` |
| M17 Statistical units | Denominators table; site-clustered paired bootstrap for all contrasts; site distributions; season and site x month blocks; exact full-cohort probabilities; sampled days distinguished. | Section 4.5 | `STATS_RESULTS.md` |
| M18 Corruption and failures untested | CRC with context; hardened receiver; censoring of out-of-range readings; corruption, glitch, and outage experiments; clock and authentication requirements quantified. The confirmation found one CRC-16 false acceptance at a bit-error rate of 1e-2; reported, with a corroboration rule evaluated exploratorily. | Sections 3.5, 5.5, 5.7, 6.3 | `ROBUSTNESS_RESULTS.md`, `CONFIRM2_RESULTS.md`, `POSTHOC_C2.md` |

## Mathematical audit

- Equation (1) conditional: stated relative to the sensor record and a positive tolerance (Section 3.1).
- Formal definitions E, F, G: Section 3.5 and `RECORD_MODEL.md` (record error, full certification, within-tolerance share, G_cert).
- Quantisation margin: replaced by exact evaluation against dequantised endpoints (Lemma 1 in `RECORD_MODEL.md`), covering held head and tail, the logarithmic conductance grid, and censored readings.
- MDS recovery bound: exact probabilities for independent and Gilbert channels (forward recursions), checked against brute-force enumeration and the byte pipeline (`analytic.py`, tests).
- Certifiability condition: rule from received positions only, with a proof (Proposition 1) and exhaustive adversarial tests.
- Time and space: measured, not inferred (Section 5.6).

## Required experiments

| Experiment | Done | Record |
|---|---|---|
| E1 Real payload replay | Yes | `E2E_RESULTS.md` |
| E2 Anchor-loss stress | Yes (self-contained vs chained; bursts across midnight) | `E2E_RESULTS.md` |
| E3 Unknown-channel deployment | Yes (channel-blind choice, mismatch, regret, pilot estimation) | `ROBUST_RESULTS.md` |
| E4 Packet-level multi-day FIFO | Yes | `MULTIDAY_RESULTS.md` |
| E5 Environmental decision fidelity | Yes | `ENV_RESULTS.md` |
| E6 New-river validation | Yes (36 sealed sites, five regions) | `CONFIRM2_RESULTS.md` |
| E7 Full baselines and sensitivity | Yes | `BASELINES_RESULTS.md` |
| E8 Embedded resource profile | Partly: host measurements and operation counts; no microcontroller available (stated) | `RESOURCES_RESULTS.md` |

## Requested figures and tables

Table A (contributions): Table 1. Table B (per-site cohort): Table 4 and Supplementary Tables S1 to S3. Table C
(environmental decisions): Table 7. Figure A (workflow): Fig. 1. Figure B (error under exact, quantised, and
missed-anchor conditions): replaced by the certified-span example (Fig. 6) and the quantisation result (exact, zero
cost on USGS data) because quantisation no longer adds error. Figure C (robust choice of K): Fig. 4. Figure D
(multi-day delay): Fig. 5. Table 2 revision (hypothesis families): Table 5 (eight hypotheses, joint reporting).

## Outcome of the confirmation (for the cover letter)

Six of eight frozen hypotheses held on the new sites. C1 (median record at most two messages, interval upper bound
<= 30 B) was not supported: median 27 B, upper bound 33 B. C2 (zero false certificates) was not supported: one
CRC-16 false acceptance at a bit-error rate of 1e-2 certified 96 readings on one day. Both are reported in the
manuscript with their causes; the corroboration rule adopted afterwards is labelled exploratory.

## Venue (Sections 2 and 10 of the review)

The revision adds the environmental decision analysis, the reproducibility record, and the software description
that Environmental Modelling & Software expects; it is submitted there on the subscription route (no APC).
Elsevier Internet of Things remains the alternative if the editor judges the contribution to be primarily
communication engineering.

## Final check (2026-10-27)

A final check of the manuscript against this table found several items whose evidence was in `docs/` but not in the
paper. They were added: chained versus self-contained days under loss (Section 3.1, M3); the cohort flow
(Supplementary Table S3), days with fewer than four parameters, and site-equal results (Sections 4.1, 5.1, 5.2, M10);
the pilot channel-estimation scenario (Section 5.2, M8); measured host time and memory (Section 5.6, M12); the
denominators of every outcome and the site x month block bootstrap (Section 4.5, M17); golden byte vectors and pinned
package versions (software section, M4, software availability); recent reproducibility work in this journal and
prior art on grid-restricted endpoints and application-layer IoT coding (Section 2; Table 1). The code is now under
the MIT licence (`LICENSE`), with CC BY 4.0 for the derived data and results. The monthly figure moved to the
supplement (Supplementary Fig. S1); the dissolved-oxygen example is now Fig. 6.
