"""Budget usage, category utilization, and savings what-if projections."""

from dataclasses import dataclass

import pandas as pd


BUDGET_WARNING_PERCENT = 80
DISCRETIONARY_CATEGORIES = ("food", "entertainment", "shopping")
WHAT_IF_ANNUAL_RETURN = 0.11


def _safe_float(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return default if number != number else number


def spent_by_category(month_df):
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


def calculate_budget_status(month_df, budgets):
    """Calculate spending and budget usage for each budgeted category."""

    columns = [
        "Category",
        "Budget (₹)",
        "Spent (₹)",
        "Remaining (₹)",
        "Used (%)",
    ]

    if not budgets:
        return pd.DataFrame(columns=columns)

    # Total expenses per category, calculated once (case-insensitive).
    spent_by_category = {}

    if month_df is not None and not month_df.empty:
        expenses = month_df.loc[month_df["transaction_type"] == "Expense"]

        if not expenses.empty:
            spent_by_category = (
                expenses.groupby(
                    expenses["category"].astype(str).str.casefold()
                )["amount"]
                .sum()
                .to_dict()
            )

    rows = []

    for category, limit in budgets.items():
        limit = float(limit)
        spent = float(spent_by_category.get(category.casefold(), 0.0))

        if limit > 0:
            used = spent / limit * 100
        else:
            used = 100.0 if spent > 0 else 0.0

        rows.append({
            "Category": category,
            "Budget (₹)": round(limit, 2),
            "Spent (₹)": round(spent, 2),
            "Remaining (₹)": round(limit - spent, 2),
            "Used (%)": round(used, 2),
        })

    return pd.DataFrame(rows, columns=columns)

def total_budget(budgets):
    """Sum of budget limits, ignoring values that are not numbers."""

    return sum(_safe_float(value) for value in (budgets or {}).values())


@dataclass(frozen=True)
class BudgetTotals:
    total_limit: float
    spent: float
    remaining: float
    used_percent: float
    unbudgeted: float


def summarize_budgets(budget_df, month_df=None):
    """Totals across budgeted categories, plus spending outside them."""

    total_limit = float(budget_df["Budget (₹)"].sum())
    spent = float(budget_df["Spent (₹)"].sum())
    unbudgeted = 0.0
    if month_df is not None and not month_df.empty:
        all_expenses = float(
            month_df.loc[
                month_df["transaction_type"] == "Expense", "amount"
            ].sum()
        )
        unbudgeted = max(all_expenses - spent, 0.0)
    return BudgetTotals(
        total_limit=total_limit,
        spent=spent,
        remaining=total_limit - spent,
        used_percent=spent / total_limit * 100 if total_limit > 0 else 0.0,
        unbudgeted=unbudgeted,
    )


def budget_status_level(used_percent, near_percent=BUDGET_WARNING_PERCENT):
    """'over' at 100%+, 'near' at ``near_percent``+, otherwise 'ok'."""

    if used_percent >= 100:
        return "over"
    if used_percent >= near_percent:
        return "near"
    return "ok"


def count_status_levels(budget_df, near_percent=BUDGET_WARNING_PERCENT):
    counts = {"over": 0, "near": 0, "ok": 0}
    for used in budget_df["Used (%)"]:
        counts[budget_status_level(_safe_float(used), near_percent)] += 1
    return counts


def unbudgeted_spending(budgets, spent_by_category):
    """Positive spending in categories without a budget (lower-case keys)."""

    budgeted = {name.casefold() for name in budgets}
    return {
        name: amount
        for name, amount in spent_by_category.items()
        if name not in budgeted and amount > 0
    }


def discretionary_spending(spent_by_category):
    return sum(
        max(float(spent_by_category.get(category, 0.0)), 0.0)
        for category in DISCRETIONARY_CATEGORIES
    )


def project_monthly_savings(
    monthly_savings,
    months,
    annual_return=WHAT_IF_ANNUAL_RETURN,
):
    monthly_rate = annual_return / 12

    if monthly_rate == 0:
        return monthly_savings * months

    return monthly_savings * (
        ((1 + monthly_rate) ** months - 1) / monthly_rate
    )


def what_if_projection(spent_by_category, reduction_percent, years=(1, 3, 5)):
    """Monthly savings from cutting discretionary spend, and their growth."""

    monthly_savings = (
        discretionary_spending(spent_by_category) * reduction_percent / 100
    )
    return {
        "monthly_savings": monthly_savings,
        "projections": {
            year: project_monthly_savings(monthly_savings, months=year * 12)
            for year in years
        },
        "monthly_curve": [
            project_monthly_savings(monthly_savings, month)
            for month in range(max(years) * 12 + 1)
        ],
    }
