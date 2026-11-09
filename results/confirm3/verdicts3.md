# Verdicts of the third confirmation

| id   | statement                                                                                                                                                                                                  | result                                                                                                                                                                                           | supported   |
|:-----|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|
| H1   | no wrong certificate decision in any certificate design (Q 6 and 12, both loss models) and no frame v2 round-trip mismatch                                                                                 | wrong decisions max 0.000; round trip: 0 mismatches in 30285 blocks                                                                                                                              | True        |
| H2   | 3b rule minus record only, hard-case decisions at the configured thresholds, lower bound >= 0.15 (Q = 6, both loss models)                                                                                 | +0.318 (+0.234 to +0.417) / +0.300 (+0.223 to +0.390)                                                                                                                                            | True        |
| H3   | 3b rule minus the same layering on random days, hard-case decisions, lower bound >= 0.05 (Q = 6, both)                                                                                                     | +0.141 (+0.105 to +0.174) / +0.130 (+0.096 to +0.165)                                                                                                                                            | True        |
| H4   | record recovered, 3b rule minus record only, lower bound >= -0.12 (Q = 6, both)                                                                                                                            | -0.083 (-0.105 to -0.062) / -0.071 (-0.091 to -0.053)                                                                                                                                            | True        |
| H5   | unanticipated thresholds: 3b rule minus flags >= 0.1 and minus record only >= 0.1 (lower bounds, Q = 6, both)                                                                                              | flags: +0.531 (+0.494 to +0.569) / +0.441 (+0.411 to +0.472); record only: +0.260 (+0.191 to +0.344) / +0.245 (+0.184 to +0.320)                                                                 | True        |
| H6   | neither coded send-on-delta nor tolerance x 0.5 dominates the 3b rule on (record recovered, hard-case decisions), Q = 6, both                                                                              | sod_mds/iid_p0.3: no; tight50/iid_p0.3: no; sod_mds/gilbert_p0.3_b3: no; tight50/gilbert_p0.3_b3: no                                                                                             | True        |
| H7   | known limit: decision flags exceed the 3b rule in hard-case decisions at the configured thresholds (lower bound > 0, Q = 6, independent loss)                                                              | +0.043 (+0.025 to +0.068)                                                                                                                                                                        | True        |
| H8   | conditional false-certificate day share given one CRC-valid forgery (CRC + sanity + corroboration), upper bound within limits                                                                              | record Q6: 0.0463 (upper 0.0584, limit 0.06); record Q12: 0.0061 (upper 0.0134, limit 0.01); layered k2 Q6: 0.1050 (upper 0.1197, limit 0.15); layered k2 Q12: 0.0126 (upper 0.0215, limit 0.02) | False       |
| H9   | hybrid 1 (flags with all witnesses hosted in spare slots) minus flags, Q = 6, both: unanticipated thresholds lower bound >= 0.2; configured hard-case decisions and record recovered lower bounds >= -0.01 | alt: +0.355 (+0.297 to +0.418) / +0.294 (+0.248 to +0.345); cfg: +0.000 (+0.000 to +0.000) / +0.000 (+0.000 to +0.000); record: +0.000 (+0.000 to +0.000) / +0.000 (+0.000 to +0.000)            | True        |

## Descriptive secondary results (no verdict)

Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard alternative / all configured)
  rec       0.892 / 0.638 / 0.546 / 0.883
  heur      0.809 / 0.956 / 0.806 / 0.923
  ex1       0.837 / 0.941 / 0.748 / 0.972
  tight50   0.698 / 0.524 / 0.526 / 0.754
  sod_mds   0.533 / 0.396 / 0.369 / 0.620
  sod_once  0.237 / 0.327 / 0.304 / 0.444
  flags     0.877 / 0.999 / 0.275 / 0.999
  randmix   0.812 / 0.815 / 0.707 / 0.914
  hyb1      0.877 / 0.999 / 0.629 / 0.999
  hyb2      0.779 / 0.999 / 0.806 / 0.999
  exact lambda 1 minus 3b rule: rec +0.028 / hard_cfg -0.015 / hard_alt -0.057 / all_cfg +0.049

Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard alternative / all configured)
  rec       0.817 / 0.536 / 0.460 / 0.783
  heur      0.746 / 0.836 / 0.705 / 0.824
  ex1       0.759 / 0.810 / 0.644 / 0.869
  tight50   0.652 / 0.458 / 0.464 / 0.675
  sod_mds   0.520 / 0.341 / 0.321 / 0.567
  sod_once  0.355 / 0.302 / 0.284 / 0.453
  flags     0.804 / 0.960 / 0.264 / 0.960
  randmix   0.747 / 0.706 / 0.615 / 0.816
  hyb1      0.804 / 0.960 / 0.557 / 0.962
  hyb2      0.723 / 0.960 / 0.725 / 0.963
  exact lambda 1 minus 3b rule: rec +0.013 / hard_cfg -0.026 / hard_alt -0.061 / all_cfg +0.046

Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard alternative / all configured)
  rec       0.972 / 0.759 / 0.641 / 0.950
  heur      0.941 / 0.971 / 0.828 / 0.981
  ex1       0.956 / 0.969 / 0.742 / 0.994
  tight50   0.916 / 0.760 / 0.733 / 0.927
  sod_mds   0.864 / 0.610 / 0.570 / 0.857
  sod_once  0.249 / 0.405 / 0.380 / 0.509
  flags     0.969 / 1.000 / 0.275 / 1.000
  randmix   0.946 / 0.887 / 0.766 / 0.972
  hyb1      0.969 / 1.000 / 0.692 / 1.000
  hyb2      0.930 / 1.000 / 0.828 / 1.000
  exact lambda 1 minus 3b rule: rec +0.016 / hard_cfg -0.002 / hard_alt -0.086 / all_cfg +0.013

Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard alternative / all configured)
  rec       0.954 / 0.721 / 0.610 / 0.926
  heur      0.917 / 0.955 / 0.813 / 0.959
  ex1       0.937 / 0.937 / 0.718 / 0.974
  tight50   0.882 / 0.699 / 0.680 / 0.883
  sod_mds   0.828 / 0.547 / 0.518 / 0.807
  sod_once  0.408 / 0.384 / 0.369 / 0.529
  flags     0.949 / 0.997 / 0.274 / 0.996
  randmix   0.922 / 0.857 / 0.741 / 0.949
  hyb1      0.949 / 0.997 / 0.669 / 0.997
  hyb2      0.905 / 0.997 / 0.815 / 0.997
  exact lambda 1 minus 3b rule: rec +0.020 / hard_cfg -0.018 / hard_alt -0.094 / all_cfg +0.015
