"""TFS Model Monitoring Dashboard — Streamlit mockup.

Design exploration prototype. Uses synthetic data only.
"""

from pathlib import Path

import streamlit as st

_ASSETS = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="TFS Model Monitor",
    page_icon=str(_ASSETS / "favicon.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Load Material Symbols icon font ------------------------------------------
st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family='
    'Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />',
    unsafe_allow_html=True,
)

# -- Professional TFS Styling -------------------------------------------------
_logo_svg = (_ASSETS / "logo.svg").read_text()

st.markdown(
    f"""
<style>
    /* ── Brand tokens ────────────────────────────────────── */
    :root {{
        --tfs-red: #EB0A1E;
        --tfs-dark: #1A1A1A;
        --tfs-dark-2: #2A2A2A;
        --tfs-gray: #58595B;
        --tfs-light: #D1D3D4;
        --tfs-border: #E5E5E5;
        --tfs-surface: #FAFAFA;
        --tfs-white: #FFFFFF;
        --tfs-green: #2E7D32;
        --tfs-amber: #F5A623;
        --tfs-text: #333333;
        --tfs-text-muted: #888888;
    }}

    /* ── Typography ──────────────────────────────────────── */
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}

    /* ── Top header bar ──────────────────────────────────── */
    header[data-testid="stHeader"] {{
        background-color: var(--tfs-dark) !important;
        border-bottom: 2px solid var(--tfs-red);
    }}

    /* ── Sidebar — dark professional theme ───────────────── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--tfs-dark) 0%, var(--tfs-dark-2) 100%);
        border-right: none;
        box-shadow: 2px 0 8px rgba(0,0,0,0.15);
    }}

    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0rem;
    }}

    /* Sidebar — all text white by default */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p {{
        color: rgba(255,255,255,0.75) !important;
    }}

    /* Sidebar nav links */
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] a span,
    section[data-testid="stSidebar"] a p,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] p,
    section[data-testid="stSidebar"] nav a,
    section[data-testid="stSidebar"] nav a span,
    section[data-testid="stSidebar"] nav a p {{
        color: rgba(255,255,255,0.75) !important;
        transition: all 0.15s ease;
    }}

    section[data-testid="stSidebar"] a:hover,
    section[data-testid="stSidebar"] a:hover span,
    section[data-testid="stSidebar"] a:hover p {{
        color: #FFFFFF !important;
        background-color: rgba(255,255,255,0.08);
    }}

    /* Active nav page */
    section[data-testid="stSidebar"] a[aria-current="page"],
    section[data-testid="stSidebar"] a[aria-current="page"] span,
    section[data-testid="stSidebar"] a[aria-current="page"] p {{
        color: #FFFFFF !important;
        font-weight: 600;
        border-left: 3px solid var(--tfs-red);
        padding-left: 12px;
    }}

    /* Sidebar selectbox styling */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] label {{
        color: rgba(255,255,255,0.5) !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ── Main content area ───────────────────────────────── */
    .stApp {{
        background-color: var(--tfs-surface);
    }}

    .stApp p, .stApp span, .stApp label {{
        color: var(--tfs-text);
    }}

    /* ── Metric cards ────────────────────────────────────── */
    div[data-testid="stMetric"] {{
        background-color: var(--tfs-white);
        border: 1px solid var(--tfs-border);
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }}

    /* ── Containers/expanders ────────────────────────────── */
    [data-testid="stExpander"] {{
        background-color: var(--tfs-white);
        border: 1px solid var(--tfs-border);
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}

    div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div[data-testid="stHorizontalBlock"] {{
    }}

    /* ── Material icon helper ────────────────────────────── */
    .mat-icon {{
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        vertical-align: middle;
        margin-right: 6px;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
        -webkit-font-smoothing: antialiased;
    }}

    /* ── Dividers ────────────────────────────────────────── */
    hr {{
        border: none;
        border-top: 1px solid var(--tfs-border);
        margin: 1rem 0;
    }}

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {{
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid var(--tfs-border);
        transition: all 0.15s ease;
    }}

    .stButton > button:hover {{
        border-color: var(--tfs-red);
        color: var(--tfs-red);
    }}
</style>
""",
    unsafe_allow_html=True,
)


# -- Sidebar logo & branding ---------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 20px 16px 16px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px;">
            {_logo_svg}
        </div>
        """,
        unsafe_allow_html=True,
    )

# -- Navigation (Material Symbols icons) ---------------------------------------
portfolio_page = st.Page(
    "pages/1_portfolio.py",
    title="Portfolio Overview",
    icon=":material/dashboard:",
    default=True,
)
model_page = st.Page(
    "pages/2_model_summary.py",
    title="Model Summary",
    icon=":material/monitoring:",
)
feature_page = st.Page(
    "pages/3_feature_monitor.py",
    title="Feature Monitor",
    icon=":material/query_stats:",
)
performance_page = st.Page(
    "pages/4_performance.py",
    title="Performance",
    icon=":material/speed:",
)

pg = st.navigation([portfolio_page, model_page, feature_page, performance_page])
pg.run()
