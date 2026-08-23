# atta_satta

**Atta Satta** is an experimental historical lottery analysis and prediction research platform.

The project studies whether historical lottery results, statistical features, temporal patterns, and experimentally defined astronomical features contain measurable out-of-sample predictive information.

> **Scientific disclaimer:** Lottery outcomes may be random or independently generated. This project does not claim that lottery results can be reliably predicted. Candidate rankings are experimental statistical estimates, not guaranteed winning numbers.

## MVP status

The MVP now contains the complete foundation-to-analysis flow:

```text
PDF/Image
  -> source fingerprint + provenance
  -> PDF extraction / OCR
  -> candidate normalization
  -> validation and review status
  -> SQLite historical database
  -> descriptive statistics
  -> explainable frequency/recency ranking
  -> leakage-safe walk-forward backtesting
  -> model comparison report
  -> Streamlit dashboard / CLI
```

### Implemented capabilities

- PDF text extraction with page provenance
- Image OCR with OCR confidence metadata
- SHA-256 source-file fingerprints
- Canonical `LotteryDraw` domain model
- Conservative normalization that never silently changes OCR characters
- Valid/review/invalid record states
- Non-destructive duplicate detection
- SQLite historical storage and indexed read queries
- Frequency, recency/gap, distribution and autocorrelation analysis
- Explainable candidate ranking
- Reproducible random baseline
- Walk-forward backtesting without target-draw leakage
- Model-comparison status reporting
- Optional experimental astronomy feature engine using Skyfield
- Streamlit dashboard for data preview, historical analysis and candidate ranking
- CLI for statistics and candidate ranking
- Unit-test coverage for the core pipeline

## Install

Core development installation:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For the full MVP:

```bash
python -m pip install -e ".[all,dev]"
```

If your shell interprets extras differently, install them separately:

```bash
python -m pip install -e ".[documents]"
python -m pip install -e ".[ocr]"
python -m pip install -e ".[analytics]"
python -m pip install -e ".[astronomy]"
python -m pip install -e ".[ui]"
```

Tesseract itself must also be installed on the host for OCR. Skyfield may download its ephemeris data when astronomy calculations are first used.

## Run the CLI

Show historical statistics:

```bash
atta-satta stats
```

Rank an experimental candidate range:

```bash
atta-satta predict --minimum 0 --maximum 99 --count 10
```

Use a specific database:

```bash
atta-satta --database data/atta_satta.sqlite3 stats
```

## Run the dashboard

```bash
streamlit run src/atta_satta/ui/app.py
```

The dashboard provides:

- dataset summary
- historical frequency table
- PDF/image extraction preview
- OCR preview
- experimental candidate ranking
- evaluation status

## Data quality and provenance

Imported records preserve source filename, source hash, source page, extraction method, extraction confidence, original extracted text and validation status. Questionable values are retained for review rather than silently discarded.

## Prediction methodology

The MVP deliberately starts with transparent baselines. The current ranking combines historical frequency and recency; it does **not** claim those features increase the true probability of an independent lottery outcome.

Walk-forward validation evaluates a target draw using only records that occurred before that draw. Random and historical baselines can therefore be compared without look-ahead leakage.

Astronomy features are explicitly experimental. They must demonstrate reproducible out-of-sample improvement before they can be allowed to influence a combined ranking.

The application reports unsuccessful predictions as well as successful ones. A high numerical score is not automatically labeled high confidence; validation is required before confidence categories become meaningful.

## Testing

```bash
python -m pytest
ruff check .
mypy src
```

## Project structure

```text
src/atta_satta/
├── astronomy/       # experimental celestial features
├── database/        # SQLite persistence and queries
├── evaluation/      # walk-forward backtesting
├── extraction/      # PDF extraction
├── ingestion/       # source file provenance
├── models/          # model comparison
├── normalization/   # canonical domain records
├── ocr/             # image OCR
├── pipeline/        # import orchestration
├── prediction/      # candidate ranking
├── statistics/      # historical analysis
├── ui/              # Streamlit MVP
└── validation/      # record validation and duplicate detection
```

## Limitations of the MVP

- Document layouts are not yet automatically learned; extraction output still needs domain-specific parsing/review.
- OCR correction is intentionally conservative and does not guess substitutions such as `O -> 0`.
- The current ranking is a baseline, not a validated winning-number predictor.
- Full historical-feature ML and astronomy-feature model training require sufficient real timestamped data and are not enabled by default.
- PostgreSQL/FastAPI production deployment is not required for the MVP; SQLite and Streamlit keep the initial system reproducible and inexpensive.
