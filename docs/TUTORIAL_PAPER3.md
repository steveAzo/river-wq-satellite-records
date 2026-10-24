# Paper 3 from the ground up: a tutorial

*Written 2026-10-24, after the confirmation run, the v0.1 draft, and the Q1 audit that produced v0.2. It assumes you know nothing about this project beyond Papers 1 and 2, and it re-explains every idea it uses.*

**How to read it:**
- Read it in order.
- Parts 1–3 build the concepts, with small worked examples.
- Part 4 tells the story of what we did and found, including the dead ends and the mistakes.
- Part 5 is the paper in one page.
- Part 6 tests you (answers follow the questions).
- Parts 7–8 are the glossary and the file map.

**Every number** comes from our result files or from the code; Part 8 gives the paths. When you can do the exercises in Part 6 without looking, you understand the paper well enough to defend it.

**The paper:** "A regulatory-grade river water-quality record in a few satellite messages a day", Kofi Sarpong Adu-Manu and Stephen Kwaku Azongo, aimed at Environmental Modelling & Software (Elsevier, Q1).

---

## Part 1. The problem, in plain words

### 1.1 The setting

- **Rivers under pressure are often out of coverage.** In Ghana, illegal small-scale gold mining (galamsey) has degraded rivers such as the Fena in forested catchments where there is little or no mobile coverage (Duncan, 2020).
- **Low-cost water-quality nodes work** (Weija in Ghana, InWaterSense in Kosovo), but they send their data over the mobile network. Where there is no network, they cannot report.
- **Satellite IoT now reaches anywhere.** A small module (the Kinéis KIM1, 3 g, 5 V) sends short messages straight to low-orbit satellites.

### 1.2 The catch: you buy messages, not bandwidth

From the KIM1 datasheet (`papers/standards/Kineis_KIM1_datasheet.pdf`):
- **Typical payload: 23 bytes per message**, about as much as 23 typed characters.
- **400 bit/s, under 1 second per transmission, 500 mA at 5 V while transmitting.**
- **One-way: transmission only.** The node never hears back, so it never learns whether a message arrived.
- **Plans sell a few to a few dozen messages per day.**

**A node that sends everything** (4 parameters every 10 minutes, 2 bytes per value plus a 1-byte time stamp per cycle) produces 144 × 9 = **1,296 bytes per day**, which is about **62 messages**. That is far more than a cheap plan allows.

### 1.3 The research question

> **What does a credible river record cost in bytes, and how do you deliver it over a link that sells a handful of short messages a day, loses some of them, and never tells you which?**

Two words in that question need a precise meaning:
- **"Credible"**: we borrow the regulator's own definition (Part 2.2), so the answer means something to an agency.
- **"Deliver"**: the record must survive message loss without any feedback (Part 2.6).

The paper splits the question into four research questions:
1. **RQ1, cost:** how many bytes per day does a guaranteed record need, and how does that vary across sites, seasons, and parameters?
2. **RQ2, buffering:** which plans carry the record if the node may spill demanding days into quieter ones, and with what delay?
3. **RQ3, delivery design:** which way of packing and sending the record guarantees the most days over a lossy one-way link?
4. **RQ4, sizing:** can an agency pick the right plan from a short pilot record?

---

## Part 2. The concepts you need (with tiny examples)

### 2.1 The four parameters and why they move

| Parameter | Unit | What drives it | Typical daily behaviour |
|---|---|---|---|
| Temperature (T) | °C | Sun, air temperature, flow | Smooth daily (diel) rise and fall of 1–5 °C |
| Specific conductance (SC) | µS/cm | Dissolved salts; rain dilutes, runoff and discharges raise it | Mostly slow; jumps after rain or a discharge |
| Dissolved oxygen (DO) | mg/L | Photosynthesis by day, respiration by night | Strong diel cycle in summer: a night trough, a steep morning rise |
| pH | units | Linked to DO through CO₂ uptake by plants | Gentle diel cycle |

**"Diel"** means the 24-hour day–night cycle. It matters because it makes summer days more expensive to record (Part 4.7).

### 2.2 The USGS accuracy rating: our definition of "credible"

The US Geological Survey (USGS) rates continuous water-quality records as excellent, good, fair, or poor (Wagner et al., 2006, Techniques and Methods 1-D3). We use the limits of an **excellent** record as the tolerance:

| Parameter | Excellent | Good (used only in a sensitivity analysis) |
|---|---|---|
| Temperature | ±0.2 °C | ±0.5 °C |
| Specific conductance | ±3% of the value | ±10% |
| Dissolved oxygen | ±0.3 mg/L or ±5%, whichever is greater | ±0.5 mg/L or ±10% |
| pH | ±0.2 units | ±0.5 |

**Why this choice is clever:** a reviewer cannot say "you picked a tolerance that suits you". It is the regulator's own standard, written before this study existed.

**Each reading has its own tolerance** δ. For temperature it is always 0.2 °C. For conductance it depends on the value: a reading of 500 µS/cm has δ = 15 µS/cm. For DO at 8 mg/L, 5% is 0.4 mg/L, which is greater than 0.3, so δ = 0.4 mg/L.

### 2.3 What the server does with the values it receives

The server holds the last reading of the previous day (the **anchor**). For each parameter it draws **straight lines** between the values it received, starting from the anchor, and **holds the last value** to the end of the day. This is linear interpolation.

**The error of each reading** is measured in tolerances:

```
e(t) = |true reading − reconstructed value| / δ(t)
```

**A day is guaranteed** when e(t) ≤ 1 for every reading of every parameter, so the whole reconstructed day stays inside the USGS band. Because the newest reading is part of the day, the current value is guaranteed too.

**Tiny example.** Temperature readings (°C) at five times: anchor 20.0, then 20.1, 20.4, 20.6, 20.7.
- Send only the last value (20.7): the line from 20.0 to 20.7 gives 20.175, 20.35, 20.525 at the middle three times. Errors: |20.1 − 20.175| = 0.075; |20.4 − 20.35| = 0.05; |20.6 − 20.525| = 0.075. All are below 0.2, so **one value** guarantees this stretch.
- If the middle reading were 20.9 instead of 20.4, the line would miss it by 0.55, and you would need to send it too.

### 2.4 The encoder: the fewest values that keep the day inside the band

**The problem:** for each parameter, pick the fewest readings such that interpolating through them keeps every e(t) ≤ τ, where τ is a level (τ = 1 means "within tolerance").

- This is the classical **min-# problem** of polygonal approximation. Imai and Iri (1988) solved it exactly, in time linear in the number of readings. Our code uses an equivalent dynamic programme that runs in quadratic time (`src/p3/pla.py`); it gives the same answer.
- The **guaranteed set** of a day is the min-# set at τ = 1. Its size is the day's **need**: RQ1 measures it.
- **The encoder is not our invention**, and the paper says so. Our contribution is what it costs on real rivers under a regulatory tolerance, and how to deliver its output over a one-way link.

**When there is room for more values** (budget k values), the encoder uses one **common level τ** for all parameters: the smallest τ such that the four min-# sets together fit in k values. A smaller τ means a tighter record. The code finds it by binary search over the candidate τ values.

### 2.5 Bytes and messages

- **One value = 3 bytes = 24 bits:** 2 bits say which parameter, 9 bits say which time slot (up to 512 slots, enough for 5-minute sampling, which has 288), and 13 bits carry the reading.
- **The 13-bit reading** is quantised linearly for T (−5 to 40 °C), DO (0 to 25 mg/L), and pH (0 to 14), and logarithmically for SC (1 to 100,000 µS/cm). The worst rounding error is 2.3% of the SC tolerance and below 1.4% of the others. An encoder that aims at 0.975 of the tolerance therefore stays inside it even after rounding.
- **One message = 23 bytes:** a 1-byte header (3-bit day index, 5-bit sequence number) and 7 values. So "1 message" = 21 bytes of values.
- **Plans** of 1, 6, 12, 24, and 96 messages per day were evaluated. They are illustrative tiers, because the providers' price lists are behind sign-ins.

### 2.6 The one-way lossy link

The node sends Q messages per day; each arrives or not, and the node never learns which. We do not know the real loss rate of the service (no published measurement exists), so we **swept** it:
- **Independent loss:** each message is lost with probability p ∈ {0.1, 0.3, 0.5}.
- **Bursty loss (Gilbert channel):** the channel switches between a good state (nothing lost) and a bad state (everything lost); bad spells last 3 messages on average, and the long-run loss is the same p. Bursts are harder, because consecutive messages die together.

### 2.7 Protecting the record: repetition versus an erasure code

You can protect data you cannot resend in two ways.

**Repetition:** send every message r times.
- Simple. A message is lost only if all r copies are lost: at p = 0.3 and r = 3, probability 0.3³ = 0.027.
- Costly: with 6 messages a day and r = 3, only 2 distinct data messages (14 values) fit.

**Erasure code (Reed–Solomon):** turn K data messages into Q messages such that **any K of the Q** recover all K.
- The smallest example uses XOR. Data messages A and B, plus parity P = A ⊕ B (bitwise exclusive or). Any two of {A, B, P} give back both: A = B ⊕ P, B = A ⊕ P. That is K = 2 of Q = 3.
- Reed–Solomon codes over the field GF(2⁸) do the same for any K ≤ Q ≤ 255 (`src/p3/rs.py`). Codes with the "any K of Q" property are called **MDS** (maximum distance separable). Ours is **systematic**: the K data messages are sent as they are, so if fewer than K arrive, the server still uses the data messages that did.

**The trade-off that RQ3 measures**, at 6 messages a day and p = 0.3 (the tuned settings):

| Design | Distinct values carried | Probability the whole record arrives |
|---|---|---|
| Code, K = 3 of Q = 6 | 21 | P(≥ 3 of 6 arrive) = 0.930 |
| Repetition, r = 3 (2 data messages) | 14 | (1 − 0.3³)² = 0.947 |
| Sent once (6 data messages) | 42 | 0.7⁶ = 0.118 |

- **The code carries 50% more values than repetition** at almost the same safety, so it can use a tighter τ. When the day needs more than 14 values (noisy records), repetition simply cannot guarantee it; that is why the code won clearly on the low-cost sites.
- **Sending everything once** gives the tightest record but almost never arrives whole. It still guarantees some days, because losing a few values of a very tight record can leave the rest within tolerance.

### 2.8 The five designs compared (all use at most Q messages a day)

| Design | What is sent | Guarantee? |
|---|---|---|
| Every k-th reading | Evenly spaced readings, k set to fill the plan | No |
| Tag practice | A fixed number of "broken-stick" points per parameter (largest absolute deviation first), sent pseudo-randomly, as satellite-tracked seals and turtles do over Argos (Boehme 2009; Photopoulou 2015) | No |
| Reliable-link design | The guaranteed set at the smallest τ that fills all 7Q values, each message once | Yes if all arrive |
| Repetition | The guaranteed set at the smallest τ that fills 7⌊Q/r⌋ values, each message r times | Yes |
| Erasure code (proposed) | The guaranteed set at the smallest τ that fills 7K values, plus Q − K parity messages | Yes |

**Why the "reliable-link design" matters:** it is what the best earlier work (SBR, Deligiannakis et al., 2007) would do, because it is optimal when nothing is lost. Showing that it collapses on a one-way link is one of the paper's main findings.

### 2.9 Certification without feedback

The sequence numbers tell the server which planned values arrived. Between two consecutive planned values that **both** arrived, the encoder promised every reading within τ × tolerance; therefore, the server can **certify** that span, even though nobody ever confirmed anything. The certified share was 91% of readings with the code and 70% with the reliable-link design.

### 2.10 Buffering across days (RQ2)

Days differ: a quiet winter day may need 1 value, a stormy summer day 60. A node can put each day's guaranteed set into a **first-in, first-out backlog** and send one coded block per day from the oldest data first. Quiet days then carry the overflow of busy days.
- **Delay** = days until a day's last block was sent (1 = sent the next day).
- **Target:** at least 90% of a site's days guaranteed within 7 days.
- A lost block is never resent (the node cannot know it was lost).

### 2.11 Choosing a plan from a pilot (RQ4)

An agency must buy a plan before it knows the river. The rule tested: record 28 days, simulate the buffered design on them, and choose the smallest plan that meets the target there (independent loss, p = 0.3). Then check that plan against the rest of the year. A safety factor on the pilot needs was tuned on 2023; it came out at 1.0 (no inflation).

### 2.12 Pre-registration: why the hypotheses are believable

A study that tunes its designs and then tests them on the same data will look better than it is (the "garden of forking paths"). We prevented that:
1. **Development set:** USGS 2023 (39 sites, 10,978 site-days). Every choice (K, r, the tag-practice share, the safety factor) was tuned here, on half of a 780-site-day sample, and checked on the other half.
2. **Sealed confirmation set:** USGS 2024, plus the two low-cost deployments. Its files were checksummed (MD5) on download and not opened.
3. **Freeze:** the plan (`docs/STUDY_PLAN.md`), the tuned parameters, and the code were frozen and checksummed (`docs/FREEZE.md`), and seven hypotheses (H1–H7) with numeric thresholds were written down.
4. **Confirmation:** the seal was verified (39/39 checksums), the 2024 data were opened once, and the frozen code was run unchanged. All seven hypotheses passed (`docs/CONFIRM_RESULTS.md`).

Anything run afterwards (the sensitivity analyses, the bootstrap intervals) is labelled **exploratory** in the paper.

### 2.13 Statistics you will meet

- **G (guaranteed share):** for one site-day and design, the share of 30 random loss draws in which the whole day stayed within tolerance. Averaged over site-days, it is the share of guaranteed site-days.
- **Mean versus median G:** a site-day's G takes values like 28/30, so medians jump in steps of 1/30. H3 and H4 were pre-registered on medians, and the paper reports means too.
- **Paired comparison:** on how many site-days was the code better than design X? (91% vs the reliable-link design, 87% vs tag practice.)
- **Site-clustered bootstrap:** days from one site resemble each other, so they are not independent evidence. We resampled the 39 **sites** with replacement 2,000 times, recomputed each statistic, and took the middle 95% as the interval. Resampling days instead would give falsely narrow intervals.

---

## Part 3. How the pieces fit: the paper's logic

```
USGS "excellent" tolerance (regulator's definition, Part 2.2)
        │
        ▼
Encoder: fewest values within tolerance (min-#, Part 2.4)
        │
        ▼
RQ1: a guaranteed day costs a median of 15 B (1.8% of the raw readings);
     63% of days fit in ONE 23-B message; the worst day needed 10 messages;
     summer and temperature are the expensive cases
        │
        ▼
But the link is one-way and loses messages (Part 2.6) ──► RQ3: how to send it?
   - sent once (the reliable-link optimum): only 34% of days survive at p = 0.3,
     and more messages do not fix it (38% at 24 msg/day)
   - fixed points sent at random (tag practice): 43%
   - guaranteed set + erasure code: 89%; + repetition: 85%
        │
        ▼
RQ2: days differ, so buffer the overflow: 6 msg/day meets the 90%-in-7-days target
     at 35/39 sites (independent loss); bursty loss needs 12 msg/day
        │
        ▼
RQ4: a 28-day pilot picks an adequate plan at 85% of sites
        │
        ▼
Guidance: send the guaranteed record, protect it, size the plan for the loss process,
pilot with a seasonal margin, do not assume temperature is cheap.
```

---

## Part 4. The story: what we did, why, and what we found

### 4.0 Where Paper 3 came from

The starting point was proposal 3 in `proposals.md`, aimed at IEEE Internet of Things Journal: send the most valuable data first when a LoRaWAN link is scarce. We scoped it in four passes (`PAPER3_SCOPING.md`) before writing a line of the paper. **Lesson (same as Paper 2):** a proposal is a starting hypothesis; the data and the literature reshape it.

### 4.1 Scoping pass 1: "send the most valuable value first"

- **Idea A:** order a node's values so that any prefix gives the best possible record ("anytime" order).
- **Killed by prior art and a fair baseline.** HIRE (Barbarioli et al., 2023) already gives progressive, error-bounded encodings. A data-blind order (newest slot first, then a bit-reversed stride) came within 1–4 percentage points of the clever order on average error. **Lesson (the stride lesson from Paper 2):** always test against the strongest simple baseline.
- **What survived:** data-awareness pays on the **worst case**. At 10% of the raw budget, the whole day was within tolerance on 69% of site-days with a greedy, data-aware order against 15% with the data-blind one.

### 4.2 Pass 2: pooling a budget across nodes, and what is scarce

- **Pooling:** on real river chains of 2–5 sites, sharing one budget by a common τ ("water level") kept the whole chain within tolerance on 85% of chain-days, against 2.5% for equal data-blind shares.
- **Satellite contacts are not scarce.** An orbit propagation (scoping E4) gave about 40 Kinéis passes per day above 25° elevation over Weija, each about 4.5 minutes long. **The scarce thing is the message quota.** This corrected our first premise.
- **LoRaWAN is not scarce for smart senders.** The Things Network's fair-use limit (30 s of airtime a day) allows about 510 bytes a day even at SF12, more than any day's guaranteed record (the worst was 306 bytes, at InWaterSense). So the paper is about satellite plans.

### 4.3 Pass 3: the Prof's decisions

- Papers 1 and 2 must **not** be cited (they were just submitted).
- The lab has no satellite or LoRaWAN deployment, so the evaluation is **trace-driven** (real sensor records, simulated links).
- The tolerances became the **USGS excellent** rating.
- E11 and E12 measured the record's cost and what plans carry it; E13 compared one-way delivery designs.

### 4.4 Pass 4: the novelty problem, and an honest pivot

- **SBR** (Deligiannakis et al., VLDB Journal 2007) already compresses buffered sensor history to a bandwidth budget, with a maximum-error variant and a group leader that gives bandwidth to the node with the largest error. That **pre-empted the algorithmic core** of our pooling idea.
- **Animal telemetry** (CTD satellite relay data loggers on seals) has long abstracted profiles to a few broken-stick points and resent them pseudo-randomly over one-way Argos.
- **Our own value-aware layering lost to plain repetition** in E13b. We reported that, and the paper does not claim the code beats repetition on clean data.
- **Verdict:** no algorithmic novelty left; what remains is **setting, guarantee, and evidence** novelty: what a regulatory-grade record costs on real rivers, which plans carry it, and how to deliver it one-way. That fits an environmental-informatics journal better than IoT-J; thus, the target moved to **Environmental Modelling & Software**, approved by the Prof.

### 4.5 Development, freeze, and confirmation

- **Development (2023):** median need 18 B/day (2.1% of raw); at 6 msg/day, p = 0.3: code 0.90, repetition 0.85, tag practice 0.42, reliable-link 0.34.
- **Freeze:** plan, parameters, and code checksummed; H1–H7 written.
- **Confirmation (2024):** all seven passed (Part 4.6). Repetition matched the code on USGS data; the code clearly beat it on the low-cost data.

### 4.6 The confirmed results, hypothesis by hypothesis

| H | What it claimed | Threshold | 2024 result |
|---|---|---|---|
| H1 | Median need ≤ 5% of the raw readings | ≤ 5% | 1.8% (15 B/day) |
| H2 | 6 msg/day, independent p = 0.3: sites with ≥ 90% of days within 7 d | ≥ 75% | 35/39 |
| H2b | Same at 12 msg/day under bursty loss | ≥ 85% | 35/39 |
| H3 | Median G, code ÷ reliable-link | ≥ 2× | 3.5× (95% interval 3.1–4.0) |
| H4 | Median G, code − tag practice | ≥ 0.25 | 0.33 |
| H5 | Code and repetition each beat reliable-link by ≥ 0.2 in all 12 settings | 12/12 | 12/12 (smallest margin 0.34) |
| H6 | Pilot plan sufficient; at most one tier too large | ≥ 80%; ≥ 80% | 85%; 100% |
| H7 | InWaterSense median need ≥ 3× USGS | ≥ 3× | 3.9× |

**Mean G at 6 msg/day, p = 0.3 (2024):**

| Design | Independent | Bursty | Low-cost sites |
|---|---|---|---|
| Erasure code | 0.89 (0.86–0.92) | 0.81 | 0.77 |
| Repetition | 0.85 | 0.81 | 0.58 |
| Tag practice | 0.43 | 0.41 | 0.20 |
| Reliable-link | 0.34 (0.30–0.40) | 0.47 | 0.17 |
| Every k-th reading | 0.28 | 0.33 | 0.01 |

**Why the reliable-link design does better under bursty loss (0.47) than under independent loss (0.34):** at the same average loss, bursts concentrate the losses in fewer days, so more days lose nothing at all. A design that needs every message prefers that.

### 4.7 What makes a day expensive

- **Season:** the median need rose from 6 B/day in January to 24 B/day in June; the highest needs were from June to August, when the diel cycles of DO and temperature are strongest.
- **Parameter:** temperature took 41% of the values, DO 26%, SC 23%, pH 10%. Temperature's tolerance (0.2 °C, absolute) is tight compared with its daily swing, whereas SC's 3% is loose. **Lesson for agencies:** do not assume temperature is a cheap "baseline".
- **Site:** site medians ranged from 3 to 57 B/day; within a site, the 99th percentile was typically 3.3× the median.
- **Low-cost sensors cost more:** InWaterSense needed 58.5 B/day (3.9× USGS). The paper says the cause was not isolated (noise and fouling are candidates; only 22 complete days).

### 4.8 The Q1 audit of v0.1 (2026-10-24): what was wrong and what we fixed

Before calling the paper ready, every claim was checked against the code, the data, and the cited documents. **Nothing changed a confirmed result**, but these would have cost credibility with a reviewer:

1. **The message format did not add up.**
   - One byte for the time slot cannot index 288 five-minute slots (one site samples every 5 minutes). Fixed: 9 bits for the slot, 13 for the reading (2 + 9 + 13 = 24 bits, still 3 bytes).
   - The readings' quantisation was not modelled; the old text only said "14 bits is far finer than any tolerance". Fixed: the quantiser is now specified, its worst error computed (2.3% of the SC tolerance), and a sensitivity run measures what an encoder costs if it aims at 0.975 of the tolerance to absorb that error.
   - A 5-bit sequence number counts only 32 messages, but a 96-message tier was evaluated. Fixed: the text states that this tier needs a 2-byte header (6 values per message), which cannot change its result, because the largest daily need was 67 values.
2. **"1.8% of the raw data"** suggested bytes, but the share counts values (15 B is 1.2% of 1,296 B). Fixed to "of the raw readings".
3. **Two method details were missing:** the pilot's safety factor (tuned; it came out at 1.0) and the K/Q ratio reused for the 96-message tier. Both are now stated.
4. **"The values p span the erasure probabilities used in direct-to-satellite studies"** overstated the source: Tondo et al. (2021) sweep 0.01–0.9. Fixed to "lie within the range".
5. **References:** a co-author's name was printed as "Boulger, Robert W., J."; one title ended in "atmosphere1"; Deligiannakis was cited as 2007 but printed as 2006; the EDBT 2004 chapter lost its book title. All fixed in `draft/bib/build_bib.py`, so a rebuild keeps them.
6. **Fig. 2:** the legend covered the DO trough in panel (a), and panel (b)'s dashed line had no legend entry. Now one shared legend sits below both panels and names every element.
7. **Journal requirements:** a structured software-availability block, the CRediT roles in the official wording, and a funding statement were added. Elsevier also requires a generative-AI declaration before the references; you will add that yourself. The author name is now in full, as for the Prof.
8. **Uncertainty:** no intervals were reported. Site-clustered bootstrap intervals were added; every pre-registered threshold holds across its interval.
9. **The Word copy:** pandoc's raw output had default fonts, no numbered headings, no equation number, and no Fig. 1 (TikZ). The Word copy is now built from the same sources and restyled to match the PDF (Times New Roman, the same sizes, numbering, captions, and all six figures).
10. **The promised sensitivity analyses had not been run.** They have now (Part 4.9).

### 4.9 Sensitivity analyses (exploratory, after confirmation)

These were listed in the study plan but run only after confirmation, so the paper calls them exploratory (Section 5.5, Table 4). Bytes per day over the 12,221 site-days of 2024:

| Record and encoder | Median | 99th percentile | Max | InWaterSense median |
|---|---|---|---|---|
| Main result: excellent record, fewest values | 15 | 108 | 201 | 58.5 |
| Within 0.975 of the tolerance (quantiser margin) | 18 | 117 | 219 | 63.0 |
| Within half the tolerance (sensor margin) | 33 | 207 | 366 | 139.5 |
| Good record, fewest values | 6 | 39 | 123 | 21.0 |
| Excellent record, greedy online segmentation | 18 | 138 | 255 | 84.0 |
| Excellent record, deadband reporting | 30 | 176 | 270 | 133.5 |

**What each line teaches:**
- **Quantiser margin (+13% values):** the confirmed results used exact readings. A real node sends 13-bit values, so it should aim at 0.975 of the tolerance. That costs about one more value at the median, less than one message on the worst days. The paper says so openly.
- **Sensor margin (2.2×):** if you leave half the USGS error budget to the sensor, the record roughly doubles in size, still about two messages on a median day. This is the answer to "your guarantee ignores sensor error".
- **Good rating (6 B):** a looser standard makes the record very cheap.
- **Simpler encoders cost more:** greedy segmentation (the swinging-door family) needs 25% more values; deadband reporting needs 1.9× as many, because holding a flat value cannot follow a slope. The optimal encoder earns its place.
- **Coarser sampling did not reduce the need:** at the 15-minute sites the median stayed at 18 B/day when only every 2nd or 4th reading was kept. The cost is set by how much the river moves, not by how often you sample; therefore, sampling faster is almost free in satellite bytes.
- **Uncertainty:** the site-clustered 95% intervals were 12–21 B for the median need, 86–92% for the code's guaranteed share, 30–40% for the reliable-link design, and 3.1–4.0 for the H3 ratio. The code beat repetition under independent loss by 0.04 (0.01–0.07): small, but not zero.

**19-byte messages** (6 values instead of 7) did not change the ranking at 6 msg/day and p = 0.3: code 88%, repetition 81%, tag practice 36%, reliable-link 35%, evenly spaced readings 28%.

---

## Part 5. The paper in one page

**Problem:** polluted rivers beyond terrestrial coverage can be reached by satellite IoT, but the service sells a few 23-byte, one-way messages a day.

**Definition:** a day is guaranteed when every reconstructed reading stays within the USGS excellent-record tolerance.

**Findings (USGS 2024, pre-registered, all seven hypotheses passed):**
1. **Cost (RQ1):** median 15 B/day (1.8% of the raw readings; 95% interval 12–21 B); 63% of days fit in one message; the worst day needed 10 messages; summer and temperature are expensive.
2. **Delivery (RQ3):** at 6 msg/day and 30% loss, the guaranteed set with an erasure code guaranteed 89% of days, repetition 85%, tag practice 43%, the reliable-link optimum 34%, and evenly spaced readings 28%. More capacity did not rescue the unprotected design.
3. **Buffering (RQ2):** 6 msg/day met the 90%-within-7-days target at 35/39 sites under independent loss; bursty loss needs 12.
4. **Sizing (RQ4):** a 28-day pilot picked an adequate plan at 85% of sites, never more than one tier too large.
5. **Low-cost sensors** needed 3.9× more bytes; there, the code beat repetition clearly (77% vs 58%).

**What is new:** not the encoder (Imai–Iri 1988) or the code (Reed–Solomon 1960), but the cost of a regulatory-grade record on real rivers, the demonstration that the reliable-link optimum fails on one-way links, a feedback-free certification, plan-sizing guidance, and the pre-registered evidence.

**Limitations:** illustrative plan tiers; swept (not measured) loss; trace-driven, no hardware; the guarantee covers the encoder's error, not the sensor's; few complete low-cost days; tag practice modelled within one day.

---

## Part 6. Test yourself (answers below; try first)

1. A conductance reading is 800 µS/cm. What is its excellent-record tolerance? A DO reading is 4 mg/L: what is its tolerance?
2. Why does the paper call the encoder "not novel", and what is novel instead?
3. A day of four parameters at 15-minute sampling has how many raw readings? If its guaranteed set has 6 values, what share of the raw readings is that, and how many bytes?
4. At p = 0.3 with 6 messages a day, compute the probability that a K = 3 code decodes, and that r = 3 repetition delivers both of its data messages. Which carries more values?
5. The reliable-link design sends 42 values once. The chance all 6 messages arrive is 0.118, yet it guaranteed 34% of days. Why more than 12%?
6. Why did the reliable-link design not recover at 24 messages a day?
7. Why does bursty loss hurt the buffered design at 6 messages a day so much more (17/39 sites) than independent loss (35/39)?
8. Why was 2024 sealed with checksums, and what would have been wrong with tuning K on 2024?
9. Why resample sites, not days, in the bootstrap?
10. A reviewer says: "Your guarantee is meaningless, because the sensor itself has error." How do you answer?
11. Why is temperature the most expensive parameter, although it changes smoothly?
12. Why does the code beat repetition clearly on the low-cost data but not on USGS data?
13. What does the server certify without feedback, and why is that possible?
14. A 5-minute site has 288 readings a day. Why did the v0.1 message format fail for it, and what fixed it?

**Answers:**
1. SC: 3% of 800 = **24 µS/cm**. DO: 5% of 4 is 0.2, which is below 0.3, so **0.3 mg/L**.
2. Minimum-size piecewise-linear approximation with a maximum error is classical (Imai and Iri, 1988; Soroush 2008), and budgeted compression of sensor history exists (SBR). What is new: the measured cost of a USGS-excellent record on real rivers, the one-way delivery comparison showing the reliable-link optimum fails, feedback-free certification, plan sizing, and the pre-registered evidence.
3. 96 × 4 = **384** readings; 6/384 = **1.6%**; 6 × 3 = **18 bytes**, which fits in one message.
4. Code: P(≥ 3 of 6) = **0.930**. Repetition: (1 − 0.027)² = **0.947**. The code carries **21** values against **14**, so it can use a tighter τ, and it can carry days that need 15–21 values, which repetition cannot.
5. Its 42 values form a very tight record (small τ). Losing one message removes up to 7 values, but the remaining values often still keep every reading within the tolerance, so many days survive partial loss.
6. Each message still carries values that nothing else duplicates; with more messages there are more chances to lose one. The record grows tighter, but its survival depends on every message, and at 24 messages and p = 0.3 a lossless day is rare (it guaranteed 38%).
7. The buffered node sends one coded block per day. A burst can erase most of a day's 6 messages at once, so the block fails to decode and that day's data are gone for good (no resending). Independent losses rarely remove more than Q − K messages together.
8. To keep the confirmation honest. If K had been tuned on 2024, the test would partly measure luck in tuning (the garden of forking paths), and the reported numbers would be optimistic. Checksums prove the files were not changed or peeked at before the freeze.
9. Days at one site resemble each other (same river, same sensor, same season). Treating them as independent would make the intervals far too narrow. Resampling sites captures the variation that would come from deploying at other rivers.
10. Agree that the guarantee bounds the encoder's added error, not the sensor's, and the paper says so. Show the sensitivity analysis: reserving half of the error budget for the sensor (encoding within 0.5 × tolerance) raised the median need from 15 to 33 bytes a day (Part 4.9), still only about two messages.
11. Its tolerance is a tight 0.2 °C in absolute terms, while its diel swing is several degrees; every bend in the curve needs a value. SC's tolerance is relative (3%), which is loose for slow-changing conductance.
12. USGS records are clean, so most days need fewer values than repetition's 14-value capacity; then repetition's slightly higher survival probability wins (its median G was higher). Noisy low-cost records need more values than repetition can carry, and the code's 50% extra capacity decides the outcome (77% vs 58%).
13. Every span between two consecutive planned values that both arrived. The sequence numbers tell the server which planned values are missing, and the encoder promised every reading between consecutive planned values within τ × tolerance.
14. One byte indexes only 256 slots. Fixed by using 9 bits for the slot (512 slots) and 13 bits for the reading, still 24 bits per value.

---

## Part 7. Glossary

| Term | Meaning |
|---|---|
| Anchor | The previous day's last reading, which the server already holds; reconstruction starts from it |
| Argos | The satellite data-collection system used by animal tags since the late 1970s; Kinéis grew out of it (CLS and the French space agency CNES) |
| Bootstrap (site-clustered) | Resampling whole sites with replacement to estimate uncertainty |
| Certified span | Readings between two consecutive planned values that both arrived; guaranteed within τ × tolerance without feedback |
| Code dimension K | Number of data messages in an erasure-coded block of Q messages |
| CTD-SRDL | Conductivity–temperature–depth satellite relay data logger (seal tags); source of "tag practice" |
| Diel | Day–night (24-hour) cycle |
| Erasure code (MDS) | Q messages built from K so that any K recover all; Reed–Solomon is one |
| G (guaranteed share) | Share of loss draws (or site-days) in which the whole day stayed within tolerance |
| Gilbert channel | Two-state loss model with bursts: good state loses nothing, bad state loses everything |
| Greedy online segmentation | Extend each line as far as the tolerance allows, then keep its end reading (swinging-door family) |
| Deadband reporting | Send a reading when it leaves the band around the last value sent; the server holds the last value |
| Guaranteed set | The fewest readings that keep the whole day within tolerance (min-# at τ = 1) |
| Min-# problem | Fewest vertices of a piecewise-linear approximation within a maximum error (Imai and Iri, 1988) |
| Need | Size of the guaranteed set (values, or bytes at 3 B per value) |
| One-way link | The node can send but never receive, so it never learns what arrived |
| Pre-registration | Writing the hypotheses, thresholds, and analysis before seeing the test data |
| Reliable-link design | Fill all messages with the tightest record, send each once; optimal only if nothing is lost |
| Repetition (r) | Sending every message r times |
| SBR | Self-based regression (Deligiannakis et al.): budgeted compression of sensor history; closest prior art |
| Sealed set | Test data checksummed and left unopened until the plan was frozen |
| Systematic code | The data messages are sent as they are, plus separate parity messages |
| τ (tau) | Common error level: every reading within τ × its tolerance; τ = 1 is the guarantee |
| Tolerance δ | The USGS excellent-record limit for one reading |
| USGS TM 1-D3 | Wagner et al. (2006): the USGS procedures that define the accuracy ratings |

---

## Part 8. Where everything is (all paths relative to `Paper3/`)

| What | Where |
|---|---|
| Scoping history (four passes, every correction) | `PAPER3_SCOPING.md` |
| Frozen study plan, freeze checksums, confirmation verdicts | `docs/STUDY_PLAN.md`, `docs/FREEZE.md`, `docs/CONFIRM_RESULTS.md` |
| Literature cards | `papers/LITERATURE_NOTES.md`; PDFs in `papers/pdf/`, text in `papers/txt/` |
| Datasheet and USGS rating | `papers/standards/Kineis_KIM1_datasheet.pdf`, `papers/standards/Wagner2006_USGS_TM1D3_Continuous_WQ_Monitors.pdf` |
| Data | `data/clean/usgs/` (2023), `data/clean/usgs_2024/` (sealed; checksums in `usgs_2024.md5`), `results/confirm/lowcost_input/` |
| Encoder (min-#, common τ, tag-practice points) | `src/p3/pla.py` |
| Site-days and tolerances | `src/p3/data.py` |
| Designs, loss channels, Reed–Solomon, server | `src/p3/designs.py`, `channel.py`, `rs.py`, `server.py` |
| RQ1 need | `src/p3/need.py` → `results/{dev,confirm,lowcost}/need_excellent.csv` |
| RQ3 development and confirmation | `src/p3/run_dev.py`, `run_confirm.py` → `results/dev/`, `results/confirm/usgs2024_rq3.csv` |
| RQ2 and RQ4 | `src/p3/pooling.py`, `confirm_pooling.py` → `results/confirm/usgs2024_pooling.csv`, `usgs2024_sizing.csv` |
| Bootstrap intervals (exploratory) | `src/p3/bootstrap.py` → `results/sens/bootstrap.json` |
| Sensitivity analyses (exploratory) | `src/p3/sensitivity.py`, `sens_rq3.py` → `results/sens/` |
| Tests | `tests/test_p3.py` (run `python -m pytest tests -q` from `Paper3/`) |
| Manuscript sources | `draft/main.tex`, `draft/sec_*.tex`, `draft/tables/`, `draft/figs/` (Fig. 1 is `figs/arch.tex`) |
| Every number in the text | `draft/numbers.tex`, generated (with assertions) by `src/paper/paper_numbers.py` |
| Figures, checks, Word copy | `src/paper/make_figures.py`, `check_draft.py`, `make_word.py`, `fix_word.py` |
| Rebuild everything | `sh draft/build.sh` (from `Paper3/`) → `draft/deliverables/` |
| Open points for the authors | `draft/COVER_NOTE.md` |
