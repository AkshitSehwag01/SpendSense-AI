import math
import pandas as pd

from database import KNOWN_CATEGORIES


TRANSACTION_COLUMNS = [
    "id",
    "transaction_type",
    "amount",
    "category",
    "description",
    "transaction_date",
]

VALID_TYPES = ("Income", "Expense")

# Same canonical spellings the database uses (e.g. "EMI / Loans").
_CANONICAL_CATEGORY = {
    name.casefold(): name for name in KNOWN_CATEGORIES
}


# -----------------------------
# Internal helpers
# -----------------------------

def _to_datetime(series):
    """
    Parse ISO dates, with or without a time part, in one column.
    Invalid values become NaT. Requires pandas >= 2.0.
    """
    return pd.to_datetime(series, errors="coerce", format="ISO8601")


def _normalize_categories(series, empty_value=""):
    """
    Tidy whitespace and apply canonical capitalization.
    Known categories keep their exact spelling (EMI / Loans);
    custom ones are title-cased.
    """

    def clean(name):
        if not name:
            return empty_value
        return _CANONICAL_CATEGORY.get(name.casefold(), name.title())

    return (
        series.fillna("")
        .astype(str)
        .str.split()
        .str.join(" ")
        .map(clean)
    )


def _empty_summary():
    return {
        "income": 0.0,
        "expenses": 0.0,
        "savings": 0.0,
        "savings_rate": 0.0,
        "transaction_count": 0,
    }


# -----------------------------
# Public functions
# -----------------------------

def prepare_transactions(transactions):
    """
    Convert database transactions into a clean DataFrame.
    Normalize types and categories, drop invalid rows, and keep the
    number of dropped rows in df.attrs["invalid_rows"].
    """

    df = pd.DataFrame(transactions)

    if df.empty:
        df = pd.DataFrame(columns=TRANSACTION_COLUMNS)
        df.attrs["invalid_rows"] = 0
        return df

    # Ensure expected columns exist.
    for column in TRANSACTION_COLUMNS:
        if column not in df.columns:
            df[column] = None

    # Normalize text fields.
    df["transaction_type"] = (
        df["transaction_type"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.title()
    )

    df["category"] = _normalize_categories(df["category"])

    df["description"] = df["description"].fillna("").astype(str)

    # Convert dates and amounts.
    df["transaction_date"] = _to_datetime(df["transaction_date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Identify invalid records before filtering.
    invalid_mask = (
        df["transaction_date"].isna()
        | df["amount"].isna()
        | ~df["amount"].map(math.isfinite)
        | (df["amount"] <= 0)
        | ~df["transaction_type"].isin(VALID_TYPES)
        | (df["category"] == "")
    )

    invalid_rows = int(invalid_mask.sum())

    # Exclude invalid records from financial calculations.
    df = df.loc[~invalid_mask].reset_index(drop=True)

    # Keep data-quality information available to the app.
    df.attrs["invalid_rows"] = invalid_rows

    return df


def calculate_summary(df):
    """
    Calculate income, expenses, savings, and savings rate.
    """

    if df is None or df.empty:
        return _empty_summary()

    totals = df.groupby("transaction_type")["amount"].sum()

    income = float(totals.get("Income", 0.0))
    expenses = float(totals.get("Expense", 0.0))
    savings = income - expenses

    savings_rate = (savings / income) * 100 if income > 0 else 0.0

    return {
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "savings": round(savings, 2),
        "savings_rate": round(savings_rate, 2),
        "transaction_count": int(len(df)),
    }


def category_breakdown(df):
    """
    Calculate expense totals and percentages by category.
    """

    columns = ["category", "amount", "percentage"]

    if df is None or df.empty:
        return pd.DataFrame(columns=columns)

    expenses = df.loc[df["transaction_type"] == "Expense"].copy()

    if expenses.empty:
        return pd.DataFrame(columns=columns)

    # Safe even if the frame did not come from prepare_transactions().
    expenses["category"] = _normalize_categories(
        expenses["category"],
        empty_value="Other",
    )

    result = (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .reset_index(drop=True)
    )

    total = result["amount"].sum()

    result["percentage"] = (
        result["amount"] / total * 100 if total > 0 else 0.0
    )

    result["amount"] = result["amount"].round(2)

    return result[columns]


def monthly_trend(df):
    """
    Calculate monthly income, expenses, and savings.

    The month column is in YYYY-MM format (for example 2026-10),
    which sorts chronologically and displays cleanly.
    """

    columns = ["month", "income", "expenses", "savings"]

    if df is None or df.empty:
        return pd.DataFrame(columns=columns)

    data = df.copy()

    # Safe even if the frame did not come from prepare_transactions().
    data["transaction_date"] = _to_datetime(data["transaction_date"])
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")

    data = data.loc[
        data["transaction_date"].notna()
        & data["amount"].notna()
        & (data["amount"] > 0)
        & data["transaction_type"].isin(VALID_TYPES)
    ].copy()

    if data.empty:
        return pd.DataFrame(columns=columns)

    data["month"] = data["transaction_date"].dt.strftime("%Y-%m")

    # One row per month, one column per transaction type.
    result = (
        data.pivot_table(
            index="month",
            columns="transaction_type",
            values="amount",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reindex(columns=list(VALID_TYPES), fill_value=0.0)
        .rename(columns={"Income": "income", "Expense": "expenses"})
    )

    result["savings"] = result["income"] - result["expenses"]

    result = result.round(2).sort_index().reset_index()
    result.columns.name = None

    return result[columns]


def compare_months(df, current_month, previous_month):
    """
    Compare spending between two months (both in YYYY-MM format).
    """

    empty = {
        "current_expenses": 0.0,
        "previous_expenses": 0.0,
        "change": 0.0,
        "change_percentage": None,
    }

    required = {"transaction_date", "transaction_type", "amount"}

    if df is None or df.empty or not required.issubset(df.columns):
        return empty

    months = _to_datetime(df["transaction_date"]).dt.strftime("%Y-%m")
    is_expense = df["transaction_type"] == "Expense"

    current_expenses = float(
        df.loc[(months == current_month) & is_expense, "amount"].sum()
    )

    previous_expenses = float(
        df.loc[(months == previous_month) & is_expense, "amount"].sum()
    )

    change = current_expenses - previous_expenses

    change_percentage = (
        round(change / previous_expenses * 100, 2)
        if previous_expenses > 0
        else None
    )

    return {
        "current_expenses": round(current_expenses, 2),
        "previous_expenses": round(previous_expenses, 2),
        "change": round(change, 2),
        "change_percentage": change_percentage,
    }


def get_month_data(df, month):
    """Return the transactions that belong to a month (YYYY-MM)."""

    if df is None:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    if df.empty:
        return df.copy()

    months = _to_datetime(df["transaction_date"]).dt.strftime("%Y-%m")

    return df.loc[months == month].copy()


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