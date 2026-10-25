import html

import pandas as pd
import streamlit as st

from database import MAX_AMOUNT, delete_budget, get_budgets, save_budget


# -----------------------------
# Settings
# -----------------------------

GREEN = "#34D399"
RED = "#FB7185"
AMBER = "#FBBF24"
BLUE = "#60A5FA"
MUTED = "#94A3B8"

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


def _pill(text, color):
    return (
        f'<span style="padding:3px 9px;border-radius:999px;'
        f"font-size:0.68rem;font-weight:800;letter-spacing:0.05em;"
        f"color:{color};background:{color}22;"
        f'border:1px solid {color}55;">{text}</span>'
    )


def _stat_card(icon, label, value, color, note):
    with st.container(border=True):
        st.caption(f"{icon} {label}")
        st.markdown(
            _html(
                f"""
                <div style="font-size:clamp(1.15rem,1.6vw,1.5rem);
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

        for category, amount in previous.items():
            save_budget(month, category, float(amount))
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

    {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
    }.get(kind, st.info)(message)


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

        budget_df = calculate_budget_status(month_df, budgets)

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

    with st.container(border=True):
        st.markdown(
            _html(
                f"""
                <div style="display:flex;justify-content:space-between;
                    align-items:center;gap:8px;">
                    <span style="font-weight:800;color:#F1F5F9;
                        font-size:1rem;">{html.escape(name)}</span>
                    {_pill(label, color)}
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


# -----------------------------
# Public page function
# -----------------------------

def render_budget_planner(
    selected_month,
    expense_categories,
    month_df,
    calculate_budget_status,
    money,
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
        )

    if budget_df is not None and not budget_df.empty:
        _spacer(8)
        _render_budget_cards(budget_df, selected_month, money)

    _render_unbudgeted(budgets, spent_by_category, money)