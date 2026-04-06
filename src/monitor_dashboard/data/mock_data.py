"""Fast synthetic data generators for dashboard mockups.

Generates realistic-looking monitoring data using simple random number
generation — no sklearn model training.  Loads in <1 second.
"""

from __future__ import annotations

import datetime
from functools import lru_cache

import numpy as np
import polars as pl

# ---------------------------------------------------------------------------
# Model registry — same 10 models as the sklearn version
# ---------------------------------------------------------------------------

MODEL_CONFIGS: list[dict] = [
    {
        "name": "Auto Loan Default",
        "task": "classification",
        "cadence": "daily",
        "owner": "J. Martinez",
        "domain": "Credit",
        "baseline_date": "2025-06-15",
        "drift_scenario": "critical",
        "n_features": 18,
    },
    {
        "name": "Fraud Detection",
        "task": "classification",
        "cadence": "daily",
        "owner": "S. Patel",
        "domain": "Fraud",
        "baseline_date": "2025-03-01",
        "drift_scenario": "warning",
        "n_features": 22,
    },
    {
        "name": "Lease Residual Value",
        "task": "regression",
        "cadence": "monthly",
        "owner": "R. Chen",
        "domain": "Leasing",
        "baseline_date": "2025-01-10",
        "drift_scenario": "healthy",
        "n_features": 14,
    },
    {
        "name": "Early Payment Default",
        "task": "classification",
        "cadence": "weekly",
        "owner": "K. Williams",
        "domain": "Credit",
        "baseline_date": "2025-04-20",
        "drift_scenario": "healthy",
        "n_features": 16,
    },
    {
        "name": "Collections Propensity",
        "task": "classification",
        "cadence": "daily",
        "owner": "A. Johnson",
        "domain": "Collections",
        "baseline_date": "2025-07-01",
        "drift_scenario": "healthy",
        "n_features": 15,
    },
    {
        "name": "Dealer Risk Score",
        "task": "regression",
        "cadence": "monthly",
        "owner": "M. Thompson",
        "domain": "Dealer",
        "baseline_date": "2025-02-15",
        "drift_scenario": "healthy",
        "n_features": 12,
    },
    {
        "name": "Credit Line Increase",
        "task": "classification",
        "cadence": "weekly",
        "owner": "L. Davis",
        "domain": "Credit",
        "baseline_date": "2025-05-10",
        "drift_scenario": "warning",
        "n_features": 17,
    },
    {
        "name": "Application Fraud",
        "task": "classification",
        "cadence": "daily",
        "owner": "S. Patel",
        "domain": "Fraud",
        "baseline_date": "2025-08-01",
        "drift_scenario": "healthy",
        "n_features": 20,
    },
    {
        "name": "Prepayment Risk",
        "task": "classification",
        "cadence": "monthly",
        "owner": "R. Chen",
        "domain": "Credit",
        "baseline_date": "2025-03-20",
        "drift_scenario": "healthy",
        "n_features": 13,
    },
    {
        "name": "Loss Given Default",
        "task": "regression",
        "cadence": "weekly",
        "owner": "J. Martinez",
        "domain": "Credit",
        "baseline_date": "2025-06-01",
        "drift_scenario": "healthy",
        "n_features": 15,
    },
]

# Backward-compatible alias
MODELS = MODEL_CONFIGS

# ---------------------------------------------------------------------------
# Feature name pools by domain
# ---------------------------------------------------------------------------

_FEATURE_POOLS: dict[str, list[str]] = {
    "Credit": [
        "fico_score",
        "dti_ratio",
        "loan_amount",
        "interest_rate",
        "term_months",
        "ltv_ratio",
        "annual_income",
        "employment_length",
        "delinquency_count",
        "credit_util_ratio",
        "open_accounts",
        "total_balance",
        "months_since_delinq",
        "revolving_balance",
        "installment_amount",
        "home_ownership_flag",
        "verification_status",
        "payment_history_score",
        "credit_age_months",
        "inquiries_last_6m",
        "collections_count",
        "public_records",
    ],
    "Fraud": [
        "transaction_amount",
        "transaction_velocity",
        "ip_risk_score",
        "device_fingerprint_hash",
        "geo_distance_km",
        "session_duration_sec",
        "failed_auth_count",
        "account_age_days",
        "avg_transaction_amount",
        "time_since_last_txn",
        "merchant_category_risk",
        "card_present_flag",
        "billing_shipping_match",
        "email_domain_risk",
        "phone_verified",
        "address_change_recency",
        "new_device_flag",
        "velocity_24h",
        "cross_border_flag",
        "amt_std_dev",
        "weekend_flag",
        "night_flag",
    ],
    "Leasing": [
        "vehicle_age_months",
        "mileage",
        "residual_pct",
        "lease_term",
        "msrp",
        "depreciation_rate",
        "market_adjustment",
        "region_factor",
        "vehicle_class",
        "brand_premium",
        "condition_score",
        "auction_price_idx",
        "seasonal_factor",
        "fuel_type_code",
    ],
    "Collections": [
        "days_past_due",
        "outstanding_balance",
        "contact_attempt_count",
        "payment_plan_flag",
        "promise_to_pay_count",
        "skip_trace_score",
        "account_tenure_months",
        "previous_collection_flag",
        "settlement_ratio",
        "hardship_flag",
        "debt_to_income",
        "employment_verified",
        "contact_preference",
        "response_rate",
        "cure_rate_30d",
    ],
    "Dealer": [
        "dealer_volume",
        "avg_deal_margin",
        "chargeback_rate",
        "dealer_tenure_years",
        "audit_score",
        "compliance_flag",
        "region_code",
        "inventory_turnover",
        "customer_satisfaction",
        "finance_penetration",
        "warranty_attach_rate",
        "dealer_tier",
    ],
}


def _get_features(domain: str, n: int) -> list[str]:
    """Pick n feature names from the domain pool, cycling if needed."""
    pool = _FEATURE_POOLS.get(domain, _FEATURE_POOLS["Credit"])
    return [pool[i % len(pool)] for i in range(n)]


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

_TODAY = datetime.date(2026, 4, 6)


def _run_dates(cadence: str, baseline_date: str) -> list[datetime.date]:
    """Generate scoring run dates from baseline to today."""
    base = datetime.date.fromisoformat(baseline_date)
    step = {"daily": 1, "weekly": 7, "monthly": 30}.get(cadence, 7)
    dates: list[datetime.date] = []
    d = base + datetime.timedelta(days=step)
    while d <= _TODAY:
        dates.append(d)
        d += datetime.timedelta(days=step)
    return dates


# Backward-compatible alias
_generate_run_dates = _run_dates

# ---------------------------------------------------------------------------
# PSI ranges by drift scenario
# ---------------------------------------------------------------------------

_PSI_RANGES: dict[str, tuple[float, float, float, float]] = {
    # (base_mean, base_std, trend_per_run, noise_std)
    "healthy": (0.03, 0.01, 0.0002, 0.005),
    "warning": (0.06, 0.02, 0.001, 0.008),
    "critical": (0.10, 0.03, 0.003, 0.012),
}


# ---------------------------------------------------------------------------
# Core data generation
# ---------------------------------------------------------------------------


def _build_model_data(cfg: dict, rng: np.random.Generator) -> dict:
    """Build all monitoring data for a single model."""
    name = cfg["name"]
    task = cfg["task"]
    scenario = cfg["drift_scenario"]
    features = _get_features(cfg["domain"], cfg["n_features"])
    dates = _run_dates(cfg["cadence"], cfg["baseline_date"])
    n_runs = len(dates)

    if n_runs == 0:
        dates = [_TODAY]
        n_runs = 1

    # -- PSI time series ---------------------------------------------------
    base_mean, base_std, trend, noise = _PSI_RANGES[scenario]
    psi_values = np.clip(
        rng.normal(base_mean, base_std, n_runs)
        + np.arange(n_runs) * trend
        + rng.normal(0, noise, n_runs),
        0.001,
        0.6,
    )

    score_psi_rows = {
        "model_name": [name] * n_runs,
        "run_date": dates,
        "metric_name": ["score_psi"] * n_runs,
        "value": [round(float(v), 4) for v in psi_values],
        "threshold_warning": [0.10] * n_runs,
        "threshold_critical": [0.20] * n_runs,
    }

    # -- Performance metrics -----------------------------------------------
    if task == "classification":
        metric_names = ["roc_auc", "ks_statistic", "gini"]
        base_values = {"roc_auc": 0.82, "ks_statistic": 0.45, "gini": 0.64}
        degradation = {"healthy": 0.0001, "warning": 0.0008, "critical": 0.0015}
    else:
        metric_names = ["r_squared", "rmse", "mae"]
        base_values = {"r_squared": 0.78, "rmse": 0.15, "mae": 0.10}
        degradation = {"healthy": 0.0001, "warning": 0.0005, "critical": 0.001}

    deg = degradation[scenario]
    actuals_lag = int(rng.choice([30, 45, 60, 90]))
    actuals_cutoff = _TODAY - datetime.timedelta(days=actuals_lag)

    perf_rows: dict[str, list] = {
        "model_name": [],
        "run_date": [],
        "metric_name": [],
        "value": [],
        "is_estimated": [],
        "actuals_through": [],
    }

    for metric in metric_names:
        base = base_values[metric]
        for i, d in enumerate(dates):
            if metric in ("rmse", "mae"):
                val = base + i * deg * 0.5 + rng.normal(0, 0.005)
            else:
                val = base - i * deg + rng.normal(0, 0.008)
            is_est = d > actuals_cutoff
            perf_rows["model_name"].append(name)
            perf_rows["run_date"].append(d)
            perf_rows["metric_name"].append(metric)
            perf_rows["value"].append(round(float(np.clip(val, 0.0, 1.0)), 4))
            perf_rows["is_estimated"].append(is_est)
            perf_rows["actuals_through"].append(None if is_est else actuals_cutoff)

    # -- Feature CSI (latest snapshot) -------------------------------------
    csi_base = {"healthy": 0.03, "warning": 0.08, "critical": 0.15}[scenario]
    csi_values = np.clip(
        rng.exponential(csi_base, cfg["n_features"]),
        0.001,
        0.5,
    )
    if scenario in ("warning", "critical"):
        top_k = min(3, cfg["n_features"])
        csi_values[:top_k] = rng.uniform(0.12, 0.35, top_k)

    feature_csi_rows = {
        "model_name": [name] * cfg["n_features"],
        "run_date": [dates[-1]] * cfg["n_features"],
        "feature_name": features,
        "csi_value": [round(float(v), 4) for v in csi_values],
        "threshold_warning": [0.10] * cfg["n_features"],
        "threshold_critical": [0.20] * cfg["n_features"],
    }

    # -- Data quality ------------------------------------------------------
    base_missing = rng.uniform(0.001, 0.02)
    dq_rows = {
        "model_name": [name] * n_runs,
        "run_date": dates,
        "total_features": [cfg["n_features"]] * n_runs,
        "missing_rate": [
            round(float(np.clip(base_missing + rng.normal(0, 0.003), 0, 0.1)), 4)
            for _ in range(n_runs)
        ],
        "baseline_missing_rate": [round(float(base_missing), 4)] * n_runs,
        "out_of_range_features": [
            int(rng.choice([0, 0, 0, 0, 1, 1, 2])) for _ in range(n_runs)
        ],
        "schema_valid": [bool(rng.random() > 0.02) for _ in range(n_runs)],
        "record_count": [int(rng.integers(5000, 50000)) for _ in range(n_runs)],
    }

    # -- Distributions (baseline vs current, per feature) -------------------
    n_bins = 10
    distributions: dict[str, dict] = {}
    for feat in features:
        baseline_pct = rng.dirichlet(np.ones(n_bins)).tolist()
        shift = rng.normal(0, csi_base * 0.3, n_bins)
        current_raw = np.array(baseline_pct) + shift
        current_raw = np.clip(current_raw, 0.001, None)
        current_pct = (current_raw / current_raw.sum()).tolist()

        distributions[feat] = {
            "bin_label": [
                f"{i / n_bins:.1f} – {(i + 1) / n_bins:.1f}" for i in range(n_bins)
            ],
            "baseline_pct": [round(v, 4) for v in baseline_pct],
            "current_pct": [round(v, 4) for v in current_pct],
        }

    # -- Feature CSI history (per feature, over time) -----------------------
    feature_csi_history: dict[str, pl.DataFrame] = {}
    for fi, feat in enumerate(features):
        feat_csi_base = float(csi_values[fi]) * 0.6
        hist_vals = np.clip(
            rng.normal(feat_csi_base, max(feat_csi_base * 0.3, 0.005), n_runs),
            0.001,
            0.5,
        )
        if float(csi_values[fi]) > 0.10:
            hist_vals = hist_vals + np.linspace(0, float(csi_values[fi]) * 0.4, n_runs)
            hist_vals = np.clip(hist_vals, 0.001, 0.5)

        feature_csi_history[feat] = pl.DataFrame(
            {
                "model_name": [name] * n_runs,
                "run_date": dates,
                "feature_name": [feat] * n_runs,
                "csi_value": [round(float(v), 4) for v in hist_vals],
                "threshold_warning": [0.10] * n_runs,
                "threshold_critical": [0.20] * n_runs,
            }
        )

    return {
        "score_psi": pl.DataFrame(score_psi_rows),
        "feature_csi": pl.DataFrame(feature_csi_rows),
        "performance": pl.DataFrame(perf_rows),
        "data_quality": pl.DataFrame(dq_rows),
        "distributions": distributions,
        "feature_csi_history": feature_csi_history,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def generate_all_mock_data() -> dict:
    """Build all synthetic monitoring data.  Cached after first call."""
    rng = np.random.default_rng(42)

    # Model registry
    registry = pl.DataFrame(
        {
            "model_name": [c["name"] for c in MODEL_CONFIGS],
            "task": [c["task"] for c in MODEL_CONFIGS],
            "cadence": [c["cadence"] for c in MODEL_CONFIGS],
            "owner": [c["owner"] for c in MODEL_CONFIGS],
            "domain": [c["domain"] for c in MODEL_CONFIGS],
            "n_features": [c["n_features"] for c in MODEL_CONFIGS],
            "baseline_date": [
                datetime.date.fromisoformat(c["baseline_date"]) for c in MODEL_CONFIGS
            ],
            "last_run_date": [
                (
                    _run_dates(c["cadence"], c["baseline_date"])[-1]
                    if _run_dates(c["cadence"], c["baseline_date"])
                    else _TODAY
                )
                for c in MODEL_CONFIGS
            ],
        }
    )

    # Per-model data
    all_score_psi: list[pl.DataFrame] = []
    all_feature_csi: list[pl.DataFrame] = []
    all_performance: list[pl.DataFrame] = []
    all_data_quality: list[pl.DataFrame] = []
    all_distributions: dict[str, dict] = {}
    all_feature_csi_history: dict[str, dict] = {}

    for cfg in MODEL_CONFIGS:
        md = _build_model_data(cfg, rng)
        all_score_psi.append(md["score_psi"])
        all_feature_csi.append(md["feature_csi"])
        all_performance.append(md["performance"])
        all_data_quality.append(md["data_quality"])
        all_distributions[cfg["name"]] = md["distributions"]
        all_feature_csi_history[cfg["name"]] = md["feature_csi_history"]

    return {
        "model_registry": registry,
        "score_psi": pl.concat(all_score_psi),
        "feature_csi": pl.concat(all_feature_csi),
        "performance": pl.concat(all_performance),
        "data_quality": pl.concat(all_data_quality),
        "distributions": all_distributions,
        "feature_csi_history": all_feature_csi_history,
    }


def generate_feature_csi_history(
    model_name: str,
    _run_dates: list,
    feature_name: str,
) -> pl.DataFrame:
    """Return CSI history for one feature."""
    data = generate_all_mock_data()
    hist = data.get("feature_csi_history", {}).get(model_name, {})
    if feature_name in hist:
        return hist[feature_name]
    return pl.DataFrame(
        {"model_name": [], "run_date": [], "feature_name": [], "csi_value": []}
    )


def generate_distribution_data(
    feature_name: str,
    model_name: str | None = None,
    n_bins: int = 10,
) -> pl.DataFrame:
    """Baseline vs current distribution for a feature."""
    data = generate_all_mock_data()
    dists = data.get("distributions", {})

    target_model = model_name
    if target_model is None:
        for mname, feat_dists in dists.items():
            if feature_name in feat_dists:
                target_model = mname
                break

    if target_model and target_model in dists and feature_name in dists[target_model]:
        d = dists[target_model][feature_name]
        n = len(d["bin_label"])
        return pl.DataFrame(
            {
                "feature_name": [feature_name] * n,
                "bin_label": d["bin_label"],
                "baseline_pct": [round(v, 4) for v in d["baseline_pct"]],
                "current_pct": [round(v, 4) for v in d["current_pct"]],
            }
        )

    return pl.DataFrame(
        {"feature_name": [], "bin_label": [], "baseline_pct": [], "current_pct": []}
    )
