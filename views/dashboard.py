import html
from utils.dates import today_local

import pandas as pd
import streamlit as st

from analytics import (
    calculate_summary,
    detect_recurring_subscriptions,
    get_month_data,
    parse_natural_language_query,
)
from components.budget_components import render_budget_progress
from components.charts import render_cash_flow, render_spending_breakdown
from components.metric_cards import (
    AMBER,
    BLUE,
    GREEN,
    MUTED,
    RED,
    collapse_html,
    delta_html,
    go_to,
    pretty_month,
    section_header,
    spacer,
    stat_card,
)
from components.transaction_table import render_recent_transactions


# -----------------------------
# Data helpers
# -----------------------------

def _previous_month(selected_month):
    return str(pd.Period(selected_month, "M") - 1)


def _daily_average(expenses_total, selected_month, today):
    """Average daily spending and the days used for it."""

    period = pd.Period(selected_month, "M")
    current = pd.Period(today, "M")

    if period == current:
        days = today.day
    elif period < current:
        days = period.days_in_month
    else:
        days = 1

    return expenses_total / max(days, 1), period.days_in_month, period == current


# -----------------------------
# Page sections
# -----------------------------

def _render_header(selected_month):
    header_left, header_right = st.columns([3, 1], gap="large")

    with header_left:
        st.markdown(
            '<div class="ss-eyebrow">'
            "SPENDSENSE AI · PERSONAL FINANCE"
            "</div>"
            '<div class="ss-page-title">Your money, in focus.</div>'
            '<div class="ss-subtitle">'
            "Understand your cash flow, track your spending, "
            "and make more confident financial decisions."
            "</div>",
            unsafe_allow_html=True,
        )

    with header_right:
        with st.container(border=True):
            st.caption("📅 ANALYSIS PERIOD")
            st.markdown(
                collapse_html(
                    f"""
                    <div style="font-size:1.5rem;font-weight:800;
                        color:#F8FAFC;letter-spacing:-0.03em;">
                        {html.escape(pretty_month(selected_month))}
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            st.caption("Monthly financial overview")


def _render_natural_language_search(df, money):
    query = st.text_input(
        "💬 Ask SpendSense AI",
        placeholder=(
            "e.g., How much did I spend on Food? "
            "or What is my top category?"
        ),
        key="nl_search_query",
    )
    if not query.strip():
        return

    result = parse_natural_language_query(query, df)
    with st.container(border=True):
        if not result["success"]:
            st.info(
                result["answer"],
                title="Try asking a different way",
            )
            st.caption(
                "For example: “How much did I spend on Food?”, "
                "“What is my highest expense category?”, or "
                "“How many transactions?”"
            )
            return

        st.caption("SPENDSENSE ANSWER")
        st.markdown(f"**{result['answer']}**")
        metric_type = result["type"]
        metric_value = result["metric_val"]

        if metric_type == "currency":
            st.metric("Amount", money(metric_value), border=True)
        elif metric_type == "count":
            st.metric("Transactions", f"{metric_value:,}", border=True)
        elif metric_type == "comparison":
            current, previous, change = st.columns(3)
            current.metric("This month", money(metric_value["current"]))
            previous.metric("Last month", money(metric_value["previous"]))
            change.metric("Change", money(metric_value["change"]))


def _render_empty_state(selected_month):
    with st.container(border=True):
        text_col, button_col = st.columns([3, 1], gap="large")

        with text_col:
            st.markdown(
                f"**No transactions recorded for "
                f"{pretty_month(selected_month)}.**"
            )
            st.caption(
                "Add your income and expenses to unlock your cash flow, "
                "spending breakdown, and insights."
            )

        with button_col:
            st.button(
                "➕ Add transaction",
                key="dashboard_empty_add",
                on_click=go_to,
                args=("Add Transaction",),
                use_container_width=True,
            )

    spacer(8)


def _render_kpis(summary, prev_summary, money):
    has_prev = prev_summary["transaction_count"] > 0

    st.markdown(
        collapse_html(
            f"""
            <div style="margin:8px 0 14px 0;color:{MUTED};
                font-size:0.76rem;font-weight:800;
                letter-spacing:0.13em;text-transform:uppercase;">
                Your financial snapshot
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    income = summary["income"]
    expenses = summary["expenses"]
    savings = summary["savings"]
    rate = float(summary["savings_rate"])

    k1, k2, k3, k4 = st.columns(4, gap="medium")

    with k1:
        stat_card(
            "💰",
            "MONTHLY INCOME",
            money(income),
            GREEN,
            "Money received this month",
            delta_html(
                "percent",
                income,
                prev_summary["income"] if has_prev else None,
                True,
                money,
            ),
        )

    with k2:
        stat_card(
            "💳",
            "TOTAL EXPENSES",
            money(expenses),
            RED,
            "Money spent this month",
            delta_html(
                "percent",
                expenses,
                prev_summary["expenses"] if has_prev else None,
                False,
                money,
            ),
        )

    with k3:
        stat_card(
            "📈",
            "NET SAVINGS",
            money(savings),
            GREEN if savings >= 0 else RED,
            "Surplus this month" if savings >= 0 else "Deficit this month",
            delta_html(
                "amount",
                savings,
                prev_summary["savings"] if has_prev else None,
                True,
                money,
            ),
        )

    with k4:
        if income <= 0:
            rate_text, rate_color = "—", MUTED
            rate_label = "Add income to calculate"
            rate_delta = delta_html("points", 0, None, True, money)
        else:
            rate_text = f"{rate:.1f}%"

            if rate >= 20:
                rate_color, rate_label = GREEN, "Strong savings"
            elif rate >= 10:
                rate_color, rate_label = AMBER, "Room to improve"
            else:
                rate_color, rate_label = RED, "Needs attention"

            prev_rate = (
                float(prev_summary["savings_rate"])
                if has_prev and prev_summary["income"] > 0
                else None
            )
            rate_delta = delta_html(
                "points", rate, prev_rate, True, money
            )

        stat_card(
            "🎯",
            "SAVINGS RATE",
            rate_text,
            rate_color,
            rate_label,
            rate_delta,
        )


def _render_quick_stats(summary, month_df, selected_month, today, money):
    expenses_df = month_df.loc[month_df["transaction_type"] == "Expense"]

    daily_avg, days_in_month, is_current = _daily_average(
        summary["expenses"], selected_month, today
    )

    if is_current and summary["expenses"] > 0:
        daily_note = f"Projected {money(daily_avg * days_in_month)} by month end"
    else:
        daily_note = "Average expense per day"

    if expenses_df.empty:
        largest_value = money(0)
        largest_note = "No expenses yet"
    else:
        largest = expenses_df.loc[expenses_df["amount"].idxmax()]
        largest_value = money(largest["amount"])
        largest_note = html.escape(str(largest["category"]))

    spacer(4)

    s1, s2, s3 = st.columns(3, gap="medium")
    small = "1.25rem"

    with s1:
        stat_card(
            "🧾",
            "TRANSACTIONS",
            str(summary["transaction_count"]),
            "#F1F5F9",
            "Recorded this month",
            size=small,
        )

    with s2:
        stat_card(
            "📆",
            "DAILY AVERAGE SPEND",
            money(daily_avg),
            BLUE,
            daily_note,
            size=small,
        )

    with s3:
        stat_card(
            "🔥",
            "LARGEST EXPENSE",
            largest_value,
            AMBER,
            largest_note,
            size=small,
        )


def _render_insights(month_df, budgets, total_budget, generate_insights, show_insights):
    with st.container(border=True):
        title_col, action_col = st.columns([3, 1])

        with title_col:
            section_header(
                "Financial Insights",
                "Observations based on your recorded "
                "transactions and budgets",
            )

        with action_col:
            spacer(5)
            st.button(
                "See all insights",
                key="dashboard_all_insights",
                on_click=go_to,
                args=("Financial Insights",),
                use_container_width=True,
            )

        insights = generate_insights(
            month_df,
            budget_amount=total_budget,
            budgets=budgets,
        )

        show_insights(insights[:3])


def _render_subscription_warning(
    df,
    monthly_income,
    money,
    user_id=None,
    selected_month=None,
):
    if monthly_income <= 0:
        return

    subscriptions = detect_recurring_subscriptions(
        df,
        user_id=user_id,
        selected_month=selected_month,
    )
    if not subscriptions:
        return

    monthly_cost = sum(
        subscription["monthly_cost"] for subscription in subscriptions
    )
    yearly_projection = sum(
        subscription["yearly_projection"] for subscription in subscriptions
    )
    monthly_income_share = yearly_projection / monthly_income

    if yearly_projection <= monthly_income * 0.15:
        return

    with st.container(border=True):
        st.warning(
            f"Detected recurring subscriptions cost about "
            f"{money(monthly_cost)} per month "
            f"({money(yearly_projection)} per year), or "
            f"{monthly_income_share:.1%} of one month's income annually. "
            "Review these payments if you want to reduce fixed expenses.",
            title="Annual subscription costs exceed 15% of monthly income",
        )

        descriptions = ", ".join(
            subscription["description"] for subscription in subscriptions
        )
        st.text(f"Detected subscriptions: {descriptions}")


# -----------------------------
# Public page function
# -----------------------------

def render_dashboard(
    selected_month,
    summary,
    df,
    month_df,
    budgets,
    total_budget,
    money,
    calculate_budget_status,
    generate_insights,
    show_insights,
    user_id=None,
):
    """Render the SpendSense AI financial dashboard."""

    today = today_local()

    previous_month = _previous_month(selected_month)
    prev_month_df = get_month_data(df, previous_month)
    prev_summary = calculate_summary(
        prev_month_df,
        user_id=user_id,
        selected_month=previous_month,
    )

    _render_header(selected_month)
    _render_natural_language_search(df, money)
    spacer(14)

    if month_df.empty:
        _render_empty_state(selected_month)

    _render_kpis(summary, prev_summary, money)
    _render_subscription_warning(
        df,
        summary["income"],
        money,
        user_id=user_id,
        selected_month=selected_month,
    )
    _render_quick_stats(summary, month_df, selected_month, today, money)

    spacer(14)

    cashflow_col, spending_col = st.columns([1.85, 1], gap="large")

    with cashflow_col:
        render_cash_flow(df, selected_month, user_id=user_id)

    with spending_col:
        render_spending_breakdown(
            month_df,
            money,
            user_id=user_id,
            selected_month=selected_month,
        )

    spacer(6)

    recent_col, budget_col = st.columns([1.25, 1], gap="large")

    with recent_col:
        render_recent_transactions(month_df, selected_month, money)

    with budget_col:
        render_budget_progress(
            month_df,
            budgets,
            calculate_budget_status,
            money,
            user_id=user_id,
            selected_month=selected_month,
        )

    spacer(6)

    _render_insights(
        month_df,
        budgets,
        total_budget,
        generate_insights,
        show_insights,
    )