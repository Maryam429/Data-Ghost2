DataGhost: AI-powered insider threat detection. Databricks (Spark, Delta Lake, MLflow) profiles employee behavior and scores risky data movement; a Gemini AI agent investigates alerts and explains them in plain English. All data is synthetic.

# 👻 DataGhost

**AI-powered insider threat detection, built on Databricks and Gemini.**

DataGhost watches how employees interact with sensitive data, learns what "normal" looks like for each person, and flags behavior that looks like data theft — then uses a Gemini AI agent to investigate each alert and explain it in plain English.

> Built for **TAMU Datathon 2026** — Databricks Challenge.
> ⚠️ All employees, files, and activity in this project are **synthetic**. DataGhost flags patterns for human review; it never claims anyone is guilty.

---

## The problem

Insider data leaks — an employee downloading thousands of customer records, copying confidential files to a USB drive, or a quiet account suddenly opening financial records — are often discovered months later. Security teams drown in raw logs and have no time to connect the dots.

## What DataGhost does

| | |
|---|---|
| **Monitor** | Ingests employee activity logs (logons, file access, USB devices, external emails) |
| **Profile** | Builds a behavioral baseline for every employee using Spark |
| **Detect** | Combines security rules + an Isolation Forest anomaly model into a single risk score |
| **Investigate** | A Gemini agent reviews the evidence and writes a grounded incident report |
| **Visualize** | A Databricks App with a security dashboard, employee timelines, and an AI chat investigator |

---

## Architecture

```
Synthetic activity generator (PySpark)
            │
            ▼
   Bronze  ── raw events (Delta table: bronze_events)
            │
            ▼
   Silver/Gold ── cleaned events + per-employee daily behavior features
            │      & z-scores vs. each employee's own baseline (gold_features)
            ▼
   Detection ── rule-based flags + Isolation Forest (tracked in MLflow)
            │      → combined risk score (gold_risk)
            ▼
   Gemini Investigator ── evidence → structured incident report
            │               with citation check (incident_reports)
            ▼
   DataGhost App (Databricks App, Streamlit)
      ├─ 📊 Security Dashboard
      ├─ 🔍 Employee Investigation
      └─ 🤖 AI Investigator (Gemini agent with Databricks SQL tools)
```

### How we use Databricks
- **Delta Lake + Unity Catalog** — every stage is stored as a governed Delta table in `workspace.default`.
- **Apache Spark** — generates and processes the activity logs, builds daily behavior features and per-employee baselines.
- **MLflow** — tracks the Isolation Forest anomaly-detection model and its parameters.
- **Databricks Secrets** — the Gemini API key is stored in a secret scope, never in code.
- **Databricks SQL Warehouse** — serves the app's queries.
- **Databricks Apps** — hosts the DataGhost web app.

### How we use Gemini
1. **Incident reports** — for each high-risk employee, Gemini receives their risky days, their events, and their normal baseline, and returns a structured JSON report: severity, summary, what happened, why it's unusual, **possible innocent explanations**, and recommended next steps.
2. **Grounding check** — Gemini must cite specific event IDs; our code verifies every cited event actually exists (e.g. *"7/7 cited events verified"*).
3. **AI Investigator agent** — in the app, Gemini uses **function calling** to query Databricks itself (top risky employees, an employee's events, their risk history, saved reports) before answering questions like *"Who is the riskiest employee and why?"*
4. **Red Ghost (bonus)** — Gemini *invents* a new synthetic insider-theft scenario, which is injected into the pipeline to test whether DataGhost catches an attack we didn't design.

---

## Repository structure

```
DataGhost/
├── notebooks/
│   ├── 01_generate_data      # synthetic company + planted insiders → bronze_events
│   ├── 02_features           # cleaning, daily features, baselines → gold_features
│   ├── 03_detection          # rules + Isolation Forest (MLflow) → gold_risk
│   └── 04_gemini             # Gemini investigation reports → incident_reports
├── app/
│   ├── app.py                # Streamlit app (dashboard, investigation, AI agent)
│   ├── app.yaml              # Databricks App config
│   └── requirements.txt
└── README.md
```

---

## Running it yourself

### 1. Databricks setup
1. Create a [Databricks Free Edition](https://www.databricks.com/learn/free-edition) workspace.
2. Import the notebooks from `notebooks/` (or clone this repo with **Git folders**).
3. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com).

### 2. Store the Gemini key securely
In the Gemini notebook, run the one-time setup cell: it creates a text box at the top of the notebook — paste the key there and re-run the cell. The key is saved to the secret scope `dataghost` / `gemini_key` and never appears in code.

### 3. Run the pipeline
Run the notebooks in order: `01 → 02 → 03 → 04`. Each one saves a Delta table the next one reads.

### 4. Deploy the app
1. **New → App → Create a custom app**, name it `dataghost`.
2. Add resources:
   - **SQL warehouse** → resource key `sql-warehouse`
   - **Secret** `dataghost/gemini_key` → resource key `gemini-key`
3. Upload the files in `app/`.
4. Grant the app's service principal read access:
   ```sql
   GRANT USE CATALOG ON CATALOG workspace TO `<APP_SERVICE_PRINCIPAL_ID>`;
   GRANT USE SCHEMA ON SCHEMA workspace.default TO `<APP_SERVICE_PRINCIPAL_ID>`;
   GRANT SELECT ON SCHEMA workspace.default TO `<APP_SERVICE_PRINCIPAL_ID>`;
   ```
5. Click **Deploy**.

---

## Demo walkthrough

1. **Dashboard** — a company of 150 employees and tens of thousands of normal activity events.
2. **The anomaly** — one employee is normal for weeks, then suddenly opens hundreds of confidential files and connects a USB drive after hours.
3. **Detection** — rules and the anomaly model push their risk score to the top.
4. **AI investigation** — Gemini explains what happened, cites the exact evidence, and offers a possible innocent explanation.
5. **Ask the agent** — *"Compare the top 3 risky employees"* — Gemini queries Databricks live and answers.

---

## Responsible AI

- **Synthetic data only** — no real people or company records.
- **Human in the loop** — DataGhost recommends investigations; it never takes action or makes accusations.
- **Explainable** — every alert shows which rules and features drove the score.
- **Grounded AI** — Gemini must cite evidence, and citations are verified automatically.
- **Innocent explanations** — every report includes plausible non-malicious reasons for the behavior.

---

## Built with

Databricks · Apache Spark · Delta Lake · Unity Catalog · MLflow · Databricks Apps · scikit-learn · Google Gemini API (`google-genai`) · Streamlit

## Team

Hemamrutha Krishna
Maryam Danish
Shriya Nair
