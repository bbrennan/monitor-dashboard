# Model Monitoring Dashboard

## Project Overview

Internal Streamlit/Dash dashboard for the Risk Data Science team (~30 people) in financial services. Monitors ~10 production ML models for data drift, performance degradation, feature importance shifts, and threshold-based alerting.

## Architecture

```
src/monitor_dashboard/
├── app.py              # Streamlit entry point
├── drift/              # Data drift detection (PSI, KS, etc.)
├── metrics/            # Model performance tracking (AUC, KS, Gini, etc.)
├── features/           # Feature importance monitoring
├── alerts/             # Alerting & threshold configuration
├── data/               # Data access layer
└── utils/              # Shared utilities
```

## Code Style

- Python 3.11+, type hints on all public functions
- Use `ruff` for linting and formatting (configured in pyproject.toml)
- Follow Google-style docstrings
- Prefer dataclasses or Pydantic models over raw dicts for structured data
- Use `pathlib.Path` over `os.path`

## Build & Test

```bash
make install       # Install dependencies with uv
make test          # Run pytest
make lint          # Ruff check + format check
make format        # Auto-format with ruff
make run           # Launch dashboard locally
```

## Conventions

- **Sensitive data**: Never log or display PII, account numbers, or model scores tied to real customers. Use synthetic/anonymized data in tests.
- **Model identifiers**: Always reference models by their registered model name, not internal IDs.
- **Metrics naming**: Use sklearn-compatible metric names where possible (e.g., `roc_auc`, `precision`, `recall`).
- **DataFrames**: Prefer polars over pandas for new code. Existing pandas code does not need to be migrated.
- **Configuration**: Use environment variables for secrets, YAML files for model/threshold configs.
- **Error handling**: Fail fast with clear messages. Dashboard pages should show graceful error states, not crash.
