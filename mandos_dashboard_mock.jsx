import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";

const COLORS = {
  bg: "#0f1117",
  card: "#1a1d27",
  cardBorder: "#2a2d3a",
  accent: "#4f8ff7",
  accentDim: "#3a6bbf",
  text: "#e4e6ef",
  textDim: "#8b8fa3",
  gradeA: "#22c55e",
  gradeB: "#3b82f6",
  gradeC: "#f59e0b",
  gradeD: "#ef4444",
  portfolio: "#a78bfa",
  good: "#22c55e",
  warn: "#f59e0b",
  critical: "#ef4444",
  confirmed: "#ef4444",
  probable: "#f59e0b",
  floor: "rgba(239,68,68,0.15)",
};

const FONTS = {
  mono: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace",
  sans: "'DM Sans', 'Segoe UI', sans-serif",
};

// Mock Data
const gradeSepData = [3, 6, 9, 12, 15, 18, 21, 24].map(mob => ({
  mob: `M${mob}`,
  A: [0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1][Math.floor(mob / 3) - 1],
  B: [0, 0.1, 0.2, 0.4, 0.5, 0.7, 0.8, 0.9][Math.floor(mob / 3) - 1],
  C: [0.1, 0.5, 1.0, 1.7, 2.3, 2.9, 3.2, 3.5][Math.floor(mob / 3) - 1],
  D: [0.4, 1.8, 3.5, 5.3, 6.8, 8.0, 8.7, 9.2][Math.floor(mob / 3) - 1],
}));

const crossVintageData = [
  { vintage: "24-01", A: 0.3, B: 1.3, C: 3.6, D: 8.0, portfolio: 2.5 },
  { vintage: "24-04", A: 0.3, B: 1.4, C: 3.8, D: 8.2, portfolio: 2.6 },
  { vintage: "24-07", A: 0.4, B: 1.5, C: 3.9, D: 8.5, portfolio: 2.7 },
  { vintage: "24-10", A: 0.3, B: 1.6, C: 4.0, D: 8.7, portfolio: 2.8 },
  { vintage: "25-01", A: 0.4, B: 1.5, C: 4.2, D: 9.1, portfolio: 2.9 },
  { vintage: "25-04", A: 0.4, B: 1.7, C: 4.4, D: 9.5, portfolio: 3.1 },
];

const maturationOverlay = {
  "24-07": [0.3, 1.5, 3.0, 5.0, 6.4, 7.6, 8.2, 8.5],
  "24-10": [0.4, 1.7, 3.2, 5.3, 6.7, 7.9, 8.5, 8.7],
  "25-01": [0.4, 1.8, 3.5, 5.3, 6.8, 8.0, 8.7, 9.2],
  "25-04": [0.5, 2.1, 3.9, 5.8, null, null, null, null],
};
const overlayData = [3, 6, 9, 12, 15, 18, 21, 24].map((mob, i) => ({
  mob: `M${mob}`,
  ...Object.fromEntries(Object.entries(maturationOverlay).map(([k, v]) => [k, v[i]])),
}));

const floorCeilData = [3, 6, 9, 12, 15, 18, 21, 24].map((mob, i) => ({
  mob: `M${mob}`,
  confirmed: [0.1, 0.4, 0.9, 1.4, 1.9, 2.3, 2.6, 2.8][i],
  probable: [0.2, 0.8, 1.7, 2.6, 3.2, 3.6, 3.4, 2.8][i],
}));

const alertHistory = [
  { date: "2026-02-01", vintage: "2025-01", grade: "D", metric: "ever_60_rate", mob: 8, value: "9.6%", baseline: "7.8%", deviation: "+23%", severity: "warning" },
  { date: "2026-02-01", vintage: "2025-01", grade: "D", metric: "psi_dti", mob: 8, value: "0.22", baseline: "0.05", deviation: "+340%", severity: "critical" },
  { date: "2026-04-01", vintage: "2025-04", grade: "D", metric: "ever_30_rate", mob: 3, value: "6.8%", baseline: "5.5%", deviation: "+24%", severity: "watch" },
  { date: "2026-05-01", vintage: "2025-01", grade: "D", metric: "confirmed_bad_rate", mob: 11, value: "4.8%", baseline: "3.8%", deviation: "+26%", severity: "warning" },
];

const modelHealth = [
  { model: "zuul_originations", status: "warning", latest_metric: "Confirmed bad ↑ Grade D", vintage: "2025-01", mob: 12 },
  { model: "loss_forecast_v3", status: "good", latest_metric: "All tiers nominal", vintage: "2025-03", mob: 6 },
  { model: "epd_model", status: "good", latest_metric: "All tiers nominal", vintage: "2025-06", mob: 3 },
  { model: "collections_v2", status: "critical", latest_metric: "Grade C ≈ Grade D at M4", vintage: "2025-04", mob: 4 },
];

const VIEWS = [
  { id: "health", label: "Model Health" },
  { id: "separation", label: "Grade Separation" },
  { id: "crossvintage", label: "Cross-Vintage Trend" },
  { id: "overlay", label: "Vintage Overlay" },
  { id: "floorceil", label: "Floor / Ceiling" },
  { id: "alerts", label: "Alert History" },
];

const StatusDot = ({ status }) => (
  <span style={{
    display: "inline-block", width: 8, height: 8, borderRadius: "50%",
    background: status === "good" ? COLORS.good : status === "warning" ? COLORS.warn : COLORS.critical,
    boxShadow: `0 0 6px ${status === "good" ? COLORS.good : status === "warning" ? COLORS.warn : COLORS.critical}`,
    marginRight: 8,
  }} />
);

const SeverityBadge = ({ severity }) => {
  const c = severity === "critical" ? COLORS.critical : severity === "warning" ? COLORS.warn : COLORS.textDim;
  return (
    <span style={{
      fontSize: 11, fontFamily: FONTS.mono, fontWeight: 600,
      color: c, background: `${c}18`, border: `1px solid ${c}40`,
      padding: "2px 8px", borderRadius: 4, textTransform: "uppercase", letterSpacing: 0.5,
    }}>{severity}</span>
  );
};

const Card = ({ title, subtitle, children, style }) => (
  <div style={{
    background: COLORS.card, border: `1px solid ${COLORS.cardBorder}`,
    borderRadius: 10, padding: "20px 24px", ...style,
  }}>
    {title && <div style={{ fontFamily: FONTS.sans, fontWeight: 600, fontSize: 15, color: COLORS.text, marginBottom: 2 }}>{title}</div>}
    {subtitle && <div style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textDim, marginBottom: 16 }}>{subtitle}</div>}
    {children}
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#1e2130", border: `1px solid ${COLORS.cardBorder}`,
      borderRadius: 6, padding: "10px 14px", fontSize: 12, fontFamily: FONTS.mono,
    }}>
      <div style={{ color: COLORS.textDim, marginBottom: 6, fontWeight: 600 }}>{label}</div>
      {payload.filter(p => p.value != null).map((p, i) => (
        <div key={i} style={{ color: p.color, marginBottom: 2 }}>
          {p.dataKey}: {typeof p.value === "number" ? p.value.toFixed(1) : p.value}%
        </div>
      ))}
    </div>
  );
};

const GradeLegend = () => (
  <div style={{ display: "flex", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
    {[["A", COLORS.gradeA], ["B", COLORS.gradeB], ["C", COLORS.gradeC], ["D", COLORS.gradeD]].map(([g, c]) => (
      <div key={g} style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>
        <span style={{ width: 12, height: 3, background: c, borderRadius: 2, display: "inline-block" }} />
        Grade {g}
      </div>
    ))}
  </div>
);

export default function MandosDashboard() {
  const [activeView, setActiveView] = useState("health");

  return (
    <div style={{ background: COLORS.bg, minHeight: "100vh", color: COLORS.text, fontFamily: FONTS.sans, padding: 0 }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${COLORS.cardBorder}`,
        padding: "16px 28px", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontFamily: FONTS.mono, fontWeight: 700, fontSize: 22, color: COLORS.accent, letterSpacing: -0.5 }}>MANDOS</span>
          <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim, letterSpacing: 1 }}>MODEL MONITORING</span>
        </div>
        <div style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>
          zuul_originations v2.1 &nbsp;·&nbsp; Last run: 2026-04-01
        </div>
      </div>

      {/* Nav */}
      <div style={{
        display: "flex", gap: 4, padding: "12px 28px", borderBottom: `1px solid ${COLORS.cardBorder}`,
        overflowX: "auto",
      }}>
        {VIEWS.map(v => (
          <button
            key={v.id}
            onClick={() => setActiveView(v.id)}
            style={{
              background: activeView === v.id ? COLORS.accent + "20" : "transparent",
              border: activeView === v.id ? `1px solid ${COLORS.accent}50` : "1px solid transparent",
              borderRadius: 6, padding: "7px 16px", cursor: "pointer",
              fontFamily: FONTS.mono, fontSize: 12, fontWeight: 500, whiteSpace: "nowrap",
              color: activeView === v.id ? COLORS.accent : COLORS.textDim,
              transition: "all 0.15s ease",
            }}
          >{v.label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "24px 28px", maxWidth: 1100 }}>

        {/* MODEL HEALTH */}
        {activeView === "health" && (
          <div>
            <Card title="Model Health Summary" subtitle="Latest status for all monitored models with lagged actuals">
              <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                <div style={{
                  display: "grid", gridTemplateColumns: "28px 1.5fr 0.8fr 1.5fr 0.8fr 0.6fr",
                  padding: "8px 0", borderBottom: `1px solid ${COLORS.cardBorder}`,
                  fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textDim, fontWeight: 600, letterSpacing: 0.5,
                }}>
                  <span></span><span>MODEL</span><span>STATUS</span><span>LATEST SIGNAL</span><span>VINTAGE</span><span>MOB</span>
                </div>
                {modelHealth.map((m, i) => (
                  <div key={i} style={{
                    display: "grid", gridTemplateColumns: "28px 1.5fr 0.8fr 1.5fr 0.8fr 0.6fr",
                    padding: "12px 0", borderBottom: i < modelHealth.length - 1 ? `1px solid ${COLORS.cardBorder}20` : "none",
                    alignItems: "center",
                  }}>
                    <StatusDot status={m.status} />
                    <span style={{ fontFamily: FONTS.mono, fontSize: 13, fontWeight: 600 }}>{m.model}</span>
                    <SeverityBadge severity={m.status} />
                    <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>{m.latest_metric}</span>
                    <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>{m.vintage}</span>
                    <span style={{ fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>{m.mob}</span>
                  </div>
                ))}
              </div>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, marginTop: 16 }}>
              {[
                { label: "Active Vintages", value: "14", sub: "Across 4 models" },
                { label: "Alerts (30d)", value: "4", sub: "2 warning · 1 critical · 1 watch", color: COLORS.warn },
                { label: "Avg Confirmed Rate", value: "1.4%", sub: "Portfolio @ MOB 12" },
                { label: "Next Run", value: "May 1", sub: "18 vintages queued" },
              ].map((kpi, i) => (
                <Card key={i}>
                  <div style={{ fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textDim, marginBottom: 4, letterSpacing: 0.5 }}>{kpi.label}</div>
                  <div style={{ fontFamily: FONTS.mono, fontSize: 28, fontWeight: 700, color: kpi.color || COLORS.text, lineHeight: 1 }}>{kpi.value}</div>
                  <div style={{ fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim, marginTop: 4 }}>{kpi.sub}</div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* GRADE SEPARATION */}
        {activeView === "separation" && (
          <Card title="Grade Separation Chart" subtitle="Vintage 2025-01 · Confirmed bad rate by grade over MOB · Wide separation = strong discrimination">
            <GradeLegend />
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={gradeSepData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.cardBorder} />
                <XAxis dataKey="mob" tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} />
                <YAxis tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="D" stroke={COLORS.gradeD} strokeWidth={2.5} dot={{ r: 3.5 }} />
                <Line type="monotone" dataKey="C" stroke={COLORS.gradeC} strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="B" stroke={COLORS.gradeB} strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="A" stroke={COLORS.gradeA} strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{
              marginTop: 12, padding: "12px 16px", borderRadius: 6,
              background: `${COLORS.good}10`, border: `1px solid ${COLORS.good}30`,
              fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim,
            }}>
              ✓ &nbsp;Grade separation is clean and monotonic (A &lt; B &lt; C &lt; D) at every MOB. Model discrimination is holding for this vintage.
            </div>
          </Card>
        )}

        {/* CROSS-VINTAGE */}
        {activeView === "crossvintage" && (
          <Card title="Cross-Vintage Trend by Grade" subtitle="Ever 60+ DPD rate at MOB 12 · Grade D trending upward across recent vintages">
            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={crossVintageData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.cardBorder} />
                <XAxis dataKey="vintage" tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} />
                <YAxis tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="A" fill={COLORS.gradeA} radius={[2, 2, 0, 0]} />
                <Bar dataKey="B" fill={COLORS.gradeB} radius={[2, 2, 0, 0]} />
                <Bar dataKey="C" fill={COLORS.gradeC} radius={[2, 2, 0, 0]} />
                <Bar dataKey="D" fill={COLORS.gradeD} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <GradeLegend />
            <div style={{
              marginTop: 8, padding: "12px 16px", borderRadius: 6,
              background: `${COLORS.warn}10`, border: `1px solid ${COLORS.warn}30`,
              fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim,
            }}>
              ⚠ &nbsp;Grade D ever-60+ rate rising: 8.2% → 9.5% over 5 quarters. Grades A–C stable. Degradation is segment-specific.
            </div>
          </Card>
        )}

        {/* VINTAGE OVERLAY */}
        {activeView === "overlay" && (
          <Card title="Vintage Overlay" subtitle="Grade D confirmed bad rate · Multiple vintages on same maturation axis · Newer vintages running hotter">
            <div style={{ display: "flex", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
              {[["24-07", "#6b7280"], ["24-10", "#8b5cf6"], ["25-01", COLORS.warn], ["25-04", COLORS.critical]].map(([v, c]) => (
                <div key={v} style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>
                  <span style={{ width: 12, height: 3, background: c, borderRadius: 2, display: "inline-block" }} />
                  {v}
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={overlayData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.cardBorder} />
                <XAxis dataKey="mob" tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} />
                <YAxis tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} unit="%" />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="24-07" stroke="#6b7280" strokeWidth={1.5} dot={{ r: 3 }} strokeDasharray="5 5" connectNulls={false} />
                <Line type="monotone" dataKey="24-10" stroke="#8b5cf6" strokeWidth={1.5} dot={{ r: 3 }} strokeDasharray="5 5" connectNulls={false} />
                <Line type="monotone" dataKey="25-01" stroke={COLORS.warn} strokeWidth={2.5} dot={{ r: 4 }} connectNulls={false} />
                <Line type="monotone" dataKey="25-04" stroke={COLORS.critical} strokeWidth={2.5} dot={{ r: 4 }} connectNulls={false} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{
              marginTop: 12, padding: "12px 16px", borderRadius: 6,
              background: `${COLORS.critical}10`, border: `1px solid ${COLORS.critical}30`,
              fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim,
            }}>
              🔴 &nbsp;Vintage 25-04 (4 months of data) is tracking above 25-01 at the same MOB. If the trajectory holds, final Grade D bad rate could exceed 10%.
            </div>
          </Card>
        )}

        {/* FLOOR / CEILING */}
        {activeView === "floorceil" && (
          <Card title="Confirmed vs. Probable Bad Rate" subtitle="Vintage 2025-01 · Portfolio level · Gap between floor and ceiling narrows as vintage matures">
            <div style={{ display: "flex", gap: 16, marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>
                <span style={{ width: 12, height: 3, background: COLORS.confirmed, borderRadius: 2, display: "inline-block" }} />
                Confirmed (floor)
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim }}>
                <span style={{ width: 12, height: 3, background: COLORS.probable, borderRadius: 2, display: "inline-block" }} />
                Probable (ceiling)
              </div>
            </div>
            <ResponsiveContainer width="100%" height={380}>
              <LineChart data={floorCeilData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.cardBorder} />
                <XAxis dataKey="mob" tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} />
                <YAxis tick={{ fill: COLORS.textDim, fontSize: 12, fontFamily: FONTS.mono }} stroke={COLORS.cardBorder} unit="%" domain={[0, 4.5]} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="probable" stroke={COLORS.probable} strokeWidth={2} dot={{ r: 3 }} strokeDasharray="6 3" />
                <Line type="monotone" dataKey="confirmed" stroke={COLORS.confirmed} strokeWidth={2.5} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{
              marginTop: 12, padding: "12px 16px", borderRadius: 6,
              background: `${COLORS.accent}10`, border: `1px solid ${COLORS.accent}30`,
              fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim, lineHeight: 1.6,
            }}>
              ℹ &nbsp;At M12, confirmed floor = 1.4%, probable ceiling = 2.6%. The gap (1.2pp) represents accounts at 90+ DPD that haven't yet crossed 120+ DPD. By M24, both converge to 2.8% — the final actual bad rate.
            </div>
          </Card>
        )}

        {/* ALERTS */}
        {activeView === "alerts" && (
          <Card title="Alert History" subtitle="Threshold breaches across all vintages and grades · Last 90 days">
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              <div style={{
                display: "grid", gridTemplateColumns: "0.8fr 0.8fr 0.5fr 1.2fr 0.5fr 0.7fr 0.7fr 0.7fr 0.7fr",
                padding: "8px 0", borderBottom: `1px solid ${COLORS.cardBorder}`,
                fontFamily: FONTS.mono, fontSize: 10, color: COLORS.textDim, fontWeight: 600, letterSpacing: 0.5,
              }}>
                <span>DATE</span><span>VINTAGE</span><span>GRADE</span><span>METRIC</span><span>MOB</span>
                <span>VALUE</span><span>BASELINE</span><span>DEV.</span><span>SEVERITY</span>
              </div>
              {alertHistory.map((a, i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "0.8fr 0.8fr 0.5fr 1.2fr 0.5fr 0.7fr 0.7fr 0.7fr 0.7fr",
                  padding: "10px 0", borderBottom: i < alertHistory.length - 1 ? `1px solid ${COLORS.cardBorder}20` : "none",
                  alignItems: "center", fontFamily: FONTS.mono, fontSize: 12, color: COLORS.textDim,
                }}>
                  <span>{a.date}</span>
                  <span style={{ color: COLORS.text }}>{a.vintage}</span>
                  <span style={{ color: COLORS.gradeD, fontWeight: 600 }}>{a.grade}</span>
                  <span>{a.metric}</span>
                  <span>{a.mob}</span>
                  <span style={{ color: COLORS.text }}>{a.value}</span>
                  <span>{a.baseline}</span>
                  <span style={{ color: a.severity === "critical" ? COLORS.critical : a.severity === "warning" ? COLORS.warn : COLORS.textDim, fontWeight: 600 }}>{a.deviation}</span>
                  <SeverityBadge severity={a.severity} />
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${COLORS.cardBorder}`,
        padding: "12px 28px", fontFamily: FONTS.mono, fontSize: 11, color: COLORS.textDim,
        display: "flex", justifyContent: "space-between",
      }}>
        <span>Mandos v1.0 · Streamlit on Snowflake</span>
        <span>ML Engineering · Risk Organization</span>
      </div>
    </div>
  );
}
