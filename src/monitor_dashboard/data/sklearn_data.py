"""Dummy data built from real sklearn models and open datasets.

Trains actual models on synthetic-but-structured data, scores over time
windows, injects drift, and computes genuine PSI/CSI/AUC/KS metrics.

This replaces the purely random generators with data that tells a
realistic story for the dashboard prototype.
"""

from __future__ import annotations

import datetime
import hashlib
import random
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CACHE_DIR = Path(__file__).parent / "_cache"
_TODAY = datetime.date(2026, 4, 6)

# Model definitions — mix of classification and regression
MODEL_CONFIGS: list[dict] = [
    {
        "name": "Auto Loan Default",
        "task": "classification",
        "cadence": "daily",
        "owner": "J. Martinez",
        "domain": "Credit",
        "baseline_date": "2025-06-15",
        "drift_scenario": "critical",  # significant drift injected
        "n_samples": 20_000,
        "n_features": 18,
        "n_informative": 12,
    },
    {
        "name": "Fraud Detection",
        "task": "classification",
        "cadence": "daily",
        "owner": "S. Patel",
        "domain": "Fraud",
        "baseline_date": "2025-03-01",
        "drift_scenario": "warning",
        "n_samples": 25_000,
        "n_features": 22,
        "n_informative": 15,
    },
    {
        "name": "Lease Residual Value",
        "task": "regression",
        "cadence": "monthly",
        "owner": "R. Chen",
        "domain": "Leasing",
        "baseline_date": "2025-01-10",
        "drift_scenario": "healthy",
        "n_samples": 10_000,
        "n_features": 14,
        "n_informative": 10,
    },
    {
        "name": "Early Payment Default",
        "task": "classification",
        "cadence": "weekly",
        "owner": "K. Williams",
        "domain": "Credit",
        "baseline_date": "2025-04-20",
        "drift_scenario": "healthy",
        "n_samples": 15_000,
        "n_features": 16,
        "n_informative": 11,
    },
    {
        "name": "Collections Propensity",
        "task": "classification",
        "cadence": "daily",
        "owner": "A. Johnson",
        "domain": "Collections",
        "baseline_date": "2025-07-01",
        "drift_scenario": "healthy",
        "n_samples": 18_000,
        "n_features": 15,
        "n_informative": 10,
    },
    {
        "name": "Dealer Risk Score",
        "task": "regression",
        "cadence": "monthly",
        "owner": "M. Thompson",
        "domain": "Dealer",
        "baseline_date": "2025-02-15",
        "drift_scenario": "healthy",
        "n_samples": 5_000,
        "n_features": 12,
        "n_informative": 8,
    },
    {
        "name": "Credit Line Increase",
        "task": "classification",
        "cadence": "weekly",
        "owner": "L. Davis",
        "domain": "Credit",
        "baseline_date": "2025-05-10",
        "drift_scenario": "warning",
        "n_samples": 12_000,
        "n_features": 17,
        "n_informative": 12,
    },
    {
        "name": "Application Fraud",
        "task": "classification",
        "cadence": "daily",
        "owner": "S. Patel",
        "domain": "Fraud",
        "baseline_date": "2025-08-01",
        "drift_scenario": "healthy",
        "n_samples": 20_000,
        "n_features": 20,
        "n_informative": 14,
    },
    {
        "name": "Prepayment Risk",
        "task": "classification",
        "cadence": "monthly",
        "owner": "R. Chen",
        "domain": "Credit",
        "baseline_date": "2025-03-20",
        "drift_scenario": "healthy",
        "n_samples": 10_000,
        "n_features": 13,
        "n_informative": 9,
    },
    {
        "name": "Loss Given Default",
        "task": "regression",
        "cadence": "weekly",
        "owner": "J. Martinez",
        "domain": "Credit",
        "baseline_date": "2025-06-01",
        "drift_scenario": "healthy",
        "n_samples": 8_000,
        "n_features": 15,
        "n_informative": 10,
    },
]

# Realistic feature names per domain
_CREDIT_FEATURES = [
    "credit_score",
    "debt_to_income",
    "income_ratio",
    "ltv_ratio",
    "employment_years",
    "loan_amount",
    "interest_rate",
    "term_months",
    "payment_history",
    "num_open_accounts",
    "utilization_rate",
    "months_since_delinquency",
    "num_inquiries_6mo",
    "num_trades",
    "revolving_balance",
    "installment_balance",
    "down_payment_pct",
    "vehicle_age",
    "vehicle_mileage",
    "gross_monthly_income",
    "monthly_debt_payment",
    "num_derogatory",
]
_FRAUD_FEATURES = [
    "application_score",
    "ip_risk_score",
    "device_fingerprint_age",
    "velocity_24h",
    "address_mismatch",
    "phone_tenure_months",
    "email_domain_risk",
    "ssn_issuance_gap",
    "income_stated",
    "employer_verified",
    "id_doc_quality",
    "bureau_hit_count",
    "time_on_page_sec",
    "prior_apps_count",
    "distance_branch_mi",
    "session_anomaly_score",
    "cross_ref_alerts",
    "fico_delta_90d",
    "num_name_variants",
    "addr_change_count",
    "phone_change_count",
    "bank_acct_age_mo",
]
_LEASING_FEATURES = [
    "msrp",
    "residual_pct",
    "lease_term",
    "annual_mileage",
    "vehicle_segment",
    "model_year_delta",
    "region_idx",
    "depreciation_rate_hist",
    "brand_loyalty_score",
    "market_supply_idx",
    "fuel_type_code",
    "incentive_amount",
    "credit_tier",
    "prior_lease_flag",
]
_COLLECTIONS_FEATURES = [
    "days_past_due",
    "promise_keep_rate",
    "contact_attempts",
    "right_party_contact_rate",
    "balance_remaining",
    "original_loan_amt",
    "monthly_income_est",
    "payment_channel_pref",
    "cure_rate_30d",
    "segment_code",
    "skip_trace_score",
    "prior_collections_cnt",
    "bankruptcy_flag",
    "hardship_flag",
    "loan_age_months",
]
_DEALER_FEATURES = [
    "dealer_volume_mo",
    "chargeback_rate",
    "avg_deal_margin",
    "finance_penetration",
    "warranty_attach_rate",
    "customer_sat_score",
    "inventory_turn",
    "days_to_fund",
    "doc_error_rate",
    "compliance_score",
    "years_in_business",
    "territory_risk_idx",
]

_FEATURE_POOLS: dict[str, list[str]] = {
    "Credit": _CREDIT_FEATURES,
    "Fraud": _FRAUD_FEATURES,
    "Leasing": _LEASING_FEATURES,
    "Collections": _COLLECTIONS_FEATURES,
    "Dealer": _DEALER_FEATURES,
}


def _feature_names_for(domain: str, n: int) -> list[str]:
    """Pick feature names from the domain pool, padding with generic names."""
    pool = _FEATURE_POOLS.get(domain, _CREDIT_FEATURES)
    if n <= len(pool):
        return pool[:n]
    extra = [f"feature_{i}" for i in range(n - len(pool))]
    return pool + extra


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _run_dates(cadence: str, baseline_date: str) -> list[datetime.date]:
    """Generate scoring run dates from first run to today."""
    start = datetime.date.fromisoformat(baseline_date) + datetime.timedelta(days=30)
    dates: list[datetime.date] = []
    cur = start
    while cur <= _TODAY:
        dates.append(cur)
        if cadence == "daily":
            cur += datetime.timedelta(days=1)
        elif cadence == "weekly":
            cur += datetime.timedelta(weeks=1)
        elif cadence == "monthly":
            cur += datetime.timedelta(days=30)
        else:
            cur += datetime.timedelta(days=7)
    return dates


# ---------------------------------------------------------------------------
# PSI / CSI computation
# ---------------------------------------------------------------------------


def _compute_psi(
    baseline: np.ndarray,
    current: np.ndarray,
    bins: int | np.ndarray = 10,
) -> float:
    """Population Stability Index between two 1-D arrays."""
    if isinstance(bins, int):
        edges = np.percentile(baseline, np.linspace(0, 100, bins + 1))
        edges[0] = -np.inf
        edges[-1] = np.inf
    else:
        edges = bins

    base_counts = np.histogram(baseline, bins=edges)[0].astype(float)
    curr_counts = np.histogram(current, bins=edges)[0].astype(float)

    # Proportions with small-sample correction
    base_pct = (base_counts + 0.5) / (base_counts.sum() + 0.5 * len(base_counts))
    curr_pct = (curr_counts + 0.5) / (curr_counts.sum() + 0.5 * len(curr_counts))

    psi = float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))
    return max(psi, 0.0)


def _compute_csi_per_feature(
    baseline_X: np.ndarray,
    current_X: np.ndarray,
    feature_names: list[str],
    n_bins: int = 10,
) -> list[dict]:
    """CSI for each feature column."""
    results = []
    for i, fname in enumerate(feature_names):
        csi = _compute_psi(baseline_X[:, i], current_X[:, i], bins=n_bins)
        results.append({"feature_name": fname, "csi_value": round(csi, 6)})
    return results


# ---------------------------------------------------------------------------
# Data generation per model
# ---------------------------------------------------------------------------


def _generate_dataset(
    cfg: dict,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate a train/test split for one model using sklearn."""
    rng = np.random.RandomState(seed)

    if cfg["task"] == "classification":
        X, y = make_classification(
            n_samples=cfg["n_samples"],
            n_features=cfg["n_features"],
            n_informative=cfg["n_informative"],
            n_redundant=max(0, cfg["n_features"] - cfg["n_informative"] - 2),
            n_classes=2,
            flip_y=0.03,
            class_sep=1.2,
            random_state=seed,
        )
    else:
        X, y = make_regression(
            n_samples=cfg["n_samples"],
            n_features=cfg["n_features"],
            n_informative=cfg["n_informative"],
            noise=10.0,
            random_state=seed,
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=seed,
    )
    return X_train, X_test, y_train, y_test


def _inject_drift(
    X: np.ndarray,
    scenario: str,
    progress: float,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Shift feature distributions to simulate drift.

    Args:
        X: Feature matrix to shift.
        scenario: One of "critical", "warning", "healthy".
        progress: Float 0..1 indicating how far into the monitoring period
                  (0 = just after baseline, 1 = most recent run).
        rng: RandomState for reproducibility.
    """
    X_shifted = X.copy()
    n_feat = X.shape[1]

    if scenario == "critical":
        # Strong shift in first 4 features, growing over time
        n_shift = min(4, n_feat)
        for j in range(n_shift):
            magnitude = progress * (1.5 + 0.5 * j)
            X_shifted[:, j] += magnitude
            X_shifted[:, j] *= 1.0 + progress * 0.3  # scale shift too
    elif scenario == "warning":
        # Moderate shift in 2 features
        n_shift = min(2, n_feat)
        for j in range(n_shift):
            magnitude = progress * 0.7
            X_shifted[:, j] += magnitude
    # else: healthy — no shift

    # Add a little random noise for realism
    X_shifted += rng.normal(0, 0.01, X_shifted.shape)
    return X_shifted


def _build_model_data(cfg: dict) -> dict:
    """Train a model on baseline data and score over time with drift injection.

    Returns dict with:
        - model_registry row
        - score_psi: list of dicts
        - feature_csi: list of dicts (latest snapshot)
        - feature_csi_history: dict[feature_name -> list of dicts] (all snapshots)
        - performance: list of dicts
        - data_quality: list of dicts
        - distributions: dict (baseline / current per feature for latest)
        - bin_edges: dict[feature_name -> ndarray]
    """
    # Deterministic seed per model
    seed = int(hashlib.md5(cfg["name"].encode()).hexdigest()[:8], 16) % (2**31)
    rng = np.random.RandomState(seed)

    X_train, X_test, y_train, y_test = _generate_dataset(cfg, seed)
    feature_names = _feature_names_for(cfg["domain"], cfg["n_features"])
    run_dates = _run_dates(cfg["cadence"], cfg["baseline_date"])
    n_runs = len(run_dates)

    # ---- Train model on baseline ----
    if cfg["task"] == "classification":
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            random_state=seed,
        )
        model.fit(X_train, y_train)
        baseline_scores = model.predict_proba(X_test)[:, 1]
        baseline_auc = roc_auc_score(y_test, baseline_scores)
    else:
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            random_state=seed,
        )
        model.fit(X_train, y_train)
        baseline_scores = model.predict(X_test)
        baseline_auc = None  # regression — no AUC

    # ---- Compute baseline bin edges (persisted at onboarding) ----
    n_psi_bins = 10
    score_bin_edges = np.percentile(
        baseline_scores,
        np.linspace(0, 100, n_psi_bins + 1),
    )
    score_bin_edges[0] = -np.inf
    score_bin_edges[-1] = np.inf

    feature_bin_edges: dict[str, np.ndarray] = {}
    for j in range(X_test.shape[1]):
        edges = np.percentile(X_test[:, j], np.linspace(0, 100, n_psi_bins + 1))
        edges[0] = -np.inf
        edges[-1] = np.inf
        feature_bin_edges[feature_names[j]] = edges

    # ---- Actuals lag config ----
    actuals_lag_days = int(rng.choice([30, 45, 60, 90]))

    # ---- Score over time windows ----
    score_psi_rows: list[dict] = []
    feature_csi_latest: list[dict] = []
    feature_csi_history: dict[str, list[dict]] = {fn: [] for fn in feature_names}
    perf_rows: list[dict] = []
    dq_rows: list[dict] = []

    for i, run_date in enumerate(run_dates):
        progress = i / max(n_runs - 1, 1)

        # Inject drift into features
        X_current = _inject_drift(X_test, cfg["drift_scenario"], progress, rng)

        # Score with the trained model
        if cfg["task"] == "classification":
            current_scores = model.predict_proba(X_current)[:, 1]
        else:
            current_scores = model.predict(X_current)

        # ---- Score PSI (using persisted bin edges) ----
        psi = _compute_psi(baseline_scores, current_scores, bins=score_bin_edges)
        score_psi_rows.append(
            {
                "model_name": cfg["name"],
                "run_date": run_date,
                "metric_name": "score_psi",
                "value": round(psi, 6),
                "threshold_warning": 0.10,
                "threshold_critical": 0.20,
            }
        )

        # ---- Feature CSI (using persisted bin edges per feature) ----
        for j, fname in enumerate(feature_names):
            csi = _compute_psi(
                X_test[:, j],
                X_current[:, j],
                bins=feature_bin_edges[fname],
            )
            row = {
                "model_name": cfg["name"],
                "run_date": run_date,
                "feature_name": fname,
                "csi_value": round(csi, 6),
                "threshold_warning": 0.10,
                "threshold_critical": 0.20,
            }
            feature_csi_history[fname].append(row)

            # Keep latest snapshot
            if i == n_runs - 1:
                feature_csi_latest.append(row)

        # ---- Performance metrics ----
        has_actuals = (_TODAY - run_date).days > actuals_lag_days
        is_estimated = not has_actuals

        if cfg["task"] == "classification":
            # Recompute AUC on drifted data — model degrades if features shift
            try:
                current_auc = roc_auc_score(y_test, current_scores)
            except ValueError:
                current_auc = baseline_auc
            ks = _ks_statistic(y_test, current_scores)
            gini = 2 * current_auc - 1

            for metric_name, value in [
                ("roc_auc", current_auc),
                ("ks_statistic", ks),
                ("gini", gini),
            ]:
                perf_rows.append(
                    {
                        "model_name": cfg["name"],
                        "run_date": run_date,
                        "metric_name": metric_name,
                        "value": round(value, 6),
                        "is_estimated": is_estimated,
                        "actuals_through": (
                            run_date - datetime.timedelta(days=actuals_lag_days)
                            if has_actuals
                            else None
                        ),
                    }
                )
        else:
            # Regression — use RMSE / MAE / R² as "performance"
            from sklearn.metrics import (
                mean_squared_error,
                r2_score,
                mean_absolute_error,
            )

            rmse_val = float(np.sqrt(mean_squared_error(y_test, current_scores)))
            r2_val = float(r2_score(y_test, current_scores))
            mae_val = float(mean_absolute_error(y_test, current_scores))

            for metric_name, value in [
                ("rmse", rmse_val),
                ("r_squared", r2_val),
                ("mae", mae_val),
            ]:
                perf_rows.append(
                    {
                        "model_name": cfg["name"],
                        "run_date": run_date,
                        "metric_name": metric_name,
                        "value": round(value, 6),
                        "is_estimated": is_estimated,
                        "actuals_through": (
                            run_date - datetime.timedelta(days=actuals_lag_days)
                            if has_actuals
                            else None
                        ),
                    }
                )

        # ---- Data quality ----
        missing_rate = max(0.0, 0.002 + rng.normal(0, 0.001))
        # Inject DQ issues for drifted models
        if cfg["drift_scenario"] == "critical" and progress > 0.7:
            oor = rng.randint(2, 6)
        elif cfg["drift_scenario"] == "warning" and progress > 0.8:
            oor = rng.randint(1, 4)
        else:
            oor = rng.randint(0, 2)

        dq_rows.append(
            {
                "model_name": cfg["name"],
                "run_date": run_date,
                "total_features": cfg["n_features"],
                "missing_rate": round(missing_rate, 5),
                "baseline_missing_rate": 0.001,
                "out_of_range_features": int(oor),
                "schema_valid": rng.random() > 0.02,
                "record_count": int(rng.randint(5_000, 50_000)),
            }
        )

    # ---- Distribution data for latest snapshot (baseline vs current) ----
    latest_X = _inject_drift(X_test, cfg["drift_scenario"], 1.0, rng)
    distributions: dict[str, dict] = {}
    for j, fname in enumerate(feature_names):
        edges = feature_bin_edges[fname]
        finite_edges = edges.copy()
        finite_edges[0] = np.min(np.concatenate([X_test[:, j], latest_X[:, j]])) - 1
        finite_edges[-1] = np.max(np.concatenate([X_test[:, j], latest_X[:, j]])) + 1

        base_hist = np.histogram(X_test[:, j], bins=edges)[0].astype(float)
        curr_hist = np.histogram(latest_X[:, j], bins=edges)[0].astype(float)

        base_pct = base_hist / base_hist.sum()
        curr_pct = curr_hist / curr_hist.sum()

        bin_labels = [
            f"{finite_edges[k]:.2f} – {finite_edges[k+1]:.2f}"
            for k in range(len(finite_edges) - 1)
        ]

        distributions[fname] = {
            "bin_label": bin_labels,
            "baseline_pct": base_pct.tolist(),
            "current_pct": curr_pct.tolist(),
        }

    return {
        "registry": {
            "model_name": cfg["name"],
            "task": cfg["task"],
            "cadence": cfg["cadence"],
            "owner": cfg["owner"],
            "domain": cfg["domain"],
            "n_features": cfg["n_features"],
            "baseline_date": datetime.date.fromisoformat(cfg["baseline_date"]),
            "last_run_date": run_dates[-1] if run_dates else None,
        },
        "score_psi": score_psi_rows,
        "feature_csi": feature_csi_latest,
        "feature_csi_history": feature_csi_history,
        "performance": perf_rows,
        "data_quality": dq_rows,
        "distributions": distributions,
    }


def _ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Kolmogorov–Smirnov statistic for binary classification."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)

    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]

    if len(pos) == 0 or len(neg) == 0:
        return 0.0

    all_vals = np.sort(np.unique(np.concatenate([pos, neg])))
    pos_cdf = np.searchsorted(np.sort(pos), all_vals, side="right") / len(pos)
    neg_cdf = np.searchsorted(np.sort(neg), all_vals, side="right") / len(neg)

    return float(np.max(np.abs(pos_cdf - neg_cdf)))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_all_mock_data() -> dict[str, pl.DataFrame | dict]:
    """Build all mock data from trained sklearn models.

    Returns:
        Dict with keys:
        - model_registry: pl.DataFrame
        - score_psi: pl.DataFrame
        - feature_csi: pl.DataFrame (latest per model)
        - performance: pl.DataFrame
        - data_quality: pl.DataFrame
        - distributions: dict[model_name -> dict[feature_name -> dict]]
        - feature_csi_history: dict[model_name -> dict[feature_name -> pl.DataFrame]]
    """
    registries: list[dict] = []
    all_psi: list[dict] = []
    all_csi: list[dict] = []
    all_perf: list[dict] = []
    all_dq: list[dict] = []
    all_dists: dict[str, dict] = {}
    all_csi_hist: dict[str, dict[str, pl.DataFrame]] = {}

    for cfg in MODEL_CONFIGS:
        result = _build_model_data(cfg)

        registries.append(result["registry"])
        all_psi.extend(result["score_psi"])
        all_csi.extend(result["feature_csi"])
        all_perf.extend(result["performance"])
        all_dq.extend(result["data_quality"])
        all_dists[cfg["name"]] = result["distributions"]

        # Convert CSI history lists to DataFrames
        hist_dfs: dict[str, pl.DataFrame] = {}
        for fname, rows in result["feature_csi_history"].items():
            if rows:
                hist_dfs[fname] = pl.DataFrame(rows)
        all_csi_hist[cfg["name"]] = hist_dfs

    return {
        "model_registry": pl.DataFrame(registries),
        "score_psi": pl.DataFrame(all_psi),
        "feature_csi": pl.DataFrame(all_csi),
        "performance": pl.DataFrame(all_perf),
        "data_quality": pl.DataFrame(all_dq),
        "distributions": all_dists,
        "feature_csi_history": all_csi_hist,
    }
