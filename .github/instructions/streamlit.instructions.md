---
description: "Use when writing or modifying Streamlit dashboard pages, UI components, layouts, or visualizations."
applyTo: "src/monitor_dashboard/app.py"
---
# Streamlit Dashboard Guidelines

- Each monitoring concern (drift, metrics, features, alerts) gets its own page via `st.navigation`
- Use `st.cache_data` for data loading and `st.cache_resource` for expensive connections
- Display graceful error states with `st.error()` or `st.warning()` — never let a page crash
- Model selector should appear in sidebar, shared across all pages
- Date range selector for evaluation windows should default to last 30 days
- Charts: prefer Plotly for interactive visualizations
- All displayed values must be aggregated — never show individual customer-level data
- Use `st.metric()` for KPIs with delta indicators showing change vs. previous period
