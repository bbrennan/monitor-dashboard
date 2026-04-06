# UI/UX Design Strategy Study

> Epic 1 — Model Monitoring Dashboard for TFS Risk Data Science

## 1. Problem Statement

We need to monitor ~10 production ML models across drift, performance, feature importance, and alerting for the Risk Data Science org at Toyota Financial Services. An existing monitoring library already computes metrics and writes them to Snowflake — this dashboard **visualizes that pre-computed data**, it doesn't recompute anything.

This is a **"morning coffee" tool** — anyone in the org should be able to log in, scan the portfolio, and know in under a minute whether anything needs attention.

### Personas (progressive disclosure)

| Persona | Need | Depth | Frequency |
|---------|------|-------|-----------|
| **CRO** | Portfolio health at a glance. Red/yellow/green. No jargon. | Summary only | Weekly |
| **VP** | Which models need attention? Any trends? | Summary + trends | Daily |
| **Model Validation Analyst** | Review models in their domain. Compare across models. | Domain-level metrics | Daily |
| **Model Owner (SME)** | Deep dive into their model. Feature-level forensics. Why did PSI shift? | Full detail | Daily |

The design must serve *all four* through progressive disclosure — the same landing page, with detail revealed on demand.

### Key domain constraints

- **Variable cadences**: Models score at different frequencies (daily, weekly, monthly, ad hoc). The dashboard cannot assume uniform time steps.
- **Delayed actuals**: In financial services, outcomes (defaults, losses) lag scoring by weeks to months. Performance metrics are often *estimates* until actuals arrive. The dashboard must clearly distinguish estimated vs. confirmed metrics and show how stale the actuals are.
- **Four data categories** per model run:
  - *Summary Statistics* — feature-level distributional summaries
  - *Data Quality* — missing rates, out-of-range, cardinality shifts
  - *Drift Metrics* — PSI, CSI, KS, chi-squared, JS divergence vs. baseline
  - *Monitoring Metrics / Estimates* — AUC, KS, Gini (often estimated)

### PSI-first investigation workflow

Users almost always supply a **model score** at onboarding. The natural investigation flow is:

```
1. Score PSI  → Did the overall model score distribution shift?
   │
   ├─ YES → 2. Feature CSI  → Which features drifted?
   │              │
   │              └─→ 3. Deeper metrics (KS, summary stats, data quality)
   │                     for the drifted features
   │
   └─ NO  → Score is stable, BUT check anyway:
              → Feature CSI for silent drift
              → Data quality for upstream issues
              → Performance estimates for degradation
              (Something could be wrong that hasn't impacted the score YET)
```

The UI should guide this workflow naturally — PSI front and center, CSI one click away, deeper metrics on drill-down.

## 2. Anti-Patterns to Avoid

| Pattern | Why It Fails |
|---------|-------------|
| **Model tile grid** (Okta-style) | Equal visual weight for all models hides urgency. Forces click-through to see status. Scales poorly beyond ~12 items. |
| **Tab-per-model** | Same problem — status is invisible until selected. |
| **Giant data table** | Information-dense but lacks visual hierarchy and trend context. |
| **Consumer-style dashboards** | Card-heavy, low-density layouts waste screen real estate for power users. |
| **Bloomberg-style density** | Too overwhelming. Our VP and CRO personas need clean, scannable layouts. |

## 3. Design Inspirations & Patterns

### 3.1 Design References (user-validated)

**Primary inspiration** (monitoring tools):
- **WhyLabs** — clean single-page layout, model health overview, metric panels
- **Fiddler AI** — single-page with large text boxes of results + charts, feature drill-down
- **NannyML** — estimated performance visualization, handles "no actuals yet" elegantly

**UX/interaction inspiration**:
- **Linear** — information density without clutter, keyboard-first, fast transitions, triage view
- **Stripe Dashboard** — progressive disclosure masterclass, easy for non-technical users, clean status indicators
- **TradingView / Koyfin** — high-level market summary, multi-panel time-series layouts

### 3.2 Pattern: Single-Page Model Summary (WhyLabs/Fiddler style)

Each model gets a **single scrollable page** with large, clear metric panels:

```
┌─────────────────────────────────────────────────────────────┐
│  MODEL NAME          Last scored: 2h ago    Cadence: Daily  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ SCORE PSI ──────────────────────────────────────────┐   │
│  │  PSI: 0.08  ▪ STABLE                    [sparkline] │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ PERFORMANCE ────────────────────────────────────────┐   │
│  │  AUC: 0.82 (estimated)  KS: 0.41   Gini: 0.64     │   │
│  │  Actuals through: 2026-02-15  (51 days stale)       │   │
│  │  [trend chart]                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ FEATURE DRIFT (CSI) ───────────────────────────────┐   │
│  │  2 of 47 features drifted  [ranked bar chart]       │   │
│  │  income_ratio: 0.31 ▪ CRITICAL                      │   │
│  │  employment_years: 0.18 ▪ WARNING                   │   │
│  │  [click any feature to expand]                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ DATA QUALITY ──────────────────────────────────────┐   │
│  │  Missing rate: 0.2% (baseline: 0.1%)                │   │
│  │  Schema: OK    Out-of-range: 3 features             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**This is the Model Owner view** — detailed, single-page, scrollable, large panels.

### 3.3 Pattern: Portfolio Overview (Stripe/Linear style)

The **landing page** serves the CRO/VP — a scannable portfolio summary:

```
┌──────────────────────────────────────────────────────────────┐
│  MODEL PORTFOLIO HEALTH              As of: 2026-04-06 8am  │
│                                                              │
│  10 models │ 8 healthy │ 1 warning │ 1 critical             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━      │
│  ██████████████████████████████████░░░░░██████                │
│  (green bar ──────────────────────)(amb)(red─)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ▼ NEEDS ATTENTION                                           │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ● Auto Loan Default    PSI: 0.24 ■ CRITICAL         │    │
│  │   Scored 3h ago │ 4 features drifted │ AUC ↓ 0.04   │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │ ◐ Fraud Detection      PSI: 0.12 ■ WARNING          │    │
│  │   Scored 1d ago │ 1 feature drifted  │ AUC stable   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ▶ ALL MODELS STABLE (8)    [expand to see]                  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  RECENT EVENTS                                               │
│  09:12  Auto Loan Default — income_ratio CSI exceeded 0.25  │
│  09:12  Auto Loan Default — Score PSI crossed critical       │
│  Yesterday  Fraud Detection — employment_years CSI warning   │
│  3 days ago  All models — monthly refresh completed          │
└──────────────────────────────────────────────────────────────┘
```

**Key design decisions**:
- Problems float to the top (ranked by severity, not alphabetical)
- Stable models collapse into a single expandable row — don't waste space on green
- PSI is the headline metric for every model
- Click any model row → navigates to the single-page model summary (Section 3.2)
- Recent events feed at the bottom for daily "what changed" scanning

### 3.4 Information Hierarchy (Progressive Disclosure)

```
Level 0: Portfolio bar    → CRO glances at the color bar (3 seconds)
Level 1: Problem list     → VP reads the "needs attention" rows (30 seconds)
Level 2: Model summary    → Analyst reviews PSI, performance, drift panels (2-5 min)
Level 3: Feature detail   → Model owner drills into CSI, bin distributions (10+ min)
```

Each level is revealed on demand — no persona sees more complexity than they need.

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

- Clean and spacious like Stripe — not Bloomberg-dense
- Large metric panels with clear labels (WhyLabs/Fiddler style)
- Minimal borders, use whitespace for separation
- Subtle shadows only on elevated panels
- Professional but approachable — CRO and model owner both feel at home

## 5. Navigation Architecture

### Recommended: Two-level progressive disclosure

```
Landing: Portfolio Overview (all models, ranked by health)
  └─→ Model Summary Page (single-page, scrollable, large panels)
        └─→ Feature Detail (expandable sections within model page)
```

**Sidebar** (always visible):
- Model list (sorted by health, color-coded)
- Cadence filter (daily / weekly / monthly)
- Domain filter (if models are grouped by business line)

**This is NOT tab-per-concern navigation.** Instead:
- The Portfolio Overview shows health across all concerns (PSI, performance, quality)
- The Model Summary shows all concerns for one model on a single page
- This matches the WhyLabs/Fiddler pattern the team prefers

## 6. Key Design Principles

1. **Morning coffee tool**: Anyone can scan the portfolio in under a minute
2. **PSI-first**: Score PSI is the headline metric. Feature CSI is one click away.
3. **Problems float up**: Critical models always at top. Stable models collapse.
4. **Progressive disclosure**: CRO sees the color bar. Model owner sees bin distributions. Same app.
5. **Single-page model view**: No tabs within a model — scroll, don't click. Large panels with clear results.
6. **Anomaly-first**: Visual design makes deviations from normal immediately obvious
7. **Cadence-aware time axes**: Always plot against calendar time, never run index
8. **Actuals transparency**: Every performance metric must show estimated vs. confirmed and staleness
9. **Stripe-clean, not Bloomberg-dense**: Approachable for the CRO, detailed enough for the model owner

## 7. Next Steps

- [ ] Build the Portfolio Overview page in Streamlit
- [ ] Build the Model Summary page (single-page, large panels)
- [ ] Implement PSI-first layout with CSI drill-down
- [ ] Design the "estimated vs. confirmed" performance indicator
- [ ] Create synthetic data generator for ~10 models with mixed cadences
- [ ] Choose chart library (Plotly recommended for interactive)
