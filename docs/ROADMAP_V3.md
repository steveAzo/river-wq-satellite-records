# Roadmap to the end of Paper 3 (version 3), written 2026-11-10

Written by an AI assistant for the author. Time figures are my estimates (plus or minus 50%), not measurements; "session" means one working sitting of a few hours; "machine time" is the PC running on its own.

## Where we are in one paragraph

Cohort 3 showed the method works (no wrong decisions) but the integrity claim failed (H8) and the review found the comparison unfair (flags threw away their record). Version 3 fixes both on development data: the fair comparison keeps the 3b rule (+0.16 to +0.27 on thresholds nobody configured, at a record cost of 0.03 to 0.09), and the integrity study picked a CRC-24 per message. A new 2022 cohort of 35 sites is selected (metadata only, not downloaded). What is left is building the final run, freezing it, running it once, and writing up whatever comes out.

## What is left, in order

| # | Step | Who | Time |
|---|---|---|---|
| 1 | Receiver hardening plus fuzz tests (new files only) | Claude | 1 session |
| 2 | Version 3 confirmation driver: freeze check, run log, byte round trip, verdict script | Claude | 1 to 2 sessions |
| 3 | Tests for every new file, full suite green | Claude | half a session |
| 4 | Second AI session reads code and plan; fixes | Claude, separate session | 1 session |
| 5 | Freeze record, committed BEFORE the run | You | 10 minutes |
| 6 | Download, clean, seal the 35 sites of 2022 (needs your go-ahead) | Claude and the PC | 2 to 4 hours machine time |
| 7 | The one confirmatory run | the PC | 4 to 8 hours machine time |
| 8 | Results document, then manuscript rewrite, figures, Word copy, supplement | Claude | 2 to 3 sessions |
| 9 | Outside review before any preprint | someone else | not in my control |

Total: about 6 to 8 working sessions plus 6 to 12 hours of machine time that can run overnight; about 1.5 to 2.5 weeks if there is a session most days.

## The rule that ends the rounds

- Steps 1 to 5 are the last development. After the freeze nothing changes, whatever the run shows.
- If a hypothesis fails in the run, it is reported as a finding and the paper is written around it; there is no second run on this cohort, and no new method version for this paper.
- Optional items that are NOT on the path (cut unless you ask): re-running send-on-delta, tolerance x 0.5, the random-day control, and the exact allocator in version 3.
- Decisions I need from you, and nothing else: the go-ahead for step 6, and the commit for step 5.
