"""Recurring payments, bills, anomalies, spending trends, and insight rules."""

import math
import re
import statistics
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from domain.transactions import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    KNOWN_CATEGORIES,
    normalize_descriptions,
    prepare_transactions,
    to_datetime,
)


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

# -----------------------------
# Recurring payments and bills
# -----------------------------

def detect_recurring_subscriptions(df, today):
    """Find active monthly expense patterns with similar descriptions/amounts."""

    required = {
        "transaction_type",
        "amount",
        "description",
        "transaction_date",
    }
    if df is None or df.empty or not required.issubset(df.columns):
        return []

    expenses = df.loc[
        df["transaction_type"].astype(str).str.casefold().eq("expense"),
        list(required),
    ].copy()
    if expenses.empty:
        return []

    expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce")
    expenses["transaction_date"] = to_datetime(
        expenses["transaction_date"]
    )
    expenses = expenses.loc[
        expenses["amount"].notna()
        & expenses["amount"].map(math.isfinite)
        & (expenses["amount"] > 0)
        & expenses["transaction_date"].notna()
    ].copy()
    expenses["normalized_description"] = normalize_descriptions(
        expenses["description"]
    )
    expenses = expenses.loc[
        expenses["normalized_description"].ne("")
    ]
    if expenses.empty:
        return []

    active_cutoff = today - timedelta(days=35)
    subscriptions = []

    for description, description_group in expenses.groupby(
        "normalized_description",
        sort=False,
    ):
        amount_clusters = []
        for _, transaction in description_group.sort_values(
            "amount"
        ).iterrows():
            amount = float(transaction["amount"])
            cluster = next(
                (
                    candidate
                    for candidate in amount_clusters
                    if abs(amount - candidate["median"])
                    <= max(candidate["median"] * 0.05, 0.01)
                ),
                None,
            )
            if cluster is None:
                cluster = {"median": amount, "transactions": []}
                amount_clusters.append(cluster)

            cluster["transactions"].append(transaction)
            cluster["median"] = float(
                pd.Series(
                    [item["amount"] for item in cluster["transactions"]]
                ).median()
            )

        for cluster in amount_clusters:
            transactions = pd.DataFrame(cluster["transactions"])
            transactions = transactions.drop_duplicates(
                subset=["transaction_date"]
            ).sort_values("transaction_date")
            dates = transactions["transaction_date"].dt.date.tolist()

            if len(dates) < 2:
                continue

            # Use the latest uninterrupted monthly sequence, so an old
            # cadence does not hide a more recent missed or stopped payment.
            chain_start = 0
            for index in range(1, len(dates)):
                gap_days = (dates[index] - dates[index - 1]).days
                if not 25 <= gap_days <= 35:
                    chain_start = index - 1

            active_payments = dates[chain_start:]
            last_payment = active_payments[-1]
            if (
                len(active_payments) < 2
                or last_payment < active_cutoff
                or last_payment > today
            ):
                continue

            monthly_cost = float(
                transactions.loc[
                    transactions["transaction_date"].dt.date.isin(
                        active_payments
                    ),
                    "amount",
                ].mean()
            )
            subscriptions.append(
                {
                    "description": description,
                    "monthly_cost": round(monthly_cost, 2),
                    "yearly_projection": round(monthly_cost * 12, 2),
                    "last_payment_date": last_payment,
                }
            )

    return sorted(
        subscriptions,
        key=lambda subscription: subscription["yearly_projection"],
        reverse=True,
    )


SUBSCRIPTION_INCOME_SHARE_LIMIT = 0.15


@dataclass(frozen=True)
class SubscriptionSummary:
    count: int
    monthly_cost: float
    yearly_projection: float
    monthly_income_share: float
    next_expected: date
    exceeds_income_share_limit: bool
    descriptions: tuple


def summarize_subscriptions(subscriptions, monthly_income):
    """Totals for detected subscriptions relative to one month's income."""

    if not subscriptions or monthly_income <= 0:
        return None

    monthly_cost = sum(
        subscription["monthly_cost"] for subscription in subscriptions
    )
    yearly_projection = sum(
        subscription["yearly_projection"] for subscription in subscriptions
    )
    return SubscriptionSummary(
        count=len(subscriptions),
        monthly_cost=monthly_cost,
        yearly_projection=yearly_projection,
        monthly_income_share=yearly_projection / monthly_income,
        next_expected=min(
            subscription["last_payment_date"] + timedelta(days=30)
            for subscription in subscriptions
        ),
        exceeds_income_share_limit=(
            yearly_projection > monthly_income * SUBSCRIPTION_INCOME_SHARE_LIMIT
        ),
        descriptions=tuple(
            subscription["description"] for subscription in subscriptions
        ),
    )


_BILL_KEYWORDS = {
    "Electricity": (r"\belectricity\b", r"\belectric bill\b", r"\bpower bill\b"),
    "Broadband": (
        r"\bbroadband\b",
        r"\binternet bill\b",
        r"\bwifi bill\b",
        r"\bfiber\b",
        r"\bfibre\b",
    ),
    "Water": (r"\bwater\b",),
    "FASTag": (
        r"\bfast\s?ag\b",
        r"\bfast\s?tag\b",
        r"\btoll recharge\b",
    ),
    "Rent": (r"\brent\b",),
    "Credit Card": (
        r"\bcredit card\b",
        r"\bcard bill\b",
        r"\bcard payment\b",
    ),
}


def monthly_anniversary(last_date, month_offset):
    month_index = last_date.year * 12 + last_date.month - 1 + month_offset
    year, month = divmod(month_index, 12)
    month += 1
    return date(year, month, min(last_date.day, monthrange(year, month)[1]))


def detect_upcoming_bills(rows, today):
    """Infer recurring utility bills due within three days from transaction rows."""

    history_start = today - timedelta(days=190)
    payments_by_type = {}
    for row in rows:
        try:
            payment_date = date.fromisoformat(str(row["transaction_date"])[:10])
            amount = float(row["amount"])
        except (KeyError, TypeError, ValueError):
            continue
        if (
            str(row.get("transaction_type", "")).casefold() != "expense"
            or not history_start <= payment_date <= today
            or amount <= 0
        ):
            continue

        category = str(row.get("category", "")).casefold().strip()
        description = str(row.get("description", "")).casefold().strip()
        searchable = f"{category} {description}"
        bill_type = next(
            (
                name
                for name, patterns in _BILL_KEYWORDS.items()
                if any(re.search(pattern, searchable) for pattern in patterns)
            ),
            None,
        )
        if bill_type is None:
            continue
        payments_by_type.setdefault(bill_type, []).append(
            (payment_date, amount)
        )

    upcoming = []
    for bill_type, payments in payments_by_type.items():
        monthly_payments = {}
        for payment_date, amount in payments:
            month_key = (payment_date.year, payment_date.month)
            entry = monthly_payments.setdefault(
                month_key,
                {"date": payment_date, "amount": 0.0},
            )
            entry["date"] = max(entry["date"], payment_date)
            entry["amount"] += amount

        monthly = sorted(
            monthly_payments.values(),
            key=lambda payment: payment["date"],
        )
        if len(monthly) < 2:
            continue

        chain_start = len(monthly) - 1
        while chain_start > 0:
            gap = (monthly[chain_start]["date"] - monthly[chain_start - 1]["date"]).days
            if not 20 <= gap <= 40:
                break
            chain_start -= 1
        active_payments = monthly[chain_start:]
        if len(active_payments) < 2:
            continue

        gaps = [
            (current["date"] - previous["date"]).days
            for previous, current in zip(active_payments, active_payments[1:])
        ]
        cadence_days = max(25, min(35, round(statistics.median(gaps))))
        due_date = active_payments[-1]["date"] + timedelta(days=cadence_days)
        if due_date.day <= active_payments[-1]["date"].day:
            due_date = monthly_anniversary(active_payments[-1]["date"], 1)

        days_until_due = (due_date - today).days
        if not 0 <= days_until_due <= 3:
            continue

        upcoming.append(
            {
                "bill_type": bill_type,
                "amount": round(
                    sum(payment["amount"] for payment in active_payments)
                    / len(active_payments),
                    2,
                ),
                "due_date": due_date,
                "days_until_due": days_until_due,
                "last_payment_date": active_payments[-1]["date"],
            }
        )

    return sorted(
        upcoming,
        key=lambda bill: (bill["due_date"], bill["bill_type"]),
    )


# -----------------------------
# Anomalies and trends
# -----------------------------

def detect_spending_anomalies(transactions, selected_month):
    """Flag current-month expenses unusually large for their category."""

    selected_period = pd.Period(selected_month, freq="M")

    if isinstance(transactions, pd.DataFrame):
        data = prepare_transactions(transactions.to_dict("records"))
    else:
        data = prepare_transactions(transactions)
    if data.empty:
        return []

    data["transaction_date"] = to_datetime(data["transaction_date"])
    data["month"] = data["transaction_date"].dt.to_period("M")
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    expenses = data.loc[
        data["transaction_type"].eq("Expense")
        & data["amount"].notna()
        & data["amount"].gt(0)
    ].copy()
    historical = expenses.loc[
        expenses["month"].between(
            selected_period - 6,
            selected_period - 1,
        )
    ]
    current_month = expenses.loc[expenses["month"].eq(selected_period)]
    if historical.empty or current_month.empty:
        return []

    baselines = (
        historical.groupby("category")["amount"]
        .agg(["mean", "std"])
        .to_dict("index")
    )
    baseline_month_counts = historical.groupby("category")["month"].nunique()
    anomalies = []
    for _, transaction in current_month.iterrows():
        baseline = baselines.get(transaction["category"])
        if baseline is None:
            continue

        average = float(baseline["mean"])
        if average <= 0:
            continue
        amount = float(transaction["amount"])
        standard_deviation = baseline["std"]
        z_score = (
            (amount - average) / float(standard_deviation)
            if pd.notna(standard_deviation) and standard_deviation > 0
            else 0.0
        )
        if z_score <= 2.0 and amount <= average * 2.5:
            continue

        anomalies.append(
            {
                "transaction_id": transaction["id"],
                "date": transaction["transaction_date"].date(),
                "category": str(transaction["category"]),
                "description": str(transaction["description"]),
                "amount": amount,
                "avg_amount": average,
                "percentage_above_normal": (amount / average - 1) * 100,
                "baseline_months": int(
                    baseline_month_counts[transaction["category"]]
                ),
            }
        )

    return sorted(
        anomalies,
        key=lambda anomaly: anomaly["percentage_above_normal"],
        reverse=True,
    )


def percent_change(current, previous):
    """Change from ``previous`` relative to its magnitude, or None at zero."""

    if previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def classify_savings_rate(savings_rate, income):
    """Bucket a savings rate: no_income, excellent, healthy, low, negative."""

    if income <= 0:
        return "no_income"
    if savings_rate >= 20:
        return "excellent"
    if savings_rate >= 10:
        return "healthy"
    if savings_rate > 0:
        return "low"
    return "negative"


def income_allocation(income, expenses):
    """Percent of income spent and saved, or None without income."""

    if income <= 0:
        return None
    spent = expenses / income * 100
    return {"spent_percent": spent, "saved_percent": max(100.0 - spent, 0.0)}


# -----------------------------
# Natural-language questions
# -----------------------------

def parse_natural_language_query(query: str, df: pd.DataFrame, today: date) -> dict:
    """Answer common finance questions using rules and the supplied data."""

    def failure(message):
        return {
            "success": False,
            "answer": message,
            "metric_val": None,
            "type": "text",
        }

    if not isinstance(query, str) or not query.strip():
        return failure("Enter a question about your transactions.")

    required = {"transaction_type", "amount", "category"}
    if df is None or not required.issubset(df.columns):
        return failure("Transaction data is unavailable for this question.")

    question = query.casefold()
    data = df.copy()
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data = data.loc[
        data["amount"].notna()
        & data["amount"].map(math.isfinite)
        & (data["amount"] >= 0)
    ].copy()
    data["transaction_type"] = (
        data["transaction_type"].fillna("").astype(str).str.strip().str.title()
    )
    data["category"] = data["category"].fillna("").astype(str).str.strip()

    transaction_kind = None
    if any(
        word in question
        for word in ("income", "earned", "earnings", "salary", "revenue")
    ):
        transaction_kind = "Income"
    elif any(
        word in question
        for word in (
            "spend",
            "spent",
            "expense",
            "expenses",
            "spending",
            "purchase",
            "purchases",
            "cost",
        )
    ):
        transaction_kind = "Expense"

    normalized_question = re.sub(r"[^a-z0-9]+", " ", question).strip()
    category = None
    for known_category in sorted(KNOWN_CATEGORIES, key=len, reverse=True):
        normalized_category = re.sub(
            r"[^a-z0-9]+", " ", known_category.casefold()
        ).strip()
        if f" {normalized_category} " in f" {normalized_question} ":
            category = known_category
            break

    if category and transaction_kind is None:
        if category in EXPENSE_CATEGORIES:
            transaction_kind = "Expense"
        elif category in INCOME_CATEGORIES:
            transaction_kind = "Income"

    if "transaction_date" in data.columns:
        data["transaction_date"] = to_datetime(data["transaction_date"])
    else:
        data["transaction_date"] = pd.NaT

    month = None
    current_period = pd.Period(today, freq="M")
    if any(term in question for term in ("last month", "previous month")):
        month = str(current_period - 1)
    elif any(term in question for term in ("this month", "current month")):
        month = str(current_period)

    if month:
        transaction_months = data["transaction_date"].dt.strftime("%Y-%m")
        data = data.loc[transaction_months == month].copy()

    if transaction_kind:
        data = data.loc[data["transaction_type"] == transaction_kind].copy()

    if category:
        data = data.loc[
            data["category"].str.casefold() == category.casefold()
        ].copy()

    if any(
        term in question
        for term in (
            "highest category",
            "top category",
            "most",
            "highest expense",
            "where did i spend",
        )
    ):
        expenses = data.loc[data["transaction_type"] == "Expense"]
        if expenses.empty:
            return failure("There are no expenses in that period to rank.")
        totals = expenses.groupby("category")["amount"].sum()
        top_category = str(totals.idxmax())
        amount = float(totals.max())
        period_label = (
            f" in {pd.Period(month, freq='M').strftime('%B %Y')}" if month else ""
        )
        return {
            "success": True,
            "answer": f"{top_category} was your highest spending category{period_label}.",
            "metric_val": amount,
            "type": "currency",
        }

    comparison_requested = any(
        term in question
        for term in (
            "compared to",
            "compared with",
            "versus",
            " vs ",
            "change from",
            "difference",
            "month over month",
        )
    )
    if comparison_requested and "transaction_date" in df.columns:
        comparison_data = df.copy()
        comparison_data["amount"] = pd.to_numeric(
            comparison_data["amount"], errors="coerce"
        )
        comparison_data["transaction_date"] = to_datetime(
            comparison_data["transaction_date"]
        )
        comparison_data = comparison_data.loc[
            comparison_data["amount"].notna()
            & comparison_data["amount"].map(math.isfinite)
            & (comparison_data["amount"] >= 0)
        ]
        if transaction_kind:
            comparison_data = comparison_data.loc[
                comparison_data["transaction_type"] == transaction_kind
            ]
        else:
            comparison_data = comparison_data.loc[
                comparison_data["transaction_type"] == "Expense"
            ]
        if category:
            comparison_data = comparison_data.loc[
                comparison_data["category"].astype(str).str.casefold()
                == category.casefold()
            ]

        current_month = str(current_period)
        previous_month = str(current_period - 1)
        comparison_months = comparison_data["transaction_date"].dt.strftime(
            "%Y-%m"
        )
        current_total = float(
            comparison_data.loc[
                comparison_months == current_month, "amount"
            ].sum()
        )
        previous_total = float(
            comparison_data.loc[
                comparison_months == previous_month, "amount"
            ].sum()
        )
        label = "income" if transaction_kind == "Income" else "expenses"
        category_label = f" for {category}" if category else ""
        return {
            "success": True,
            "answer": (
                f"{label.capitalize()}{category_label}: this month compared "
                "with last month."
            ),
            "metric_val": {
                "current": current_total,
                "previous": previous_total,
                "change": current_total - previous_total,
            },
            "type": "comparison",
        }

    if any(term in question for term in ("how many", "count", "number of")):
        return {
            "success": True,
            "answer": "Matching transactions",
            "metric_val": int(len(data)),
            "type": "count",
        }

    if any(term in question for term in ("average", "avg", "mean")):
        if data.empty:
            return failure("There are no matching transactions to average.")
        kind_label = (
            "income"
            if transaction_kind == "Income"
            else "expenses"
            if transaction_kind == "Expense"
            else "transactions"
        )
        return {
            "success": True,
            "answer": f"Average {kind_label} transaction amount",
            "metric_val": float(data["amount"].mean()),
            "type": "currency",
        }

    if month:
        month_label = pd.Period(month, freq="M").strftime("%B %Y")
        kind_label = (
            "income"
            if transaction_kind == "Income"
            else "expenses"
            if transaction_kind == "Expense" or not transaction_kind
            else "transactions"
        )
        total = float(data["amount"].sum())
        return {
            "success": True,
            "answer": f"Total {kind_label} for {month_label}",
            "metric_val": total,
            "type": "currency",
        }

    if category:
        if data.empty:
            return failure(f"No matching transactions were found for {category}.")
        kind_label = (
            "income" if transaction_kind == "Income" else "spending"
        )
        return {
            "success": True,
            "answer": f"Total {kind_label} for {category}",
            "metric_val": float(data["amount"].sum()),
            "type": "currency",
        }

    return failure(
        "I couldn't match that question to your transaction data. "
        "Try asking about spending by category, monthly totals, top categories, "
        "transaction counts, or averages."
    )
