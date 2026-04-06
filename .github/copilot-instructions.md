# Model Monitoring Dashboard

## Project Overview

Design exploration / prototype for a model monitoring dashboard for the Risk Data Science team (~30 people) at Toyota Financial Services. This is a **local development sandbox** — not the production product. No access to production data or databases.

The production environment uses **Snowflake**. Any architecture decisions must be compatible with Snowflake as the data platform (Snowpark, Snowflake connectors, Streamlit in Snowflake, etc.).

Monitors ~10 production ML models for data drift, performance degradation, feature importance shifts, and threshold-based alerting.

## Branding

- Toyota Financial Services (TFS) branding
- Primary: TFS Red (`#EB0A1E`), Dark Gray (`#333333`), White (`#FFFFFF`)
- Accent: Toyota Gray (`#58595B`), Light Gray (`#D1D3D4`)
- Typography: clean, modern sans-serif (Toyota Type or fallback to system fonts)
- Professional, data-dense aesthetic — not consumer-facing flashy

## Branching Strategy

- `main` — stable, reviewed code only (PRs from `develop`)
- `develop` — integration branch (PRs from epic branches)
- `epic/<name>` — one branch per epic, PR'd into `develop`
- `feature/<epic>/<name>` — task branches off an epic branch if needed

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
- **Data layer**: Must be designed to work with Snowflake. Use synthetic/local data for development; real queries happen against Snowflake in production.
- **Local development**: Use synthetic data generators and local fixtures — never depend on network access to run the dashboard locally.
