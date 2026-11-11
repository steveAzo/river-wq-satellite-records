# Certified threshold decisions from error-bounded river water-quality records over one-way satellite IoT links

Code and data for the paper by Kofi Sarpong Adu-Manu and Stephen Kwaku Azongo (Department of Computer Science,
University of Ghana), prepared for Environmental Modelling & Software.

Archive (Zenodo; these are earlier versions of the work, the current version is not yet deposited):
- Version v2.0.0: https://doi.org/10.5281/zenodo.23711183
- Version v1.0.0, the first round: https://doi.org/10.5281/zenodo.23617665
- All versions (always resolves to the latest): https://doi.org/10.5281/zenodo.23617664

Cite as: see `CITATION.cff`.

Licence: MIT for the code; CC BY 4.0 for the derived data and results (see `LICENSE`). Third-party data keep their
own licences; the Weija data are not included.

## The question and the answer in brief

Remote rivers often lie beyond terrestrial networks, and satellite IoT services sell a few short, one-way messages per
day; the node never learns which were lost. A node sends an error-bounded record within the USGS "excellent"
tolerance plus witnesses of hard cases (quantised daily extrema, a conductance rate pair), erasure-coded with a CRC-24
per 23-byte message. The server answers threshold queries with exceeded, not exceeded, or undetermined, soundly under
stated assumptions.

Second confirmation (version 3 of the method; frozen at tag `confirm4-freeze`; 35 sealed USGS sites, 2022; byte level):
- All three hypotheses that could fail held. On thresholds nobody configured, the witness design decided 0.18 to 0.23
  more hard cases than a node sending configured decision flags plus its record, and 0.20 to 0.28 more than the record
  alone, at a cost of 0.03 to 0.08 in whole-record recovery.
- No certain decision was wrong; 41,668 message blocks passed a byte-level round trip.
- The design was adopted although its record cost at six messages per day exceeded its own written adoption limit;
  the cost was tested instead (`docs/CONFIRM4_PLAN.md`, Section 1).
- Results: `docs/CONFIRM4_RESULTS.md`. The first confirmation (version 2, 2024) is in `docs/CONFIRM3_RESULTS.md`.

## Layout

| Path | Contents |
|---|---|
| `src/p3v3/` | Version 3: frame with CRC-24, hardened receiver, guarded bounds, slot and byte models, confirmation driver, cohort preparation, freeze writer |
| `src/p3/` | The framework of earlier versions (certificate language, record encoder, codes), reused by version 3; frozen |
| `src/data/` | USGS download and cleaning, cohort selection from metadata, sealing |
| `tests/`, `tests/v3/` | Unit, property, and fuzz tests (`python -m pytest -q -p no:cacheprovider tests`) |
| `docs/` | Plans, results, reviews, and handoffs; start with `docs/ROADMAP_V3.md` and `docs/CONFIRM4_PLAN.md` |
| `data/clean/` | Development data (`usgs/` 2023, `usgs_new3_2024/` 2024) and the sealed cohort (`usgs_new4_2022/`, seal `usgs_new4_2022.md5`) |
| `results/` | `confirm4/` (the confirmation), `rehearsal4_2023/` and `rehearsal4v2/` (development rehearsals), `v3dev/`, and earlier rounds |
| `draft4/` | Manuscript v1.0 (elsarticle); deliverables in `draft4/deliverables/` |
| `paper_tools/` | Tables, figures, Word copy, and number audit of the manuscript |
| `archive/` | Superseded manuscripts, rehearsals, and early reviews (`archive/README.md`) |

The Weija (Ghana) records belong to the deployment team and are not in this repository; they are available from the
corresponding author on reasonable request.

## Reproducing

Python 3.13; `pip install -r requirements.txt`; run every script from this folder with `python -I`.
- Tests: `python -m pytest -q -p no:cacheprovider tests` (858 tests, about 5 minutes).
- Confirmation (recorded run): `python -I src/p3v3/confirm4.py data/clean/usgs_new4_2022 confirm4 data/clean/usgs_new4_2022.md5`.
  It refuses to start unless the code equals the tag `confirm4-freeze` (record `docs/FREEZE4.md`) and the seal covers the
  folder, and it refuses to run again once finished. To repeat the analysis, copy the folder to a name without "new4" or
  "2022" and run it under another tag (rehearsal mode).
- Manuscript tables and figures: `python -I -W ignore paper_tools/make_v1.py`; then build `draft4/main.tex` with
  pdflatex and bibtex.
