# Atta Satta

**Atta Satta** is an experimental historical lottery analysis and prediction research platform.

The project studies whether historical lottery results, statistical features, temporal patterns, and experimentally defined astronomical features contain measurable **out-of-sample predictive information**.

> **Scientific disclaimer:** Lottery outcomes may be random or independently generated. This project does not claim that lottery results can be reliably predicted. Candidate rankings are experimental statistical estimates, not guaranteed winning numbers.

---

# Current Project State

**State snapshot:** 2026-09-05<br>
**Repository:** `raajivvkumar/atta_satta`<br>
**Default branch:** `main`<br>
**Version:** `0.1.0`<br>
**Primary language:** Python 3.12+<br>
**Persistence:** SQLite<br>
**UI:** Streamlit
**Package entry point:** `atta-satta`

This README is the canonical handoff/state document for future development. Read it before starting a new implementation phase.

## Current end-to-end pipeline

```text
PDF / Image source
        |
        v
Source fingerprint + provenance
        |
        +--> PDF text extraction
        |
        +--> Image OCR / Tesseract
        |
        v
Ticket-number candidate extraction
        |
        v
Normalization + validation + review status
        |
        v
SQLite historical database
        |
        +--> Descriptive statistics
        +--> Frequency / recency ranking
        +--> Random baseline
        +--> Walk-forward backtesting
        +--> Model comparison
        +--> Experimental astronomy features
        |
        v
CLI + Streamlit dashboard
```

## Feature status

| Area | Current state |
|---|---|
| Configuration | Pydantic settings and project/data paths implemented |
| Logging | Application logging module implemented |
| File ingestion | Supported-source validation, SHA-256 fingerprint and metadata implemented |
| PDF extraction | Page-by-page text extraction with provenance implemented |
| OCR | Tesseract image and scanned-PDF OCR with confidence metadata implemented |
| Ticket detection | Line-aware ranked extraction for varied result formats implemented |
| Normalization | Canonical lottery draw model and conservative normalization implemented |
| Validation | Valid/review/invalid states and range validation implemented |
| Duplicate handling | Non-destructive duplicate detection implemented |
| Database | SQLite persistence and indexed queries implemented |
| Statistics | Frequency, distribution, gaps/recency and autocorrelation-related analysis implemented |
| Prediction | Explainable frequency/recency candidate ranking implemented as a baseline |
| Random baseline | Reproducible random ranking implemented |
| Backtesting | Chronological walk-forward evaluation implemented |
| Model comparison | Random/historical comparison plus readiness/status reporting implemented |
| Astronomy | Basic experimental Sun/Moon/lunar-phase features implemented through Skyfield |
| Historical ML | Dependencies and readiness foundation exist; no validated production ML model yet |
| Combined model | Explicitly disabled until component signals demonstrate out-of-sample improvement |
| CLI | `stats`, `predict`, `backtest`, `models`, `ocr`, `import` implemented |
| UI | Streamlit upload/review, prize-labeled results, statistics, ranking and evaluation status implemented |
| Tests | Unit and integration coverage implemented |

## Latest saved state

- The Streamlit dashboard runs with:

  ```powershell
  .\.venv\Scripts\streamlit.exe run src\atta_satta\ui\app.py
  ```

- Local dashboard URL: `http://127.0.0.1:8501`
- Tesseract 5.4.0 is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- OCR automatically discovers `TESSERACT_CMD`, Tesseract on `PATH`, and the standard
  Windows installation directories. A manual PATH restart is not required for the app.
- Scanned PDFs are rendered page by page and processed through the same Tesseract
  configuration as image uploads.
- Result previews display only `Rank` and `Ticket Number`; prize amounts are excluded.
- Rank labels are displayed as `1st Prize`, `2nd Prize`, `3rd Prize`, `4th Prize`, and
  so on. Explicit labels in source text are preferred; unlabeled rows use source order.
- Validation completed: full test suite passed, OCR integration tests passed, and Ruff
  lint passed.

---

# Technology Stack

- Python `>=3.12`
- pandas
- NumPy
- Pydantic / pydantic-settings
- PyMuPDF
- pdfplumber
- OpenCV
- Pillow
- pytesseract
- SciPy
- scikit-learn
- Skyfield
- Streamlit
- SQLite
- pytest / pytest-cov
- Ruff
- mypy

Optional dependencies are separated in `pyproject.toml` for documents, OCR, analytics, astronomy and UI.

---

# Source Data and Ticket Detection

## Supported source files

- PDF
- PNG
- JPG / JPEG
- TIFF / TIF
- WEBP

Source provenance includes filename, SHA-256 fingerprint, source page where applicable, extraction method, extraction confidence, original extracted text and validation status. Questionable values are retained for review rather than silently discarded.

## Supported ticket patterns

The structured ticket extractor currently recognizes patterns such as:

```text
A123456
B123456
C123457

A-123456
B-123456
C-123456

A 123456
B 123456
C 123456

1234568
1234587
1234659
```

Prefixed tickets normalize to uppercase without separators:

```text
A123456
A-123456
A 123456
```

all become:

```text
A123456
```

Numeric structured tickets currently use seven digits.

The extractor deliberately avoids numbers embedded in larger alphanumeric tokens such as:

```text
XA1234567
12345678
```

Each `TicketCandidate` retains normalized value, raw value, detected pattern, confidence and source-text positions. A separate general numeric-token extractor remains available because documents also contain dates, page numbers and unrelated numbers.

The PDF/image result view uses the line-aware ranked extractor. It recognizes explicit
labels such as `1st`, `Rank 2`, `Third Prize`, and `Position 4`, associates the
nearest ticket on that result line (or the immediately following line), and displays
only `Rank` and `Ticket Number`. Prize amounts are not displayed as results. When a
document has no rank labels, source order is used as the fallback.

---

# OCR State

Image OCR is implemented with `pytesseract` and Pillow. The OCR flow validates the image, runs Tesseract, collects available confidence values, returns the extracted text and passes that text to ticket candidate detection.

`pytesseract` is only a Python wrapper. The external **Tesseract executable must also be installed and available on `PATH`**. This was a real development environment issue encountered in Codespaces and is documented here so it is not mistaken for an application-code failure.

On Windows, install Tesseract OCR. The application automatically checks the standard
installation directory (`C:\Program Files\Tesseract-OCR`) even when it is not on the
current process `PATH`. You can also set `TESSERACT_CMD` to an explicit executable
path. To verify the installation manually:

```powershell
tesseract --version
```

OCR is intentionally conservative: the system does not silently guess substitutions such as `O -> 0`.

---

# Import and Validation Pipeline

```text
source file
  -> provenance
  -> PDF extraction / OCR
  -> ticket candidates
  -> normalization
  -> validation
  -> duplicate checks
  -> SQLite
```

The canonical historical entity is `LotteryDraw`. Stored provenance includes game, draw date/time, timezone, ticket number, source filename/hash/page, extraction method/confidence, original text, validation status and import timestamp.

SQLite currently indexes game/date and source hash.

The import process is review-first and never silently converts questionable OCR text into a supposedly correct ticket.

---

# Current Statistical Analysis

Implemented analysis includes:

- frequency counts
- relative frequency
- last-seen position / gap
- distribution summary
- mean
- standard deviation
- number range
- unique-number counts
- temporal/rolling analysis foundations
- autocorrelation-related analysis
- random-baseline comparison

These are descriptive/statistical features. They do not prove that historical frequency changes the probability of a future independent draw.

---

# Current Prediction Engine

The current ranking is deliberately a transparent **baseline**, not a winning-number predictor.

The implemented score is based on frequency and recency:

```text
historical = 0.6 * frequency + 0.4 * recency
score      = 0.7 * historical + 0.3 * frequency
```

These are baseline weights, not scientifically validated probabilities.

Each candidate exposes:

- rank
- ticket number
- overall score
- statistical score
- historical score
- astronomy score
- model score
- supporting signals
- contradicting signals
- explanation
- confidence category

Confidence is `Unvalidated` unless ranking validation has explicitly been enabled. This prevents the UI from manufacturing confidence.

---

# Backtesting

Walk-forward backtesting is implemented. For target draw `D`, only records before `D` are used:

```text
history[0 ... D-1] -> prediction for D
```

The current comparison is:

1. Historical frequency/recency ranking
2. Reproducible random ranking

Current metrics:

- prediction count
- top-K hits
- hit rate
- random hit rate
- lift versus random

The implementation is chronological and avoids ordinary random train/test splitting for this time-dependent problem.

The current backtest is still a foundation. It does not yet provide the complete research-grade evaluation suite requested for the final system, including calibrated probabilities, Brier score, all applicable MRR/precision/recall formulations, bootstrap uncertainty, multiple-testing correction and formal significance testing.

---

# Model Comparison State

Current model families are represented as follows:

- **Random baseline:** validated when enough observations exist.
- **Frequency/recency baseline:** validated through chronological evaluation when enough observations exist.
- **Statistical model:** descriptive/statistical foundation exists; schema-specific inferential modeling remains to be implemented.
- **Historical-feature ML:** readiness is reported after a minimum data threshold, but a demonstrated validated ML model is not yet enabled.
- **Astronomy-feature model:** experimental readiness depends on timestamped observations.
- **Combined model:** explicitly disabled until component signals demonstrate out-of-sample improvement.

This conservative behavior is intentional. More complexity must never be treated as evidence of better prediction.

---

# Astronomy State

Astronomy is an **experimental feature layer** and currently includes:

- timezone-aware UTC timestamp validation
- Sun ecliptic longitude
- Moon ecliptic longitude
- lunar phase angle

Skyfield is used for calculations.

Astronomy currently does **not** influence the baseline candidate ranking.

Future experimental features may include planetary positions, angular separations, declination, ecliptic longitude, appropriate retrograde/direct state and reproducible conjunction/opposition/aspect-derived variables.

Every astronomy feature must be evaluated out-of-sample against history-only baselines before it can contribute to a combined ranking. Astrological interpretations must not be presented as scientific causal claims.

---

# CLI

The package defines:

```text
atta-satta = atta_satta.cli:main
```

Current commands in source:

```bash
atta-satta stats
atta-satta predict --minimum 0 --maximum 99 --count 10
atta-satta backtest --minimum 0 --maximum 99 --top-k 10
atta-satta models --minimum 0 --maximum 99 --top-k 10
atta-satta ocr data/input/R01.webp
atta-satta import data/input/R01.webp --game R01 --draw-date 2026-08-23 --minimum 0 --maximum 9999999
```

A specific database can be selected with:

```bash
atta-satta --database data/atta_satta.sqlite3 stats
```

The console command is provided by the package installation declared in `pyproject.toml`.

---

# Streamlit UI

Implemented in `src/atta_satta/ui/app.py`.

### Dashboard

- validated record count
- unique ticket count
- minimum/maximum values
- historical frequency table

### Import

- multiple PDF/image uploads
- PDF extraction preview
- image OCR preview
- source SHA-256
- OCR confidence
- rank labels formatted as `1st Prize`, `2nd Prize`, `3rd Prize`, etc.
- prize amounts excluded from the result preview
- manual reviewed-result commit
- validation before insertion

### Prediction

- configurable ticket range
- configurable candidate count
- explainable ranking table
- statistical/historical/astronomy/model scores
- supporting and contradicting signals

### Evaluation

- points to leakage-safe CLI backtesting/model comparison
- labels the analysis as experimental

---

# Project Structure

```text
src/atta_satta/
├── __init__.py
├── config.py
├── logging.py
├── cli.py
├── astronomy/
│   ├── __init__.py
│   └── features.py
├── database/
│   ├── __init__.py
│   ├── sqlite.py
│   └── queries.py
├── evaluation/
│   ├── __init__.py
│   └── backtest.py
├── extraction/
│   ├── __init__.py
│   ├── candidates.py
│   └── pdf.py
├── ingestion/
│   ├── __init__.py
│   └── files.py
├── models/
│   ├── __init__.py
│   └── comparison.py
├── normalization/
│   ├── __init__.py
│   ├── models.py
│   └── text.py
├── ocr/
│   ├── __init__.py
│   └── image.py
├── pipeline/
│   ├── __init__.py
│   └── importer.py
├── prediction/
│   ├── __init__.py
│   └── ranking.py
├── statistics/
│   ├── __init__.py
│   └── analysis.py
├── ui/
│   ├── __init__.py
│   └── app.py
└── validation/
    ├── __init__.py
    ├── duplicates.py
    └── results.py

tests/
├── integration/
│   └── test_optional_components.py
└── unit/
    ├── test_backtest.py
    ├── test_config.py
    ├── test_database.py
    ├── test_duplicates.py
    ├── test_extraction_candidates.py
    ├── test_ingestion.py
    ├── test_models.py
    ├── test_normalization.py
    ├── test_package.py
    ├── test_pipeline.py
    ├── test_prediction.py
    ├── test_statistics.py
    └── test_validation.py
```

---

# Testing and Quality State

Configured quality commands:

```bash
python -m pytest
ruff check .
mypy src
```

Ruff is configured with line length 100 and E/F/I/B/UP checks. The project has automated unit and integration tests for the core pipeline.

### Latest known validation state

During the latest reported development cycle:

- Ruff reached a clean state.
- The earlier ingestion `.txt` test mismatch was corrected while keeping `.txt` rejected as an unsupported source format.
- The test suite reached **43 collected tests**.
- The last explicitly reported test run had **42 passing and 1 failing** in `test_ticket_candidates_do_not_match_embedded_numbers`, involving `XA1234567`. The ticket extractor was subsequently adjusted during development, so the full suite must be rerun before claiming the repository is fully green.

Do not record a test suite as passing unless the current checkout has actually been tested.

---

# Known Limitations / Technical Debt

1. **OCR environment:** Tesseract executable is an external host dependency.
2. **OCR quality:** OCR can produce errors and corrections are intentionally conservative.
3. **Document layouts:** PDF/image layouts are not automatically learned.
4. **Ticket detection:** Current patterns are deliberately limited and should be expanded from real source evidence.
5. **ML:** No demonstrated leakage-safe ML model has yet proven out-of-sample superiority over simple baselines.
6. **Astronomy:** Experimental features are not predictive evidence and do not influence the baseline ranking.
7. **Backtesting:** Deeper calibration, bootstrap uncertainty, multiple-testing safeguards and formal significance analysis remain.
8. **Production deployment:** SQLite/Streamlit are sufficient for the MVP; PostgreSQL/FastAPI should wait until justified by actual scale.

---

# Next Development Roadmap

Continue incrementally. Do not rewrite working modules without justification.

## Priority 1 — Real-data ingestion validation

1. Add representative real PDF/image fixtures.
2. Run PDF extraction and OCR against them.
3. Validate ticket detection against actual layouts.
4. Measure false positives and false negatives.
5. Expand patterns only when real source evidence requires it.
6. Verify provenance through the entire import flow.

## Priority 2 — Research-grade evaluation

1. Build a canonical time-indexed evaluation dataset.
2. Persist every walk-forward prediction.
3. Store feature snapshots and eventual outcomes.
4. Add top-1/top-K, MRR and applicable precision/recall.
5. Add probability calibration and Brier score where probability estimates exist.
6. Add bootstrap uncertainty estimates.
7. Add multiple-testing safeguards.
8. Compare every experiment with random and simple historical baselines.

## Priority 3 — Historical-feature ML

1. Define target and feature schema.
2. Generate only pre-draw features.
3. Use chronological splits.
4. Start with simple models.
5. Compare against the existing baseline.
6. Reject models without reproducible out-of-sample improvement.

## Priority 4 — Astronomy experiment

1. Require precise draw timestamps and timezone information.
2. Generate astronomy features independently of results.
3. Compare astronomy-only against history-only features.
4. Use walk-forward validation.
5. Report effect size and uncertainty, not just hit rate.
6. Do not add astronomy weights unless evidence justifies them.

## Priority 5 — Combined model

Only after independent validation of component models should combined weights be learned and validated.

---

# Scientific Decision Rule

The project succeeds scientifically even if the result is:

> **Historical, ML, and astronomical features do not provide measurable predictive information beyond random/simple baselines.**

That is a valid research result.

The application may still generate ranked candidates when requested, but those candidates must remain clearly labeled as experimental rankings rather than guaranteed winning numbers.

The primary objective is to measure whether a predictive signal exists, not to manufacture impressive-looking predictions.

---

# Future Development Rule

Before making a substantial change:

1. Read this README completely.
2. Inspect the current source files involved.
3. Reuse working modules.
4. Preserve provenance and reviewability.
5. Add/update tests for behavioral changes.
6. Run Ruff and the full test suite.
7. Do not claim validation without testing the current checkout.
8. Never introduce look-ahead leakage.
9. Never turn experimental correlation into a causal or guaranteed prediction claim.

This README is the project handoff/state document for future development sessions.
