---
description: "Use when writing or modifying alerting, threshold configuration, notification logic, or alert routing."
applyTo: "src/monitor_dashboard/alerts/**"
---
# Alerting & Threshold Guidelines

- Thresholds are defined in YAML config files, never hardcoded
- Alert severity levels: `info`, `warning`, `critical`
- Each alert must include: model_name, metric_name, current_value, threshold_value, severity, timestamp
- Use a structured `Alert` dataclass — never raw dicts
- Support per-model threshold overrides (model-level config takes precedence over global)
- Alert deduplication: do not re-fire the same alert within a configurable cooldown window
- Critical alerts should be actionable — include context about what drifted and suggested next steps
- Never include customer data or PII in alert messages
