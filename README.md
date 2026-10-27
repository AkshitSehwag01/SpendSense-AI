# SpendSense AI

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20ready-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-local%20database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Plotly](https://img.shields.io/badge/Plotly-interactive%20charts-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-analytics-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-4B8BBE)](https://github.com/tesseract-ocr/tesseract)

**Intelligent personal finance tracking, built for clearer everyday decisions.**
SpendSense AI brings transactions, budgets, and financial insights together in
one polished dashboard, with local-first development and production-ready
SQLite or PostgreSQL storage.

## Features

### Core finance tools

- **💬 Ask SpendSense — natural language search:** Ask plain-English questions
  from the dashboard for category totals, monthly spending, top categories,
  transaction counts, averages, and month-to-month comparisons.
- **🇮🇳 Indian tax & 80C investment planner:** Review Investment-category
  expenses against the ₹1,50,000 80C limit and Healthcare spending as potential
  80D deductions for the April–March Indian financial year, with progress and
  remaining-headroom indicators. These category-based figures are estimates,
  not verified deductions or tax advice.
- **🔮 What-If wealth & runway simulator:** Adjust a discretionary-spending
  reduction slider and project monthly savings growth over 1, 3, and 5 years
  using an assumed 11% annual return compounded monthly.
- **🔔 Recurring subscription & bill detector:** Identify active monthly
  expense patterns from repeated descriptions, similar amounts, and payment
  dates to help find forgotten recurring charges.
- **🧾 Smart receipt & invoice OCR parser:** Upload JPG, PNG, or PDF receipts
  to suggest a transaction date, vendor/description, and amount in the Add
  Transaction form. Image and scanned-PDF OCR uses the local Tesseract engine;
  review extracted details before saving.
- **📊 Multi-month dashboard & financial reports:** Explore cash flow,
  category budgets, and interactive Plotly visualizations with Indian
  lakh/crore (`₹`) formatting. The Reports page provides four one-click CSV
  exports: selected-month transactions, all transactions, monthly summary,
  and budgets.
- **Secure authentication & tenant isolation:** Passwords are stored as
  salted scrypt hashes; transaction and budget records are scoped to the
  signed-in user. Optional persistent sign-in uses the `spendsense_session`
  cookie. Registration can be gated with an invite code when `INVITE_CODE` is
  configured.

Additional tools include category budgeting, transaction management,
financial insights, and spreadsheet-safe CSV exports.

## Architecture

```text
┌───────────────────────────────────────────────┐
│ Streamlit UI                                   │
│ app.py · views/ · components/                  │
└───────────────────────┬───────────────────────┘
                        │ user input and reports
                        ▼
┌───────────────────────────────────────────────┐
│ Analytics & OCR layer                          │
│ analytics.py · insights.py · local Tesseract   │
└───────────────────────┬───────────────────────┘
                        │ normalized, user-scoped data
                        ▼
┌───────────────────────────────────────────────┐
│ Database access layer · database.py            │
└───────────────────────┬───────────────────────┘
                        │
             ┌──────────┴───────────┐
             ▼                      ▼
┌────────────────────┐  ┌────────────────────────┐
│ SQLite             │  │ Neon PostgreSQL        │
│ local development  │  │ hosted deployment      │
└────────────────────┘  └────────────────────────┘
```

Receipt parsing runs locally in the application; there is no external OCR
service. Analytics and database reads are scoped to the current user.

## Local setup

### 1. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

The repository's [`packages.txt`](./packages.txt) lists the Linux packages
`tesseract-ocr` and `libtesseract-dev`; supported hosted environments such as
Streamlit Community Cloud install these OS packages from that file.

For a Debian/Ubuntu local environment:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
```

On Windows, install a Tesseract OCR distribution separately and ensure
`tesseract.exe` is on `PATH`. Selectable-text PDFs can be parsed without
Tesseract; image receipts and scanned PDFs need the OCR engine.

### 4. Configure secrets

The app reads `DATABASE_URL` and `INVITE_CODE` from environment variables or
Streamlit secrets. If `DATABASE_URL` is unset, it uses the local SQLite file
`spendsense.db`. If `INVITE_CODE` is unset, registration is open to people who
can access the app.

**Environment / `.env` reference**

```dotenv
# Optional. Omit to use local SQLite.
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require

# Optional. When set, registration requires this invite code.
INVITE_CODE=replace-with-a-long-random-invite-code

# Reserved example: the current authentication flow does not use this value.
SESSION_SECRET=replace-with-a-long-random-secret
```

The app does not automatically load `.env` files; add values to your shell or
deployment environment. Example PowerShell configuration:

```powershell
$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
$env:INVITE_CODE = "your-long-random-invite-code"
```

**Streamlit secrets**

Alternatively, create `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
INVITE_CODE = "your-long-random-invite-code"

# Reserved example: currently not used by authentication.
SESSION_SECRET = "replace-with-a-long-random-secret"
```

For Streamlit Community Cloud, configure these values in the app's Secrets
settings instead of committing `secrets.toml`. Keep real credentials out of
source control. PostgreSQL connections require TLS.

### 5. Run SpendSense AI

```bash
streamlit run app.py
```

On Windows, you can also run [`run.bat`](./run.bat), which activates the
project virtual environment when present and starts Streamlit. Open the local
URL printed in the terminal, usually <http://localhost:8501>.

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
packages.txt        Linux OS packages, including Tesseract OCR
requirements.txt    Python dependencies
```

## Disclaimer

Insights, tax trackers, and investment projections are estimates based on
recorded data and stated assumptions. They are for informational purposes
only and are not professional financial, tax, investment, or legal advice.
