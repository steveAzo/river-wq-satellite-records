# Paper 3 revision plan (response to the EM&S pre-submission review)

Source: `Environmental_Modelling_Software_Critical_Editorial_Review.docx` (18 comments M1–M18, a maths
audit, experiments E1–E8, figures/tables A–D, and a P0/P1/P2 checklist). Started 2026-10-25.
Rule: every item below is either done, or the paper says plainly why it cannot be done. No item is dropped.

## Integrity decision (applies to every step)

The fixes change the method (byte-level codec, self-contained days, channel-blind configuration, packet-level
buffering). USGS 2024 has already been opened, so results of the revised method on 2024 are a temporal
re-test, not a blind confirmation. Therefore:

- Develop and tune the revised method on USGS 2023 only (as before).
- Re-run 2024 and report it as "temporal re-test (opened 2026-10-23)".
- Assemble a NEW sealed cohort of USGS rivers not among the 39 sites, preferably other hydro-climatic regions,
  chosen by metadata only (parameter availability, interval), checksummed before any value is read. This is the
  new confirmation set (covers M13/E6 and M15).
- Freeze the revised plan (git tag + Zenodo version + checksums) BEFORE opening the new cohort; keep an audit log.
- Keep the original 2023-10-23 frozen results as a documented first round; do not rewrite history.

## Steps (ordered; P0 first)

| Step | Work | Review items | Status |
|---|---|---|---|
| 1 | Cohort audit: site/sensor/interval/parameter-count flow, exclusions, four-parameter cohort, three byte metrics with stated denominators, 1,296-B example made consistent | M10, M11, Table B | audit done; loader fix in Step 4 |
| 2 | Frame specification: complete 23-B packet layout (version, day/date + rollover, block id, K, message index, value count, padding, CRC, identity from operator metadata), worked encode/decode example, useful capacity after overhead | M5, M18 (CRC, out-of-range, identity, clock) | done (docs/FRAME_SPEC.md) |
| 3 | Self-contained days (keyframe) and the chained-anchor alternative; formal definitions E, F, G, certified span; proposition + proof of certificate correctness from received payloads only; quantisation-margin lemma incl. log-EC, saturation, held tail; adversarial tests | M3, M7, maths audit, E2 | done (docs/RECORD_MODEL.md); E2 loss runs in Step 4 |
| 4 | End-to-end codec: quantise, pack, RS over real bytes, erase, decode, unpack, reconstruct, certify; golden byte test vectors; replaces the mask-based path for ALL primary results; per-channel loader (Step 1 fix); G_cert primary, G_ok secondary; E2 runs (self vs chain under loss, bursts across midnight) | M4, M6, E1, E2, M10 | done on 2023 (docs/E2E_RESULTS.md); RQ2/RQ4 on bytes in Step 7 |
| 5 | Channel-blind configuration: one K (and r) per tier chosen on 2023 without knowing p or burst model; mismatch grid (assumed vs true p, both models); regret vs per-channel oracle; analytic MDS P_full check per K/Q and a Gilbert counterpart | M8, E3, Fig. C, maths audit | done (docs/ROBUST_RESULTS.md); byte confirmation with Step 6 |
| 6 | Stronger baselines: multi-day tag buffer rotation, periodic repetition with interleaving, robust fixed redundancy, fountain-style (LT/random linear) code; equal payload/quota/delay | M14, E7 | done (docs/BASELINES_RESULTS.md); multi-day tag rotation in Step 7 |
| 7 | Packet-level multi-day FIFO replay: real date tags, decoded payloads, anchors, missing days, deadlines, stale data, backlog > 7 d; delay measured at server recovery; burst at a day boundary example | M9, E4, Fig. D | done (docs/MULTIDAY_RESULTS.md); Fig. D example in Step 13 |
| 8 | Environmental use: daily min/max/mean, threshold exceedances (e.g. DO < 5 mg/L, T > limits, pH outside 6.5–8.5), rapid-change events, peak value and timing, false negatives and decision delay; one downstream model (e.g. daily DO metabolism/metric or exceedance duration) on exact vs reconstructed vs baseline records | M16, E5, Table C | done (docs/ENV_RESULTS.md) |
| 9 | Robustness: corruption (bit flips caught by CRC), out-of-range/clipping, clock drift/day rollover misassociation, outage days, sensor dropout; restrict claims where untestable | M18 | done (docs/ROBUSTNESS_RESULTS.md) |
| 10 | Complexity and resources: measured CPU/RAM of encoder for 5/10/15/60-min days; implement/verify a lower-memory selector or state the exact complexity; RS encode cost; energy per report from message count and modem datasheet (no hardware: stated) | M12, E8 | done (docs/RESOURCES_RESULTS.md) |
| 11 | Statistics: every outcome with its denominator; paired cluster bootstrap for all headline contrasts (esp. code vs repetition); multi-seed tier choice; seed and season-block uncertainty; all site-days where feasible (RAM 3.7 GB, <= 3 workers) | M17 | done (docs/STATS_RESULTS.md) |
| 12 | Freeze the revised plan, assemble and seal the new-river cohort, run confirmation once | M13, M15, E6 | todo |
| 13 | Manuscript: new title, abstract, claim language (no "regulatory-grade", no "guaranteed" without condition), contribution matrix (Table A), workflow figure (Fig. A), Figs B–D, Tables B–C, "pre-specified and checksum-frozen", seven families/eight tests, sample-size notes, related work (environmental compression, data-quality flags, uncertainty-aware telemetry, mission protocols, EM&S transparency), discussion limits, software availability (commit, environment, one command, code vs data licence, Weija restrictions) | M1, M2, M15, Sec. 7, Sec. 8 | todo |
| 14 | Venue check (EM&S if Step 8 shows clear environmental value; else Elsevier Internet of Things), Writing-rule sweep, Word copy | Sec. 2, Sec. 10 | todo |

## Item-to-step index

M1 13 · M2 13 · M3 3,7 · M4 4 · M5 2 · M6 4 · M7 3 · M8 5 · M9 7 · M10 1 · M11 1 · M12 10 · M13 12 · M14 6 ·
M15 12,13 · M16 8 · M17 11 · M18 2,9 · E1 4 · E2 3 · E3 5 · E4 7 · E5 8 · E6 12 · E7 6 · E8 10 ·
Table A 13 · Table B 1 · Table C 8 · Fig. A 13 · Fig. B 4 · Fig. C 5 · Fig. D 7 · Table 2 revision 13.

## Known limits that will be stated, not hidden

- No satellite hardware or field deployment: channels are synthetic; the paper says so.
- No microcontroller: resource figures come from instrumented host runs plus operation counts, labelled as such.
- Sensor accuracy (calibration, fouling) is outside the reconstruction bound; the bound is relative to the sensor record.

## Log

- 2026-10-25: plan written; Step 1 started.
- 2026-10-25: Step 1 audit done (docs/COHORT_AUDIT.md). Four-parameter median is 18 B, not 15 B; byte share
  approximately 1.85x the count share; loader drops channels with coarser native intervals or seasonal sensors.
  The per-channel data model moves into Step 4. Table B data ready in results/cohort/.
- 2026-10-25: Step 2 done (docs/FRAME_SPEC.md, src/p3/frame.py, tests/test_frame.py; 43 tests pass).
  3-B header (version, day mod 64, index, K, coded) + 20-B self-parsing coded unit (CRC-16 with context,
  segments with day offset / first planned position / last / bound flags, 24-bit values). 5 values per
  23-B message (was 7); 3 per 19-B. Operator supplies device ID and reception time; raw format has no
  integrity flag. Kinéis facts to re-confirm with Kinéis before submission. Next: Step 3.
- 2026-10-25: Step 3 done (docs/RECORD_MODEL.md, src/p3/record.py, tests/test_record.py; 92 tests pass).
  Separate quantities E(S), b, E(S,A), F, Phi, G_cert (primary, server-verifiable), G_ok (oracle), c.
  Certificate rule from received positions only; Proposition 1 (soundness) and Corollary 1 (full iff all
  arrived) under assumptions (a)-(e); exhaustive loss-pattern tests. Encoder is quantisation-exact; the
  quantiser grid is now decimal (T 0.01, DO 0.005, pH 0.002; EC log), so USGS readings travel exactly and
  the 0.975 margin is withdrawn. Self-contained days adopted: +0.25 values/day over chaining (2.6%).
  Honest four-parameter cost on 2023: median 27 B (draft 18 B); the draft's saving came mostly from sending
  nothing for 39% of channel-days on the strength of an anchor no server holds. Next: Step 4.
- 2026-10-25: Step 4 done on development data (docs/E2E_RESULTS.md; 109 tests pass). Per-channel loader
  (four-parameter days 2023 10,342 / 2024 11,168, 38 sites each). Byte-level pipeline with golden vectors.
  Q = 6, p = 0.3, 2023: G_cert code 0.780 / repetition 0.636 / reliable 0.116 / tag 0.105 / every-k 0.040
  (bursty: 0.679 / 0.647). Code now clearly beats repetition under independent loss. E2: self-contained beats
  chained in G_cert by 0.03-0.09 although chaining saves 0.8 values/day. RQ1 2023: 27 B median.
  Tag baseline weakened by the 5-value frame: strengthen in Step 6. Next: Step 5 (channel-blind K).
- 2026-10-25: Step 5 done (docs/STEP5_PLAN.md fixed beforehand; docs/ROBUST_RESULTS.md; 179 tests pass).
  New proposed design: record-first code (K = D1 per day, rest parity; Proposition 2: optimal among unit-level
  linear designs on every erasure channel, no channel knowledge). Exact probabilities (analytic.py) agree with
  the byte pipeline. Q = 6, 2023 test days: code 0.905 iid p0.3 / 0.833 bursty; record-first repetition
  0.802 / 0.806 (nearly equal under long bursts); fixed-K channel-blind regret up to 0.108; mismatch up to 0.272.
  Lesson: the first run was slowed by an exponential dict recursion; vectorised (30x). Next: Step 6 baselines.
- 2026-10-25: Step 6 done (docs/BASELINES_RESULTS.md; 187 tests pass). Fountain (systematic random linear)
  code ties RS; tag deficit is content (0.59) more than policy (0.10); interleaving +0.11 under bursts; code vs
  interleaved repetition +0.105 iid / +0.026 bursty / +0.005 long bursts (repetition slightly more partial
  certificates). Bytes vs exact: mean |diff| 0.0014 over 525 cells. A bug in analytic.p_units (tag orders that
  skip a unit counted as delivered) was found by a new test and fixed; Step 5 tag rows corrected and noted.
  Next: Step 7 (packet-level multi-day FIFO, RQ2/RQ4 on bytes, multi-day tag rotation).
- 2026-10-25: Step 7 done (docs/STEP7_PLAN.md fixed beforehand; docs/MULTIDAY_RESULTS.md; 197 tests pass;
  6,270 byte-checked replays, no mismatch). Buffering does NOT help once the record is honest (FIFO <= daily code
  at Q >= 6, much worse at Q = 1). RQ2 honest: Q = 6 gives G7 >= 0.9 at 13/19 test sites (iid 0.3) and 5/19
  (bursty); Q = 12 at 19/19. 7-day cyclic rotation beats the daily code under long bursts (G7 0.800 vs 0.769) but
  is slower (G1 0.245 vs 0.769): coding across days = future work. RQ4: 17/19 sufficient, 19/19 within one tier.
  Draft H2/H2b cannot be claimed. Next: Step 8 (environmental use).
- 2026-10-25: Step 8 done (docs/STEP8_PLAN.md confirmed by the user; docs/ENV_RESULTS.md; 221 tests pass).
  Three-valued (certified) decisions: 0 wrong over 10,342 days; record decides 97.5% (DO), 96% (pH), 98.5%
  (7DADM) of days with perfect delivery vs 13-32% for periodic/tag. Record catches EC pulses (11% missed vs
  76-84%). BUT naive near-threshold pH exceedances are missed more by the record (37% vs 8-10%) and diel shape
  (peak time, DO range) is not better than periodic samples. Future work: decision-aware tolerance.
  Next: Step 9 (robustness: corruption, out-of-range, clock, outages).
- 2026-10-25: Step 9 done (docs/STEP9_PLAN.md fixed beforehand; docs/ROBUSTNESS_RESULTS.md; 238 tests pass).
  Fixed: out-of-range readings are censored (previously one glitch voided the day); hardened receiver (majority
  header, CRC-verified units, retried decoding). Zero false certificates under corruption up to bit-error rate
  1e-2; G_cert -0.007 at 1e-4, -0.083 at 1e-3 (Q = 6). Glitches cost approximately 2.35 values each. Outages do
  not propagate. Clock resync within 87 to 521 days (20 ppm); a MAC would cost 20% of capacity.
  Next: Step 10 (complexity and resources).
- 2026-10-25: Step 10 done (docs/RESOURCES_RESULTS.md; 468 tests pass). Table-free exact encoder
  (stream.py; O(n^2) time, O(n) memory) reproduced all 12,674 cached 2023 plans exactly. The draft's linear-time
  claim is withdrawn. Host: 5-min day 4.9 s / 42 kB vs table 11.9 s / 7.9 MB. MCU estimates: approximately
  14 kB RAM, 0.56 s at 48 MHz for a 5-min day; encoding approximately 0.1% of the 15 J/day transmission energy.
  Next: Step 11 (statistics).
- 2026-10-25: Step 11 done (docs/STATS_RESULTS.md). Exact full-cohort G_cert (cohort_exact.py, 10,342 days);
  site-clustered paired bootstrap for all headline contrasts; denominators table. Q = 6: code 0.905
  (0.873-0.934) iid 0.3; code - repetition 0.092 / 0.024 / 0.005 (iid / bursty / long bursts), all intervals > 0.
  RQ2 exact: 25/38 sites (iid), 9/38 (bursty) at Q = 6; 38/38 at Q = 12. RQ4 by pilot month: 87.6% sufficient
  (bursty planning 79.6%; December pilots worst). Next: Step 12 (freeze, new sealed cohort, confirmation).
- 2026-10-26: Step 12 prepared, awaiting the authors' approval. Draft plan docs/CONFIRM2_PLAN.md (hypotheses
  C1-C8 with interval-based thresholds). New cohort selected from metadata only: 36 USGS sites in five regions not
  among the 39 (results/confirm2/selection.csv); 2024 downloaded with the unchanged Paper 2 tools, cleaned, and
  sealed unread (data/{raw,clean}/usgs_new2024.md5). Runner src/p3/confirm2.py dry-run on a dev subset.
  Freeze: authors commit and tag `confirm2-freeze`, then `python -I src/data/freeze2.py confirm2-freeze`.
