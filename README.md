# atta_satta

**Atta Satta** is an experimental historical lottery analysis and prediction research platform.

The project is designed to study whether historical lottery results, statistical features, temporal patterns, and experimentally defined astronomical features contain measurable out-of-sample predictive information.

> **Scientific disclaimer:** Lottery outcomes may be random or independently generated. This project does not claim that lottery results can be reliably predicted. Candidate rankings are experimental statistical estimates, not guaranteed winning numbers.

## Current Status

Phase 1 — repository stabilization is in progress.

The repository now uses a Python `src/` package layout with:

- Python 3.12+
- `pyproject.toml` packaging
- Hatchling build backend
- pytest test configuration
- Ruff lint configuration
- mypy strict configuration
- typed application configuration
- application logging foundation
- environment configuration template

## Development

Create a virtual environment and install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

Run linting:

```bash
ruff check .
```

Run type checking:

```bash
mypy src
```

## Planned Pipeline

```text
Input Files
    -> Extraction / OCR
    -> Validation
    -> Normalization
    -> Historical Database
    -> Feature Engineering
    -> Statistical Analysis
    -> Astronomy Features
    -> Prediction Models
    -> Walk-forward Backtesting
    -> Candidate Ranking
    -> Evaluation
```

The implementation will prioritize reproducibility, data provenance, temporal validation, leakage prevention, and honest reporting of unsuccessful predictions.
