---
description: "Use when writing or modifying drift detection modules — PSI, KS tests, chi-squared, Jensen-Shannon divergence, population stability analysis."
applyTo: "src/monitor_dashboard/drift/**"
---
# Drift Detection Guidelines

- Implement drift metrics as pure functions: `(reference: pl.DataFrame, current: pl.DataFrame, ...) -> DriftResult`
- Return structured results using a `DriftResult` dataclass, never raw dicts
- Always include: metric_name, statistic_value, p_value (if applicable), threshold, is_drifted (bool)
- Support both numerical (KS, PSI) and categorical (chi-squared, PSI) features
- PSI bins should be configurable with sensible defaults (10 bins)
- Handle edge cases: empty bins, zero counts (use Laplace smoothing)
- Log warnings for low-sample comparisons (< 100 observations)
- Reference and current data windows must be explicitly parameterized, not hardcoded
