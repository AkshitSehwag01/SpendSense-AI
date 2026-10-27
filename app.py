import logging

import pandas as pd
import streamlit as st

from analytics import (
    calculate_budget_status,
    calculate_summary,
    get_month_data,
    prepare_transactions,
)
from auth import (
    apply_cookie_actions,
    is_authenticated,
    login_required,
    restore_session,
)
from components.insight_cards import show_insights
from components.sidebar import render_sidebar
from database import (
    get_budgets,
    get_transactions,
    get_transactions_for_month,
    get_transactions_for_month_range,
    get_transaction_months,
    initialize_database,
)
from insights import generate_insights
from utils.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils.dates import today_local
from utils.formatting import money
from utils.styles import apply_styles

from functools import partial

from views.add_transaction import render_add_transaction
from views.budget_planner import render_budget_planner
from views.dashboard import render_dashboard
from views.financial_insights import render_financial_insights
from views.login import render_account_box, render_login
from views.reports import render_reports
from views.transactions import render_transactions


logger = logging.getLogger(__name__)


# =========================================================
# PAGE CONFIGURATION (must be the first Streamlit call)
# =========================================================

st.set_page_config(
    page_title="SpendSense AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE INITIALIZATION
# Runs once per browser session (not once per server), so tables
# added by a new version are created even when the server process
# was not restarted after a deploy. Every statement is
# CREATE ... IF NOT EXISTS, so repeating it is safe.
# =========================================================

if not st.session_state.get("_db_ready"):
    try:
        initialize_database()
    except Exception:
        logger.exception("Database setup failed")
        st.error(
            "SpendSense AI could not connect to its database. "
            "Please try again in a moment."
        )
        st.stop()

    st.session_state["_db_ready"] = True


# =========================================================
# DESIGN SYSTEM
# =========================================================

apply_styles()


# =========================================================
# SIGN-IN GATE
# Nothing below this point runs until a user is signed in.
# =========================================================

restore_session()

if login_required() and not is_authenticated():
    render_login()
    apply_cookie_actions()
    st.stop()


# =========================================================
# HELPER FUNCTIONS
# (money() comes from utils/formatting.py, so every page shows
#  the same Indian number format, e.g. ₹12,34,567.00)
# =========================================================

def build_available_months(transaction_months, today, recent_count=12):
    """Last `recent_count` months plus any month with transactions."""

    current = pd.Timestamp(today).to_period("M")

    months = {str(current - i) for i in range(recent_count)}
    months.update(transaction_months)

    return sorted(months, reverse=True)


# =========================================================
# LOAD AVAILABLE MONTHS
# =========================================================

try:
    transaction_months = get_transaction_months()
except Exception:
    logger.exception("Could not load transaction months")
    st.error(
        "SpendSense AI could not load your transaction history. "
        "Please refresh the page. If the problem continues, "
        "try again in a few minutes."
    )
    st.stop()

# Indian date, not the server's (UTC) date.
today = today_local()


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

page, selected_month = render_sidebar(
    build_available_months(transaction_months, today)
)


# =========================================================
# LOAD DATA REQUIRED BY THE ACTIVE PAGE
# =========================================================

df = prepare_transactions([])
month_df = df
summary = calculate_summary(month_df)
budgets = {}
total_budget = 0.0
generate_month_insights = partial(generate_insights, budgets=budgets)

try:
    if page in ("Transactions", "Reports"):
        df = prepare_transactions(get_transactions())
        month_df = get_month_data(df, selected_month)
        summary = calculate_summary(month_df)
    elif page == "Dashboard":
        start_month = str(pd.Period(selected_month, "M") - 5)
        df = prepare_transactions(
            get_transactions_for_month_range(start_month, selected_month)
        )
        month_df = get_month_data(df, selected_month)
        summary = calculate_summary(month_df)
    elif page in ("Budget Planner", "Financial Insights"):
        month_df = prepare_transactions(
            get_transactions_for_month(selected_month)
        )
        summary = calculate_summary(month_df)

    if page in ("Dashboard", "Financial Insights"):
        budgets = get_budgets(selected_month)
        total_budget = sum(float(value) for value in budgets.values())
        generate_month_insights = partial(
            generate_insights,
            budgets=budgets,
        )
except Exception:
    logger.exception("Could not load data for page %s", page)
    st.error(
        "SpendSense AI could not load the data for this page. "
        "Please refresh the page. If the problem continues, "
        "try again in a few minutes."
    )
    st.stop()


# =========================================================
# PAGE ROUTING
# =========================================================

routes = {
    "Dashboard": lambda: render_dashboard(
        selected_month=selected_month,
        summary=summary,
        df=df,
        month_df=month_df,
        budgets=budgets,
        total_budget=total_budget,
        money=money,
        calculate_budget_status=calculate_budget_status,
        generate_insights=generate_month_insights,
        show_insights=show_insights,
    ),
    "Add Transaction": lambda: render_add_transaction(
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        today=today,
    ),
    "Transactions": lambda: render_transactions(df),
    "Budget Planner": lambda: render_budget_planner(
        selected_month=selected_month,
        expense_categories=EXPENSE_CATEGORIES,
        month_df=month_df,
        calculate_budget_status=calculate_budget_status,
        money=money,
    ),
    "Financial Insights": lambda: render_financial_insights(
        selected_month=selected_month,
        month_df=month_df,
        generate_insights=generate_month_insights,
        show_insights=show_insights,
        calculate_budget_status=calculate_budget_status,
        money=money,
    ),
    "Reports": lambda: render_reports(
        selected_month=selected_month,
        summary=summary,
        month_df=month_df,
        df=df,
        money=money,
    ),
}

render_page = routes.get(page)

if render_page:
    render_page()
else:
    st.error(f"Unknown page: {page}")


# =========================================================
# GLOBAL SIDEBAR FOOTER
# =========================================================

skipped_rows = df.attrs.get("invalid_rows", 0)

if skipped_rows:
    st.sidebar.warning(
        f"{skipped_rows} saved record(s) have invalid data and "
        "were left out of the calculations."
    )

st.sidebar.caption(
    "Insights are estimates based on recorded data, "
    "not professional financial advice."
)

render_account_box()
apply_cookie_actions()