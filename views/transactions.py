import math

import pandas as pd
import streamlit as st

from components.metric_cards import (
    collapse_html as _html,
    go_to as _go_to,
    spacer as _spacer,
    stat_card as _stat_card,
)

from database import delete_transaction
from utils.formatting import money as _money


# -----------------------------
# Settings
# -----------------------------

GREEN = "#34D399"
RED = "#FB7185"
BLUE = "#60A5FA"
MUTED = "#94A3B8"

FLASH_KEY = "transactions_flash"

SORT_OPTIONS = {
    "Newest first": (["transaction_date", "id"], False),
    "Oldest first": (["transaction_date", "id"], True),
    "Highest amount": (["amount", "id"], False),
    "Lowest amount": (["amount", "id"], True),
}

FILTER_DEFAULTS = {
    "txn_search": "",
    "txn_type": "All",
    "txn_categories": [],
    "txn_period": "All time",
    "txn_sort": "Newest first",
}


# -----------------------------
# Small helpers
# -----------------------------

def _html(text):
    """Collapse indentation so Markdown never treats HTML as code."""
    return " ".join(line.strip() for line in text.splitlines())


def _go_to(page):
    """Button callback: switch the sidebar to another page."""
    st.session_state["nav_page"] = page


def _spacer(height=16):
    st.markdown(
        f"<div style='height:{height}px'></div>",
        unsafe_allow_html=True,
    )


def _stat_card(icon, label, value, color, note):
    with st.container(border=True):
        st.caption(f"{icon} {label}")
        st.markdown(
            _html(
                f"""
                <div style="font-size:clamp(1.25rem,1.8vw,1.7rem);
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


def _month_label(month):
    if month == "All time":
        return "All time"

    return pd.Period(month, "M").strftime("%B %Y")


def _signed_amount(transaction_type, amount):
    sign = "+" if transaction_type == "Income" else "−"
    return f"{sign}{_money(amount)}"


# -----------------------------
# Callbacks (run before the page reruns)
# -----------------------------

def _reset_filters():
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def _delete_selected():
    transaction_id = st.session_state.get("txn_delete_select")

    if not st.session_state.get("txn_delete_confirm"):
        st.session_state[FLASH_KEY] = (
            "warning",
            "Please tick the confirmation box before deleting.",
        )
        return

    if transaction_id is None:
        return

    try:
        deleted = delete_transaction(int(transaction_id))
    except Exception:
        st.session_state[FLASH_KEY] = (
            "error",
            "The transaction could not be deleted. Please try again.",
        )
        return

    st.session_state["txn_delete_confirm"] = False

    if deleted:
        st.session_state[FLASH_KEY] = (
            "success",
            "Transaction deleted successfully.",
        )
    else:
        st.session_state[FLASH_KEY] = (
            "warning",
            "That transaction no longer exists.",
        )


# -----------------------------
# Data helpers
# -----------------------------

def _apply_filters(df, search, type_filter, categories, period):
    result = df

    term = search.strip()

    if term:
        # regex=False so characters like ( or + are treated as text.
        mask = result["description"].str.contains(
            term, case=False, na=False, regex=False
        ) | result["category"].str.contains(
            term, case=False, na=False, regex=False
        )
        result = result[mask]

    if type_filter != "All":
        result = result[result["transaction_type"] == type_filter]

    if categories:
        result = result[result["category"].isin(categories)]

    if period != "All time":
        months = result["transaction_date"].dt.strftime("%Y-%m")
        result = result[months == period]

    return result


def _build_display_table(data):
    return pd.DataFrame({
        "Date": data["transaction_date"].dt.strftime("%d %b %Y"),
        "Type": data["transaction_type"].map({
            "Income": "🟢 Income",
            "Expense": "🔴 Expense",
        }),
        "Category": data["category"],
        "Description": data["description"].replace("", "—"),
        "Amount": [
            _signed_amount(kind, amount)
            for kind, amount in zip(
                data["transaction_type"], data["amount"]
            )
        ],
    })


def _delete_label(row):
    description = str(row["description"]).strip() or "No description"

    if len(description) > 40:
        description = description[:37] + "..."

    return (
        f"{row['transaction_date']:%d %b %Y} · {row['category']} · "
        f"{_signed_amount(row['transaction_type'], row['amount'])} · "
        f"{description} (#{int(row['id'])})"
    )


# -----------------------------
# Page sections
# -----------------------------

def _render_header():
    st.markdown(
        '<div class="ss-eyebrow">SPENDSENSE AI · HISTORY</div>'
        '<div class="ss-page-title">Every rupee, accounted for.</div>'
        '<div class="ss-subtitle">'
        "Search, filter, and review your complete financial history."
        "</div>",
        unsafe_allow_html=True,
    )


def _render_empty_state():
    with st.container(border=True):
        text_col, button_col = st.columns([3, 1], gap="large")

        with text_col:
            st.markdown("**Your history starts here.**")
            st.caption(
                "Add your first income or expense and it will appear "
                "in this timeline."
            )

        with button_col:
            st.button(
                "➕ Add transaction",
                key="txn_empty_add",
                on_click=_go_to,
                args=("Add Transaction",),
                use_container_width=True,
            )


def _render_filters(df):
    month_options = ["All time"] + sorted(
        df["transaction_date"].dt.strftime("%Y-%m").unique().tolist(),
        reverse=True,
    )

    category_options = sorted(df["category"].unique().tolist())

    # Drop saved selections that no longer exist (e.g. after a delete).
    saved = st.session_state.get("txn_categories", [])
    st.session_state["txn_categories"] = [
        item for item in saved if item in category_options
    ]

    if st.session_state.get("txn_period", "All time") not in month_options:
        st.session_state["txn_period"] = "All time"

    with st.container(border=True):
        top_left, top_right = st.columns([2, 1], gap="medium")

        with top_left:
            search = st.text_input(
                "Search",
                placeholder="Search by description or category",
                key="txn_search",
            )

        with top_right:
            type_filter = st.radio(
                "Type",
                ["All", "Income", "Expense"],
                horizontal=True,
                key="txn_type",
            )

        col_a, col_b, col_c, col_d = st.columns(
            [2, 1.2, 1.2, 0.8], gap="medium"
        )

        with col_a:
            categories = st.multiselect(
                "Categories",
                category_options,
                placeholder="All categories",
                key="txn_categories",
            )

        with col_b:
            period = st.selectbox(
                "Period",
                month_options,
                format_func=_month_label,
                key="txn_period",
            )

        with col_c:
            sort_choice = st.selectbox(
                "Sort by",
                list(SORT_OPTIONS),
                key="txn_sort",
            )

        with col_d:
            _spacer(28)
            st.button(
                "Clear",
                key="txn_clear",
                on_click=_reset_filters,
                use_container_width=True,
            )

    return search, type_filter, categories, period, sort_choice


def _render_summary(filtered):
    income = float(
        filtered.loc[filtered["transaction_type"] == "Income", "amount"].sum()
    )
    expenses = float(
        filtered.loc[filtered["transaction_type"] == "Expense", "amount"].sum()
    )
    net = income - expenses

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        _stat_card(
            "🧾", "TRANSACTIONS", str(len(filtered)),
            "#F1F5F9", "Matching your filters",
        )

    with c2:
        _stat_card(
            "💰", "INCOME", _money(income), GREEN, "Money received",
        )

    with c3:
        _stat_card(
            "💳", "EXPENSES", _money(expenses), RED, "Money spent",
        )

    with c4:
        _stat_card(
            "📈", "NET", _money(net),
            GREEN if net >= 0 else RED,
            "Surplus" if net >= 0 else "Deficit",
        )


def _render_table(filtered, total_count):
    with st.container(border=True):
        left, right = st.columns([3, 1], gap="medium")

        with left:
            st.markdown(
                _html(
                    f"""
                    <div class="ss-section-title">Transaction Timeline</div>
                    <div class="ss-muted">
                        Showing {len(filtered):,} of {total_count:,}
                        transactions
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        with right:
            export = filtered[
                [
                    "transaction_date",
                    "transaction_type",
                    "category",
                    "description",
                    "amount",
                ]
            ].copy()

            export["transaction_date"] = export[
                "transaction_date"
            ].dt.strftime("%Y-%m-%d")

            st.download_button(
                "⬇ Export CSV",
                data=export.to_csv(index=False).encode("utf-8-sig"),
                file_name="spendsense_transactions.csv",
                mime="text/csv",
                key="txn_export",
                use_container_width=True,
            )

        _spacer(6)

        st.dataframe(
            _build_display_table(filtered),
            use_container_width=True,
            hide_index=True,
            height=min(420, 38 + 35 * len(filtered)),
            column_config={
                "Date": st.column_config.TextColumn(width="small"),
                "Type": st.column_config.TextColumn(width="small"),
                "Category": st.column_config.TextColumn(width="medium"),
                "Description": st.column_config.TextColumn(width="large"),
                "Amount": st.column_config.TextColumn(width="medium"),
            },
        )


def _render_manage(filtered):
    with st.expander("🗑️ Manage transactions"):
        st.caption(
            "Choose a transaction from your current results to delete it. "
            "This cannot be undone."
        )

        labels = {
            int(row["id"]): _delete_label(row)
            for _, row in filtered.iterrows()
        }

        st.selectbox(
            "Transaction",
            list(labels),
            format_func=labels.get,
            key="txn_delete_select",
        )

        st.checkbox(
            "I confirm that I want to delete this transaction.",
            key="txn_delete_confirm",
        )

        st.button(
            "Delete transaction",
            key="txn_delete_button",
            on_click=_delete_selected,
        )


# -----------------------------
# Public page function
# -----------------------------

def render_transactions(df):
    """Render transaction history, search, filters, and deletion."""

    _render_header()

    flash = st.session_state.pop(FLASH_KEY, None)

    if flash:
        kind, message = flash
        {
            "success": st.success,
            "warning": st.warning,
            "error": st.error,
        }.get(kind, st.info)(message)

    if df is None or df.empty:
        _render_empty_state()
        return

    search, type_filter, categories, period, sort_choice = _render_filters(df)

    filtered = _apply_filters(df, search, type_filter, categories, period)

    sort_columns, ascending = SORT_OPTIONS[sort_choice]
    filtered = filtered.sort_values(sort_columns, ascending=ascending)

    _spacer(8)
    _render_summary(filtered)
    _spacer(8)

    if filtered.empty:
        with st.container(border=True):
            st.markdown("**No transactions match your filters.**")
            st.caption("Try a different search or clear the filters.")
        return

    _render_table(filtered, len(df))
    _render_manage(filtered)