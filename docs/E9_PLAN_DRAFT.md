# E9 plan (DRAFT, SUPERSEDED 2026-10-16): outage-recovery drain on real outage records

> **Superseded** by the third scoping pass (`../PAPER3_SCOPING.md` §T). E11 showed that a LoRaWAN node that sends the right bytes never runs short of TTN airtime, so this plan's LoRaWAN-drain framing is now only a negative control. The replacement plan (satellite plan tiers × pools × one-way loss) will be written after the Prof confirms the framing.

**Status:** draft written 2026-10-16, updated after E7c (policy 7 added). It is frozen, and the hypotheses become binding, only after the Prof agrees on scope A2 (E7 showed that greedy is about 1.4× the optimum, so the proposed scheme is common-τ min-#, policy 7). Changes after freezing are logged as deviations, as in Paper 2.

## Question
After a real outage, a node (or a gateway's pool of nodes) has a backlog plus live data. The uplink allows a fixed daily byte budget. Which upload policy gets the server's record back within tolerance fastest, and keeps the worst error smallest during the drain, without delaying alarms?

## Set-up
- **Signals:** 39 USGS sites (2023) in 6 river chains as gateway pools, plus InWaterSense node 1 as the noisy counter-case. L2 tolerances.
- **Outages:** start times and durations replayed from the real records, InWaterSense node 1 and Weija conductivity (from Paper 2's sources; cite the original data, not Paper 2), with UVA system outages as a third. Each record is applied by circular time shift to each site, with seeds fixed in advance.
- **Budgets:** TTN fair use (30 s/day) at SF10, SF11 and SF12 (E8: 2,142 / 969 / 510 B/day). For gateway pools, a shared backhaul quota equal to N × the per-node budget.
- **Live traffic:** new readings keep arriving during the drain and compete for the same budget. Alarms (Paper-1-type detector, frozen) are sent immediately and charged to the budget.

## Policies
1. FIFO drain, then live (what bulk store-and-forward does).
2. Newest-first (AoI-optimal; Paper 2's packing).
3. Class priority (proposal 3).
4. stride_nf, the newest-plus-progressive data-blind order.
5. Value order per node, with equal shares of a pool.
6. Water level, nested (pooled greedy value order; τ broadcast once a day, with node residuals advertised in 1 B).
7. Common-τ min-# (the exact pooled min-max optimum for a known daily budget; E7c). This is the proposed scheme; 6 is its fallback when truncation is unpredictable.

## Metrics
- **R1, recovery time:** time until the server's record of the outage period and the live picture are both within tolerance.
- **R2, worst error during the drain:** network-wide, in tolerance units.
- **R3, alarm latency:** for events injected during and after the outage.
- **R4, bytes and energy** per delivered guarantee.

## Draft hypotheses (to be fixed before running)
- **H1:** at SF11–12, common-τ min-# reaches R1 at least 2× faster than FIFO, with median over sites and outages.
- **H2:** common-τ min-#'s R2 is at most 0.5× that of equal-share value order on at least 4 of 6 chains.
- **H3:** alarm latency under common-τ min-# is not worse than newest-first by more than one budget period.
- **H4 (negative control):** at SF10 and below (no scarcity), all policies reach R1 within one day and differ by less than 1 percentage point.

## Open choices
- How τ is updated with only 10 downlinks a day.
- Whether residuals are piggy-backed on every uplink.
- The buffer cap: real flash limits, e.g. a 7-day backlog.
