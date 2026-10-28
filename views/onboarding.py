import logging
import math

import streamlit as st

from auth import get_user_context
from database import save_budget
from utils.constants import EXPENSE_CATEGORIES


logger = logging.getLogger(__name__)

_DEFAULT_BUDGET_CATEGORIES = ["Food", "Rent", "Utilities", "Shopping"]


@st.dialog("Welcome to SpendSense AI")
def show_onboarding_dialog(selected_month):
    """Guide a new user through income and initial monthly budgets."""

    context = get_user_context()
    st.progress(
        0.5 if context.get("onboarding_step", 1) == 1 else 1.0,
        text=(
            "Step 1 of 2 · Monthly income target"
            if context.get("onboarding_step", 1) == 1
            else "Step 2 of 2 · Category budgets"
        ),
    )

    if context.get("onboarding_step", 1) == 1:
        st.subheader("Set your monthly income target")
        st.caption(
            "This helps SpendSense personalize your budget overview. "
            "You can change it later."
        )
        monthly_income = st.number_input(
            "Expected monthly income (₹)",
            min_value=0.0,
            value=float(st.session_state.get("onboarding_income_input", 0.0)),
            step=1000.0,
            format="%.2f",
            key="onboarding_income_input",
        )

        if st.button("Next", type="primary", width="stretch"):
            if not math.isfinite(monthly_income) or monthly_income < 0:
                st.error("Enter a valid, non-negative monthly income.")
                return

            context["monthly_income_target"] = monthly_income
            context["onboarding_step"] = 2
            st.rerun()

        return

    st.subheader("Choose your first category budgets")
    st.caption(
        f"Set monthly limits for {selected_month}. You can edit these "
        "budgets at any time."
    )
    categories = st.multiselect(
        "Categories to budget",
        options=EXPENSE_CATEGORIES,
        default=[
            category
            for category in _DEFAULT_BUDGET_CATEGORIES
            if category in EXPENSE_CATEGORIES
        ],
        key="onboarding_categories",
    )

    amounts = {}
    for category in categories:
        amounts[category] = st.number_input(
            f"{category} monthly limit (₹)",
            min_value=0.0,
            value=0.0,
            step=500.0,
            format="%.2f",
            key=f"onboarding_budget_{category}",
        )

    if st.button("Finish Setup", type="primary", width="stretch"):
        invalid_categories = [
            category
            for category in categories
            if category not in EXPENSE_CATEGORIES
        ]
        invalid_amounts = [
            category
            for category, amount in amounts.items()
            if not math.isfinite(amount) or amount < 0
        ]
        if invalid_categories or invalid_amounts:
            st.error("Choose valid categories and non-negative budget amounts.")
            return

        try:
            for category in categories:
                save_budget(selected_month, category, amounts[category])
        except Exception:
            logger.exception(
                "Could not save onboarding budgets for month %s",
                selected_month,
            )
            st.error(
                "We couldn't save your initial budgets. Please try again."
            )
            return

        context["has_completed_onboarding"] = True
        st.rerun()
