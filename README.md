# SpendSense AI

A personal finance app built with Streamlit. Track income and expenses,
set monthly category budgets, see insights, and export reports.
Each user signs in with their own account and sees only their own data.

## Requirements

- Python 3.10 or newer
- An internet connection the first time (for installing packages and
  loading the Inter font)

## Install

Open a terminal in the project folder and run:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(On macOS or Linux, use `source .venv/bin/activate` instead of the
second line.)

## Run

On Windows, double-click `run.bat`, or run:

```
streamlit run app.py
```

Then open the address shown in the terminal (usually
http://localhost:8501).

## Accounts and login

Login is **on by default**. Create an account on the first screen.

To skip login on your own computer (for testing), set this before
starting the app:

- PowerShell: `$env:SPENDSENSE_REQUIRE_LOGIN="0"`
- Command Prompt: `set SPENDSENSE_REQUIRE_LOGIN=0`

In that mode the app uses a single local account and shows no login page.

## Your data

SpendSense AI uses one of two databases:

- **Local (default):** a file called `spendsense.db` in the project folder.
- **Hosted:** PostgreSQL (for example Neon), used automatically when a
  `DATABASE_URL` is configured. Put it in the environment, or in
  `.streamlit/secrets.toml` as `DATABASE_URL = "postgresql://..."`.
  Never commit that file or share the address: it contains the password.

To check that the configured database works, run:

```
python check_database.py
```

In local mode, all data is stored in `spendsense.db` in the project folder.
Back it up by copying that file while the app is stopped.
Never share or publish this file: it contains financial records and
password hashes.

## Moving old data into an account

If you used SpendSense before accounts existed, your old data belongs to a
reserved local account. To move it to your account (replace `2` with your
account's ID; the first account created has ID 2):

```
python -c "from database import claim_local_data; print(claim_local_data(2))"
```

## Project layout

```
app.py              entry point, routing, sign-in gate
auth.py             password hashing, sign-up, sign-in, session
database.py         all database access (one place to change for hosting)
analytics.py        summaries, breakdowns, trends, budget status
insights.py         insight generation
components/         shared UI pieces (sidebar, cards, charts, tables)
views/              one file per page
utils/              constants and styles
.streamlit/         Streamlit settings (config.toml)
```

## Disclaimer

Insights are estimates based on recorded data and are not professional
financial advice.