import streamlit as st


# =========================================================
# EDIT THESE LINES BEFORE YOU SHARE THE APP
# =========================================================

OPERATOR_NAME = "Akshit Sehwag"            # your name or business name
CONTACT_EMAIL = "akkiisehwag2@gmail.com"   # a real address you read
LAST_UPDATED = "27 October 2026"


PRIVACY_POLICY = f"""
*Last updated: {LAST_UPDATED}*

SpendSense AI ("the app", "we") is a personal finance tool operated by
**{OPERATOR_NAME}**. This policy explains what we collect, why, and the
choices you have. You can reach us at **{CONTACT_EMAIL}**.

#### What we collect

- **Account details:** your email address and, if you give one, your name.
  Your password is never stored. We keep only a one-way scrambled version
  (a salted hash) that cannot be turned back into your password.
- **Financial records you enter:** transactions (amount, category,
  description, date) and monthly budgets.
- **Sign-in information:** the time you accepted these documents, failed
  sign-in counts (to protect your account), and, if you select "Keep me
  signed in", an authentication cookie named `spendsense_session` in your
  browser. The cookie can persist for up to 30 days.
- **Typography request:** the app requests the Inter font from Google Fonts
  (`fonts.googleapis.com`) for display. Your browser connects to Google to
  retrieve the font, and Google may receive connection information such as
  your IP address and browser details.

We do not collect your bank account numbers, card numbers or bank logins.
Please do not type them into descriptions.

#### How we use it

Only to run the app for you: to show your dashboard, budgets, insights and
reports, and to keep your account secure. We do not currently provide
automated password-reset emails. For account recovery, contact the
SpendSense administrator at **{CONTACT_EMAIL}**. We do not sell your data,
show ads, or share your information for marketing.

#### Where it is stored

In hosted mode, records are stored in the configured PostgreSQL database
(for example, Neon). The database provider and its configured region
determine where hosted data is stored and processed. In local mode, records
are stored in a SQLite file on the computer running the app.

#### How long we keep it

For as long as your account exists. When you delete your account, your
transactions, budgets and account details are deleted from the live
database. Copies may remain in provider-managed backups until those backups
expire under the provider's retention settings. For Neon-hosted databases,
backup and point-in-time recovery availability depends on the active plan
and project configuration. We do not promise a fixed backup-retention
period or 90-day point-in-time recovery. In local mode, the database file
and any copies of it are managed on the computer where the app runs.

#### Your choices

- **See and export your data:** download full CSV exports of your
  transactions and budgets from the Reports page at any time.
- **Delete your data:** use **Delete my account** in the sidebar. This is
  permanent.
- **Correction, questions or complaints:** email **{CONTACT_EMAIL}**. We aim
  to reply within 7 days.

We aim to handle personal data in line with applicable Indian data
protection law, including the Digital Personal Data Protection Act, 2023.
By creating an account you consent to the use of your data as described
here. You can withdraw that consent at any time by deleting your account.

#### Security

Connections to the app are encrypted, passwords are stored as salted
hashes, and each account can only see its own records. If you choose
"Keep me signed in", the `spendsense_session` cookie is used to restore
your sign-in on this browser for up to 30 days. No online service can
promise perfect security, so please use a strong password that you do not
use anywhere else.

#### Children

The app is not meant for people under 18.

#### Changes

If we change this policy we will update the date above. If the change is
significant we will tell you in the app.
"""


TERMS_OF_SERVICE = f"""
*Last updated: {LAST_UPDATED}*

By creating an account or using SpendSense AI ("the app"), you agree to
these terms. The app is operated by **{OPERATOR_NAME}**
(**{CONTACT_EMAIL}**).

#### 1. What the app is

A tool to record income and expenses, set budgets and see summaries and
insights. It is currently a **beta**: features may change, and the app may
be unavailable from time to time.

#### 2. Not financial advice

Insights, scores and projections are automatic estimates based on what you
enter. They are not financial, tax, investment or legal advice. Please make
your own decisions, and speak to a qualified professional where needed.

#### 3. Your account

You must be 18 or older. Give a real email address, keep your password
private, and tell us if you think someone else has access. You are
responsible for what happens under your account.

#### 4. Acceptable use

Do not try to break into the app or other people's accounts, overload it,
reverse-engineer it, or use it for anything unlawful. We may suspend
accounts that do.

#### 5. Your data

Your records belong to you. You allow us to store and process them only to
run the app for you, as described in the Privacy Policy. You can download
full CSV exports of your transactions and budgets from the Reports page
at any time. Please keep your own copies of important records.

#### 6. No guarantees

The app is provided "as is". We work to keep it accurate and available, but
we cannot promise it will be error-free, uninterrupted, or that no data will
ever be lost. To the extent the law allows, we are not liable for indirect
or consequential losses, or for decisions you make based on the app.

#### 7. Ending your use

You can stop at any time and delete your account in the sidebar. We may
suspend or close accounts that break these terms or put the app at risk.

#### 8. Changes and law

We may update these terms and will change the date above when we do.
Continuing to use the app after a change means you accept it. These terms
are governed by the laws of India.

#### 9. Contact

Questions about these terms: **{CONTACT_EMAIL}**.
"""


@st.dialog("Privacy Policy & Terms", width="large")
def _legal_dialog():
    privacy_tab, terms_tab = st.tabs(
        ["Privacy Policy", "Terms of Service"]
    )

    with privacy_tab:
        st.markdown(PRIVACY_POLICY)

    with terms_tab:
        st.markdown(TERMS_OF_SERVICE)


def render_legal_button(key, label="Privacy Policy & Terms"):
    """A small button that opens the policy and terms in a pop-up."""

    if st.button(label, key=key, use_container_width=True):
        _legal_dialog()