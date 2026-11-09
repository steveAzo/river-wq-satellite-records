# Mutation check of the revision-2 tests

Date: 2026-11-07. Program: `tools/mutation_check.py` (committed; plants one fault at a time in a scratch copy of `src/` and `tests/` and runs the named test files; a failing run is a catch). Access: repository. Raw output: `results/mutation_check_run1.md` (first round, all 18), `results/mutation_check_rerun1.md` and `results/mutation_check_rerun.md` (reruns of the six faults that escaped).
Status: numerical evidence about test power. An AI assistant chose the faults and wrote the tests; no outside reviewer has read them.

## Result

First round: 12 of 18 planted faults caught. Six escaped (M04, M12, M13, M14, M17, M18). Ten tests were added in `tests/test_mutation_gaps.py`. Second round: M12, M13, M14, M17, and M18 caught; M04 escaped a second time because my test's three-reading box tripped the lower-side check and hid the lax upper-side rule; with a two-reading test M04 is caught. Final: 18 of 18 caught. After the in-project review of 2026-11-09 three more faults were defined for the review's new rules (M19 to M21) and all were caught by `tests/test_review_fixes.py`, so 21 of 21 planted faults are caught.

| id | file | planted fault | first round | final |
|---|---|---|---|---|
| M01 | src/p3/certlang.py | tolerance interval half as wide: unsound | yes | yes |
| M02 | src/p3/certlang.py | 'yes' below threshold made too eager | yes | yes |
| M03 | src/p3/certlang.py | 'no' below threshold made too eager | yes | yes |
| M04 | src/p3/certlang.py | conductance 'no' rule too lax | NO | yes (after the test was corrected: it needs two readings) |
| M05 | src/p3/certlang.py | rolling mean lower bound uses the upper ends | yes | yes |
| M06 | src/p3/certlang.py | grid snapping moves the lower end outward instead of inward | yes | yes |
| M07 | src/p3/certlang.py | witness cross-check no longer rejects a minimum above the record | yes | yes |
| M08 | src/p3/certlang.py | slotless minimum witness raises the global lower bound to the cell top | yes | yes |
| M09 | src/p3/certlang.py | rate witness ignores downward changes | yes | yes |
| M10 | src/p3/frame2.py | CRC test inverted | yes | yes |
| M11 | src/p3/frame2.py | record corroboration disabled | yes | yes |
| M12 | src/p3/frame2.py | sanity rule no longer checks the slot against the profile | NO | yes |
| M13 | src/p3/frame2.py | censored witness codes accepted | NO | yes |
| M14 | src/p3/allocate.py | layered term allowed to go negative | NO | yes |
| M15 | src/p3/allocate.py | recovery probability uses the lower tail | yes | yes |
| M16 | src/p3/sod.py | send-on-delta deadband twice the tolerance | yes | yes |
| M17 | src/p3/sod.py | hold certified one reading too far | NO | yes |
| M18 | src/p3/capacity.py | bit budget forgets the hosted flag | NO | yes |
| M19 | src/p3/frame2.py | a witness descriptor that differs between messages no longer rejects the block | (not run before the review) | yes |
| M20 | src/p3/frame2.py | conflicting CRC-valid copies of one message no longer reject the block | (not run before the review) | yes |
| M21 | src/p3/robust2.py | the forgery may change only the CRC bytes (a no-op forgery) | (not run before the review) | yes |

## What each escape showed

- M04: no test exercised a conductance "no change" decision whose upper side was only just unsafe. The brute-force test did not reach it with its random boxes.
- M12 and M13: the receiver's sanity rule (slot inside the site profile, planned order, censored witness codes) had no unit test, although the integrity experiment relied on it.
- M14: the allocation objective was compared with exact enumeration only on plans that the solver itself chose, and the solver almost never layers an easy object; explicit plans are now compared as well.
- M17: no test had a censored reading next to a hold.
- M18: all budget quantities are byte-aligned, so a one-bit error in the segment overhead never changes the capacity of a byte-aligned layout; the fault matters only at non-aligned sizes, which the new test covers. In that sense the fault is equivalent for the layouts the codec produces.

## Limits

- Twenty-one faults chosen by hand, in four modules; not an exhaustive or statistically sampled mutation set. Modules without mutations (loader, delivery, record, the prototype runners) are not covered by this check.
- A caught fault shows only that some test fails on it, not that the tests are complete.
- The full run takes about 40 minutes on the project PC (the clean-tree baseline alone took 581 seconds).
