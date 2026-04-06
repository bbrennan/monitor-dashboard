# UI/UX Design Strategy Study

> Epic 1 — Model Monitoring Dashboard for TFS Risk Data Science

## 1. Problem Statement

We need to monitor ~10 production ML models across drift, performance, feature importance, and alerting for a 30-person Risk Data Science team. An existing monitoring library already computes metrics and writes them to Snowflake — this dashboard **visualizes that pre-computed data**, it doesn't recompute anything.

### Key domain constraints

- **Variable cadences**: Models score at different frequencies (daily, weekly, monthly, ad hoc). The dashboard cannot assume uniform time steps.
- **Delayed actuals**: In financial services, outcomes (defaults, losses) lag scoring by weeks to months. Performance metrics are often *estimates* until actuals arrive. The dashboard must clearly distinguish estimated vs. confirmed metrics and show how stale the actuals are.
- **Four data categories** per model run:
  - *Summary Statistics* — feature-level distributional summaries
  - *Data Quality* — missing rates, out-of-range, cardinality shifts
  - *Drift Metrics* — PSI, KS, chi-squared, JS divergence vs. reference
  - *Monitoring Metrics / Estimates* — AUC, KS, Gini (often estimated)

The default instinct is a "model tile grid" (Okta-style homepage) — but that pattern optimizes for *selection*, not *monitoring*. We need a design that surfaces **what needs attention** without forcing users to click into each model.

## 2. Anti-Patterns to Avoid

| Pattern | Why It Fails |
|---------|-------------|
| **Model tile grid** (Okta-style) | Equal visual weight for all models hides urgency. Forces click-through to see status. Scales poorly beyond ~12 items. |
| **Tab-per-model** | Same problem — status is invisible until selected. |
| **Giant data table** | Information-dense but lacks visual hierarchy and trend context. |
| **Consumer-style dashboards** | Card-heavy, low-density layouts waste screen real estate for power users. |

## 3. Design Inspirations & Patterns

### 3.1 Command Center / Mission Control

**Examples**: Datadog Infrastructure Map, Grafana dashboards, Bloomberg Terminal

**Key idea**: A single view showing the health of *everything* at once, using color/intensity to encode status. Users scan, not click.

- **Heat maps**: Model × metric matrix where color encodes severity (green → yellow → red)
- **Sparkline grids**: Compact trend lines per model/metric in a dense grid
- **Status-at-a-glance bar**: Horizontal bar showing all models with color-coded health

**Why this works for us**: 10 models × 4-5 metrics = ~50 cells. That fits in a single matrix view without scrolling.

### 3.2 Feed / Timeline Pattern

**Examples**: Evidently AI monitoring, PagerDuty incident feed, GitHub activity

**Key idea**: Chronological feed of events — drift detected, metric degraded, threshold breached. Most recent issues float to the top.

- Combines naturally with alerting
- Shows *when* things changed, not just current state
- Can filter by model, severity, metric type

**Why this works for us**: Data scientists care about "what changed since I last looked" more than "what is the current absolute value."

### 3.3 Ranked / Sorted Priority View

**Examples**: Arize AI model overview, WhyLabs monitor summary

**Key idea**: Models ranked by "health score" or "attention needed." Worst models at top. Each row expands for detail.

- Naturally draws attention to problems
- Progressive disclosure — summary → detail on demand
- Works well at 10 models, scales to 50+

### 3.4 Small Multiples / Faceted Grid

**Examples**: Financial Times data journalism, Edward Tufte's principles

**Key idea**: Identical chart repeated for each model, arranged in grid. The eye catches the outlier instantly because the shape breaks the pattern.

- Sparklines with identical y-axes make anomalies visually obvious
- Dense, minimal, *professional* — matches TFS aesthetic
- Tufte calls this "small multiples" — the most effective way to compare time-series

### 3.5 Hybrid Approach (Recommended)

Combine the best elements:

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: TFS Branding + Date Range Selector                │
├────────────┬────────────────────────────────────────────────┤
│            │  STATUS BAR: All models, color-coded health    │
│            │  (includes last-run timestamp + cadence badge) │
│            ├────────────────────────────────────────────────┤
│  SIDEBAR   │  ALERT FEED: Recent events, filterable        │
│  - Filters │  (drift, quality, performance, staleness)     │
│  - Model   │────────────────────────────────────────────────┤
│    groups  │  DETAIL PANEL: Selected model deep dive       │
│  - Cadence │  - Drift heat map (feature × time)            │
│    filter  │  - Performance sparklines (estimated vs.      │
│  - Views   │    confirmed badges)                          │
│            │  - Data quality summary                       │
│            │  - Actuals horizon indicator                   │
│            │  - Threshold status indicators                 │
└────────────┴────────────────────────────────────────────────┘
```

**Landing view**: Status bar + alert feed (what needs attention NOW)
**Drill-down**: Click any model in the status bar → detail panel updates
**No tile grid**: Models are a continuous status bar, not discrete tiles

## 4. TFS Branding Application

### Color System

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Critical / Alert | TFS Red | `#EB0A1E` | Threshold breaches, critical drift |
| Warning | Amber | `#F5A623` | Approaching thresholds, moderate drift |
| Healthy | Green | `#2E7D32` | All metrics within bounds |
| Primary text | Dark Gray | `#333333` | Headings, primary content |
| Secondary text | Toyota Gray | `#58595B` | Labels, secondary content |
| Borders / dividers | Light Gray | `#D1D3D4` | Structural elements |
| Background | White | `#FFFFFF` | Page background |
| Surface | Near-white | `#F7F7F7` | Cards, panels |

### Typography

- **Headings**: System sans-serif (SF Pro / Segoe UI / Roboto), semibold
- **Body**: Same family, regular weight, 14px base
- **Data values**: Tabular numerals (monospace for alignment in tables)
- **Sparklines**: No labels — the shape is the message

### Component Style

- Minimal borders, use whitespace for separation
- No rounded corners on data containers (squared = professional)
- Subtle shadows only on elevated panels
- Dense spacing — this is a work tool, not a marketing page

## 5. Navigation Architecture

### Option A: Single-Page with Tab Sections (Recommended for Streamlit)

```
Overview (landing) → Summary Stats → Data Quality → Drift → Performance → Alerts → Config
```

Each tab shows all models for that concern. Maps directly to the four metric categories from the monitoring library, plus an overview and alerts/config layer. The sidebar provides model and cadence filtering.

### Option B: Two-Level Navigation

```
Level 1 (sidebar): Overview | Drift | Performance | Features | Alerts
Level 2 (within page): Model selector / filter
```

### Recommendation

**Option A** — Streamlit's `st.navigation` supports this natively. Each page is a monitoring *concern*, not a model. This avoids the trap of model-centric navigation which leads back to the tile pattern.

## 6. Key Design Principles

1. **Monitoring, not browsing**: The landing page should answer "is anything broken?" in under 3 seconds
2. **Concern-centric, not model-centric**: Navigate by *what* (drift, performance) not *which* (Model A, Model B)
3. **Information density**: Every pixel should convey data. No decorative elements
4. **Progressive disclosure**: Summary → detail. Never force users to drill down to see status
5. **Anomaly-first**: Visual design should make deviations from normal immediately obvious
6. **Consistent scales**: When comparing models, always use the same y-axis range
7. **Cadence-aware time axes**: Always plot against calendar time, never run index. Irregular cadences must be visually obvious (e.g., gaps in sparklines)
8. **Actuals transparency**: Every performance metric must show whether it's estimated or confirmed, and when actuals were last available
9. **Freshness-first**: Show each model's last-run timestamp, scoring frequency, and data staleness prominently — stale data is the most common silent failure

## 7. Next Steps

- [ ] Build a static mockup of the hybrid layout in Streamlit
- [ ] Validate the status bar + alert feed landing page concept
- [ ] Define the exact metrics shown on the overview page
- [ ] Choose chart library (Plotly recommended for interactive, Altair as alternative)
