import streamlit as st

from analytics import monthly_trend
from components.metric_cards import (
    AMBER,
    BLUE,
    GREEN,
    MUTED,
    RED,
    collapse_html,
    go_to,
    page_header,
    pretty_month,
    safe_float,
    section_header,
    spacer,
    stat_card,
)


def _health_verdict(savings_rate, income):
    """Return (headline, colour) describing the month's savings health."""
    if income <= 0:
        return "No income recorded this month", MUTED
    if savings_rate >= 20:
        return "Excellent. You're saving a strong share of your income.", GREEN
    if savings_rate >= 10:
        return "Healthy. You're saving steadily.", BLUE
    if savings_rate > 0:
        return "Room to improve. Try to save a little more.", AMBER
    return "Spending is higher than income this month.", RED


def render_reports(
    selected_month,
    summary,
    month_df,
    df,
    money,
):
    """Render financial reports and transaction exports."""

    month_label = pretty_month(selected_month)

    income = safe_float(summary.get("income"))
    expenses = safe_float(summary.get("expenses"))
    savings = safe_float(summary.get("savings"))
    savings_rate = safe_float(summary.get("savings_rate"))
    transactions = int(safe_float(summary.get("transaction_count")))

    # ---------------------------------------------------------------- header
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
        with st.container(border=True):
            text_col, button_col = st.columns([3, 1], gap="large")

            with text_col:
                st.markdown(
                    f"**No financial activity recorded for {month_label}.**"
                )
                st.caption(
                    "Add income and expenses to see this month's report."
                )

            with button_col:
                st.button(
                    "➕ Add transaction",
                    key="reports_empty_add",
                    on_click=go_to,
                    args=("Add Transaction",),
                    use_container_width=True,
                )

        spacer(8)

    # ---------------------------------------------------------- summary cards
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        stat_card("💰", "INCOME", money(income), GREEN, "Money received")

    with c2:
        stat_card("💳", "EXPENSES", money(expenses), AMBER, "Money spent")

    with c3:
        stat_card(
            "📈",
            "SAVINGS",
            money(savings),
            BLUE if savings >= 0 else RED,
            "Income minus expenses",
        )

    with c4:
        stat_card(
            "🎯",
            "SAVINGS RATE",
            f"{savings_rate:.1f}%" if income > 0 else "—",
            "#F8FAFC" if income > 0 else MUTED,
            f"{transactions} transactions",
        )

    spacer(14)

    # ------------------------------------------------- month at a glance
    if not month_df.empty:
        with st.container(border=True):
            section_header(
                "Month at a glance",
                "How your income was used this month.",
            )

            headline, headline_color = _health_verdict(savings_rate, income)

            if income > 0:
                spent_pct = min(max(expenses / income * 100, 0.0), 100.0)
                saved_pct = max(100.0 - spent_pct, 0.0)
            else:
                spent_pct, saved_pct = 0.0, 0.0

            st.markdown(
                collapse_html(
                    f"""
                    <div style="font-weight:700;color:{headline_color};
                        margin-bottom:12px;">{headline}</div>
                    <div style="display:flex;height:12px;
                        border-radius:999px;overflow:hidden;
                        background:rgba(148,163,184,0.15);">
                        <div style="width:{spent_pct:.1f}%;
                            background:linear-gradient(90deg,
                            #F59E0B,#FBBF24);"></div>
                        <div style="width:{saved_pct:.1f}%;
                            background:linear-gradient(90deg,
                            #10B981,#34D399);"></div>
                    </div>
                    <div style="display:flex;
                        justify-content:space-between;margin-top:10px;
                        font-size:0.8rem;color:{MUTED};">
                        <span><span style="color:#FBBF24;">●</span>
                            Spent {spent_pct:.0f}%</span>
                        <span><span style="color:#34D399;">●</span>
                            Saved {saved_pct:.0f}%</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        spacer(8)

    # ------------------------------------------------------ history
    with st.container(border=True):
        section_header(
            "Monthly history",
            "Your income, expenses and savings, month by month.",
        )

        trend = monthly_trend(df)

        if trend is not None and not trend.empty:
            chart_cols = [
                col for col in ("income", "expenses", "savings")
                if col in trend.columns
            ]

            if chart_cols and len(trend) >= 2:
                chart_df = trend.sort_values("month").copy()
                chart_df["month"] = chart_df["month"].astype(str).map(
                    pretty_month
                )
                st.bar_chart(
                    chart_df.set_index("month")[chart_cols],
                    use_container_width=True,
                )

            history = trend.sort_values("month", ascending=False).copy()
            history["month"] = history["month"].astype(str).map(
                pretty_month
            )

            st.dataframe(
                history.round(2),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "Monthly history will appear after you add transactions."
            )

    spacer(8)

    # ------------------------------------------------------ exports
    with st.container(border=True):
        section_header(
            "Export your data",
            "Download your records as CSV files to open in Excel or "
            "share with your accountant.",
        )

        export_left, export_right = st.columns(2, gap="medium")

        with export_left:
            if not month_df.empty:
                st.download_button(
                    label=f"⬇  {month_label} transactions",
                    data=month_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"spendsense_transactions_{selected_month}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="export_month_csv",
                )
            else:
                st.info(f"No transactions to export for {month_label}.")

        with export_right:
            if df is not None and not df.empty:
                st.download_button(
                    label="⬇  All transactions (every month)",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="spendsense_all_transactions.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="export_all_csv",
                )
            else:
                st.info("No transactions to export yet.")