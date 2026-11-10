# Exploratory hybrid designs (development data only)

Date: 2026-11-07. Status: exploratory (the adoption rule was written before the run, docs/REVISION2_PLAN.md, "Exploratory hybrid designs"). Numbers: numerical, trace-driven simulation on USGS 2023 (38 sites), same loss draws as Step 4. Access: repository (`results/dev/proto_b_hyb1_hyb2/`, `results/hyb_eval.txt`, produced by `src/p3/proto_base.py` with `P3_DESIGNS=hyb1,hyb2` and `src/p3/hyb_eval.py`). Not peer review.

## Designs

- hyb1: decision flags for the configured queries (8 bits per message, record capacity 4.75 values per message as for the flags design) plus all four witness objects hosted in the spare slots of the record group (they cost no record capacity); no layered group.
- hyb2: flags plus the generalised 3b rule (hard witnesses layered, easy ones hosted).
- Decision rule: the certificate decision when it is certain, otherwise the flag decision when any message arrived.

## Result against the adoption rule (Q = 6, both loss models)

- hyb1 matches the flags on the configured thresholds (hard-case decisions 0.999 and 0.961, record recovered 0.889 and 0.819, all equal to the flags to three decimals) and gains +0.416 (independent loss) and +0.355 (bursts) on the unanticipated thresholds: adoption rule MET.
- hyb2 matches the flags on hard-case decisions but loses record recovery (-0.094 and -0.076) and gains more on the unanticipated thresholds (+0.564 and +0.497): adoption rule NOT MET.
- Against the 3b rule (Q = 6, independent loss): hyb1 decides 0.999 of hard cases at the configured thresholds against 0.968 and recovers the record 0.889 against 0.825, but decides 0.633 against 0.783 on the unanticipated thresholds (the 3b rule protects witnesses in their own columns).
- Zero wrong decisions in all rows (flags decisions are correct by construction).

## Reading

- For the question "which design should the paper present", hyb1 is a free addition to decision flags: no cost in configured-threshold decisions or in record recovery, with a large gain on thresholds nobody configured. The 3b rule buys a further +0.15 on unanticipated thresholds at the price of 0.03 in configured-threshold decisions and 0.06 in record recovery.
- hyb1 inherits the flags' dependence on the configured thresholds for the configured decisions; the hosted witnesses are protected only as well as the record is.
- Caveats: development data; flags modelled at 4.75 values per message although the frame gives 4 (favours the flags, and favours hyb1 more on the alternative thresholds because it enlarges the spare room for hosted witnesses; the flags design decides from its flags alone and does not use the recovered record; review findings A2 and A4 of 2026-11-09); the alternative threshold sets were chosen by the analyst; the witnesses are hosted only when the record group has spare room (about 78% of days have at least one spare slot, 21% have four).
- Adoption is a decision for the authors before the freeze (docs/CONFIRM3_PLAN.md, Section 7). The drafter recommends adopting hyb1 and keeps hyb2 as a descriptive design.

## Raw evaluation output

## Q = 6: 38 sites; wrong decisions max 0.000

### iid_p0.3
| design                              | record recovered       | hard, configured       | hard, alternative      | all, configured        |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| record only                         | 0.905 (0.874 to 0.934) | 0.677 (0.634 to 0.726) | 0.573 (0.526 to 0.617) | 0.898 (0.874 to 0.921) |
| 3b rule                             | 0.825 (0.776 to 0.871) | 0.968 (0.960 to 0.975) | 0.783 (0.736 to 0.825) | 0.923 (0.904 to 0.941) |
| exact, lambda 1                     | 0.838 (0.786 to 0.885) | 0.949 (0.937 to 0.960) | 0.727 (0.680 to 0.771) | 0.975 (0.970 to 0.980) |
| decision flags                      | 0.889 (0.855 to 0.920) | 0.999 (0.999 to 0.999) | 0.217 (0.177 to 0.255) | 0.999 (0.999 to 0.999) |
| hybrid 1 (flags + hosted witnesses) | 0.889 (0.855 to 0.920) | 0.999 (0.999 to 0.999) | 0.633 (0.583 to 0.679) | 0.999 (0.999 to 1.000) |
| hybrid 2 (flags + 3b rule)          | 0.795 (0.739 to 0.846) | 0.999 (0.999 to 0.999) | 0.781 (0.733 to 0.824) | 0.999 (0.999 to 1.000) |
  hyb1 minus flags: hard configured +0.000, record +0.000, hard alternative +0.416 -> adoption rule MET for iid_p0.3
  hyb2 minus flags: hard configured +0.000, record -0.094, hard alternative +0.564 -> adoption rule NOT MET for iid_p0.3

### gilbert_p0.3_b3
| design                              | record recovered       | hard, configured       | hard, alternative      | all, configured        |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| record only                         | 0.835 (0.808 to 0.861) | 0.572 (0.538 to 0.613) | 0.490 (0.446 to 0.529) | 0.803 (0.780 to 0.826) |
| 3b rule                             | 0.767 (0.725 to 0.808) | 0.853 (0.841 to 0.863) | 0.691 (0.646 to 0.730) | 0.830 (0.813 to 0.848) |
| exact, lambda 1                     | 0.765 (0.717 to 0.810) | 0.824 (0.805 to 0.839) | 0.632 (0.586 to 0.674) | 0.879 (0.869 to 0.889) |
| decision flags                      | 0.819 (0.792 to 0.847) | 0.961 (0.959 to 0.962) | 0.209 (0.171 to 0.244) | 0.961 (0.960 to 0.961) |
| hybrid 1 (flags + hosted witnesses) | 0.819 (0.792 to 0.847) | 0.961 (0.959 to 0.962) | 0.564 (0.517 to 0.607) | 0.963 (0.962 to 0.963) |
| hybrid 2 (flags + 3b rule)          | 0.744 (0.699 to 0.786) | 0.961 (0.959 to 0.962) | 0.705 (0.659 to 0.746) | 0.963 (0.962 to 0.963) |
  hyb1 minus flags: hard configured +0.000, record +0.000, hard alternative +0.355 -> adoption rule MET for gilbert_p0.3_b3
  hyb2 minus flags: hard configured +0.000, record -0.076, hard alternative +0.497 -> adoption rule NOT MET for gilbert_p0.3_b3

## Q = 12: 38 sites; wrong decisions max 0.000

### iid_p0.3
| design                              | record recovered       | hard, configured       | hard, alternative      | all, configured        |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| record only                         | 0.991 (0.984 to 0.996) | 0.790 (0.744 to 0.831) | 0.664 (0.616 to 0.704) | 0.968 (0.956 to 0.978) |
| 3b rule                             | 0.964 (0.945 to 0.982) | 0.982 (0.974 to 0.989) | 0.813 (0.765 to 0.855) | 0.989 (0.984 to 0.993) |
| exact, lambda 1                     | 0.976 (0.963 to 0.988) | 0.980 (0.972 to 0.987) | 0.720 (0.671 to 0.763) | 0.997 (0.995 to 0.998) |
| decision flags                      | 0.988 (0.981 to 0.995) | 1.000 (1.000 to 1.000) | 0.217 (0.177 to 0.255) | 1.000 (1.000 to 1.000) |
| hybrid 1 (flags + hosted witnesses) | 0.988 (0.981 to 0.995) | 1.000 (1.000 to 1.000) | 0.700 (0.650 to 0.745) | 1.000 (1.000 to 1.000) |
| hybrid 2 (flags + 3b rule)          | 0.955 (0.933 to 0.975) | 1.000 (1.000 to 1.000) | 0.811 (0.764 to 0.854) | 1.000 (1.000 to 1.000) |

### gilbert_p0.3_b3
| design                              | record recovered       | hard, configured       | hard, alternative      | all, configured        |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| record only                         | 0.971 (0.963 to 0.978) | 0.749 (0.706 to 0.790) | 0.630 (0.584 to 0.670) | 0.943 (0.929 to 0.954) |
| 3b rule                             | 0.940 (0.921 to 0.958) | 0.966 (0.959 to 0.974) | 0.797 (0.750 to 0.839) | 0.966 (0.959 to 0.972) |
| exact, lambda 1                     | 0.956 (0.941 to 0.970) | 0.947 (0.938 to 0.955) | 0.696 (0.648 to 0.738) | 0.976 (0.972 to 0.980) |
| decision flags                      | 0.967 (0.957 to 0.975) | 0.997 (0.996 to 0.997) | 0.217 (0.177 to 0.254) | 0.997 (0.996 to 0.997) |
| hybrid 1 (flags + hosted witnesses) | 0.967 (0.957 to 0.975) | 0.997 (0.996 to 0.997) | 0.675 (0.624 to 0.720) | 0.997 (0.997 to 0.997) |
| hybrid 2 (flags + 3b rule)          | 0.929 (0.906 to 0.950) | 0.997 (0.996 to 0.997) | 0.797 (0.749 to 0.839) | 0.997 (0.997 to 0.997) |
