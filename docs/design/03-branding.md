# Branding & Styling

> Visual identity system for the TFS Model Monitoring Dashboard.

## Color Palette

### Brand Colors

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Primary | TFS Red | `#EB0A1E` | Critical alerts, active indicators, brand accent |
| Dark | Dark Gray | `#1A1A1A` | Sidebar background, header |
| Dark 2 | Dark Gray 2 | `#2A2A2A` | Sidebar gradient end |
| Text | Text Gray | `#333333` | Primary body text |
| Secondary | Toyota Gray | `#58595B` | Labels, secondary text |
| Border | Border Gray | `#E5E5E5` | Card borders, dividers |
| Light | Light Gray | `#D1D3D4` | Subtle borders |
| Surface | Surface | `#FAFAFA` | Page background |
| White | White | `#FFFFFF` | Card backgrounds, sidebar text |

### Semantic Colors

| Role | Hex | Usage |
|------|-----|-------|
| Healthy / Good | `#2E7D32` | Metrics within thresholds |
| Warning | `#F5A623` | Approaching thresholds |
| Critical / Alert | `#EB0A1E` | Threshold breaches, critical drift |
| Estimated | dashed lines | Metrics based on estimates (no actuals) |
| Confirmed | solid lines | Metrics validated against actuals |

## Typography

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

- **Headings**: Semibold (600), system sans-serif
- **Body**: Regular (400), 14px base
- **Data values**: `font-variant-numeric: tabular-nums` for column alignment
- **Labels**: Uppercase, 0.75rem, letter-spacing 0.05em (sidebar section labels)

## Sidebar

- Dark gradient background: `linear-gradient(180deg, #1A1A1A, #2A2A2A)`
- SVG logo at top with bottom border divider
- Navigation links: white text at 75% opacity, 100% on hover/active
- Active page: white text, bold, 3px red left border
- Box shadow: `2px 0 8px rgba(0,0,0,0.15)`

## Header

- Dark background matching sidebar
- 2px TFS Red bottom border accent

## Cards & Containers

- White background, 1px border `#E5E5E5`, 8px border-radius
- Subtle shadow: `0 1px 3px rgba(0,0,0,0.04)`
- 16px internal padding

## Icons

Streamlit Material Design icons (native support):
- Portfolio: `:material/dashboard:`
- Model Summary: `:material/monitoring:`
- Feature Monitor: `:material/query_stats:`
- Performance: `:material/speed:`

## Logo

Two SVG assets in `src/monitor_dashboard/assets/`:

### `logo.svg` (sidebar)
- 240×48 viewport
- Red rounded rectangle (shield shape) with white ECG pulse line
- "TOYOTA FINANCIAL SERVICES" in muted white (60% opacity)
- "Model Monitor" in white, semibold

### `favicon.svg` (browser tab)
- 32×32 viewport
- Red rounded square with white ECG pulse line
- Minimal — recognizable at small sizes

## Chart Styling (Plotly)

All charts follow consistent theming:
- Background: transparent (inherits page surface)
- Grid lines: `#E5E5E5`
- Font: system sans-serif
- Colors: TFS Red for PSI/drift lines, Green for healthy metrics, Amber for warnings
- Threshold lines: dashed horizontal lines with labels
