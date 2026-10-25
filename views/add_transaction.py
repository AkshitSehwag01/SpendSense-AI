from datetime import date

import streamlit as st

from database import MAX_AMOUNT, MAX_DESCRIPTION_LENGTH, add_transaction
from utils.formatting import money


FLASH_KEY = "add_transaction_flash"


def render_add_transaction(expense_categories, income_categories, today):
    """Render the Add Transaction page."""

    st.markdown(
        '<div class="ss-eyebrow">SPENDSENSE AI · NEW ENTRY</div>'
        '<div class="ss-page-title">Add a transaction.</div>'
        '<div class="ss-subtitle">'
        "Record your income and daily expenses in a few seconds."
        "</div>",
        unsafe_allow_html=True,
    )

    # Message saved before the rerun, so it is visible after saving.
    flash = st.session_state.pop(FLASH_KEY, None)

    if flash:
        st.success(flash)

    with st.container(border=True):

        # Type and category stay outside the form so the category
        # list updates immediately when the type changes.
        transaction_type = st.radio(
            "Transaction Type",
            ["Expense", "Income"],
            horizontal=True,
            key="transaction_type_selector",
        )

        categories = (
            expense_categories
            if transaction_type == "Expense"
            else income_categories
        )

        category = st.selectbox(
            "Category",
            categories,
            key=f"category_{transaction_type}",
        )

        placeholder = (
            "Example: Groceries"
            if transaction_type == "Expense"
            else "Example: Monthly salary"
        )

        with st.form("transaction_form", clear_on_submit=False):

            amount_col, date_col = st.columns(2, gap="medium")

            with amount_col:
                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.01,
                    max_value=float(MAX_AMOUNT),
                    value=None,
                    step=100.0,
                    format="%.2f",
                    placeholder="Enter amount",
                )

            with date_col:
                transaction_date = st.date_input(
                    "Transaction Date",
                    value=today,
                    min_value=date(2000, 1, 1),
                    max_value=today,
                )

            description = st.text_input(
                "Description (optional)",
                placeholder=placeholder,
                max_chars=MAX_DESCRIPTION_LENGTH,
            )

            submitted = st.form_submit_button(
                f"Save {transaction_type}",
                use_container_width=True,
            )

    if not submitted:
        return

    if amount is None:
        st.error("Please enter an amount before saving.")
        return

    try:
        add_transaction(
            transaction_type=transaction_type,
            amount=float(amount),
            category=category,
            description=description.strip(),
            transaction_date=transaction_date.isoformat(),
        )

    except (ValueError, TypeError) as error:
        st.error(str(error))
        return

    except Exception:
        st.error(
            "The transaction could not be saved. "
            "Please try again in a moment."
        )
        return

    # Rerun so the sidebar, dashboard, and reports use the new data.
    st.session_state[FLASH_KEY] = (
        f"{transaction_type} of {money(amount)} saved "
        f"under {category}."
    )
    st.rerun()