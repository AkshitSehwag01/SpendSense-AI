"""
Streamlit-facing adapters for the domain services.

These keep the historical function names and signatures used by the
views, add Streamlit caching, and fetch data from the database when a
caller does not pass it in. All calculations live in ``domain``.
The ``user_id`` and ``selected_month`` arguments only scope cache keys.
"""

import pandas as pd
import streamlit as st

from database import get_transactions, get_transactions_for_month_range
from domain import budgets as _budgets
from domain import forecasting as _forecasting
from domain import goals as _goals
from domain import insights as _insights
from domain import tax as _tax
from domain import transactions as _transactions
from domain.forecasting import ROLLING_SPEND_WINDOW_DAYS
from domain.transactions import (
    TRANSACTION_COLUMNS,
    VALID_TYPES,
    filter_transactions_by_month_range,
    get_month_data,
    prepare_transactions,
)
from utils.dates import today_local


__all__ = [
    "ROLLING_SPEND_WINDOW_DAYS",
    "TRANSACTION_COLUMNS",
    "VALID_TYPES",
    "calculate_80c_headroom",
    "calculate_budget_status",
    "calculate_cash_flow_forecast",
    "calculate_goal_metrics",
    "calculate_rolling_daily_spend",
    "calculate_summary",
    "category_breakdown",
    "compare_months",
    "detect_recurring_subscriptions",
    "detect_spending_anomalies",
    "filter_transactions_by_month_range",
    "get_month_data",
    "load_demo_transactions",
    "monthly_trend",
    "parse_natural_language_query",
    "prepare_transactions",
]


def load_demo_transactions():
    """Prepare the synthetic transaction dataset for a guest demo."""

    from utils.demo_data import get_demo_transactions

    return prepare_transactions(get_demo_transactions())


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_summary(df, user_id=None, selected_month=None):
    return _transactions.calculate_summary(df)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def category_breakdown(df, user_id=None, selected_month=None):
    return _transactions.category_breakdown(df)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def monthly_trend(df, user_id=None, selected_month=None):
    return _transactions.monthly_trend(df)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def compare_months(
    df,
    current_month,
    previous_month,
    user_id=None,
    selected_month=None,
):
    return _transactions.compare_months(df, current_month, previous_month)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_budget_status(
    month_df,
    budgets,
    user_id=None,
    selected_month=None,
):
    return _budgets.calculate_budget_status(month_df, budgets)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_80c_headroom(
    financial_year_df,
    today,
    user_id=None,
    selected_month=None,
):
    return _tax.calculate_80c_headroom(financial_year_df, today)


def calculate_goal_metrics(goal, monthly_savings_avg=0.0):
    return _goals.calculate_goal_metrics(
        goal,
        today_local(),
        monthly_savings_avg,
    )


def parse_natural_language_query(query: str, df: pd.DataFrame) -> dict:
    return _insights.parse_natural_language_query(query, df, today_local())


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def detect_recurring_subscriptions(
    df,
    user_id=None,
    selected_month=None,
):
    return _insights.detect_recurring_subscriptions(df, today_local())


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def detect_spending_anomalies(user_id, selected_month, transactions=None):
    if user_id is None:
        raise ValueError("user_id is required to detect spending anomalies.")

    if transactions is None:
        transactions = get_transactions_for_month_range(
            str(pd.Period(selected_month, freq="M") - 6),
            selected_month,
            user_id=user_id,
        )
    return _insights.detect_spending_anomalies(transactions, selected_month)


def calculate_rolling_daily_spend(
    df,
    as_of=None,
    window_days=ROLLING_SPEND_WINDOW_DAYS,
):
    return _forecasting.calculate_rolling_daily_spend(
        df,
        as_of or today_local(),
        window_days,
    )


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_cash_flow_forecast(
    user_id,
    current_balance,
    forecast_days=30,
    transactions=None,
):
    if transactions is None:
        transactions = prepare_transactions(get_transactions(user_id))
    return _forecasting.calculate_cash_flow_forecast(
        transactions,
        current_balance,
        today_local(),
        forecast_days=forecast_days,
    )
