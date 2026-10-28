import html

import pandas as pd
import plotly.express as px
import streamlit as st

from database import MAX_AMOUNT, delete_budget, get_budgets, save_budget

from database import (
    MAX_AMOUNT,
    delete_budget,
    get_budgets,
    save_budget,
    save_budgets_batch,  # Add this import
)
from utils.formatting import render_badge
from components.charts import apply_chart_theme


# -----------------------------
# Settings
# -----------------------------

GREEN = "var(--success)"
RED = "var(--danger)"
AMBER = "var(--warning)"
BLUE = "var(--info)"
MUTED = "var(--text-muted)"

FLASH_KEY = "budget_flash"
CATEGORY_KEY = "budget_category"


# -----------------------------
# Small helpers
# -----------------------------

def _html(text):
    """Collapse indentation so Markdown never treats HTML as code."""
    return " ".join(line.strip() for line in text.splitlines())


def _spacer(height=16):
    st.markdown(
        f"<div style='height:{height}px'></div>",
        unsafe_allow_html=True,
    )


def _month_label(month):
    return pd.Period(month, "M").strftime("%B %Y")


def _previous_month(month):
    return str(pd.Period(month, "M") - 1)


def _amount_key(month, category):
    return f"budget_amount::{month}::{category}"


def _status(used):
    if used >= 100:
        return "OVER BUDGET", RED
    if used >= 80:
        return "NEAR LIMIT", AMBER
    return "ON TRACK", GREEN


def _stat_card(icon, label, value, color, note):
    with st.container(border=True):
        st.caption(f"{icon} {label}")
        st.markdown(
            _html(
                f"""
                <div class="ss-money" style="font-size:clamp(1.15rem,1.6vw,1.5rem);
                    font-weight:800;color:{color};
                    letter-spacing:-0.04em;overflow-wrap:anywhere;">
                    {value}
                </div>
                <div style="color:{MUTED};font-size:0.78rem;
                    margin-top:8px;">{note}</div>
                """
            ),
            unsafe_allow_html=True,
        )


def _spent_by_category(month_df):
    """Expense totals per category, keyed by lower-case name."""

    if month_df is None or month_df.empty:
        return {}

    expenses = month_df.loc[month_df["transaction_type"] == "Expense"]

    if expenses.empty:
        return {}

    return (
        expenses.groupby(expenses["category"].astype(str).str.casefold())[
            "amount"
        ]
        .sum()
        .to_dict()
    )


# -----------------------------
# Callbacks (run before the page reruns)
# -----------------------------

def _flash(kind, message):
    st.session_state[FLASH_KEY] = (kind, message)


def _save_budget(month, money):
    category = st.session_state.get(CATEGORY_KEY)
    amount = st.session_state.get(_amount_key(month, category))

    try:
        amount = float(amount or 0.0)
    except (TypeError, ValueError):
        amount = 0.0

    if amount <= 0:
        _flash(
            "warning",
            "Enter an amount above ₹0, or use Remove to delete "
            "a budget.",
        )
        return

    try:
        save_budget(month, category, amount)
    except (ValueError, TypeError) as error:
        _flash("error", str(error))
        return
    except Exception:
        _flash("error", "The budget could not be saved. Please try again.")
        return

    _flash("success", f"Budget for {category} saved: {money(amount)}.")


def _edit_budget(category):
    st.session_state[CATEGORY_KEY] = category


def _remove_budget(month, category):
    try:
        removed = delete_budget(month, category)
    except Exception:
        _flash("error", "The budget could not be removed. Please try again.")
        return

    st.session_state[_amount_key(month, category)] = 0.0

    if removed:
        _flash("success", f"Budget for {category} removed.")
    else:
        _flash("warning", "That budget no longer exists.")


def _copy_previous(month, previous_month):
    try:
        previous = get_budgets(previous_month)

        if not previous:
            _flash("warning", "Last month has no budgets to copy.")
            return

        # Batch insert all budgets in 1 transaction instead of N round-trips
        save_budgets_batch(month, previous, user_id=None)

        for category, amount in previous.items():
            st.session_state[_amount_key(month, category)] = float(amount)

    except Exception:
        _flash("error", "Budgets could not be copied. Please try again.")
        return

    _flash(
        "success",
        f"Copied {len(previous)} budget(s) from "
        f"{_month_label(previous_month)}.",
    )


# -----------------------------
# Page sections
# -----------------------------

def _render_header(selected_month):
    st.markdown(
        '<div class="ss-eyebrow">SPENDSENSE AI · BUDGETS</div>'
        '<div class="ss-page-title">Plan with purpose.</div>'
        '<div class="ss-subtitle">'
        "Set a limit for each category and stay in control "
        "of your spending."
        "</div>"
        f'<span class="ss-pill">📅 {_month_label(selected_month)}</span>',
        unsafe_allow_html=True,
    )


def _render_flash():
    flash = st.session_state.pop(FLASH_KEY, None)

    if not flash:
        return

    kind, message = flash

    if kind == "success":
        st.toast(message, icon="💸")
    elif kind == "warning":
        st.warning(message)
    elif kind == "error":
        st.error(message)
    else:
        st.error("An unexpected budget update status occurred.")


def _render_set_budget(
    selected_month,
    category_options,
    budgets,
    spent_by_category,
    money,
):
    with st.container(border=True):
        st.markdown(
            '<div class="ss-section-title">Set a budget</div>'
            '<div class="ss-muted" style="margin-bottom:12px;">'
            "Choose a category and set its monthly limit."
            "</div>",
            unsafe_allow_html=True,
        )

        category = st.selectbox(
            "Expense category",
            category_options,
            key=CATEGORY_KEY,
        )

        spent = float(spent_by_category.get(category.casefold(), 0.0))
        st.caption(f"Spent so far in {category}: {money(spent)}")

        # Start from the saved budget; widget state keeps it afterwards.
        amount_key = _amount_key(selected_month, category)

        if amount_key not in st.session_state:
            st.session_state[amount_key] = float(budgets.get(category, 0.0))

        with st.form("budget_form"):
            st.number_input(
                "Monthly budget (₹)",
                min_value=0.0,
                max_value=float(MAX_AMOUNT),
                step=500.0,
                format="%.2f",
                key=amount_key,
            )

            st.form_submit_button(
                "Save budget",
                on_click=_save_budget,
                args=(selected_month, money),
                use_container_width=True,
            )


def _render_overview(
    selected_month,
    budgets,
    month_df,
    calculate_budget_status,
    money,
    user_id=None,
):
    with st.container(border=True):
        st.markdown(
            '<div class="ss-section-title">Month overview</div>'
            '<div class="ss-muted" style="margin-bottom:12px;">'
            "How your budgeted categories are performing."
            "</div>",
            unsafe_allow_html=True,
        )

        if not budgets:
            st.markdown(f"**No budgets for {_month_label(selected_month)} yet.**")
            st.caption("Set your first category budget to start tracking.")

            previous_month = _previous_month(selected_month)

            try:
                has_previous = bool(get_budgets(previous_month))
            except Exception:
                has_previous = False

            if has_previous:
                st.button(
                    f"Copy {_month_label(previous_month)} budgets",
                    key="budget_copy_previous",
                    on_click=_copy_previous,
                    args=(selected_month, previous_month),
                )

            return None

        budget_df = calculate_budget_status(
            month_df,
            budgets,
            user_id=user_id,
            selected_month=selected_month,
        )

        total_limit = float(budget_df["Budget (₹)"].sum())
        spent = float(budget_df["Spent (₹)"].sum())
        remaining = total_limit - spent
        used = spent / total_limit * 100 if total_limit > 0 else 0.0

        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            _stat_card(
                "🎯", "TOTAL BUDGET", money(total_limit), BLUE,
                f"{len(budget_df)} categories",
            )

        with c2:
            _stat_card(
                "💸", "SPENT IN BUDGETS", money(spent),
                RED if remaining < 0 else "#F1F5F9",
                f"{used:.0f}% of budget used",
            )

        with c3:
            _stat_card(
                "🛟",
                "REMAINING" if remaining >= 0 else "OVER BY",
                money(abs(remaining)),
                GREEN if remaining >= 0 else RED,
                "Still available" if remaining >= 0 else "Above your limits",
            )

        st.progress(min(max(used / 100, 0.0), 1.0))

        return budget_df


def _render_budget_card(row, selected_month, money):
    name = str(row["Category"])
    used = float(row["Used (%)"])
    left = float(row["Remaining (₹)"])
    label, color = _status(used)
    status_badge = render_badge(
        label,
        bg_color=f"{color}22",
        text_color=color,
    )

    with st.container(border=True):
        st.markdown(
            _html(
                f"""
                <div style="display:flex;justify-content:space-between;
                    align-items:center;gap:8px;">
                    <span style="font-weight:800;color:#F1F5F9;
                        font-size:1rem;">{html.escape(name)}</span>
                    {status_badge}
                </div>
                <div style="margin-top:10px;">
                    <span style="font-size:1.35rem;font-weight:800;
                        color:#F8FAFC;letter-spacing:-0.03em;">
                        {money(row['Spent (₹)'])}</span>
                    <span style="color:{MUTED};font-size:0.82rem;">
                        of {money(row['Budget (₹)'])}</span>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        st.progress(min(max(used / 100, 0.0), 1.0))

        note = (
            f"Over by {money(abs(left))}"
            if left < 0
            else f"{money(left)} remaining"
        )

        st.markdown(
            f'<div style="color:{color};font-size:0.78rem;'
            f'font-weight:700;margin-top:-6px;margin-bottom:8px;">'
            f"{note} · {used:.0f}% used</div>",
            unsafe_allow_html=True,
        )

        edit_col, remove_col = st.columns(2, gap="small")

        with edit_col:
            st.button(
                "✏️ Edit",
                key=f"budget_edit::{name}",
                on_click=_edit_budget,
                args=(name,),
                use_container_width=True,
            )

        with remove_col:
            st.button(
                "🗑️ Remove",
                key=f"budget_remove::{name}",
                on_click=_remove_budget,
                args=(selected_month, name),
                use_container_width=True,
            )


def _render_budget_cards(budget_df, selected_month, money):
    st.markdown(
        '<div class="ss-section-title">Category budgets</div>'
        '<div class="ss-muted" style="margin-bottom:12px;">'
        "Sorted by how much of each budget you have used."
        "</div>",
        unsafe_allow_html=True,
    )

    ranked = budget_df.sort_values("Used (%)", ascending=False)
    rows = [row for _, row in ranked.iterrows()]

    for start in range(0, len(rows), 2):
        columns = st.columns(2, gap="medium")

        for column, row in zip(columns, rows[start:start + 2]):
            with column:
                _render_budget_card(row, selected_month, money)


def _render_unbudgeted(budgets, spent_by_category, money):
    budgeted = {name.casefold() for name in budgets}

    unbudgeted = {
        name: amount
        for name, amount in spent_by_category.items()
        if name not in budgeted and amount > 0
    }

    if not unbudgeted:
        return

    _spacer(8)

    with st.container(border=True):
        total = sum(unbudgeted.values())

        st.markdown(
            '<div class="ss-section-title">Spending without a budget</div>'
            f'<div class="ss-muted" style="margin-bottom:10px;">'
            f"{money(total)} was spent in categories with no limit. "
            "Pick one in “Set a budget” to track it."
            "</div>",
            unsafe_allow_html=True,
        )

        for name, amount in sorted(
            unbudgeted.items(), key=lambda item: item[1], reverse=True
        ):
            st.markdown(
                _html(
                    f"""
                    <div style="display:flex;justify-content:space-between;
                        padding:6px 0;border-bottom:1px solid #1F2E44;">
                        <span style="color:#CBD5E1;">
                            {html.escape(name.title())}</span>
                        <span style="color:{AMBER};font-weight:700;">
                            {money(amount)}</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )


def _project_monthly_savings(monthly_savings, months, annual_return=0.11):
    monthly_rate = annual_return / 12

    if monthly_rate == 0:
        return monthly_savings * months

    return monthly_savings * (
        ((1 + monthly_rate) ** months - 1) / monthly_rate
    )


def _render_what_if_simulator(spent_by_category, money):
    discretionary_categories = ("food", "entertainment", "shopping")
    discretionary_spending = sum(
        max(float(spent_by_category.get(category, 0.0)), 0.0)
        for category in discretionary_categories
    )

    with st.expander("What-If Scenario Simulator"):
        reduction_percent = st.slider(
            "If I reduce spending by X% across discretionary categories "
            "(Food, Entertainment, Shopping)",
            min_value=0,
            max_value=100,
            value=10,
            step=5,
            format="%d%%",
            key="budget_what_if_reduction",
        )

        monthly_savings = discretionary_spending * reduction_percent / 100
        st.metric("Potential monthly savings", money(monthly_savings))

        st.caption(
            "Assumes these monthly savings are invested at the end of each "
            "month and earn an 11% annual return, compounded monthly."
        )

        annual_projections = {
            years: _project_monthly_savings(
                monthly_savings,
                months=years * 12,
            )
            for years in (1, 3, 5)
        }
        projection_cols = st.columns(3, gap="medium")
        for column, years in zip(projection_cols, (1, 3, 5)):
            with column:
                st.metric(
                    f"Projected value in {years} year"
                    f"{'s' if years != 1 else ''}",
                    money(annual_projections[years]),
                )

        monthly_points = list(range(61))
        projection_df = pd.DataFrame(
            {
                "Month": monthly_points,
                "Projected value": [
                    _project_monthly_savings(monthly_savings, month)
                    for month in monthly_points
                ],
            }
        )
        projection_df["Formatted value"] = projection_df[
            "Projected value"
        ].map(money)
        figure = px.line(
            projection_df,
            x="Month",
            y="Projected value",
            custom_data=["Formatted value"],
            markers=False,
            title="Projected savings growth over 5 years",
        )
        apply_chart_theme(
            figure,
            height=450,
            yaxis_title="Projected value (₹)",
            xaxis_title="Months",
            margin=dict(l=12, r=12, t=48, b=12),
            hovermode="x",
        )
        figure.update_traces(
            hovertemplate=(
                "Month %{x}<br>Projected value %{customdata[0]}"
                "<extra></extra>"
            )
        )
        figure.update_yaxes(tickprefix="₹", tickformat=",.0f")
        st.plotly_chart(
            figure,
            config={"displayModeBar": False},
            alt="Projected value of monthly savings grows over five years.",
        )


# -----------------------------
# Public page function
# -----------------------------

def render_budget_planner(
    selected_month,
    expense_categories,
    month_df,
    calculate_budget_status,
    money,
    user_id=None,
):
    """Render the monthly budget planner and performance."""

    _render_header(selected_month)
    _spacer(8)
    _render_flash()

    budgets = get_budgets(selected_month)
    spent_by_category = _spent_by_category(month_df)

    # Include custom categories that already have a budget.
    category_options = list(
        dict.fromkeys(list(expense_categories) + list(budgets))
    )

    left_col, right_col = st.columns([1, 1.5], gap="large")

    with left_col:
        _render_set_budget(
            selected_month,
            category_options,
            budgets,
            spent_by_category,
            money,
        )

    with right_col:
        budget_df = _render_overview(
            selected_month,
            budgets,
            month_df,
            calculate_budget_status,
            money,
            user_id=user_id,
        )

    if budget_df is not None and not budget_df.empty:
        _spacer(8)
        _render_budget_cards(budget_df, selected_month, money)

    _render_unbudgeted(budgets, spent_by_category, money)
    _render_what_if_simulator(spent_by_category, money)