import os
import html
import base64
import pandas as pd
import altair as alt
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

# =====================================================================
#  Page setup
# =====================================================================
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
_icon = None
if os.path.exists(ICON_PATH):
    try:
        from PIL import Image
        _icon = Image.open(ICON_PATH)
    except Exception:
        _icon = None

st.set_page_config(page_title="DataGhost · Insider Threat Detection",
                   page_icon=_icon or "👻", layout="wide")

DB = "workspace.default"
cfg = Config()

# Brand palette (matches the DataGhost logo)
BG, CARD, BORDER = "#0a0d18", "#141a2e", "#232b45"
TEAL, VIOLET, RED = "#7cf5e1", "#6c63ff", "#ff4d5e"
ORANGE, AMBER = "#ff8a4c", "#ffd166"
TEXT, MUTED, GRID = "#e6e9f2", "#8b93b0", "#1c2340"
CATEGORICAL = [TEAL, VIOLET, RED, AMBER, "#4cc9ff", ORANGE]

def logo_b64():
    if not os.path.exists(ICON_PATH):
        return ""
    with open(ICON_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

# =====================================================================
#  Styling
# =====================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, .stApp, [class*="st-"], button, input, textarea {{ font-family: 'Inter', sans-serif; }}
.stApp {{
  background:
    radial-gradient(1100px 520px at 0% -10%, rgba(108,99,255,.14), transparent 60%),
    radial-gradient(900px 480px at 100% -5%, rgba(124,245,225,.09), transparent 60%),
    {BG};
}}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1380px; }}

/* ---------- header ---------- */
.dg-header {{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:18px 24px; margin-bottom:18px; border-radius:20px;
  background: linear-gradient(135deg, {CARD} 0%, #10152a 100%);
  border:1px solid {BORDER};
}}
.dg-brand {{ display:flex; align-items:center; gap:16px; }}
.dg-brand img {{ width:58px; height:58px; border-radius:15px; box-shadow:0 0 24px rgba(124,245,225,.25); }}
.dg-title {{ font-size:2rem; font-weight:800; letter-spacing:-.03em; color:#fff; line-height:1; }}
.dg-title span {{ background:linear-gradient(90deg,{TEAL},{VIOLET}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.dg-sub {{ color:{MUTED}; font-size:.9rem; margin-top:6px; }}
.dg-pills {{ display:flex; gap:8px; flex-wrap:wrap; }}
.dg-pill {{
  display:inline-flex; align-items:center; gap:8px; padding:7px 13px; border-radius:999px;
  font-size:.78rem; font-weight:600; color:{MUTED}; background:rgba(255,255,255,.03); border:1px solid {BORDER};
}}
.dg-pill.live {{ color:{TEAL}; background:rgba(124,245,225,.08); border-color:rgba(124,245,225,.3); }}
.dg-dot {{ width:8px; height:8px; border-radius:50%; background:{TEAL}; box-shadow:0 0 10px {TEAL}; }}

/* ---------- KPI cards ---------- */
.dg-kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:6px 0 18px; }}
.dg-kpi {{
  position:relative; overflow:hidden; padding:18px 20px; border-radius:16px;
  background:{CARD}; border:1px solid {BORDER};
}}
.dg-kpi::before {{ content:""; position:absolute; inset:0 auto 0 0; width:4px; background:var(--accent); }}
.dg-kpi::after {{
  content:""; position:absolute; right:-40px; top:-40px; width:120px; height:120px; border-radius:50%;
  background:var(--accent); opacity:.07;
}}
.dg-kpi .label {{ color:{MUTED}; font-size:.74rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }}
.dg-kpi .value {{ color:#fff; font-size:2.1rem; font-weight:800; letter-spacing:-.03em; margin-top:6px; }}
.dg-kpi .hint  {{ color:{MUTED}; font-size:.8rem; margin-top:2px; }}

/* ---------- section titles ---------- */
.dg-h {{ color:{TEXT}; font-size:1.02rem; font-weight:700; margin:2px 0 0; }}
.dg-hsub {{ color:{MUTED}; font-size:.82rem; margin:2px 0 6px; }}
.dg-legend {{ display:flex; gap:16px; color:{MUTED}; font-size:.8rem; margin-bottom:4px; }}
.dg-legend i {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px; }}

/* ---------- bordered containers become cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background:{CARD}; border:1px solid {BORDER} !important; border-radius:16px !important;
}}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
  gap:6px; padding:6px; border-radius:14px; background:{CARD}; border:1px solid {BORDER}; width:fit-content;
}}
.stTabs [data-baseweb="tab"] {{
  height:42px; padding:0 20px; border-radius:10px; color:{MUTED}; font-weight:600; background:transparent;
}}
.stTabs [aria-selected="true"] {{ background:rgba(124,245,225,.10) !important; color:{TEAL} !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* ---------- incidents ---------- */
.dg-inc {{ display:grid; grid-template-columns:110px 92px 1fr; gap:16px; align-items:start;
          padding:14px 4px; border-top:1px solid {BORDER}; }}
.dg-inc:first-child {{ border-top:none; }}
.dg-emp {{ font-family:'JetBrains Mono',monospace; font-weight:700; color:{TEXT}; }}
.dg-score {{ font-family:'JetBrains Mono',monospace; color:{MUTED}; font-size:.8rem; margin-top:2px; }}
.dg-txt {{ color:#c9cee0; font-size:.9rem; line-height:1.5; }}
.sev {{ display:inline-block; padding:4px 10px; border-radius:999px; font-size:.7rem; font-weight:800;
        letter-spacing:.07em; text-transform:uppercase; border:1px solid; }}
.sev-Critical {{ color:{RED};    background:rgba(255,77,94,.12);  border-color:rgba(255,77,94,.45); }}
.sev-High     {{ color:{ORANGE}; background:rgba(255,138,76,.12); border-color:rgba(255,138,76,.45); }}
.sev-Medium   {{ color:{AMBER};  background:rgba(255,209,102,.10); border-color:rgba(255,209,102,.4); }}
.sev-Low      {{ color:{TEAL};   background:rgba(124,245,225,.10); border-color:rgba(124,245,225,.4); }}

/* ---------- report ---------- */
.dg-report-top {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:10px; }}
.dg-report-top .meta {{ color:{MUTED}; font-size:.82rem; }}
.dg-check {{ color:{TEAL}; font-weight:700; }}
.dg-summary {{ color:{TEXT}; font-size:1rem; line-height:1.6; padding:14px 16px; border-radius:12px;
               background:rgba(108,99,255,.08); border:1px solid rgba(108,99,255,.25); margin-bottom:14px; }}
.dg-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.dg-sec {{ padding:14px 16px; border-radius:12px; background:rgba(255,255,255,.02); border:1px solid {BORDER}; }}
.dg-sec h5 {{ margin:0 0 8px; font-size:.74rem; letter-spacing:.09em; text-transform:uppercase; color:var(--c); }}
.dg-sec ul {{ margin:0; padding-left:18px; color:#c9cee0; font-size:.88rem; line-height:1.55; }}

/* ---------- profile strip ---------- */
.dg-prof {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:8px 0 16px; }}

/* ---------- buttons, inputs, chat ---------- */
.stButton > button {{
  width:100%; background:{CARD}; color:{TEXT}; border:1px solid {BORDER}; border-radius:12px;
  padding:10px 14px; font-weight:600; transition:all .15s ease;
}}
.stButton > button:hover {{ border-color:{TEAL}; color:{TEAL}; background:rgba(124,245,225,.06); }}
div[data-baseweb="select"] > div {{ background:{CARD}; border-color:{BORDER}; border-radius:12px; }}
[data-testid="stChatMessage"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; }}
[data-testid="stChatInput"] textarea {{ background:{CARD}; }}
.dg-tool {{ display:flex; flex-direction:column; align-items:flex-start; gap:6px; padding:12px 0; border-top:1px solid {BORDER}; }}
.dg-tool:first-of-type {{ border-top:none; }}
.dg-tool code {{ color:{TEAL}; background:rgba(124,245,225,.08); padding:2px 6px; border-radius:6px; font-size:.8rem; }}
.dg-tool div {{ color:{MUTED}; font-size:.82rem; }}
.dg-footer {{ text-align:center; color:{MUTED}; font-size:.78rem; margin-top:28px; opacity:.8; }}

@media (max-width: 900px) {{
  .dg-kpis, .dg-prof {{ grid-template-columns:repeat(2,1fr); }}
  .dg-grid {{ grid-template-columns:1fr; }}
  .dg-header {{ flex-direction:column; align-items:flex-start; }}
  .dg-inc {{ grid-template-columns:1fr; gap:6px; }}
}}
</style>
""", unsafe_allow_html=True)

# =====================================================================
#  Databricks data access
# =====================================================================
@st.cache_resource
def conn():
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate,
    )

@st.cache_data(ttl=600, show_spinner=False)
def q(query: str) -> pd.DataFrame:
    with conn().cursor() as c:
        c.execute(query)
        return c.fetchall_arrow().to_pandas()

@st.cache_data(ttl=3600, show_spinner=False)
def cols(table):
    return list(q(f"SELECT * FROM {DB}.{table} LIMIT 0").columns)

def pick(table, options):
    return next((c for c in options if c in cols(table)), None)

with st.spinner("Connecting to Databricks…"):
    EMP   = pick("gold_risk", ["employee_id", "user_id", "emp_id"])
    SCORE = pick("gold_risk", ["risk_score", "risk", "anomaly_score", "score"])
    RDATE = pick("gold_risk", ["date", "event_date", "activity_date", "day"])
    B_EMP = pick("bronze_events", ["employee_id", "user_id", "emp_id"])
    TS    = pick("bronze_events", ["timestamp", "event_time", "event_timestamp", "ts", "datetime", "date"])
    ETYPE = pick("bronze_events", ["event_type", "activity", "action", "type"])
    DEPT  = pick("bronze_events", ["department", "dept"])

def fmt_id(x):
    try:
        return str(int(float(x)))
    except Exception:
        return str(x)

def top_risk(n=10):
    return q(f"""SELECT `{EMP}` AS employee_id, ROUND(MAX(`{SCORE}`), 3) AS max_risk
                 FROM {DB}.gold_risk GROUP BY `{EMP}` ORDER BY max_risk DESC LIMIT {int(n)}""")

def emp_events(emp, limit=200):
    order = f"ORDER BY `{TS}`" if TS else ""
    return q(f"SELECT * FROM {DB}.bronze_events WHERE `{B_EMP}` = {float(emp)} {order} LIMIT {int(limit)}")

def reports():
    try:
        return q(f"SELECT * FROM {DB}.incident_reports")
    except Exception:
        return pd.DataFrame()

def report_for(emp):
    r = reports()
    if r.empty:
        return None
    m = r[pd.to_numeric(r["employee_id"], errors="coerce") == float(emp)]
    return None if m.empty else m.iloc[0]

# =====================================================================
#  UI helpers
# =====================================================================
def esc(x):
    return html.escape(str(x if x is not None else ""))

def sev_badge(sev):
    sev = str(sev or "Unknown").strip().title()
    cls = sev if sev in ("Critical", "High", "Medium", "Low") else "Low"
    return f'<span class="sev sev-{cls}">{esc(sev)}</span>'

def bullets(text):
    items = [l.strip(" -•\t") for l in str(text or "").split("\n") if l.strip()]
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>" if items else "<ul><li>—</li></ul>"

def kpi(label, value, hint, accent):
    return (f'<div class="dg-kpi" style="--accent:{accent}"><div class="label">{label}</div>'
            f'<div class="value">{value}</div><div class="hint">{hint}</div></div>')

def section(title, sub=None):
    st.markdown(f'<div class="dg-h">{title}</div>' + (f'<div class="dg-hsub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)

def style(chart, height=300):
    return (chart.properties(height=height, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=GRID, domainColor=BORDER,
                            tickColor=BORDER, labelFont="Inter", titleFont="Inter", labelFontSize=11,
                            titleFontSize=11, titleFontWeight=600)
            .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFont="Inter", titleFont="Inter")
            .configure_text(font="Inter"))

def show_report(rep):
    model = esc(rep.get("model", "Gemini")) if hasattr(rep, "get") else "Gemini"
    st.markdown(f"""
<div class="dg-report-top">
  {sev_badge(rep['severity'])}
  <span class="dg-emp">Employee {esc(fmt_id(rep['employee_id']))}</span>
  <span class="meta">Risk score <b>{float(rep['risk_score']):.3f}</b></span>
  <span class="meta">· Evidence check <span class="dg-check">✓ {esc(rep['grounding'])}</span></span>
  <span class="meta">· {model}</span>
</div>
<div class="dg-summary">{esc(rep['summary'])}</div>
<div class="dg-grid">
  <div class="dg-sec" style="--c:{RED}"><h5>What happened</h5>{bullets(rep['what_happened'])}</div>
  <div class="dg-sec" style="--c:{ORANGE}"><h5>Why it's unusual</h5>{bullets(rep['why_unusual'])}</div>
  <div class="dg-sec" style="--c:{TEAL}"><h5>Possible innocent explanations</h5>{bullets(rep['innocent_explanations'])}</div>
  <div class="dg-sec" style="--c:{VIOLET}"><h5>Recommended next steps</h5>{bullets(rep['next_steps'])}</div>
</div>""", unsafe_allow_html=True)

# =====================================================================
#  Header
# =====================================================================
b64 = logo_b64()
logo_html = f'<img src="data:image/png;base64,{b64}"/>' if b64 else '<div style="font-size:42px">👻</div>'
st.markdown(f"""
<div class="dg-header">
  <div class="dg-brand">
    {logo_html}
    <div>
      <div class="dg-title">Data<span>Ghost</span></div>
      <div class="dg-sub">AI-powered insider threat detection</div>
    </div>
  </div>
  <div class="dg-pills">
    <span class="dg-pill live"><span class="dg-dot"></span>Live · Databricks SQL</span>
    <span class="dg-pill">Spark · Delta · MLflow</span>
    <span class="dg-pill">Gemini AI</span>
  </div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Security Overview", "Investigate Employee", "AI Investigator"])

# =====================================================================
#  Tab 1 — Security Overview
# =====================================================================
with tab1:
    k = q(f"SELECT COUNT(*) AS events, COUNT(DISTINCT `{B_EMP}`) AS emps FROM {DB}.bronze_events").iloc[0]
    rep = reports()
    n_rep = len(rep)
    high = 0 if rep.empty else int(rep["severity"].astype(str).str.title().isin(["High", "Critical"]).sum())

    st.markdown('<div class="dg-kpis">'
                + kpi("Activity events", f"{int(k['events']):,}", "logons, files, USB, email", TEAL)
                + kpi("Employees monitored", f"{int(k['emps']):,}", "behavior baselines built", VIOLET)
                + kpi("AI investigations", f"{n_rep}", "Gemini incident reports", AMBER)
                + kpi("High / critical cases", f"{high}", "need analyst review", RED)
                + "</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.25], gap="medium")
    with c1:
        with st.container(border=True):
            section("Top 10 riskiest employees", "Peak risk score from rules + Isolation Forest")
            t = top_risk(10)
            t["employee"] = t["employee_id"].map(lambda x: f"EMP-{fmt_id(x)}")
            bars = alt.Chart(t).mark_bar(cornerRadiusEnd=6, height=18).encode(
                x=alt.X("max_risk:Q", title="Peak risk score"),
                y=alt.Y("employee:N", sort="-x", title=None,
                        axis=alt.Axis(labelFont="JetBrains Mono", labelColor=TEXT)),
                color=alt.Color("max_risk:Q", scale=alt.Scale(range=[VIOLET, RED]), legend=None),
                tooltip=[alt.Tooltip("employee:N", title="Employee"), alt.Tooltip("max_risk:Q", title="Peak risk")],
            )
            labels = bars.mark_text(align="left", dx=6, color=TEXT, fontSize=11).encode(
                text=alt.Text("max_risk:Q", format=".2f"), color=alt.value(TEXT))
            st.altair_chart(style(bars + labels, 330), use_container_width=True)

    with c2:
        with st.container(border=True):
            section("Company risk over time", "Daily average vs. peak employee risk")
            if RDATE:
                d = q(f"""SELECT `{RDATE}` AS day, AVG(`{SCORE}`) AS avg_risk, MAX(`{SCORE}`) AS max_risk
                          FROM {DB}.gold_risk GROUP BY `{RDATE}` ORDER BY day""")
                d["day"] = pd.to_datetime(d["day"], errors="coerce")
                st.markdown(f'<div class="dg-legend"><span><i style="background:{TEAL}"></i>Average</span>'
                            f'<span><i style="background:{RED}"></i>Peak</span></div>', unsafe_allow_html=True)
                base = alt.Chart(d).encode(x=alt.X("day:T", title=None, axis=alt.Axis(format="%b %d")))
                area = base.mark_area(
                    line={"color": TEAL, "strokeWidth": 2},
                    color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0, stops=[
                        alt.GradientStop(color="rgba(124,245,225,0)", offset=0),
                        alt.GradientStop(color="rgba(124,245,225,0.35)", offset=1)]),
                ).encode(y=alt.Y("avg_risk:Q", title="Risk score"),
                         tooltip=[alt.Tooltip("day:T", format="%b %d"), alt.Tooltip("avg_risk:Q", format=".3f")])
                peak = base.mark_line(color=RED, strokeWidth=2, point=alt.OverlayMarkDef(color=RED, size=28)).encode(
                    y="max_risk:Q",
                    tooltip=[alt.Tooltip("day:T", format="%b %d"), alt.Tooltip("max_risk:Q", format=".3f")])
                st.altair_chart(style(area + peak, 306), use_container_width=True)
            else:
                st.info("No date column found in gold_risk.")

    c3, c4 = st.columns([1, 1.25], gap="medium")
    with c3:
        with st.container(border=True):
            section("Activity mix", "All monitored events by type")
            if ETYPE:
                a = q(f"SELECT `{ETYPE}` AS type, COUNT(*) AS n FROM {DB}.bronze_events GROUP BY 1 ORDER BY 2 DESC")
                donut = alt.Chart(a).mark_arc(innerRadius=72, outerRadius=118, cornerRadius=4, padAngle=0.015).encode(
                    theta="n:Q",
                    color=alt.Color("type:N", scale=alt.Scale(range=CATEGORICAL),
                                    legend=alt.Legend(title=None, orient="right")),
                    tooltip=["type:N", alt.Tooltip("n:Q", format=",")])
                st.altair_chart(style(donut, 270), use_container_width=True)
            else:
                st.info("No event-type column found.")

    with c4:
        with st.container(border=True):
            section("Risk by department", "Average peak risk of employees in each department")
            if DEPT:
                dep = q(f"""SELECT b.dept, ROUND(AVG(r.m), 3) AS avg_peak_risk
                            FROM (SELECT `{EMP}` AS e, MAX(`{SCORE}`) AS m FROM {DB}.gold_risk GROUP BY 1) r
                            JOIN (SELECT DISTINCT `{B_EMP}` AS e, `{DEPT}` AS dept FROM {DB}.bronze_events) b
                            ON r.e = b.e GROUP BY b.dept ORDER BY 2 DESC""")
                dbar = alt.Chart(dep).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=38).encode(
                    x=alt.X("dept:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0, labelColor=TEXT)),
                    y=alt.Y("avg_peak_risk:Q", title="Avg peak risk"),
                    color=alt.Color("avg_peak_risk:Q", scale=alt.Scale(range=[TEAL, VIOLET]), legend=None),
                    tooltip=["dept:N", alt.Tooltip("avg_peak_risk:Q", format=".3f")])
                st.altair_chart(style(dbar, 270), use_container_width=True)
            else:
                st.info("No department column found.")

    with st.container(border=True):
        section("AI incident queue", "Gemini investigations of the highest-risk employees")
        if rep.empty:
            st.info("No incident reports yet. Run the Gemini notebook to generate them.")
        else:
            rows = rep.sort_values("risk_score", ascending=False)
            items = "".join(
                f'<div class="dg-inc"><div><div class="dg-emp">EMP-{esc(fmt_id(r["employee_id"]))}</div>'
                f'<div class="dg-score">risk {float(r["risk_score"]):.3f}</div></div>'
                f'<div>{sev_badge(r["severity"])}</div><div class="dg-txt">{esc(r["summary"])}</div></div>'
                for _, r in rows.iterrows())
            st.markdown(items, unsafe_allow_html=True)

# =====================================================================
#  Tab 2 — Investigate an employee
# =====================================================================
with tab2:
    ranked = top_risk(25)
    choices = ranked["employee_id"].tolist()
    sel_col, _ = st.columns([1, 2])
    with sel_col:
        emp = st.selectbox("Select an employee (ranked by risk)", choices,
                           format_func=lambda x: f"EMP-{fmt_id(x)}")

    rank = choices.index(emp) + 1
    peak = float(ranked.loc[ranked["employee_id"] == emp, "max_risk"].iloc[0])
    ev = emp_events(emp)
    rep = report_for(emp)
    sev = rep["severity"] if rep is not None else "Not investigated"
    st.markdown('<div class="dg-prof">'
                + kpi("Risk rank", f"#{rank}", f"of {len(choices)} highest-risk", RED)
                + kpi("Peak risk score", f"{peak:.3f}", "rules + anomaly model", ORANGE)
                + kpi("Events reviewed", f"{len(ev):,}", "from bronze_events", TEAL)
                + kpi("AI severity", esc(sev), "Gemini assessment", VIOLET)
                + "</div>", unsafe_allow_html=True)

    with st.container(border=True):
        section("Daily risk timeline", "Red points mark this employee's riskiest days")
        if RDATE:
            r = q(f"SELECT `{RDATE}` AS day, `{SCORE}` AS risk FROM {DB}.gold_risk "
                  f"WHERE `{EMP}` = {float(emp)} ORDER BY day")
            r["day"] = pd.to_datetime(r["day"], errors="coerce")
            cutoff = r["risk"].nlargest(3).min() if len(r) else 0
            r["flag"] = r["risk"] >= cutoff
            base = alt.Chart(r).encode(x=alt.X("day:T", title=None, axis=alt.Axis(format="%b %d")),
                                       y=alt.Y("risk:Q", title="Risk score"))
            area = base.mark_area(
                line={"color": TEAL, "strokeWidth": 2},
                color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0, stops=[
                    alt.GradientStop(color="rgba(124,245,225,0)", offset=0),
                    alt.GradientStop(color="rgba(124,245,225,0.3)", offset=1)]))
            pts = base.mark_circle(size=90, color=RED, stroke=BG, strokeWidth=2).transform_filter(
                alt.datum.flag == True).encode(tooltip=[alt.Tooltip("day:T", format="%b %d"),
                                                        alt.Tooltip("risk:Q", format=".3f")])
            st.altair_chart(style(area + pts, 260), use_container_width=True)

    with st.container(border=True):
        section("Gemini investigation report")
        if rep is not None:
            show_report(rep)
        else:
            st.info("No AI report for this employee yet. Ask about them in the AI Investigator tab.")

    with st.container(border=True):
        section("Activity log", "Raw events for this employee (most recent 200)")
        st.dataframe(ev, use_container_width=True, hide_index=True, height=320)

# =====================================================================
#  Tab 3 — AI Investigator (Gemini agent with Databricks tools)
# =====================================================================
with tab3:
    def get_top_risky_employees(n: int = 10) -> str:
        """Return the n employees with the highest risk scores from the Databricks detection model."""
        return top_risk(n).to_csv(index=False)

    def get_employee_events(employee_id: float, limit: int = 60) -> str:
        """Return raw activity log events (logons, files, USB, emails) for one employee."""
        return emp_events(employee_id, limit).astype(str).to_csv(index=False)

    def get_employee_risk_history(employee_id: float) -> str:
        """Return an employee's daily risk scores so you can compare abnormal days to normal ones."""
        d = f"`{RDATE}`," if RDATE else ""
        return q(f"SELECT {d} `{SCORE}` FROM {DB}.gold_risk WHERE `{EMP}` = {float(employee_id)}").to_csv(index=False)

    def get_incident_report(employee_id: float) -> str:
        """Return the saved AI incident report for an employee, if one exists."""
        r = report_for(employee_id)
        return "No report exists." if r is None else r.to_json()

    SYSTEM = """You are DataGhost, a cautious insider-threat analyst. All data is synthetic.
Use your tools to look up evidence in the Databricks tables before answering.
Cite specific evidence (dates, event types, counts). Never claim someone is guilty;
describe patterns that warrant review and always mention a possible innocent explanation.
Keep answers short and well formatted with headings and bullet points."""

    chat_col, info_col = st.columns([2.3, 1], gap="medium")

    with info_col:
        with st.container(border=True):
            section("How the agent works", "Gemini chooses which Databricks lookups to run")
            st.markdown("""
<div class="dg-tool"><code>get_top_risky_employees</code><div>Ranks employees by peak risk score</div></div>
<div class="dg-tool"><code>get_employee_events</code><div>Pulls raw logon, file, USB and email events</div></div>
<div class="dg-tool"><code>get_employee_risk_history</code><div>Compares abnormal days with normal behavior</div></div>
<div class="dg-tool"><code>get_incident_report</code><div>Reads saved Gemini incident reports</div></div>
""", unsafe_allow_html=True)

    with chat_col:
        with st.container(border=True):
            section("Ask DataGhost", "Plain-English questions, answered with evidence from Databricks")

            if "chat" not in st.session_state:
                st.session_state.msgs = []
                st.session_state.chat = None
                st.session_state.chat_error = None
                key = os.getenv("GEMINI_API_KEY")
                if not key:
                    st.session_state.chat_error = "GEMINI_API_KEY is not set. Add the gemini-key secret resource to the app."
                else:
                    try:
                        from google import genai
                        from google.genai import types
                        client = genai.Client(api_key=key)
                        st.session_state.chat = client.chats.create(
                            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM, temperature=0.2,
                                tools=[get_top_risky_employees, get_employee_events,
                                       get_employee_risk_history, get_incident_report]))
                    except Exception as e:
                        st.session_state.chat_error = f"Could not start Gemini: {str(e)[:150]}"

            if st.session_state.chat_error:
                st.warning(st.session_state.chat_error)

            b1, b2, b3 = st.columns(3)
            preset = None
            if b1.button("Who is the riskiest employee and why?"):
                preset = "Who is the riskiest employee and why?"
            if b2.button("Compare the top 3 risky employees"):
                preset = "Compare the top 3 risky employees."
            if b3.button("Any signs of USB data theft?"):
                preset = "Are there signs of data theft via USB devices?"

            for role, text in st.session_state.msgs:
                with st.chat_message(role, avatar="👻" if role == "assistant" else "🧑‍💻"):
                    st.markdown(text)

            prompt = st.chat_input("Ask about an employee, a department, or a pattern…") or preset
            if prompt and st.session_state.chat is not None:
                st.session_state.msgs.append(("user", prompt))
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(prompt)
                with st.chat_message("assistant", avatar="👻"):
                    with st.spinner("Investigating in Databricks…"):
                        try:
                            resp = st.session_state.chat.send_message(prompt)
                            used = [p.function_call.name
                                    for c in (resp.automatic_function_calling_history or [])
                                    for p in (c.parts or []) if getattr(p, "function_call", None)]
                            answer = resp.text or "_No answer returned._"
                            if used:
                                answer += "\n\n---\n*🔧 Databricks lookups: " + ", ".join(
                                    f"`{u}`" for u in dict.fromkeys(used)) + "*"
                        except Exception as e:
                            answer = ("⚠️ Gemini is busy or over its free quota right now. "
                                      f"Try again in a minute.\n\n`{str(e)[:120]}`")
                    st.markdown(answer)
                st.session_state.msgs.append(("assistant", answer))

st.markdown('<div class="dg-footer">DataGhost · Databricks + Gemini · All data is synthetic · '
            'Flags patterns for human review — never a verdict</div>', unsafe_allow_html=True)
