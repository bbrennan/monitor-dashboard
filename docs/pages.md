# Dashboard Pages

> Reference for each dashboard page — purpose, audience, and key features.

## Page 1: Portfolio Overview

**File:** `src/monitor_dashboard/pages/1_portfolio.py`
**Icon:** `:material/dashboard:`
**Primary audience:** CRO, VP

The landing page — a "morning coffee" scan of the entire model portfolio.

### Layout

1. **Health summary bar** — colored bar showing healthy/warning/critical model counts
2. **Metric cards** — total models, healthy count, warning count, critical count
3. **Needs Attention section** — models with PSI warnings or critical drift, ranked by severity
4. **Stable Models expander** — collapsed by default, shows all healthy models
5. **Recent Events feed** — timeline of recent alert events across all models

### Key behaviors

- Models are ranked by health status, not alphabetically
- Each model card shows: PSI value, status badge, performance metric, last run date
- Clicking a model navigates to the Model Summary page (`st.switch_page`)
- CRO can scan the entire portfolio in under a minute

---

## Page 2: Model Summary

**File:** `src/monitor_dashboard/pages/2_model_summary.py`
**Icon:** `:material/monitoring:`
**Primary audience:** Validation Analyst, Model Owner

Single-model deep dive — WhyLabs/Fiddler-style large metric panels on a scrollable page.

### Layout

1. **Model header** — name, cadence, domain, owner, last run date
2. **Score PSI panel** — current PSI value with status badge + PSI trend chart
3. **Performance panel** — current metrics (AUC/KS/Gini or R²/RMSE/MAE) with trend chart, actuals staleness warning
4. **Feature Drift panel** — top drifted features by CSI, horizontal bar chart
5. **Data Quality panel** — missing rate, out-of-range count, schema status
6. **Model Info table** — reference metadata

### Key behaviors

- Model selected via sidebar selectbox (persists in session state)
- Performance metrics adapt to task type (classification vs. regression)
- Actuals staleness prominently displayed when metrics are estimated
- Feature CSI bar chart links to Feature Monitor for drill-down

---

## Page 3: Feature Monitor

**File:** `src/monitor_dashboard/pages/3_feature_monitor.py`
**Icon:** `:material/query_stats:`
**Primary audience:** Model Owner

Feature-level drift investigation — the deepest level of the drill-down.

### Layout

1. **Feature ranking** — all features sorted by CSI (worst-first), horizontal bar chart
2. **Feature deep dive** (select any feature):
   - **Distribution tab** — baseline vs. current bin-level overlay chart
   - **CSI History tab** — CSI trend over time with warning/critical threshold lines
   - **Summary Stats tab** — feature-level statistics comparison

### Key behaviors

- Features color-coded by CSI status (green/amber/red)
- Distribution overlay uses grouped bar chart (baseline vs. current per bin)
- CSI history shows the feature's drift trajectory over all scoring runs
- Helps answer: "Which features drove the PSI shift?"

---

## Page 4: Performance

**File:** `src/monitor_dashboard/pages/4_performance.py`
**Icon:** `:material/speed:`
**Primary audience:** Validation Analyst, Model Owner

Performance tracking with explicit estimated vs. confirmed distinction.

### Layout

1. **Actuals horizon** — how stale the actuals are (days since last confirmed metric)
2. **Metric selector** — radio buttons to switch between available metrics
3. **Performance trend chart** — metric value over time, estimated (dashed) vs. confirmed (solid)
4. **Recent runs table** — tabular view of recent scoring runs with metric values and estimation status
5. **PSI × Performance correlation** — dual-axis chart overlaying PSI trend with performance

### Key behaviors

- Estimated metrics shown with dashed lines; confirmed with solid
- Actuals lag is shown prominently with a warning callout
- Task-appropriate metrics: classification gets AUC/KS/Gini, regression gets R²/RMSE/MAE
- PSI × Performance chart helps identify whether drift is causing degradation
