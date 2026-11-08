import os
import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

st.set_page_config(page_title="DataGhost", page_icon="👻", layout="wide")
DB = "workspace.default"
cfg = Config()

# ---------------- Databricks connection ----------------
@st.cache_resource
def conn():
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate,
    )

@st.cache_data(ttl=600)
def q(query: str) -> pd.DataFrame:
    with conn().cursor() as c:
        c.execute(query)
        return c.fetchall_arrow().to_pandas()

@st.cache_data(ttl=3600)
def cols(table):
    return list(q(f"SELECT * FROM {DB}.{table} LIMIT 0").columns)

def pick(table, options):
    return next((c for c in options if c in cols(table)), None)

# Auto-detect column names from the notebooks
EMP   = pick("gold_risk", ["employee_id", "user_id", "emp_id"])
SCORE = pick("gold_risk", ["risk_score", "risk", "anomaly_score", "score"])
RDATE = pick("gold_risk", ["date", "event_date", "activity_date", "day"])
B_EMP = pick("bronze_events", ["employee_id", "user_id", "emp_id"])
TS    = pick("bronze_events", ["timestamp", "event_time", "event_timestamp", "ts", "datetime", "date"])
ETYPE = pick("bronze_events", ["event_type", "activity", "action", "type"])
DEPT  = pick("bronze_events", ["department", "dept"])

def fmt_id(x):
    try: return str(int(float(x)))
    except: return str(x)

def top_risk(n=10):
    return q(f"""SELECT `{EMP}` AS employee_id, ROUND(MAX(`{SCORE}`), 3) AS max_risk
                 FROM {DB}.gold_risk GROUP BY `{EMP}` ORDER BY max_risk DESC LIMIT {int(n)}""")

def emp_events(emp, limit=200):
    order = f"ORDER BY `{TS}`" if TS else ""
    return q(f"SELECT * FROM {DB}.bronze_events WHERE `{B_EMP}` = {float(emp)} {order} LIMIT {int(limit)}")

def reports():
    try: return q(f"SELECT * FROM {DB}.incident_reports")
    except Exception: return pd.DataFrame()

def report_for(emp):
    r = reports()
    if r.empty: return None
    m = r[r["employee_id"].astype(float) == float(emp)]
    return None if m.empty else m.iloc[0]

def show_report(rep):
    sev_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(rep["severity"], "⚪")
    st.markdown(f"### {sev_color} {rep['severity']} — Employee {fmt_id(rep['employee_id'])}")
    st.caption(f"Risk score {rep['risk_score']:.3f} · Evidence check: {rep['grounding']} · {rep['model']}")
    st.write(rep["summary"])
    for title, key in [("What happened", "what_happened"), ("Why it's unusual", "why_unusual"),
                       ("Possible innocent explanations", "innocent_explanations"),
                       ("Recommended next steps", "next_steps")]:
        with st.expander(title, expanded=(key == "what_happened")):
            for line in str(rep[key]).split("\n"):
                if line.strip(): st.markdown(f"- {line}")

# ---------------- Header ----------------
st.title("👻 DataGhost")
st.caption("Insider-threat detection · Databricks (Spark, Delta, MLflow) + Gemini AI · all data is synthetic")

tab1, tab2, tab3 = st.tabs(["📊 Security Dashboard", "🔍 Investigate Employee", "🤖 AI Investigator"])

# ---------------- Tab 1: Dashboard ----------------
with tab1:
    k = q(f"SELECT COUNT(*) AS events, COUNT(DISTINCT `{B_EMP}`) AS emps FROM {DB}.bronze_events").iloc[0]
    rep = reports()
    high = 0 if rep.empty else rep["severity"].isin(["High", "Critical"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activity events", f"{int(k['events']):,}")
    c2.metric("Employees monitored", int(k["emps"]))
    c3.metric("AI investigations", len(rep))
    c4.metric("High / Critical cases", int(high))

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 riskiest employees")
        t = top_risk(10)
        t["employee_id"] = t["employee_id"].map(fmt_id)
        st.bar_chart(t, x="employee_id", y="max_risk", horizontal=True)
    with right:
        if RDATE:
            st.subheader("Company risk over time")
            d = q(f"""SELECT `{RDATE}` AS day, AVG(`{SCORE}`) AS avg_risk, MAX(`{SCORE}`) AS max_risk
                      FROM {DB}.gold_risk GROUP BY `{RDATE}` ORDER BY day""")
            st.line_chart(d, x="day", y=["avg_risk", "max_risk"])

    left, right = st.columns(2)
    with left:
        if ETYPE:
            st.subheader("Activity by type")
            st.bar_chart(q(f"SELECT `{ETYPE}` AS type, COUNT(*) AS n FROM {DB}.bronze_events GROUP BY 1"),
                         x="type", y="n")
    with right:
        if DEPT:
            st.subheader("Average peak risk by department")
            dep = q(f"""SELECT b.dept, ROUND(AVG(r.m), 3) AS avg_peak_risk
                        FROM (SELECT `{EMP}` AS e, MAX(`{SCORE}`) AS m FROM {DB}.gold_risk GROUP BY 1) r
                        JOIN (SELECT DISTINCT `{B_EMP}` AS e, `{DEPT}` AS dept FROM {DB}.bronze_events) b
                        ON r.e = b.e GROUP BY b.dept ORDER BY 2 DESC""")
            st.bar_chart(dep, x="dept", y="avg_peak_risk")

    if not rep.empty:
        st.subheader("🚨 Latest AI incident reports")
        st.dataframe(rep[["employee_id", "severity", "risk_score", "summary"]]
                     .assign(employee_id=rep["employee_id"].map(fmt_id)),
                     use_container_width=True, hide_index=True)

# ---------------- Tab 2: Investigate an employee ----------------
with tab2:
    choices = top_risk(25)["employee_id"].tolist()
    emp = st.selectbox("Employee (ranked by risk)", choices, format_func=fmt_id)

    if RDATE:
        st.subheader("Daily risk score")
        r = q(f"SELECT `{RDATE}` AS day, `{SCORE}` AS risk FROM {DB}.gold_risk "
              f"WHERE `{EMP}` = {float(emp)} ORDER BY day")
        st.line_chart(r, x="day", y="risk")

    rep = report_for(emp)
    if rep is not None:
        st.subheader("Gemini investigation report")
        show_report(rep)
    else:
        st.info("No AI report for this employee yet. Ask the AI Investigator tab!")

    st.subheader("Activity log")
    st.dataframe(emp_events(emp), use_container_width=True, hide_index=True)

# ---------------- Tab 3: AI Investigator (Gemini agent) ----------------
with tab3:
    from google import genai
    from google.genai import types

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
Keep answers short and well formatted."""

    st.caption("Ask questions in plain English. Gemini decides which Databricks tables to query.")
    if "chat" not in st.session_state:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        st.session_state.chat = client.chats.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM, temperature=0.2,
                tools=[get_top_risky_employees, get_employee_events,
                       get_employee_risk_history, get_incident_report]))
        st.session_state.msgs = []

    for role, text in st.session_state.msgs:
        st.chat_message(role).markdown(text)

    examples = st.columns(3)
    preset = None
    if examples[0].button("Who is the riskiest employee and why?"): preset = "Who is the riskiest employee and why?"
    if examples[1].button("Compare the top 3 risky employees"):     preset = "Compare the top 3 risky employees."
    if examples[2].button("Any signs of USB data theft?"):           preset = "Are there signs of data theft via USB devices?"

    prompt = st.chat_input("Ask DataGhost…") or preset
    if prompt:
        st.session_state.msgs.append(("user", prompt))
        st.chat_message("user").markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Investigating in Databricks…"):
                try:
                    resp = st.session_state.chat.send_message(prompt)
                    used = [p.function_call.name for c in (resp.automatic_function_calling_history or [])
                            for p in (c.parts or []) if getattr(p, "function_call", None)]
                    answer = resp.text
                    if used:
                        answer += "\n\n*🔧 Databricks lookups: " + ", ".join(dict.fromkeys(used)) + "*"
                except Exception as e:
                    answer = ("⚠️ Gemini is busy or over its free quota right now. Try again in a minute.\n\n"
                              f"`{str(e)[:120]}`")
            st.markdown(answer)
        st.session_state.msgs.append(("assistant", answer))
