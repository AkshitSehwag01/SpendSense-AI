import pandas as pd
import streamlit as st

from components.metric_cards import (
    go_to,
    pretty_month,
    section_header,
    spacer,
)


def render_recent_transactions(month_df, selected_month, money):
    """The five latest transactions of the selected month."""

    with st.container(border=True):
        title_col, action_col = st.columns([3, 1])

        with title_col:
            section_header(
                "Recent Transactions",
                "Your latest five transactions this month",
            )

        with action_col:
            spacer(5)
            st.button(
                "View all",
                key="dashboard_view_all",
                on_click=go_to,
                args=("Transactions",),
                width="stretch",
            )

        if month_df.empty:
            st.info(
                f"No transactions recorded for {pretty_month(selected_month)}.",
                icon=":material/receipt_long:",
            )
            return

        transaction_filter = st.segmented_control(
            "Transaction type",
            ["All", "Income", "Expense"],
            default="All",
            key="dashboard_transaction_filter",
            label_visibility="collapsed",
        )
        if transaction_filter != "All":
            month_df = month_df.loc[
                month_df["transaction_type"] == transaction_filter
            ]
        if month_df.empty:
            st.caption("No transactions match this filter.")
            return

        recent = month_df.sort_values(
            ["transaction_date", "id"],
            ascending=False,
        ).head(5)

        category_icons = {
            "Food": "🍽️",
            "Transport": "🚗",
            "Shopping": "🛍️",
            "Bills": "🧾",
            "Salary": "💼",
            "Investment": "📈",
        }
        rows = []
        for _, row in recent.iterrows():
            transaction_type = str(row["transaction_type"])
            amount_class = "ss-income" if transaction_type == "Income" else "ss-expense"
            sign = "+" if transaction_type == "Income" else "−"
            category = str(row["category"])
            icon = category_icons.get(category, "●")
            date_label = pd.to_datetime(
                row["transaction_date"], errors="coerce"
            ).strftime("%d %b")
            rows.append(
                f"""
                <div class="ss-transaction-row">
                    <span class="ss-category-icon">{icon}</span>
                    <div class="ss-transaction-main">
                        <strong>{row['description']}</strong>
                        <span>{category} · {date_label}</span>
                    </div>
                    <strong class="{amount_class} ss-money">
                        {sign}{money(row['amount'])}
                    </strong>
                </div>
                """
            )
        st.markdown("".join(rows), unsafe_allow_html=True)