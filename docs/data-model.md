# Data Model

> Schema contract between the data layer and dashboard pages.

## Overview

`generate_all_mock_data()` returns a `dict` with 7 keys. All DataFrames use [Polars](https://pola.rs/). In production, these would be Snowflake query results with identical schemas.

```python
{
    "model_registry":       pl.DataFrame,   # Model metadata
    "score_psi":            pl.DataFrame,   # PSI time series
    "feature_csi":          pl.DataFrame,   # Latest CSI per feature
    "performance":          pl.DataFrame,   # Performance metrics over time
    "data_quality":         pl.DataFrame,   # DQ metrics over time
    "distributions":        dict,           # Bin-level distributions
    "feature_csi_history":  dict,           # CSI time series per feature
}
```

---

## Table Schemas

### `model_registry`

One row per monitored model. Reference data set at model onboarding.

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | `str` | Registered model name (primary identifier) |
| `task` | `str` | `"classification"` or `"regression"` |
| `cadence` | `str` | `"daily"`, `"weekly"`, or `"monthly"` |
| `owner` | `str` | Model owner name |
| `domain` | `str` | Business domain (Credit, Fraud, Leasing, etc.) |
| `n_features` | `int` | Number of input features |
| `baseline_date` | `date` | Date model was onboarded (baseline established) |
| `last_run_date` | `date` | Most recent scoring run date |

### `score_psi`

One row per scoring run per model. Population Stability Index of the model score distribution vs. baseline.

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | `str` | Model identifier |
| `run_date` | `date` | Scoring run date |
| `metric_name` | `str` | Always `"score_psi"` |
| `value` | `float` | PSI value |
| `threshold_warning` | `float` | Warning threshold (typically 0.10) |
| `threshold_critical` | `float` | Critical threshold (typically 0.20) |

### `feature_csi`

One row per feature per model — **latest snapshot only**. Characteristic Stability Index measures per-feature drift.

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | `str` | Model identifier |
| `run_date` | `date` | Latest scoring run date |
| `feature_name` | `str` | Feature name |
| `csi_value` | `float` | CSI value |
| `threshold_warning` | `float` | Warning threshold (typically 0.10) |
| `threshold_critical` | `float` | Critical threshold (typically 0.20) |

### `performance`

Multiple rows per scoring run (one per metric). Tracks model performance over time with estimated/confirmed distinction.

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | `str` | Model identifier |
| `run_date` | `date` | Scoring run date |
| `metric_name` | `str` | Classification: `roc_auc`, `ks_statistic`, `gini`. Regression: `r_squared`, `rmse`, `mae` |
| `value` | `float` | Metric value |
| `is_estimated` | `bool` | `True` if actuals not yet available |
| `actuals_through` | `date \| None` | Date through which actuals are confirmed; `None` if estimated |

### `data_quality`

One row per scoring run per model. Tracks data quality over time.

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | `str` | Model identifier |
| `run_date` | `date` | Scoring run date |
| `total_features` | `int` | Feature count in scoring batch |
| `missing_rate` | `float` | Overall missing value rate (0.0–1.0) |
| `baseline_missing_rate` | `float` | Baseline missing rate for comparison |
| `out_of_range_features` | `int` | Count of features with out-of-range values |
| `schema_valid` | `bool` | Whether schema validation passed |
| `record_count` | `int` | Number of records in scoring batch |

### `distributions`

Nested dict. Baseline vs. current bin-level distributions for each feature of each model. Used for distribution overlay charts.

```python
distributions: dict[str, dict[str, dict]] = {
    "Model Name": {
        "feature_name": {
            "bin_label":    list[str],    # e.g., ["0.0 – 0.1", "0.1 – 0.2", ...]
            "baseline_pct": list[float],  # baseline bin proportions (sum to 1.0)
            "current_pct":  list[float],  # current bin proportions (sum to 1.0)
        },
    },
}
```

**Note:** Bin edges are fixed at model onboarding and reused for all subsequent drift calculations. This ensures PSI/CSI comparability over time.

### `feature_csi_history`

Nested dict of DataFrames. CSI time series per feature per model.

```python
feature_csi_history: dict[str, dict[str, pl.DataFrame]] = {
    "Model Name": {
        "feature_name": pl.DataFrame({
            "model_name":         list[str],
            "run_date":           list[date],
            "feature_name":       list[str],
            "csi_value":          list[float],
            "threshold_warning":  list[float],
            "threshold_critical": list[float],
        }),
    },
}
```

---

## Page Consumption Matrix

| Key | Portfolio | Model Summary | Feature Monitor | Performance |
|-----|:---------:|:-------------:|:---------------:|:-----------:|
| `model_registry` | ● | ● | ● | ● |
| `score_psi` | ● | ● | | ● |
| `feature_csi` | | ● | ● | |
| `performance` | ● | ● | | ● |
| `data_quality` | ● | ● | | |
| `distributions` | | | ● | |
| `feature_csi_history` | | | ● | |

---

## Monitored Models

10 models across 5 business domains with mixed scoring cadences:

| Model | Task | Cadence | Domain | Features | Drift Scenario |
|-------|------|---------|--------|----------|----------------|
| Auto Loan Default | Classification | Daily | Credit | 18 | Critical |
| Fraud Detection | Classification | Daily | Fraud | 22 | Warning |
| Lease Residual Value | Regression | Monthly | Leasing | 14 | Healthy |
| Early Payment Default | Classification | Weekly | Credit | 16 | Healthy |
| Collections Propensity | Classification | Daily | Collections | 15 | Healthy |
| Dealer Risk Score | Regression | Monthly | Dealer | 12 | Healthy |
| Credit Line Increase | Classification | Weekly | Credit | 17 | Warning |
| Application Fraud | Classification | Daily | Fraud | 20 | Healthy |
| Prepayment Risk | Classification | Monthly | Credit | 13 | Healthy |
| Loss Given Default | Regression | Weekly | Credit | 15 | Healthy |

7 classification models, 3 regression models. Scoring cadences: 4 daily, 3 weekly, 3 monthly.
