# Verdicts of the version 3 confirmation

| id   | type                                                                                              | statement                                                                                                                                                                                              | result                                                                                                                                                                                                                                                                         | verdict    |
|:-----|:--------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------|
| H1   | code check (holds by construction under assumption R)                                             | no wrong decision (byte check and slot model, Q 6 and 12, both loss models), no decoded value that differs from the plan, no decision-layer error, and no byte round-trip mismatch on any analysed day | byte wrong max 0.000; slot wrong max 0.000; value mismatches 0; decision-layer errors 0; round trip 0 mismatches in 41668 blocks (0 not buildable); byte days without a 3b block 0                                                                                             | pass       |
| H2   | test                                                                                              | byte level: 3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= 0.1 (Q 6 and 12, both loss models)                                                                          | +0.226 (+0.196 to +0.258) / +0.189 (+0.165 to +0.215) / +0.182 (+0.154 to +0.214) / +0.191 (+0.164 to +0.222)                                                                                                                                                                  | pass       |
| H3   | test                                                                                              | byte level: 3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= 0.1 (all four)                                                                                           | +0.275 (+0.233 to +0.324) / +0.249 (+0.212 to +0.292) / +0.197 (+0.160 to +0.246) / +0.217 (+0.181 to +0.263)                                                                                                                                                                  | pass       |
| H4   | test                                                                                              | byte level: cost of the post-hoc adopted design, 3b rule minus record only, whole record recovered, lower bound >= -0.15 (Q 6) and >= -0.1 (Q 12), both loss models                                    | -0.082 (-0.099 to -0.064) / -0.068 (-0.081 to -0.055) / -0.026 (-0.035 to -0.017) / -0.032 (-0.041 to -0.023)                                                                                                                                                                  | pass       |
| H6   | known limit (flags are exact at the configured thresholds by construction)                        | byte level: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus flagsrec) < 0.0 (Q 6, both loss models)                                             | -0.028 (-0.034 to -0.022) / -0.107 (-0.117 to -0.099)                                                                                                                                                                                                                          | pass       |
| H7   | analytic bound (cannot fail: the ceiling with a conditional share of 1 is below any useful limit) | expected false-certificate days per million days at bit-error rate 0.001 under random corruption                                                                                                       | heur Q6: 0.0030 (upper 0.0035; ceiling 0.042); heur Q12: 0.0008 (upper 0.0012; ceiling 0.084); rec Q6: 0.0022 (upper 0.0026; ceiling 0.042); rec Q12: 0.0006 (upper 0.0009; ceiling 0.084)                                                                                     | not a test |
| H8   | code check (the slot model of the record only is the frame's code)                                | record only: byte frame and slot model agree in whole-record recovery, |difference| <= 0.01 (Q 6 and 12, both loss models)                                                                             | Q6 gilbert_p0.3_b3: byte 0.776, slot 0.775, |diff| 0.001 (10417 days); Q6 iid_p0.3: byte 0.842, slot 0.842, |diff| 0.001 (10417 days); Q12 gilbert_p0.3_b3: byte 0.939, slot 0.939, |diff| 0.000 (10417 days); Q12 iid_p0.3: byte 0.964, slot 0.963, |diff| 0.000 (10417 days) | pass       |

## Descriptive results (no verdict)

Assumption R (reporting resolution inferred from the record): 26 of 35 analysed sites have an inferred resolution for at least one of DO, pH, temperature; per parameter: {'DO': 14, 'pH': 23, 'T': 11}.

Byte check (hypotheses), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.842 / 0.608 / 0.523 / 0.857
  heur      0.760 / 0.971 / 0.798 / 0.882
  flagsrec  0.842 / 0.999 / 0.572 / 0.999

Byte check (hypotheses), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.776 / 0.527 / 0.455 / 0.767
  heur      0.707 / 0.854 / 0.704 / 0.793
  flagsrec  0.776 / 0.961 / 0.515 / 0.963

Byte check (hypotheses), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.964 / 0.758 / 0.646 / 0.954
  heur      0.937 / 0.986 / 0.844 / 0.976
  flagsrec  0.964 / 1.000 / 0.662 / 1.000

Byte check (hypotheses), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.939 / 0.710 / 0.607 / 0.924
  heur      0.907 / 0.970 / 0.825 / 0.948
  flagsrec  0.939 / 0.996 / 0.634 / 0.997

Slot model (cross-check), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.842 / 0.612 / 0.525 / 0.858
  heur      0.724 / 0.974 / 0.777 / 0.873
  flags     0.842 / 0.999 / 0.199 / 0.999
  flagsrec  0.842 / 0.999 / 0.574 / 0.999

Slot model (cross-check), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.775 / 0.524 / 0.453 / 0.765
  heur      0.677 / 0.861 / 0.689 / 0.787
  flags     0.775 / 0.960 / 0.191 / 0.960
  flagsrec  0.775 / 0.960 / 0.514 / 0.962

Slot model (cross-check), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.963 / 0.758 / 0.647 / 0.954
  heur      0.908 / 0.987 / 0.820 / 0.967
  flags     0.963 / 1.000 / 0.199 / 1.000
  flagsrec  0.963 / 1.000 / 0.662 / 1.000

Slot model (cross-check), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.939 / 0.712 / 0.608 / 0.924
  heur      0.880 / 0.972 / 0.804 / 0.942
  flags     0.939 / 0.996 / 0.198 / 0.996
  flagsrec  0.939 / 0.996 / 0.634 / 0.997

Byte check, Q = 6: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.657 / heur 0.875 / flagsrec 0.712; 3b minus flagsrec +0.162 (+0.113 to +0.216); 3b minus record +0.217 (+0.138 to +0.316)
  iid_p0.3 do_cfg    rec 0.630 / heur 0.963 / flagsrec 0.999; 3b minus flagsrec -0.036 (-0.059 to -0.015); 3b minus record +0.333 (+0.239 to +0.453)
  iid_p0.3 ph_alt    rec 0.735 / heur 0.862 / flagsrec 0.756; 3b minus flagsrec +0.106 (+0.066 to +0.151); 3b minus record +0.127 (+0.081 to +0.178)
  iid_p0.3 ph_cfg    rec 0.727 / heur 0.971 / flagsrec 0.999; 3b minus flagsrec -0.028 (-0.055 to -0.011); 3b minus record +0.244 (+0.152 to +0.351)
  iid_p0.3 ec_alt    rec 0.320 / heur 0.688 / flagsrec 0.377; 3b minus flagsrec +0.311 (+0.279 to +0.341); 3b minus record +0.368 (+0.318 to +0.424)
  iid_p0.3 ec_cfg    rec 0.553 / heur 0.979 / flagsrec 0.999; 3b minus flagsrec -0.020 (-0.024 to -0.016); 3b minus record +0.426 (+0.368 to +0.485)
  iid_p0.3 win7_alt  rec 0.605 / heur 0.940 / flagsrec 0.682; 3b minus flagsrec +0.258 (+0.216 to +0.296); 3b minus record +0.335 (+0.284 to +0.381)
  iid_p0.3 win7_cfg  rec 0.623 / heur 0.957 / flagsrec 0.999; 3b minus flagsrec -0.043 (-0.057 to -0.030); 3b minus record +0.334 (+0.282 to +0.387)
  gilbert_p0.3_b3 do_alt    rec 0.618 / heur 0.824 / flagsrec 0.679; 3b minus flagsrec +0.145 (+0.099 to +0.195); 3b minus record +0.206 (+0.136 to +0.298)
  gilbert_p0.3_b3 do_cfg    rec 0.600 / heur 0.898 / flagsrec 0.962; 3b minus flagsrec -0.063 (-0.087 to -0.040); 3b minus record +0.298 (+0.219 to +0.406)
  gilbert_p0.3_b3 ph_alt    rec 0.676 / heur 0.792 / flagsrec 0.697; 3b minus flagsrec +0.095 (+0.061 to +0.134); 3b minus record +0.116 (+0.075 to +0.162)
  gilbert_p0.3_b3 ph_cfg    rec 0.681 / heur 0.890 / flagsrec 0.961; 3b minus flagsrec -0.071 (-0.096 to -0.054); 3b minus record +0.209 (+0.129 to +0.301)
  gilbert_p0.3_b3 ec_alt    rec 0.294 / heur 0.629 / flagsrec 0.359; 3b minus flagsrec +0.270 (+0.241 to +0.296); 3b minus record +0.335 (+0.290 to +0.383)
  gilbert_p0.3_b3 ec_cfg    rec 0.505 / heur 0.896 / flagsrec 0.961; 3b minus flagsrec -0.065 (-0.069 to -0.060); 3b minus record +0.392 (+0.342 to +0.445)
  gilbert_p0.3_b3 win7_alt  rec 0.365 / heur 0.654 / flagsrec 0.490; 3b minus flagsrec +0.163 (+0.130 to +0.196); 3b minus record +0.289 (+0.255 to +0.320)
  gilbert_p0.3_b3 win7_cfg  rec 0.380 / heur 0.672 / flagsrec 0.961; 3b minus flagsrec -0.289 (-0.309 to -0.268); 3b minus record +0.292 (+0.251 to +0.332)

Byte check, Q = 12: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.770 / heur 0.931 / flagsrec 0.798; 3b minus flagsrec +0.133 (+0.091 to +0.180); 3b minus record +0.161 (+0.097 to +0.241)
  iid_p0.3 do_cfg    rec 0.754 / heur 0.969 / flagsrec 1.000; 3b minus flagsrec -0.031 (-0.055 to -0.007); 3b minus record +0.215 (+0.140 to +0.319)
  iid_p0.3 ph_alt    rec 0.833 / heur 0.952 / flagsrec 0.841; 3b minus flagsrec +0.111 (+0.071 to +0.156); 3b minus record +0.119 (+0.078 to +0.167)
  iid_p0.3 ph_cfg    rec 0.858 / heur 0.981 / flagsrec 1.000; 3b minus flagsrec -0.019 (-0.041 to -0.001); 3b minus record +0.124 (+0.046 to +0.212)
  iid_p0.3 ec_alt    rec 0.403 / heur 0.701 / flagsrec 0.423; 3b minus flagsrec +0.277 (+0.243 to +0.313); 3b minus record +0.297 (+0.250 to +0.357)
  iid_p0.3 ec_cfg    rec 0.658 / heur 0.990 / flagsrec 1.000; 3b minus flagsrec -0.010 (-0.013 to -0.006); 3b minus record +0.332 (+0.281 to +0.387)
  iid_p0.3 win7_alt  rec 0.912 / heur 0.991 / flagsrec 0.919; 3b minus flagsrec +0.072 (+0.048 to +0.104); 3b minus record +0.079 (+0.052 to +0.115)
  iid_p0.3 win7_cfg  rec 0.931 / heur 0.993 / flagsrec 1.000; 3b minus flagsrec -0.007 (-0.013 to -0.002); 3b minus record +0.062 (+0.039 to +0.088)
  gilbert_p0.3_b3 do_alt    rec 0.742 / heur 0.918 / flagsrec 0.777; 3b minus flagsrec +0.141 (+0.100 to +0.185); 3b minus record +0.176 (+0.115 to +0.254)
  gilbert_p0.3_b3 do_cfg    rec 0.724 / heur 0.961 / flagsrec 0.996; 3b minus flagsrec -0.035 (-0.059 to -0.012); 3b minus record +0.237 (+0.164 to +0.333)
  gilbert_p0.3_b3 ph_alt    rec 0.809 / heur 0.927 / flagsrec 0.818; 3b minus flagsrec +0.109 (+0.070 to +0.154); 3b minus record +0.119 (+0.078 to +0.168)
  gilbert_p0.3_b3 ph_cfg    rec 0.832 / heur 0.972 / flagsrec 0.996; 3b minus flagsrec -0.024 (-0.047 to -0.008); 3b minus record +0.140 (+0.064 to +0.229)
  gilbert_p0.3_b3 ec_alt    rec 0.381 / heur 0.692 / flagsrec 0.412; 3b minus flagsrec +0.280 (+0.248 to +0.313); 3b minus record +0.311 (+0.269 to +0.367)
  gilbert_p0.3_b3 ec_cfg    rec 0.628 / heur 0.979 / flagsrec 0.996; 3b minus flagsrec -0.017 (-0.021 to -0.013); 3b minus record +0.351 (+0.303 to +0.401)
  gilbert_p0.3_b3 win7_alt  rec 0.785 / heur 0.946 / flagsrec 0.821; 3b minus flagsrec +0.125 (+0.104 to +0.150); 3b minus record +0.162 (+0.137 to +0.191)
  gilbert_p0.3_b3 win7_cfg  rec 0.801 / heur 0.951 / flagsrec 0.996; 3b minus flagsrec -0.045 (-0.057 to -0.035); 3b minus record +0.150 (+0.126 to +0.175)

Whole-record recovery, byte frame against slot model (the slot model gives the layered group whole slots, so it is pessimistic for the 3b rule):
  Q= 6 gilbert_p0.3_b3  flagsrec  byte 0.776, slot 0.775, difference +0.001 (10417 days)
  Q= 6 gilbert_p0.3_b3  heur      byte 0.707, slot 0.677, difference +0.030 (10417 days)
  Q= 6 gilbert_p0.3_b3  rec       byte 0.776, slot 0.775, difference +0.001 (10417 days)
  Q= 6 iid_p0.3         flagsrec  byte 0.842, slot 0.842, difference -0.001 (10417 days)
  Q= 6 iid_p0.3         heur      byte 0.760, slot 0.724, difference +0.036 (10417 days)
  Q= 6 iid_p0.3         rec       byte 0.842, slot 0.842, difference -0.001 (10417 days)
  Q=12 gilbert_p0.3_b3  flagsrec  byte 0.939, slot 0.939, difference -0.000 (10417 days)
  Q=12 gilbert_p0.3_b3  heur      byte 0.907, slot 0.880, difference +0.027 (10417 days)
  Q=12 gilbert_p0.3_b3  rec       byte 0.939, slot 0.939, difference -0.000 (10417 days)
  Q=12 iid_p0.3         flagsrec  byte 0.964, slot 0.963, difference +0.000 (10417 days)
  Q=12 iid_p0.3         heur      byte 0.937, slot 0.908, difference +0.029 (10417 days)
  Q=12 iid_p0.3         rec       byte 0.964, slot 0.963, difference +0.000 (10417 days)

Integrity, given one CRC-valid forgery (header or body): classes of day (share of draws / false-certificate share in class); rejected share; day with a wrong decision (point, site-clustered 95% interval); decision-layer errors
  heur  Q= 6: N<K 0.15/0.1648; N=K 0.15/0.2158; N>K 0.61/0.0000; uncoded 0.10/0.1745; rejected 0.799; wrong decision 0.0219 (0.0184 to 0.0255); errors 0
  heur  Q=12: N<K 0.03/0.1093; N=K 0.02/0.1721; N>K 0.92/0.0000; uncoded 0.03/0.1127; rejected 0.908; wrong decision 0.0024 (0.0016 to 0.0033); errors 0
  rec   Q= 6: N<K 0.10/0.1464; N=K 0.13/0.2143; N>K 0.72/0.0000; uncoded 0.06/0.1705; rejected 0.805; wrong decision 0.0187 (0.0152 to 0.0226); errors 0
  rec   Q=12: N<K 0.02/0.1116; N=K 0.01/0.1636; N>K 0.95/0.0000; uncoded 0.02/0.1543; rejected 0.909; wrong decision 0.0017 (0.0010 to 0.0026); errors 0
