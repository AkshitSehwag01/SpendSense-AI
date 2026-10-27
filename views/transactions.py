from datetime import date

import pandas as pd
import streamlit as st

from components.metric_cards import (
    GREEN,
    RED,
    collapse_html,
    go_to,
    spacer,
    stat_card,
)
from database import (
    MAX_AMOUNT,
    MAX_DESCRIPTION_LENGTH,
    delete_transaction,
    update_transaction,
)
from utils.constants import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from utils.dates import today_local
from utils.formatting import money, render_badge, signed_money


# -----------------------------
# Settings
# -----------------------------

FLASH_KEY = "transactions_flash"

# The edit / delete pick-lists show at most this many matches.
MAX_MANAGE_OPTIONS = 500

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

def _month_label(month):
    if month == "All time":
        return "All time"

    return pd.Period(month, "M").strftime("%B %Y")


def _edit_key(transaction_id, field, *extra):
    """Session-state key for one field of one transaction's edit form."""
    parts = ["txn_edit", str(int(transaction_id)), field, *map(str, extra)]
    return "::".join(parts)


def _clear_edit_state(transaction_id):
    """Forget the edit form's values so it reloads from saved data."""

    prefix = f"txn_edit::{int(transaction_id)}::"

    for key in [k for k in st.session_state.keys() if k.startswith(prefix)]:
        st.session_state.pop(key, None)


def _flash(kind, message):
    st.session_state[FLASH_KEY] = (kind, message)


# -----------------------------
# Callbacks (run before the page reruns)
# -----------------------------

def _reset_filters():
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def _delete_selected():
    transaction_id = st.session_state.get("txn_delete_select")

    if not st.session_state.get("txn_delete_confirm"):
        _flash("warning", "Please tick the confirmation box before deleting.")
        return

    if transaction_id is None:
        return

    try:
        deleted = delete_transaction(int(transaction_id))
    except Exception:
        _flash(
            "error",
            "The transaction could not be deleted. Please try again.",
        )
        return

    st.session_state["txn_delete_confirm"] = False
    _clear_edit_state(transaction_id)

    if deleted:
        _flash("success", "Transaction deleted successfully.")
    else:
        _flash("warning", "That transaction no longer exists.")


def _save_edit(transaction_id):
    state = st.session_state

    kind = state.get(_edit_key(transaction_id, "type"))
    category = state.get(_edit_key(transaction_id, "category", kind))
    amount = state.get(_edit_key(transaction_id, "amount"))
    day = state.get(_edit_key(transaction_id, "date"))
    description = state.get(_edit_key(transaction_id, "description"), "")

    if not kind or not category or amount is None or day is None:
        _flash("error", "Some details are missing. Please check the form.")
        return

    try:
        updated = update_transaction(
            transaction_id,
            kind,
            float(amount),
            category,
            description or "",
            day.isoformat(),
        )
    except (ValueError, TypeError) as error:
        _flash("error", str(error))
        return
    except Exception:
        _flash(
            "error",
            "The changes could not be saved. Please try again.",
        )
        return

    if not updated:
        _flash("warning", "That transaction no longer exists.")
        return

    _clear_edit_state(transaction_id)
    _flash(
        "success",
        f"Transaction updated: {kind} of {money(amount)} "
        f"under {category}.",
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
            signed_money(kind, amount)
            for kind, amount in zip(
                data["transaction_type"], data["amount"]
            )
        ],
    })


def _option_labels(data):
    """{transaction id: readable label} for the edit / delete lists."""

    labels = {}

    for transaction_id, when, category, kind, amount, description in zip(
        data["id"],
        data["transaction_date"],
        data["category"],
        data["transaction_type"],
        data["amount"],
        data["description"],
    ):
        text = str(description).strip() or "No description"

        if len(text) > 40:
            text = text[:37] + "..."

        labels[int(transaction_id)] = (
            f"{when:%d %b %Y} · {category} · "
            f"{signed_money(kind, amount)} · {text} "
            f"(#{int(transaction_id)})"
        )

    return labels


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
        st.error("An unexpected transaction update status occurred.")


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
                on_click=go_to,
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
            spacer(28)
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
        stat_card(
            "🧾", "TRANSACTIONS", str(len(filtered)),
            "#F1F5F9", "Matching your filters",
        )

    with c2:
        stat_card("💰", "INCOME", money(income), GREEN, "Money received")

    with c3:
        stat_card("💳", "EXPENSES", money(expenses), RED, "Money spent")

    with c4:
        stat_card(
            "📈", "NET", money(net),
            GREEN if net >= 0 else RED,
            "Surplus" if net >= 0 else "Deficit",
        )


def _render_compact_cards(filtered):
    for row in filtered.itertuples(index=False):
        with st.container(border=True):
            date_col, amount_col = st.columns([1, 1], gap="small")
            with date_col:
                st.caption(row.transaction_date.strftime("%d %b %Y"))
            with amount_col:
                st.markdown(
                    f"**{signed_money(row.transaction_type, row.amount)}**"
                )

            st.markdown(
                render_badge(
                    row.category,
                    bg_color="#172554",
                    text_color="#93C5FD",
                ),
                unsafe_allow_html=True,
            )
            description = str(row.description).strip() or "—"
            st.text(description)


def _render_table(filtered, total_count):
    with st.container(border=True):
        left, right = st.columns([3, 1], gap="medium")

        with left:
            st.markdown(
                collapse_html(
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
            compact_view = st.toggle(
                "Compact View",
                value=False,
                key="txn_compact_view",
            )
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

        spacer(6)

        if compact_view:
            _render_compact_cards(filtered)
        else:
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


def _render_edit(filtered, labels):
    st.caption("Fix a mistake without deleting and re-adding the entry.")

    selected = st.selectbox(
        "Transaction to edit",
        list(labels),
        format_func=labels.get,
        key="txn_edit_select",
    )

    match = filtered.loc[filtered["id"] == selected]

    if selected is None or match.empty:
        return

    row = match.iloc[0]
    transaction_id = int(selected)
    original_type = row["transaction_type"]
    original_category = row["category"]

    # Type and category sit outside the form so the category list
    # changes straight away when the type changes.
    type_key = _edit_key(transaction_id, "type")

    if type_key not in st.session_state:
        st.session_state[type_key] = original_type

    kind = st.radio(
        "Type",
        ["Expense", "Income"],
        horizontal=True,
        key=type_key,
    )

    options = list(
        EXPENSE_CATEGORIES if kind == "Expense" else INCOME_CATEGORIES
    )

    if kind == original_type and original_category not in options:
        options.append(original_category)

    category_key = _edit_key(transaction_id, "category", kind)

    if category_key not in st.session_state:
        st.session_state[category_key] = (
            original_category if original_category in options else options[0]
        )

    st.selectbox("Category", options, key=category_key)

    amount_key = _edit_key(transaction_id, "amount")
    date_key = _edit_key(transaction_id, "date")
    description_key = _edit_key(transaction_id, "description")

    today = today_local()
    earliest = date(2000, 1, 1)

    if amount_key not in st.session_state:
        st.session_state[amount_key] = float(row["amount"])

    if date_key not in st.session_state:
        saved_day = row["transaction_date"].date()
        st.session_state[date_key] = min(max(saved_day, earliest), today)

    if description_key not in st.session_state:
        st.session_state[description_key] = str(row["description"])

    with st.form(f"txn_edit_form::{transaction_id}"):
        amount_col, date_col = st.columns(2, gap="medium")

        with amount_col:
            st.number_input(
                "Amount (₹)",
                min_value=0.01,
                max_value=float(MAX_AMOUNT),
                step=100.0,
                format="%.2f",
                key=amount_key,
            )

        with date_col:
            st.date_input(
                "Date",
                min_value=earliest,
                max_value=today,
                key=date_key,
            )

        st.text_input(
            "Description (optional)",
            max_chars=MAX_DESCRIPTION_LENGTH,
            key=description_key,
        )

        st.form_submit_button(
            "Save changes",
            on_click=_save_edit,
            args=(transaction_id,),
            use_container_width=True,
        )


def _render_delete(labels):
    st.caption(
        "Choose a transaction from your current results to delete it. "
        "This cannot be undone."
    )

    st.selectbox(
        "Transaction to delete",
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


def _render_manage(filtered):
    with st.expander("✏️ Edit or delete transactions"):
        shown = filtered.head(MAX_MANAGE_OPTIONS)
        labels = _option_labels(shown)

        if len(filtered) > MAX_MANAGE_OPTIONS:
            st.caption(
                f"Showing the first {MAX_MANAGE_OPTIONS} matches. "
                "Use the filters above to narrow the list."
            )

        edit_tab, delete_tab = st.tabs(["Edit", "Delete"])

        with edit_tab:
            _render_edit(shown, labels)

        with delete_tab:
            _render_delete(labels)


# -----------------------------
# Public page function
# -----------------------------

def render_transactions(df, read_only=False):
    """Render transaction history, search, filters, edit and delete."""

    _render_header()
    _render_flash()

    if df is None or df.empty:
        _render_empty_state()
        return

    search, type_filter, categories, period, sort_choice = _render_filters(df)

    filtered = _apply_filters(df, search, type_filter, categories, period)

    sort_columns, ascending = SORT_OPTIONS[sort_choice]
    filtered = filtered.sort_values(sort_columns, ascending=ascending)

    spacer(8)
    _render_summary(filtered)
    spacer(8)

    if filtered.empty:
        with st.container(border=True):
            st.markdown("**No transactions match your filters.**")
            st.caption("Try a different search or clear the filters.")
        return

    _render_table(filtered, len(df))
    if read_only:
        st.info("Demo transactions are read-only.")
    else:
        _render_manage(filtered)