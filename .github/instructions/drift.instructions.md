---
description: "Use when writing or modifying drift detection modules — PSI, KS tests, chi-squared, Jensen-Shannon divergence, population stability analysis."
applyTo: "src/monitor_dashboard/drift/**"
---
# Drift Detection Guidelines

- The dashboard **visualizes pre-computed drift metrics** from Snowflake — it does not compute drift from raw feature distributions
- Drift data includes: PSI, KS, chi-squared, Jensen-Shannon divergence, computed by an upstream monitoring library
- Display drift results using a `DriftResult` dataclass, never raw dicts
- Always include: metric_name, statistic_value, p_value (if applicable), threshold, is_drifted (bool), run_timestamp
- Support both numerical and categorical feature drift visualization
- Show drift trends over time (sparklines per feature)
- Handle variable model cadences — x-axis must be time-based, not run-index-based
- Reference window metadata (training period, baseline dates) should be displayed for context
- Color-code drift severity: green (stable), amber (warning), red (breached threshold)
