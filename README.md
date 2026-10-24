# A regulatory-grade river water-quality record in a few satellite messages a day

Code and data for the paper by Kofi Sarpong Adu-Manu and Stephen Kwaku Azongo (Department of Computer Science, University of Ghana), submitted to Environmental Modelling & Software.

**Archive:** Azongo, S. K. (2026). river-wq-satellite-records, version v1.0.0. Zenodo. https://doi.org/10.5281/zenodo.23617665 (see `CITATION.cff`).

**The question:** what does a river water-quality record within the USGS "excellent" accuracy rating cost in bytes, and how can it be delivered over one-way satellite IoT links that sell a few 23-byte messages a day and lose some of them without notice?

**The answer, in brief (USGS 2024, pre-registered; all seven hypotheses held):**
- A guaranteed day of temperature, specific conductance, dissolved oxygen, and pH needed a median of 15 bytes (1.8% of the raw readings).
- At six messages a day and 30% message loss, the guaranteed record protected by an erasure code was guaranteed on 89% of site-days, against 34% for the same record sent without protection and 43% for satellite-tag practice.

## Layout

| Path | Contents |
|---|---|
| `src/p3/` | The toolkit (below) |
| `src/paper/` | Every number, table, and figure of the manuscript, the draft checker, and the Word copy |
| `src/scoping/`, `src/lit/` | Scoping experiments E1–E13b and literature-search scripts |
| `tests/test_p3.py` | Unit tests (`python -m pytest tests -q`) |
| `docs/STUDY_PLAN.md`, `docs/FREEZE.md`, `docs/CONFIRM_RESULTS.md` | Pre-registered plan, checksums of the frozen plan and code, confirmation verdicts |
| `data/clean/usgs/` | Development set: 39 USGS sites, 2023 (public, USGS NWIS) |
| `data/clean/usgs_2024/` | Confirmation set, 2024; sealed until the plan was frozen (checksums in `data/clean/usgs_2024.md5`) |
| `data/clean/inws_cycles.csv` | InWaterSense node 1, Sitnica River, Kosovo (Ahmedi, Mendeley Data, doi:10.17632/krzv3g6d5f.1, CC BY 4.0) |
| `data/tle/` | Kinéis orbital elements (scoping E4) |
| `results/` | `dev/` (2023), `confirm/` (2024 and low-cost), `lowcost/`, `sens/` (exploratory sensitivity and bootstrap), `scoping/` |
| `draft/` | Manuscript sources (elsarticle); `sh draft/build.sh` rebuilds the PDF and the Word copy |
| `papers/LITERATURE_NOTES.md` | Notes on the literature (the publications themselves are not redistributed) |

**Weija data:** the Weija (Ghana) deployment records belong to the deployment team and are not in this repository; they are available from the corresponding author on reasonable request. Results derived from them are included.

## Toolkit `src/p3/`

| Module | Role |
|---|---|
| `data.py` | Site-days with per-value USGS TM 1-D3 tolerances ("excellent", "good") |
| `pla.py` | Tolerance-normalised min-# selection (Imai and Iri, 1988); `Encoder.fit(k)` gives the smallest common τ that fits k values |
| `server.py` | Reconstruction, the day's guarantee, and certification without feedback |
| `rs.py` | Systematic Reed–Solomon erasure code across messages, GF(256), Cauchy parity |
| `channel.py` | One-way loss channels: independent and Gilbert (bursty) |
| `designs.py` | The delivery designs: raw_periodic, srdl_style, reliable_opt, repeat_r, mds_K |
| `need.py` | RQ1: values and bytes a site-day needs for a guaranteed record |
| `run_dev.py`, `run_confirm.py` | RQ3: tuning on 2023; confirmation on 2024 with the frozen parameters |
| `pooling.py`, `confirm_pooling.py` | RQ2 (buffering across days) and RQ4 (plan choice from a 28-day pilot) |
| `lowcost.py` | Conversion of the low-cost deployments to the toolkit's format |
| `bootstrap.py` | Site-clustered bootstrap intervals (exploratory) |
| `sensitivity.py`, `sens_rq3.py` | Sensitivity analyses (exploratory) |

## Reproducing

Python 3.13; `pip install -r requirements.txt`. Run every script from this folder with `python -I`, for example `python -I src/p3/need.py data/clean/usgs_2024 confirm`. The confirmation outputs are already in `results/confirm/`; `sh draft/build.sh` regenerates every number, table, and figure of the paper from `results/` (it needs a LaTeX installation and pandoc).
