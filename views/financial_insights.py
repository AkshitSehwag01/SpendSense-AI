from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from analytics import category_breakdown
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
    progress_bar_html,
    safe_float,
    section_header,
    spacer,
    stat_card,
)
from database import get_budgets


# Colour palette used for category rows (cycles if there are more categories)
CATEGORY_COLORS = [
    "#34D399",  # green
    "#38BDF8",  # sky
    "#A78BFA",  # violet
    "#FBBF24",  # amber
    "#F472B6",  # pink
    "#2DD4BF",  # teal
    "#FB923C",  # orange
    "#94A3B8",  # slate
]

STATUS_STYLES = {
    "over": ("OVER BUDGET", RED),
    "near": ("NEAR LIMIT", AMBER),
    "ok": ("ON TRACK", GREEN),
}


def _budget_state(used_percent, remaining, money):
    """Return (status key, message) for one budget row."""
    if used_percent >= 100:
        return "over", f"Over by {money(abs(remaining))}. Time to rein this in."
    if used_percent >= 80:
        return "near", f"Only {money(max(remaining, 0))} left. Spend carefully."
    return "ok", f"{money(max(remaining, 0))} still available."


def _render_monthly_insights(
    selected_month,
    month_df,
    generate_insights,
    show_insights,
    calculate_budget_status,
    money,
):
    """Render financial insights, spending analysis, and budget alerts."""

    month_label = pretty_month(selected_month)

    # ---------------------------------------------------------------- header
    page_header(
        "SPENDSENSE AI · SMART ANALYSIS",
        "Your financial intelligence.",
        "Understand your spending patterns, spot budget risks early, "
        "and discover where you can save more.",
        "ANALYSIS PERIOD",
        month_label,
        "Spending patterns and budget health",
    )
    spacer(14)

    # ------------------------------------------------------------------ data
    budgets = get_budgets(selected_month)
    total_budget = sum(safe_float(value) for value in budgets.values())

    breakdown = category_breakdown(month_df)
    has_spending = breakdown is not None and not breakdown.empty

    if not has_spending:
        with st.container(border=True):
            text_col, button_col = st.columns([3, 1], gap="large")

            with text_col:
                st.markdown(f"**No expenses recorded for {month_label}.**")
                st.caption(
                    "Add a few expenses to unlock your spending "
                    "breakdown and personalised insights."
                )

            with button_col:
                st.button(
                    "➕ Add transaction",
                    key="insights_empty_add",
                    on_click=go_to,
                    args=("Add Transaction",),
                    use_container_width=True,
                )

        spacer(8)

    # --------------------------------------------------------- summary cards
    if has_spending:
        breakdown = breakdown.sort_values("amount", ascending=False)
        total_spent = sum(safe_float(v) for v in breakdown["amount"])
        top_row = breakdown.iloc[0]
        top_name = escape(str(top_row["category"]))
        top_share = safe_float(top_row["percentage"])

        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            stat_card(
                "💳",
                "TOTAL SPENT",
                money(total_spent),
                "#F8FAFC",
                f"Across {len(breakdown)} categories",
            )

        with c2:
            stat_card(
                "🔥",
                "BIGGEST CATEGORY",
                top_name,
                GREEN,
                f"{top_share:.1f}% of your spending",
                size="1.35rem",
            )

        with c3:
            if total_budget > 0:
                left = total_budget - total_spent
                stat_card(
                    "🎯",
                    "BUDGET LEFT" if left >= 0 else "OVER TOTAL BUDGET",
                    money(abs(left)),
                    BLUE if left >= 0 else RED,
                    f"of {money(total_budget)} planned",
                )
            else:
                stat_card(
                    "🎯",
                    "BUDGET",
                    "Not set",
                    MUTED,
                    "Add budgets to track limits",
                )

        spacer(14)

    # -------------------------------------------------------- smart insights
    with st.container(border=True):
        section_header(
            "Smart insights",
            "Personalised observations based on your activity this month.",
        )

        insights = generate_insights(
            month_df,
            budget_amount=total_budget,
            budgets=budgets,
        )
        show_insights(insights)

    spacer(8)

    # ---------------------------------------------------- where money goes
    if has_spending:
        with st.container(border=True):
            section_header(
                "Where your money goes",
                "Your expenses ranked by category, biggest first.",
            )

            for position, (_, row) in enumerate(breakdown.iterrows()):
                category = escape(str(row["category"]))
                amount = safe_float(row["amount"])
                percentage = safe_float(row["percentage"])
                color = CATEGORY_COLORS[position % len(CATEGORY_COLORS)]

                st.markdown(
                    collapse_html(
                        f"""
                        <div style="margin-bottom:14px;">
                            <div style="display:flex;
                                justify-content:space-between;
                                align-items:center;gap:12px;">
                                <div style="display:flex;
                                    align-items:center;gap:10px;
                                    min-width:0;">
                                    <span style="width:10px;height:10px;
                                        border-radius:50%;
                                        background:{color};
                                        flex-shrink:0;"></span>
                                    <span style="font-weight:700;
                                        color:#F1F5F9;">{category}</span>
                                </div>
                                <div style="text-align:right;
                                    white-space:nowrap;">
                                    <span style="font-size:1rem;
                                        font-weight:800;
                                        color:#F8FAFC;">
                                        {money(amount)}</span>
                                    <span style="font-size:0.8rem;
                                        color:{MUTED};margin-left:10px;">
                                        {percentage:.1f}%</span>
                                </div>
                            </div>
                            {progress_bar_html(percentage, color)}
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

        spacer(8)

    # ---------------------------------------------------- budget health
    with st.container(border=True):
        section_header(
            "Budget health monitor",
            "Category limits at a glance, riskiest first.",
        )

        if not budgets:
            st.info(
                f"No budgets set for {month_label}. "
                "Create category budgets to unlock limit tracking "
                "and early warnings."
            )
            st.button(
                "Go to Budget Planner",
                key="insights_budget_link",
                on_click=go_to,
                args=("Budget Planner",),
            )
            return

        budget_df = calculate_budget_status(month_df, budgets)

        if budget_df is None or budget_df.empty:
            st.info("No budget status is available for this month.")
            return

        budget_df = budget_df.sort_values("Used (%)", ascending=False)

        states = []
        for _, row in budget_df.iterrows():
            used = safe_float(row["Used (%)"])
            remaining = safe_float(row["Remaining (₹)"])
            key, message = _budget_state(used, remaining, money)
            states.append((row, used, key, message))

        over_count = sum(1 for s in states if s[2] == "over")
        near_count = sum(1 for s in states if s[2] == "near")
        ok_count = sum(1 for s in states if s[2] == "ok")

        s1, s2, s3 = st.columns(3, gap="medium")

        with s1:
            stat_card(
                "✅", "ON TRACK", str(ok_count),
                GREEN, "Within healthy limits", size="1.35rem",
            )
        with s2:
            stat_card(
                "⚠️", "NEAR LIMIT", str(near_count),
                AMBER, "80% or more used", size="1.35rem",
            )
        with s3:
            stat_card(
                "🚨", "OVER BUDGET", str(over_count),
                RED, "Limit exceeded", size="1.35rem",
            )

        spacer(8)

        for row, used, key, message in states:
            label, color = STATUS_STYLES[key]
            category = escape(str(row["Category"]))
            spent = safe_float(row["Spent (₹)"])
            budget = safe_float(row["Budget (₹)"])

            st.markdown(
                collapse_html(
                    f"""
                    <div style="margin-bottom:16px;">
                        <div style="display:flex;
                            justify-content:space-between;
                            align-items:flex-start;gap:12px;">
                            <div>
                                <div style="font-weight:700;
                                    color:#F1F5F9;">{category}</div>
                                <div style="font-size:0.8rem;
                                    color:{MUTED};margin-top:2px;">
                                    {money(spent)} of {money(budget)}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="color:{color};
                                    font-size:0.7rem;font-weight:800;
                                    letter-spacing:0.06em;">{label}</div>
                                <div style="color:#F8FAFC;
                                    font-size:1.1rem;
                                    font-weight:800;">{used:.1f}%</div>
                            </div>
                        </div>
                        {progress_bar_html(used, color)}
                        <div style="font-size:0.8rem;color:{MUTED};
                            margin-top:8px;">{message}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )


def _render_tax_tracker(financial_year_df, today, money):
    financial_year_start = date(
        today.year if today.month >= 4 else today.year - 1,
        4,
        1,
    )
    financial_year_end = date(financial_year_start.year + 1, 3, 31)
    section_80c_limit = 150_000
    required_columns = {
        "transaction_date",
        "transaction_type",
        "category",
        "amount",
    }

    if (
        financial_year_df is None
        or financial_year_df.empty
        or not required_columns.issubset(financial_year_df.columns)
    ):
        fy_transactions = pd.DataFrame(columns=required_columns)
    else:
        fy_transactions = financial_year_df.copy()
        dates = pd.to_datetime(
            fy_transactions["transaction_date"],
            errors="coerce",
        ).dt.date
        in_financial_year = dates.between(
            financial_year_start,
            financial_year_end,
            inclusive="both",
        )
        fy_transactions = fy_transactions.loc[in_financial_year]

    expenses = fy_transactions.loc[
        fy_transactions["transaction_type"].eq("Expense")
    ]
    investment_total = sum(
        safe_float(amount)
        for amount in expenses.loc[
            expenses["category"].eq("Investment"), "amount"
        ]
    )
    healthcare_total = sum(
        safe_float(amount)
        for amount in expenses.loc[
            expenses["category"].eq("Healthcare"), "amount"
        ]
    )
    section_80c_total = min(investment_total, section_80c_limit)
    remaining_headroom = max(section_80c_limit - section_80c_total, 0)
    goal_text = (
        f"Tax-Saving Goal: {money(section_80c_total)} / "
        "₹1,50,000 completed"
    )

    section_header(
        "Indian Tax & 80C Savings Tracker",
        f"Financial year {financial_year_start.year}-"
        f"{financial_year_end.year} "
        f"({financial_year_start:%d %b %Y} to "
        f"{financial_year_end:%d %b %Y})",
    )
    st.progress(section_80c_total / section_80c_limit)
    st.caption(goal_text)

    investment_col, healthcare_col = st.columns(2, gap="medium")
    with investment_col:
        st.metric(
            "80C amount counted toward goal",
            money(section_80c_total),
            help=(
                "Based on Expense transactions in the Investment category; "
                "only eligible investments qualify for an actual deduction."
            ),
        )
        if investment_total > section_80c_limit:
            st.caption(
                f"Investment-category total: {money(investment_total)}; "
                "the 80C tracker is capped at ₹1,50,000."
            )
        if remaining_headroom:
            st.info(
                f"{money(remaining_headroom)} remaining to reach the "
                f"₹1,50,000 80C limit before "
                f"{financial_year_end:%d %B %Y}."
            )
        else:
            st.success("The ₹1,50,000 80C limit has been reached.")

    with healthcare_col:
        st.metric(
            "Healthcare expenses (potential 80D)",
            money(healthcare_total),
            help=(
                "Based on Expense transactions in the Healthcare category. "
                "This is not a verified insurance-premium deduction."
            ),
        )

    st.caption(
        "Estimates are based on transaction categories, not verified tax "
        "eligibility or supporting documents. Actual 80C/80D deductions "
        "depend on applicable tax rules and personal circumstances."
    )


def render_financial_insights(
    selected_month,
    month_df,
    generate_insights,
    show_insights,
    calculate_budget_status,
    money,
    financial_year_df,
    today,
):
    spending_tab, tax_tab = st.tabs(
        ["Financial insights", "Indian Tax & 80C Savings Tracker"]
    )

    with spending_tab:
        _render_monthly_insights(
            selected_month=selected_month,
            month_df=month_df,
            generate_insights=generate_insights,
            show_insights=show_insights,
            calculate_budget_status=calculate_budget_status,
            money=money,
        )

    with tax_tab:
        _render_tax_tracker(financial_year_df, today, money)