# SpendSense AI

<p align="center">
  <strong>India-centric wealth intelligence and tax planning for everyday money.</strong><br>
  <sub>Track spending, forecast runway, prepare tax summaries, and make better financial decisions from one production-minded Streamlit workspace.</sub>
</p>

<p align="center">
  <a href="https://github.com/AkshitSehwag01/SpendSense-AI"><img src="https://img.shields.io/badge/status-production--ready-10B981?style=for-the-badge" alt="Production-ready status"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14"></a>
  <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL and Neon"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Plotly-analytics-3F4F75?logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/Pandas-data%20engine-150458?logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/Tesseract-local%20OCR-4B8BBE" alt="Tesseract OCR">
  <img src="https://img.shields.io/badge/SQLite-local%20fallback-003B57?logo=sqlite&logoColor=white" alt="SQLite">
</p>

## Overview

SpendSense AI is a multi-tenant personal finance and tax-planning SaaS
platform built for Indian financial workflows. It combines transaction
analytics, predictive cash-flow intelligence, tax deduction mapping, receipt
OCR, natural-language exploration, and proactive bill reminders in a single
Streamlit application.

The platform is designed around the Indian context:

- INR-first accounting with Lakh/Crore formatting and multi-currency display.
- April 1–March 31 Indian Financial Year reporting.
- Tax planning estimates for Sections 80C, 80D, 80TTA/80TTB, and
  10(13A) HRA.
- India Standard Time for date-sensitive insights and bill reminders.
- Neon PostgreSQL for hosted deployments, with concurrent-safe SQLite for
  local development.

The UI includes a dual-theme design system: **Glassmorphic Cosmic Dark** for
an ambient, data-dense workspace and **Enterprise Clean Light** for a crisp
professional experience.

> **Financial and tax disclaimer:** SpendSense AI produces estimates from
> recorded transactions and user-provided assumptions. It is not tax, legal,
> investment, or financial advice, and its exports are not a substitute for
> verification by a qualified professional.

## V3 feature suite

| Capability | What it delivers |
|---|---|
| 🔮 **Predictive cash-flow and runway forecasting** | 30/60/90-day projected balances, 60-day daily burn analysis, recurring bill impact, and an estimated balance run-out date with low-runway alerts. |
| 🚨 **Spending anomaly and fraud outlier detection** | Category baselines across prior months, Z-score analysis, and multiplier checks that flag unusual current-month spending, including deviations above 2.5× a category average. |
| 📄 **Automated ITR tax summary and exporter** | Indian Financial Year mapping for 80C investments such as PPF, ELSS, EPF, LIC premiums and tuition fees; 80D health insurance; 80TTA/80TTB interest; and Section 10(13A) HRA/rent records. Export summaries for CA review. |
| 💳 **Utility bill tracker and Telegram reminders** | Recurring cycle detection for Electricity, Broadband, Water, FASTag, Rent, and Credit Card payments, with reminders for bills due within three days. |
| 🌐 **Multi-currency conversion engine** | INR, USD, EUR, and AED display conversion with INR Lakh/Crore grouping and standard international separators for other currencies. Rates are centrally configured and cached. |
| 🎨 **Dual-theme customizer** | Instant switching between Glassmorphic Cosmic Dark and Enterprise Clean Light across views, cards, forms, sidebars, and charts. |
| 🧾 **OCR receipt parser** | Local Tesseract extraction for image receipts and scanned PDFs, with date, merchant, amount, and category suggestions for review before saving. |
| 💬 **Ask SpendSense natural-language analytics** | Plain-language queries for category totals, monthly comparisons, top categories, averages, and transaction counts. |
| 📊 **Budgets, goals, reports, and insights** | Budget utilization, savings goals, compound-growth scenarios, multi-month trends, downloadable reports, onboarding, and a read-only demo mode. |

## Product architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ Streamlit application                                       │
│ app.py · views/ · components/                              │
│ Dashboard · Reports · Tax Planner · Settings · Onboarding   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Intelligence and workflow layer                             │
│ analytics.py · insights.py · utils/                         │
│ Forecasting · anomalies · tax mapping · OCR · notifications │
└──────────────────────────────┬──────────────────────────────┘
                               │ user-scoped, parameterized access
┌──────────────────────────────▼──────────────────────────────┐
│ Database abstraction                                         │
│ database.py · schema initialization · migrations · caching   │
└───────────────────────┬──────────────────────┬──────────────┘
                        │                      │
                 ┌──────▼─────┐        ┌───────▼────────┐
                 │ SQLite     │        │ Neon PostgreSQL│
                 │ local mode │        │ hosted mode    │
                 └────────────┘        └────────────────┘

Optional integrations:
  Receipt images/PDFs ──local ThreadPoolExecutor──> Tesseract OCR
  Confirmed reminders ────────────────────────────> Telegram Bot API
```

## Technology and production engineering

| Layer | Implementation |
|---|---|
| Runtime and UI | Python 3.14, Streamlit, custom CSS design system |
| Analytics | Pandas, Plotly, cached aggregation functions, deterministic finance rules |
| Persistence | PostgreSQL on Neon via `psycopg3`/`psycopg_pool`; SQLite fallback for local use |
| OCR | Tesseract, Pytesseract, Pillow, PyMuPDF, pypdf |
| Connectivity | Pooled PostgreSQL connections with bounded sizes, idle cleanup, and fast connection timeouts |
| Notifications | Telegram Bot API with Fernet-encrypted per-user bot credentials |
| TLS | `certifi` CA root provisioning for PostgreSQL certificate validation |
| Performance | `@st.cache_resource` for shared connection pools, `@st.cache_data` for expensive calculations, and non-blocking OCR workers |

### Security and tenant isolation

- Every authenticated request is scoped through the signed-in `user_id`
  context; transaction, budget, goal, session, and preference queries are
  user-scoped.
- SQL uses bound parameters for SQLite and PostgreSQL rather than string
  interpolation.
- Passwords use salted scrypt hashing with bounded verification settings.
- Sign-out clears session state, including user-scoped context.
- Persistent sign-in stores an opaque session-token hash rather than the
  token itself.
- Telegram bot tokens stored in user preferences are encrypted with Fernet.
- PostgreSQL deployments use TLS and provision a `certifi` root certificate
  at `~/.postgresql/root.crt` when needed.
- Database errors are logged server-side with tracebacks while frontend
  messages remain safe and actionable.

### Performance model

- PostgreSQL pools are shared with `st.cache_resource` to avoid opening new
  connection handles for every rerun.
- Forecasting, anomaly detection, summaries, category totals, and tax-related
  calculations use short-lived `st.cache_data` results with user and period
  inputs included in cache keys.
- OCR parsing runs in a `ThreadPoolExecutor` and presents a processing spinner
  while the worker resolves.
- SQLite uses WAL mode and scoped connections to support concurrent reads in
  local development.

## Getting started

### Prerequisites

- Python 3.14
- Git
- Tesseract OCR for image receipts and scanned PDFs
- PostgreSQL/Neon credentials for hosted mode; no database service is needed
  for local SQLite mode

### Local development

```bash
git clone https://github.com/AkshitSehwag01/SpendSense-AI.git
cd SpendSense-AI

# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
# python3 -m venv .venv
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

When `DATABASE_URL` is not configured, the application creates and uses the
local `spendsense.db` SQLite database. Open the URL printed by Streamlit,
normally <http://localhost:8501>.

### Tesseract setup

Tesseract is optional for the rest of the application:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
```

On Windows, install a Tesseract distribution and ensure `tesseract.exe` is
available on `PATH`. Selectable-text PDFs can be parsed without Tesseract;
images and scanned PDFs require it.

## Streamlit Cloud and Neon deployment

1. Create a Neon PostgreSQL database and copy its pooled connection string.
2. Deploy this repository as a Streamlit Community Cloud app with
   `app.py` as the entry point.
3. Add the following values in **App settings → Secrets**:

```toml
# Neon pooled PostgreSQL connection string.
# The application normalizes PostgreSQL SSL parameters and requires TLS.
DATABASE_URL = "postgresql://USER:PASSWORD@POOLER_HOST/DATABASE?sslmode=require"

# Optional: require this code before account registration.
INVITE_CODE = "generate-a-long-random-value"

# Required only when users save personal Telegram credentials in Settings.
# Generate locally:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
NOTIFICATIONS_ENCRYPTION_KEY = "generate-a-fernet-key"

# Optional legacy/manual digest integration.
TELEGRAM_BOT_TOKEN = "telegram-bot-token"
TELEGRAM_CHAT_ID = "telegram-chat-id"
```

4. Redeploy or restart the app. Database tables and compatible schema columns
   are initialized automatically.
5. Confirm that registration, sign-in, a transaction read, and a receipt OCR
   upload work before inviting users.

The PostgreSQL layer uses `psycopg_pool` with bounded pool sizes, a
`connect_timeout`, and idle cleanup. TLS certificate support is provisioned
with `certifi`; do not disable certificate verification in production or
commit secrets to the repository.

### Operational notes

- Keep `NOTIFICATIONS_ENCRYPTION_KEY` stable. Changing or losing it makes
  previously saved per-user Telegram tokens undecryptable.
- Use a Neon pooled endpoint for hosted deployments.
- `DATABASE_URL` unset means local SQLite; `DATABASE_URL` set means
  PostgreSQL.
- Telegram bill reminders are triggered when the dashboard is visited; this
  repository does not run a separate server-side scheduler.
- Demo Mode uses synthetic data and does not write changes to the database.

## Repository layout

```text
app.py                  Streamlit entry point and page routing
auth.py                 Authentication, sessions, and user context
database.py             SQLite/PostgreSQL abstraction, pooling, and migrations
analytics.py            Forecasts, anomaly detection, tax and transaction analytics
insights.py             Natural-language and financial insight generation
components/             Shared cards, charts, tables, and budget widgets
views/                  Dashboard, reports, tax planner, settings, and workflows
utils/                  Formatting, themes, OCR, dates, demo data, notifications
requirements.txt        Python dependencies
packages.txt            Linux packages for hosted Tesseract support
```

## License and disclaimer

See the repository license for usage terms. SpendSense AI is an engineering
project and an informational decision-support tool. Always verify deductions,
income, investments, tax eligibility, exchange rates, and filing data with
authoritative records and a qualified professional before acting.
