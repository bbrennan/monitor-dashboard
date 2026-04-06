# Architecture

> TFS Model Monitoring Dashboard — Technical Architecture

## System Context

```
┌──────────────────────────────────────────────────────────┐
│                   Production Environment                  │
│                                                          │
│   ML Models ──► Monitoring Library ──► Snowflake         │
│   (scoring)     (computes metrics)     (stores results)  │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │  reads pre-computed metrics
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  Monitoring Dashboard                     │
│                                                          │
│   Streamlit App ──► Data Access Layer ──► Snowflake      │
│   (visualization)   (queries/caching)    (read-only)     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**The dashboard is a read-only visualization layer.** It does not compute metrics from raw predictions — an existing monitoring library handles that and writes results to Snowflake. The dashboard queries those pre-computed results.

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **UI Framework** | Streamlit | Native Python, Streamlit in Snowflake (SiS) deployment path, rapid prototyping |
| **Charts** | Plotly | Interactive, publication-quality, Streamlit-native integration |
| **DataFrames** | Polars | Fast, memory-efficient, preferred over pandas for new code |
| **Data Platform** | Snowflake | Production data warehouse; Snowpark/connectors for integration |
| **Package Manager** | uv | Fast, deterministic dependency resolution |
| **Build System** | hatchling | Standard Python build backend |
| **Linting** | ruff | Fast, all-in-one linter and formatter |
| **Testing** | pytest | Standard Python test framework |

## Application Structure

```
src/monitor_dashboard/
├── app.py                      # Streamlit entry point, theming, navigation
├── assets/
│   ├── logo.svg                # TFS Model Monitor logo (sidebar)
│   └── favicon.svg             # Browser tab icon
├── pages/
│   ├── 1_portfolio.py          # Portfolio Overview (landing page)
│   ├── 2_model_summary.py      # Single-model deep dive
│   ├── 3_feature_monitor.py    # Feature-level drift investigation
│   └── 4_performance.py        # Performance tracking & actuals
├── data/
│   ├── mock_data.py            # Fast synthetic data (numpy-based, <1s)
│   └── sklearn_data.py         # Realistic data with trained models (60s+)
├── drift/                      # Drift detection modules (PSI, KS, etc.)
├── metrics/                    # Performance metric calculations
├── features/                   # Feature importance monitoring
├── alerts/                     # Alerting & threshold configuration
└── utils/                      # Shared utilities
```

### Entry Point

`app.py` is the Streamlit entry point. It:
1. Configures page settings (title, favicon, layout)
2. Injects TFS brand CSS (dark sidebar, color tokens, typography)
3. Renders the SVG logo in the sidebar
4. Defines navigation pages with Material Design icons
5. Delegates to the selected page via `st.navigation()`

### Page Architecture

Each page follows the same pattern:

```python
from monitor_dashboard.data.mock_data import generate_all_mock_data

@st.cache_data
def load_data() -> dict:
    return generate_all_mock_data()

data = load_data()
# ... page-specific rendering
```

Pages are stateless Streamlit scripts. Model selection is coordinated via `st.session_state["selected_model"]`, allowing navigation between pages to preserve context.

### Data Layer

Two data generators exist:

| Module | Load Time | Use Case |
|--------|-----------|----------|
| `mock_data.py` | <1 second | Day-to-day development, CI, demos |
| `sklearn_data.py` | ~60 seconds | Realistic metrics from trained GradientBoosting models |

Both produce the same data contract (see [Data Model](data-model.md)). The active generator is `mock_data.py`; pages import from it exclusively.

In production, `mock_data.py` would be replaced by a Snowflake data access module that queries the monitoring library's output tables. The data contract remains the same.

## Navigation Model

```
Portfolio Overview         ← Landing page (CRO/VP scan)
  │
  ├── Model Summary        ← Single-model hub (Analyst/Owner)
  │     │
  │     ├── Feature Monitor  ← Feature-level drill-down
  │     │
  │     └── Performance      ← Performance trends & actuals
  │
  └── (click any model card to navigate)
```

Hub-and-spoke: Portfolio is the hub. Model Summary is the per-model hub. Feature Monitor and Performance are spokes accessed from Model Summary.

## Deployment Paths

### Local Development (current)
```bash
make run  # uv run streamlit run src/monitor_dashboard/app.py
```

### Streamlit in Snowflake (production target)
- Deploy as a SiS app within the Snowflake account
- Data access switches from mock generators to Snowpark queries
- Authentication handled by Snowflake (no separate auth layer)
- Same Streamlit code, different data backend

### Streamlit Community Cloud (optional staging)
- Connect to GitHub repo
- Use Snowflake connector for data access
- Useful for stakeholder review before SiS deployment

## Configuration

| Configuration | Location | Notes |
|---------------|----------|-------|
| Dependencies | `pyproject.toml` | Managed by uv |
| Lint/format rules | `pyproject.toml` `[tool.ruff]` | ruff configuration |
| Test settings | `pyproject.toml` `[tool.pytest]` | pytest markers and paths |
| Build commands | `Makefile` | install, test, lint, format, run, clean |
| CI/CD | `.github/workflows/` | GitHub Actions |
| Coding standards | `.github/copilot-instructions.md` | Project conventions |
| Module-specific rules | `.github/instructions/*.md` | Per-module coding guidelines |
