import pandas as pd

from database import KNOWN_CATEGORIES


# -----------------------------
# Settings
# -----------------------------

LOW_SAVINGS_RATE = 10          # below this: warning
HEALTHY_SAVINGS_RATE = 20      # at or above this: success
CONCENTRATION_THRESHOLD = 50   # one category above this % of spending
BUDGET_WARNING_PERCENT = 80
OUTLIER_MULTIPLIER = 3
MIN_EXPENSES_FOR_OUTLIER = 5

_LEVEL_ORDER = {"danger": 0, "warning": 1, "info": 2, "success": 3}

_CANONICAL_CATEGORY = {
    name.casefold(): name for name in KNOWN_CATEGORIES
}


# -----------------------------
# Small helpers
# -----------------------------

def _insight(title, message, level):
    return {"title": title, "message": message, "level": level}


def _money(value):
    return f"₹{float(value):,.2f}"


def _canonical(name):
    """Tidy whitespace and apply the app's canonical capitalization."""
    name = " ".join(str(name).split())

    if not name or name.lower() == "nan":
        return "Uncategorized"

    return _CANONICAL_CATEGORY.get(name.casefold(), name.title())


def _clean(df):
    """Return a cleaned copy containing only valid transactions."""

    data = df.copy()

    data["transaction_type"] = (
        data["transaction_type"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.title()
    )

    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")

    if "category" in data.columns:
        data["category"] = data["category"].map(_canonical)
    else:
        data["category"] = "Uncategorized"

    if "description" not in data.columns:
        data["description"] = ""

    data["description"] = data["description"].fillna("").astype(str)

    return data[
        data["transaction_type"].isin(["Income", "Expense"])
        & data["amount"].notna()
        & (data["amount"] > 0)
    ].copy()


# -----------------------------
# Insight rules
# -----------------------------

def _savings_insights(income, total_expenses, savings):

    if income > 0:
        savings_rate = savings / income * 100

        if savings < 0:
            return [_insight(
                "Expenses exceed your income",
                f"You recorded {_money(total_expenses)} in expenses "
                f"against {_money(income)} in income. Your expenses "
                f"exceed your income by {_money(abs(savings))}. "
                "Review your spending and identify expenses you can "
                "reduce.",
                "danger",
            )]

        if savings_rate < LOW_SAVINGS_RATE:
            return [_insight(
                "Low savings rate",
                f"Your current savings rate is {savings_rate:.1f}%. "
                "Consider reviewing non-essential spending and setting "
                "a realistic monthly savings target.",
                "warning",
            )]

        if savings_rate < HEALTHY_SAVINGS_RATE:
            return [_insight(
                "Opportunity to increase savings",
                f"You are retaining {savings_rate:.1f}% of your "
                "recorded income after expenses. Review your spending "
                "to find opportunities to save more.",
                "info",
            )]

        return [_insight(
            "Healthy savings rate",
            f"You are retaining {savings_rate:.1f}% of your recorded "
            "income after expenses. Keep tracking your finances and "
            "maintaining this habit.",
            "success",
        )]

    if total_expenses > 0:
        return [_insight(
            "Income information needed",
            "You have recorded expenses but no positive income for "
            "this period. Add your income to calculate your savings "
            "rate accurately.",
            "info",
        )]

    return []


def _category_insights(expenses_df, total_expenses):

    if expenses_df.empty or total_expenses <= 0:
        return []

    totals = (
        expenses_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    top_category = totals.index[0]
    top_amount = float(totals.iloc[0])
    percentage = top_amount / total_expenses * 100

    results = [_insight(
        "Largest spending category",
        f"{top_category} is your largest recorded expense category "
        f"at {_money(top_amount)}, representing {percentage:.1f}% of "
        "your total expenses.",
        "info",
    )]

    # A single category is always 100%, so only warn when there is
    # more than one category to compare against.
    if percentage >= CONCENTRATION_THRESHOLD and len(totals) > 1:
        results.append(_insight(
            "High spending concentration",
            f"{top_category} accounts for more than half of your "
            "recorded expenses. Check whether this reflects essential "
            "costs or spending that you could reduce.",
            "warning",
        ))

    return results


def _large_transaction_insights(expenses_df):

    if len(expenses_df) < MIN_EXPENSES_FOR_OUTLIER:
        return []

    # The median is not pulled up by the outlier itself.
    typical = float(expenses_df["amount"].median())

    largest = expenses_df.iloc[expenses_df["amount"].to_numpy().argmax()]
    largest_amount = float(largest["amount"])

    if typical <= 0 or largest_amount <= typical * OUTLIER_MULTIPLIER:
        return []

    description = str(largest["description"]).strip()
    label = f" ({description})" if description else ""

    return [_insight(
        "Large transaction detected",
        f"Your largest recorded expense is {_money(largest_amount)}"
        f"{label}, which is more than {OUTLIER_MULTIPLIER} times your "
        f"typical expense of {_money(typical)}. Check whether this "
        "transaction was expected.",
        "warning",
    )]


def _total_budget_insight(total_expenses, budget_amount):
    """Fallback: compare all expenses with one total budget."""

    try:
        budget_amount = float(budget_amount)
    except (TypeError, ValueError):
        return []

    if not pd.notna(budget_amount) or budget_amount <= 0:
        return []

    usage = total_expenses / budget_amount * 100
    remaining = budget_amount - total_expenses

    if usage >= 100:
        return [_insight(
            "Budget exceeded",
            f"You recorded {_money(total_expenses)} in expenses "
            f"against a total budget of {_money(budget_amount)}. "
            f"You exceeded your budget by {_money(abs(remaining))}.",
            "danger",
        )]

    if usage >= BUDGET_WARNING_PERCENT:
        return [_insight(
            "Budget running low",
            f"You have used {usage:.1f}% of your total budget. "
            f"Only {_money(remaining)} remains. "
            "Monitor your upcoming expenses.",
            "warning",
        )]

    return [_insight(
        "Budget on track",
        f"You have used {usage:.1f}% of your total budget, "
        f"with {_money(remaining)} remaining.",
        "success",
    )]


def _category_budget_insights(expenses_df, budgets):
    """Compare spending with budgets, for budgeted categories only."""

    limits = {}

    for category, limit in budgets.items():
        try:
            limit = float(limit)
        except (TypeError, ValueError):
            continue

        if limit > 0:
            limits[_canonical(category)] = limit

    if not limits:
        return []

    spent_by_category = expenses_df.groupby("category")["amount"].sum()

    over, near = [], []
    budgeted_spent = 0.0

    for category, limit in limits.items():
        spent = float(spent_by_category.get(category, 0.0))
        budgeted_spent += spent
        usage = spent / limit * 100

        if usage >= 100:
            over.append((category, spent - limit))
        elif usage >= BUDGET_WARNING_PERCENT:
            near.append((category, usage))

    total_limit = sum(limits.values())
    total_usage = budgeted_spent / total_limit * 100
    remaining = total_limit - budgeted_spent

    results = []

    # Overall status, based only on the categories you budgeted.
    if total_usage >= 100:
        results.append(_insight(
            "Budget exceeded",
            f"You spent {_money(budgeted_spent)} in budgeted "
            f"categories against a combined budget of "
            f"{_money(total_limit)}, exceeding it by "
            f"{_money(abs(remaining))}.",
            "danger",
        ))
    elif total_usage >= BUDGET_WARNING_PERCENT:
        results.append(_insight(
            "Budget running low",
            f"You have used {total_usage:.1f}% of your combined "
            f"category budgets. Only {_money(remaining)} remains. "
            "Monitor your upcoming expenses.",
            "warning",
        ))
    else:
        results.append(_insight(
            "Budget on track",
            f"You have used {total_usage:.1f}% of your combined "
            f"category budgets, with {_money(remaining)} remaining.",
            "success",
        ))

    if over:
        details = ", ".join(
            f"{name} (over by {_money(amount)})" for name, amount in over
        )
        results.append(_insight(
            "Category budgets exceeded",
            f"These categories are over budget: {details}.",
            "warning",
        ))

    if near:
        details = ", ".join(
            f"{name} ({usage:.0f}% used)" for name, usage in near
        )
        results.append(_insight(
            "Categories near their limit",
            f"These categories are close to their budget: {details}.",
            "warning",
        ))

    unbudgeted = float(expenses_df["amount"].sum()) - budgeted_spent

    if unbudgeted > 0:
        results.append(_insight(
            "Spending outside your budgets",
            f"{_money(unbudgeted)} was spent in categories without a "
            "budget. Add budgets for them to track these expenses.",
            "info",
        ))

    return results


# -----------------------------
# Public function
# -----------------------------

def generate_insights(df, budget_amount=0, budgets=None):
    """
    Analyze financial transactions and generate actionable insights.

    Parameters
    ----------
    df : pandas.DataFrame
        Transactions with transaction_type, amount, and optionally
        category and description.

    budget_amount : float
        Total budget for the period. Only used when `budgets` is not
        given (kept for backward compatibility).

    budgets : dict, optional
        Category budgets as {category: amount}, e.g. from
        get_budgets(month). Preferred over budget_amount because it
        only compares budgeted categories.

    Returns
    -------
    list[dict]
        Insights with title, message, and level, most serious first.
    """

    if df is None or not isinstance(df, pd.DataFrame):
        return [_insight(
            "Unable to analyze transactions",
            "Transaction data is unavailable. "
            "Please refresh the application and try again.",
            "warning",
        )]

    if df.empty:
        return [_insight(
            "Start tracking your money",
            "Add income and expenses to receive "
            "personalized financial insights.",
            "info",
        )]

    if not {"transaction_type", "amount"}.issubset(df.columns):
        return [_insight(
            "Transaction data needs attention",
            "Some required transaction fields are missing. "
            "Please check your transaction data.",
            "warning",
        )]

    data = _clean(df)

    if data.empty:
        return [_insight(
            "No valid transactions found",
            "Add valid income or expense transactions "
            "to generate financial insights.",
            "info",
        )]

    income = float(
        data.loc[data["transaction_type"] == "Income", "amount"].sum()
    )
    expenses_df = data.loc[data["transaction_type"] == "Expense"].copy()
    total_expenses = float(expenses_df["amount"].sum())
    savings = income - total_expenses

    insights = []
    insights += _savings_insights(income, total_expenses, savings)
    insights += _category_insights(expenses_df, total_expenses)
    insights += _large_transaction_insights(expenses_df)

    if budgets:
        insights += _category_budget_insights(expenses_df, budgets)
    else:
        insights += _total_budget_insight(total_expenses, budget_amount)

    if not insights:
        insights.append(_insight(
            "Keep tracking your finances",
            "Continue recording transactions to build "
            "a clearer picture of your financial habits.",
            "info",
        ))

    # Most serious first. The sort is stable, so insights of the same
    # level keep their original order.
    insights.sort(key=lambda item: _LEVEL_ORDER.get(item["level"], 99))

    return insights