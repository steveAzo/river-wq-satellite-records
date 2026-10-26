# Step 7 analysis plan: packet-level multi-day replay (review M9, E4, Fig. D; RQ2, RQ4)

Written 2026-10-25 BEFORE any Step 7 result was computed. Development data (USGS 2023) only.

## Model
- Each site's year is replayed day by day on UTC days. At the end of day d the node plans the self-contained
  record of day d (all eligible channels; `record.Encoder.plan_at(1.0)`). Days without data add nothing.
- Every day the node transmits at most Q messages of frame v1. Segments carry the record day as an offset from
  the block day; a record day may be split over several units and blocks. Record days older than 63 days are
  dropped by the node (frame limit) and counted as lost.
- The link is one-way, so the transmission schedule does not depend on the channel. Each schedule is built once
  on bytes; each loss draw decides which messages arrive. One loss process runs over all messages in order, so
  Gilbert bursts span midnight.
- Server: recovers units (RS decode when at least K of a coded block arrive, else the systematic units that
  arrived; uncoded: the units that arrived), parses segments, and accumulates positions per record day. A record
  day is fully certified when its bound flag holds, its last position is known, and all positions 0..last have
  arrived (Corollary 1). Its delay is (block day of completion) - (record day), so at least 1.
- Byte check: for draw 0 of every channel, every block is decoded from its bytes (`delivery.receive_multi`) and
  must give the same recovered units as the decoding rule; any mismatch stops the run.

## Designs (equal quota Q; equal deadline)
- buf_rec (proposed): FIFO backlog of record units; one block per day with K = min(backlog units, ceil(rho Q))
  data units and Q - K parity (no block if the backlog is empty). rho in {1/3, 1/2, 2/3, 1}.
- daily_rec: record-first without a buffer (Step 5): day d's record in the block of day d + 1 if D1 <= Q,
  otherwise the reliable-link plan (not bound).
- rep_multi_rec: a buffer of the record units of the last W = 7 record days; the Q daily transmissions cycle
  round robin through the buffer (the pointer continues across days); uncoded.
- tag_multi_rec: the same buffer; the Q transmissions pick units pseudo-randomly with replacement (CTD-SRDL
  policy with the record's content).
- tag_multi: CTD-SRDL practice: each day m broken-stick points per channel (m in {2, 3, 4, 6}), packed into
  units, the same 7-day buffer and random policy.
Tiers Q = 1, 6, 12, 24, 96.

## Channels and draws
The 15 test channels of Step 5 (independent and Gilbert burst 3 at p = 0.05 ... 0.6; Gilbert burst 6 at p = 0.3);
30 draws per site, tier, design, and channel.

## Outcomes (per record day; primary cohort = four-parameter record days; all record days reported too)
- G_D: share fully certified within D days, D = 1, 2, 7 (G7 primary), and eventually.
- Delay distribution of fully certified days (median, p95); backlog in units (median, p95, max) per day for
  buf_rec; share of record days dropped by the 63-day limit.
- RQ2 summary: sites with G7 >= 0.9 (as in the draft's H2), per tier and channel.

## Parameter choice (fixed now)
Sites are split by sorted order: even-indexed sites tune, odd-indexed sites test. rho for buf_rec and m for
tag_multi are chosen by minimax regret of mean G7 (four-parameter days) over the six tuning channels on the tuning
sites. Reported on test sites; rho = 1 (parameter-free) reported alongside.

## RQ4 (plan sizing from a 28-day pilot), with buf_rec at the chosen rho
Planning assumption: independent loss p = 0.3 (as pre-registered for the draft). For each site, pilot G7 = G7 over
the record days of the first 28 days; hindsight tier = the smallest tier whose G7 over the remaining days is >= 0.9
(96 if none). The pilot rule picks the smallest tier whose pilot G7 >= T; T in {0.9, 0.95, 0.99, 1.0} is tuned on
the even sites (criterion: min(sufficient share, 0.8) + share over-provisioned by at most one tier) and evaluated
on the odd sites: sufficient share (pilot tier >= hindsight tier) and over-provision by at most one tier.
Sensitivity: the same with the planning channel set to Gilbert p = 0.3.

## Expectations stated in advance
- buf_rec with rho = 1 equals daily_rec whenever no day's record exceeds Q units (so mainly differs at Q = 1).
- Buffering cannot raise the probability that a given block decodes; it helps only days whose record exceeds the
  tier, at the price of delay and of making later days wait behind them.
