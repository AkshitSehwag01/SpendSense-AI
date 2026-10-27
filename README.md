# 💸 SpendSense AI — Intelligent Personal Finance & Wealth Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20ready-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-local%20database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Plotly](https://img.shields.io/badge/Plotly-analytics-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-data%20analysis-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-4B8BBE)](https://github.com/tesseract-ocr/tesseract)

SpendSense AI is a multi-tenant financial analytics platform built with
Streamlit, Python 3.10+, Plotly, and SQLite or PostgreSQL. It brings everyday
money management, personalized insights, and wealth planning into one
interactive experience.

Designed for Indian personal finance, SpendSense uses Indian Rupee (`₹`)
formatting with lakh/crore grouping, India Standard Time (IST) dates, and the
April–March Indian Financial Year for 80C/80D tracking. Explore transaction
patterns through natural-language search, model savings scenarios with
compound-growth projections, or use Guest Demo Mode to preview the app.

## Platform features

- **💬 Ask SpendSense — natural-language query engine:** Ask plain-English
  questions about category totals, monthly spending, top categories,
  transaction counts, averages, and month comparisons.
- **🧾 Smart receipt & invoice OCR parser:** Upload JPG, PNG, or PDF receipts
  to suggest the date, merchant description, and amount in the Add Transaction
  form. Image and scanned-PDF OCR runs locally using Tesseract; review the
  extracted fields before saving.
- **🔔 Subscription & ghost bill detector:** Detect repeated expense patterns
  with similar descriptions and amounts and payment dates typically
  25–35 days apart, helping identify subscriptions and forgotten auto-debits.
- **💎 Glassmorphic login experience:** Frosted glass cards, emerald and cyan
  ambient gradients, glowing input focus states, and subtle hover animations.
- **🚀 Guest Demo Mode & interactive onboarding:** Explore sample transactions
  and budgets without signing up. New users can set an expected monthly income
  and choose initial category budgets through a two-step setup wizard.
- **🇮🇳 Indian tax & 80C/80D planner:** Review Investment-category expenses
  against the ₹1,50,000 80C limit and Healthcare spending as a potential 80D
  deduction for the Indian Financial Year, with progress and headroom
  indicators. These are category-based estimates, not verified deductions or
  tax advice.
- **🔮 What-If wealth & runway simulator:** Adjust a savings scenario and view
  estimated compound-growth projections over 1, 3, and 5 years using stated
  assumptions.
- **🎯 Savings goal tracker:** Set targets, track progress, estimate required
  monthly contributions, and add deposits with quick-action popovers.
- **⚙️ Account settings & data control:** Change passwords, configure
  per-user Telegram settings, download a ZIP backup of transactions and
  budgets, and delete an account after confirmation.
- **📊 Multi-month analytics & reports:** Explore dark Plotly visualizations,
  budgets, trends, and Indian Rupee totals. Reports provide four Excel-safe
  CSV exports: selected-month transactions, all transactions, monthly
  summary, and budgets. Transaction history also offers a compact mobile card
  view.
- **🔐 Authentication & tenant isolation:** Passwords are stored as salted
  scrypt hashes. User records are isolated in database queries. Optional
  persistent sign-in uses an opaque session cookie; only its hash is stored
  server-side. Registration can be gated with `INVITE_CODE`.
- **📬 Telegram report notifications:** Send a report-period digest with
  summary totals, top categories, and budget alerts to the configured Telegram
  chat after explicit confirmation. Sending is manual; scheduled weekly
  notifications and email delivery are not implemented.

## Technology stack

| Layer | Technologies |
|---|---|
| User interface | Streamlit, custom Glassmorphism CSS, Plotly Express |
| Application | Python 3.10+, Pandas, NumPy (via Pandas), analytics, natural-language rules |
| OCR | Tesseract OCR, Pytesseract, Pillow, PyMuPDF, pypdf |
| Data storage | SQLite for local use; Neon PostgreSQL for hosted deployments via psycopg 3 |
| Notifications | Telegram Bot API; Fernet-encrypted per-user bot tokens |
| Authentication | Python scrypt password hashing, user-scoped queries, persistent session cookies |

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│ Streamlit Web UI                                         │
│ app.py · views/ · components/                             │
└───────────────────────────┬──────────────────────────────┘
                            │ user actions and requests
                            ▼
┌──────────────────────────────────────────────────────────┐
│ Application Layer                                        │
│ Analytics · natural-language query engine · OCR · auth   │
│ analytics.py · insights.py · utils/ · auth.py             │
└───────────────────────────┬──────────────────────────────┘
                            │ user-scoped reads and writes
                            ▼
┌──────────────────────────────────────────────────────────┐
│ User-Isolated Database Layer                             │
│ database.py · schema initialization · query helpers      │
└───────────────────────────┬──────────────────────────────┘
                            │
                 ┌──────────┴───────────┐
                 ▼                      ▼
          ┌─────────────┐       ┌─────────────────┐
          │ SQLite      │       │ Neon PostgreSQL │
          │ local       │       │ production      │
          └─────────────┘       └─────────────────┘

Optional: Reports ── confirmed manual digest ──> Telegram Bot API
OCR: uploaded images/scans ── local processing ──> Tesseract
```

Receipt parsing is performed in the application and does not send documents to
an external OCR service. PostgreSQL connections require TLS. Guest Demo Mode
uses synthetic data and does not write demo changes to the database.

## Quickstart

### Prerequisites

- Python 3.10 or later
- Git
- Tesseract OCR for image receipts and scanned PDFs (optional for other app
  features)

### 1. Clone the repository

```bash
git clone https://github.com/AkshitSehwag01/SpendSense-AI.git
cd SpendSense-AI
```

### 2. Create and activate a virtual environment

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

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set up Tesseract OCR (optional)

The repository's [`packages.txt`](./packages.txt) declares `tesseract-ocr` and
`libtesseract-dev` for supported hosted environments such as Streamlit
Community Cloud.

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev
```

On Windows, install a Tesseract OCR distribution separately and ensure
`tesseract.exe` is on `PATH`. Selectable-text PDFs can be parsed without
Tesseract; image receipts and scanned PDFs require the OCR engine.

### 5. Configure secrets

When `DATABASE_URL` is unset, the app uses local SQLite (`spendsense.db`).
Set `DATABASE_URL` to use PostgreSQL. If `INVITE_CODE` is unset, registration
is open to users who can access the app. The app does not load `.env` files
automatically; configure environment variables in your shell/deployment or
use Streamlit secrets.

Create `.streamlit/secrets.toml` for hosted settings:

```toml
# Optional. Omit to use local SQLite.
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"

# Optional. When configured, registration requires this invite code.
INVITE_CODE = "replace-with-a-long-random-invite-code"

# Reserved for future use; the current authentication flow does not use it.
SESSION_SECRET = "replace-with-a-long-random-secret"

# Optional. Enables the manually confirmed Reports Telegram summary.
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = "your-telegram-chat-id"

# Required only to persist per-user Telegram bot tokens in Settings.
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
NOTIFICATIONS_ENCRYPTION_KEY = "replace-with-a-generated-fernet-key"
```

Keep actual credentials private and never commit `.streamlit/secrets.toml`.
Keep `NOTIFICATIONS_ENCRYPTION_KEY` stable: rotating or losing it prevents
decryption of saved per-user Telegram tokens. `SESSION_SECRET` is currently
unused; persistent sessions use cryptographically random tokens, with hashes
stored in the database.

### 6. Launch the app

```bash
streamlit run app.py
```

On Windows, [`run.bat`](./run.bat) activates the project virtual environment
when present and launches Streamlit. Open the local URL printed in the
terminal, usually <http://localhost:8501>.

## Repository layout

```text
app.py              Streamlit entry point, initialization, and routing
auth.py             Authentication and persistent session handling
database.py         SQLite/PostgreSQL access and schema migrations
analytics.py        Transaction preparation and financial calculations
insights.py         Financial insight generation
components/         Reusable charts, cards, and UI components
views/              Dashboard, reports, onboarding, settings, and finance pages
utils/              Demo data, formatting, dates, styles, and notifications
packages.txt        Linux OS packages, including Tesseract OCR
requirements.txt    Python dependencies
```

## Disclaimer

Financial insights, tax trackers, and investment projections are estimates
based on recorded data and stated assumptions. They are for informational
purposes only and are not professional financial, tax, investment, or legal
advice.
