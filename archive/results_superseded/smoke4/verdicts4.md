# Verdicts of the version 3 confirmation (REHEARSAL on development data, not confirmatory)

| id   | type                                                                                              | statement                                                                                                                                                                                              | result                                                                                                                                                                                                                                                                 | verdict    |
|:-----|:--------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------|
| H1   | code check (holds by construction under assumption R)                                             | no wrong decision (byte check and slot model, Q 6 and 12, both loss models), no decoded value that differs from the plan, no decision-layer error, and no byte round-trip mismatch on any analysed day | byte wrong max 0.000; slot wrong max 0.000; value mismatches 0; decision-layer errors 0; round trip 0 mismatches in 2860 blocks (0 not buildable); byte days without a 3b block 0                                                                                      | pass       |
| H2   | test                                                                                              | byte level: 3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= 0.1 (Q 6 and 12, both loss models)                                                                          | +0.282 (+0.236 to +0.289) / +0.218 (+0.214 to +0.218) / +0.238 (+0.238 to +0.239) / +0.239 (+0.234 to +0.240)                                                                                                                                                          | pass       |
| H3   | test                                                                                              | byte level: 3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= 0.1 (all four)                                                                                           | +0.327 (+0.236 to +0.340) / +0.275 (+0.214 to +0.284) / +0.240 (+0.238 to +0.240) / +0.254 (+0.234 to +0.257)                                                                                                                                                          | pass       |
| H4   | test                                                                                              | byte level: cost of the post-hoc adopted design, 3b rule minus record only, whole record recovered, lower bound >= -0.15 (Q 6) and >= -0.1 (Q 12), both loss models                                    | -0.086 (-0.170 to -0.002) / -0.074 (-0.144 to -0.005) / -0.020 (-0.041 to +0.000) / -0.028 (-0.055 to -0.001)                                                                                                                                                          | fail       |
| H6   | known limit (flags are exact at the configured thresholds by construction)                        | byte level: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus flagsrec) < 0.0 (Q 6, both loss models)                                             | -0.022 (-0.023 to +0.000) / -0.111 (-0.112 to -0.054)                                                                                                                                                                                                                  | fail       |
| H7   | analytic bound (cannot fail: the ceiling with a conditional share of 1 is below any useful limit) | expected false-certificate days per million days at bit-error rate 0.001 under random corruption                                                                                                       | heur Q6: 0.0019 (upper 0.0034; ceiling 0.042); heur Q12: 0.0002 (upper 0.0004; ceiling 0.084); rec Q6: 0.0013 (upper 0.0023; ceiling 0.042); rec Q12: 0.0000 (upper 0.0001; ceiling 0.084)                                                                             | not a test |
| H8   | code check (the slot model of the record only is the frame's code)                                | record only: byte frame and slot model agree in whole-record recovery, |difference| <= 0.01 (Q 6 and 12, both loss models)                                                                             | Q6 gilbert_p0.3_b3: byte 0.873, slot 0.879, |diff| 0.005 (715 days); Q6 iid_p0.3: byte 0.945, slot 0.948, |diff| 0.003 (715 days); Q12 gilbert_p0.3_b3: byte 0.982, slot 0.983, |diff| 0.001 (715 days); Q12 iid_p0.3: byte 0.999, slot 0.998, |diff| 0.001 (715 days) | pass       |

## Descriptive results (no verdict)

Assumption R (reporting resolution inferred from the record): 2 of 2 analysed sites have an inferred resolution for at least one of DO, pH, temperature; per parameter: {'DO': 0, 'pH': 2, 'T': 1}.

Byte check (hypotheses), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.945 / 0.789 / 0.502 / 0.926
  heur      0.859 / 0.978 / 0.828 / 0.963
  flagsrec  0.945 / 1.000 / 0.546 / 1.000

Byte check (hypotheses), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.873 / 0.698 / 0.437 / 0.839
  heur      0.799 / 0.848 / 0.713 / 0.865
  flagsrec  0.873 / 0.959 / 0.495 / 0.964

Byte check (hypotheses), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.999 / 0.915 / 0.614 / 0.980
  heur      0.979 / 0.997 / 0.854 / 0.999
  flagsrec  0.999 / 1.000 / 0.616 / 1.000

Byte check (hypotheses), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.982 / 0.871 / 0.578 / 0.956
  heur      0.954 / 0.974 / 0.832 / 0.977
  flagsrec  0.982 / 0.995 / 0.592 / 0.996

Slot model (cross-check), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.948 / 0.793 / 0.506 / 0.927
  heur      0.791 / 0.982 / 0.793 / 0.939
  flags     0.948 / 0.999 / 0.240 / 0.999
  flagsrec  0.948 / 0.999 / 0.549 / 0.999

Slot model (cross-check), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.879 / 0.708 / 0.445 / 0.849
  heur      0.744 / 0.872 / 0.700 / 0.864
  flags     0.879 / 0.962 / 0.231 / 0.963
  flagsrec  0.879 / 0.962 / 0.501 / 0.966

Slot model (cross-check), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.998 / 0.910 / 0.609 / 0.978
  heur      0.901 / 0.997 / 0.814 / 0.993
  flags     0.998 / 1.000 / 0.240 / 1.000
  flagsrec  0.998 / 1.000 / 0.613 / 1.000

Slot model (cross-check), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.983 / 0.879 / 0.583 / 0.959
  heur      0.886 / 0.980 / 0.799 / 0.973
  flags     0.983 / 0.996 / 0.239 / 0.997
  flagsrec  0.983 / 0.996 / 0.595 / 0.997

Byte check, Q = 6: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.864 / heur 0.945 / flagsrec 0.883; 3b minus flagsrec +0.062 (+0.000 to +0.062); 3b minus record +0.081 (+0.000 to +0.081)
  iid_p0.3 do_cfg    rec 0.898 / heur 0.978 / flagsrec 1.000; 3b minus flagsrec -0.022 (-0.022 to +0.000); 3b minus record +0.080 (+0.000 to +0.080)
  iid_p0.3 ph_alt    rec 0.594 / heur 0.981 / flagsrec 0.608; 3b minus flagsrec +0.373 (+0.000 to +0.373); 3b minus record +0.387 (+0.000 to +0.387)
  iid_p0.3 ph_cfg    rec 0.887 / heur 0.990 / flagsrec 1.000; 3b minus flagsrec -0.009 (-0.009 to +0.000); 3b minus record +0.103 (+0.000 to +0.103)
  iid_p0.3 ec_alt    rec 0.154 / heur 0.520 / flagsrec 0.175; 3b minus flagsrec +0.345 (+0.236 to +0.430); 3b minus record +0.366 (+0.236 to +0.468)
  iid_p0.3 ec_cfg    rec 0.696 / heur 0.991 / flagsrec 1.000; 3b minus flagsrec -0.009 (-0.010 to +0.000); 3b minus record +0.295 (+0.077 to +0.325)
  iid_p0.3 win7_alt  rec 0.414 / heur 0.915 / flagsrec 0.622; 3b minus flagsrec +0.293 (+0.000 to +0.293); 3b minus record +0.502 (+0.000 to +0.502)
  iid_p0.3 win7_cfg  rec 0.412 / heur 0.921 / flagsrec 1.000; 3b minus flagsrec -0.079 (-0.079 to +0.000); 3b minus record +0.509 (+0.000 to +0.509)
  gilbert_p0.3_b3 do_alt    rec 0.787 / heur 0.880 / flagsrec 0.825; 3b minus flagsrec +0.055 (+0.000 to +0.055); 3b minus record +0.093 (+0.000 to +0.093)
  gilbert_p0.3_b3 do_cfg    rec 0.818 / heur 0.902 / flagsrec 0.959; 3b minus flagsrec -0.057 (-0.057 to +0.000); 3b minus record +0.085 (+0.000 to +0.085)
  gilbert_p0.3_b3 ph_alt    rec 0.534 / heur 0.890 / flagsrec 0.556; 3b minus flagsrec +0.335 (+0.000 to +0.335); 3b minus record +0.356 (+0.000 to +0.356)
  gilbert_p0.3_b3 ph_cfg    rec 0.807 / heur 0.902 / flagsrec 0.960; 3b minus flagsrec -0.058 (-0.058 to +0.000); 3b minus record +0.096 (+0.000 to +0.096)
  gilbert_p0.3_b3 ec_alt    rec 0.144 / heur 0.469 / flagsrec 0.168; 3b minus flagsrec +0.301 (+0.214 to +0.369); 3b minus record +0.325 (+0.214 to +0.412)
  gilbert_p0.3_b3 ec_cfg    rec 0.626 / heur 0.900 / flagsrec 0.956; 3b minus flagsrec -0.055 (-0.056 to -0.054); 3b minus record +0.275 (+0.077 to +0.301)
  gilbert_p0.3_b3 win7_alt  rec 0.250 / heur 0.524 / flagsrec 0.493; 3b minus flagsrec +0.031 (+0.000 to +0.031); 3b minus record +0.274 (+0.000 to +0.274)
  gilbert_p0.3_b3 win7_cfg  rec 0.241 / heur 0.530 / flagsrec 0.961; 3b minus flagsrec -0.431 (-0.431 to +0.000); 3b minus record +0.288 (+0.000 to +0.288)

Byte check, Q = 12: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.910 / heur 0.969 / flagsrec 0.911; 3b minus flagsrec +0.058 (+0.000 to +0.058); 3b minus record +0.059 (+0.000 to +0.059)
  iid_p0.3 do_cfg    rec 0.946 / heur 0.987 / flagsrec 1.000; 3b minus flagsrec -0.013 (-0.013 to +0.000); 3b minus record +0.041 (+0.000 to +0.041)
  iid_p0.3 ph_alt    rec 0.640 / heur 1.000 / flagsrec 0.640; 3b minus flagsrec +0.360 (+0.000 to +0.360); 3b minus record +0.360 (+0.000 to +0.360)
  iid_p0.3 ph_cfg    rec 0.949 / heur 1.000 / flagsrec 1.000; 3b minus flagsrec +0.000 (+0.000 to +0.000); 3b minus record +0.051 (+0.000 to +0.051)
  iid_p0.3 ec_alt    rec 0.205 / heur 0.530 / flagsrec 0.205; 3b minus flagsrec +0.325 (+0.238 to +0.393); 3b minus record +0.325 (+0.238 to +0.394)
  iid_p0.3 ec_cfg    rec 0.780 / heur 1.000 / flagsrec 1.000; 3b minus flagsrec +0.000 (+0.000 to +0.000); 3b minus record +0.220 (+0.077 to +0.239)
  iid_p0.3 win7_alt  rec 0.923 / heur 0.994 / flagsrec 0.932; 3b minus flagsrec +0.062 (+0.000 to +0.062); 3b minus record +0.071 (+0.000 to +0.071)
  iid_p0.3 win7_cfg  rec 0.916 / heur 1.000 / flagsrec 1.000; 3b minus flagsrec +0.000 (+0.000 to +0.000); 3b minus record +0.084 (+0.000 to +0.084)
  gilbert_p0.3_b3 do_alt    rec 0.888 / heur 0.956 / flagsrec 0.896; 3b minus flagsrec +0.060 (+0.000 to +0.060); 3b minus record +0.068 (+0.000 to +0.068)
  gilbert_p0.3_b3 do_cfg    rec 0.923 / heur 0.975 / flagsrec 0.995; 3b minus flagsrec -0.020 (-0.020 to +0.000); 3b minus record +0.052 (+0.000 to +0.052)
  gilbert_p0.3_b3 ph_alt    rec 0.624 / heur 0.986 / flagsrec 0.626; 3b minus flagsrec +0.360 (+0.000 to +0.360); 3b minus record +0.362 (+0.000 to +0.362)
  gilbert_p0.3_b3 ph_cfg    rec 0.926 / heur 0.988 / flagsrec 0.995; 3b minus flagsrec -0.006 (-0.006 to +0.000); 3b minus record +0.063 (+0.000 to +0.063)
  gilbert_p0.3_b3 ec_alt    rec 0.191 / heur 0.521 / flagsrec 0.199; 3b minus flagsrec +0.323 (+0.234 to +0.392); 3b minus record +0.330 (+0.234 to +0.405)
  gilbert_p0.3_b3 ec_cfg    rec 0.749 / heur 0.986 / flagsrec 0.995; 3b minus flagsrec -0.009 (-0.015 to -0.008); 3b minus record +0.238 (+0.077 to +0.259)
  gilbert_p0.3_b3 win7_alt  rec 0.766 / heur 0.906 / flagsrec 0.835; 3b minus flagsrec +0.071 (+0.000 to +0.071); 3b minus record +0.140 (+0.000 to +0.140)
  gilbert_p0.3_b3 win7_cfg  rec 0.756 / heur 0.911 / flagsrec 0.995; 3b minus flagsrec -0.084 (-0.084 to +0.000); 3b minus record +0.155 (+0.000 to +0.155)

Whole-record recovery, byte frame against slot model (the slot model gives the layered group whole slots, so it is pessimistic for the 3b rule):
  Q= 6 gilbert_p0.3_b3  flagsrec  byte 0.873, slot 0.879, difference -0.005 (715 days)
  Q= 6 gilbert_p0.3_b3  heur      byte 0.799, slot 0.744, difference +0.055 (715 days)
  Q= 6 gilbert_p0.3_b3  rec       byte 0.873, slot 0.879, difference -0.005 (715 days)
  Q= 6 iid_p0.3         flagsrec  byte 0.945, slot 0.948, difference -0.003 (715 days)
  Q= 6 iid_p0.3         heur      byte 0.859, slot 0.791, difference +0.068 (715 days)
  Q= 6 iid_p0.3         rec       byte 0.945, slot 0.948, difference -0.003 (715 days)
  Q=12 gilbert_p0.3_b3  flagsrec  byte 0.982, slot 0.983, difference -0.001 (715 days)
  Q=12 gilbert_p0.3_b3  heur      byte 0.954, slot 0.886, difference +0.068 (715 days)
  Q=12 gilbert_p0.3_b3  rec       byte 0.982, slot 0.983, difference -0.001 (715 days)
  Q=12 iid_p0.3         flagsrec  byte 0.999, slot 0.998, difference +0.001 (715 days)
  Q=12 iid_p0.3         heur      byte 0.979, slot 0.901, difference +0.078 (715 days)
  Q=12 iid_p0.3         rec       byte 0.999, slot 0.998, difference +0.001 (715 days)

Integrity, given one CRC-valid forgery (header or body): classes of day (share of draws / false-certificate share in class); rejected share; day with a wrong decision (point, site-clustered 95% interval); decision-layer errors
  heur  Q= 6: N<K 0.07/0.1953; N=K 0.10/0.2328; N>K 0.78/0.0000; uncoded 0.05/0.1442; rejected 0.856; wrong decision 0.0147 (0.0000 to 0.0294); errors 0
  heur  Q=12: N<K 0.01/0.0385; N=K 0.01/0.1200; N>K 0.97/0.0000; uncoded 0.00/0.0000; rejected 0.922; wrong decision 0.0005 (0.0000 to 0.0011); errors 0
  rec   Q= 6: N<K 0.04/0.1951; N=K 0.09/0.2410; N>K 0.87/0.0000; uncoded 0.00/0.2500; rejected 0.860; wrong decision 0.0136 (0.0000 to 0.0274); errors 0
  rec   Q=12: N<K 0.00/0.0000; N=K 0.00/0.1667; N>K 1.00/0.0000; rejected 0.927; wrong decision 0.0005 (0.0000 to 0.0011); errors 0
