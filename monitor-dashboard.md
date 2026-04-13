# Mandos Dashboard: Design & Architecture

*ML Engineering, Risk Organization · Internal · April 2026*

---

## 1. Dashboard Structure

### 1.1 Two-Level Navigation

The dashboard follows a **Homepage → Model Detail** pattern:

- **Homepage:** Model portfolio view. Every monitored model in the Auto Credit Risk org appears as a card. Each card shows at-a-glance health: status indicator, active vintage count, latest alert, and a sparkline of the most important trending metric. The user glances at the homepage and immediately knows which models need attention. This is a NOC dashboard, not an app launcher.

- **Model Detail:** Selected when the user clicks a model card. Contains a sidebar with five views: Overview, Vintage Analysis, Data Quality, Drift, and Alerts. The "MANDOS" wordmark in the top bar always returns to the homepage.

### 1.2 Why Separate Views Instead of One Page

The alternative was putting DQ, drift, and vintage charts all on a single scrollable page. We rejected this because:

- The **Overview** already answers "is anything wrong?" in one glance — three health cards plus the active vintages table. Most visits end here. Cluttering it with full charts makes the quick-check use case slower.
- The **Vintage Analysis** view is an investigation tool that needs screen real estate for interactive chart selection, grade/vintage pickers, and insight callouts. Cramming it alongside DQ and drift tables would make both worse.
- **Data Quality** and **Drift** are feature-level detail — tables with 7+ rows of per-feature metrics. These are essential during root cause investigation but irrelevant during routine health checks. They deserve their own space but shouldn't distract from the overview.

The sidebar navigation makes the five views feel like one cohesive experience rather than five separate pages.

---

## 2. Homepage: Model Portfolio

### 2.1 Model Cards

Each card displays:

| Element | Purpose |
|---|---|
| Model name + version | Identification |
| Observation window (e.g., "24 mo") | Context for how long monitoring takes |
| Status dot (green/yellow/red) | Instant health signal |
| Active vintage count | Scale of monitoring activity |
| Latest alert (or "—") | Most recent issue, if any |
| Sparkline | Trending metric (confirmed bad rate or PSI) over last 8 snapshots |

### 2.2 Portfolio KPIs

Above the cards, four summary tiles: total models monitored, count healthy, count warning, count critical. These give leadership the one-number answer to "how's the portfolio?"

### 2.3 Models in the Portfolio

The current model set includes Zuul Originations, Residual Value, Dynamic Pricing, IFRS9 Loss Forecasting, CECL Allowance, and Early Payment Default. As new models are onboarded via YAML config, they automatically appear on the homepage.

---

## 3. Model Detail: Zuul Originations

### 3.1 Sidebar Navigation

| View | Purpose | When Used |
|---|---|---|
| **Overview** | "Is anything wrong?" Health cards + active vintages table + recent alerts. | Every visit. Quick check. |
| **Vintage Analysis** | Deep-dive into vintage performance. Grade separation, cross-vintage trends, vintage overlays, floor/ceiling. | Investigation. When something IS wrong. |
| **Data Quality** | Feature-level DQ metrics: null rates, OOR rates, cardinality vs. baseline. | Root cause investigation. |
| **Drift** | Feature-level PSI/CSI with sparkline trends. | Root cause investigation. |
| **Alerts** | Full audit trail of all threshold breaches with vintage, grade, metric, deviation. | Audit, compliance, post-mortem. |

### 3.2 Overview View

The default landing page when a user selects a model. Contains three sections:

**Health Cards (top row):** Three cards — Data Quality, Drift, Performance — each with a status indicator, the most important metric, and one line of detail. Example: "Drift: 1 feature PSI > 0.20 — dti_ratio: PSI 0.22." The user reads three cards and knows the state of the model across all monitoring dimensions.

**Active Vintages Table:** Every vintage currently being monitored, showing vintage ID, MOB, account count, confirmed bad rate by grade (A through D), portfolio aggregate, and status dot. Grades are color-coded (A = green, B = blue, C = amber, D = red) so the eye is drawn to the highest-risk segments. This table is the single most information-dense view in the dashboard.

**Recent Alerts:** The last 3–5 threshold breaches with enough context to understand the issue without navigating to the full alerts view.

### 3.3 Vintage Analysis View

The star of the dashboard. Contains a pill selector to switch between four chart types:

**Grade Separation Chart:** For a selected vintage, shows one line per grade (A, B, C, D) plotting confirmed bad rate over MOB. Wide separation between lines = strong model discrimination. Lines converging = discrimination loss. This is the most important single chart in the dashboard.

**Cross-Vintage Trend:** For a selected metric (e.g., ever 60+ DPD) and fixed MOB, shows a grouped bar chart across vintages by grade. Reveals whether a specific grade is degrading over time across cohorts. This is where the Grade D drift from the walkthrough example becomes visible.

**Vintage Overlay:** Multiple vintages plotted on the same maturation axis for a single grade. Shows whether newer vintages are running hotter than older ones at the same MOB. Uses dashed lines for older vintages and solid lines for recent ones to emphasize the comparison.

**Floor / Ceiling:** For a selected vintage, shows confirmed bad rate (floor) and probable bad rate (ceiling) as an area chart over MOB. The gap between the two bands represents uncertainty. As the vintage matures, the bands converge until they meet at the final actual bad rate.

Each chart includes an insight callout at the bottom — a one-line interpretation of what the chart is showing (e.g., "Grade separation is clean and monotonic" or "Grade D ever-60+ rising across recent vintages").

### 3.4 Data Quality View

A feature-level table showing:

| Column | Content |
|---|---|
| Feature name | The monitored input feature |
| Null rate | Current null percentage |
| Baseline null rate | Expected null percentage from baseline |
| OOR rate | Out-of-range percentage |
| Cardinality | Distinct value count |
| Status | Badge: good / watch / warning |

Features with null rates significantly above baseline are highlighted. This view is most valuable during investigation — when the Drift view flags a feature, the DQ view helps determine whether the drift is caused by a data quality issue (missing values, schema change) vs. a genuine population shift.

### 3.5 Drift View

A feature-level table showing:

| Column | Content |
|---|---|
| Feature name | The monitored input feature |
| Current PSI | Population Stability Index against baseline |
| Baseline PSI | Historical PSI for context |
| Trend sparkline | 6-month PSI trend inline |
| Status | Badge: good / warning / critical |

PSI thresholds are color-coded: green below 0.10, amber 0.10–0.25, red above 0.25. The inline sparkline shows whether drift is stable, increasing, or spiking — a single elevated PSI is less concerning than a steadily climbing trend.

### 3.6 Alerts View

Full audit trail table with columns: date, vintage, grade, metric, MOB, observed value, baseline value, deviation percentage, severity badge. Sortable and filterable. This is the compliance and post-mortem view — "show me every time Mandos flagged an issue for this model."

---

## 4. Updated Library Integration Notes

### 4.1 Revised Decision Table

Based on the current Mandos codebase, the library decisions are:

| Library | Decision | Role in Mandos |
|---|---|---|
| **numpy / scipy / pandas** | **BUILD with** | Core compute for Tier 1 Primitives: PSI, CSI, DQ metrics. Also used for Tier 2 paired-array handling. |
| **scikit-learn** | **USE** | `roc_auc_score` for AUC. One-liner, production-grade. |
| **scipy** | **USE** | `ks_2samp` for KS statistic. Canonical implementation. |
| **NannyML** | **USE** | CBPE performance estimation. Non-trivial algorithm we should not maintain. |
| **datacompy** | **USE** (already integrated) | Powers `.compare_rows()` for row/account-level comparisons. Handles schema alignment, value-level diffs, and mismatch reporting. |
| **Evidently AI** | **SKIP** for production | Requires full DataFrames. Incompatible with Primitives architecture. |
| **ydata-profiling** | **SKIP** for production | Useful for ad-hoc exploration, not automated monitoring. |

### 4.2 datacompy: Corrected Assessment

The earlier design document listed datacompy as "SKIP — solves a different problem." This was incorrect. Mandos has already integrated datacompy via the `.compare_rows()` method, which provides row-level and account-level comparison capabilities that complement the aggregate Primitives approach.

Where Primitives handle aggregate monitoring (portfolio-level and grade-level metrics), `.compare_rows()` handles a different class of questions:

- **Prediction reconciliation:** Do the scores in the serving pipeline match the scores in the monitoring pipeline? Row-level comparison catches silent data pipeline divergence.
- **Replay validation:** When rerunning a model on historical data, does the output match the original? Account-level comparison validates reproducibility.
- **Data pipeline integrity:** Has the feature table changed between runs? Column-level schema comparison plus value-level diff catches upstream ETL issues.

These are data quality and integrity checks that operate at a different level than PSI/CSI drift detection. datacompy's strength is in precise, row-level "these two datasets should be identical — show me where they differ" analysis, which is complementary to Mandos's aggregate statistical monitoring.

### 4.3 How the Libraries Map to Dashboard Views

| Dashboard View | Libraries Used |
|---|---|
| Overview (health cards, vintages table) | Tier 1 Primitives (numpy) + Snowflake aggregation |
| Vintage Analysis (grade separation, trends, overlays) | Tier 1 (severity rates from Snowflake) + Tier 2 (sklearn AUC, scipy KS) |
| Data Quality | Tier 1 Primitives (numpy) + datacompy for row-level reconciliation |
| Drift | Tier 1 Primitives (numpy PSI/CSI) + NannyML CBPE for early months |
| Alerts | Threshold evaluation on Tier 1 + Tier 2 results (no external library) |

---

## 5. Implementation Notes

### 5.1 Technology Stack

| Component | Technology |
|---|---|
| Dashboard framework | Streamlit |
| Hosting | Streamlit on Snowflake |
| Data source | `mandos.snapshots` table in Snowflake (Mandos output) |
| Charting | Streamlit native charts / Plotly (for interactive vintage analysis) |
| Mandos dependency | Mandos Python library (installed as package in the Streamlit app) |

### 5.2 Dashboard Does Not Own Computation

The dashboard is a read-only visualization layer. It queries the `mandos.snapshots` table and renders results. It does not compute metrics, run data joins, or manage scheduling. The only write action it may expose is a button to trigger an ad-hoc Mandos run — but the scheduled monthly runs operate independently of the dashboard.

### 5.3 Responsive Considerations

The active vintages table and alert history table can be wide. Both should support horizontal scrolling on smaller screens. The vintage analysis charts should be responsive via container-width sizing. The sidebar collapses to a top nav on narrow viewports if needed, though the primary use case is desktop (analysts at workstations).
