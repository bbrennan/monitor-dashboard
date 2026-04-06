"""Model Summary — Single-page deep dive for one model.

WhyLabs/Fiddler-style: large metric panels, scrollable, PSI-first.
Serves the Validation Analyst and Model Owner personas.
"""

import datetime

import plotly.graph_objects as go
import streamlit as st

from monitor_dashboard.data.mock_data import generate_all_mock_data


@st.cache_data
def load_data() -> dict:
    return generate_all_mock_data()


data = load_data()
registry = data["model_registry"]
score_psi = data["score_psi"]
performance = data["performance"]
feature_csi = data["feature_csi"]
dq = data["data_quality"]

today = datetime.date(2026, 4, 6)

# ---------------------------------------------------------------------------
# Model selector (sidebar or session state)
# ---------------------------------------------------------------------------

model_names = registry["model_name"].to_list()
default_model = st.session_state.get("selected_model", model_names[0])
default_idx = model_names.index(default_model) if default_model in model_names else 0

selected = st.sidebar.selectbox("Select Model", model_names, index=default_idx)
st.session_state["selected_model"] = selected

model_info = registry.filter(registry["model_name"] == selected).row(0, named=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

days_since = (
    (today - model_info["last_run_date"]).days if model_info["last_run_date"] else None
)

st.markdown(
    f'<h1 style="color: #333333; margin-bottom: 0;">{selected}</h1>',
    unsafe_allow_html=True,
)
st.caption(
    f'{model_info["cadence"].title()} · Owner: {model_info["owner"]} · '
    f'Domain: {model_info["domain"]} · {model_info["n_features"]} features · '
    f'Baseline: {model_info["baseline_date"]} · '
    f'Last scored: {"today" if days_since == 0 else f"{days_since}d ago"}'
)

st.divider()

# ---------------------------------------------------------------------------
# Panel 1: Score Health (PSI)
# ---------------------------------------------------------------------------

st.markdown("## 📊 Score Health")

model_psi = score_psi.filter(score_psi["model_name"] == selected).sort("run_date")
latest_psi = model_psi.row(-1, named=True) if len(model_psi) > 0 else None

if latest_psi:
    psi_val = latest_psi["value"]
    if psi_val >= 0.20:
        status_text = "CRITICAL"
        status_color = "#EB0A1E"
    elif psi_val >= 0.10:
        status_text = "WARNING"
        status_color = "#F5A623"
    else:
        status_text = "STABLE"
        status_color = "#2E7D32"

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.metric("Score PSI", f"{psi_val:.4f}")
    with col2:
        st.markdown(
            f'<div style="background-color: {status_color}; color: white; '
            f"padding: 8px 16px; border-radius: 4px; text-align: center; "
            f'font-weight: 600; font-size: 18px; margin-top: 28px;">'
            f"{status_text}</div>",
            unsafe_allow_html=True,
        )
    with col3:
        # PSI trend chart
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=model_psi["run_date"].to_list(),
                y=model_psi["value"].to_list(),
                mode="lines+markers",
                line=dict(color="#333333", width=2),
                marker=dict(size=3),
                name="Score PSI",
            )
        )
        fig.add_hline(
            y=0.10,
            line_dash="dash",
            line_color="#F5A623",
            annotation_text="Warning (0.10)",
        )
        fig.add_hline(
            y=0.20,
            line_dash="dash",
            line_color="#EB0A1E",
            annotation_text="Critical (0.20)",
        )
        fig.update_layout(
            height=200,
            margin=dict(l=40, r=20, t=10, b=30),
            yaxis_title="PSI",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            yaxis=dict(gridcolor="#E5E5E5"),
            xaxis=dict(gridcolor="#E5E5E5"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# Panel 2: Model Performance
# ---------------------------------------------------------------------------

st.markdown("## 📈 Performance")

model_perf = performance.filter(performance["model_name"] == selected).sort("run_date")
task = (
    model_info.get("task", "classification")
    if isinstance(model_info, dict)
    else "classification"
)

# Determine which metrics this model has
if task == "classification":
    metric_names = ["roc_auc", "ks_statistic", "gini"]
    metric_labels = {"roc_auc": "AUC", "ks_statistic": "KS Statistic", "gini": "Gini"}
    primary_metric = "roc_auc"
    primary_label = "AUC"
else:
    metric_names = ["r_squared", "rmse", "mae"]
    metric_labels = {"r_squared": "R²", "rmse": "RMSE", "mae": "MAE"}
    primary_metric = "r_squared"
    primary_label = "R²"

if len(model_perf) > 0:
    # Latest metrics
    latest_date = model_perf["run_date"].max()
    latest_metrics = model_perf.filter(model_perf["run_date"] == latest_date)

    cols = st.columns(3)
    for i, metric_name in enumerate(metric_names):
        metric_row = latest_metrics.filter(latest_metrics["metric_name"] == metric_name)
        if len(metric_row) > 0:
            row = metric_row.row(0, named=True)
            label = metric_labels[metric_name]
            badge = " *(estimated)*" if row["is_estimated"] else " *(confirmed)*"
            cols[i].metric(f"{label}{badge}", f'{row["value"]:.4f}')

    # Actuals staleness
    confirmed = model_perf.filter(~model_perf["is_estimated"])
    if len(confirmed) > 0:
        last_actuals = confirmed["actuals_through"].max()
        if last_actuals:
            staleness = (today - last_actuals).days
            st.info(
                f"📅 Actuals available through **{last_actuals}** ({staleness} days ago)"
            )
    else:
        st.warning("⚠️ No confirmed actuals available yet — all metrics are estimates")

    # Performance trend (primary metric)
    trend_series = model_perf.filter(model_perf["metric_name"] == primary_metric)
    est_series = trend_series.filter(trend_series["is_estimated"])
    conf_series = trend_series.filter(~trend_series["is_estimated"])

    fig_perf = go.Figure()
    if len(conf_series) > 0:
        fig_perf.add_trace(
            go.Scatter(
                x=conf_series["run_date"].to_list(),
                y=conf_series["value"].to_list(),
                mode="lines+markers",
                line=dict(color="#333333", width=2),
                marker=dict(size=4),
                name=f"{primary_label} (confirmed)",
            )
        )
    if len(est_series) > 0:
        fig_perf.add_trace(
            go.Scatter(
                x=est_series["run_date"].to_list(),
                y=est_series["value"].to_list(),
                mode="lines+markers",
                line=dict(color="#999999", width=2, dash="dot"),
                marker=dict(size=4, symbol="diamond-open"),
                name=f"{primary_label} (estimated)",
            )
        )
    fig_perf.update_layout(
        height=250,
        margin=dict(l=40, r=20, t=10, b=30),
        yaxis_title=primary_label,
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(gridcolor="#E5E5E5"),
        xaxis=dict(gridcolor="#E5E5E5"),
    )
    st.plotly_chart(fig_perf, width="stretch", config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# Panel 3: Feature Drift (CSI)
# ---------------------------------------------------------------------------

st.markdown("## 📋 Feature Drift (CSI)")

model_csi = feature_csi.filter(feature_csi["model_name"] == selected).sort(
    "csi_value", descending=True
)

if len(model_csi) > 0:
    n_critical = len(model_csi.filter(model_csi["csi_value"] >= 0.20))
    n_warning = len(
        model_csi.filter(
            (model_csi["csi_value"] >= 0.10) & (model_csi["csi_value"] < 0.20)
        )
    )
    n_stable = len(model_csi.filter(model_csi["csi_value"] < 0.10))

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Critical", n_critical)
    c2.metric("🟡 Warning", n_warning)
    c3.metric("🟢 Stable", n_stable)

    # Top drifted features bar chart
    top_n = min(15, len(model_csi))
    top_features = model_csi.head(top_n)

    colors = []
    for val in top_features["csi_value"].to_list():
        if val >= 0.20:
            colors.append("#EB0A1E")
        elif val >= 0.10:
            colors.append("#F5A623")
        else:
            colors.append("#2E7D32")

    fig_csi = go.Figure(
        go.Bar(
            y=top_features["feature_name"].to_list()[::-1],
            x=top_features["csi_value"].to_list()[::-1],
            orientation="h",
            marker_color=colors[::-1],
        )
    )
    fig_csi.add_vline(
        x=0.10, line_dash="dash", line_color="#F5A623", annotation_text="Warning"
    )
    fig_csi.add_vline(
        x=0.20, line_dash="dash", line_color="#EB0A1E", annotation_text="Critical"
    )
    fig_csi.update_layout(
        height=max(250, top_n * 25),
        margin=dict(l=150, r=20, t=10, b=30),
        xaxis_title="CSI",
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        yaxis=dict(gridcolor="#E5E5E5"),
        xaxis=dict(gridcolor="#E5E5E5"),
    )
    st.plotly_chart(fig_csi, width="stretch", config={"displayModeBar": False})

    if st.button("🔍 Open Feature Monitor →"):
        st.switch_page("pages/3_feature_monitor.py")

st.divider()

# ---------------------------------------------------------------------------
# Panel 4: Data Quality
# ---------------------------------------------------------------------------

st.markdown("## 🛡️ Data Quality")

model_dq = dq.filter(dq["model_name"] == selected).sort("run_date")

if len(model_dq) > 0:
    latest_dq = model_dq.row(-1, named=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Missing Rate",
        f'{latest_dq["missing_rate"]:.3%}',
        delta=f'{latest_dq["missing_rate"] - latest_dq["baseline_missing_rate"]:.3%}',
        delta_color="inverse",
    )
    c2.metric("Out-of-Range Features", latest_dq["out_of_range_features"])
    c3.metric("Schema Valid", "✅" if latest_dq["schema_valid"] else "❌")
    c4.metric("Record Count", f'{latest_dq["record_count"]:,}')

    # Missing rate trend
    fig_dq = go.Figure()
    fig_dq.add_trace(
        go.Scatter(
            x=model_dq["run_date"].to_list(),
            y=model_dq["missing_rate"].to_list(),
            mode="lines",
            line=dict(color="#333333", width=2),
            name="Missing Rate",
        )
    )
    fig_dq.add_hline(
        y=latest_dq["baseline_missing_rate"],
        line_dash="dash",
        line_color="#58595B",
        annotation_text="Baseline",
    )
    fig_dq.update_layout(
        height=200,
        margin=dict(l=40, r=20, t=10, b=30),
        yaxis_title="Missing Rate",
        yaxis_tickformat=".2%",
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        yaxis=dict(gridcolor="#E5E5E5"),
        xaxis=dict(gridcolor="#E5E5E5"),
    )
    st.plotly_chart(fig_dq, width="stretch", config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# Panel 5: Model Info
# ---------------------------------------------------------------------------

st.markdown("## ℹ️ Model Information")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f"""
    | Field | Value |
    |-------|-------|
    | **Model Name** | {model_info["model_name"]} |
    | **Owner** | {model_info["owner"]} |
    | **Domain** | {model_info["domain"]} |
    | **Scoring Cadence** | {model_info["cadence"].title()} |
    """
    )
with c2:
    st.markdown(
        f"""
    | Field | Value |
    |-------|-------|
    | **Features** | {model_info["n_features"]} |
    | **Baseline Date** | {model_info["baseline_date"]} |
    | **Last Scored** | {model_info["last_run_date"]} |
    | **Days Since Last Run** | {days_since} |
    """
    )
