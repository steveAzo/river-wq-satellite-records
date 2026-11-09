# Mutation check of the revision-2 tests

Faults planted one at a time in a scratch copy; a test run that fails is a catch. Caught 12 of 18 applied mutations (18 defined).

| id | file | planted fault | tests | caught | seconds |
|---|---|---|---|---|---|
| M01 | src/p3/certlang.py | tolerance interval half as wide: unsound | test_certlang.py | yes | 16 |
| M02 | src/p3/certlang.py | 'yes' below threshold made too eager | test_certlang.py | yes | 12 |
| M03 | src/p3/certlang.py | 'no' below threshold made too eager | test_certlang.py | yes | 14 |
| M04 | src/p3/certlang.py | conductance 'no' rule too lax | test_certlang.py | NO | 287 |
| M05 | src/p3/certlang.py | rolling mean lower bound uses the upper ends | test_certlang.py | yes | 104 |
| M06 | src/p3/certlang.py | grid snapping moves the lower end outward instead of inward | test_certlang.py | yes | 114 |
| M07 | src/p3/certlang.py | witness cross-check no longer rejects a minimum above the record | test_certlang.py | yes | 319 |
| M08 | src/p3/certlang.py | slotless minimum witness raises the global lower bound to the cell top | test_certlang.py | yes | 270 |
| M09 | src/p3/certlang.py | rate witness ignores downward changes | test_certlang.py | yes | 193 |
| M10 | src/p3/frame2.py | CRC test inverted | test_frame2.py | yes | 7 |
| M11 | src/p3/frame2.py | record corroboration disabled | test_frame2.py | yes | 15 |
| M12 | src/p3/frame2.py | sanity rule no longer checks the slot against the profile | test_frame2.py | NO | 9 |
| M13 | src/p3/frame2.py | censored witness codes accepted | test_frame2.py | NO | 8 |
| M14 | src/p3/allocate.py | layered term allowed to go negative | test_allocate.py | NO | 6 |
| M15 | src/p3/allocate.py | recovery probability uses the lower tail | test_allocate.py | yes | 6 |
| M16 | src/p3/sod.py | send-on-delta deadband twice the tolerance | test_sod.py | yes | 13 |
| M17 | src/p3/sod.py | hold certified one reading too far | test_sod.py | NO | 144 |
| M18 | src/p3/capacity.py | bit budget forgets the hosted flag | test_capacity.py, test_frame2.py | NO | 11 |
