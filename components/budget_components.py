import html

import streamlit as st

from components.metric_cards import (
    AMBER,
    BLUE,
    GREEN,
    MUTED,
    RED,
    collapse_html,
    go_to,
    section_header,
    stat_card,
)


def render_budget_progress(
    month_df,
    budgets,
    calculate_budget_status,
    money,
    user_id=None,
    selected_month=None,
):
    """Budget totals plus the five most-used category budgets."""

    with st.container(border=True):
        section_header(
            "Budget Progress",
            "Category limits for the selected month",
        )

        if not budgets:
            st.info("You haven't set budgets for this month yet.")
            st.button(
                "Go to Budget Planner",
                key="dashboard_budget_link",
                on_click=go_to,
                args=("Budget Planner",),
            )
            return

        budget_df = calculate_budget_status(
            month_df,
            budgets,
            user_id=user_id,
            selected_month=selected_month,
        )

        if budget_df.empty:
            st.info("No budget status is available for this month.")
            return

        total_limit = float(budget_df["Budget (₹)"].sum())
        budgeted_spent = float(budget_df["Spent (₹)"].sum())
        remaining = total_limit - budgeted_spent

        all_expenses = float(
            month_df.loc[
                month_df["transaction_type"] == "Expense", "amount"
            ].sum()
        )
        unbudgeted = max(all_expenses - budgeted_spent, 0.0)

        b1, b2 = st.columns(2, gap="medium")

        with b1:
            stat_card(
                "🎯",
                "TOTAL BUDGET",
                money(total_limit),
                BLUE,
                "Planned spending limit",
                size="1.35rem",
            )

        with b2:
            stat_card(
                "💸",
                "SPENT IN BUDGETS",
                money(budgeted_spent),
                RED if remaining < 0 else GREEN,
                (
                    f"Over by {money(abs(remaining))}"
                    if remaining < 0
                    else f"{money(remaining)} remaining"
                ),
                size="1.35rem",
            )

        if unbudgeted > 0:
            st.caption(
                f"{money(unbudgeted)} was spent in categories "
                "without a budget."
            )

        ranked = budget_df.sort_values("Used (%)", ascending=False)

        for _, row in ranked.head(5).iterrows():
            used = float(row["Used (%)"])
            left = float(row["Remaining (₹)"])
            name = html.escape(str(row["Category"]))

            if used >= 100:
                color = RED
                status = f"Over budget by {money(abs(left))}"
            elif used >= 80:
                color = AMBER
                status = f"{money(max(left, 0))} remaining · {used:.0f}% used"
            else:
                color = GREEN
                status = f"{money(max(left, 0))} remaining · {used:.0f}% used"

            st.markdown(
                collapse_html(
                    f"""
                    <div style="display:flex;justify-content:space-between;
                        align-items:baseline;gap:8px;margin-top:6px;">
                        <span style="font-weight:700;color:#F1F5F9;">
                            {name}
                        </span>
                        <span style="color:{MUTED};font-size:0.8rem;">
                            {money(row['Spent (₹)'])} /
                            {money(row['Budget (₹)'])}
                        </span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            st.progress(min(max(used / 100, 0.0), 1.0))

            st.markdown(
                collapse_html(
                    f"""
                    <div style="color:{color};font-size:0.75rem;
                        font-weight:700;margin-top:-8px;
                        margin-bottom:8px;">{status}</div>
                    """
                ),
                unsafe_allow_html=True,
            )

        if len(ranked) > 5:
            st.button(
                f"View all {len(ranked)} budgets",
                key="dashboard_all_budgets",
                on_click=go_to,
                args=("Budget Planner",),
            )