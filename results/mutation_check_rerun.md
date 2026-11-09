# Mutation check of the revision-2 tests

Faults planted one at a time in a scratch copy; a test run that fails is a catch. Caught 3 of 3 applied mutations (3 run, 21 defined).

| id | file | planted fault | tests | caught | seconds |
|---|---|---|---|---|---|
| M19 | src/p3/frame2.py | a witness descriptor that differs between messages no longer rejects the block | test_review_fixes.py | yes | 4 |
| M20 | src/p3/frame2.py | conflicting CRC-valid copies of one message no longer reject the block | test_review_fixes.py | yes | 5 |
| M21 | src/p3/robust2.py | the forgery may change only the CRC bytes (a no-op forgery) | test_review_fixes.py | yes | 2 |
