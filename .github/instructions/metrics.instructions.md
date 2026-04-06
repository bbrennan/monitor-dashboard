---
description: "Use when writing or modifying model performance metrics — AUC, KS, Gini, precision, recall, lift, or performance tracking over time."
applyTo: "src/monitor_dashboard/metrics/**"
---
# Model Performance Metrics Guidelines

- The dashboard **visualizes pre-computed performance metrics** from Snowflake — it does not compute metrics from raw predictions
- Metrics are computed by an upstream monitoring library at each model's scoring cadence
- Use sklearn-compatible metric names: `roc_auc`, `precision`, `recall`, `f1`, `log_loss`, `ks_statistic`, `gini`
- Gini = 2 * AUC - 1; always derive rather than compute independently
- Return a `MetricResult` dataclass: metric_name, value, confidence_interval (optional), timestamp, model_name, is_estimated (bool)
- **Distinguish estimated vs. confirmed metrics**: actuals are often delayed weeks to months in financial services
- Show the actuals horizon clearly — when were actuals last available vs. when was the model last scored
- Time-series tracking: metrics must be associated with an evaluation window (start_date, end_date) and the model's scoring cadence
- Handle variable cadences — some models score daily, others monthly; x-axis must be calendar time, not run index
- Never expose raw customer-level predictions — only aggregate metrics
- Handle edge cases: missing actuals windows, single-class batches, insufficient samples
