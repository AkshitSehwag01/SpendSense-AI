import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import calculate_summary, get_month_data, monthly_trend
from auth import current_user_id
from components.metric_cards import (
    BLUE,
    GREEN,
    MUTED,
    RED,
    collapse_html,
    delta_html,
    go_to,
    page_header,
    pretty_month,
    safe_float,
    section_header,
    spacer,
    stat_card,
)
from database import get_all_budgets
from domain.insights import classify_savings_rate, income_allocation
from domain.transactions import (
    best_savings_month,
    month_window,
    previous_month as _previous_month,
    savings_rate,
)
from theme import chart_layout, current_palette
from components.charts import apply_chart_theme
from utils.notifications import (
    format_weekly_digest,
    send_telegram_message,
)


CHART_CONFIG = {"displayModeBar": False}

# Spreadsheet programs treat cells starting with these characters as
# formulas. A leading apostrophe keeps them as plain text.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


# -----------------------------
# Small helpers
# -----------------------------

def _health_verdict(savings_rate, income):
    """Return (headline, colour) describing the month's savings health."""

    return {
        "no_income": ("No income recorded this month", MUTED),
        "excellent": (
            "Excellent. You're saving a strong share of your income.",
            GREEN,
        ),
        "healthy": ("Healthy. You're saving steadily.", BLUE),
        "low": (
            "Room to improve. Try to save a little more.",
            "var(--warning)",
        ),
        "negative": ("Spending is higher than income this month.", RED),
    }[classify_savings_rate(savings_rate, income)]


def _csv_safe(value):
    if not isinstance(value, str):
        return value

    text = value
    if text.startswith(_FORMULA_PREFIXES):
        return "'" + text

    return text


def _dataframe_to_csv(df):
    """Return UTF-8 CSV bytes, escaping formulas in text columns."""

    safe_df = df.copy()

    for column in safe_df.select_dtypes(include=["object", "string"]):
        safe_df[column] = safe_df[column].map(_csv_safe)

    # utf-8-sig makes Excel open the file with the correct characters.
    return safe_df.to_csv(index=False).encode("utf-8-sig")


# -----------------------------
# Data builders (also used for the CSV exports)
# -----------------------------

def _twelve_month_window(trend, selected_month):
    """Twelve months ending at the selected month; empty months are 0."""

    window = month_window(trend, selected_month, 12)

    window["month_label"] = window["month"].map(pretty_month)

    return window


def _history_table(trend, money):
    """One formatted row per month, newest first."""

    rows = []

    for _, row in trend.sort_values("month", ascending=False).iterrows():
        income = safe_float(row["income"])
        expenses = safe_float(row["expenses"])
        savings = safe_float(row["savings"])

        rate_value = savings_rate(income, savings)
        rate = f"{rate_value:.1f}%" if rate_value is not None else "—"

        rows.append({
            "Month": pretty_month(row["month"]),
            "Income": money(income),
            "Expenses": money(expenses),
            "Savings": money(savings),
            "Savings rate": rate,
        })

    return pd.DataFrame(rows)


def _transactions_export(data):
    """A clean transactions file: no internal IDs or timestamps."""

    if data is None or data.empty:
        return None

    return pd.DataFrame({
        "Date": data["transaction_date"].dt.strftime("%Y-%m-%d"),
        "Type": data["transaction_type"],
        "Category": data["category"],
        "Description": data["description"],
        "Amount": data["amount"].round(2),
    }).sort_values("Date", ascending=False, kind="stable")


def _summary_export(trend):
    if trend is None or trend.empty:
        return None

    export = trend.sort_values("month", ascending=False).copy()

    export["Savings rate (%)"] = [
        round(rate, 1) if rate is not None else ""
        for rate in (
            savings_rate(row.income, row.savings)
            for row in export.itertuples()
        )
    ]

    export = export.rename(columns={
        "month": "Month",
        "income": "Income",
        "expenses": "Expenses",
        "savings": "Savings",
    })

    return export


def _budgets_export(budgets):
    if not budgets:
        return None

    export = pd.DataFrame(budgets).rename(columns={
        "month": "Month",
        "category": "Category",
        "amount": "Monthly budget",
    })

    return export[["Month", "Category", "Monthly budget"]]


# -----------------------------
# Page sections
# -----------------------------

def _render_empty_state(month_label):
    with st.container(border=True):
        text_col, button_col = st.columns([3, 1], gap="large")

        with text_col:
            st.markdown(
                f"**No financial activity recorded for {month_label}.**"
            )
            st.caption("Add income and expenses to see this month's report.")

        with button_col:
            st.button(
                "➕ Add transaction",
                key="reports_empty_add",
                on_click=go_to,
                args=("Add Transaction",),
                use_container_width=True,
            )

    spacer(8)


def _render_kpis(summary, prev_summary, money):
    has_prev = prev_summary["transaction_count"] > 0

    income = safe_float(summary.get("income"))
    expenses = safe_float(summary.get("expenses"))
    savings = safe_float(summary.get("savings"))
    savings_rate = safe_float(summary.get("savings_rate"))
    transactions = int(safe_float(summary.get("transaction_count")))

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        stat_card(
            "💰", "INCOME", money(income), GREEN, "Money received",
            delta_html(
                "percent", income,
                prev_summary["income"] if has_prev else None,
                True, money,
            ),
        )

    with c2:
        stat_card(
            "💳", "EXPENSES", money(expenses), RED, "Money spent",
            delta_html(
                "percent", expenses,
                prev_summary["expenses"] if has_prev else None,
                False, money,
            ),
        )

    with c3:
        stat_card(
            "📈", "SAVINGS", money(savings),
            BLUE if savings >= 0 else RED,
            "Income minus expenses",
            delta_html(
                "amount", savings,
                prev_summary["savings"] if has_prev else None,
                True, money,
            ),
        )

    with c4:
        prev_rate = (
            safe_float(prev_summary["savings_rate"])
            if has_prev and prev_summary["income"] > 0
            else None
        )

        stat_card(
            "🎯",
            "SAVINGS RATE",
            f"{savings_rate:.1f}%" if income > 0 else "—",
            "var(--text)" if income > 0 else MUTED,
            f"{transactions} transactions",
            delta_html(
                "points", savings_rate,
                prev_rate if income > 0 else None,
                True, money,
            ),
        )


def _render_month_at_a_glance(summary):
    income = safe_float(summary.get("income"))
    expenses = safe_float(summary.get("expenses"))
    savings_rate = safe_float(summary.get("savings_rate"))

    headline, headline_color = _health_verdict(savings_rate, income)

    allocation = income_allocation(income, expenses)
    if allocation is not None:
        spent_raw = allocation["spent_percent"]
        spent_width = min(max(spent_raw, 0.0), 100.0)
        saved_width = allocation["saved_percent"]
        spent_label = f"Spent {spent_raw:.0f}% of income"
        saved_label = f"Saved {saved_width:.0f}%"
    else:
        spent_width = saved_width = 0.0
        spent_label = "Spent —"
        saved_label = "Saved —"

    with st.container(border=True):
        section_header(
            "Month at a glance",
            "How your income was used this month.",
        )

        st.markdown(
            collapse_html(
                f"""
                <div style="font-weight:700;color:{headline_color};
                    margin-bottom:12px;">{headline}</div>
                <div style="display:flex;height:12px;border-radius:999px;
                    overflow:hidden;background:var(--border);">
                    <div style="width:{spent_width:.1f}%;
                        background:linear-gradient(90deg,
                        var(--warning),var(--accent));"></div>
                    <div style="width:{saved_width:.1f}%;
                        background:linear-gradient(90deg,
                        var(--accent),var(--success));"></div>
                </div>
                <div style="display:flex;justify-content:space-between;
                    margin-top:10px;font-size:0.8rem;color:{MUTED};">
                    <span><span style="color:var(--warning);">●</span>
                        {spent_label}</span>
                    <span><span style="color:var(--success);">●</span>
                        {saved_label}</span>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


def _render_comparison_chart(trend, selected_month):
    window = _twelve_month_window(trend, selected_month)

    if window[["income", "expenses"]].sum().sum() <= 0:
        st.info("Your chart will appear when transactions are recorded.")
        return

    labels = window["month_label"].tolist()

    long = window.melt(
        id_vars=["month", "month_label"],
        value_vars=["income", "expenses"],
        var_name="kind",
        value_name="amount",
    )

    long["kind"] = long["kind"].map(
        {"income": "Income", "expenses": "Expenses"}
    )

    fig = px.bar(
        long,
        x="month_label",
        y="amount",
        color="kind",
        barmode="group",
        color_discrete_map={
            "Income": current_palette()["success"],
            "Expenses": current_palette()["danger"],
        },
        labels={"month_label": "", "amount": "Amount (₹)", "kind": ""},
        category_orders={"month_label": labels},
    )

    fig.update_traces(
        marker_line_width=0,
        hovertemplate="₹%{y:,.2f}<extra>%{fullData.name}</extra>",
    )

    palette = current_palette()
    apply_chart_theme(
        fig,
        palette,
        height=330,
        autosize=True,
        bargap=0.28,
        bargroupgap=0.08,
        hovermode="x unified",
        margin=dict(l=12, r=12, t=25, b=12),
        font=dict(
            family="Inter, Arial, sans-serif",
            color=palette["text"],
            size=12,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color=palette["text"]),
        ),
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=labels,
            showgrid=False,
            showline=True,
            linecolor=palette["border"],
            tickfont=dict(color=palette["text_muted"], size=11),
            fixedrange=True,
        ),
        yaxis=dict(
            gridcolor=palette["grid"],
            zeroline=False,
            tickprefix="₹",
            tickformat=",.0f",
            tickfont=dict(color=palette["text_muted"]),
            fixedrange=True,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)


def _render_history(trend, selected_month, money):
    with st.container(border=True):
        section_header(
            "Monthly history",
            "Income and expenses for the last twelve months, "
            "and every month in the table.",
        )

        if trend is None or trend.empty:
            st.info(
                "Monthly history will appear after you add transactions."
            )
            return

        _render_comparison_chart(trend, selected_month)

        best = best_savings_month(trend)

        if best is not None:
            st.caption(
                f"🏆 Best month so far: {pretty_month(best['month'])} · "
                f"saved {money(best['savings'])}"
            )

        spacer(4)

        st.dataframe(
            _history_table(trend, money),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Month": st.column_config.TextColumn(width="medium"),
                "Income": st.column_config.TextColumn(width="medium"),
                "Expenses": st.column_config.TextColumn(width="medium"),
                "Savings": st.column_config.TextColumn(width="medium"),
                "Savings rate": st.column_config.TextColumn(width="small"),
            },
        )


def _render_exports(
    month_df,
    df,
    trend,
    selected_month,
    month_label,
    all_budgets=None,
):
    budgets = all_budgets

    if budgets is None:
        try:
            budgets = get_all_budgets()
        except Exception as error:
            detail = str(error).strip() or type(error).__name__
            st.error(
                "Budget export is unavailable because budgets could not be "
                f"loaded from the database. Details: {detail}"
            )

    with st.container(border=True):
        section_header(
            "Export your data",
            "Download your records as CSV files to open in Excel or "
            "share with your accountant.",
        )

        left, right = st.columns(2, gap="medium")

        with left:
            if month_df is not None and not month_df.empty:
                st.download_button(
                    label=f"⬇  {month_label} transactions",
                    data=lambda: _dataframe_to_csv(
                        _transactions_export(month_df)
                    ),
                    file_name=f"spendsense_transactions_{selected_month}.csv",
                    mime="text/csv",
                    width="stretch",
                    key="export_month_csv",
                )
            else:
                st.info(f"No transactions to export for {month_label}.")

            if trend is not None and not trend.empty:
                st.download_button(
                    label="⬇  Monthly summary",
                    data=lambda: _dataframe_to_csv(_summary_export(trend)),
                    file_name="spendsense_monthly_summary.csv",
                    mime="text/csv",
                    width="stretch",
                    key="export_summary_csv",
                )

        with right:
            if df is not None and not df.empty:
                st.download_button(
                    label="⬇  All transactions (every month)",
                    data=lambda: _dataframe_to_csv(_transactions_export(df)),
                    file_name="spendsense_all_transactions.csv",
                    mime="text/csv",
                    width="stretch",
                    key="export_all_csv",
                )
            else:
                st.info("No transactions to export yet.")

            if budgets:
                st.download_button(
                    label="⬇  Budgets (every month)",
                    data=lambda: _dataframe_to_csv(_budgets_export(budgets)),
                    file_name="spendsense_budgets.csv",
                    mime="text/csv",
                    width="stretch",
                    key="export_budgets_csv",
                )
            else:
                st.download_button(
                    label="⬇  Budgets (every month)",
                    data=b"",
                    file_name="spendsense_budgets.csv",
                    mime="text/csv",
                    disabled=True,
                    width="stretch",
                    key="export_budgets_csv",
                )
                if budgets is not None:
                    st.info("No budgets to export yet.")

    return budgets


def _render_telegram_summary(
    summary,
    month_df,
    budgets,
    selected_month,
    is_demo=False,
):
    if is_demo:
        st.info("Telegram sending is disabled while exploring demo data.")
        return

    with st.container(border=True):
        section_header(
            "Send Summary to Telegram",
            "Manually send this report period's summary to the Telegram "
            "chat configured in Streamlit secrets.",
        )
        st.warning(
            "This sends financial summary data outside SpendSense AI to the "
            "configured Telegram chat. Only continue if you trust that chat."
        )
        confirmed = st.checkbox(
            "I confirm I want to send this financial summary to Telegram.",
            key="telegram_summary_confirmed",
        )
        if not st.button(
            "Send Summary to Telegram",
            key="send_telegram_summary",
            disabled=not confirmed,
        ):
            return

        expenses = (
            month_df.loc[month_df["transaction_type"] == "Expense"]
            if month_df is not None and not month_df.empty
            else pd.DataFrame(columns=["category", "amount"])
        )
        if expenses.empty:
            top_categories = []
            spent_by_category = {}
        else:
            category_totals = (
                expenses.groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )
            top_categories = list(category_totals.head(5).items())
            spent_by_category = {
                str(category).casefold(): float(amount)
                for category, amount in category_totals.items()
            }

        budget_alerts = []
        for budget in budgets or []:
            if budget.get("month") != selected_month:
                continue
            category = str(budget.get("category") or "Other")
            limit = safe_float(budget.get("amount"))
            spent = spent_by_category.get(category.casefold(), 0.0)
            if limit > 0 and spent >= limit * 0.8:
                budget_alerts.append(
                    {
                        "category": category,
                        "spent": spent,
                        "budget": limit,
                    }
                )

        digest_summary = dict(summary)
        digest_summary["period"] = pretty_month(selected_month)
        message = format_weekly_digest(
            user_id=current_user_id(),
            summary=digest_summary,
            top_categories=top_categories,
            budget_alerts=budget_alerts,
        )
        sent, detail = send_telegram_message(message)
        if sent:
            st.toast(detail, icon="📨")
        else:
            st.error(detail)


# -----------------------------
# Public page function
# -----------------------------

def render_reports(
    selected_month,
    summary,
    month_df,
    df,
    money,
    all_budgets=None,
    is_demo=False,
    user_id=None,
):
    """Render financial reports and transaction exports."""

    month_label = pretty_month(selected_month)

    previous_month = _previous_month(selected_month)
    prev_summary = calculate_summary(
        get_month_data(df, previous_month),
        user_id=user_id,
        selected_month=previous_month,
    )

    page_header(
        "SPENDSENSE AI · REPORTS",
        "Your financial reports.",
        "Review your month, compare it with earlier months, and export "
        "your data whenever you need it.",
        "REPORT PERIOD",
        month_label,
        "Summary, history and exports",
    )
    spacer(14)

    if month_df.empty:
        _render_empty_state(month_label)

    _render_kpis(summary, prev_summary, money)
    spacer(14)

    if not month_df.empty:
        _render_month_at_a_glance(summary)
        spacer(8)

    trend = monthly_trend(
        df,
        user_id=user_id,
        selected_month=selected_month,
    )

    _render_history(trend, selected_month, money)
    spacer(8)

    budgets = _render_exports(
        month_df,
        df,
        trend,
        selected_month,
        month_label,
        all_budgets=all_budgets,
    )
    spacer(8)
    _render_telegram_summary(
        summary,
        month_df,
        budgets,
        selected_month,
        is_demo=is_demo,
    )