import html
import logging
from datetime import timedelta
from utils.dates import today_local
from utils.formatting import convert_currency

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics import (
    calculate_cash_flow_forecast,
    calculate_summary,
    detect_recurring_subscriptions,
    detect_spending_anomalies,
    get_month_data,
    load_demo_transactions,
    parse_natural_language_query,
    prepare_transactions,
)
from auth import get_user_context
from components.budget_components import render_budget_progress
from components.charts import apply_chart_theme, render_cash_flow, render_spending_breakdown
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
from theme import chart_layout, current_palette
from components.transaction_table import render_recent_transactions
from database import get_transactions
from utils.notifications import (
    get_upcoming_bill_due_dates,
    send_bill_due_reminders,
)


logger = logging.getLogger(__name__)


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
                        color:var(--text);letter-spacing:-0.03em;">
                        {html.escape(pretty_month(selected_month))}
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            st.caption("Monthly financial overview")


def _render_hero(summary, prev_summary, money):
    """Render the dashboard's primary savings snapshot."""

    savings = float(summary.get("savings", 0))
    previous_savings = float(prev_summary.get("savings", 0))
    if previous_savings:
        delta = (savings - previous_savings) / abs(previous_savings) * 100
        delta_label = f"{'▲' if delta >= 0 else '▼'} {abs(delta):.1f}% vs last month"
        delta_class = "success" if delta >= 0 else "danger"
    else:
        delta_label = "Compared with last month"
        delta_class = "neutral"

    spark_values = [previous_savings, savings]
    minimum = min(spark_values)
    maximum = max(spark_values, 1)
    points = []
    for index, value in enumerate(spark_values):
        x = 8 + index * 84
        y = 42 - ((value - minimum) / max(maximum - minimum, 1)) * 34
        points.append(f"{x:.0f},{y:.0f}")

    st.markdown(
        collapse_html(
            f"""
            <div class="ss-hero-card">
                <div>
                    <div class="ss-eyebrow">NET SAVINGS · THIS MONTH</div>
                    <div class="ss-hero-value ss-money">{money(savings)}</div>
                    <span class="ss-delta-chip {delta_class}">
                        {delta_label}
                    </span>
                    <div class="ss-muted ss-hero-helper">
                        Income after recorded expenses
                    </div>
                </div>
                <svg class="ss-sparkline" viewBox="0 0 100 48"
                    role="img" aria-label="Savings trend">
                    <polyline points="0,44 100,44"
                        class="ss-sparkline-base" />
                    <polyline points="{' '.join(points)}"
                        class="ss-sparkline-line" />
                </svg>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def _render_upcoming_bills(user_id, money):
    if get_user_context().get("is_demo"):
        return

    try:
        bills = get_upcoming_bill_due_dates(user_id)
    except Exception:
        logger.exception("Could not detect upcoming bills for user %s", user_id)
        st.warning("Upcoming bills could not be loaded right now.")
        return

    with st.container(border=True):
        st.subheader("Upcoming utility bills")
        st.caption("Recurring monthly payments expected within the next 3 days")
        if not bills:
            st.info("No recurring utility bills are due within the next 3 days.")
            return

        for bill in bills:
            days_until_due = bill["days_until_due"]
            due_text = (
                "due today"
                if days_until_due == 0
                else f"due in {days_until_due} day"
                + ("s" if days_until_due != 1 else "")
            )
            st.warning(
                f"{bill['bill_type']} · approximately "
                f"{money(bill['amount'])} · {due_text} "
                f"({bill['due_date']:%d %b %Y})"
            )

        user_context = get_user_context()
        today_key = today_local().isoformat()
        if user_context.get("bill_reminders_sent_on") == today_key:
            return

        try:
            sent, detail = send_bill_due_reminders(user_id, bills=bills)
        except Exception:
            logger.exception(
                "Could not send bill reminders for user %s",
                user_id,
            )
            st.warning("Telegram bill reminders could not be sent right now.")
            return
        if sent and detail == "Bill due reminders sent to Telegram.":
            user_context["bill_reminders_sent_on"] = today_key
            st.toast("Bill reminders sent to Telegram.", icon="🔔")
        elif not sent and detail.startswith("Save your Telegram"):
            st.caption(
                "Save your Telegram bot token and chat ID in Settings "
                "to receive automatic reminders."
            )


def _render_spending_anomaly_alerts(user_id, selected_month, money):
    transactions = (
        load_demo_transactions()
        if get_user_context().get("is_demo")
        else None
    )
    anomalies = detect_spending_anomalies(
        user_id,
        selected_month,
        transactions=transactions,
    )
    if not anomalies:
        return

    with st.expander(
        "🚨 Unusual Spending Alerts Detected",
        expanded=True,
    ):
        for anomaly in anomalies:
            merchant = html.escape(
                anomaly["description"] or anomaly["category"],
                quote=True,
            )
            category = html.escape(anomaly["category"], quote=True)
            amount = html.escape(money(anomaly["amount"]), quote=True)
            percentage = anomaly["percentage_above_normal"]
            percentage_label = f"{percentage:.0f}%"
            baseline_months = anomaly["baseline_months"]
            date_label = anomaly["date"].strftime("%d %b %Y")
            st.markdown(
                collapse_html(
                    f"""
                    <div style="display:flex;align-items:center;
                        justify-content:space-between;gap:12px;
                        padding:12px 16px;margin:8px 0;
                        border:1px solid color-mix(in srgb, var(--danger) 30%, transparent);
                        border-radius:12px;
                        background:color-mix(in srgb, var(--danger) 18%, transparent);">
                        <div>
                            <div style="font-weight:750;color:var(--text);">
                                {merchant}
                                <span style="color:var(--text-muted);font-weight:500;">
                                    · {category} · {date_label}
                                </span>
                            </div>
                            <div style="margin-top:4px;color:var(--text-muted);">
                                {amount} is {percentage_label} higher than
                                your {baseline_months}-month category average.
                            </div>
                        </div>
                        <span style="white-space:nowrap;padding:5px 9px;
                            border-radius:999px;background:var(--danger);
                            color:var(--on-accent);font-size:0.8rem;font-weight:750;">
                            +{percentage_label}
                        </span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )


def _render_natural_language_search(df, money):
    suggestion_columns = st.columns(3, gap="small")
    suggestions = (
        "Top spending category?",
        "How much on Food?",
        "Can I afford X?",
    )
    for column, suggestion in zip(suggestion_columns, suggestions):
        with column:
            st.button(
                suggestion,
                key=f"nl_suggestion_{suggestion}",
                on_click=lambda value=suggestion: st.session_state.update(
                    nl_search_query=value
                ),
                width="stretch",
            )

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
            "var(--text)",
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

    with st.container(border=True):
        next_dates = [
            subscription["last_payment_date"] + timedelta(days=30)
            for subscription in subscriptions
        ]
        next_expected = min(next_dates)
        st.markdown(
            f"""
            <div class="ss-recurring-card">
                <div>
                    <div class="ss-eyebrow">RECURRING & SUBSCRIPTIONS</div>
                    <strong>{money(monthly_cost)} / month</strong>
                    <span>{len(subscriptions)} recurring payment(s) detected</span>
                </div>
                <div>
                    <div class="ss-muted">Next expected</div>
                    <strong>{next_expected:%d %b %Y}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if yearly_projection > monthly_income * 0.15:
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


def _render_cash_flow_forecast(user_id, money):
    """Render a recorded-history balance estimate and 90-day forecast."""

    is_demo = bool(get_user_context().get("is_demo"))
    transactions = (
        load_demo_transactions()
        if is_demo
        else prepare_transactions(get_transactions(user_id))
    )
    today = today_local()
    transaction_dates = pd.to_datetime(
        transactions["transaction_date"],
        errors="coerce",
        format="ISO8601",
    )
    historical = transactions.loc[
        transaction_dates.notna()
        & transaction_dates.dt.date.le(today)
    ].copy()
    historical["transaction_date"] = transaction_dates.loc[
        historical.index
    ]
    historical["balance_change"] = historical["amount"].where(
        historical["transaction_type"].eq("Income"),
        -historical["amount"],
    )
    current_balance = float(historical["balance_change"].sum())

    forecast = calculate_cash_flow_forecast(
        user_id,
        current_balance,
        forecast_days=90,
        transactions=transactions,
    )
    projected_df = forecast["projected_df"]
    runway_days = forecast["runway_days"]
    runout_date = forecast["runout_date"]

    with st.container(border=True):
        st.subheader("🔮 30-Day Cash Flow Forecast & Runway")
        st.caption(
            "Starting balance is estimated from recorded income and "
            "expenses; add any unrecorded opening balance to your history."
        )

        with st.container(horizontal=True):
            st.metric("Estimated available balance", money(current_balance))
            st.metric(
                "Forecast burn rate · daily",
                money(forecast["burn_rate_daily"]),
            )
            st.metric(
                "Estimated runway",
                f"{runway_days} days" if runway_days is not None else "No run-out",
            )

        if runway_days is not None and runway_days < 30:
            st.warning(
                f"At your current daily spend of "
                f"{money(forecast['burn_rate_daily'])}/day, your available "
                f"balance is projected to reach zero on "
                f"{runout_date.strftime('%d %b %Y')}.",
                title="Cash runway below 30 days",
            )
        elif runway_days is None:
            st.info(
                "No run-out date is projected because no recent expenses "
                "or recurring bills were found."
            )

        forecast_by_day = projected_df.set_index("date")["projected_balance"]
        with st.container(horizontal=True):
            for horizon in (30, 60, 90):
                horizon_date = today + timedelta(days=horizon)
                projected_balance = forecast_by_day.get(horizon_date)
                st.metric(
                    f"Projected balance · {horizon} days",
                    money(projected_balance)
                    if projected_balance is not None
                    else "Not available",
                )

        history_start = today - timedelta(days=29)
        historical["balance_date"] = historical[
            "transaction_date"
        ].dt.date
        daily_changes = historical.groupby("balance_date")[
            "balance_change"
        ].sum()
        history_dates = pd.date_range(
            start=history_start,
            end=today,
            freq="D",
        )
        prior_balance = float(
            historical.loc[
                historical["balance_date"] < history_start,
                "balance_change",
            ].sum()
        )
        history_balances = []
        balance = prior_balance
        for history_date in history_dates:
            balance += float(daily_changes.get(history_date.date(), 0.0))
            history_balances.append(balance)

        forecast_end = today + timedelta(days=30)
        forecast_through_30_days = projected_df.loc[
            projected_df["date"] <= forecast_end
        ]
        forecast_dates = [today] + forecast_through_30_days[
            "date"
        ].tolist()
        forecast_balances = [current_balance] + forecast_through_30_days[
            "projected_balance"
        ].tolist()
        currency_prefix = str(get_user_context().get("currency_symbol", "₹"))
        historical_plot_balances = [
            convert_currency(amount, currency_prefix)
            for amount in history_balances
        ]
        forecast_plot_balances = [
            convert_currency(amount, currency_prefix)
            for amount in forecast_balances
        ]
        palette = current_palette()
        chart_text_color = palette["text"]
        chart_grid_color = palette["grid"]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=history_dates,
                y=historical_plot_balances,
                mode="lines",
                name="Recorded balance",
                line=dict(color=palette["info"], width=3),
                fill="tozeroy",
                fillcolor=palette["accent_soft"],
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    f"{currency_prefix}%{{y:,.2f}}"
                    "<extra>Recorded balance</extra>"
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=forecast_dates,
                y=forecast_plot_balances,
                mode="lines",
                name="Projected balance",
                line=dict(color=palette["warning"], width=3, dash="dash"),
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    f"{currency_prefix}%{{y:,.2f}}"
                    "<extra>Projected balance</extra>"
                ),
            )
        )
        if forecast_balances and min(forecast_balances) < 0:
            fig.add_hrect(
                y0=min(forecast_balances),
                y1=0,
                fillcolor=palette["danger"],
                opacity=0.10,
                line_width=0,
                annotation_text="Danger zone",
                annotation_position="bottom left",
                annotation_font_color=palette["danger"],
            )
        apply_chart_theme(
            fig,
            palette,
            font=dict(color=chart_text_color),
            height=360,
            margin=dict(l=12, r=12, t=20, b=12),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(
                title="Balance",
                tickprefix=currency_prefix,
                tickformat=",.0f",
                gridcolor=chart_grid_color,
            ),
        )
        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )


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
    _render_upcoming_bills(user_id, money)
    _render_spending_anomaly_alerts(user_id, selected_month, money)
    _render_natural_language_search(df, money)
    spacer(14)

    if month_df.empty:
        _render_empty_state(selected_month)

    _render_hero(summary, prev_summary, money)
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

    _render_cash_flow_forecast(user_id, money)

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