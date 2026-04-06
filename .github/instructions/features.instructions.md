---
description: "Use when writing or modifying feature importance monitoring — SHAP values, permutation importance, feature contribution tracking."
applyTo: "src/monitor_dashboard/features/**"
---
# Feature Importance Monitoring Guidelines

- Track feature importance over time to detect shifts in model behavior
- Support SHAP-based and permutation-based importance methods
- Importance values must be associated with: model_name, evaluation_date, feature_name, importance_value, rank
- Detect rank shifts: alert when a feature's rank changes by more than a configurable threshold
- Normalize importance values to sum to 1.0 for cross-model comparison
- Never include raw feature values that could contain PII — only importance scores and feature names
- For large feature sets (>100 features), support top-N filtering with configurable N
