"""Portfolio Overview — Landing page.

CRO/VP view: scan the entire model portfolio in under a minute.
Problems float to the top. Stable models collapse.
"""

import datetime

import plotly.graph_objects as go
import streamlit as st

from monitor_dashboard.data.mock_data import generate_all_mock_data


@st.cache_data
def load_data() -> dict:
    """Load and cache synthetic monitoring data."""
    return generate_all_mock_data()


data = load_data()
registry = data["model_registry"]
score_psi = data["score_psi"]
performance = data["performance"]
dq = data["data_quality"]

today = datetime.date(2026, 4, 6)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<h1 style="color: #333333; margin-bottom: 0;">Model Portfolio Health</h1>',
    unsafe_allow_html=True,
)
st.caption(
    f"As of {today.strftime('%B %d, %Y')} · Toyota Financial Services · Risk Data Science"
)

st.divider()

# ---------------------------------------------------------------------------
# Build model health summary
# ---------------------------------------------------------------------------

model_health = []
for row_reg in registry.iter_rows(named=True):
    name = row_reg["model_name"]

    # Latest PSI
    model_psi = score_psi.filter(score_psi["model_name"] == name).sort("run_date")
    latest_psi = model_psi.row(-1, named=True) if len(model_psi) > 0 else None

    # Latest performance — pick primary metric based on task
    task = row_reg["task"] if "task" in row_reg else "classification"
    primary_metric = "roc_auc" if task == "classification" else "r_squared"
    model_perf = performance.filter(
        (performance["model_name"] == name)
        & (performance["metric_name"] == primary_metric)
    ).sort("run_date")
    latest_auc = model_perf.row(-1, named=True) if len(model_perf) > 0 else None

    # Latest data quality
    model_dq = dq.filter(dq["model_name"] == name).sort("run_date")
    latest_dq = model_dq.row(-1, named=True) if len(model_dq) > 0 else None

    psi_val = latest_psi["value"] if latest_psi else 0
    auc_val = latest_auc["value"] if latest_auc else 0
    is_estimated = latest_auc["is_estimated"] if latest_auc else True
    task = (
        row_reg.get("task", "classification")
        if isinstance(row_reg, dict)
        else "classification"
    )

    # Determine status
    if psi_val >= 0.20:
        status = "🔴 Critical"
        sort_order = 0
    elif psi_val >= 0.10:
        status = "🟡 Warning"
        sort_order = 1
    else:
        status = "🟢 Stable"
        sort_order = 2

    days_since_run = (
        (today - row_reg["last_run_date"]).days if row_reg["last_run_date"] else None
    )

    perf_label = "AUC" if task == "classification" else "R\u00b2"

    model_health.append(
        {
            "name": name,
            "task": task,
            "status": status,
            "sort_order": sort_order,
            "psi": psi_val,
            "auc": auc_val,
            "perf_label": perf_label,
            "is_estimated": is_estimated,
            "cadence": row_reg["cadence"],
            "owner": row_reg["owner"],
            "domain": row_reg["domain"],
            "last_run": row_reg["last_run_date"],
            "days_since_run": days_since_run,
            "missing_rate": latest_dq["missing_rate"] if latest_dq else 0,
            "dq_issues": int(latest_dq["out_of_range_features"]) if latest_dq else 0,
            "psi_history": model_psi["value"].to_list() if len(model_psi) > 0 else [],
            "psi_dates": model_psi["run_date"].to_list() if len(model_psi) > 0 else [],
        }
    )

model_health.sort(key=lambda x: (x["sort_order"], -x["psi"]))

# ---------------------------------------------------------------------------
# Portfolio summary bar
# ---------------------------------------------------------------------------

n_critical = sum(1 for m in model_health if m["sort_order"] == 0)
n_warning = sum(1 for m in model_health if m["sort_order"] == 1)
n_stable = sum(1 for m in model_health if m["sort_order"] == 2)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Models", len(model_health))
col2.metric("🟢 Stable", n_stable)
col3.metric("🟡 Warning", n_warning)
col4.metric("🔴 Critical", n_critical)

# Visual health bar
bar_segments = (
    ["#2E7D32"] * n_stable + ["#F5A623"] * n_warning + ["#EB0A1E"] * n_critical
)
if bar_segments:
    fig_bar = go.Figure(
        go.Bar(
            x=[1] * len(bar_segments),
            y=[""] * len(bar_segments),
            orientation="h",
            marker_color=bar_segments,
            showlegend=False,
        )
    )
    fig_bar.update_layout(
        barmode="stack",
        height=40,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_bar, width="stretch", config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Needs Attention section
# ---------------------------------------------------------------------------

attention_models = [m for m in model_health if m["sort_order"] < 2]
stable_models = [m for m in model_health if m["sort_order"] == 2]

if attention_models:
    st.markdown("### ⚠️ Needs Attention")

    for model in attention_models:
        status_color = "#EB0A1E" if model["sort_order"] == 0 else "#F5A623"
        est_badge = " *(est.)*" if model["is_estimated"] else ""

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 2])

            with c1:
                st.markdown(
                    f'<span style="color: {status_color}; font-size: 20px; font-weight: 600;">'
                    f'{model["status"].split(" ")[0]} {model["name"]}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f'{model["cadence"].title()} · {model["owner"]} · {model["domain"]} · '
                    f'Last scored: {model["days_since_run"]}d ago'
                )

            with c2:
                st.metric("Score PSI", f'{model["psi"]:.3f}')

            with c3:
                st.metric(f"AUC{est_badge}", f'{model["auc"]:.3f}')

            with c4:
                st.metric("DQ Issues", model["dq_issues"])

            with c5:
                # Mini sparkline of PSI trend
                if model["psi_history"]:
                    fig_spark = go.Figure(
                        go.Scatter(
                            x=model["psi_dates"][-30:],
                            y=model["psi_history"][-30:],
                            mode="lines",
                            line=dict(color=status_color, width=2),
                            showlegend=False,
                        )
                    )
                    # Threshold line
                    fig_spark.add_hline(
                        y=0.10, line_dash="dot", line_color="#F5A623", line_width=1
                    )
                    fig_spark.add_hline(
                        y=0.20, line_dash="dot", line_color="#EB0A1E", line_width=1
                    )
                    fig_spark.update_layout(
                        height=70,
                        margin=dict(l=0, r=0, t=5, b=5),
                        xaxis=dict(
                            showticklabels=False, showgrid=False, zeroline=False
                        ),
                        yaxis=dict(
                            showticklabels=False, showgrid=False, zeroline=False
                        ),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                    )
                    st.plotly_chart(
                        fig_spark,
                        width="stretch",
                        config={"displayModeBar": False},
                    )

            if st.button(
                "View Details →",
                key=f"detail_{model['name']}",
                width="content",
            ):
                st.session_state["selected_model"] = model["name"]
                st.switch_page("pages/2_model_summary.py")

# ---------------------------------------------------------------------------
# Stable models (collapsed)
# ---------------------------------------------------------------------------

if stable_models:
    with st.expander(f"🟢 All Models Stable ({len(stable_models)})", expanded=False):
        for model in stable_models:
            est_badge = " *(est.)*" if model["is_estimated"] else ""
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 2])

            with c1:
                st.markdown(f'**{model["name"]}**')
                st.caption(
                    f'{model["cadence"].title()} · {model["owner"]} · '
                    f'Last: {model["days_since_run"]}d ago'
                )
            with c2:
                st.metric("PSI", f'{model["psi"]:.3f}')
            with c3:
                st.metric(f'{model["perf_label"]}{est_badge}', f'{model["auc"]:.3f}')
            with c4:
                st.metric(
                    "DQ",
                    f'{"OK" if model["dq_issues"] == 0 else str(model["dq_issues"]) + " issues"}',
                )
            with c5:
                if st.button("View →", key=f"stable_{model['name']}"):
                    st.session_state["selected_model"] = model["name"]
                    st.switch_page("pages/2_model_summary.py")

            st.divider()

# ---------------------------------------------------------------------------
# Recent Events feed
# ---------------------------------------------------------------------------

st.markdown("### 📋 Recent Events")

events = [
    {
        "time": "Today 09:12",
        "model": "Auto Loan Default",
        "msg": "Score PSI crossed critical threshold (0.24)",
        "severity": "🔴",
    },
    {
        "time": "Today 09:12",
        "model": "Auto Loan Default",
        "msg": "income_ratio CSI exceeded 0.25 — critical drift",
        "severity": "🔴",
    },
    {
        "time": "Today 09:12",
        "model": "Auto Loan Default",
        "msg": "debt_to_income CSI exceeded 0.20 — critical drift",
        "severity": "🔴",
    },
    {
        "time": "Yesterday",
        "model": "Fraud Detection",
        "msg": "Score PSI approaching warning threshold (0.11)",
        "severity": "🟡",
    },
    {
        "time": "Yesterday",
        "model": "Credit Line Increase",
        "msg": "AUC estimate declined 0.03 over last 4 weeks",
        "severity": "🟡",
    },
    {
        "time": "3 days ago",
        "model": "All models",
        "msg": "Weekly refresh completed — 7 daily, 3 weekly models scored",
        "severity": "🟢",
    },
    {
        "time": "1 week ago",
        "model": "Lease Residual Value",
        "msg": "Monthly scoring completed — all metrics stable",
        "severity": "🟢",
    },
]

for event in events:
    st.markdown(
        f'{event["severity"]}  **{event["time"]}** · {event["model"]} — {event["msg"]}'
    )
