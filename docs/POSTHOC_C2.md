# Post-confirmation change after the C2 failure (exploratory)

Status: exploratory. The change was made after the second confirmation (`docs/CONFIRM2_RESULTS.md`) and does not
alter its verdicts. Code: `delivery.CORROBORATE`, `delivery.corroborated`; tests: `tests/test_posthoc_c2.py`.

## 1. The failure

On one day of the confirmation (site 04231600, 2024-12-28, 12 messages per day, independent loss 0.3, bit-error rate
1e-2), the frozen receiver accepted a unit that it had rebuilt from a corrupted parity message on its fourth decoding
attempt: the corrupted message passed CRC-16 by chance, and 96 readings were certified from wrong values. Retrying the
erasure decoding over several parity combinations gives every retry another chance for a corrupted message to pass a
16-bit check.

## 2. Rules considered

The rules were derived from this mechanism, not tuned on the confirmation outcome:
- Rule A (first variant): every decoding built from parity must reproduce, when re-encoded, a received message that it
  did not use (or no such message may exist).
- Rule B (adopted): only a decoding accepted after an earlier attempt failed must do so. A first attempt carries the
  same single-CRC risk as any directly received data unit, which the framework accepts and states; retries add risk.

Both rules were evaluated by re-running the corruption experiment (`src/p3/robustness.py`) on both cohorts:
`results/{dev,confirm2}_posthoc` (rule A) and `results/{dev,confirm2}_posthoc2` (rule B).

## 3. Results (record-first code; share of days fully certified; independent loss 0.3)

| Cohort | Q | Corruption | Frozen | Rule A | Rule B | Repetition |
|---|---|---|---|---|---|---|
| Confirmation | 6 | none | 0.915 | 0.915 | 0.915 | 0.805 |
| Confirmation | 6 | bit errors 1e-4 | 0.906 | 0.894 | 0.903 | 0.794 |
| Confirmation | 6 | bit errors 1e-3 | 0.821 | 0.713 | 0.784 | 0.684 |
| Confirmation | 6 | 10% of messages hit | 0.863 | 0.815 | 0.847 | 0.736 |
| Confirmation | 6 | bit errors 1e-2 | 0.112 | 0.035 | 0.066 | 0.085 |
| Confirmation | 12 | bit errors 1e-3 | 0.981 | 0.964 | 0.971 | 0.902 |
| Development | 6 | bit errors 1e-3 | 0.843 | 0.743 | 0.811 | 0.715 |

Readings certified outside their tolerance: frozen 96 (confirmation) and 0 (development); rule A 0 and 0; rule B 0
and 0. Glitch experiments: no change (all days certifiable, no false certificate).

## 4. Interpretation

- Rule B removed every false certificate at a small cost under realistic corruption (0.003 at a bit-error rate of
  1e-4; 0.016 with 10% of messages corrupted; 0.037 at 1e-3, six messages per day). Rule A cost three times as much.
- Under extreme corruption (1e-2, where only 16% of 23-byte messages arrive intact), the code with rule B certified
  fewer days than repetition (0.066 against 0.085), because it rejects decodings it cannot corroborate; repetition
  never decodes and therefore never retries.
- The residual risk of a first decoding attempt, and of any directly received unit, remains that of CRC-16
  (2^-16 per corrupted unit). A longer check (CRC-32) would cost one value per message (Section 4 of
  `docs/ROBUSTNESS_RESULTS.md`).
- Rule B is the receiver of the revised method. It was not part of the frozen confirmation, so its evaluation on the
  confirmation cohort is exploratory and is reported as such.
