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
                use_container_width=True,
            )

        if month_df.empty:
            st.info(
                f"No transactions recorded for "
                f"{pretty_month(selected_month)}."
            )
            return

        recent = month_df.sort_values(
            ["transaction_date", "id"],
            ascending=False,
        ).head(5)

        display = recent[
            [
                "transaction_date",
                "transaction_type",
                "category",
                "description",
                "amount",
            ]
        ].copy()

        display["transaction_date"] = pd.to_datetime(
            display["transaction_date"],
            errors="coerce",
        ).dt.strftime("%d %b")

        display["amount"] = display.apply(
            lambda row: (
                "+" if row["transaction_type"] == "Income" else "−"
            )
            + money(row["amount"]),
            axis=1,
        )

        display = display.rename(
            columns={
                "transaction_date": "Date",
                "transaction_type": "Type",
                "category": "Category",
                "description": "Description",
                "amount": "Amount",
            }
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=240,
            column_config={
                "Date": st.column_config.TextColumn(width="small"),
                "Type": st.column_config.TextColumn(width="small"),
                "Category": st.column_config.TextColumn(width="medium"),
                "Description": st.column_config.TextColumn(width="large"),
                "Amount": st.column_config.TextColumn(width="medium"),
            },
        )