# Verdicts of the version 3 confirmation (REHEARSAL on development data, not confirmatory)

| id   | type                                                                                              | statement                                                                                                                                                                                              | result                                                                                                                                                                                                                                                                         | verdict    |
|:-----|:--------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------|
| H1   | code check (holds by construction under assumption R)                                             | no wrong decision (byte check and slot model, Q 6 and 12, both loss models), no decoded value that differs from the plan, no decision-layer error, and no byte round-trip mismatch on any analysed day | byte wrong max 0.000; slot wrong max 0.000; value mismatches 0; decision-layer errors 0; round trip 0 mismatches in 40468 blocks (0 not buildable); byte days without a 3b block 0                                                                                             | pass       |
| H2   | test                                                                                              | byte level: 3b rule minus flagsrec, hard cases at unanticipated thresholds, lower bound >= 0.1 (Q 6 and 12, both loss models)                                                                          | +0.223 (+0.196 to +0.249) / +0.185 (+0.161 to +0.205) / +0.179 (+0.156 to +0.201) / +0.188 (+0.164 to +0.210)                                                                                                                                                                  | pass       |
| H3   | test                                                                                              | byte level: 3b rule minus record only, hard cases at unanticipated thresholds, lower bound >= 0.1 (all four)                                                                                           | +0.272 (+0.234 to +0.307) / +0.249 (+0.218 to +0.277) / +0.188 (+0.163 to +0.211) / +0.208 (+0.183 to +0.233)                                                                                                                                                                  | pass       |
| H4   | test                                                                                              | byte level: cost of the post-hoc adopted design, 3b rule minus record only, whole record recovered, lower bound >= -0.15 (Q 6) and >= -0.1 (Q 12), both loss models                                    | -0.088 (-0.113 to -0.066) / -0.071 (-0.089 to -0.055) / -0.027 (-0.039 to -0.015) / -0.032 (-0.043 to -0.022)                                                                                                                                                                  | pass       |
| H6   | known limit (flags are exact at the configured thresholds by construction)                        | byte level: flagsrec exceeds the 3b rule on hard cases at the configured thresholds, upper bound of (3b rule minus flagsrec) < 0.0 (Q 6, both loss models)                                             | -0.036 (-0.045 to -0.027) / -0.121 (-0.133 to -0.111)                                                                                                                                                                                                                          | pass       |
| H7   | analytic bound (cannot fail: the ceiling with a conditional share of 1 is below any useful limit) | expected false-certificate days per million days at bit-error rate 0.001 under random corruption                                                                                                       | heur Q6: 0.0031 (upper 0.0036; ceiling 0.042); heur Q12: 0.0008 (upper 0.0012; ceiling 0.084); rec Q6: 0.0021 (upper 0.0026; ceiling 0.042); rec Q12: 0.0004 (upper 0.0006; ceiling 0.084)                                                                                     | not a test |
| H8   | code check (the slot model of the record only is the frame's code)                                | record only: byte frame and slot model agree in whole-record recovery, |difference| <= 0.01 (Q 6 and 12, both loss models)                                                                             | Q6 gilbert_p0.3_b3: byte 0.780, slot 0.780, |diff| 0.000 (10117 days); Q6 iid_p0.3: byte 0.844, slot 0.844, |diff| 0.000 (10117 days); Q12 gilbert_p0.3_b3: byte 0.954, slot 0.954, |diff| 0.000 (10117 days); Q12 iid_p0.3: byte 0.980, slot 0.980, |diff| 0.000 (10117 days) | pass       |

## Descriptive results (no verdict)

Assumption R (reporting resolution inferred from the record): 30 of 35 analysed sites have an inferred resolution for at least one of DO, pH, temperature; per parameter: {'DO': 21, 'pH': 21, 'T': 22}.

Byte check (hypotheses), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.844 / 0.616 / 0.524 / 0.849
  heur      0.757 / 0.963 / 0.796 / 0.875
  flagsrec  0.844 / 0.999 / 0.573 / 0.999

Byte check (hypotheses), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.780 / 0.522 / 0.449 / 0.758
  heur      0.708 / 0.840 / 0.698 / 0.787
  flagsrec  0.780 / 0.961 / 0.513 / 0.963

Byte check (hypotheses), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.980 / 0.777 / 0.653 / 0.962
  heur      0.953 / 0.981 / 0.841 / 0.982
  flagsrec  0.980 / 1.000 / 0.662 / 1.000

Byte check (hypotheses), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.954 / 0.726 / 0.613 / 0.928
  heur      0.922 / 0.964 / 0.821 / 0.952
  flagsrec  0.954 / 0.997 / 0.634 / 0.997

Slot model (cross-check), Q = 6, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.844 / 0.615 / 0.525 / 0.850
  heur      0.718 / 0.964 / 0.762 / 0.864
  flags     0.844 / 0.999 / 0.217 / 0.999
  flagsrec  0.844 / 0.999 / 0.574 / 0.999

Slot model (cross-check), Q = 6, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.780 / 0.523 / 0.449 / 0.759
  heur      0.673 / 0.847 / 0.671 / 0.778
  flags     0.780 / 0.961 / 0.209 / 0.961
  flagsrec  0.780 / 0.961 / 0.513 / 0.963

Slot model (cross-check), Q = 12, iid_p0.3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.980 / 0.777 / 0.653 / 0.962
  heur      0.919 / 0.981 / 0.806 / 0.972
  flags     0.980 / 1.000 / 0.217 / 1.000
  flagsrec  0.980 / 1.000 / 0.662 / 1.000

Slot model (cross-check), Q = 12, gilbert_p0.3_b3: pooled level (record recovered / hard configured / hard unanticipated / all configured)
  rec       0.954 / 0.725 / 0.612 / 0.928
  heur      0.890 / 0.965 / 0.788 / 0.944
  flags     0.954 / 0.997 / 0.216 / 0.996
  flagsrec  0.954 / 0.997 / 0.633 / 0.997

Byte check, Q = 6: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.725 / heur 0.917 / flagsrec 0.766; 3b minus flagsrec +0.151 (+0.128 to +0.177); 3b minus record +0.192 (+0.162 to +0.218)
  iid_p0.3 do_cfg    rec 0.704 / heur 0.947 / flagsrec 0.999; 3b minus flagsrec -0.052 (-0.085 to -0.018); 3b minus record +0.243 (+0.197 to +0.306)
  iid_p0.3 ph_alt    rec 0.683 / heur 0.866 / flagsrec 0.734; 3b minus flagsrec +0.131 (+0.081 to +0.175); 3b minus record +0.183 (+0.106 to +0.255)
  iid_p0.3 ph_cfg    rec 0.628 / heur 0.956 / flagsrec 0.999; 3b minus flagsrec -0.043 (-0.068 to -0.020); 3b minus record +0.328 (+0.235 to +0.406)
  iid_p0.3 ec_alt    rec 0.284 / heur 0.641 / flagsrec 0.319; 3b minus flagsrec +0.323 (+0.278 to +0.366); 3b minus record +0.358 (+0.309 to +0.403)
  iid_p0.3 ec_cfg    rec 0.566 / heur 0.981 / flagsrec 0.999; 3b minus flagsrec -0.018 (-0.022 to -0.013); 3b minus record +0.415 (+0.318 to +0.487)
  iid_p0.3 win7_alt  rec 0.624 / heur 0.933 / flagsrec 0.706; 3b minus flagsrec +0.227 (+0.177 to +0.278); 3b minus record +0.309 (+0.243 to +0.374)
  iid_p0.3 win7_cfg  rec 0.635 / heur 0.947 / flagsrec 0.999; 3b minus flagsrec -0.052 (-0.073 to -0.035); 3b minus record +0.313 (+0.243 to +0.381)
  gilbert_p0.3_b3 do_alt    rec 0.672 / heur 0.852 / flagsrec 0.726; 3b minus flagsrec +0.126 (+0.100 to +0.154); 3b minus record +0.181 (+0.152 to +0.204)
  gilbert_p0.3_b3 do_cfg    rec 0.652 / heur 0.878 / flagsrec 0.959; 3b minus flagsrec -0.081 (-0.109 to -0.049); 3b minus record +0.226 (+0.185 to +0.280)
  gilbert_p0.3_b3 ph_alt    rec 0.631 / heur 0.801 / flagsrec 0.687; 3b minus flagsrec +0.113 (+0.071 to +0.151); 3b minus record +0.170 (+0.099 to +0.237)
  gilbert_p0.3_b3 ph_cfg    rec 0.579 / heur 0.878 / flagsrec 0.963; 3b minus flagsrec -0.085 (-0.108 to -0.063); 3b minus record +0.299 (+0.215 to +0.368)
  gilbert_p0.3_b3 ec_alt    rec 0.262 / heur 0.587 / flagsrec 0.303; 3b minus flagsrec +0.284 (+0.242 to +0.324); 3b minus record +0.325 (+0.283 to +0.364)
  gilbert_p0.3_b3 ec_cfg    rec 0.520 / heur 0.898 / flagsrec 0.962; 3b minus flagsrec -0.064 (-0.068 to -0.058); 3b minus record +0.378 (+0.294 to +0.441)
  gilbert_p0.3_b3 win7_alt  rec 0.363 / heur 0.642 / flagsrec 0.504; 3b minus flagsrec +0.138 (+0.099 to +0.184); 3b minus record +0.278 (+0.237 to +0.322)
  gilbert_p0.3_b3 win7_cfg  rec 0.366 / heur 0.656 / flagsrec 0.960; 3b minus flagsrec -0.304 (-0.334 to -0.279); 3b minus record +0.289 (+0.244 to +0.335)

Byte check, Q = 12: hard cases per kind (pooled level; contrasts with site-clustered 95% intervals)
  iid_p0.3 do_alt    rec 0.849 / heur 0.961 / flagsrec 0.856; 3b minus flagsrec +0.105 (+0.078 to +0.139); 3b minus record +0.112 (+0.087 to +0.144)
  iid_p0.3 do_cfg    rec 0.822 / heur 0.953 / flagsrec 1.000; 3b minus flagsrec -0.047 (-0.078 to -0.012); 3b minus record +0.132 (+0.102 to +0.163)
  iid_p0.3 ph_alt    rec 0.804 / heur 0.940 / flagsrec 0.813; 3b minus flagsrec +0.126 (+0.092 to +0.157); 3b minus record +0.136 (+0.098 to +0.171)
  iid_p0.3 ph_cfg    rec 0.789 / heur 0.966 / flagsrec 1.000; 3b minus flagsrec -0.034 (-0.059 to -0.009); 3b minus record +0.177 (+0.126 to +0.208)
  iid_p0.3 ec_alt    rec 0.355 / heur 0.654 / flagsrec 0.360; 3b minus flagsrec +0.294 (+0.244 to +0.348); 3b minus record +0.299 (+0.249 to +0.354)
  iid_p0.3 ec_cfg    rec 0.682 / heur 0.992 / flagsrec 1.000; 3b minus flagsrec -0.008 (-0.012 to -0.004); 3b minus record +0.310 (+0.213 to +0.405)
  iid_p0.3 win7_alt  rec 0.911 / heur 0.994 / flagsrec 0.927; 3b minus flagsrec +0.067 (+0.043 to +0.096); 3b minus record +0.084 (+0.050 to +0.124)
  iid_p0.3 win7_cfg  rec 0.913 / heur 0.998 / flagsrec 1.000; 3b minus flagsrec -0.002 (-0.004 to -0.000); 3b minus record +0.085 (+0.055 to +0.123)
  gilbert_p0.3_b3 do_alt    rec 0.818 / heur 0.948 / flagsrec 0.838; 3b minus flagsrec +0.111 (+0.085 to +0.143); 3b minus record +0.131 (+0.108 to +0.157)
  gilbert_p0.3_b3 do_cfg    rec 0.790 / heur 0.946 / flagsrec 0.997; 3b minus flagsrec -0.051 (-0.082 to -0.017); 3b minus record +0.155 (+0.131 to +0.182)
  gilbert_p0.3_b3 ph_alt    rec 0.779 / heur 0.919 / flagsrec 0.795; 3b minus flagsrec +0.124 (+0.090 to +0.156); 3b minus record +0.140 (+0.099 to +0.178)
  gilbert_p0.3_b3 ph_cfg    rec 0.761 / heur 0.956 / flagsrec 0.997; 3b minus flagsrec -0.041 (-0.065 to -0.017); 3b minus record +0.195 (+0.144 to +0.226)
  gilbert_p0.3_b3 ec_alt    rec 0.338 / heur 0.646 / flagsrec 0.351; 3b minus flagsrec +0.295 (+0.248 to +0.347); 3b minus record +0.308 (+0.262 to +0.360)
  gilbert_p0.3_b3 ec_cfg    rec 0.653 / heur 0.981 / flagsrec 0.997; 3b minus flagsrec -0.015 (-0.019 to -0.011); 3b minus record +0.328 (+0.235 to +0.416)
  gilbert_p0.3_b3 win7_alt  rec 0.778 / heur 0.944 / flagsrec 0.827; 3b minus flagsrec +0.117 (+0.087 to +0.149); 3b minus record +0.166 (+0.124 to +0.216)
  gilbert_p0.3_b3 win7_cfg  rec 0.781 / heur 0.953 / flagsrec 0.996; 3b minus flagsrec -0.043 (-0.052 to -0.035); 3b minus record +0.173 (+0.130 to +0.221)

Whole-record recovery, byte frame against slot model (the slot model gives the layered group whole slots, so it is pessimistic for the 3b rule):
  Q= 6 gilbert_p0.3_b3  flagsrec  byte 0.780, slot 0.780, difference -0.000 (10117 days)
  Q= 6 gilbert_p0.3_b3  heur      byte 0.708, slot 0.673, difference +0.036 (10117 days)
  Q= 6 gilbert_p0.3_b3  rec       byte 0.780, slot 0.780, difference -0.000 (10117 days)
  Q= 6 iid_p0.3         flagsrec  byte 0.844, slot 0.844, difference -0.000 (10117 days)
  Q= 6 iid_p0.3         heur      byte 0.757, slot 0.718, difference +0.039 (10117 days)
  Q= 6 iid_p0.3         rec       byte 0.844, slot 0.844, difference -0.000 (10117 days)
  Q=12 gilbert_p0.3_b3  flagsrec  byte 0.954, slot 0.954, difference -0.000 (10117 days)
  Q=12 gilbert_p0.3_b3  heur      byte 0.922, slot 0.890, difference +0.033 (10117 days)
  Q=12 gilbert_p0.3_b3  rec       byte 0.954, slot 0.954, difference -0.000 (10117 days)
  Q=12 iid_p0.3         flagsrec  byte 0.980, slot 0.980, difference +0.000 (10117 days)
  Q=12 iid_p0.3         heur      byte 0.953, slot 0.919, difference +0.034 (10117 days)
  Q=12 iid_p0.3         rec       byte 0.980, slot 0.980, difference +0.000 (10117 days)

Integrity, given one CRC-valid forgery (header or body): classes of day (share of draws / false-certificate share in class); rejected share; day with a wrong decision (point, site-clustered 95% interval); decision-layer errors
  heur  Q= 6: N<K 0.15/0.1640; N=K 0.14/0.2249; N>K 0.61/0.0000; uncoded 0.10/0.1654; rejected 0.806; wrong decision 0.0237 (0.0201 to 0.0275); errors 0
  heur  Q=12: N<K 0.03/0.1073; N=K 0.02/0.2024; N>K 0.93/0.0000; uncoded 0.01/0.1224; rejected 0.909; wrong decision 0.0022 (0.0014 to 0.0030); errors 0
  rec   Q= 6: N<K 0.11/0.1445; N=K 0.14/0.2034; N>K 0.71/0.0000; uncoded 0.05/0.1494; rejected 0.809; wrong decision 0.0183 (0.0140 to 0.0229); errors 0
  rec   Q=12: N<K 0.02/0.1121; N=K 0.01/0.1900; N>K 0.97/0.0000; uncoded 0.00/0.1333; rejected 0.916; wrong decision 0.0020 (0.0011 to 0.0031); errors 0
