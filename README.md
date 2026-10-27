# SpendSense AI

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-supported-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Plotly](https://img.shields.io/badge/Plotly-charts-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)

SpendSense AI helps you understand your personal cash flow with clear, multi-month analytics, category budgets, and practical financial insights. Record transactions, follow spending trends, and export your data from a polished Streamlit dashboard.

## Features

- **Multi-month analytics** — Explore income, expenses, savings, and category trends across monthly periods.
- **Budgeting engine** — Set category limits, monitor progress, compare spending with budgets, and spot unbudgeted expenses.
- **Financial insights** — Surface spending patterns and budget health from recorded activity.
- **Indian tax & 80C savings tracker** — Track Investment-category expenses toward the ₹1,50,000 80C limit and review Healthcare-category expenses as potential 80D deductions for the April–March financial year. Figures are estimates based on categories, not verified tax eligibility or insurance premiums.
- **What-if wealth simulator** — Model monthly savings from lower Food, Entertainment, and Shopping spending, then explore 1-, 3-, and 5-year compound-growth projections at an assumed 11% annual return.
- **Recurring subscription & bill detector** — Identify active monthly expense patterns from repeated descriptions, similar amounts, and payment dates; review possible forgotten or unwanted recurring charges.
- **Smart bill & receipt parser** — Upload JPG, PNG, or PDF receipts to extract suggested amounts, dates, and descriptions for the transaction form. OCR runs locally and detected fields should be checked before saving.
- **CSV data export** — Download transaction and budget exports from the Reports page.
- **Secure authentication** — Passwords are stored as salted scrypt hashes, accounts are isolated, failed sign-ins are rate-limited, and persistent sign-in is optional.

## Architecture

```text
┌────────────────────┐
│   Streamlit UI     │
│ app.py / views /   │
│    components      │
└─────────┬──────────┘
          │ user actions and data requests
          ▼
┌────────────────────┐
│  Analytics Engine  │
│ analytics.py /     │
│   insights.py      │
└─────────┬──────────┘
          │ database operations
          ▼
┌────────────────────┐
│   Database Layer   │
│   database.py      │
└─────────┬──────────┘
          │
          ▼
┌──────────────────────────────┐
│ SQLite (local) or PostgreSQL │
│     (hosted, e.g. Neon)      │
└──────────────────────────────┘
```

Query results flow back through the analytics engine to the Streamlit UI.
Receipt parsing runs locally in the app, while recurring-payment detection
and financial projections operate on transaction data without a separate
service.

### Technology stack

Python powers the transaction and analytics logic; Streamlit provides the interactive application; SQLite supports local use and PostgreSQL supports hosted deployments; Plotly renders interactive financial charts. Receipt images and scanned PDFs use the local Tesseract OCR engine.

## Local setup

### 1. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Image receipts and scanned PDFs use local Tesseract OCR. Install the
Tesseract system application and ensure its executable is on `PATH`; PDFs
with selectable text do not require OCR. Uploaded receipt content is parsed
locally by the app and is not sent to an external OCR service.

### 3. Configure the database and optional invite-only signup

Without `DATABASE_URL`, the app uses the local `spendsense.db` SQLite file. To use a hosted PostgreSQL database, set `DATABASE_URL` using the environment or Streamlit secrets, as shown below.

### 4. Start the app

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>.

## Environment variables and secrets

The app reads `DATABASE_URL` from the process environment or Streamlit secrets. Authentication reads `INVITE_CODE` from either source. `SESSION_SECRET` is included as a reserved configuration example but is **not currently used** by the authentication flow; persistent session tokens are generated cryptographically by the app.

### `.env` reference

The project does not automatically load `.env` files. Use this as a reference and add the values to your shell or deployment environment. `.env` is ignored by Git; never commit real credentials.

```dotenv
# Optional. If omitted, the app uses local SQLite.
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require

# Optional. When set, account registration requires this invite code.
INVITE_CODE=replace-with-a-long-random-invite-code

# Reserved example only; not currently consumed by the application.
SESSION_SECRET=replace-with-a-long-random-secret
```

For a local PowerShell session, set values before starting Streamlit:

```powershell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
$env:INVITE_CODE = "your-long-random-invite-code"
streamlit run app.py
```

Leave `DATABASE_URL` unset to use SQLite. If `INVITE_CODE` is unset, registration is open to anyone who can access the app.

### Streamlit `secrets.toml`

Alternatively, create `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
INVITE_CODE = "your-long-random-invite-code"

# Reserved example only; not currently consumed by the application.
SESSION_SECRET = "replace-with-a-long-random-secret"
```

This file is ignored by Git. For Streamlit Community Cloud, add the same settings in the app's Secrets configuration instead of committing the file.

The database layer enforces TLS for PostgreSQL connections. Do not share database URLs or publish local database files: they may contain private financial records and account data.

## Project structure

```text
app.py              Streamlit entry point, initialization, and routing
auth.py             Account authentication and session handling
database.py         SQLite/PostgreSQL access and schema management
analytics.py        Transaction normalization and financial calculations
insights.py         Financial insight generation
components/         Reusable charts, cards, and UI components
views/              Dashboard, transactions, budgets, reports, and account views
utils/              Shared formatting, dates, styles, and constants
```

## Disclaimer

Insights and projections are estimates based on recorded data. They are for informational purposes only and are not professional financial, tax, investment, or legal advice.
