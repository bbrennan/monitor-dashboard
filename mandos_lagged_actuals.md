# Mandos: Model Monitoring with Lagged Actuals

**Vintage-Based Monitoring, Cumulative Severity Tiers & Grade-Level Segmentation**

Reference Implementation: Zuul Originations Model | With Generalization to Automotive Credit Risk Model Portfolio

*Prepared by: ML Engineering, Risk Organization*
*Classification: Internal | Version 2.0 · April 2026*

---

## 1. Executive Summary

Credit risk models in automotive financial services universally depend on target variables that require extended observation windows before ground truth becomes available. The Zuul originations model, for example, defines its bad flag based on account behavior observed over a 24-month window. This creates a structural gap between the moment a prediction is generated at origination and the moment that prediction can be validated against actual outcomes.

This document defines how Mandos — our model-agnostic data quality and model monitoring library — handles this gap. The strategy rests on three pillars:

- **Cumulative severity tiers:** Rather than computing fixed-window proxy labels at predetermined checkpoints, Mandos tracks monotonically increasing delinquency counters (ever 30+ DPD, ever 60+ DPD, ever 90+ DPD, ever 120+ DPD) on a monthly cadence for each vintage. Every month adds real information. Accounts that cross certain thresholds become confirmed bads before the observation window closes.

- **Grade-level segmentation:** Severity tiers are computed not only at the portfolio level but at the origination grade level (A, B, C, D, X). This reveals whether the model's ranking is holding — grade D accounts should deteriorate faster than grade A accounts. When that separation collapses, the model's discrimination is failing.

- **Config-driven onboarding:** A single YAML configuration file defines everything Mandos needs to monitor a model: source tables, bad flag definition, severity tiers, segmentation column, and alert thresholds. No custom pipeline code is required.

The framework generalizes across the automotive credit risk model portfolio. The Zuul originations model serves as the reference implementation, but the architecture applies identically to any model with lagged actuals.

---

## 2. Why Mandos? Platform Comparison

### 2.1 The Landscape

Our infrastructure already includes two platforms with native model monitoring capabilities: **AWS SageMaker Model Monitor** (where we develop models) and **Snowflake ML Observability** (where all our data lives). Both offer data quality monitoring, drift detection, and model quality tracking. A reasonable question is: why build and maintain Mandos instead of using these services?

The answer is that neither platform was designed for the specific problem that dominates our model portfolio — **monitoring models with long-lag actuals in a credit risk context, where ground truth arrives incrementally over months or years.** Both platforms assume a fundamentally different monitoring paradigm.

### 2.2 AWS SageMaker Model Monitor

SageMaker Model Monitor provides four monitoring dimensions: data quality, model quality, bias drift, and feature attribution drift. It is tightly integrated with SageMaker endpoints and batch transform jobs, captures inference inputs and outputs automatically, and can detect feature distribution shifts against a computed baseline.

**Where it works well:** SageMaker Model Monitor excels at real-time inference monitoring where ground truth is available quickly — fraud detection, recommendation systems, classification tasks where labels arrive within hours or days. Its data quality monitoring (schema validation, statistical drift detection via Deequ) is robust and production-grade.

**Where it falls short for our use case:**

- **Ground truth model:** SageMaker expects you to upload ground truth labels to S3, matched to predictions via an inference ID. It supports time offsets to account for delayed labels (e.g., `-P8D` for a week of lag). But this mechanism was designed for delays of hours to days — not 18 to 24 months. There is no native concept of a vintage, a maturation window, or ground truth that arrives incrementally across severity tiers.

- **No vintage cohort tracking:** SageMaker monitors the overall prediction population against a baseline. It does not group predictions into origination cohorts and track their maturation trajectories independently. There is no built-in way to ask "how is vintage 2024-10 performing at month 12 relative to vintage 2024-07 at month 12?"

- **No cumulative severity tiers:** SageMaker has no concept of monotonically increasing proxy labels that converge toward a final bad flag. It computes model quality metrics when ground truth is available — period. The intermediate states (confirmed vs. probable bads, partial maturation) are not representable in its framework.

- **No grade-level segmentation for discrimination tracking:** SageMaker can detect data drift, but it does not natively track whether a model's rank-ordering is holding across business decision segments (grades). The grade separation analysis that catches discrimination loss is not a built-in capability.

- **Infrastructure coupling:** SageMaker Model Monitor is designed around SageMaker-hosted endpoints and S3-based data capture. Our models are deployed on EKS, and our data lives in Snowflake. Integrating SageMaker Model Monitor would require piping data from Snowflake to S3 for monitoring, then piping results somewhere visible — adding complexity without adding capability.

### 2.3 Snowflake ML Observability

Snowflake's ML Observability feature, integrated with the Snowflake Model Registry, allows monitoring of performance, drift, and data volume for models logged in the registry. It stores inference data in monitoring logs, supports segment-based analysis via string categorical columns, and provides a dashboard in Snowsight.

**Where it works well:** Snowflake ML Observability is compelling when models are trained and registered within Snowflake's ML ecosystem, inference runs on Snowflake compute, and ground truth is available in a straightforward prediction-vs-label format. It supports daily aggregation windows and segment columns for sliced analysis.

**Where it falls short for our use case:**

- **Registry coupling:** Snowflake ML Observability requires models to be logged in the Snowflake Model Registry. Our models are developed in SageMaker and deployed on EKS. While Snowflake's documentation notes that externally-trained models can be registered, the monitoring workflow is optimized for models running inference within Snowflake.

- **Same ground truth gap:** Like SageMaker, Snowflake's monitoring assumes ground truth labels exist and can be matched to predictions. The monitoring log expects a "ground truth label" column. There is no native concept of cumulative severity tiers, partial maturation, confirmed vs. probable bads, or vintage-level cohort tracking across a multi-year observation window.

- **Binary classification limitation:** Snowflake ML Observability currently supports regression and binary classification models. While Zuul is binary classification, the monitoring logic we need goes beyond standard binary classification metrics — it requires domain-specific concepts like vintage maturation curves and grade separation tracking that are not part of the standard ML Observability feature set.

- **Aggregation window granularity:** Snowflake ML Observability aggregates at a minimum of one-day windows. Our monitoring needs are organized by vintage × MOB × grade, which is a fundamentally different aggregation grain than time-windowed inference batches.

### 2.4 What Mandos Provides That Neither Platform Does

| Capability | SageMaker Model Monitor | Snowflake ML Observability | Mandos |
|---|---|---|---|
| Data quality monitoring | ✓ Built-in | ✓ Built-in | ✓ Built-in |
| Feature drift detection (PSI/CSI) | ✓ Built-in | ✓ Built-in | ✓ Built-in |
| Ground truth with short lag (hours/days) | ✓ Designed for this | ✓ Designed for this | ✓ Supported |
| Ground truth with long lag (months/years) | ✗ Not designed for this | ✗ Not designed for this | **✓ Core design** |
| Vintage cohort tracking | ✗ | ✗ | **✓** |
| Cumulative severity tiers | ✗ | ✗ | **✓** |
| Confirmed vs. probable bad separation | ✗ | ✗ | **✓** |
| Maturation curves per vintage | ✗ | ✗ | **✓** |
| Grade-level segmentation with discrimination tracking | ✗ | Partial (segment columns) | **✓** |
| Cross-vintage trend analysis at fixed MOB | ✗ | ✗ | **✓** |
| CBPE for pre-actuals estimation | ✗ | ✗ | **✓** |
| Config-driven model onboarding | ✗ (code-based) | ✗ (code-based) | **✓ YAML** |
| Snowflake-native storage | ✗ (S3) | ✓ | **✓** |
| Works with EKS-deployed models | Requires data piping | Requires registry import | **✓ Direct** |

### 2.5 How They Complement Each Other

Mandos does not replace SageMaker or Snowflake for everything. The recommended architecture uses each tool for what it does best:

- **SageMaker:** Model development, training, experiment tracking, hyperparameter tuning. We continue using SageMaker Studio and SageMaker Processing for model building.
- **EKS:** Model serving and inference in production.
- **Snowflake:** All data storage — features, predictions, account performance history, and Mandos monitoring snapshots. Snowflake Tasks for scheduling Mandos batch runs.
- **Mandos:** The monitoring layer purpose-built for credit risk models with lagged actuals. It reads from Snowflake, computes metrics, and writes snapshots back to Snowflake. The Mandos Dashboard (Streamlit on Snowflake) visualizes results.

This is not a redundancy — it is a division of labor. SageMaker builds models. EKS serves them. Snowflake stores everything. Mandos monitors the things that the platform tools were not designed to monitor.

### 2.6 Build vs. Buy Justification

The decision to build Mandos rather than adopt a third-party monitoring tool (NannyML, Evidently AI, Arize, etc.) rests on three factors:

- **Domain specificity:** The vintage × MOB × grade monitoring pattern is deeply specific to credit risk. Generic ML monitoring tools share the same ground truth assumptions as SageMaker and Snowflake — they expect labels to exist. Tools like NannyML offer CBPE (which Mandos also supports), but none offer the full cumulative severity tier framework with confirmed/probable bad separation.

- **Infrastructure alignment:** Our data lives in Snowflake. Third-party tools typically require data export to their platform, adding latency, cost, and a data governance surface area. Mandos runs entirely within our Snowflake environment.

- **Control and extensibility:** As an internal library, Mandos can be extended to support new model types, new severity tier definitions, and new business logic without waiting on a vendor roadmap. The YAML config pattern makes this extension trivially cheap.

---

## 3. The Lagged Actuals Problem

### 3.1 Two Monitoring Streams

Monitoring models with lagged actuals requires operating two parallel streams. The first — input-side monitoring — is available immediately at scoring time and covers feature drift (PSI, CSI), data quality checks, and score distribution stability. The second — output-side monitoring — measures actual model discrimination and calibration but is only available as the observation window matures. The challenge is bridging the gap between these two streams with increasingly reliable performance signals.

### 3.2 Why Point-in-Time Snapshots Are Insufficient

A naive approach would compute a single pass/fail performance check once the observation window closes. This is inadequate for two reasons. First, 24 months of blindness is operationally unacceptable for model risk management. Second, a single end-of-window check discards the rich trajectory information that accumulates during the observation period — information that reveals how quickly a vintage is deteriorating relative to historical norms and, critically, whether the model's ranking of accounts is still holding.

---

## 4. Reference Model: Zuul Originations

### 4.1 Bad Flag Definition

The Zuul originations model defines an account as "bad" if any of the following conditions are met within the 24-month observation window:

- **Charge-off:** The account has been charged off at or before month 24.
- **Point-in-time delinquency:** The account is 90+ days past due at the month 24 evaluation point.
- **Peak delinquency:** The account has ever exceeded 120 days past due at any point during the observation window.

> **Critical observation:** The third leg — ever 120+ DPD — has no time boundary. An account that crosses 120 DPD at month 8 has already triggered the bad flag. This is not a proxy; it is a confirmed actual.

### 4.2 Grade Structure

At origination, Zuul assigns each application a grade based on bands of the model's predicted probability of default:

| Grade | Risk Level | Decision | Expected Behavior |
|---|---|---|---|
| A | Lowest risk | Auto-approve | Minimal delinquency; very low bad rate |
| B | Low-moderate risk | Approve with standard terms | Some early delinquency; low bad rate |
| C | Moderate risk | Approve with conditions | Moderate delinquency; meaningful bad rate |
| D | High risk | Approve with restrictions or manual review | Elevated delinquency; highest bad rate among approved |
| X | Unacceptable risk | Auto-decline | Not originated; monitored for policy validation only |

These grades are the natural segmentation axis for monitoring. They represent the model's actual decision boundaries. If grade C starts behaving like grade D historically behaved, that is a direct signal that either the model's ranking has shifted or the population within that band has changed.

---

## 5. Cumulative Severity Tiers

### 5.1 Why Not Fixed-Window Proxies?

A traditional proxy approach defines fixed-window labels such as "ever 60+ DPD within the first 6 months." This has a fundamental limitation: an account that first hits 60+ DPD at month 8 is invisible to the 6-month proxy. The label is computed once at month 6 and never updated. Information is discarded.

Mandos instead tracks cumulative severity counters that are re-evaluated every month. Because these counters can only increase — an account that has ever been 60+ DPD can never become "never 60+ DPD" — every monthly snapshot adds real information.

### 5.2 Tier Definitions

| Tier | Definition | Behavior | Classification |
|---|---|---|---|
| Ever 30+ DPD | Account has been 30+ days past due at any point through current month | Monotonic ↑ | Early signal |
| Ever 60+ DPD | Account has been 60+ days past due at any point through current month | Monotonic ↑ | Moderate signal |
| Ever 90+ DPD | Account has been 90+ days past due at any point through current month | Monotonic ↑ | Probable bad |
| Ever 120+ DPD | Account has exceeded 120 days past due at any point. Directly triggers the Zuul bad flag. | Monotonic ↑ | **Confirmed bad** |
| Ever Charge-off | Account has been charged off at any point through current month | Monotonic ↑ | **Confirmed bad** |

### 5.3 Confirmed vs. Probable vs. Not Yet Bad

At any given month during the observation window, each account falls into one of three categories:

- **Confirmed bad:** The account has already tripped a terminal condition — ever 120+ DPD or charged off. This is ground truth. This count can only increase.
- **Probable bad:** The account shows severe distress (ever 90+ DPD) but has not yet crossed the 120 DPD threshold or charged off. Highly likely to convert, but could theoretically cure.
- **Not yet bad:** No delinquency or mild delinquency. Most will remain good, but some will deteriorate before month 24.

This gives Mandos a performance floor (confirmed bads) and an estimated ceiling (confirmed + probable) at every monthly checkpoint. The gap narrows to zero at month 24.

---

## 6. Grade-Level Segmentation

### 6.1 What Grade-Level Curves Reveal

The overall severity curve for a vintage tells you how the portfolio is performing. But it does not tell you whether the model's ranking is working. To answer that question, you split the curves by origination grade.

If the model is discriminating correctly, the severity curves should separate cleanly by grade: grade D accounts should deteriorate fastest, grade A slowest, with others in order between them. The magnitude of separation is a real-time proxy for model discrimination (analogous to AUC) observable months before the window closes.

Three distinct failure modes become visible at the grade level:

**Failure Mode 1: Discrimination Loss.** Grade C's severity curve converges with grade B's — or crosses above it. The model can no longer distinguish between these risk segments.

**Failure Mode 2: Population Shift (Calibration).** All grade curves shift upward together while maintaining relative separation. The model's ranking still works, but its absolute probabilities are too low. The entire population got riskier. Recalibrate, don't rebuild.

**Failure Mode 3: Segment-Specific Data Issue.** One grade's curve diverges sharply while others remain normal. Typically points to a data issue affecting a specific region of the feature space.

### 6.2 Example: Grade-Level Severity at MOB 12 for Vintage 2025-01

| Grade | Accounts | Ever 30+ | Ever 60+ | Ever 90+ | Ever 120+ | Charge-off | Confirmed |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 4,200 | 1.2% | 0.4% | 0.1% | 0.0% | 0.0% | 0.0% |
| B | 3,800 | 3.1% | 1.5% | 0.7% | 0.3% | 0.1% | 0.4% |
| C | 2,500 | 7.8% | 4.2% | 2.4% | 1.2% | 0.5% | 1.7% |
| D | 1,200 | 14.5% | 9.1% | 5.8% | 3.5% | 1.8% | 5.3% |
| X | (declined) | — | — | — | — | — | — |
| **Portfolio** | **11,700** | **4.8%** | **2.9%** | **1.7%** | **0.9%** | **0.5%** | **1.4%** |

**Reading this table:** Grade D accounts are confirming bad at 5.3% by month 12, while grade A is at 0.0%. This clean monotonic separation (A < B < C < D across every tier) indicates the model's ranking is holding. If grade C's "Ever 60+" rate were 9.5% instead of 4.2% — approaching grade D's 9.1% — that would be a discrimination collapse signal.

### 6.3 Example: Cross-Vintage Comparison at MOB 12 by Grade

Ever 60+ DPD rate at MOB 12 across four vintages:

| Vintage | Grade A | Grade B | Grade C | Grade D | Portfolio |
|---|---:|---:|---:|---:|---:|
| 2024-04 | 0.3% | 1.4% | 3.8% | 8.2% | 2.6% |
| 2024-07 | 0.4% | 1.5% | 3.9% | 8.5% | 2.7% |
| 2024-10 | 0.3% | 1.6% | 4.0% | 8.7% | 2.8% |
| **2025-01** | **0.4%** | **1.5%** | **4.2%** | **9.1%** ⚠️ | **2.9%** |

**Reading this table:** Grades A, B, and C are stable. Grade D is drifting upward — from 8.2% to 9.1% over three quarters. The portfolio-level number (2.6% → 2.9%) would not trigger an alert on its own, but the grade-level view reveals degradation concentrated in the highest-risk approved segment.

### 6.4 Example: Maturation Curve by Grade for Vintage 2025-01

Confirmed bad rate (ever 120+ DPD or charge-off) over time:

| MOB | Grade A | Grade B | Grade C | Grade D | Portfolio |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.0% | 0.0% | 0.1% | 0.4% | 0.1% |
| 6 | 0.0% | 0.1% | 0.5% | 1.8% | 0.4% |
| 9 | 0.0% | 0.2% | 1.0% | 3.5% | 0.9% |
| 12 | 0.0% | 0.4% | 1.7% | 5.3% | 1.4% |
| 15 | 0.1% | 0.5% | 2.3% | 6.8% | 1.9% |
| 18 | 0.1% | 0.7% | 2.9% | 8.0% | 2.3% |
| 21 | 0.1% | 0.8% | 3.2% | 8.7% | 2.6% |
| 24 | 0.1% | 0.9% | 3.5% | 9.2% | 2.8% |

**Reading this table:** By month 12, grade D is at 5.3% confirmed — meaning 58% of its final bad population (5.3 / 9.2) is already locked in as ground truth. The floor can only rise. This is why monthly monitoring is valuable: you watch the answer converge toward its final value in real time.

### 6.5 Interpreting Grade Separation Over Time

The gap between grade curves at any given MOB is a direct measure of model discrimination. A practical metric: compute the ratio of grade D's confirmed bad rate to grade A's. If this ratio historically exceeds 50:1 and a new vintage shows it dropping to 15:1, the model's discrimination in the tails is collapsing.

---

## 7. Vintage-Based Monitoring Strategy

### 7.1 What Is a Vintage?

A vintage is a cohort of accounts grouped by origination period — typically calendar month. All accounts originated in January 2025 constitute vintage 2025-01.

### 7.2 Snapshot Grain

Each Mandos snapshot is keyed on three dimensions:

- **Vintage:** The origination cohort (e.g., 2025-01)
- **MOB (Months on Book):** How many months have elapsed since origination
- **Grade:** The origination grade (A, B, C, D, X), plus a portfolio-level aggregate row

Vintage 2025-01 accumulates one set of rows per month from MOB 1 through MOB 24. Each set contains one row per grade plus one portfolio aggregate, yielding six rows per monthly snapshot and up to 144 total rows over the vintage's lifetime.

### 7.3 Monthly Snapshot Content

| Metric Category | Contents |
|---|---|
| Data Quality | Null rates, out-of-range counts, cardinality shifts on scoring features for this grade's population |
| Drift | PSI and CSI against baseline for each monitored feature, segmented by grade |
| Cumulative Severity | Rates for each tier (ever 30+, 60+, 90+, 120+ DPD; charge-off) as of current MOB |
| Confirmed Bad Rate | Percentage that have triggered the bad flag (ever 120+ DPD or charge-off). Performance floor. |
| Probable Bad Rate | Confirmed + probable bads (ever 90+ DPD). Performance ceiling. |
| Performance Metrics | AUC, KS, Gini at portfolio level using confirmed + probable bads as label |
| CBPE Estimate | Confidence-Based Performance Estimation. Most valuable in early months. |

### 7.4 Cross-Vintage Trend Analysis

The most powerful model-level health signal comes from comparing vintages at the same MOB, within the same grade. Plotting grade C's confirmed bad rate at MOB 12 across vintages reveals whether that specific risk segment is getting worse over time. This is far more diagnostic than a portfolio-level trend, which can mask grade-specific degradation.

> **Key principle:** The trend across vintages at a fixed MOB and fixed grade is the most granular model health signal. Portfolio-level trends confirm systemic issues. Grade-level trends pinpoint where the model is failing.

---

## 8. Data Ingestion Architecture

### 8.1 Data Flow

The ingestion process runs on a monthly batch cadence:

1. Identify all active vintages: originated but not yet past the maturation window.
2. For each active vintage, join scored predictions to current account-level performance data.
3. Compute cumulative severity tier flags for each account as of current MOB.
4. Classify each account as confirmed bad, probable bad, or not yet bad.
5. Aggregate by vintage, MOB, and origination grade.
6. Pass aggregated results to Mandos for snapshot persistence.

### 8.2 Account-Level Joins Stay Upstream

The join between predictions and account performance occurs at the account level in Snowflake SQL. Mandos itself operates on the aggregated output. Account-level detail is consumed in the aggregation query and is not stored within Mandos.

> Mandos is not an account-level data store. Account-level joins happen upstream in Snowflake. Mandos ingests vintage × MOB × grade aggregated results.

### 8.3 Snowflake Query Pattern

```sql
WITH scored AS (
  SELECT account_id, origination_month, pd_score,
         origination_grade
  FROM {prediction_table}
  WHERE origination_month = :vintage
),
perf AS (
  SELECT account_id,
    MAX(CASE WHEN max_dpd >= 30  THEN 1 ELSE 0 END) AS ever_30_dpd,
    MAX(CASE WHEN max_dpd >= 60  THEN 1 ELSE 0 END) AS ever_60_dpd,
    MAX(CASE WHEN max_dpd >= 90  THEN 1 ELSE 0 END) AS ever_90_dpd,
    MAX(CASE WHEN max_dpd > 120  THEN 1 ELSE 0 END) AS ever_120_dpd,
    MAX(CASE WHEN chargeoff = 1  THEN 1 ELSE 0 END) AS ever_chargeoff
  FROM {actuals_table}
  WHERE months_on_book <= :current_mob
  GROUP BY account_id
),
classified AS (
  SELECT s.origination_month AS vintage,
         :current_mob AS mob,
         s.origination_grade AS grade,
         s.pd_score,
         p.ever_30_dpd, p.ever_60_dpd,
         p.ever_90_dpd, p.ever_120_dpd,
         p.ever_chargeoff,
         CASE WHEN p.ever_120_dpd = 1
                OR p.ever_chargeoff = 1
              THEN 1 ELSE 0 END AS confirmed_bad,
         CASE WHEN p.ever_90_dpd = 1
              THEN 1 ELSE 0 END AS probable_bad
  FROM scored s
  LEFT JOIN perf p ON s.account_id = p.account_id
)
SELECT vintage, mob, grade,
  COUNT(*)                          AS account_count,
  AVG(ever_30_dpd)                  AS ever_30_rate,
  AVG(ever_60_dpd)                  AS ever_60_rate,
  AVG(ever_90_dpd)                  AS ever_90_rate,
  AVG(ever_120_dpd)                 AS ever_120_rate,
  AVG(ever_chargeoff)               AS chargeoff_rate,
  AVG(confirmed_bad)                AS confirmed_bad_rate,
  AVG(GREATEST(confirmed_bad,
               probable_bad))       AS probable_bad_rate
FROM classified
GROUP BY GROUPING SETS (
  (vintage, mob, grade),
  (vintage, mob)          -- portfolio-level aggregate
)
ORDER BY vintage, mob, grade;
```

The GROUPING SETS clause produces both grade-level and portfolio-level rows in a single pass.

---

## 9. Config-Driven Model Onboarding

### 9.1 Design Philosophy

Users onboard a new model by providing a single YAML configuration file. No custom pipeline code is required. Mandos reads the config, generates queries, computes metrics, and persists snapshots.

### 9.2 Zuul Configuration

```yaml
# mandos_config/zuul_originations.yaml

model_name: zuul_originations
model_version: "2.1"
owner: credit_risk_team

# Source tables
prediction_table: RISK_DB.SCORES.ZUUL_PREDICTIONS
actuals_table: RISK_DB.PERFORMANCE.ACCOUNT_MONTHLY

# Keys and columns
join_key: account_id
vintage_column: origination_month
score_column: pd_score

# Grade segmentation
segmentation_column: origination_grade
segmentation_values: [A, B, C, D, X]
segmentation_exclude_from_perf: [X]  # Declined; no actuals

# Bad flag definition
maturation_months: 24
bad_flag:
  logic: OR
  conditions:
    - type: chargeoff_at_maturity
      column: chargeoff_flag
    - type: point_in_time_dpd
      column: dpd_days
      threshold: 90
      at_month: 24
    - type: ever_exceeds
      column: dpd_days
      threshold: 120

# Cumulative severity tiers
severity_tiers:
  - name: ever_30_dpd
    column: dpd_days
    threshold: 30
    type: ever_gte
  - name: ever_60_dpd
    column: dpd_days
    threshold: 60
    type: ever_gte
  - name: ever_90_dpd
    column: dpd_days
    threshold: 90
    type: ever_gte
    probable_bad: true
  - name: ever_120_dpd
    column: dpd_days
    threshold: 120
    type: ever_gt
    confirmed_bad: true
  - name: ever_chargeoff
    column: chargeoff_flag
    threshold: 1
    type: ever_gte
    confirmed_bad: true

# Monitoring
schedule: monthly
metrics:
  drift: [psi, csi]
  data_quality: [null_rate, out_of_range, cardinality]
  performance: [auc, ks, gini, cbpe]

# Thresholds
thresholds:
  psi_warning: 0.10
  psi_critical: 0.25
  confirmed_bad_rate_deviation_pct: 0.20
  tier_rate_deviation_pct: 0.25
  grade_separation_collapse_pct: 0.50
  min_vintage_size: 500
```

### 9.3 Key Config Features

- **`segmentation_column` and `segmentation_values`:** Computes all metrics per-grade with GROUPING SETS for both grade-level and portfolio-level aggregation.
- **`segmentation_exclude_from_perf`:** Grade X accounts are declined — excluded from performance metrics but tracked for DQ and drift (policy validation).
- **`probable_bad` and `confirmed_bad` flags:** Severity tiers marked `confirmed_bad` contribute to the performance floor. Tiers marked `probable_bad` contribute to the ceiling.
- **`grade_separation_collapse_pct`:** Alerts when the ratio of confirmed bad rates between adjacent grades narrows beyond threshold, indicating discrimination loss.

### 9.4 Onboarding Workflow

1. Model owner creates the YAML config file.
2. File is placed in `mandos_config/`.
3. Mandos validates: table existence, column presence, severity tier consistency, segmentation column presence, at least one `confirmed_bad` tier.
4. On next scheduled run, Mandos discovers the new model and begins monitoring.
5. Baseline computed from most recent fully matured vintage, segmented by grade.

---

## 10. Snapshot Storage Schema

### 10.1 Table Design

| Column | Type | Description |
|---|---|---|
| `model_name` | VARCHAR | Identifier from config |
| `snapshot_date` | DATE | Date the snapshot was computed |
| `vintage` | VARCHAR | Origination cohort (e.g., 2025-01) |
| `mob` | INT | Months on book at snapshot time |
| `grade` | VARCHAR | Origination grade (A/B/C/D/X) or NULL for portfolio aggregate |
| `account_count` | INT | Number of accounts in this vintage × grade segment |
| `dq_metrics` | ARRAY | Data quality metric results |
| `drift_metrics` | ARRAY | Drift metrics (PSI, CSI per feature) |
| `severity_tiers` | OBJECT | Rates for each cumulative severity tier |
| `confirmed_bad_rate` | FLOAT | Floor: accounts that have triggered the actual bad flag |
| `probable_bad_rate` | FLOAT | Ceiling: confirmed + probable bads |
| `perf_metrics` | ARRAY | AUC, KS, Gini (portfolio-level rows only) |
| `cbpe_estimate` | FLOAT | CBPE-estimated performance |
| `is_final` | BOOLEAN | True if mob = maturation_months |
| `alert_flags` | ARRAY | Threshold breaches detected |

### 10.2 Query Patterns

**Grade-level trend at fixed MOB:**

```sql
SELECT vintage, confirmed_bad_rate, severity_tiers
FROM mandos.snapshots
WHERE model_name = 'zuul_originations'
  AND mob = 12 AND grade = 'D'
ORDER BY vintage;
```

**Grade separation check:**

```sql
SELECT grade, confirmed_bad_rate, probable_bad_rate, severity_tiers
FROM mandos.snapshots
WHERE model_name = 'zuul_originations'
  AND vintage = '2025-01' AND mob = 12
  AND grade IS NOT NULL
ORDER BY grade;
```

**Maturation curve for a single vintage and grade:**

```sql
SELECT mob, confirmed_bad_rate, probable_bad_rate, severity_tiers
FROM mandos.snapshots
WHERE model_name = 'zuul_originations'
  AND vintage = '2025-01' AND grade = 'D'
ORDER BY mob;
```

**Portfolio-level summary:**

```sql
SELECT vintage, confirmed_bad_rate, perf_metrics
FROM mandos.snapshots
WHERE model_name = 'zuul_originations'
  AND mob = 12 AND grade IS NULL
ORDER BY vintage;
```

---

## 11. Automation & Scheduling

### 11.1 Architecture Boundaries

| Component | Owns | Does Not Own |
|---|---|---|
| Snowflake Tasks | Scheduling, triggering monthly batch runs | Business logic, metric computation, visualization |
| Mandos (Library) | Config parsing, query generation, metric computation, snapshot persistence, grade-level alerting | Scheduling, visualization, account-level storage |
| Dashboard (Streamlit) | Visualization: grade curves, maturation curves, cross-vintage trends, alert display | Metric computation, data joins, scheduling |

### 11.2 Monthly Run Logic

On each scheduled run, the Mandos batch process iterates over all registered model configs. For each model, it identifies all active vintages and computes a new snapshot at the current MOB. Each snapshot includes one row per grade plus one portfolio aggregate row. Fully matured vintages receive a final snapshot with `is_final = true` and are retired from active monitoring.

### 11.3 The Dashboard Is a Read Layer

The Streamlit dashboard queries the snapshots table and renders visualizations. It does not own computation, orchestration, or scheduling. It may expose a button for ad-hoc runs, but scheduled runs operate independently.

---

## 12. End-to-End Walkthrough: Detecting Grade-Level Degradation

### 12.1 Onboarding (Month 0)

The credit risk team deploys zuul_originations and creates the YAML config. Mandos validates and computes a baseline from the most recent fully matured vintage (2023-06). Baseline confirmed bad rates at maturity: A = 0.1%, B = 0.9%, C = 3.5%, D = 9.0%, portfolio = 2.8%.

### 12.2 Months 1–3 (Early Signal)

Vintages 2025-01 and 2025-02 begin accumulating snapshots. CBPE estimates performance at 0.77. PSI is below 0.05 across all grades. By month 3, the ever 30+ DPD tier shows:

| | Grade A | Grade B | Grade C | Grade D | Portfolio |
|---|---:|---:|---:|---:|---:|
| Historical avg MOB 3 | 0.3% | 1.0% | 2.8% | 5.5% | 1.8% |
| Vintage 2025-01 | 0.3% | 1.1% | 2.9% | **6.2%** | 1.9% |

Grades A through C are within range. Grade D is elevated at 6.2% vs. 5.5% — 13% deviation. Below the 25% threshold. Mandos logs it.

### 12.3 Month 8 (Divergence Confirmed)

The grade-level view reveals a clear pattern:

| Ever 60+ DPD | Grade A | Grade B | Grade C | Grade D | Portfolio |
|---|---:|---:|---:|---:|---:|
| Historical avg MOB 8 | 0.3% | 1.2% | 3.5% | 7.8% | 2.4% |
| Vintage 2025-01 | 0.3% | 1.3% | 3.7% | **9.6%** 🔴 | 2.8% |
| Deviation | +0.0% | +0.1% | +0.2% | **+1.8%** 🔴 | +0.4% |

Grades A, B, C are within norms. Grade D has deviated by 23%, exceeding the 20% threshold. Mandos fires a warning alert. The portfolio-level deviation (17%) would not have triggered. **Grade-level monitoring caught what portfolio-level monitoring would have missed.**

### 12.4 Investigation

PSI on the debt-to-income ratio is 0.22 for grade D originations but only 0.04 for other grades. Root cause: a downstream system began rounding DTI values for high-risk applicants, causing underestimation of risk for borderline-decline accounts narrowly approved as grade D.

### 12.5 Month 24 (Actuals Confirm)

| Final Bad Rate | Grade A | Grade B | Grade C | Grade D | Portfolio |
|---|---:|---:|---:|---:|---:|
| Baseline | 0.1% | 0.9% | 3.5% | 9.0% | 2.8% |
| Vintage 2025-01 | 0.1% | 0.9% | 3.7% | **12.1%** 🔴 | 3.2% |

Grade D's actual bad rate is 12.1% vs. 9.0% baseline — a 34% deterioration. Grades A and B are on baseline. The grade-level view confirms the problem was isolated to the highest-risk approved segment, validating the alert Mandos raised 16 months earlier.

---

## 13. Dashboard Integration

### 13.1 Recommended Views

- **Grade Separation Chart:** For a selected vintage and severity tier, one line per grade across MOBs. Lines converging = discrimination loss.
- **Cross-Vintage Trend by Grade:** For a selected grade and MOB, confirmed bad rate across vintages. Primary per-segment degradation signal.
- **Vintage Maturation Curve:** For a selected vintage, confirmed bad rate for all grades across MOBs.
- **Vintage Overlay:** Multiple vintages overlaid on the same maturation axis for a single grade. Immediate detection of anomalous cohorts.
- **Model Health Summary:** Latest metric per model, color-coded by alert status.
- **Alert History:** Timeline of threshold breaches with drill-down to vintage, grade, and metric.

---

## 14. Generalization to the Model Portfolio

### 14.1 Why the Framework Generalizes

The architecture separates three concerns: what makes an account bad (bad_flag config), what early signals to track (severity_tiers config), and how to segment the population (segmentation_column config). A new model requires only a new YAML file.

### 14.2 Portfolio Examples

| Model | Window | Bad Flag | Severity Tiers | Segmentation |
|---|---|---|---|---|
| Zuul (Originations) | 24 mo | Charge-off, 90+ DPD at M24, ever 120+ DPD | Ever 30/60/90/120+ DPD; charge-off | Origination grade (A–D, X) |
| Loss Forecasting | 12 mo | Net loss exceeds threshold | Cumulative net loss at monthly intervals | Loan-to-value band |
| Collections Propensity | 6 mo | Account cures within 6 months of treatment | Payment count; partial payment; promise-to-pay | Treatment strategy |
| Early Payment Default | 6 mo | 60+ DPD within first 6 payments | Ever 30+ DPD; missed 1st payment; missed any of 1st 3 | Channel (dealer vs. direct) |
| Residual Value | 36–48 mo | Actual residual vs. predicted at lease return | Market index delta at quarterly intervals | Vehicle class |

Each model has a different target, window, tiers, and segmentation axis. The monitoring structure is identical. The only thing that changes is the config file.

### 14.3 Non-Delinquency Models

Not all models use DPD-based tiers. A residual value model's tiers might track cumulative market index deviation. A collections model's tiers might track cumulative payment activity. The `severity_tiers` config block requires only a column, a threshold, and a comparison operator — flexible enough for any monotonically trackable signal.

---

## 15. Appendix: Design Decisions

| Decision | Rationale | Alternative Considered |
|---|---|---|
| Cumulative tiers, not fixed-window proxies | Fixed-window proxies discard information. Cumulative tiers grow monotonically; every snapshot adds signal. | Compute proxies at predetermined checkpoints only |
| Monthly monitoring for all active vintages | New accounts cross thresholds every month. Monthly snapshots capture the full trajectory. | Monitor only at checkpoint horizons |
| Confirmed vs. probable bad separation | Floor and ceiling at every checkpoint; gap narrows over time. | Single composite label |
| Grade-level segmentation | Reveals discrimination loss, population shift, and segment-specific issues invisible at portfolio level. | Portfolio-level only, or arbitrary decile splits |
| Grades from origination, not current | The origination grade reflects the model's decision. Re-grading obscures ranking assessment. | Re-grade based on current score |
| Config-driven onboarding via YAML | One file per model; no custom code. | Custom SQL or Python per model |
| Mandos remains model-agnostic | All model-specific semantics in config. | Embedding model-specific logic in library |
| Aggregate storage only | Keeps Mandos lightweight; account-level joins upstream. | Account-level storage in Mandos |
| GROUPING SETS for grade + portfolio | Single query for both segmented and aggregate rows. | Separate queries per grade |
| Snowflake Tasks for scheduling | Native to platform; no external orchestrator. | Airflow, cron, manual runs |
| Dashboard as read-only layer | Clear separation of concerns. | Dashboard owns scheduling/computation |
| Mandos over SageMaker Model Monitor | SageMaker lacks vintage tracking, cumulative tiers, and grade separation; designed for short-lag ground truth | Use SageMaker Model Monitor exclusively |
| Mandos over Snowflake ML Observability | Snowflake ML Observability lacks vintage cohort logic and requires registry coupling; monitoring grain is time-windowed, not vintage × MOB × grade | Use Snowflake ML Observability exclusively |

---

## 16. Appendix: Glossary

| Term | Definition |
|---|---|
| Vintage | A cohort of accounts grouped by origination period (typically calendar month) |
| MOB | Months on Book. Months elapsed since origination. |
| Grade | Risk tier assigned at origination (A, B, C, D, X for Zuul), based on model score bands |
| Observation Window | Time period after origination during which the target is evaluated (24 months for Zuul) |
| Severity Tier | A cumulative delinquency threshold tracked over time. Monotonically increasing. |
| Confirmed Bad | An account that has already triggered the actual bad flag before the window closes |
| Probable Bad | An account showing severe distress likely but not certain to convert |
| Grade Separation | Gap in severity rates between adjacent grades. Wide = good discrimination. |
| PSI | Population Stability Index. Measures distribution shift. |
| CSI | Characteristic Stability Index. Feature-level distribution shift. |
| KS | Kolmogorov-Smirnov statistic. Max separation between score CDFs for events vs. non-events. |
| CBPE | Confidence-Based Performance Estimation. Estimates performance from predicted probabilities. |
| DPD | Days Past Due. Delinquency severity measure. |
| Maturation Curve | Trajectory of a metric within a single vintage as it ages. |
