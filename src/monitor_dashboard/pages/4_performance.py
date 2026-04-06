"""Performance Deep Dive — Model performance tracking over time.

Shows estimated vs confirmed metrics, actuals horizon, AUC/KS/Gini trends,
and backtesting comparison. Handles delayed actuals prominently.
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
performance = data["performance"]
score_psi = data["score_psi"]

today = datetime.date(2026, 4, 6)

# ---------------------------------------------------------------------------
# Model selector
# ---------------------------------------------------------------------------

model_names = registry["model_name"].to_list()
default_model = st.session_state.get("selected_model", model_names[0])
default_idx = model_names.index(default_model) if default_model in model_names else 0

selected = st.sidebar.selectbox("Select Model", model_names, index=default_idx)
st.session_state["selected_model"] = selected

model_info = registry.filter(registry["model_name"] == selected).row(0, named=True)

st.markdown(
    f'<h1 style="color: #333333; margin-bottom: 0;">Performance — {selected}</h1>',
    unsafe_allow_html=True,
)
st.caption(f'{model_info["cadence"].title()} · Owner: {model_info["owner"]}')

st.divider()

# ---------------------------------------------------------------------------
# Filter model performance data
# ---------------------------------------------------------------------------

model_perf = performance.filter(performance["model_name"] == selected).sort("run_date")

if len(model_perf) == 0:
    st.warning("No performance data available for this model.")
    st.stop()

# Determine task type from available metrics
task = (
    model_info.get("task", "classification")
    if isinstance(model_info, dict)
    else "classification"
)
if task == "classification":
    metric_names = ["roc_auc", "ks_statistic", "gini"]
    metric_labels = {"roc_auc": "AUC", "ks_statistic": "KS Statistic", "gini": "Gini"}
    primary_metric = "roc_auc"
else:
    metric_names = ["r_squared", "rmse", "mae"]
    metric_labels = {"r_squared": "R²", "rmse": "RMSE", "mae": "MAE"}
    primary_metric = "r_squared"

# ---------------------------------------------------------------------------
# Actuals Horizon
# ---------------------------------------------------------------------------

confirmed = model_perf.filter(~model_perf["is_estimated"])
estimated = model_perf.filter(model_perf["is_estimated"])

if len(confirmed) > 0:
    last_actuals = confirmed["actuals_through"].max()
    last_confirmed_date = confirmed["run_date"].max()
    staleness = (today - last_actuals).days if last_actuals else None
    n_estimated_runs = len(estimated["run_date"].unique())

    col1, col2, col3 = st.columns(3)
    col1.metric("Actuals Through", str(last_actuals) if last_actuals else "N/A")
    col2.metric("Actuals Staleness", f"{staleness}d" if staleness else "N/A")
    col3.metric("Estimated Runs (no actuals)", n_estimated_runs)

    if staleness and staleness > 60:
        st.warning(
            f"⚠️ Actuals are **{staleness} days stale**. "
            f"Performance metrics after {last_confirmed_date} are estimates only."
        )
    elif staleness and staleness > 30:
        st.info(
            f"📅 Actuals lag: {staleness} days. "
            f"Recent metrics are estimates pending actuals arrival."
        )
else:
    st.error(
        "🚫 No confirmed actuals available for this model. "
        "All displayed metrics are **estimates** (CPBE / RBE proxies)."
    )

st.divider()

# ---------------------------------------------------------------------------
# Latest Performance Snapshot
# ---------------------------------------------------------------------------

st.markdown("### Current Performance Snapshot")

latest_date = model_perf["run_date"].max()
latest = model_perf.filter(model_perf["run_date"] == latest_date)

cols = st.columns(3)
for i, mn in enumerate(metric_names):
    metric_row = latest.filter(latest["metric_name"] == mn)
    if len(metric_row) > 0:
        row = metric_row.row(0, named=True)
        label = metric_labels[mn]
        est_badge = "🔮 Estimated" if row["is_estimated"] else "✅ Confirmed"
        cols[i].metric(f"{label}", f'{row["value"]:.4f}')
        cols[i].caption(est_badge)

st.divider()

# ---------------------------------------------------------------------------
# Performance Trends — multi-metric
# ---------------------------------------------------------------------------

st.markdown("### Performance Trends")

metric_choice = st.radio(
    "Metric",
    metric_names,
    format_func=lambda x: metric_labels.get(x, x),
    horizontal=True,
)

series = model_perf.filter(model_perf["metric_name"] == metric_choice)
conf_s = series.filter(~series["is_estimated"])
est_s = series.filter(series["is_estimated"])

fig = go.Figure()

if len(conf_s) > 0:
    fig.add_trace(
        go.Scatter(
            x=conf_s["run_date"].to_list(),
            y=conf_s["value"].to_list(),
            mode="lines+markers",
            line=dict(color="#333333", width=2),
            marker=dict(size=5),
            name="Confirmed (actuals)",
        )
    )

if len(est_s) > 0:
    fig.add_trace(
        go.Scatter(
            x=est_s["run_date"].to_list(),
            y=est_s["value"].to_list(),
            mode="lines+markers",
            line=dict(color="#EB0A1E", width=2, dash="dot"),
            marker=dict(size=5, symbol="diamond-open"),
            name="Estimated (no actuals)",
        )
    )

    # Shade the estimated region
    if len(est_s) > 1:
        x_est = est_s["run_date"].to_list()
        y_est = est_s["value"].to_list()
        fig.add_vrect(
            x0=x_est[0],
            x1=x_est[-1],
            fillcolor="#EB0A1E",
            opacity=0.05,
            line_width=0,
            annotation_text="Estimates",
            annotation_position="top left",
        )

# Baseline reference
baseline_row = series.head(5)
if len(baseline_row) > 0:
    baseline_val = baseline_row["value"].mean()
    fig.add_hline(
        y=baseline_val,
        line_dash="dash",
        line_color="#58595B",
        annotation_text=f"Early avg: {baseline_val:.3f}",
    )

label_map = metric_labels
fig.update_layout(
    height=350,
    margin=dict(l=40, r=20, t=20, b=30),
    yaxis_title=label_map.get(metric_choice, metric_choice),
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis=dict(gridcolor="#E5E5E5"),
    xaxis=dict(gridcolor="#E5E5E5"),
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# All Metrics Table (recent runs)
# ---------------------------------------------------------------------------

st.markdown("### Recent Scoring Runs")

recent_dates = model_perf["run_date"].unique().sort(descending=True).head(10).to_list()
recent = model_perf.filter(model_perf["run_date"].is_in(recent_dates))

# Pivot for display
pivot_rows = []
for date in sorted(recent_dates, reverse=True):
    date_data = recent.filter(recent["run_date"] == date)
    row: dict = {"Date": str(date)}
    is_est = False
    for mn in metric_names:
        m = date_data.filter(date_data["metric_name"] == mn)
        if len(m) > 0:
            r = m.row(0, named=True)
            row[metric_labels.get(mn, mn)] = f'{r["value"]:.4f}'
            is_est = r["is_estimated"]
    row["Status"] = "🔮 Estimated" if is_est else "✅ Confirmed"
    pivot_rows.append(row)

st.dataframe(pivot_rows, width="stretch", hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# PSI vs Performance overlay
# ---------------------------------------------------------------------------

st.markdown("### Drift × Performance Correlation")
st.caption("Does score drift predict performance degradation?")

model_psi = score_psi.filter(score_psi["model_name"] == selected).sort("run_date")
primary_series = model_perf.filter(model_perf["metric_name"] == primary_metric).sort(
    "run_date"
)
primary_label = metric_labels.get(primary_metric, primary_metric)

if len(model_psi) > 0 and len(primary_series) > 0:
    fig_dual = go.Figure()

    fig_dual.add_trace(
        go.Scatter(
            x=model_psi["run_date"].to_list(),
            y=model_psi["value"].to_list(),
            mode="lines",
            line=dict(color="#F5A623", width=2),
            name="Score PSI",
            yaxis="y",
        )
    )

    fig_dual.add_trace(
        go.Scatter(
            x=primary_series["run_date"].to_list(),
            y=primary_series["value"].to_list(),
            mode="lines",
            line=dict(color="#333333", width=2),
            name=primary_label,
            yaxis="y2",
        )
    )

    fig_dual.update_layout(
        height=300,
        margin=dict(l=60, r=60, t=20, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title="PSI",
            gridcolor="#E5E5E5",
            side="left",
        ),
        yaxis2=dict(
            title=primary_label,
            overlaying="y",
            side="right",
            gridcolor="#E5E5E5",
        ),
        xaxis=dict(gridcolor="#E5E5E5"),
    )
    st.plotly_chart(fig_dual, width="stretch", config={"displayModeBar": False})
