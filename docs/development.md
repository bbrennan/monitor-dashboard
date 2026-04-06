# Development Guide

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
git clone https://github.com/bbrennan/monitor-dashboard.git
cd monitor-dashboard
make install   # uv sync
```

## Running the Dashboard

```bash
make run
# or directly:
uv run streamlit run src/monitor_dashboard/app.py
```

Opens at [http://localhost:8501](http://localhost:8501).

First load takes <1 second (synthetic data). Subsequent page switches are instant thanks to `@st.cache_data`.

## Development Commands

| Command | Purpose |
|---------|---------|
| `make install` | Install/sync dependencies with uv |
| `make run` | Launch Streamlit dashboard |
| `make test` | Run pytest (excludes slow tests) |
| `make test-all` | Run all tests including slow |
| `make lint` | Ruff check + format check |
| `make format` | Auto-format with ruff |
| `make check` | Lint + test combined |
| `make clean` | Remove build artifacts and caches |

## Branching Strategy

```
main                    ← Stable, reviewed code only
  └── develop           ← Integration branch
        └── epic/<name> ← One branch per epic
              └── feature/<epic>/<name>  ← Task branches (if needed)
```

- PRs from `epic/*` → `develop`
- PRs from `develop` → `main`
- Never push directly to `main` or `develop`

## Code Style

- Python 3.11+, type hints on all public functions
- `ruff` for linting and formatting (configured in `pyproject.toml`)
- Google-style docstrings
- Prefer `polars` over `pandas` for new code
- Prefer `pathlib.Path` over `os.path`
- Use dataclasses or Pydantic models over raw dicts for structured data

## Data Layer

### For Development

The dashboard uses `mock_data.py` — a fast numpy-based generator that produces synthetic monitoring data in <1 second. Data is deterministic (seeded with `np.random.default_rng(42)`).

An alternative `sklearn_data.py` trains 10 real GradientBoosting models and computes genuine PSI/CSI metrics. This takes ~60 seconds on first load and is useful for demos requiring realistic statistical correlations.

### For Production

Replace `mock_data.py` imports with a Snowflake data access module. The data contract (7 dict keys, column schemas) remains identical — see [Data Model](data-model.md).

## File Organization

- **Pages**: `src/monitor_dashboard/pages/` — one file per dashboard view
- **Data**: `src/monitor_dashboard/data/` — data generators and access layer
- **Assets**: `src/monitor_dashboard/assets/` — SVG logos, icons
- **Tests**: `tests/` — pytest test files
- **Docs**: `docs/` — architecture, design, and reference documentation
- **Config**: `pyproject.toml` — dependencies, ruff, pytest settings
- **CI**: `.github/workflows/` — GitHub Actions
- **Standards**: `.github/instructions/` — per-module coding guidelines

## Sensitive Data

- Never log or display PII, account numbers, or model scores tied to real customers
- Use synthetic/anonymized data in tests and development
- Reference models by registered name, not internal IDs
- Secrets go in environment variables, never in code or config files
