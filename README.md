# Model Monitoring Dashboard

Internal dashboard for the Risk Data Science team. Monitors production ML models for data drift, performance degradation, feature importance shifts, and threshold-based alerting.

## Quick Start

```bash
make install    # Install dependencies (requires uv)
make run        # Launch dashboard
```

## Development

```bash
make test       # Run tests (excludes slow)
make test-all   # Run all tests
make lint       # Check linting & formatting
make format     # Auto-format
make check      # Lint + test
```

## Project Structure

```
src/monitor_dashboard/
├── app.py          # Streamlit entry point
├── drift/          # Data drift detection (PSI, KS, etc.)
├── metrics/        # Model performance tracking
├── features/       # Feature importance monitoring
├── alerts/         # Alerting & threshold configuration
├── data/           # Data access layer
└── utils/          # Shared utilities
```

## Configuration

- **Secrets**: Environment variables (`.env` file, never committed)
- **Model/threshold configs**: YAML files in `config/`
