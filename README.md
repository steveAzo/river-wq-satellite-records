# Error-bounded reconstruction and loss-resilient delivery of river water-quality records over satellite IoT

Code and data for the paper by Kofi Sarpong Adu-Manu and Stephen Kwaku Azongo (Department of Computer Science,
University of Ghana), prepared for Environmental Modelling & Software.

Archive (Zenodo):
- Version v2.0.0, the revision behind the manuscript's numbers: https://doi.org/10.5281/zenodo.23711183
- Version v1.0.0, the first round: https://doi.org/10.5281/zenodo.23617665
- All versions (always resolves to the latest): https://doi.org/10.5281/zenodo.23617664

Cite as: Azongo, S. K., and Adu-Manu, K. S. (2026). river-wq-satellite-records (v2.0.0) [Software]. Zenodo.
https://doi.org/10.5281/zenodo.23711183 (see `CITATION.cff`).

Licence: MIT for the code; CC BY 4.0 for the derived data and results (see `LICENSE`). Third-party data keep their
own licences (table below); the Weija data are not included.

## The question and the answer in brief

Remote rivers often lie beyond terrestrial networks, and satellite IoT services sell a few short, one-way messages per
day. The framework sends the fewest values that keep every reading within the USGS "excellent" tolerance, packs them
into 23-byte messages protected by a record-first erasure code, and lets the server certify, from the received bytes
alone, which readings meet the tolerance.

Second confirmation (frozen software and hypotheses; 36 sealed USGS sites in five regions, 2024):
- A four-parameter day needed a median of 27 bytes of values (two messages).
- With six messages per day and 30% simulated loss, 0.900 of days were fully certified, more than repetition (0.799),
  a fixed code (0.786), tag practice (0.030), and periodic readings (0.019).
- Certified three-valued decisions were never wrong; conductance pulses were detected far better than with periodic
  readings; features finer than the tolerance were not resolved.
- Six of eight hypotheses were supported; C1 (record size interval) and C2 (zero false certificates under heavy
  corruption) were not (`docs/CONFIRM2_RESULTS.md`).

## Layout

| Path | Contents |
|---|---|
| `src/p3/` | The framework and every analysis (below) |
| `src/data/` | USGS download and cleaning (unchanged from Paper 2), cohort selection from metadata, sealing, freeze record |
| `src/paper/` | Numbers, tables, figures, supplement, checker, and Word copy of the manuscript |
| `tests/` | Unit and property tests (`python -m pytest tests -q`) |
| `docs/` | Revision plan and records (start with `docs/REVISION_PLAN.md` and `docs/RESPONSE_TO_REVIEW.md`) |
| `data/clean/usgs/` | Development set: 39 USGS sites, 2023 |
| `data/clean/usgs_2024/` | The 39 sites in 2024 (first-round confirmation; now a temporal re-test) |
| `data/clean/usgs_new2024/` | Second confirmation: 36 new sites, 2024; sealed (`data/clean/usgs_new2024.md5`, `data/raw/usgs_new2024.md5`) |
| `data/clean/inws_cycles.csv` | InWaterSense node 1, Sitnica River, Kosovo (doi:10.17632/krzv3g6d5f.1, CC BY 4.0) |
| `results/` | `dev/` (2023), `confirm2/` (second confirmation), `retest2024/`, `lowcost2/`, `*_posthoc*/`, first-round folders |
| `draft/` | Manuscript sources (elsarticle); `sh draft/build.sh` rebuilds the PDF, the supplement, and the Word copy |

The Weija (Ghana) records belong to the deployment team and are not in this repository; they are available from the
corresponding author on reasonable request. Results derived from them are included.

## Framework and analyses (`src/p3/`)

| Module | Role |
|---|---|
| `loader.py` | Per-channel UTC record days on each parameter's own grid; USGS TM 1-D3 tolerances (`data.py`) |
| `record.py` | Quantisation-exact, self-contained encoder (reference, with error tables), reconstruction, certificates, server-side intervals, censoring |
| `stream.py` | Table-free exact encoder, O(n^2) time and O(n) memory, identical plans |
| `frame.py` | 23-byte message frame: header, CRC-16 with context, segments, decimal and logarithmic quantiser |
| `rs.py`, `fountain.py` | Reed-Solomon (Cauchy) and systematic random linear codes over GF(2^8) |
| `delivery.py` | Delivery designs on bytes and the hardened receiver (majority header, CRC, corroborated retries) |
| `analytic.py` | Exact probabilities of full delivery under independent and Gilbert loss |
| `multiday.py` | Packet-level multi-day replay (FIFO buffer, daily code, tag-style rotations) |
| `env.py` | Environmental decisions (three-valued and naive), daily statistics, timing |
| `run_e2e.py`, `run_robust.py`, `robust_eval.py`, `robust_bytes.py` | Delivery experiments, channel-blind choice, byte-level confirmation |
| `run_multiday.py`, `multiday_eval.py`, `run_env.py`, `env_eval.py`, `robustness.py`, `bench.py` | Multi-day, environmental, robustness, and resource experiments |
| `need2.py`, `cohort2.py`, `cohort_exact.py`, `stats.py` | Record cost, cohort flow, exact full-cohort outcomes, bootstrap statistics |
| `confirm2.py` | One-command confirmation run over a sealed folder, with the hypothesis verdicts |
| `lowcost.py`, `lowcost_grid.py` | Low-cost deployments (exploratory) |

## Reproducing

Python 3.13; `pip install -r requirements.txt`; run every script from this folder with `python -I`.
- Development results: the scripts named in each `docs/*_RESULTS.md` file, with `data/clean/usgs` and the tag `dev`.
- Second confirmation: `python -I src/data/seal.py verify data/clean/usgs_new2024.md5`, then
  `python -I src/p3/confirm2.py data/clean/usgs_new2024 confirm2 data/clean/usgs_new2024.md5` (the run used the commit
  tagged `confirm2-freeze`; see `docs/FREEZE2.md`).
- Manuscript: `sh draft/build.sh` (needs LaTeX and pandoc) regenerates every number, table, and figure from `results/`.
- Tests: `python -m pytest tests -q`.
