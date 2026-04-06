---
description: "Use when writing or modifying pytest tests, test fixtures, test data generation, or test configuration."
applyTo: "tests/**"
---
# Testing Guidelines

- Use pytest with fixtures in `conftest.py` for shared test setup
- Use synthetic/anonymized data only — never real customer data in tests
- Test data factories: use `polars.DataFrame` builders for generating reproducible test datasets
- Test drift functions with known distributions (e.g., normal vs. shifted normal)
- Test metric functions against known sklearn outputs for validation
- Test threshold alerting with edge cases: exactly at threshold, just above, just below
- Parametrize tests across multiple models/metrics where applicable with `@pytest.mark.parametrize`
- Mark slow tests with `@pytest.mark.slow` — these are excluded from `make test` by default
