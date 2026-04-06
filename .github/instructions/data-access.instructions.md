---
description: "Use when writing data access code, database queries, data loading, or data pipeline integration."
applyTo: "src/monitor_dashboard/data/**"
---
# Data Access Guidelines

- Abstract all data access behind a repository pattern — dashboard code never queries directly
- Use connection pooling for database access
- Secrets (connection strings, API keys) must come from environment variables, never config files
- Return polars DataFrames from data access functions — conversion from pandas happens at the boundary
- All queries must be parameterized — never use string interpolation for SQL
- Include timeout and retry logic for external data sources
- Log data access errors with context (source, query type, timestamp) but never log query parameters that may contain PII
