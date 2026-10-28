import logging

import pandas as pd
import streamlit as st

from analytics import (
    calculate_budget_status,
    calculate_summary,
    filter_transactions_by_month_range,
    get_month_data,
    load_demo_transactions,
    prepare_transactions,
)
from auth import (
    apply_cookie_actions,
    current_user_id,
    get_user_context,
    get_secret,
    is_authenticated,
    login_required,
    restore_session,
)
from components.insight_cards import show_insights
from components.sidebar import render_sidebar
from database import (
    database_backend,
    get_budgets,
    get_goals,
    get_transactions,
    get_transactions_for_month,
    get_transactions_for_month_range,
    get_transaction_months,
    get_user_preferences,
    initialize_database,
)
from insights import generate_insights
from utils.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils.demo_data import (
    get_demo_budget_records,
    get_demo_budgets,
    get_demo_transaction_months,
)
from utils.dates import today_local
from utils.formatting import (
    SUPPORTED_CURRENCIES,
    money,
)
from utils.styles import apply_styles

from functools import partial

from views.add_transaction import render_add_transaction
from views.budget_planner import render_budget_planner
from views.dashboard import render_dashboard
from views.financial_insights import render_financial_insights
from views.goals import render_goals
from views.login import render_account_box, render_login
from views.onboarding import show_onboarding_dialog
from views.reports import render_reports
from views.settings import render_settings
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

_INSECURE_SECRET_VALUES = {
    "changeme",
    "change-me",
    "default",
    "password",
    "secret",
    "your-secret",
    "your-secret-here",
    "replace-me",
    "replace-this",
}


def _secret_is_weak(value):
    normalized = value.strip().casefold()
    return (
        len(value.strip()) < 16
        or normalized in _INSECURE_SECRET_VALUES
        or any(
            marker in normalized
            for marker in ("change-me", "changeme", "your-secret", "replace-me")
        )
    )


def _warn_production_secret_configuration():
    if database_backend() != "postgres":
        return

    if not login_required():
        logger.warning(
            "Login is disabled while using PostgreSQL; hosted account "
            "authentication is not protecting database access."
        )

    invite_code = get_secret("INVITE_CODE")
    if not invite_code:
        logger.warning(
            "INVITE_CODE is not configured; public account registration "
            "is enabled."
        )
    elif _secret_is_weak(invite_code):
        logger.warning(
            "INVITE_CODE appears weak or uses a placeholder. Configure a "
            "strong, unique value in the deployment secrets."
        )

    session_secret = get_secret("SESSION_SECRET")
    if session_secret and _secret_is_weak(session_secret):
        logger.warning(
            "SESSION_SECRET appears weak or uses a placeholder. The current "
            "authentication flow generates session tokens cryptographically "
            "and does not use SESSION_SECRET."
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


_warn_production_secret_configuration()


# =========================================================
# DESIGN SYSTEM
# =========================================================

st.session_state.setdefault("app_theme", "dark")
if st.session_state["app_theme"] not in ("dark", "light"):
    st.session_state["app_theme"] = "dark"
apply_styles(st.session_state["app_theme"])


# =========================================================
# SIGN-IN GATE
# Nothing below this point runs until a user is signed in.
# =========================================================

restore_session()

user_context = get_user_context()
is_demo = bool(user_context.get("is_demo"))

if login_required() and not is_authenticated():
    render_login()
    apply_cookie_actions()
    st.stop()

if is_demo:
    st.info(
        "🚀 Demo Mode Active — exploring sample data. Changes are not saved.",
        icon="🚀",
    )

# =========================================================
# HELPER FUNCTIONS
# (money() converts stored INR amounts to the user's selected display
#  currency while preserving the appropriate grouping format.)
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

if is_demo:
    transaction_months = get_demo_transaction_months()
else:
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
user_id = current_user_id()
user_context = get_user_context()

if is_demo:
    user_context["currency_symbol"] = SUPPORTED_CURRENCIES["INR"]["symbol"]
else:
    if user_context.get("_currency_user_id") != user_id:
        try:
            preferences = get_user_preferences(user_id=user_id)
        except Exception:
            logger.exception(
                "Could not load display currency preference for user %s",
                user_id,
            )
            st.warning(
                "Your saved display currency could not be loaded. "
                "Using Indian rupees for this session."
            )
            user_context["currency_symbol"] = (
                SUPPORTED_CURRENCIES["INR"]["symbol"]
            )
        else:
            currency_symbol = preferences.get("currency_symbol", "₹")
            if currency_symbol not in (
                details["symbol"]
                for details in SUPPORTED_CURRENCIES.values()
            ):
                currency_symbol = SUPPORTED_CURRENCIES["INR"]["symbol"]
            user_context["currency_symbol"] = currency_symbol
        st.session_state.pop("currency_selector", None)
        user_context["_currency_user_id"] = user_id

st.session_state["currency_symbol"] = user_context.get(
    "currency_symbol",
    SUPPORTED_CURRENCIES["INR"]["symbol"],
)

if not is_demo:
    onboarding_user_id = user_id
    if user_context.get("onboarding_user_id") != onboarding_user_id:
        user_context["onboarding_user_id"] = onboarding_user_id
        user_context["has_completed_onboarding"] = False
        user_context["onboarding_step"] = 1
        for key in (
            "onboarding_income_input",
            "onboarding_categories",
        ):
            st.session_state.pop(key, None)
        for category in EXPENSE_CATEGORIES:
            st.session_state.pop(f"onboarding_budget_{category}", None)

    if not user_context.get("has_completed_onboarding", False):
        show_onboarding_dialog(selected_month)


# =========================================================
# LOAD DATA REQUIRED BY THE ACTIVE PAGE
# =========================================================

df = prepare_transactions([])
month_df = df
financial_year_df = df
summary = calculate_summary(
    month_df,
    user_id=user_id,
    selected_month=selected_month,
)
budgets = {}
total_budget = 0.0
goals = []
generate_month_insights = partial(generate_insights, budgets=budgets)

try:
    demo_all_transactions = (
        load_demo_transactions() if is_demo else None
    )

    if is_demo:
        if page in ("Transactions", "Reports"):
            df = demo_all_transactions
            month_df = get_month_data(df, selected_month)
        elif page == "Dashboard":
            start_month = str(pd.Period(selected_month, "M") - 5)
            df = filter_transactions_by_month_range(
                demo_all_transactions,
                start_month,
                selected_month,
            )
            month_df = get_month_data(df, selected_month)
        elif page == "Budget Planner":
            df = demo_all_transactions
            month_df = get_month_data(df, selected_month)
        elif page == "Financial Insights":
            financial_year_start_year = (
                today.year if today.month >= 4 else today.year - 1
            )
            financial_year_start_month = f"{financial_year_start_year}-04"
            financial_year_end_month = f"{financial_year_start_year + 1}-03"
            financial_year_df = filter_transactions_by_month_range(
                demo_all_transactions,
                financial_year_start_month,
                financial_year_end_month,
            )
            selected_month_is_in_fy = (
                financial_year_start_month
                <= selected_month
                <= financial_year_end_month
            )
            if selected_month_is_in_fy:
                month_df = get_month_data(financial_year_df, selected_month)
            else:
                month_df = get_month_data(
                    demo_all_transactions,
                    selected_month,
                )
            df = financial_year_df
        elif page == "Goals":
            goals = []

        summary = calculate_summary(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )

        if page in ("Dashboard", "Financial Insights"):
            budgets = get_demo_budgets()
            total_budget = sum(float(value) for value in budgets.values())
            generate_month_insights = partial(
                generate_insights,
                budgets=budgets,
            )
    elif page in ("Transactions", "Reports"):
        df = prepare_transactions(get_transactions())
        month_df = get_month_data(df, selected_month)
        summary = calculate_summary(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )
    elif page == "Dashboard":
        start_month = str(pd.Period(selected_month, "M") - 5)
        df = prepare_transactions(
            get_transactions_for_month_range(start_month, selected_month)
        )
        month_df = get_month_data(df, selected_month)
        summary = calculate_summary(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )
    elif page == "Budget Planner":
        month_df = prepare_transactions(
            get_transactions_for_month(selected_month)
        )
        summary = calculate_summary(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )
    elif page == "Financial Insights":
        financial_year_start_year = (
            today.year if today.month >= 4 else today.year - 1
        )
        financial_year_start_month = f"{financial_year_start_year}-04"
        financial_year_end_month = f"{financial_year_start_year + 1}-03"
        financial_year_df = prepare_transactions(
            get_transactions_for_month_range(
                financial_year_start_month,
                financial_year_end_month,
            )
        )
        selected_month_is_in_fy = (
            financial_year_start_month
            <= selected_month
            <= financial_year_end_month
        )
        if selected_month_is_in_fy:
            month_df = get_month_data(financial_year_df, selected_month)
        else:
            month_df = prepare_transactions(
                get_transactions_for_month(selected_month)
            )
        summary = calculate_summary(
            month_df,
            user_id=user_id,
            selected_month=selected_month,
        )
    elif page == "Goals":
        goals = get_goals()

    if not is_demo and page in ("Dashboard", "Financial Insights"):
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

def _render_demo_page(page, budgets=None):
    st.title(page)
    st.info(
        "This page changes or manages account data and is unavailable in "
        "the read-only demo. Create an account to use this feature."
    )
    if page == "Budget Planner" and budgets:
        st.subheader(f"Sample budgets · {selected_month}")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Category": category, "Monthly budget (₹)": amount}
                    for category, amount in budgets.items()
                ]
            ),
            hide_index=True,
        )


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
        user_id=user_id,
    ),
    "Add Transaction": lambda: (
        _render_demo_page(page)
        if is_demo
        else render_add_transaction(
            expense_categories=EXPENSE_CATEGORIES,
            income_categories=INCOME_CATEGORIES,
            today=today,
        )
    ),
    "Transactions": lambda: render_transactions(df, read_only=is_demo),
    "Budget Planner": lambda: (
        _render_demo_page(page, get_demo_budgets())
        if is_demo
        else render_budget_planner(
            selected_month=selected_month,
            expense_categories=EXPENSE_CATEGORIES,
            month_df=month_df,
            calculate_budget_status=calculate_budget_status,
            money=money,
            user_id=user_id,
        )
    ),
    "Goals": lambda: (
        _render_demo_page(page)
        if is_demo
        else render_goals(
            goals=goals,
            money=money,
            today=today,
        )
    ),
    "Financial Insights": lambda: render_financial_insights(
        selected_month=selected_month,
        month_df=month_df,
        generate_insights=generate_month_insights,
        show_insights=show_insights,
        calculate_budget_status=calculate_budget_status,
        money=money,
        financial_year_df=financial_year_df,
        today=today,
        budgets=budgets if is_demo else None,
        user_id=user_id,
    ),
    "Reports": lambda: render_reports(
        selected_month=selected_month,
        summary=summary,
        month_df=month_df,
        df=df,
        money=money,
        all_budgets=(
            get_demo_budget_records(selected_month) if is_demo else None
        ),
        is_demo=is_demo,
        user_id=user_id,
    ),
    "Settings": lambda: (
        _render_demo_page(page)
        if is_demo
        else render_settings(user_id=user_id)
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