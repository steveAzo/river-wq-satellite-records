# Paper 3 study plan (DRAFT for freezing)

**Status:** FROZEN 2026-10-23 (checksums in `docs/FREEZE.md`). The hypotheses in Section 7 are binding. Every later change is logged in Section 10 as a deviation, with its reason.

**Decision behind it:** the user, 2026-10-23, after scoping §F. Scope = the setting-and-evidence paper; working venue = a Q1 environmental-informatics journal (Section 1). The Prof is to be told that the venue changed from IEEE IoT-J.

**Standalone rule:** Papers 1 and 2 are not cited. All methods are defined here from primary sources.

---

## 1. Paper

**Working titles** (statements, not questions):
1. A Regulatory-Grade River Water-Quality Record in Six Satellite Messages a Day
2. Guaranteed Water-Quality Records over Byte-Limited Satellite IoT: Cost, Delivery Design, and Plan Sizing for Remote Rivers

**Venues:**
- **Working target:** Environmental Modelling & Software (Elsevier, JCR Q1). Framed as decision support for sizing and operating remote monitoring telemetry; the software is released.
- **Alternative:** IEEE Sensors Journal (JCR Q1); check its over-length page charges first.
- Both quartiles come from third-party aggregators; **confirm in Clarivate JCR**.

**Claim in one sentence:** for remote rivers reachable only by satellite IoT, a record that meets the USGS "Excellent" accuracy rating costs a median of a few tens of bytes per day. It can be delivered with a stated guarantee over a one-way, lossy, quota-limited link, if the node sends a tolerance-guaranteed approximation protected by an erasure code. Raw periodic reporting, designs built for reliable links, and current satellite-tag practice do markedly worse at the same quota.

---

## 2. Research questions

1. **RQ1, cost:** how many bytes per day does a record within the USGS-Excellent tolerance require, and how does that need vary across sites, seasons, parameters, sampling intervals and event days?
2. **RQ2, sufficiency:** which satellite plan tiers (messages per day) can carry that record, and with what buffering delay?
3. **RQ3, delivery over a one-way link:** given a plan tier and unknown message loss, which delivery design maximises the share of days whose record is guaranteed, compared with the designs used in practice?
4. **RQ4, sizing:** can a site's required plan tier be chosen from a short pilot record?

---

## 3. Data

**Development set (used for every design choice):** 39 USGS sites, 2023, with T, SC, DO and pH; 15- or 30-minute intervals; approved data only (`data/clean/usgs/`).

**Confirmation set (sealed 2026-10-23; checksums in `data/clean/usgs_2024.md5`):**
- the same 39 sites, 2024 (`data/clean/usgs_2024/`; copied from Paper 2's public USGS downloads, 2026-10-23);
- InWaterSense node 1 (Kosovo; Ahmedi, Mendeley Data, CC BY 4.0), the noisy low-cost counter-case;
- Weija (Ghana; the Prof's deployment), the tropical low-cost case. **Confirm that permission covers Paper 3.**

None of these is opened by any Paper 3 script before the plan is frozen.

**Low-cost cases:** InWaterSense and Weija were not used for any Paper 3 design choice either. Their only prior use is in scoping E2 (InWaterSense) and the descriptive record in E11. To check: E11 used USGS only.

---

## 4. Definitions

**Tolerances:**
- **Primary, USGS TM 1-D3 Table 18 "Excellent"** (Wagner et al. 2006): T ±0.2 °C; SC ±3%; DO ±0.3 mg/L or ±5%, whichever is greater (applied per value, not as the scoping simplification); pH ±0.2.
- **Sensitivity, "Good":** T ±0.5 °C; SC ±10%; DO ±0.5 mg/L or ±10%; pH ±0.5.

**Server reconstruction:** linear interpolation through the delivered values, anchored on the last delivered value before the day, holding the last value. A "within tolerance" value is one whose reconstruction error is within the tolerance.

**Guaranteed day:** every value of every parameter in the day is within tolerance.

**Certified span:**
- Delivered values carry sequence numbers, so the server knows which planned values of a tolerance-guaranteed set arrived.
- A span between two consecutive planned values that both arrived is certified within τ × tolerance.
- The server reports the certified share of time. This is the operational form of the guarantee, and it works without feedback.

**Node encoding:** the minimum-number-of-values set (min-#, Imai & Iri 1988) at a common τ across parameters. τ is the smallest value whose set fits the available values.

**Message model:**
- **Primary: 23-byte messages**, from the Kinéis KIM1 datasheet (`papers/standards/Kineis_KIM1_datasheet.pdf`): "Data transmission: One-way, Transmission only"; typical payload 23 bytes; 400 bit/s; transmission < 1 s. Each message holds a 1 B header (day index and sequence) plus 7 values × 3 B (2 B value plus 1 B slot and parameter index).
- **Sensitivity: 19-byte messages** (6 values), the "standard message" on the Kinéis service pages (dated 2024, now behind a sign-in).
- **Plan tiers:** 1, 6, 12, 24 and 96 messages per day, also from those pages. **To confirm**, or present them as illustrative tiers.
- The link is one-way: no acknowledgements.

**Loss models:**
- independent loss, p ∈ {0.1, 0.3, 0.5};
- bursty Gilbert–Elliott loss with the same means (mean burst length 3 messages).

Values to be justified from direct-to-satellite IoT literature (e.g. [38] Yu et al. 2026; [34] Tondo et al. 2021); sweep if no measured value exists.

**Energy:** KIM1 datasheet: 500 mA at 5 V (typical) in transmit mode, transmission < 1 s, idle 5 mA, off < 2 µA. Per message: 2.5 W × airtime, where airtime = (23 B × 8 + framing) / 400 bit/s ≈ 0.5–1 s, i.e. about 1.2–2.5 J. Daily energy per design follows.

---

## 5. Designs compared (identical messages per day)

| Name | What the node sends | Represents |
|---|---|---|
| raw_periodic | Every k-th reading, all parameters, k set to fit the quota | Default practice |
| srdl_style | A fixed number of piecewise-linear points per day (broken-stick, top-down), messages re-sent pseudo-randomly from a buffer of recent days | Biologging satellite-tag practice (Boehme 2009; Photopoulou 2015) |
| reliable_opt | min-# at the smallest τ fitting the quota, each message once | Designs for reliable links (SBR-type, Deligiannakis et al. 2006) |
| repeat_r | min-# at a coarser τ, each message r times, r tuned per loss on the development set | Blind repetition |
| **mds_K (proposed)** | min-# at the τ fitting K messages, protected by a systematic Reed–Solomon code across the Q messages (any K recover all) | Proposed design |
| **mds_K + buffer (proposed)** | As above, with surplus capacity on low-need days used to deliver earlier days' residual values | Proposed design with temporal pooling |

The parameters tuned on the development set (r, K as a function of loss and tier, buffer policy) are frozen and then applied unchanged to the confirmation set.

---

## 6. Metrics

- **G, guaranteed share:** the share of site-days whose whole record is within tolerance (primary).
- **C, certified share:** the share of time certified by the server.
- **Worst and mean normalised error.**
- **Delay:** for buffered designs, the time until a day becomes guaranteed.
- **Messages and energy per guaranteed day.**
- **RQ4:** the tier chosen from the first 28 days vs the smallest sufficient tier in hindsight.

---

## 7. Hypotheses for the confirmation set

**The development numbers that informed them** (2023, USGS-Excellent, scoping E11–E13b, with 19-B messages and a scalar DO tolerance; to be recomputed with the final 23-B, per-value implementation before freezing):
- median need 36 B/day, 3.1% of raw;
- 6 messages/day plus a buffer is sufficient at 38 of 39 sites;
- at p = 0.3: G = 0.88 (MDS), 0.80 (tuned repetition), 0.37 (reliable-link design).

**Thresholds** (deliberately looser than the development values, to allow for year-to-year change):
- **H1 (RQ1):** the median daily need over 2024 USGS site-days is at most 5% of raw (development: 2.1%, i.e. 18 B/day; p99 111 B; at most 11 messages/day).
- **H2 (RQ2; restated on development evidence, before freezing):** with a buffer and the tuned code, under independent loss p = 0.3, at least 75% of the 2024 USGS sites have at least 90% of their days guaranteed within 7 days at 6 messages/day (development: 35/39 = 90%).
- **H2b (RQ2):** under bursty loss p = 0.3, the same holds for at least 85% of sites at 12 messages/day (development: 36/39 = 92%). At 6 messages/day under bursty loss, only 18/39 development sites met it; this is reported as a limitation, not a hypothesis.
- **H3 (RQ3):** at p = 0.3, independent loss, 6 messages/day, the median G of mds_K is at least 2 × that of reliable_opt (2024 USGS).
- **H4 (RQ3):** at p = 0.3, independent loss, 6 messages/day, mds_K exceeds srdl_style in median G by at least **M = 0.25** (development margin 0.47, `results/dev/`; set 2026-10-23 before any confirmation data were opened).
- **H5 (RQ3; revised on development evidence, before freezing):** at 6, 12 and 24 messages/day and p ∈ {0.3, 0.5}, both mds_K and repeat_r exceed reliable_opt in mean G by at least 0.2, under independent and under bursty loss. mds_K is not claimed to beat repeat_r: under bursty loss they tied on the development set (6 messages/day, p = 0.3: 0.81 vs 0.81).
- **H6 (RQ4):** the pilot-based tier choice (first 28 days, safety factor 1.0 tuned on development sites) is sufficient at at least 80% of sites, and over-provisions by at most one tier at at least 80% of sites (development held-out sites: 0.89 and 1.00).
- **H7 (counter-case, descriptive):** InWaterSense's median need is at least 3 × the USGS median. Its noise makes guaranteed records expensive, which is reported as a limit, not a failure.
- **Weija:** reported descriptively under the same metrics, with its data-quality caveats.

---

## 8. Implementation order

1. Verify the message model, plan tiers and energy (Section 9).
2. Implement and test the node encoder (min-# at τ, packing, sequence numbers), the RS(Q, K) code (verified by tests), the loss channels, the server decoder and certification, and the srdl_style baseline. Unit tests for every component.
3. Run every design on the development set and tune r, K and the buffer policy. Set M (H4).
4. **Freeze this plan:** commit hash, date and the Prof's confirmation.
5. Open the confirmation set once. Run everything; judge H1–H7 as pre-registered; report failures as failures.
6. Sensitivity analyses: "Good" tolerance; 5/30-minute intervals; bursty loss; message size of 23 B (KIM1 datasheet value).

---

## 9. To settle before freezing

- [x] Message size and one-way link: from the KIM1 datasheet (23 B, one-way); 19 B as sensitivity.
- [x] Plan tiers: not confirmable (Kinéis pages behind a sign-in). The paper presents 1/6/12/24/96 messages/day as illustrative tiers; message size and the one-way link rest on the KIM1 datasheet.
- [x] KIM1 transmit energy: 500 mA at 5 V, < 1 s per message.
- [x] Message loss: no measured Kinéis loss rate was found. The direct-to-satellite IoT literature models erasure probabilities over a wide range (e.g. 0.01–0.9 with on–off fading, Tondo et al. 2021 [34]; analytic frame success under replication, Rathi & Borkotoky 2025 [41]). Hence the sweep p ∈ {0.1, 0.3, 0.5}, independent and bursty.
- [x] Weija permission for Paper 3: yes (user, 2026-10-23).
- [x] srdl_style implemented and run on the development set; M = 0.25 set (Section 7).
- [x] Venue: the Prof agreed to Environmental Modelling & Software (user, 2026-10-23); confirm the JCR quartile at submission.

---

## 9b. Development results (2023, recorded 2026-10-23; `src/p3/run_dev.py`, `results/dev/`)
- **Sample:** up to 20 site-days per site (780), split into tuning and reporting halves.
- **Settings:** 23-B messages, USGS-Excellent per-value tolerances.
- **Mean G at 6 messages/day, p = 0.3:**
  - independent loss: mds 0.897, repeat 0.853, srdl_style 0.424, reliable_opt 0.340, raw_periodic 0.275;
  - bursty loss: mds 0.812, repeat 0.807, reliable_opt 0.468, srdl_style 0.411, raw_periodic 0.321.
- **At 1 message/day:** no design exceeds 0.56 (mds ≈ reliable_opt; coding cannot help with one message). This motivates RQ4, plan sizing.
- **At 12 and 24 messages/day:** mds 0.94–0.997; repeat 0.86–0.99; srdl_style 0.35–0.81; reliable_opt about 0.2–0.4 (the reliable-link design degrades with loss even at large quotas).
- **RQ1 (all 10,978 site-days; `src/p3/need.py`):** median need 18 B/day (2.1% of raw), p90 45 B, p99 111 B, max 216 B; in 23-B messages: median 1, p90 3, p99 6, max 11.
- **RQ2 (`src/p3/pooling.py`):** share of days guaranteed within 7 d, median over sites (independent loss p = 0.1/0.3/0.5):
  - 1 message/day: 0.43/0.32/0.23;
  - 6 messages/day: 0.98/0.93/0.88;
  - 12 messages/day: 1.00/1.00/0.98.
  - Sites with ≥ 0.9 at p = 0.3, independent / bursty: 1/1 (Q = 1), 35/18 (Q = 6), 37/36 (Q = 12), 39/39 (Q = 24). The median delay of guaranteed days is 1 day.
- **RQ4:** safety factor 1.0. On held-out development sites, the choice was sufficient at 0.89 and over-provisioned by at most one tier at 1.00.

## 10. Deviations log

Frozen 2026-10-23. Confirmatory analyses use, unchanged:
- the tuned design parameters in `results/dev/dev_tuning.json`;
- the RQ4 safety factor 1.0 (`results/dev/sizing_tuning.json`);
- the code in `src/p3/` as checksummed.

Deviations: none to the plan or the frozen code. For the confirmation, three wrapper scripts were added that call the frozen modules unchanged:
- `src/p3/lowcost.py`: input conversion for InWaterSense and Weija, including Benson–Krause DO conversion and dropping flagged values;
- `src/p3/run_confirm.py`: frozen RQ3 parameters, no re-tuning;
- `src/p3/confirm_pooling.py`: frozen K and safety factor applied to every site.

**Confirmation completed 2026-10-23: all of H1–H7 passed.** See `docs/CONFIRM_RESULTS.md`.
