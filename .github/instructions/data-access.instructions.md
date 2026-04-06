---
description: "Use when writing data access code, database queries, data loading, or data pipeline integration."
applyTo: "src/monitor_dashboard/data/**"
---
# Data Access Guidelines

- The dashboard reads **pre-computed monitoring data** from Snowflake — it does not compute drift or metrics from raw predictions
- Four data categories per model: summary stats, data quality, drift metrics, monitoring metrics/estimates
- Abstract all data access behind a repository pattern — dashboard code never queries directly
- Repository interface must support swapping between Snowflake (production) and local synthetic data (development)
- Each model has its own scoring cadence — queries must be cadence-aware, never assume uniform timestamps
- Always return a `last_run_at` timestamp with model data so the UI can show data freshness
- Return polars DataFrames from data access functions — conversion from pandas/Snowpark happens at the boundary
- All queries must be parameterized — never use string interpolation for SQL
- Secrets (connection strings, API keys) must come from environment variables, never config files
- Include timeout and retry logic for external data sources
- Log data access errors with context (source, query type, timestamp) but never log query parameters that may contain PII
