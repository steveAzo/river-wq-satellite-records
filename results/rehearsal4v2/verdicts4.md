# Verdicts of the version 3 confirmation (REHEARSAL on development data, not confirmatory)

| id   | type                                                                                              | statement                                                                                                                                                                                              | result                                                                                                                                                                                                                                                                         | verdict    |
|:-----|:--------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------|
| H1   | code check (holds by construction under assumption R)                                             | no wrong decision (byte check and slot model, Q 6 and 12, both loss models), no decoded value that differs from the plan, no decision-layer error, and no byte round-trip mismatch on any analysed day | byte wrong max 0.000; slot wrong max 0.000; value mismatches 0; decision-layer errors 0; round trip 0 mismatches in 40380 blocks (0 not buildable); byte days without a 3b block 0                                                                                             | pass       |
| H2   | test                                                                                              | byte level: 3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= 0.1 (Q 6 and 12, both loss models)                                                                          | +0.246 (+0.204 to +0.292) / +0.200 (+0.166 to +0.239) / +0.203 (+0.159 to +0.246) / +0.209 (+0.167 to +0.248)                                                                                                                                                                  | pass       |
| H3   | test                                                                                              | byte level: 3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= 0.1 (all four)                                                                                           | +0.317 (+0.251 to +0.397) / +0.287 (+0.230 to +0.356) / +0.226 (+0.165 to +0.294) / +0.246 (+0.188 to +0.309)                                                                                                                                                                  | pass       |
| H4   | test                                                                                              | byte level: cost of the post-hoc adopted design, 3b rule minus record only, whole record recovered, lower bound >= -0.15 (Q 6) and >= -0.1 (Q 12), both loss models                                    | -0.094 (-0.113 to -0.075) / -0.075 (-0.089 to -0.061) / -0.027 (-0.039 to -0.017) / -0.034 (-0.045 to -0.024)                                                                                                                                                                  | pass       |
| H6   | known limit (flags are exact at the configured thresholds by construction)                        | byte level: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus flagsrec) < 0.0 (Q 6, both loss models)                                             | -0.046 (-0.070 to -0.027) / -0.133 (-0.153 to -0.116)                                                                                                                                                                                                                          | pass       |
| H7   | analytic bound (cannot fail: the ceiling with a conditional share of 1 is below any useful limit) | expected false-certificate days per million days at bit-error rate 0.001 under random corruption                                                                                                       | heur Q6: 0.0031 (upper 0.0036; ceiling 0.042); heur Q12: 0.0010 (upper 0.0015; ceiling 0.084); rec Q6: 0.0023 (upper 0.0027; ceiling 0.042); rec Q12: 0.0007 (upper 0.0014; ceiling 0.084)                                                                                     | not a test |
| H8   | code check (the slot model of the record only is the frame's code)                                | record only: byte frame and slot model agree in whole-record recovery, |difference| <= 0.01 (Q 6 and 12, both loss models)                                                                             | Q6 gilbert_p0.3_b3: byte 0.767, slot 0.768, |diff| 0.001 (10095 days); Q6 iid_p0.3: byte 0.837, slot 0.837, |diff| 0.000 (10095 days); Q12 gilbert_p0.3_b3: byte 0.936, slot 0.937, |diff| 0.001 (10095 days); Q12 iid_p0.3: byte 0.961, slot 0.961, |diff| 0.000 (10095 days) | pass       |

## Descriptive results (no verdict)

Assumption R (reporting resolution inferred from the record): 26 of 31 analysed sites have an inferred resolution for at least one of DO, pH, temperature; per parameter: {'DO': 12, 'pH': 21, 'T': 18}.

Byte check (hypotheses), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.837 / 0.580 / 0.497 / 0.840
  heur      0.743 / 0.953 / 0.815 / 0.881
  flagsrec  0.837 / 0.999 / 0.568 / 0.999

Byte check (hypotheses), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.767 / 0.493 / 0.424 / 0.741
  heur      0.692 / 0.828 / 0.710 / 0.783
  flagsrec  0.767 / 0.961 / 0.510 / 0.962

Byte check (hypotheses), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.961 / 0.738 / 0.625 / 0.941
  heur      0.933 / 0.970 / 0.851 / 0.976
  flagsrec  0.961 / 1.000 / 0.648 / 1.000

Byte check (hypotheses), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.936 / 0.691 / 0.586 / 0.910
  heur      0.902 / 0.952 / 0.832 / 0.947
  flagsrec  0.936 / 0.996 / 0.623 / 0.997

Slot model (cross-check), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.837 / 0.581 / 0.498 / 0.840
  heur      0.696 / 0.954 / 0.792 / 0.867
  flags     0.837 / 0.999 / 0.274 / 0.999
  flagsrec  0.837 / 0.999 / 0.569 / 0.999

Slot model (cross-check), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.768 / 0.493 / 0.424 / 0.743
  heur      0.649 / 0.837 / 0.698 / 0.776
  flags     0.768 / 0.960 / 0.264 / 0.960
  flagsrec  0.768 / 0.960 / 0.509 / 0.962

Slot model (cross-check), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.961 / 0.737 / 0.625 / 0.942
  heur      0.891 / 0.970 / 0.823 / 0.966
  flags     0.961 / 1.000 / 0.275 / 1.000
  flagsrec  0.961 / 1.000 / 0.649 / 1.000

Slot model (cross-check), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.937 / 0.691 / 0.586 / 0.910
  heur      0.863 / 0.954 / 0.806 / 0.938
  flags     0.937 / 0.996 / 0.274 / 0.996
  flagsrec  0.937 / 0.996 / 0.622 / 0.997

Byte check, Q = 6: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.737 / heur 0.908 / flagsrec 0.786; 3b minus flagsrec +0.122 (+0.085 to +0.173); 3b minus record +0.171 (+0.113 to +0.259)
  iid_p0.3 do_cfg    rec 0.737 / heur 0.964 / flagsrec 0.999; 3b minus flagsrec -0.035 (-0.055 to -0.021); 3b minus record +0.227 (+0.152 to +0.328)
  iid_p0.3 ph_alt    rec 0.595 / heur 0.913 / flagsrec 0.696; 3b minus flagsrec +0.217 (+0.131 to +0.282); 3b minus record +0.318 (+0.182 to +0.453)
  iid_p0.3 ph_cfg    rec 0.537 / heur 0.929 / flagsrec 0.999; 3b minus flagsrec -0.070 (-0.139 to -0.011); 3b minus record +0.392 (+0.251 to +0.551)
  iid_p0.3 ec_alt    rec 0.245 / heur 0.604 / flagsrec 0.279; 3b minus flagsrec +0.325 (+0.264 to +0.393); 3b minus record +0.359 (+0.289 to +0.438)
  iid_p0.3 ec_cfg    rec 0.531 / heur 0.978 / flagsrec 0.999; 3b minus flagsrec -0.021 (-0.027 to -0.016); 3b minus record +0.447 (+0.352 to +0.548)
  iid_p0.3 win7_alt  rec 0.572 / heur 0.931 / flagsrec 0.670; 3b minus flagsrec +0.261 (+0.212 to +0.302); 3b minus record +0.360 (+0.293 to +0.414)
  iid_p0.3 win7_cfg  rec 0.595 / heur 0.952 / flagsrec 0.999; 3b minus flagsrec -0.047 (-0.059 to -0.034); 3b minus record +0.357 (+0.287 to +0.416)
  gilbert_p0.3_b3 do_alt    rec 0.680 / heur 0.849 / flagsrec 0.742; 3b minus flagsrec +0.107 (+0.074 to +0.153); 3b minus record +0.168 (+0.117 to +0.246)
  gilbert_p0.3_b3 do_cfg    rec 0.682 / heur 0.895 / flagsrec 0.961; 3b minus flagsrec -0.065 (-0.083 to -0.053); 3b minus record +0.213 (+0.146 to +0.304)
  gilbert_p0.3_b3 ph_alt    rec 0.547 / heur 0.837 / flagsrec 0.652; 3b minus flagsrec +0.185 (+0.116 to +0.242); 3b minus record +0.290 (+0.169 to +0.409)
  gilbert_p0.3_b3 ph_cfg    rec 0.497 / heur 0.850 / flagsrec 0.961; 3b minus flagsrec -0.111 (-0.174 to -0.058); 3b minus record +0.353 (+0.224 to +0.494)
  gilbert_p0.3_b3 ec_alt    rec 0.223 / heur 0.552 / flagsrec 0.265; 3b minus flagsrec +0.287 (+0.232 to +0.349); 3b minus record +0.329 (+0.266 to +0.400)
  gilbert_p0.3_b3 ec_cfg    rec 0.483 / heur 0.895 / flagsrec 0.961; 3b minus flagsrec -0.066 (-0.071 to -0.061); 3b minus record +0.413 (+0.334 to +0.501)
  gilbert_p0.3_b3 win7_alt  rec 0.339 / heur 0.637 / flagsrec 0.489; 3b minus flagsrec +0.148 (+0.115 to +0.182); 3b minus record +0.298 (+0.263 to +0.330)
  gilbert_p0.3_b3 win7_cfg  rec 0.351 / heur 0.653 / flagsrec 0.961; 3b minus flagsrec -0.308 (-0.339 to -0.275); 3b minus record +0.303 (+0.269 to +0.334)

Byte check, Q = 12: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.845 / heur 0.945 / flagsrec 0.858; 3b minus flagsrec +0.087 (+0.064 to +0.122); 3b minus record +0.100 (+0.070 to +0.149)
  iid_p0.3 do_cfg    rec 0.856 / heur 0.970 / flagsrec 1.000; 3b minus flagsrec -0.030 (-0.050 to -0.014); 3b minus record +0.115 (+0.064 to +0.189)
  iid_p0.3 ph_alt    rec 0.701 / heur 0.953 / flagsrec 0.747; 3b minus flagsrec +0.206 (+0.135 to +0.259); 3b minus record +0.252 (+0.145 to +0.353)
  iid_p0.3 ph_cfg    rec 0.651 / heur 0.939 / flagsrec 1.000; 3b minus flagsrec -0.061 (-0.134 to -0.002); 3b minus record +0.288 (+0.143 to +0.414)
  iid_p0.3 ec_alt    rec 0.304 / heur 0.623 / flagsrec 0.313; 3b minus flagsrec +0.310 (+0.247 to +0.383); 3b minus record +0.320 (+0.250 to +0.401)
  iid_p0.3 ec_cfg    rec 0.645 / heur 0.989 / flagsrec 1.000; 3b minus flagsrec -0.011 (-0.017 to -0.006); 3b minus record +0.344 (+0.268 to +0.444)
  iid_p0.3 win7_alt  rec 0.884 / heur 0.991 / flagsrec 0.899; 3b minus flagsrec +0.091 (+0.063 to +0.125); 3b minus record +0.106 (+0.073 to +0.148)
  iid_p0.3 win7_cfg  rec 0.910 / heur 0.995 / flagsrec 1.000; 3b minus flagsrec -0.005 (-0.009 to -0.001); 3b minus record +0.086 (+0.059 to +0.122)
  gilbert_p0.3_b3 do_alt    rec 0.813 / heur 0.933 / flagsrec 0.839; 3b minus flagsrec +0.094 (+0.072 to +0.130); 3b minus record +0.120 (+0.089 to +0.169)
  gilbert_p0.3_b3 do_cfg    rec 0.822 / heur 0.961 / flagsrec 0.996; 3b minus flagsrec -0.035 (-0.054 to -0.020); 3b minus record +0.140 (+0.087 to +0.215)
  gilbert_p0.3_b3 ph_alt    rec 0.681 / heur 0.938 / flagsrec 0.734; 3b minus flagsrec +0.203 (+0.132 to +0.256); 3b minus record +0.257 (+0.150 to +0.356)
  gilbert_p0.3_b3 ph_cfg    rec 0.632 / heur 0.929 / flagsrec 0.996; 3b minus flagsrec -0.067 (-0.139 to -0.008); 3b minus record +0.297 (+0.160 to +0.418)
  gilbert_p0.3_b3 ec_alt    rec 0.288 / heur 0.615 / flagsrec 0.305; 3b minus flagsrec +0.310 (+0.248 to +0.379); 3b minus record +0.327 (+0.258 to +0.407)
  gilbert_p0.3_b3 ec_cfg    rec 0.617 / heur 0.978 / flagsrec 0.997; 3b minus flagsrec -0.019 (-0.025 to -0.013); 3b minus record +0.361 (+0.292 to +0.454)
  gilbert_p0.3_b3 win7_alt  rec 0.762 / heur 0.940 / flagsrec 0.811; 3b minus flagsrec +0.129 (+0.100 to +0.163); 3b minus record +0.177 (+0.142 to +0.221)
  gilbert_p0.3_b3 win7_cfg  rec 0.784 / heur 0.948 / flagsrec 0.997; 3b minus flagsrec -0.049 (-0.059 to -0.039); 3b minus record +0.164 (+0.133 to +0.200)

Whole-record recovery, byte frame against slot model (the slot model gives the layered group whole slots, so it is pessimistic for the 3b rule):
  Q= 6 gilbert_p0.3_b3  flagsrec  byte 0.767, slot 0.768, difference -0.001 (10095 days)
  Q= 6 gilbert_p0.3_b3  heur      byte 0.692, slot 0.649, difference +0.042 (10095 days)
  Q= 6 gilbert_p0.3_b3  rec       byte 0.767, slot 0.768, difference -0.001 (10095 days)
  Q= 6 iid_p0.3         flagsrec  byte 0.837, slot 0.837, difference +0.000 (10095 days)
  Q= 6 iid_p0.3         heur      byte 0.743, slot 0.696, difference +0.048 (10095 days)
  Q= 6 iid_p0.3         rec       byte 0.837, slot 0.837, difference +0.000 (10095 days)
  Q=12 gilbert_p0.3_b3  flagsrec  byte 0.936, slot 0.937, difference -0.001 (10095 days)
  Q=12 gilbert_p0.3_b3  heur      byte 0.902, slot 0.863, difference +0.039 (10095 days)
  Q=12 gilbert_p0.3_b3  rec       byte 0.936, slot 0.937, difference -0.001 (10095 days)
  Q=12 iid_p0.3         flagsrec  byte 0.961, slot 0.961, difference -0.000 (10095 days)
  Q=12 iid_p0.3         heur      byte 0.933, slot 0.891, difference +0.042 (10095 days)
  Q=12 iid_p0.3         rec       byte 0.961, slot 0.961, difference -0.000 (10095 days)

Integrity, given one CRC-valid forgery (header or body): classes of day (share of draws / false-certificate share in class); rejected share; day with a wrong decision (point, site-clustered 95% interval); decision-layer errors
  heur  Q= 6: N<K 0.15/0.1592; N=K 0.15/0.2159; N>K 0.59/0.0000; uncoded 0.10/0.1644; rejected 0.800; wrong decision 0.0220 (0.0191 to 0.0248); errors 0
  heur  Q=12: N<K 0.03/0.1304; N=K 0.02/0.1961; N>K 0.92/0.0000; uncoded 0.04/0.1161; rejected 0.908; wrong decision 0.0024 (0.0014 to 0.0035); errors 0
  rec   Q= 6: N<K 0.10/0.1483; N=K 0.14/0.2140; N>K 0.70/0.0000; uncoded 0.06/0.1643; rejected 0.799; wrong decision 0.0199 (0.0168 to 0.0230); errors 0
  rec   Q=12: N<K 0.02/0.1503; N=K 0.01/0.1661; N>K 0.95/0.0000; uncoded 0.02/0.1447; rejected 0.904; wrong decision 0.0026 (0.0011 to 0.0049); errors 0
