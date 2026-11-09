# Step 4 results (revision 2): baselines against the witness designs, development data only

Date: 2026-11-07. Status of every number below: numerical (trace-driven simulation on USGS 2023 development data, 38 sites with four-parameter days, 10,342 days). Access: repository (`results/dev/proto_b/*.csv`, 156 files, produced by `src/p3/proto_base.py`; table by `src/p3/proto_base_eval.py`, printout `results/proto_b_eval.txt`). Not peer review; the criteria were written before the run (docs/REVISION2_PLAN.md, "Step 4").
Commands (from Paper3/): `python -I src/p3/proto_base.py data/clean/usgs dev 1` (resumable, one worker; it stopped twice on this 3.7 GB machine and was resumed), `python -I src/p3/proto_base_eval.py dev 6 12`.

## Designs and scenarios

- Same Q messages of five value slots and identical loss draws for all designs. Record only; the generalised 3b rule and the exact allocation (lambda 1) from Step 3c; tightened tolerance (x 0.5 and x 0.25, no witnesses); send-on-delta with hold reconstruction (each unit once, and in the record-first code); decision flags (the answers to the four configured queries in every message).
- Thresholds: configured (DO 5; pH 6.5 and 9.0; 7DADM 20; conductance 10%) and two alternative sets that the encoder does not know (alt1: 4.5; 6.3 and 9.2; 21; 20%; alt2: 5.5; 6.7 and 8.8; 19; 5%). The flags design decides an alternative only by monotone implication from its configured answer.
- Hard cases are defined per scenario (near the scenario's threshold or in its event state); "hard, alternative" pools both alternative sets.
- Modelling choices that favour the flags design: 8 flag bits per message are modelled as 4.75 record values per message; in frame v2 the record capacity is the integer 4 (src/p3/capacity.py). A flags decision is correct by construction when a message arrives, so its zero wrong decisions say nothing about soundness.

## Pre-registered criteria and outcome (Q = 6, both loss models)

1. Zero wrong decisions: met in every design, condition, Q (maximum 0.000). For the flags design this is trivially true (see above).
2. The 3b rule and exact lambda 1 are not dominated by send-on-delta or tightened tolerance on (record recovered, hard-case decisions at configured thresholds): met. None of the four baselines dominates either design under either loss model.
3. On the alternative thresholds, ours exceeds the decision flags in pooled hard-case decisions by at least 0.10: met. Independent loss: 3b rule +0.566, exact +0.510; bursts: +0.483 and +0.423.
4. If the flags dominate on the configured thresholds, say so: they do. Independent loss: flags exceed the 3b rule by 0.032 in hard-case decisions and by 0.064 in record recovery (exact: 0.051 and 0.051); bursts: 0.108 and 0.052 (exact: 0.137 and 0.055). The expectation written before the run (flags match or beat every witness design on the configured thresholds at lower record cost) was correct.

## Further findings

- Send-on-delta needs 1.79 times as many values as the piecewise-linear record (mean 18.8 against 10.5 per day; medians 15 and 9). Coded, it recovers the record 0.653 of the time at Q = 6 (independent loss) against 0.905, and decides 0.424 of hard cases against 0.677 for the record alone. Sent once it is worse (0.295 and 0.315).
- Tightening the tolerance does not buy decisions at this quota: x 0.5 needs 1.79 times as many values (mean 18.8), recovers the record 0.675 of the time and decides 0.530 of hard cases (below the record alone, 0.677); x 0.25 needs 4.7 times as many values and collapses (0.147 and 0.198).
- At Q = 12 the picture is the same with higher levels: flags 0.988 record and 1.000 hard-case decisions; 3b rule 0.964 and 0.982; send-on-delta coded 0.927 and 0.628; tolerance x 0.5 0.922 and 0.819.
- On alternative thresholds the witness designs are well below their configured-threshold level (3b rule 0.783 against 0.968 at Q = 6, independent loss), because the allocation protects the days that are hard at the configured thresholds, not at the alternatives.

## Reading

- For thresholds that are known when the node is configured, decision flags are the better design: cheaper, higher decision rate, higher record recovery. The paper cannot claim that witnesses are the best way to decide fixed thresholds.
- What the witnesses add is generality: decisions for thresholds nobody configured (+0.42 to +0.57 hard-case decisions over flags), and numerical extremum values (daily minimum, maximum, rate bound) that a flag cannot give. Whether that is worth its bytes depends on whether thresholds change; this is a claim about use, not a measured benefit in a field setting.
- Not yet tested (post-hoc, to be labelled exploratory if run): a hybrid of flags for the configured thresholds with witnesses hosted in spare slots.
- Limits: development data only; the alternative threshold sets were chosen by the analyst; send-on-delta and tightened tolerance were not given witnesses (as pre-registered); modelling favours the flags design as stated above.

## Raw evaluation output

## Q = 6: 38 sites; wrong decisions max 0.000
values per day: V_pla 10.5, V_sod 18.8, V_t50 18.8, V_t25 49.3

### iid_p0.3
| design               | record recovered       | hard, configured       | hard, alternative thresholds   | all, configured        |
|:---------------------|:-----------------------|:-----------------------|:-------------------------------|:-----------------------|
| record only          | 0.905 (0.871 to 0.934) | 0.677 (0.634 to 0.725) | 0.573 (0.526 to 0.616)         | 0.898 (0.875 to 0.920) |
| 3b rule generalised  | 0.825 (0.771 to 0.869) | 0.968 (0.960 to 0.976) | 0.783 (0.734 to 0.826)         | 0.923 (0.904 to 0.941) |
| exact, lambda 1      | 0.838 (0.784 to 0.889) | 0.949 (0.938 to 0.960) | 0.727 (0.677 to 0.772)         | 0.975 (0.970 to 0.980) |
| tolerance x 0.5      | 0.675 (0.602 to 0.746) | 0.530 (0.470 to 0.598) | 0.563 (0.507 to 0.625)         | 0.738 (0.686 to 0.789) |
| tolerance x 0.25     | 0.147 (0.095 to 0.201) | 0.198 (0.154 to 0.245) | 0.215 (0.173 to 0.265)         | 0.301 (0.250 to 0.350) |
| send-on-delta, once  | 0.295 (0.258 to 0.331) | 0.315 (0.276 to 0.349) | 0.317 (0.277 to 0.350)         | 0.463 (0.436 to 0.488) |
| send-on-delta, coded | 0.653 (0.577 to 0.723) | 0.424 (0.378 to 0.473) | 0.427 (0.373 to 0.477)         | 0.693 (0.637 to 0.743) |
| decision flags       | 0.889 (0.855 to 0.919) | 0.999 (0.999 to 1.000) | 0.217 (0.182 to 0.258)         | 0.999 (0.999 to 0.999) |

Criteria at Q = 6, iid_p0.3:
  (2) sod_once dominates heur: False
  (2) sod_mds dominates heur: False
  (2) tight50 dominates heur: False
  (2) tight25 dominates heur: False
  (3) heur minus flags on alternative thresholds: +0.566 (needs at least +0.100: True)
  (4) flags minus heur on configured thresholds: +0.032; record +0.064
  (2) sod_once dominates ex1: False
  (2) sod_mds dominates ex1: False
  (2) tight50 dominates ex1: False
  (2) tight25 dominates ex1: False
  (3) ex1 minus flags on alternative thresholds: +0.510 (needs at least +0.100: True)
  (4) flags minus ex1 on configured thresholds: +0.051; record +0.051

### gilbert_p0.3_b3
| design               | record recovered       | hard, configured       | hard, alternative thresholds   | all, configured        |
|:---------------------|:-----------------------|:-----------------------|:-------------------------------|:-----------------------|
| record only          | 0.835 (0.807 to 0.860) | 0.572 (0.539 to 0.614) | 0.490 (0.445 to 0.530)         | 0.803 (0.780 to 0.827) |
| 3b rule generalised  | 0.767 (0.722 to 0.809) | 0.853 (0.841 to 0.863) | 0.691 (0.646 to 0.729)         | 0.830 (0.813 to 0.848) |
| exact, lambda 1      | 0.765 (0.717 to 0.811) | 0.824 (0.805 to 0.839) | 0.632 (0.583 to 0.674)         | 0.879 (0.868 to 0.889) |
| tolerance x 0.5      | 0.639 (0.572 to 0.695) | 0.464 (0.415 to 0.520) | 0.499 (0.456 to 0.554)         | 0.670 (0.632 to 0.708) |
| tolerance x 0.25     | 0.164 (0.114 to 0.216) | 0.163 (0.125 to 0.204) | 0.189 (0.145 to 0.237)         | 0.303 (0.257 to 0.349) |
| send-on-delta, once  | 0.425 (0.382 to 0.462) | 0.300 (0.264 to 0.337) | 0.310 (0.267 to 0.348)         | 0.480 (0.450 to 0.504) |
| send-on-delta, coded | 0.625 (0.563 to 0.679) | 0.361 (0.318 to 0.402) | 0.372 (0.319 to 0.417)         | 0.630 (0.578 to 0.671) |
| decision flags       | 0.819 (0.791 to 0.845) | 0.961 (0.959 to 0.962) | 0.209 (0.166 to 0.246)         | 0.961 (0.960 to 0.961) |

Criteria at Q = 6, gilbert_p0.3_b3:
  (2) sod_once dominates heur: False
  (2) sod_mds dominates heur: False
  (2) tight50 dominates heur: False
  (2) tight25 dominates heur: False
  (3) heur minus flags on alternative thresholds: +0.483 (needs at least +0.100: True)
  (4) flags minus heur on configured thresholds: +0.108; record +0.052
  (2) sod_once dominates ex1: False
  (2) sod_mds dominates ex1: False
  (2) tight50 dominates ex1: False
  (2) tight25 dominates ex1: False
  (3) ex1 minus flags on alternative thresholds: +0.423 (needs at least +0.100: True)
  (4) flags minus ex1 on configured thresholds: +0.137; record +0.055

## Q = 12: 38 sites; wrong decisions max 0.000
values per day: V_pla 10.5, V_sod 18.8, V_t50 18.8, V_t25 49.3

### iid_p0.3
| design               | record recovered       | hard, configured       | hard, alternative thresholds   | all, configured        |
|:---------------------|:-----------------------|:-----------------------|:-------------------------------|:-----------------------|
| record only          | 0.991 (0.984 to 0.996) | 0.790 (0.746 to 0.831) | 0.664 (0.614 to 0.706)         | 0.968 (0.955 to 0.978) |
| 3b rule generalised  | 0.964 (0.945 to 0.981) | 0.982 (0.975 to 0.989) | 0.813 (0.763 to 0.855)         | 0.989 (0.984 to 0.993) |
| exact, lambda 1      | 0.976 (0.963 to 0.989) | 0.980 (0.972 to 0.987) | 0.720 (0.671 to 0.769)         | 0.997 (0.995 to 0.998) |
| tolerance x 0.5      | 0.922 (0.888 to 0.950) | 0.819 (0.778 to 0.864) | 0.792 (0.753 to 0.832)         | 0.937 (0.914 to 0.959) |
| tolerance x 0.25     | 0.518 (0.426 to 0.613) | 0.483 (0.392 to 0.579) | 0.520 (0.447 to 0.596)         | 0.620 (0.545 to 0.694) |
| send-on-delta, once  | 0.303 (0.268 to 0.336) | 0.383 (0.336 to 0.436) | 0.375 (0.334 to 0.412)         | 0.504 (0.487 to 0.521) |
| send-on-delta, coded | 0.927 (0.885 to 0.958) | 0.628 (0.572 to 0.689) | 0.611 (0.559 to 0.658)         | 0.891 (0.865 to 0.916) |
| decision flags       | 0.988 (0.981 to 0.994) | 1.000 (1.000 to 1.000) | 0.217 (0.175 to 0.261)         | 1.000 (1.000 to 1.000) |

### gilbert_p0.3_b3
| design               | record recovered       | hard, configured       | hard, alternative thresholds   | all, configured        |
|:---------------------|:-----------------------|:-----------------------|:-------------------------------|:-----------------------|
| record only          | 0.971 (0.963 to 0.978) | 0.749 (0.710 to 0.793) | 0.630 (0.584 to 0.674)         | 0.943 (0.929 to 0.956) |
| 3b rule generalised  | 0.940 (0.920 to 0.959) | 0.966 (0.959 to 0.973) | 0.797 (0.748 to 0.837)         | 0.966 (0.960 to 0.972) |
| exact, lambda 1      | 0.956 (0.941 to 0.970) | 0.947 (0.939 to 0.955) | 0.696 (0.648 to 0.741)         | 0.976 (0.972 to 0.980) |
| tolerance x 0.5      | 0.889 (0.858 to 0.919) | 0.755 (0.719 to 0.799) | 0.737 (0.701 to 0.778)         | 0.893 (0.869 to 0.916) |
| tolerance x 0.25     | 0.503 (0.415 to 0.584) | 0.444 (0.371 to 0.520) | 0.486 (0.420 to 0.555)         | 0.600 (0.536 to 0.655) |
| send-on-delta, once  | 0.459 (0.429 to 0.484) | 0.371 (0.325 to 0.416) | 0.371 (0.330 to 0.406)         | 0.530 (0.515 to 0.543) |
| send-on-delta, coded | 0.892 (0.854 to 0.921) | 0.570 (0.519 to 0.620) | 0.561 (0.507 to 0.608)         | 0.846 (0.818 to 0.872) |
| decision flags       | 0.967 (0.958 to 0.976) | 0.997 (0.996 to 0.997) | 0.217 (0.177 to 0.257)         | 0.997 (0.996 to 0.997) |
