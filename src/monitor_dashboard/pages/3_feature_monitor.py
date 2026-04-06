"""Feature Monitor — Feature-level drift investigation.

Ranked list of all features by CSI (worst-first), with drill-down
to distribution overlays, bin-level contributions, and DQ timeline.
"""

import datetime

import plotly.graph_objects as go
import streamlit as st

from monitor_dashboard.data.mock_data import (
    generate_all_mock_data,
    generate_feature_csi_history,
    generate_distribution_data,
)


@st.cache_data
def load_data() -> dict:
    return generate_all_mock_data()


data = load_data()
registry = data["model_registry"]
feature_csi = data["feature_csi"]

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
    f'<h1 style="color: #333333; margin-bottom: 0;">Feature Monitor — {selected}</h1>',
    unsafe_allow_html=True,
)
st.caption(
    f'{model_info["n_features"]} features · {model_info["cadence"].title()} scoring'
)

st.divider()

# ---------------------------------------------------------------------------
# Feature CSI ranking
# ---------------------------------------------------------------------------

model_csi = feature_csi.filter(feature_csi["model_name"] == selected).sort(
    "csi_value", descending=True
)

if len(model_csi) == 0:
    st.warning("No feature CSI data available for this model.")
    st.stop()

n_critical = len(model_csi.filter(model_csi["csi_value"] >= 0.20))
n_warning = len(
    model_csi.filter((model_csi["csi_value"] >= 0.10) & (model_csi["csi_value"] < 0.20))
)
n_stable = len(model_csi.filter(model_csi["csi_value"] < 0.10))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Features", len(model_csi))
c2.metric("🔴 Critical", n_critical)
c3.metric("🟡 Warning", n_warning)
c4.metric("🟢 Stable", n_stable)

st.divider()

# ---------------------------------------------------------------------------
# Feature ranking bar chart
# ---------------------------------------------------------------------------

st.markdown("### Feature Drift Ranking (CSI)")

top_n = min(20, len(model_csi))
top_features = model_csi.head(top_n)

colors = []
for val in top_features["csi_value"].to_list():
    if val >= 0.20:
        colors.append("#EB0A1E")
    elif val >= 0.10:
        colors.append("#F5A623")
    else:
        colors.append("#2E7D32")

csi_text = [f"{v:.4f}" for v in top_features["csi_value"].to_list()[::-1]]
fig_rank = go.Figure(
    go.Bar(
        y=top_features["feature_name"].to_list()[::-1],
        x=top_features["csi_value"].to_list()[::-1],
        orientation="h",
        marker_color=colors[::-1],
        textposition="outside",
    )
)
fig_rank.update_traces(text=csi_text)
fig_rank.add_vline(x=0.10, line_dash="dash", line_color="#F5A623")
fig_rank.add_vline(x=0.20, line_dash="dash", line_color="#EB0A1E")
fig_rank.update_layout(
    height=max(350, top_n * 28),
    margin=dict(l=180, r=60, t=10, b=30),
    xaxis_title="CSI",
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    yaxis=dict(gridcolor="#E5E5E5"),
    xaxis=dict(gridcolor="#E5E5E5"),
)
st.plotly_chart(fig_rank, width="stretch", config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# Feature drill-down
# ---------------------------------------------------------------------------

st.markdown("### Feature Deep Dive")

feature_list = model_csi["feature_name"].to_list()
selected_feature = st.selectbox("Select Feature", feature_list)

if selected_feature:
    feature_row = model_csi.filter(model_csi["feature_name"] == selected_feature).row(
        0, named=True
    )
    csi_val = feature_row["csi_value"]

    if csi_val >= 0.20:
        badge_color = "#EB0A1E"
        badge_text = "CRITICAL"
    elif csi_val >= 0.10:
        badge_color = "#F5A623"
        badge_text = "WARNING"
    else:
        badge_color = "#2E7D32"
        badge_text = "STABLE"

    st.markdown(
        f"**{selected_feature}** — CSI: `{csi_val:.4f}` "
        f'<span style="background-color:{badge_color}; color:white; padding:2px 8px; '
        f'border-radius:3px; font-size:12px;">{badge_text}</span>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["Distribution Overlay", "CSI History", "Summary Stats"])

    # ---- Tab 1: Distribution Overlay ----
    with tab1:
        dist_data = generate_distribution_data(selected_feature, model_name=selected)

        fig_dist = go.Figure()
        fig_dist.add_trace(
            go.Bar(
                x=dist_data["bin_label"].to_list(),
                y=dist_data["baseline_pct"].to_list(),
                name="Baseline",
                marker_color="#58595B",
                opacity=0.7,
            )
        )
        fig_dist.add_trace(
            go.Bar(
                x=dist_data["bin_label"].to_list(),
                y=dist_data["current_pct"].to_list(),
                name="Current",
                marker_color="#EB0A1E",
                opacity=0.7,
            )
        )
        fig_dist.update_layout(
            barmode="group",
            height=300,
            margin=dict(l=40, r=20, t=30, b=40),
            xaxis_title="Bin",
            yaxis_title="Proportion",
            yaxis_tickformat=".1%",
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            yaxis=dict(gridcolor="#E5E5E5"),
            xaxis=dict(gridcolor="#E5E5E5"),
        )
        st.plotly_chart(fig_dist, width="stretch", config={"displayModeBar": False})

        # Bin-level CSI contribution
        st.caption("Bin-level CSI contribution")
        baseline = dist_data["baseline_pct"].to_list()
        current = dist_data["current_pct"].to_list()
        bin_labels = dist_data["bin_label"].to_list()

        contributions = []
        for b, c in zip(baseline, current):
            if b > 0 and c > 0:
                contributions.append((c - b) * (c / b if b > 0 else 0))
            else:
                contributions.append(0)

        fig_contrib = go.Figure(
            go.Bar(
                x=bin_labels,
                y=contributions,
                marker_color=["#EB0A1E" if c > 0 else "#2E7D32" for c in contributions],
            )
        )
        fig_contrib.update_layout(
            height=200,
            margin=dict(l=40, r=20, t=10, b=40),
            xaxis_title="Bin",
            yaxis_title="CSI Contribution",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            yaxis=dict(gridcolor="#E5E5E5"),
            xaxis=dict(gridcolor="#E5E5E5"),
        )
        st.plotly_chart(fig_contrib, width="stretch", config={"displayModeBar": False})

    # ---- Tab 2: CSI History ----
    with tab2:
        # CSI history from cached data
        csi_hist = generate_feature_csi_history(selected, [], selected_feature)

        fig_hist = go.Figure()
        fig_hist.add_trace(
            go.Scatter(
                x=csi_hist["run_date"].to_list(),
                y=csi_hist["csi_value"].to_list(),
                mode="lines+markers",
                line=dict(color="#333333", width=2),
                marker=dict(size=3),
                name="CSI",
            )
        )
        fig_hist.add_hline(
            y=0.10, line_dash="dash", line_color="#F5A623", annotation_text="Warning"
        )
        fig_hist.add_hline(
            y=0.20, line_dash="dash", line_color="#EB0A1E", annotation_text="Critical"
        )
        fig_hist.update_layout(
            height=300,
            margin=dict(l=40, r=20, t=10, b=30),
            xaxis_title="Date",
            yaxis_title="CSI",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            yaxis=dict(gridcolor="#E5E5E5"),
            xaxis=dict(gridcolor="#E5E5E5"),
        )
        st.plotly_chart(fig_hist, width="stretch", config={"displayModeBar": False})

    # ---- Tab 3: Summary Stats ----
    with tab3:
        st.markdown("Summary statistics comparison (baseline vs current)")

        # Generate some plausible summary stats
        import numpy as np

        np.random.seed(hash(selected_feature) % 2**31)
        baseline_mean = np.random.uniform(0.1, 0.9)
        baseline_std = np.random.uniform(0.05, 0.2)
        current_mean = baseline_mean + np.random.normal(0, 0.03)
        current_std = baseline_std + np.random.normal(0, 0.02)

        stats_df = {
            "Statistic": [
                "Mean",
                "Std Dev",
                "Median",
                "Min",
                "Max",
                "25th Pctl",
                "75th Pctl",
            ],
            "Baseline": [
                f"{baseline_mean:.4f}",
                f"{baseline_std:.4f}",
                f"{baseline_mean + np.random.normal(0, 0.01):.4f}",
                f"{max(0, baseline_mean - 3*baseline_std):.4f}",
                f"{baseline_mean + 3*baseline_std:.4f}",
                f"{baseline_mean - 0.67*baseline_std:.4f}",
                f"{baseline_mean + 0.67*baseline_std:.4f}",
            ],
            "Current": [
                f"{current_mean:.4f}",
                f"{current_std:.4f}",
                f"{current_mean + np.random.normal(0, 0.01):.4f}",
                f"{max(0, current_mean - 3*current_std):.4f}",
                f"{current_mean + 3*current_std:.4f}",
                f"{current_mean - 0.67*current_std:.4f}",
                f"{current_mean + 0.67*current_std:.4f}",
            ],
        }
        st.dataframe(stats_df, width="stretch", hide_index=True)
