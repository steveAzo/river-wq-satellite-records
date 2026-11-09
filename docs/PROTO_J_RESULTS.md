# Step 3c results (revision 2): joint allocation of all witnesses, development data only

Date: 2026-11-06. Data: USGS 2023, 38 sites with four-parameter days. Code: `src/p3/allocate.py` (exact solver, `tests/test_allocate.py`, 7 tests), `proto_joint.py` (nine designs, identical loss draws), `proto_joint_eval.py`, `proto_gap.py`. Pre-registration: docs/REVISION2_PLAN.md ("Step 3c"), with one correction made before any result (the layered term uses the common arrival count N).
Commands (from Paper3/): `python -I src/p3/proto_joint.py data/clean/usgs dev <Q> 1`, `proto_joint_eval.py dev 6 12`, `proto_gap.py data/clean/usgs dev`. One worker (3.7 GB RAM).

## Setting

All four witness objects (DO min, pH min and max, T max, conductance rate pair) compete for the five value slots of each message, with the record. Designs: record only; flat (all witnesses in the record code); PET c = 2 (all witnesses in one layered group); spare slots; the Step 3b rule generalised (hard objects layered in one group with k at most 2, easy objects in spare slots); the control (that pattern on random days); exact allocation with lambda = 0.5, 1, 2 (allocate.solve under a channel-blind prior, independent loss averaged over p = 0.1 to 0.5). Queries: DO, pH, conductance pulse, 7DADM. Hard cases as in 3b.
Byte accounting: the prototype charges a full 24-bit value slot per witness. A witness needs only the parameter, the kind, and the code (about 17 bits; the rate pair about 28 bits, because the slots are not used by the decision rules), so the results are conservative for the byte budget. The frame specification for witnesses is still to be written.

## Findings

1. Soundness: 0 wrong decisions in every design, condition, and Q.
2. Pre-registered criterion 2 (exact lambda 1 against the generalised 3b rule: at least +0.02 pooled hard-case decisions at no lower record recovery, or at least +0.02 record at no lower hard-case decisions): NOT MET at Q = 6 under both loss models and at Q = 12. At Q = 6 the exact allocation changes hard-case decisions by -0.020 (independent) and -0.036 (bursts), and record recovery by +0.012 and -0.004.
3. Exploratory (not pre-registered): the exact allocation improves decisions on all cases by +0.053 (independent) and +0.048 (bursts) at equal record recovery, because its objective also protects easy witnesses. With lambda = 2 it recovers the record +0.052 (independent) and +0.033 (bursts) more often than the 3b rule, for -0.033 and -0.051 on hard cases. The two allocators lie on a common trade-off; neither dominates.
4. Both allocators beat the classical joint designs when all witnesses compete (Q = 6, independent loss, exact lambda 1): against PET c = 2, record +0.115, hard +0.050, all +0.026; against flat, +0.064, +0.140, +0.079; against the random-day control, +0.004, +0.152, +0.065.
5. The price of protecting four witnesses is larger than in isolation: 3b rule record recovery 0.825 against 0.905 for the record alone (Q = 6, independent loss), in return for pooled hard-case decisions of 0.968 against 0.677.
6. Q = 12: decisions saturate (pooled hard 0.98 for PET c = 2, the 3b rule, and exact); the allocators differ mainly in record recovery (0.954 PET c = 2, 0.964 3b rule, 0.976 exact lambda 1, 0.991 record only).
7. Model-level optimality gap (J, same prior; exact is never beaten on any day, which also checks the evaluator): at Q = 6 and lambda = 1 the 3b rule has J = 4.305 against 4.637 for the optimum (gap 0.332, 7%), and is optimal on 30% of days; at Q = 12 the gap is 0.081 (1.6%). PET c = 2 has J = 4.323 at Q = 6 (higher than the 3b rule under this equal-weight objective) but a much lower record recovery in the measured outcomes.

## Reading

- Per the pre-registered rule, the simple rule is the method to present, and the exact allocator is reported as the optimum of the bounded problem, which shows the rule is within 7% (Q = 6) and 1.6% (Q = 12) of that optimum on the stated objective.
- The exact allocator is nonetheless the more controllable instrument: lambda moves the design along the record-versus-decisions curve, and at equal record it protects easy days better. The paper can present the family (record-first code, certificates, and a protection rule chosen by lambda) and the curve, with the pre-registered verdict stated.
- Limits: the objective is an approximation (it ignores systematic partial recovery and, for the 7DADM, couples days only through the hardness flag); d for the 7DADM is a heuristic; the 7DADM band is tuned on development data; everything is on the development data.

## Raw evaluation output

C:\Users\User\Desktop\WSN_M\Paper3\src\p3\proto_joint_eval.py:51: FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version. Call result.infer_objects(copy=False) instead. To opt-in to the future behavior, set `pd.set_option('future.no_silent_downcasting', True)`
  d["hard"] = d["hard"].fillna(False).astype(bool)
C:\Users\User\Desktop\WSN_M\Paper3\src\p3\proto_joint_eval.py:51: FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version. Call result.infer_objects(copy=False) instead. To opt-in to the future behavior, set `pd.set_option('future.no_silent_downcasting', True)`
  d["hard"] = d["hard"].fillna(False).astype(bool)

## Q = 6: 38 sites; wrong decisions max 0.000

### iid_p0.3
| design                              | record recovered       | DO, hard               | pH, hard               | conductance, hard      | 7DADM near windows, hard   | pooled, hard           | pooled, all            |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|:---------------------------|:-----------------------|:-----------------------|
| record only                         | 0.905 (0.877 to 0.931) | 0.746 (0.696 to 0.787) | 0.696 (0.637 to 0.771) | 0.619 (0.534 to 0.720) | 0.721 (0.656 to 0.790)     | 0.677 (0.634 to 0.728) | 0.898 (0.872 to 0.921) |
| flat (all witnesses in record code) | 0.774 (0.730 to 0.818) | 0.872 (0.838 to 0.908) | 0.865 (0.834 to 0.895) | 0.812 (0.789 to 0.831) | 0.694 (0.658 to 0.729)     | 0.810 (0.790 to 0.827) | 0.895 (0.882 to 0.908) |
| PET c=2 (all witnesses)             | 0.726 (0.665 to 0.789) | 0.923 (0.892 to 0.957) | 0.922 (0.896 to 0.945) | 0.949 (0.945 to 0.953) | 0.806 (0.790 to 0.821)     | 0.909 (0.898 to 0.919) | 0.948 (0.943 to 0.953) |
| spare slots                         | 0.905 (0.876 to 0.934) | 0.846 (0.797 to 0.892) | 0.763 (0.699 to 0.835) | 0.619 (0.530 to 0.722) | 0.750 (0.693 to 0.811)     | 0.714 (0.670 to 0.765) | 0.912 (0.892 to 0.933) |
| 3b rule generalised                 | 0.825 (0.773 to 0.872) | 0.948 (0.916 to 0.981) | 0.958 (0.933 to 0.982) | 0.982 (0.978 to 0.986) | 0.965 (0.953 to 0.977)     | 0.968 (0.960 to 0.975) | 0.923 (0.904 to 0.941) |
| control: 3b pattern on random days  | 0.835 (0.781 to 0.879) | 0.826 (0.766 to 0.881) | 0.799 (0.736 to 0.850) | 0.794 (0.708 to 0.851) | 0.801 (0.743 to 0.858)     | 0.801 (0.763 to 0.837) | 0.911 (0.891 to 0.930) |
| exact, lambda 0.5                   | 0.798 (0.739 to 0.855) | 0.944 (0.912 to 0.979) | 0.947 (0.919 to 0.972) | 0.972 (0.968 to 0.978) | 0.963 (0.949 to 0.975)     | 0.960 (0.950 to 0.970) | 0.980 (0.976 to 0.983) |
| exact, lambda 1                     | 0.838 (0.787 to 0.885) | 0.944 (0.908 to 0.979) | 0.937 (0.908 to 0.961) | 0.955 (0.949 to 0.963) | 0.954 (0.937 to 0.968)     | 0.949 (0.937 to 0.960) | 0.975 (0.970 to 0.980) |
| exact, lambda 2                     | 0.876 (0.835 to 0.912) | 0.933 (0.900 to 0.970) | 0.927 (0.900 to 0.953) | 0.938 (0.931 to 0.946) | 0.928 (0.899 to 0.953)     | 0.933 (0.919 to 0.947) | 0.965 (0.957 to 0.972) |

Paired differences, iid_p0.3, Q = 6 (sites resampled, 95% interval); columns: record; pooled hard; pooled all
  ex1 minus heur: record +0.012 (-0.003 to +0.027); hard -0.020 (-0.026 to -0.013); all +0.053 (+0.037 to +0.070)
  ex05 minus heur: record -0.033 (-0.052 to -0.017); hard -0.010 (-0.016 to -0.005); all +0.059 (+0.042 to +0.076)
  ex2 minus heur: record +0.052 (+0.035 to +0.070); hard -0.033 (-0.044 to -0.024); all +0.042 (+0.030 to +0.057)
  ex1 minus randmix: record +0.004 (-0.009 to +0.019); hard +0.152 (+0.118 to +0.189); all +0.065 (+0.046 to +0.086)
  ex1 minus flat: record +0.064 (+0.053 to +0.075); hard +0.140 (+0.118 to +0.164); all +0.079 (+0.070 to +0.089)
  ex1 minus pet2: record +0.115 (+0.094 to +0.139); hard +0.050 (+0.037 to +0.064); all +0.026 (+0.023 to +0.029)
  ex1 minus rec: record -0.070 (-0.092 to -0.050); hard +0.241 (+0.200 to +0.281); all +0.077 (+0.055 to +0.096)
  heur minus randmix: record -0.008 (-0.013 to -0.004); hard +0.171 (+0.133 to +0.211); all +0.012 (+0.008 to +0.016)
  heur minus flat: record +0.052 (+0.038 to +0.065); hard +0.159 (+0.135 to +0.186); all +0.026 (+0.016 to +0.036)
  criterion 2 (exact lambda 1 vs 3b rule): hard +0.02 at record >= -0.005: False; record +0.02 at hard >= -0.005: False  ->  NOT MET

### gilbert_p0.3_b3
| design                              | record recovered       | DO, hard               | pH, hard               | conductance, hard      | 7DADM near windows, hard   | pooled, hard           | pooled, all            |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|:---------------------------|:-----------------------|:-----------------------|
| record only                         | 0.835 (0.808 to 0.860) | 0.691 (0.648 to 0.733) | 0.638 (0.589 to 0.700) | 0.560 (0.487 to 0.648) | 0.437 (0.384 to 0.489)     | 0.573 (0.540 to 0.615) | 0.803 (0.781 to 0.825) |
| flat (all witnesses in record code) | 0.710 (0.678 to 0.740) | 0.819 (0.786 to 0.852) | 0.814 (0.789 to 0.841) | 0.789 (0.779 to 0.801) | 0.370 (0.346 to 0.397)     | 0.714 (0.689 to 0.733) | 0.797 (0.788 to 0.806) |
| PET c=2 (all witnesses)             | 0.682 (0.628 to 0.731) | 0.852 (0.822 to 0.885) | 0.832 (0.808 to 0.852) | 0.838 (0.835 to 0.843) | 0.440 (0.419 to 0.461)     | 0.757 (0.735 to 0.776) | 0.824 (0.816 to 0.833) |
| spare slots                         | 0.835 (0.808 to 0.859) | 0.782 (0.745 to 0.827) | 0.696 (0.642 to 0.758) | 0.560 (0.487 to 0.652) | 0.458 (0.415 to 0.504)     | 0.605 (0.569 to 0.646) | 0.815 (0.793 to 0.838) |
| 3b rule generalised                 | 0.767 (0.725 to 0.809) | 0.893 (0.863 to 0.926) | 0.886 (0.865 to 0.906) | 0.901 (0.897 to 0.906) | 0.690 (0.657 to 0.718)     | 0.853 (0.841 to 0.863) | 0.830 (0.812 to 0.846) |
| control: 3b pattern on random days  | 0.776 (0.733 to 0.815) | 0.770 (0.719 to 0.821) | 0.736 (0.682 to 0.779) | 0.728 (0.652 to 0.778) | 0.531 (0.486 to 0.582)     | 0.695 (0.658 to 0.726) | 0.820 (0.801 to 0.840) |
| exact, lambda 0.5                   | 0.729 (0.670 to 0.788) | 0.892 (0.856 to 0.930) | 0.867 (0.840 to 0.893) | 0.884 (0.877 to 0.892) | 0.676 (0.642 to 0.706)     | 0.838 (0.822 to 0.852) | 0.886 (0.877 to 0.894) |
| exact, lambda 1                     | 0.765 (0.713 to 0.810) | 0.889 (0.854 to 0.926) | 0.855 (0.824 to 0.882) | 0.866 (0.858 to 0.876) | 0.659 (0.622 to 0.695)     | 0.824 (0.807 to 0.839) | 0.879 (0.869 to 0.889) |
| exact, lambda 2                     | 0.799 (0.762 to 0.835) | 0.877 (0.842 to 0.917) | 0.843 (0.814 to 0.872) | 0.846 (0.839 to 0.857) | 0.631 (0.588 to 0.671)     | 0.806 (0.786 to 0.824) | 0.868 (0.855 to 0.880) |

Paired differences, gilbert_p0.3_b3, Q = 6 (sites resampled, 95% interval); columns: record; pooled hard; pooled all
  ex1 minus heur: record -0.004 (-0.018 to +0.008); hard -0.036 (-0.052 to -0.023); all +0.048 (+0.036 to +0.062)
  ex05 minus heur: record -0.045 (-0.067 to -0.026); hard -0.024 (-0.042 to -0.013); all +0.056 (+0.042 to +0.070)
  ex2 minus heur: record +0.033 (+0.022 to +0.045); hard -0.051 (-0.068 to -0.036); all +0.037 (+0.027 to +0.047)
  ex1 minus randmix: record -0.011 (-0.025 to +0.002); hard +0.136 (+0.103 to +0.169); all +0.059 (+0.045 to +0.074)
  ex1 minus flat: record +0.053 (+0.036 to +0.070); hard +0.117 (+0.098 to +0.137); all +0.079 (+0.073 to +0.085)
  ex1 minus pet2: record +0.083 (+0.073 to +0.095); hard +0.081 (+0.064 to +0.100); all +0.052 (+0.047 to +0.057)
  ex1 minus rec: record -0.072 (-0.095 to -0.051); hard +0.226 (+0.189 to +0.264); all +0.075 (+0.058 to +0.094)
  heur minus randmix: record -0.008 (-0.011 to -0.004); hard +0.172 (+0.142 to +0.204); all +0.011 (+0.008 to +0.014)
  heur minus flat: record +0.057 (+0.044 to +0.070); hard +0.153 (+0.131 to +0.178); all +0.030 (+0.017 to +0.042)
  criterion 2 (exact lambda 1 vs 3b rule): hard +0.02 at record >= -0.005: False; record +0.02 at hard >= -0.005: False  ->  NOT MET

## Q = 12: 38 sites; wrong decisions max 0.000

### iid_p0.3
| design                              | record recovered       | DO, hard               | pH, hard               | conductance, hard      | 7DADM near windows, hard   | pooled, hard           | pooled, all            |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|:---------------------------|:-----------------------|:-----------------------|
| record only                         | 0.991 (0.984 to 0.996) | 0.837 (0.789 to 0.884) | 0.803 (0.766 to 0.855) | 0.691 (0.603 to 0.789) | 0.937 (0.913 to 0.959)     | 0.790 (0.750 to 0.832) | 0.968 (0.956 to 0.978) |
| flat (all witnesses in record code) | 0.981 (0.972 to 0.991) | 0.940 (0.909 to 0.971) | 0.956 (0.933 to 0.980) | 0.977 (0.968 to 0.985) | 0.975 (0.964 to 0.985)     | 0.966 (0.957 to 0.975) | 0.991 (0.988 to 0.994) |
| PET c=2 (all witnesses)             | 0.954 (0.932 to 0.973) | 0.953 (0.920 to 0.987) | 0.968 (0.944 to 0.991) | 0.992 (0.988 to 0.996) | 0.999 (0.998 to 1.000)     | 0.982 (0.974 to 0.988) | 0.997 (0.996 to 0.999) |
| spare slots                         | 0.991 (0.984 to 0.996) | 0.924 (0.883 to 0.964) | 0.868 (0.841 to 0.902) | 0.691 (0.604 to 0.796) | 0.947 (0.928 to 0.965)     | 0.821 (0.776 to 0.864) | 0.973 (0.962 to 0.983) |
| 3b rule generalised                 | 0.964 (0.944 to 0.981) | 0.954 (0.919 to 0.987) | 0.968 (0.944 to 0.990) | 0.992 (0.988 to 0.996) | 0.999 (0.996 to 1.000)     | 0.982 (0.975 to 0.990) | 0.989 (0.985 to 0.993) |
| control: 3b pattern on random days  | 0.976 (0.962 to 0.987) | 0.921 (0.881 to 0.965) | 0.892 (0.858 to 0.928) | 0.854 (0.793 to 0.895) | 0.966 (0.947 to 0.983)     | 0.896 (0.877 to 0.914) | 0.980 (0.975 to 0.986) |
| exact, lambda 0.5                   | 0.959 (0.938 to 0.977) | 0.954 (0.919 to 0.987) | 0.968 (0.943 to 0.991) | 0.992 (0.988 to 0.996) | 1.000 (0.999 to 1.000)     | 0.982 (0.975 to 0.989) | 0.998 (0.996 to 0.999) |
| exact, lambda 1                     | 0.976 (0.963 to 0.988) | 0.953 (0.921 to 0.984) | 0.963 (0.937 to 0.984) | 0.991 (0.987 to 0.995) | 0.998 (0.997 to 0.999)     | 0.980 (0.972 to 0.988) | 0.997 (0.995 to 0.998) |
| exact, lambda 2                     | 0.984 (0.973 to 0.993) | 0.951 (0.920 to 0.984) | 0.961 (0.938 to 0.984) | 0.990 (0.986 to 0.994) | 0.997 (0.995 to 0.999)     | 0.979 (0.971 to 0.986) | 0.996 (0.995 to 0.998) |

Paired differences, iid_p0.3, Q = 12 (sites resampled, 95% interval); columns: record; pooled hard; pooled all
  ex1 minus heur: record +0.012 (+0.006 to +0.020); hard -0.001 (-0.002 to -0.000); all +0.008 (+0.004 to +0.012)
  ex05 minus heur: record -0.006 (-0.011 to +0.000); hard +0.000 (-0.000 to +0.001); all +0.009 (+0.005 to +0.012)
  ex2 minus heur: record +0.019 (+0.011 to +0.029); hard -0.002 (-0.004 to -0.001); all +0.007 (+0.004 to +0.011)
  ex1 minus randmix: record +0.001 (-0.003 to +0.005); hard +0.096 (+0.070 to +0.126); all +0.017 (+0.012 to +0.022)
  ex1 minus flat: record -0.005 (-0.008 to -0.001); hard +0.011 (+0.007 to +0.016); all +0.005 (+0.003 to +0.007)
  ex1 minus pet2: record +0.022 (+0.014 to +0.031); hard -0.001 (-0.002 to -0.000); all -0.001 (-0.001 to -0.000)
  ex1 minus rec: record -0.014 (-0.020 to -0.007); hard +0.168 (+0.133 to +0.208); all +0.029 (+0.020 to +0.039)
  heur minus randmix: record -0.011 (-0.017 to -0.006); hard +0.097 (+0.072 to +0.130); all +0.009 (+0.007 to +0.012)
  heur minus flat: record -0.017 (-0.028 to -0.008); hard +0.013 (+0.008 to +0.017); all -0.002 (-0.004 to -0.001)
  criterion 2 (exact lambda 1 vs 3b rule): hard +0.02 at record >= -0.005: False; record +0.02 at hard >= -0.005: False  ->  NOT MET

### gilbert_p0.3_b3
| design                              | record recovered       | DO, hard               | pH, hard               | conductance, hard      | 7DADM near windows, hard   | pooled, hard           | pooled, all            |
|:------------------------------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|:---------------------------|:-----------------------|:-----------------------|
| record only                         | 0.971 (0.963 to 0.978) | 0.806 (0.766 to 0.847) | 0.780 (0.743 to 0.826) | 0.669 (0.586 to 0.778) | 0.829 (0.788 to 0.866)     | 0.749 (0.710 to 0.792) | 0.943 (0.930 to 0.955) |
| flat (all witnesses in record code) | 0.943 (0.931 to 0.954) | 0.913 (0.881 to 0.946) | 0.930 (0.905 to 0.953) | 0.938 (0.931 to 0.947) | 0.809 (0.776 to 0.838)     | 0.906 (0.894 to 0.917) | 0.953 (0.948 to 0.959) |
| PET c=2 (all witnesses)             | 0.919 (0.896 to 0.938) | 0.939 (0.907 to 0.972) | 0.949 (0.921 to 0.970) | 0.970 (0.966 to 0.974) | 0.895 (0.886 to 0.903)     | 0.945 (0.936 to 0.952) | 0.973 (0.970 to 0.975) |
| spare slots                         | 0.971 (0.963 to 0.978) | 0.898 (0.862 to 0.936) | 0.843 (0.816 to 0.878) | 0.669 (0.579 to 0.773) | 0.842 (0.806 to 0.877)     | 0.781 (0.732 to 0.828) | 0.948 (0.936 to 0.960) |
| 3b rule generalised                 | 0.940 (0.919 to 0.959) | 0.947 (0.916 to 0.980) | 0.959 (0.933 to 0.982) | 0.981 (0.977 to 0.986) | 0.959 (0.951 to 0.967)     | 0.966 (0.959 to 0.974) | 0.966 (0.959 to 0.972) |
| control: 3b pattern on random days  | 0.950 (0.934 to 0.964) | 0.895 (0.858 to 0.936) | 0.871 (0.834 to 0.907) | 0.835 (0.766 to 0.876) | 0.882 (0.851 to 0.913)     | 0.862 (0.840 to 0.882) | 0.956 (0.948 to 0.963) |
| exact, lambda 0.5                   | 0.940 (0.919 to 0.959) | 0.942 (0.911 to 0.976) | 0.951 (0.925 to 0.974) | 0.971 (0.966 to 0.976) | 0.940 (0.927 to 0.953)     | 0.955 (0.948 to 0.963) | 0.980 (0.977 to 0.983) |
| exact, lambda 1                     | 0.956 (0.942 to 0.969) | 0.936 (0.904 to 0.969) | 0.939 (0.915 to 0.962) | 0.964 (0.958 to 0.970) | 0.931 (0.914 to 0.947)     | 0.947 (0.939 to 0.956) | 0.976 (0.972 to 0.980) |
| exact, lambda 2                     | 0.963 (0.951 to 0.973) | 0.932 (0.902 to 0.963) | 0.934 (0.909 to 0.957) | 0.961 (0.954 to 0.966) | 0.925 (0.906 to 0.943)     | 0.942 (0.934 to 0.951) | 0.975 (0.970 to 0.979) |

Paired differences, gilbert_p0.3_b3, Q = 12 (sites resampled, 95% interval); columns: record; pooled hard; pooled all
  ex1 minus heur: record +0.016 (+0.010 to +0.023); hard -0.018 (-0.023 to -0.013); all +0.010 (+0.007 to +0.013)
  ex05 minus heur: record -0.000 (-0.005 to +0.005); hard -0.011 (-0.015 to -0.008); all +0.014 (+0.010 to +0.019)
  ex2 minus heur: record +0.022 (+0.014 to +0.032); hard -0.021 (-0.028 to -0.015); all +0.009 (+0.006 to +0.011)
  ex1 minus randmix: record +0.007 (+0.002 to +0.013); hard +0.097 (+0.072 to +0.128); all +0.021 (+0.016 to +0.026)
  ex1 minus flat: record +0.014 (+0.010 to +0.017); hard +0.041 (+0.034 to +0.048); all +0.023 (+0.020 to +0.025)
  ex1 minus pet2: record +0.038 (+0.030 to +0.046); hard +0.009 (+0.002 to +0.017); all +0.003 (+0.001 to +0.006)
  ex1 minus rec: record -0.014 (-0.021 to -0.008); hard +0.177 (+0.142 to +0.215); all +0.034 (+0.025 to +0.044)
  heur minus randmix: record -0.009 (-0.014 to -0.005); hard +0.115 (+0.089 to +0.146); all +0.010 (+0.008 to +0.014)
  heur minus flat: record -0.002 (-0.011 to +0.005); hard +0.059 (+0.049 to +0.070); all +0.013 (+0.010 to +0.015)
  criterion 2 (exact lambda 1 vs 3b rule): hard +0.02 at record >= -0.005: False; record +0.02 at hard >= -0.005: False  ->  NOT MET

## Model-level objective and optimality gap (proto_gap.py)

```
Q = 6, lambda = 0.5: mean J, mean gap to exact, share of days at the optimum
  rec    J 3.5509  gap 0.6906  optimal on 0.255 of days
  flat   J 3.3060  gap 0.9355  optimal on 0.000 of days
  pet2   J 3.9692  gap 0.2723  optimal on 0.000 of days
  spare  J 3.6418  gap 0.5998  optimal on 0.258 of days
  heur   J 3.9018  gap 0.3397  optimal on 0.301 of days
  ex1    J 4.2415  gap 0.0000  optimal on 1.000 of days
Q = 6, lambda = 1.0: mean J, mean gap to exact, share of days at the optimum
  rec    J 3.9919  gap 0.6450  optimal on 0.255 of days
  flat   J 3.6733  gap 0.9635  optimal on 0.000 of days
  pet2   J 4.3233  gap 0.3136  optimal on 0.005 of days
  spare  J 4.0827  gap 0.5541  optimal on 0.258 of days
  heur   J 4.3046  gap 0.3322  optimal on 0.302 of days
  ex1    J 4.6368  gap 0.0000  optimal on 1.000 of days
Q = 6, lambda = 2.0: mean J, mean gap to exact, share of days at the optimum
  rec    J 4.8737  gap 0.5933  optimal on 0.277 of days
  flat   J 4.4080  gap 1.0590  optimal on 0.000 of days
  pet2   J 5.0314  gap 0.4355  optimal on 0.000 of days
  spare  J 4.9645  gap 0.5024  optimal on 0.281 of days
  heur   J 5.1102  gap 0.3568  optimal on 0.310 of days
  ex1    J 5.4670  gap 0.0000  optimal on 1.000 of days
Q = 12, lambda = 0.5: mean J, mean gap to exact, share of days at the optimum
  rec    J 3.9499  gap 0.5174  optimal on 0.267 of days
  flat   J 4.3484  gap 0.1189  optimal on 0.000 of days
  pet2   J 4.4555  gap 0.0118  optimal on 0.122 of days
  spare  J 4.0572  gap 0.4100  optimal on 0.270 of days
  heur   J 4.3899  gap 0.0773  optimal on 0.306 of days
  ex1    J 4.4673  gap 0.0000  optimal on 1.000 of days
Q = 12, lambda = 1.0: mean J, mean gap to exact, share of days at the optimum
  rec    J 4.4422  gap 0.5063  optimal on 0.288 of days
  flat   J 4.8316  gap 0.1169  optimal on 0.000 of days
  pet2   J 4.9245  gap 0.0240  optimal on 0.018 of days
  spare  J 4.5495  gap 0.3990  optimal on 0.292 of days
  heur   J 4.8673  gap 0.0812  optimal on 0.314 of days
  ex1    J 4.9485  gap 0.0000  optimal on 1.000 of days
Q = 12, lambda = 2.0: mean J, mean gap to exact, share of days at the optimum
  rec    J 5.4268  gap 0.4972  optimal on 0.293 of days
  flat   J 5.7979  gap 0.1261  optimal on 0.000 of days
  pet2   J 5.8624  gap 0.0616  optimal on 0.000 of days
  spare  J 5.5341  gap 0.3899  optimal on 0.301 of days
  heur   J 5.8221  gap 0.1019  optimal on 0.315 of days
  ex1    J 5.9240  gap 0.0000  optimal on 1.000 of days
```
