# Design Decisions

> Key technical and design decisions made during the design study, with rationale.

## 1. Streamlit over Dash / Panel / Shiny

**Decision:** Use Streamlit as the dashboard framework.

**Rationale:**
- **Streamlit in Snowflake (SiS)** is the production deployment target — Streamlit apps can run natively inside Snowflake, eliminating the need for a separate hosting layer
- The team's data is already in Snowflake; SiS provides direct Snowpark access without network hops
- Streamlit's opinionated layout constraints are acceptable for a monitoring tool (not a general-purpose BI tool)
- Rapid prototyping — Python-only, no frontend build toolchain

**Trade-offs accepted:**
- Limited layout flexibility compared to Dash
- No server-side state management (stateless script reruns)
- Custom styling requires CSS injection via `st.markdown(unsafe_allow_html=True)`

## 2. PSI-First Investigation Workflow

**Decision:** Score PSI is the headline metric. Feature CSI is one click away. Deeper metrics on drill-down.

**Rationale:**
- Users almost always supply a model score at onboarding
- If the score distribution hasn't shifted, the model is likely stable (though silent drift in individual features is still possible)
- PSI → CSI → deeper metrics mirrors how experienced model validators actually investigate drift
- A single entry point (PSI) reduces cognitive load for the CRO/VP personas

## 3. Hub-and-Spoke Navigation (Not Tabs)

**Decision:** Portfolio Overview is the landing page. Model Summary is the per-model hub. Feature Monitor and Performance are spokes.

**Rationale:**
- Tab-per-model hides status until selected — fails the "morning coffee" test
- Model tile grids give equal visual weight to all models, hiding urgency
- Hub-and-spoke lets problems float to the top at the Portfolio level, with progressive disclosure into per-model detail
- Sidebar navigation (not top tabs) preserves vertical screen space for data-dense content

## 4. Problems Float Up, Stable Models Collapse

**Decision:** The Portfolio page ranks models by health status (critical → warning → healthy). Stable models collapse into a single expandable section.

**Rationale:**
- A CRO scanning 10 models should see the 1-2 problems in 3 seconds, not scan all 10
- Inspired by Linear's triage view and incident management UIs
- Stable models aren't hidden — they're in an expander — but they don't compete for attention

## 5. Polars over Pandas

**Decision:** Use Polars for all new DataFrame code. Existing pandas code is not migrated.

**Rationale:**
- Faster execution, especially for groupby/filter operations on monitoring data
- More predictable memory usage
- Lazy evaluation support for potential Snowflake pushdown via Polars SQL
- Growing ecosystem support in the Python data stack

## 6. Estimated vs. Confirmed Performance Metrics

**Decision:** Every performance metric must be labeled as estimated or confirmed. Actuals staleness is shown prominently.

**Rationale:**
- In financial services, outcomes (defaults, losses) lag scoring by 30–90+ days
- Showing "AUC: 0.82" without indicating it's an estimate is misleading
- The `is_estimated` flag and `actuals_through` date are first-class fields in the data model
- Performance page uses visual differentiation (dashed lines for estimated, solid for confirmed)

## 7. Fast Dummy Data for Development

**Decision:** Use numpy-based random data generators (<1s) for development. Keep sklearn-trained model data as an option.

**Rationale:**
- The sklearn data generator trains 10 GradientBoosting models on startup — takes 60+ seconds
- For UI iteration, the data shape matters more than statistical realism
- The mock data generator produces the same data contract (7 keys, identical column schemas)
- Seed-based (`np.random.default_rng(42)`) for deterministic output across runs
- `sklearn_data.py` remains available for demos requiring realistic metric correlations

## 8. Dark Sidebar with TFS Branding

**Decision:** Dark sidebar (`#1A1A1A` → `#2A2A2A` gradient), red accent line, Material Design icons, SVG logo.

**Rationale:**
- Dark sidebar provides clear visual separation between navigation and content
- TFS red accent line reinforces brand identity without overwhelming
- Material Design icons (`:material/dashboard:` etc.) are Streamlit-native — no emoji
- SVG logo renders crisply at any resolution and embeds directly in the sidebar HTML

## 9. Fixed Bin Edges from Onboarding

**Decision:** PSI/CSI bin edges are fixed at model onboarding and persisted. All subsequent drift calculations use these same bins.

**Rationale:**
- Ensures drift metrics are comparable across time — if bins change, PSI values aren't comparable
- Matches industry standard practice for model monitoring
- Bin edges are part of the baseline data written to Snowflake at onboarding
- The dashboard reads pre-computed PSI/CSI — it doesn't recompute from raw data

## 10. Calendar Time Axes (Not Run Index)

**Decision:** All time-series charts plot against calendar dates, not scoring run indices.

**Rationale:**
- Models run at different cadences — a daily model has 30x more points per month than a monthly model
- Run index makes a monthly model look like it changes as fast as a daily model
- Calendar time reveals actual temporal patterns (seasonality, business cycles)
- Gaps in the time axis are informative — they show when a model didn't run

## 11. No Homepage Model Grid

**Decision:** Explicitly rejected an "Okta-style" model tile grid for the landing page.

**Rationale:**
- Equal visual weight for all models hides urgency
- Forces click-through to see any model's status
- Scales poorly beyond ~12 items
- Contradicts the "problems float up" principle
- The stacked "needs attention" / "stable models" pattern is more information-dense and action-oriented
