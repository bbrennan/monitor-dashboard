# Mandos Compute Architecture

**Primitives-First Design with Open-Source Metric Engines**

*ML Engineering, Risk Organization · Internal · April 2026*

---

## 1. Executive Summary

Mandos uses a two-phase compute model: **Snowflake handles heavy aggregation** (full table scans, joins, GROUP BYs) and produces lightweight summary statistics called **Primitives**. Python functions then consume these Primitives to compute monitoring metrics without ever pulling raw account-level data into memory.

This document defines how the Primitives architecture integrates a small set of production-grade open-source libraries for metrics that Mandos should not build itself, while Mandos retains ownership of the orchestration layer, UX, and metrics that are simple enough to implement internally with numpy/scipy/pandas.

**The decisions:**

| Metric | Decision | Rationale |
|---|---|---|
| PSI / CSI | **BUILD** (numpy, from Primitives) | 10 lines of numpy on histogram arrays. No library adds value here. |
| DQ metrics (null rate, OOR, cardinality) | **BUILD** (arithmetic on Primitives) | Trivial computations on counts. A library would be overhead. |
| Severity tier rates, confirmed/probable | **BUILD** (aggregation results from Snowflake) | These are direct outputs of the ingestion query. Already done. |
| AUC | **USE scikit-learn** | `roc_auc_score` is production-grade, battle-tested, one-liner. |
| KS statistic | **USE scipy** | `ks_2samp` is the canonical implementation. |
| Gini coefficient | **DERIVE** from AUC | `2 * AUC - 1`. No library needed. |
| CBPE (performance estimation without actuals) | **USE NannyML** | Purpose-built for this exact problem. Non-trivial algorithm we should not maintain ourselves. |
| Evidently AI | **SKIP** | Requires full DataFrames. Incompatible with the Primitives architecture. |
| ydata-profiling | **SKIP** | Useful for exploration but not for production monitoring pipelines. |
| datacompy | **SKIP** | Solves a different problem (data reconciliation). Not relevant. |

Mandos's value is the **orchestration layer**: config-driven onboarding, vintage × MOB × grade query generation, Primitives collection, snapshot lifecycle management, alerting, and the dashboard UX. Metric computation is delegated — to our own numpy/scipy code where the math is simple, and to production libraries where the algorithm is non-trivial.

---

## 2. Current Primitives Architecture

### 2.1 What Are Primitives?

Primitives are pre-computed summary statistics produced by Snowflake SQL aggregation queries. They capture the statistical shape of a dataset without transferring row-level data to Python.

| Primitive | Snowflake SQL | Python Receives |
|---|---|---|
| `row_count` | `COUNT(*)` | Integer |
| `null_count` | `COUNT(*) - COUNT(col)` | Integer per column |
| `mean` | `AVG(col)` | Float per column |
| `stddev` | `STDDEV(col)` | Float per column |
| `min` / `max` | `MIN(col)` / `MAX(col)` | Float per column |
| `percentiles` | `PERCENTILE_CONT(p) WITHIN GROUP (ORDER BY col)` | Array of floats (p = 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99) |
| `histogram` | `WIDTH_BUCKET()` + `COUNT(*)` per bin | Bin edges array + bin counts array |
| `cardinality` | `COUNT(DISTINCT col)` | Integer per column |
| `value_counts` | `GROUP BY col` + `COUNT(*)` (categorical) | Dict of value → count |

### 2.2 How Primitives Flow Today

```
┌─────────────────────────────────────────────────────────┐
│                     SNOWFLAKE                           │
│                                                         │
│  Raw Tables ──► Aggregation SQL ──► Primitives (JSON)   │
│  (millions       (full scan,          (kilobytes,       │
│   of rows)        GROUP BY)            summary stats)   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                      PYTHON                             │
│                                                         │
│  Primitives ──► Metric Functions ──► Snapshot Results    │
│  (in memory,     (PSI, null_rate,     (persisted back   │
│   lightweight)    OOR, etc.)           to Snowflake)    │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Why This Design Is Good

- **No raw data in Python.** Snowflake handles the full table scan. Python never sees millions of rows.
- **Network efficiency.** Primitives are kilobytes. Raw feature data is gigabytes.
- **Parallelism.** Snowflake's warehouse scales the aggregation. Python processes small payloads.
- **Reproducibility.** Primitives are deterministic snapshots that can be stored, compared, and replayed.

---

## 3. Metric Taxonomy: What Needs What

### 3.1 Tier 1: Primitive-Compatible (BUILD)

These metrics are computed entirely from pre-aggregated summary statistics. No row-level data needed. Mandos builds these internally using numpy/scipy/pandas.

| Metric | Required Primitives | Implementation |
|---|---|---|
| **PSI** | Baseline histogram + current histogram | numpy: bin-to-bin log-ratio sum |
| **CSI** | Per-feature histograms | numpy: same as PSI, applied per feature |
| **Null rate** | `null_count` / `row_count` | Arithmetic |
| **Out-of-range rate** | `min`, `max`, histogram tail bins | Arithmetic |
| **Cardinality drift** | `cardinality` baseline vs. current | Arithmetic |
| **Mean / stddev shift** | `mean`, `stddev` | Arithmetic |
| **Score distribution stability** | Score histogram | numpy: PSI on the score column |
| **Cumulative severity rates** | Aggregated tier flags from ingestion query | Direct from Snowflake GROUP BY |
| **Confirmed / probable bad rates** | Same as above | Direct from Snowflake GROUP BY |
| **Volume metrics** | `row_count` per vintage × grade | Direct from GROUP BY |

### 3.2 Tier 2: Paired-Array Metrics (USE Libraries)

These metrics require paired values (predicted_score, label) per account. Cannot be derived from histograms because they depend on rank-ordering. Mandos uses production libraries for these.

| Metric | Library | Input | Size per Segment |
|---|---|---|---|
| **AUC** | scikit-learn (`roc_auc_score`) | Score + label arrays | ~16 KB (2,000 accounts × 2 floats) |
| **KS** | scipy (`ks_2samp`) | Score arrays split by label | Same |
| **Gini** | Derived: `2 * AUC - 1` | AUC result | N/A |
| **CBPE** | NannyML | Score array + baseline reference | ~16 KB + baseline |

**Why paired arrays cannot be avoided for these metrics:** AUC measures how well the model rank-orders accounts. Two very different score distributions can produce the same histogram but different AUCs. The histogram loses the pairing between "this score belongs to a good account" and "this score belongs to a bad account." That pairing is exactly what discrimination metrics measure.

**Why this is still lightweight:** Paired arrays pull exactly two columns (score + label) for a single vintage × grade segment — typically 500 to 5,000 rows, roughly 16 KB. This is not a Primitives violation; it is a minimal, bounded second tier.

---

## 4. What We Build vs. What We Use

### 4.1 BUILD: PSI / CSI (numpy)

PSI is a histogram comparison. Mandos already has the histograms as Primitives. The implementation is straightforward and no production library adds meaningful value over 10 lines of numpy.

```python
import numpy as np

def compute_psi(baseline_counts: np.ndarray, current_counts: np.ndarray) -> float:
    """PSI from two histogram count arrays sharing the same bin edges."""
    base_pct = np.clip(baseline_counts / baseline_counts.sum(), 1e-8, None)
    curr_pct = np.clip(current_counts / current_counts.sum(), 1e-8, None)
    return float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))

def compute_csi(baseline_primitives: dict, current_primitives: dict,
                features: list[str]) -> dict[str, float]:
    """CSI per feature. Same formula as PSI, applied per column."""
    return {
        feature: compute_psi(
            baseline_primitives[feature].bin_counts,
            current_primitives[feature].bin_counts,
        )
        for feature in features
    }
```

No dependency beyond numpy. PSI thresholds (0.10 warning, 0.25 critical) are applied downstream by the alerting layer.

### 4.2 BUILD: Data Quality Metrics (arithmetic)

Null rates, out-of-range rates, and cardinality drift are direct arithmetic on Primitive values. No library needed.

```python
def compute_dq_metrics(primitives: ColumnPrimitives,
                       baseline: ColumnPrimitives) -> dict:
    return {
        "null_rate": primitives.null_count / primitives.row_count,
        "cardinality": primitives.cardinality,
        "cardinality_delta": primitives.cardinality - baseline.cardinality,
        "mean_shift": abs(primitives.mean - baseline.mean) / (baseline.stddev or 1),
        "min": primitives.min_val,
        "max": primitives.max_val,
    }
```

### 4.3 BUILD: Severity Rates and Confirmed/Probable (Snowflake aggregation)

These are not computed in Python at all. They are direct outputs of the vintage × MOB × grade ingestion query (the `AVG(ever_30_dpd)`, `AVG(confirmed_bad)` columns in the GROUPING SETS query). Snowflake does the work. Python receives the results and passes them through to the snapshot.

### 4.4 USE: scikit-learn for AUC

```python
from sklearn.metrics import roc_auc_score

def compute_auc(scores: np.ndarray, labels: np.ndarray) -> float | None:
    if labels.sum() < 30 or (labels == 0).sum() < 30:
        return None  # Insufficient positive or negative labels
    return float(roc_auc_score(labels, scores))
```

One function call. Production-tested across millions of deployments. We do not build this.

### 4.5 USE: scipy for KS

```python
from scipy.stats import ks_2samp

def compute_ks(scores: np.ndarray, labels: np.ndarray) -> float | None:
    if labels.sum() < 30 or (labels == 0).sum() < 30:
        return None
    scores_bad = scores[labels == 1]
    scores_good = scores[labels == 0]
    ks_stat, _ = ks_2samp(scores_bad, scores_good)
    return float(ks_stat)
```

Same rationale. `ks_2samp` is the canonical implementation. No reason to rewrite it.

### 4.6 USE: NannyML for CBPE

CBPE (Confidence-Based Performance Estimation) estimates model performance using predicted probabilities alone, without any ground truth labels. This is the most valuable metric in the first few months of a vintage's life, before enough accounts have matured for meaningful AUC/KS.

The algorithm is non-trivial: it bins predicted probabilities, uses the calibration relationship from a reference dataset to estimate true/false positive rates per bin, and reconstructs an expected AUC. NannyML's implementation handles edge cases (calibration drift, bin sparsity, confidence intervals) that we would have to discover and solve ourselves.

```python
import nannyml as nml
import pandas as pd

def compute_cbpe(scores: np.ndarray,
                 ref_scores: np.ndarray,
                 ref_labels: np.ndarray) -> dict:
    """
    scores:     Current vintage predicted probabilities (no labels yet)
    ref_scores: Baseline vintage scores (fully matured)
    ref_labels: Baseline vintage actual labels
    """
    ref_df = pd.DataFrame({
        "y_pred_proba": ref_scores,
        "y_pred": (ref_scores >= 0.5).astype(int),
        "y_true": ref_labels,
    })
    analysis_df = pd.DataFrame({
        "y_pred_proba": scores,
        "y_pred": (scores >= 0.5).astype(int),
    })

    estimator = nml.CBPE(
        y_pred_proba="y_pred_proba",
        y_pred="y_pred",
        y_true="y_true",
        problem_type="classification_binary",
        metrics=["roc_auc"],
    )
    estimator.fit(ref_df)
    results = estimator.estimate(analysis_df)

    return {
        "cbpe_auc": float(results.data["estimated_roc_auc"].iloc[0]),
    }
```

NannyML is the only external dependency beyond numpy/scipy/sklearn, and it earns its place by implementing a non-trivial algorithm that we should not maintain ourselves.

### 4.7 SKIP: Evidently AI

Evidently's API requires full reference and current DataFrames. Every function expects `pandas.DataFrame` in, report out. There is no way to pass pre-computed Primitives. Using Evidently would mean pulling raw feature data from Snowflake into Python for every monitoring run — the exact pattern the Primitives architecture is designed to avoid. Every metric Evidently computes (PSI, null rate, column drift) we already compute from Primitives, more efficiently, with no data movement.

### 4.8 SKIP: ydata-profiling

ydata-profiling generates comprehensive statistical profiles from DataFrames. Useful for exploration but not designed for production monitoring. Slow on large datasets, produces HTML reports rather than programmatic outputs, and requires the full DataFrame in memory. If a model owner wants to profile data during investigation, they can use it independently. It is not part of the Mandos pipeline.

### 4.9 SKIP: datacompy

Data reconciliation tool. Not relevant to model monitoring.

---

## 5. Two-Tier Architecture

### 5.1 Design Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        SNOWFLAKE                             │
│                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │   Tier 1 Query  │    │         Tier 2 Query             │ │
│  │                 │    │                                  │ │
│  │  Primitives:    │    │  Paired arrays:                  │ │
│  │  histograms,    │    │  (score, label) per account      │ │
│  │  counts, means, │    │  for segments needing AUC/KS     │ │
│  │  percentiles,   │    │                                  │ │
│  │  severity rates │    │  Only 2 columns, scoped to one   │ │
│  │                 │    │  vintage × grade (~2K rows)      │ │
│  └────────┬────────┘    └──────────────┬───────────────────┘ │
│           │                            │                     │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            ▼                            ▼
┌───────────────────────┐  ┌────────────────────────────────────┐
│   Tier 1: BUILD       │  │   Tier 2: USE                      │
│                       │  │                                    │
│  Mandos internal:     │  │  scikit-learn → AUC                │
│  numpy  → PSI / CSI   │  │  scipy       → KS                  │
│  python → DQ metrics  │  │  derived     → Gini                │
│  direct → severity    │  │  NannyML     → CBPE                │
│           rates       │  │                                    │
│                       │  │  Input: ~500–5,000 paired values   │
│  Input: Primitives    │  │  per segment (kilobytes)           │
│  (bytes to kilobytes) │  │                                    │
└───────────┬───────────┘  └──────────────┬─────────────────────┘
            │                             │
            ▼                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     SNAPSHOT ASSEMBLY                         │
│                                                              │
│  Merge Tier 1 + Tier 2 → snapshot row per vintage × MOB ×   │
│  grade → persist to mandos.snapshots in Snowflake            │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 When Each Tier Fires

| MOB Range | Tier 1 (Primitives) | Tier 2 (Paired Arrays) |
|---|---|---|
| 1–2 | ✓ DQ, drift, severity rates | ✓ CBPE only (no labels for AUC/KS yet) |
| 3–23 | ✓ DQ, drift, severity rates | ✓ AUC, KS, Gini on confirmed + probable labels; CBPE |
| 24 (final) | ✓ DQ, drift, severity rates | ✓ Final AUC, KS, Gini on actual labels |

Tier 2 is skipped for any grade segment with fewer than `min_vintage_size` accounts (default 500) or fewer than 30 positive labels.

### 5.3 Tier 2 Query

```sql
SELECT pd_score,
       GREATEST(confirmed_bad, probable_bad) AS composite_label
FROM mandos_staging.classified_{vintage}
WHERE grade = :grade
  AND mob = :current_mob
```

For CBPE on early vintages (MOB 1–2), the query pulls `pd_score` only — no labels needed.

---

## 6. Primitive Data Structures

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class ColumnPrimitives:
    """Summary statistics for a single column, computed in Snowflake."""
    column_name: str
    row_count: int
    null_count: int
    mean: float | None
    stddev: float | None
    min_val: float | None
    max_val: float | None
    percentiles: dict[float, float] | None
    bin_edges: np.ndarray | None
    bin_counts: np.ndarray | None
    cardinality: int | None
    value_counts: dict[str, int] | None

@dataclass
class SegmentPrimitives:
    """All primitives for a vintage × MOB × grade segment."""
    vintage: str
    mob: int
    grade: str | None  # None = portfolio aggregate
    account_count: int
    columns: dict[str, ColumnPrimitives]
    severity_rates: dict[str, float]
    confirmed_bad_rate: float
    probable_bad_rate: float
```

### Future Extension: Conditional Histogram

A natural extension that would make calibration metrics Tier 1 compatible:

```sql
SELECT
  WIDTH_BUCKET(pd_score, 0, 1, 10)  AS score_decile,
  COUNT(*)                            AS n,
  AVG(pd_score)                       AS mean_predicted,
  AVG(confirmed_bad)                  AS observed_rate
FROM mandos_staging.classified_{vintage}
WHERE grade = :grade AND mob = :current_mob
GROUP BY score_decile
ORDER BY score_decile
```

Produces ~10 rows. Enables calibration plots and Hosmer-Lemeshow from Primitives. Could also serve as the basis for an internal CBPE approximation if we ever want to drop NannyML — but that is a future decision.

---

## 7. Module Structure

```
mandos/
├── config/
│   └── parser.py              # YAML config parsing + validation
├── primitives/
│   ├── query_builder.py       # Generates Tier 1 Snowflake SQL
│   ├── models.py              # ColumnPrimitives, SegmentPrimitives
│   └── collector.py           # Executes queries, returns Primitive objects
├── paired/
│   ├── query_builder.py       # Generates Tier 2 paired-array SQL
│   └── collector.py           # Executes queries, returns numpy arrays
├── metrics/
│   ├── drift.py               # PSI, CSI (numpy, Tier 1) — BUILD
│   ├── data_quality.py        # Null rate, OOR, cardinality (Tier 1) — BUILD
│   ├── severity.py            # Tier rates, confirmed/probable (Tier 1) — BUILD
│   ├── discrimination.py      # AUC, KS, Gini (sklearn/scipy, Tier 2) — USE
│   └── cbpe.py                # CBPE (NannyML, Tier 2) — USE
├── snapshots/
│   ├── assembler.py           # Merges Tier 1 + Tier 2 into snapshot
│   └── persistence.py         # Writes snapshots to Snowflake
├── alerting/
│   └── thresholds.py          # Threshold evaluation, alert generation
└── orchestrator.py            # Config → queries → metrics → persist
```

Each module has a single dependency:

- `drift.py` → numpy
- `data_quality.py` → stdlib
- `severity.py` → stdlib
- `discrimination.py` → sklearn, scipy
- `cbpe.py` → nannyml, pandas

---

## 8. Orchestrator Flow

```python
def run_monthly_batch(config: MandosConfig):
    """Main orchestration loop for a single model."""

    active_vintages = get_active_vintages(config)
    baseline = load_baseline(config)

    for vintage in active_vintages:
        current_mob = compute_mob(vintage)

        # ── Tier 1: Primitives (always) ──
        primitives_by_grade = collect_primitives(config, vintage, current_mob)

        tier1 = {}
        for grade, prims in primitives_by_grade.items():
            tier1[grade] = {
                "drift": compute_csi(baseline.columns, prims.columns,
                                     config.monitored_features),
                "dq": {col: compute_dq_metrics(prims.columns[col],
                                                baseline.columns[col])
                       for col in config.monitored_features},
                "severity": prims.severity_rates,
                "confirmed_bad_rate": prims.confirmed_bad_rate,
                "probable_bad_rate": prims.probable_bad_rate,
            }

        # ── Tier 2: Paired arrays (conditional) ──
        tier2 = {}
        for grade in config.perf_grades:
            n = primitives_by_grade[grade].account_count
            n_confirmed = int(
                primitives_by_grade[grade].confirmed_bad_rate * n
            )

            if n_confirmed >= 30 and current_mob >= 3:
                scores, labels = collect_paired_arrays(
                    config, vintage, current_mob, grade
                )
                auc = compute_auc(scores, labels)
                ks = compute_ks(scores, labels)
                gini = (2 * auc - 1) if auc else None
                tier2[grade] = {"auc": auc, "ks": ks, "gini": gini}

            if current_mob <= 12:
                scores = collect_score_array(config, vintage, grade)
                cbpe = compute_cbpe(scores, baseline.ref_scores,
                                    baseline.ref_labels)
                tier2.setdefault(grade, {}).update(cbpe)

        # ── Assemble + Persist ──
        for grade in config.all_grades + [None]:
            snapshot = assemble_snapshot(
                vintage, current_mob, grade,
                tier1.get(grade, {}),
                tier2.get(grade, {}),
            )
            persist_snapshot(snapshot)
            evaluate_thresholds(snapshot, config.thresholds)
```

---

## 9. Dependencies

### Required (Already in Any ML Environment)

| Package | Used By | Purpose |
|---|---|---|
| `numpy` | `drift.py` | PSI/CSI from histogram arrays |
| `scipy` | `discrimination.py` | KS statistic |
| `scikit-learn` | `discrimination.py` | AUC |
| `pandas` | `cbpe.py` | DataFrame wrapper for NannyML |
| `snowflake-snowpark-python` | `collector.py` | Snowflake query execution |
| `pyyaml` | `parser.py` | Config parsing |

### One New Dependency

| Package | Used By | Purpose |
|---|---|---|
| `nannyml` | `cbpe.py` | CBPE performance estimation |

NannyML is the only new dependency. It is optional — Mandos runs without it if CBPE is not enabled in the model config.

```python
try:
    import nannyml as nml
    HAS_NANNYML = True
except ImportError:
    HAS_NANNYML = False
```

---

## 10. Data Volume per Monthly Run

Assuming 14 active vintages across 4 models:

| Component | Per Segment | Full Run (~60 segments) |
|---|---|---|
| Tier 1 Primitives (Snowflake → Python) | ~10 KB | ~600 KB |
| Tier 2 Paired arrays (Snowflake → Python) | ~16 KB | ~1 MB |
| Snapshot rows (Python → Snowflake) | ~2 KB | ~120 KB |
| **Total network I/O** | | **~1.7 MB** |

The entire monthly monitoring run moves less data than a single high-resolution image.

---

## 11. Design Decisions

| Decision | Rationale |
|---|---|
| **BUILD PSI/CSI internally** | 10 lines of numpy. A library adds dependency weight with no value. |
| **BUILD DQ metrics internally** | Arithmetic on Primitives. Trivial. |
| **USE sklearn for AUC** | Production-tested one-liner. We do not maintain our own AUC. |
| **USE scipy for KS** | Canonical implementation. Same rationale. |
| **USE NannyML for CBPE** | Non-trivial algorithm with edge cases we should not own. The one metric where a library genuinely earns its dependency cost. |
| **SKIP Evidently** | Requires full DataFrames. Incompatible with Primitives. Every metric it provides, we already compute more efficiently. |
| **SKIP ydata-profiling** | Not a production monitoring tool. |
| **SKIP datacompy** | Solves a different problem. |
| **Keep Tier 1 unchanged** | Handles 70% of metrics. Proven. No reason to change. |
| **Add Tier 2 as lightweight paired arrays** | AUC/KS cannot be computed from histograms. Paired arrays are small and transient. |
| **Minimum 30 positive labels for Tier 2** | AUC/KS with fewer positives is unreliable. Skip rather than mislead. |
| **NannyML as optional** | CBPE is valuable but not required for every model. Graceful fallback. |

---

## 12. Implementation Phases

### Phase 1: Validate Tier 1 (No Changes)
- Confirm existing Primitives cover all Tier 1 metrics
- Audit PSI/CSI/DQ implementations for correctness
- Document Primitive schema as stable interface

### Phase 2: Add Tier 2
- Implement `paired/` module (query builder + collector)
- Implement `metrics/discrimination.py` (sklearn + scipy)
- Add Tier 2 conditional logic to orchestrator
- Test with Zuul historical vintages

### Phase 3: Integrate CBPE
- Add NannyML as optional dependency
- Implement `metrics/cbpe.py`
- Validate CBPE estimates against known mature vintages
- Confirm graceful degradation when NannyML is absent

### Phase 4: Conditional Histogram (Future)
- Add conditional histogram Primitive to Tier 1 query builder
- Implement calibration metrics from Primitives
- Evaluate whether internal CBPE approximation is viable to remove NannyML
