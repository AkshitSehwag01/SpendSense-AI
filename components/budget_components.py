import html

import streamlit as st

from domain.budgets import budget_status_level, summarize_budgets
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

        totals = summarize_budgets(budget_df, month_df)
        total_limit = totals.total_limit
        budgeted_spent = totals.spent
        remaining = totals.remaining
        unbudgeted = totals.unbudgeted

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
            category_icon = {
                "Food": "🍽️",
                "Transport": "🚗",
                "Shopping": "🛍️",
                "Bills": "🧾",
            }.get(str(row["Category"]), "●")

            level = budget_status_level(used, near_percent=75)
            if level == "over":
                status_class = "danger"
                status = f"Over budget by {money(abs(left))}"
            elif level == "near":
                status_class = "warning"
                status = f"{money(max(left, 0))} remaining · {used:.0f}% used"
            else:
                status_class = "ok"
                status = f"{money(max(left, 0))} remaining · {used:.0f}% used"

            status_parts = status.split(" · ", 1)
            st.markdown(
                collapse_html(
                    f"""
                    <div class="ss-budget-row">
                      <div class="ss-budget-row-header">
                        <span class="ss-budget-category">
                            {category_icon} {name}
                        </span>
                        <span class="ss-budget-amount">
                            {money(row['Spent (₹)'])} /
                            {money(row['Budget (₹)'])}
                        </span>
                      </div>
                      <div class="ss-budget-track">
                        <div class="ss-budget-fill ss-budget-fill--{status_class}"
                            style="width:{min(max(used, 0.0), 100.0):.1f}%;"></div>
                      </div>
                      <div class="ss-budget-caption ss-budget-caption--{status_class}">
                        <span>{status_parts[0]}</span>
                        <span>{status_parts[1] if len(status_parts) > 1 else ""}</span>
                      </div>
                    </div>
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