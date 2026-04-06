---
description: "Use when writing or modifying model performance metrics — AUC, KS, Gini, precision, recall, lift, or performance tracking over time."
applyTo: "src/monitor_dashboard/metrics/**"
---
# Model Performance Metrics Guidelines

- Use sklearn-compatible metric names: `roc_auc`, `precision`, `recall`, `f1`, `log_loss`
- Gini = 2 * AUC - 1; always derive rather than compute independently
- KS statistic: compute as max separation between cumulative distributions of positive/negative classes
- All metric functions must accept `y_true` and `y_score`/`y_pred` with clear typing
- Return a `MetricResult` dataclass: metric_name, value, confidence_interval (optional), timestamp, model_name
- Time-series tracking: metrics must be associated with an evaluation window (start_date, end_date)
- Never expose raw customer-level predictions — only aggregate metrics
- Handle edge cases: single-class batches, NaN scores, insufficient samples
