import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from "recharts";

// ── Design Tokens ──
const C = {
  bg: "#0B0F19", surface: "#111827", card: "#1A2236", cardHover: "#1E2A45",
  border: "#1F2A40", borderLight: "#2A3655",
  accent: "#4F8FF7", accentDim: "#3A6BBF22",
  text: "#E4E8F0", textDim: "#6B7B98", textMuted: "#4A5568",
  good: "#22C55E", goodDim: "#22C55E20",
  warn: "#F59E0B", warnDim: "#F59E0B20",
  crit: "#EF4444", critDim: "#EF444420",
  gradeA: "#22C55E", gradeB: "#3B82F6", gradeC: "#F59E0B", gradeD: "#EF4444",
  purple: "#A78BFA",
};
const F = { mono: "'SF Mono','Fira Code','Consolas',monospace", sans: "'DM Sans','Segoe UI',system-ui,sans-serif" };

// ── Mock Data ──
const MODELS = [
  { id: "zuul", name: "Zuul Originations", version: "2.1", window: "24 mo", status: "warning", activeVintages: 14, latestAlert: "Grade D ever-60+ ↑", sparkline: [2.1,2.2,2.3,2.4,2.6,2.8,2.9,3.1] },
  { id: "resval", name: "Residual Value", version: "1.4", window: "36 mo", status: "good", activeVintages: 8, latestAlert: "—", sparkline: [1.1,1.0,1.1,1.0,0.9,1.0,1.0,0.9] },
  { id: "dynprice", name: "Dynamic Pricing", version: "3.0", window: "12 mo", status: "good", activeVintages: 6, latestAlert: "—", sparkline: [0.5,0.5,0.6,0.5,0.5,0.4,0.5,0.5] },
  { id: "ifrs9", name: "IFRS9 Loss Forecast", version: "2.2", window: "12 mo", status: "critical", activeVintages: 10, latestAlert: "Portfolio PSI > 0.25", sparkline: [3.0,3.1,3.3,3.5,3.8,4.2,4.5,4.9] },
  { id: "cecl", name: "CECL Allowance", version: "1.1", window: "Life of loan", status: "good", activeVintages: 12, latestAlert: "—", sparkline: [1.8,1.7,1.8,1.9,1.8,1.7,1.8,1.8] },
  { id: "epd", name: "Early Payment Default", version: "2.0", window: "6 mo", status: "good", activeVintages: 4, latestAlert: "—", sparkline: [0.8,0.7,0.8,0.7,0.7,0.8,0.7,0.7] },
];

const ZUUL_VINTAGES = [
  { vintage: "2024-07", mob: 21, accts: 11200, gradeA: "0.1%", gradeB: "0.7%", gradeC: "3.0%", gradeD: "8.2%", portfolio: "2.5%", status: "good" },
  { vintage: "2024-10", mob: 18, accts: 10800, gradeA: "0.1%", gradeB: "0.7%", gradeC: "2.9%", gradeD: "8.5%", portfolio: "2.6%", status: "good" },
  { vintage: "2025-01", mob: 15, accts: 11700, gradeA: "0.1%", gradeB: "0.5%", gradeC: "2.3%", gradeD: "6.8%", portfolio: "1.9%", status: "warning" },
  { vintage: "2025-04", mob: 12, accts: 10500, gradeA: "0.0%", gradeB: "0.4%", gradeC: "1.9%", gradeD: "5.8%", portfolio: "1.5%", status: "warning" },
  { vintage: "2025-07", mob: 9, accts: 11100, gradeA: "0.0%", gradeB: "0.2%", gradeC: "1.1%", gradeD: "3.7%", portfolio: "0.9%", status: "good" },
  { vintage: "2025-10", mob: 6, accts: 10900, gradeA: "0.0%", gradeB: "0.1%", gradeC: "0.5%", gradeD: "1.9%", portfolio: "0.4%", status: "good" },
  { vintage: "2026-01", mob: 3, accts: 11400, gradeA: "0.0%", gradeB: "0.0%", gradeC: "0.1%", gradeD: "0.5%", portfolio: "0.1%", status: "good" },
];

const GRADE_SEP = [3,6,9,12,15,18,21,24].map((m,i) => ({
  mob: `M${m}`, A: [0,0,0,0,.1,.1,.1,.1][i], B: [0,.1,.2,.4,.5,.7,.8,.9][i],
  C: [.1,.5,1,1.7,2.3,2.9,3.2,3.5][i], D: [.4,1.8,3.5,5.3,6.8,8,8.7,9.2][i]
}));

const CROSS_VINTAGE = [
  { v: "24-01", A:.3,B:1.3,C:3.6,D:8.0,p:2.5 }, { v: "24-04", A:.3,B:1.4,C:3.8,D:8.2,p:2.6 },
  { v: "24-07", A:.4,B:1.5,C:3.9,D:8.5,p:2.7 }, { v: "24-10", A:.3,B:1.6,C:4.0,D:8.7,p:2.8 },
  { v: "25-01", A:.4,B:1.5,C:4.2,D:9.1,p:2.9 }, { v: "25-04", A:.4,B:1.7,C:4.4,D:9.5,p:3.1 },
];

const OVERLAY_DATA = [3,6,9,12,15,18,21,24].map((m,i) => ({
  mob: `M${m}`, "24-07": [.3,1.5,3,5,6.4,7.6,8.2,8.5][i], "24-10": [.4,1.7,3.2,5.3,6.7,7.9,8.5,8.7][i],
  "25-01": [.4,1.8,3.5,5.3,6.8,8,8.7,9.2][i], "25-04": [.5,2.1,3.9,5.8,null,null,null,null][i],
}));

const FLOOR_CEIL = [3,6,9,12,15,18,21,24].map((m,i) => ({
  mob: `M${m}`, confirmed: [.1,.4,.9,1.4,1.9,2.3,2.6,2.8][i], probable: [.3,1.2,2.6,4.0,5.1,5.9,6.2,2.8][i],
}));

const DQ_FEATURES = [
  { feature: "bureau_score", null_rate: 0.001, baseline_null: 0.001, oor_rate: 0.002, cardinality: 312, status: "good" },
  { feature: "dti_ratio", null_rate: 0.003, baseline_null: 0.002, oor_rate: 0.018, cardinality: 89, status: "watch" },
  { feature: "ltv", null_rate: 0.001, baseline_null: 0.001, oor_rate: 0.001, cardinality: 156, status: "good" },
  { feature: "income", null_rate: 0.012, baseline_null: 0.005, oor_rate: 0.004, cardinality: 2840, status: "warning" },
  { feature: "loan_amount", null_rate: 0.000, baseline_null: 0.000, oor_rate: 0.001, cardinality: 1456, status: "good" },
  { feature: "term_months", null_rate: 0.000, baseline_null: 0.000, oor_rate: 0.000, cardinality: 5, status: "good" },
  { feature: "vehicle_age", null_rate: 0.002, baseline_null: 0.002, oor_rate: 0.003, cardinality: 22, status: "good" },
];

const DRIFT_FEATURES = [
  { feature: "bureau_score", psi: 0.04, baseline: 0.02, trend: [.02,.02,.03,.03,.04,.04], status: "good" },
  { feature: "dti_ratio", psi: 0.22, baseline: 0.03, trend: [.03,.04,.06,.09,.15,.22], status: "critical" },
  { feature: "ltv", psi: 0.06, baseline: 0.03, trend: [.03,.03,.04,.04,.05,.06], status: "good" },
  { feature: "income", psi: 0.11, baseline: 0.04, trend: [.04,.05,.06,.07,.09,.11], status: "warning" },
  { feature: "loan_amount", psi: 0.03, baseline: 0.02, trend: [.02,.02,.02,.03,.03,.03], status: "good" },
  { feature: "term_months", psi: 0.02, baseline: 0.01, trend: [.01,.01,.01,.02,.02,.02], status: "good" },
  { feature: "vehicle_age", psi: 0.05, baseline: 0.03, trend: [.03,.03,.04,.04,.04,.05], status: "good" },
];

const ALERTS = [
  { date: "2026-04-01", vintage: "2025-04", grade: "D", metric: "ever_30_rate", mob: 12, value: "15.2%", baseline: "12.8%", dev: "+19%", sev: "watch" },
  { date: "2026-03-01", vintage: "2025-01", grade: "D", metric: "confirmed_bad_rate", mob: 14, value: "6.2%", baseline: "5.0%", dev: "+24%", sev: "warning" },
  { date: "2026-02-01", vintage: "2025-01", grade: "D", metric: "psi:dti_ratio", mob: 13, value: "0.22", baseline: "0.03", dev: "+633%", sev: "critical" },
  { date: "2026-02-01", vintage: "2025-01", grade: "D", metric: "ever_60_rate", mob: 13, value: "9.6%", baseline: "7.8%", dev: "+23%", sev: "warning" },
  { date: "2026-01-01", vintage: "2025-01", grade: "D", metric: "ever_30_rate", mob: 12, value: "14.5%", baseline: "12.0%", dev: "+21%", sev: "warning" },
  { date: "2025-11-01", vintage: "2025-01", grade: "D", metric: "ever_30_rate", mob: 10, value: "12.1%", baseline: "10.5%", dev: "+15%", sev: "watch" },
];

// ── Shared Components ──
const StatusDot = ({ s, size = 7 }) => (
  <span style={{ display:"inline-block", width:size, height:size, borderRadius:"50%",
    background: s==="good"?C.good:s==="warning"?C.warn:s==="critical"?C.crit:C.textDim,
    boxShadow:`0 0 ${size}px ${s==="good"?C.good:s==="warning"?C.warn:s==="critical"?C.crit:C.textDim}60`,
    flexShrink:0 }} />
);
const Badge = ({ text, color }) => (
  <span style={{ fontSize:10, fontFamily:F.mono, fontWeight:600, color, background:`${color}18`,
    border:`1px solid ${color}35`, padding:"2px 7px", borderRadius:3, textTransform:"uppercase", letterSpacing:.4 }}>{text}</span>
);
const Sparkline = ({ data, color, w=80, h=24 }) => {
  const max = Math.max(...data), min = Math.min(...data), range = max-min||1;
  const pts = data.map((v,i) => `${(i/(data.length-1))*w},${h-(((v-min)/range)*h*.8+h*.1)}`).join(" ");
  return <svg width={w} height={h} style={{display:"block"}}><polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"/></svg>;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active||!payload?.length) return null;
  return (
    <div style={{ background:"#1E2540", border:`1px solid ${C.border}`, borderRadius:6, padding:"8px 12px", fontSize:11, fontFamily:F.mono }}>
      <div style={{ color:C.textDim, marginBottom:4, fontWeight:600 }}>{label}</div>
      {payload.filter(p=>p.value!=null).map((p,i) => (
        <div key={i} style={{ color:p.color||p.stroke, marginBottom:1 }}>{p.dataKey}: {typeof p.value==="number"?p.value.toFixed(1):p.value}%</div>
      ))}
    </div>
  );
};

const GradeLegend = ({ items }) => (
  <div style={{ display:"flex", gap:14, flexWrap:"wrap" }}>
    {items.map(([label,color]) => (
      <div key={label} style={{ display:"flex", alignItems:"center", gap:5, fontFamily:F.mono, fontSize:11, color:C.textDim }}>
        <span style={{ width:10, height:2.5, background:color, borderRadius:2 }}/>{label}
      </div>
    ))}
  </div>
);

// ── Pages ──

function HomePage({ onSelectModel }) {
  const good = MODELS.filter(m=>m.status==="good").length;
  const warn = MODELS.filter(m=>m.status==="warning").length;
  const crit = MODELS.filter(m=>m.status==="critical").length;
  return (
    <div>
      <div style={{ display:"flex", gap:12, marginBottom:24, flexWrap:"wrap" }}>
        {[
          { label:"Models Monitored", value:MODELS.length, color:C.accent },
          { label:"Healthy", value:good, color:C.good },
          { label:"Warning", value:warn, color:C.warn },
          { label:"Critical", value:crit, color:C.crit },
        ].map((k,i) => (
          <div key={i} style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"14px 20px", flex:"1 1 120px", minWidth:120 }}>
            <div style={{ fontFamily:F.mono, fontSize:10, color:C.textDim, letterSpacing:.5, marginBottom:4 }}>{k.label.toUpperCase()}</div>
            <div style={{ fontFamily:F.mono, fontSize:28, fontWeight:700, color:k.color }}>{k.value}</div>
          </div>
        ))}
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(280px, 1fr))", gap:12 }}>
        {MODELS.map(m => (
          <div key={m.id} onClick={()=>onSelectModel(m)} style={{
            background:C.card, border:`1px solid ${C.border}`, borderRadius:10, padding:"18px 20px",
            cursor:"pointer", transition:"all .15s",
          }} onMouseEnter={e=>{e.currentTarget.style.borderColor=C.accent;e.currentTarget.style.background=C.cardHover}}
             onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border;e.currentTarget.style.background=C.card}}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:10 }}>
              <div>
                <div style={{ fontFamily:F.sans, fontSize:15, fontWeight:600, color:C.text }}>{m.name}</div>
                <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginTop:2 }}>v{m.version} · {m.window} window</div>
              </div>
              <StatusDot s={m.status} size={9}/>
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end" }}>
              <div>
                <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim }}>{m.activeVintages} active vintages</div>
                <div style={{ fontFamily:F.mono, fontSize:11, color:m.latestAlert==="—"?C.textMuted:C.warn, marginTop:2 }}>{m.latestAlert}</div>
              </div>
              <Sparkline data={m.sparkline} color={m.status==="good"?C.good:m.status==="warning"?C.warn:C.crit}/>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OverviewView() {
  const health = [
    { label:"Data Quality", status:"warning", metric:"1 feature elevated null rate", detail:"income: 1.2% vs 0.5% baseline" },
    { label:"Drift", status:"critical", metric:"1 feature PSI > 0.20", detail:"dti_ratio: PSI 0.22" },
    { label:"Performance", status:"warning", metric:"Grade D confirmed rate ↑", detail:"6.8% at M15 vs 5.0% baseline" },
  ];
  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:20 }}>
        {health.map((h,i) => (
          <div key={i} style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"16px 18px",
            borderTop:`3px solid ${h.status==="good"?C.good:h.status==="warning"?C.warn:C.crit}` }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8 }}>
              <StatusDot s={h.status}/><span style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text }}>{h.label}</span>
            </div>
            <div style={{ fontFamily:F.mono, fontSize:12, color:C.text, marginBottom:4 }}>{h.metric}</div>
            <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim }}>{h.detail}</div>
          </div>
        ))}
      </div>
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"16px 18px" }}>
        <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:4 }}>Active Vintages</div>
        <div style={{ fontFamily:F.mono, fontSize:10, color:C.textDim, marginBottom:10 }}>Confirmed bad rate by grade · Latest snapshot</div>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontFamily:F.mono, fontSize:11 }}>
            <thead><tr style={{ borderBottom:`1px solid ${C.border}` }}>
              {["Vintage","MOB","Accts","Grade A","Grade B","Grade C","Grade D","Portfolio","Status"].map(h => (
                <th key={h} style={{ padding:"6px 8px", textAlign:h==="Vintage"||h==="Status"?"left":"right", color:C.textDim, fontWeight:600, fontSize:10, letterSpacing:.4 }}>{h.toUpperCase()}</th>
              ))}
            </tr></thead>
            <tbody>{ZUUL_VINTAGES.map((v,i) => (
              <tr key={i} style={{ borderBottom:`1px solid ${C.border}15` }}>
                <td style={{ padding:"8px", color:C.text, fontWeight:600 }}>{v.vintage}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.textDim }}>{v.mob}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.textDim }}>{v.accts.toLocaleString()}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.gradeA }}>{v.gradeA}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.gradeB }}>{v.gradeB}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.gradeC }}>{v.gradeC}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.gradeD, fontWeight:600 }}>{v.gradeD}</td>
                <td style={{ padding:"8px", textAlign:"right", color:C.text }}>{v.portfolio}</td>
                <td style={{ padding:"8px" }}><StatusDot s={v.status}/></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function VintageView() {
  const [chart, setChart] = useState("separation");
  const charts = [
    { id:"separation", label:"Grade Separation" },
    { id:"crossvintage", label:"Cross-Vintage Trend" },
    { id:"overlay", label:"Vintage Overlay" },
    { id:"floorceil", label:"Floor / Ceiling" },
  ];
  return (
    <div>
      <div style={{ display:"flex", gap:6, marginBottom:16, flexWrap:"wrap" }}>
        {charts.map(c => (
          <button key={c.id} onClick={()=>setChart(c.id)} style={{
            background:chart===c.id?`${C.accent}20`:"transparent", border:`1px solid ${chart===c.id?`${C.accent}50`:"transparent"}`,
            borderRadius:5, padding:"5px 14px", cursor:"pointer", fontFamily:F.mono, fontSize:11, fontWeight:500,
            color:chart===c.id?C.accent:C.textDim, transition:"all .12s"
          }}>{c.label}</button>
        ))}
      </div>
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"18px 20px" }}>
        {chart==="separation" && <>
          <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Grade Separation — Confirmed Bad Rate</div>
          <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:12 }}>Vintage 2025-01 · Wide separation = strong discrimination</div>
          <GradeLegend items={[["Grade A",C.gradeA],["Grade B",C.gradeB],["Grade C",C.gradeC],["Grade D",C.gradeD]]}/>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={GRADE_SEP} margin={{top:15,right:20,bottom:5,left:5}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="mob" tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border}/>
              <YAxis tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border} unit="%"/>
              <Tooltip content={<CustomTooltip/>}/>
              <Line type="monotone" dataKey="D" stroke={C.gradeD} strokeWidth={2.5} dot={{r:3}}/>
              <Line type="monotone" dataKey="C" stroke={C.gradeC} strokeWidth={2} dot={{r:2.5}}/>
              <Line type="monotone" dataKey="B" stroke={C.gradeB} strokeWidth={2} dot={{r:2.5}}/>
              <Line type="monotone" dataKey="A" stroke={C.gradeA} strokeWidth={2} dot={{r:2.5}}/>
            </LineChart>
          </ResponsiveContainer>
          <div style={{ marginTop:10, padding:"10px 14px", borderRadius:5, background:C.goodDim, border:`1px solid ${C.good}30`,
            fontFamily:F.mono, fontSize:11, color:C.textDim }}>
            ✓ Grade separation is clean and monotonic (A &lt; B &lt; C &lt; D) at every MOB.
          </div>
        </>}
        {chart==="crossvintage" && <>
          <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Cross-Vintage Trend — Ever 60+ DPD at MOB 12</div>
          <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:12 }}>By grade across vintages · Grade D trending upward</div>
          <GradeLegend items={[["A",C.gradeA],["B",C.gradeB],["C",C.gradeC],["D",C.gradeD]]}/>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={CROSS_VINTAGE} margin={{top:15,right:20,bottom:5,left:5}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="v" tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border}/>
              <YAxis tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border} unit="%"/>
              <Tooltip content={<CustomTooltip/>}/>
              <Bar dataKey="A" fill={C.gradeA} radius={[2,2,0,0]}/>
              <Bar dataKey="B" fill={C.gradeB} radius={[2,2,0,0]}/>
              <Bar dataKey="C" fill={C.gradeC} radius={[2,2,0,0]}/>
              <Bar dataKey="D" fill={C.gradeD} radius={[2,2,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ marginTop:10, padding:"10px 14px", borderRadius:5, background:C.warnDim, border:`1px solid ${C.warn}30`,
            fontFamily:F.mono, fontSize:11, color:C.textDim }}>
            ⚠ Grade D ever-60+ rising: 8.0% → 9.5% over 5 quarters. Grades A–C stable.
          </div>
        </>}
        {chart==="overlay" && <>
          <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Vintage Overlay — Grade D Confirmed Bad Rate</div>
          <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:12 }}>Multiple vintages on same maturation axis</div>
          <GradeLegend items={[["24-07","#6B7280"],["24-10","#8B5CF6"],["25-01",C.warn],["25-04",C.crit]]}/>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={OVERLAY_DATA} margin={{top:15,right:20,bottom:5,left:5}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="mob" tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border}/>
              <YAxis tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border} unit="%"/>
              <Tooltip content={<CustomTooltip/>}/>
              <Line type="monotone" dataKey="24-07" stroke="#6B7280" strokeWidth={1.5} dot={{r:2.5}} strokeDasharray="5 5" connectNulls={false}/>
              <Line type="monotone" dataKey="24-10" stroke="#8B5CF6" strokeWidth={1.5} dot={{r:2.5}} strokeDasharray="5 5" connectNulls={false}/>
              <Line type="monotone" dataKey="25-01" stroke={C.warn} strokeWidth={2.5} dot={{r:3.5}} connectNulls={false}/>
              <Line type="monotone" dataKey="25-04" stroke={C.crit} strokeWidth={2.5} dot={{r:3.5}} connectNulls={false}/>
            </LineChart>
          </ResponsiveContainer>
          <div style={{ marginTop:10, padding:"10px 14px", borderRadius:5, background:C.critDim, border:`1px solid ${C.crit}30`,
            fontFamily:F.mono, fontSize:11, color:C.textDim }}>
            🔴 Vintage 25-04 tracking above 25-01 at same MOB. If trajectory holds, final Grade D bad rate could exceed 10%.
          </div>
        </>}
        {chart==="floorceil" && <>
          <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Floor & Ceiling — Portfolio Confirmed vs. Probable</div>
          <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:12 }}>Vintage 2025-01 · Gap narrows as vintage matures</div>
          <GradeLegend items={[["Confirmed (floor)",C.crit],["Probable (ceiling)",C.warn]]}/>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={FLOOR_CEIL} margin={{top:15,right:20,bottom:5,left:5}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
              <XAxis dataKey="mob" tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border}/>
              <YAxis tick={{fill:C.textDim,fontSize:11,fontFamily:F.mono}} stroke={C.border} unit="%" domain={[0,7]}/>
              <Tooltip content={<CustomTooltip/>}/>
              <Area type="monotone" dataKey="probable" stroke={C.warn} fill={C.warnDim} strokeWidth={2} dot={{r:2.5}}/>
              <Area type="monotone" dataKey="confirmed" stroke={C.crit} fill={C.critDim} strokeWidth={2.5} dot={{r:3}}/>
            </AreaChart>
          </ResponsiveContainer>
          <div style={{ marginTop:10, padding:"10px 14px", borderRadius:5, background:`${C.accent}10`, border:`1px solid ${C.accent}30`,
            fontFamily:F.mono, fontSize:11, color:C.textDim }}>
            ℹ At M12: floor = 1.4%, ceiling = 4.0%. By M24 both converge to 2.8% (final actual).
          </div>
        </>}
      </div>
    </div>
  );
}

function DQView() {
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"18px 20px" }}>
      <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Data Quality — Feature-Level</div>
      <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:14 }}>Latest vintage scored · Compared against baseline</div>
      <table style={{ width:"100%", borderCollapse:"collapse", fontFamily:F.mono, fontSize:11 }}>
        <thead><tr style={{ borderBottom:`1px solid ${C.border}` }}>
          {["Feature","Null Rate","Baseline","OOR Rate","Cardinality","Status"].map(h => (
            <th key={h} style={{ padding:"6px 8px", textAlign:h==="Feature"||h==="Status"?"left":"right", color:C.textDim, fontWeight:600, fontSize:10, letterSpacing:.4 }}>{h.toUpperCase()}</th>
          ))}
        </tr></thead>
        <tbody>{DQ_FEATURES.map((f,i) => (
          <tr key={i} style={{ borderBottom:`1px solid ${C.border}15` }}>
            <td style={{ padding:"8px", color:C.text, fontWeight:600 }}>{f.feature}</td>
            <td style={{ padding:"8px", textAlign:"right", color:f.null_rate>f.baseline_null*2?C.warn:C.textDim }}>{(f.null_rate*100).toFixed(2)}%</td>
            <td style={{ padding:"8px", textAlign:"right", color:C.textMuted }}>{(f.baseline_null*100).toFixed(2)}%</td>
            <td style={{ padding:"8px", textAlign:"right", color:C.textDim }}>{(f.oor_rate*100).toFixed(2)}%</td>
            <td style={{ padding:"8px", textAlign:"right", color:C.textDim }}>{f.cardinality}</td>
            <td style={{ padding:"8px" }}><Badge text={f.status} color={f.status==="good"?C.good:f.status==="warning"?C.warn:C.textDim}/></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function DriftView() {
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"18px 20px" }}>
      <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Feature Drift — PSI</div>
      <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:14 }}>Population Stability Index by feature · Warning: 0.10 · Critical: 0.25</div>
      <table style={{ width:"100%", borderCollapse:"collapse", fontFamily:F.mono, fontSize:11 }}>
        <thead><tr style={{ borderBottom:`1px solid ${C.border}` }}>
          {["Feature","Current PSI","Baseline","Trend (6 mo)","Status"].map(h => (
            <th key={h} style={{ padding:"6px 8px", textAlign:h==="Feature"||h==="Status"||h==="Trend (6 mo)"?"left":"right", color:C.textDim, fontWeight:600, fontSize:10, letterSpacing:.4 }}>{h.toUpperCase()}</th>
          ))}
        </tr></thead>
        <tbody>{DRIFT_FEATURES.map((f,i) => {
          const psiColor = f.psi>=0.25?C.crit:f.psi>=0.10?C.warn:C.good;
          return (
            <tr key={i} style={{ borderBottom:`1px solid ${C.border}15` }}>
              <td style={{ padding:"8px", color:C.text, fontWeight:600 }}>{f.feature}</td>
              <td style={{ padding:"8px", textAlign:"right", color:psiColor, fontWeight:600 }}>{f.psi.toFixed(2)}</td>
              <td style={{ padding:"8px", textAlign:"right", color:C.textMuted }}>{f.baseline.toFixed(2)}</td>
              <td style={{ padding:"8px" }}><Sparkline data={f.trend} color={psiColor} w={70} h={20}/></td>
              <td style={{ padding:"8px" }}><Badge text={f.status} color={f.status==="good"?C.good:f.status==="warning"?C.warn:C.crit}/></td>
            </tr>
          );
        })}</tbody>
      </table>
      <div style={{ marginTop:14, padding:"10px 14px", borderRadius:5, background:C.critDim, border:`1px solid ${C.crit}30`,
        fontFamily:F.mono, fontSize:11, color:C.textDim }}>
        🔴 dti_ratio PSI at 0.22 — above warning threshold. Investigate: DTI rounding change affecting Grade D originations.
      </div>
    </div>
  );
}

function AlertsView() {
  return (
    <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8, padding:"18px 20px" }}>
      <div style={{ fontFamily:F.sans, fontSize:14, fontWeight:600, color:C.text, marginBottom:2 }}>Alert History</div>
      <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim, marginBottom:14 }}>All threshold breaches · Last 6 months</div>
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontFamily:F.mono, fontSize:11, minWidth:700 }}>
          <thead><tr style={{ borderBottom:`1px solid ${C.border}` }}>
            {["Date","Vintage","Grade","Metric","MOB","Value","Baseline","Dev.","Severity"].map(h => (
              <th key={h} style={{ padding:"6px 8px", textAlign:"left", color:C.textDim, fontWeight:600, fontSize:10, letterSpacing:.4 }}>{h.toUpperCase()}</th>
            ))}
          </tr></thead>
          <tbody>{ALERTS.map((a,i) => (
            <tr key={i} style={{ borderBottom:`1px solid ${C.border}15` }}>
              <td style={{ padding:"8px", color:C.textDim }}>{a.date}</td>
              <td style={{ padding:"8px", color:C.text }}>{a.vintage}</td>
              <td style={{ padding:"8px", color:C.gradeD, fontWeight:600 }}>{a.grade}</td>
              <td style={{ padding:"8px", color:C.textDim }}>{a.metric}</td>
              <td style={{ padding:"8px", color:C.textDim }}>{a.mob}</td>
              <td style={{ padding:"8px", color:C.text }}>{a.value}</td>
              <td style={{ padding:"8px", color:C.textMuted }}>{a.baseline}</td>
              <td style={{ padding:"8px", color:a.sev==="critical"?C.crit:a.sev==="warning"?C.warn:C.textDim, fontWeight:600 }}>{a.dev}</td>
              <td style={{ padding:"8px" }}><Badge text={a.sev} color={a.sev==="critical"?C.crit:a.sev==="warning"?C.warn:C.textDim}/></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main App ──
export default function MandosDashboard() {
  const [selectedModel, setSelectedModel] = useState(null);
  const [view, setView] = useState("overview");

  const NAV = [
    { id:"overview", label:"Overview", icon:"◉" },
    { id:"vintages", label:"Vintage Analysis", icon:"◈" },
    { id:"dq", label:"Data Quality", icon:"◇" },
    { id:"drift", label:"Drift", icon:"◆" },
    { id:"alerts", label:"Alerts", icon:"⚑" },
  ];

  return (
    <div style={{ background:C.bg, minHeight:"100vh", color:C.text, fontFamily:F.sans }}>
      {/* Top Bar */}
      <div style={{ background:C.surface, borderBottom:`1px solid ${C.border}`, padding:"10px 24px",
        display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ fontFamily:F.mono, fontWeight:700, fontSize:18, color:C.accent, letterSpacing:-.3, cursor:"pointer" }}
            onClick={()=>{setSelectedModel(null);setView("overview")}}>MANDOS</span>
          {selectedModel && <>
            <span style={{ color:C.textMuted, fontSize:14 }}>/</span>
            <span style={{ fontFamily:F.mono, fontSize:13, color:C.text }}>{selectedModel.name}</span>
            <span style={{ fontFamily:F.mono, fontSize:11, color:C.textDim }}>v{selectedModel.version}</span>
          </>}
        </div>
        <div style={{ fontFamily:F.mono, fontSize:11, color:C.textDim }}>Last run: 2026-04-01 · Next: 2026-05-01</div>
      </div>

      {!selectedModel ? (
        <div style={{ padding:"24px" }}>
          <div style={{ fontFamily:F.sans, fontSize:20, fontWeight:600, color:C.text, marginBottom:4 }}>Model Portfolio</div>
          <div style={{ fontFamily:F.mono, fontSize:12, color:C.textDim, marginBottom:20 }}>Automotive Credit Risk · All monitored models</div>
          <HomePage onSelectModel={(m)=>{setSelectedModel(m);setView("overview")}}/>
        </div>
      ) : (
        <div style={{ display:"flex", minHeight:"calc(100vh - 45px)" }}>
          {/* Sidebar */}
          <div style={{ width:180, background:C.surface, borderRight:`1px solid ${C.border}`, padding:"16px 0", flexShrink:0 }}>
            {NAV.map(n => (
              <div key={n.id} onClick={()=>setView(n.id)} style={{
                padding:"9px 20px", cursor:"pointer", transition:"all .1s",
                background:view===n.id?`${C.accent}12`:"transparent",
                borderLeft:view===n.id?`2px solid ${C.accent}`:"2px solid transparent",
                color:view===n.id?C.accent:C.textDim,
                fontFamily:F.mono, fontSize:12, fontWeight:view===n.id?600:400,
                display:"flex", alignItems:"center", gap:8,
              }}><span style={{ fontSize:10 }}>{n.icon}</span>{n.label}</div>
            ))}
            <div style={{ borderTop:`1px solid ${C.border}`, margin:"12px 20px" }}/>
            <div onClick={()=>{setSelectedModel(null);setView("overview")}} style={{
              padding:"9px 20px", cursor:"pointer", fontFamily:F.mono, fontSize:11, color:C.textDim,
              display:"flex", alignItems:"center", gap:8,
            }}>← All Models</div>
          </div>
          {/* Content */}
          <div style={{ flex:1, padding:"20px 24px", overflowY:"auto", maxHeight:"calc(100vh - 45px)" }}>
            {view==="overview" && <OverviewView/>}
            {view==="vintages" && <VintageView/>}
            {view==="dq" && <DQView/>}
            {view==="drift" && <DriftView/>}
            {view==="alerts" && <AlertsView/>}
          </div>
        </div>
      )}
    </div>
  );
}
