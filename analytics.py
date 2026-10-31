import math
import re
from calendar import monthrange
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from database import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    KNOWN_CATEGORIES,
    get_transactions,
    get_transactions_for_month_range,
)
from utils.dates import today_local


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


def _normalize_descriptions(series):
    """Casefold descriptions and collapse punctuation/whitespace."""

    return (
        series.fillna("")
        .astype(str)
        .str.casefold()
        .str.replace(r"[^\w]+", " ", regex=True)
        .str.replace("_", " ", regex=False)
        .str.split()
        .str.join(" ")
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


def load_demo_transactions():
    """Prepare the synthetic transaction dataset for a guest demo."""

    from utils.demo_data import get_demo_transactions

    return prepare_transactions(get_demo_transactions())


def filter_transactions_by_month_range(df, start_month, end_month):
    """Filter transaction dates or month labels to an inclusive YYYY-MM range."""

    if df is None or df.empty:
        return (
            df.copy()
            if isinstance(df, pd.DataFrame)
            else pd.DataFrame(columns=TRANSACTION_COLUMNS)
        )

    date_column = (
        "transaction_date"
        if "transaction_date" in df.columns
        else "month" if "month" in df.columns else None
    )
    if date_column is None:
        return df.iloc[0:0].copy()

    start = pd.Period(start_month, freq="M")
    end = pd.Period(end_month, freq="M")
    if start > end:
        return df.iloc[0:0].copy()

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce",
        format="ISO8601",
    )
    months = dates.dt.to_period("M")
    filtered = df.loc[months.between(start, end)].copy()
    if "invalid_rows" in df.attrs:
        filtered.attrs["invalid_rows"] = df.attrs["invalid_rows"]
    return filtered.reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_summary(df, user_id=None, selected_month=None):
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_80c_headroom(
    financial_year_df,
    today,
    user_id=None,
    selected_month=None,
):
    """Summarize investment and healthcare spending for the tax tracker."""

    financial_year_start = date(
        today.year if today.month >= 4 else today.year - 1,
        4,
        1,
    )
    financial_year_end = date(financial_year_start.year + 1, 3, 31)
    required_columns = {
        "transaction_date",
        "transaction_type",
        "category",
        "amount",
    }

    if (
        financial_year_df is None
        or financial_year_df.empty
        or not required_columns.issubset(financial_year_df.columns)
    ):
        fy_transactions = pd.DataFrame(columns=required_columns)
    else:
        fy_transactions = financial_year_df.copy()
        dates = pd.to_datetime(
            fy_transactions["transaction_date"],
            errors="coerce",
        ).dt.date
        in_financial_year = dates.between(
            financial_year_start,
            financial_year_end,
            inclusive="both",
        )
        fy_transactions = fy_transactions.loc[in_financial_year]

    expenses = fy_transactions.loc[
        fy_transactions["transaction_type"].eq("Expense")
    ]

    def category_total(category):
        total = 0.0
        for amount in expenses.loc[
            expenses["category"].eq(category), "amount"
        ]:
            try:
                number = float(amount)
            except (TypeError, ValueError):
                continue
            if not math.isnan(number):
                total += number
        return total

    investment_total = category_total("Investment")
    healthcare_total = category_total("Healthcare")
    section_80c_limit = 150_000
    section_80c_total = min(investment_total, section_80c_limit)

    return {
        "investment_total": investment_total,
        "healthcare_total": healthcare_total,
        "section_80c_total": section_80c_total,
        "remaining_headroom": max(
            section_80c_limit - section_80c_total,
            0,
        ),
    }


def calculate_goal_metrics(goal, monthly_savings_avg=0.0):
    """Calculate progress and monthly funding needs for a savings goal."""

    try:
        target_amount = float(goal["target_amount"])
        current_amount = float(goal.get("current_amount", 0.0))
        target_date_value = goal["target_date"]
        monthly_savings_avg = float(monthly_savings_avg)
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ValueError("Goal amounts and target date must be provided.")

    if (
        not math.isfinite(target_amount)
        or target_amount <= 0
        or not math.isfinite(current_amount)
        or current_amount < 0
        or not math.isfinite(monthly_savings_avg)
        or monthly_savings_avg < 0
    ):
        raise ValueError("Goal amounts and monthly savings must be valid.")

    if isinstance(target_date_value, datetime):
        target_date = target_date_value.date()
    elif isinstance(target_date_value, date):
        target_date = target_date_value
    elif isinstance(target_date_value, str):
        try:
            target_date = date.fromisoformat(target_date_value.strip())
        except ValueError:
            try:
                target_date = datetime.fromisoformat(
                    target_date_value.strip()
                ).date()
            except ValueError:
                raise ValueError("Goal target date must be a valid ISO date.")
    else:
        raise ValueError("Goal target date must be a valid ISO date.")

    remaining_amount = target_amount - current_amount
    percent_complete = min(current_amount / target_amount * 100, 100.0)
    today = today_local()

    if target_date <= today:
        months_remaining = 0
    else:
        months_remaining = max(
            1,
            (target_date.year - today.year) * 12
            + target_date.month
            - today.month,
        )

    if current_amount >= target_amount:
        status = "COMPLETED"
        required_monthly_savings = 0.0
    elif months_remaining == 0:
        status = "BEHIND"
        required_monthly_savings = remaining_amount
    else:
        required_monthly_savings = remaining_amount / months_remaining
        status = (
            "ON_TRACK"
            if monthly_savings_avg >= required_monthly_savings
            else "BEHIND"
        )

    return {
        "percent_complete": round(percent_complete, 2),
        "remaining_amount": round(remaining_amount, 2),
        "months_remaining": months_remaining,
        "required_monthly_savings": round(required_monthly_savings, 2),
        "status": status,
    }


def parse_natural_language_query(query: str, df: pd.DataFrame) -> dict:
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
        data["transaction_date"] = _to_datetime(data["transaction_date"])
    else:
        data["transaction_date"] = pd.NaT

    month = None
    current_period = pd.Period(today_local(), freq="M")
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
        comparison_data["transaction_date"] = _to_datetime(
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def category_breakdown(df, user_id=None, selected_month=None):
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def detect_recurring_subscriptions(
    df,
    user_id=None,
    selected_month=None,
):
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
    expenses["transaction_date"] = _to_datetime(
        expenses["transaction_date"]
    )
    expenses = expenses.loc[
        expenses["amount"].notna()
        & expenses["amount"].map(math.isfinite)
        & (expenses["amount"] > 0)
        & expenses["transaction_date"].notna()
    ].copy()
    expenses["normalized_description"] = _normalize_descriptions(
        expenses["description"]
    )
    expenses = expenses.loc[
        expenses["normalized_description"].ne("")
    ]
    if expenses.empty:
        return []

    today = today_local()
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def detect_spending_anomalies(user_id, selected_month, transactions=None):
    """Flag current-month expenses unusually large for their category."""

    if user_id is None:
        raise ValueError("user_id is required to detect spending anomalies.")

    selected_period = pd.Period(selected_month, freq="M")
    history_start = str(selected_period - 6)
    history_end = str(selected_period - 1)

    if transactions is None:
        transactions = get_transactions_for_month_range(
            history_start,
            selected_month,
            user_id=user_id,
        )
    if isinstance(transactions, pd.DataFrame):
        data = prepare_transactions(transactions.to_dict("records"))
    else:
        data = prepare_transactions(transactions)
    if data.empty:
        return []

    data["transaction_date"] = _to_datetime(data["transaction_date"])
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


ROLLING_SPEND_WINDOW_DAYS = 30


def calculate_rolling_daily_spend(
    df,
    as_of=None,
    window_days=ROLLING_SPEND_WINDOW_DAYS,
):
    """
    Average daily expenses over the trailing window ending on as_of
    (inclusive). Days without expenses count as zero spend.
    """

    if not isinstance(window_days, int) or window_days <= 0:
        raise ValueError("window_days must be a positive integer.")

    if df is None or df.empty:
        return 0.0

    as_of = as_of or today_local()
    dates = _to_datetime(df["transaction_date"]).dt.date
    window_expenses = df.loc[
        df["transaction_type"].eq("Expense")
        & dates.ge(as_of - timedelta(days=window_days - 1))
        & dates.le(as_of),
        "amount",
    ]
    total = float(
        pd.to_numeric(window_expenses, errors="coerce").fillna(0).sum()
    )
    return total / window_days


def _monthly_payment_date(payment_date, month_offset):
    month_index = payment_date.year * 12 + payment_date.month - 1 + month_offset
    year, month = divmod(month_index, 12)
    month += 1
    return date(
        year,
        month,
        min(payment_date.day, monthrange(year, month)[1]),
    )


def _billing_cycle_payment_indices(payment_dates, last_payment_date, since):
    """
    Pick one payment per monthly cycle, walking back from the last payment
    with the same 25-35 day cadence the subscription detector uses.
    """

    indices = []
    earliest = latest = last_payment_date
    while latest >= since:
        in_cycle = payment_dates.loc[
            payment_dates.ge(earliest) & payment_dates.le(latest)
        ]
        if in_cycle.empty:
            break
        payment_date = in_cycle.max()
        indices.append(in_cycle.index[in_cycle.eq(payment_date)][0])
        earliest = payment_date - timedelta(days=35)
        latest = payment_date - timedelta(days=25)
    return indices


def _recurring_cost_through_day(recurring_bills, today, days):
    target_date = today + timedelta(days=days)
    total = 0.0

    for bill in recurring_bills:
        payment_date = bill["last_payment_date"]
        month_offset = (
            (target_date.year - payment_date.year) * 12
            + target_date.month
            - payment_date.month
        )
        if month_offset < bill["first_month_offset"]:
            continue
        if _monthly_payment_date(payment_date, month_offset) > target_date:
            month_offset -= 1
        payment_count = max(
            0,
            month_offset - bill["first_month_offset"] + 1,
        )
        total += bill["monthly_cost"] * payment_count

    return total


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_cash_flow_forecast(
    user_id,
    current_balance,
    forecast_days=30,
    transactions=None,
):
    """Project cash balances using recent spending and detected monthly bills."""

    if not isinstance(forecast_days, int) or forecast_days < 0:
        raise ValueError("forecast_days must be a non-negative integer.")

    try:
        starting_balance = float(current_balance)
    except (TypeError, ValueError) as error:
        raise ValueError("current_balance must be a finite number.") from error
    if not math.isfinite(starting_balance):
        raise ValueError("current_balance must be a finite number.")

    if transactions is None:
        transactions = prepare_transactions(get_transactions(user_id))
    elif not isinstance(transactions, pd.DataFrame):
        transactions = prepare_transactions(transactions)
    else:
        transactions = prepare_transactions(transactions.to_dict("records"))

    today = today_local()
    burn_rate_daily = calculate_rolling_daily_spend(transactions, as_of=today)

    subscriptions = detect_recurring_subscriptions(
        transactions,
        user_id=user_id,
        selected_month=today.strftime("%Y-%m"),
    )
    recurring_bills = []
    for subscription in subscriptions:
        last_payment = subscription["last_payment_date"]
        if isinstance(last_payment, pd.Timestamp):
            last_payment = last_payment.date()
        elif isinstance(last_payment, datetime):
            last_payment = last_payment.date()
        monthly_cost = float(subscription["monthly_cost"])
        first_month_offset = 1
        while _monthly_payment_date(
            last_payment,
            first_month_offset,
        ) <= today:
            first_month_offset += 1
        recurring_bills.append(
            {
                "last_payment_date": last_payment,
                "first_month_offset": first_month_offset,
                "monthly_cost": monthly_cost,
            }
        )

    # Recurring bills are scheduled separately below, so drop their actual
    # payments from the window instead of subtracting a monthly average
    # (a 30-day window can hold zero or two payments of the same bill).
    is_recurring_payment = pd.Series(False, index=transactions.index)
    if subscriptions:
        descriptions = _normalize_descriptions(transactions["description"])
        amounts = pd.to_numeric(transactions["amount"], errors="coerce")
        payment_dates = _to_datetime(transactions["transaction_date"]).dt.date
        for subscription, bill in zip(subscriptions, recurring_bills):
            monthly_cost = bill["monthly_cost"]
            candidates = payment_dates.loc[
                transactions["transaction_type"].eq("Expense")
                & descriptions.eq(subscription["description"])
                & (amounts - monthly_cost).abs().le(
                    max(monthly_cost * 0.05, 0.01)
                )
                & ~is_recurring_payment
            ]
            is_recurring_payment.loc[
                _billing_cycle_payment_indices(
                    candidates,
                    bill["last_payment_date"],
                    since=today - timedelta(days=ROLLING_SPEND_WINDOW_DAYS - 1),
                )
            ] = True
    discretionary_burn_daily = calculate_rolling_daily_spend(
        transactions.loc[~is_recurring_payment],
        as_of=today,
    )

    def projected_balance_after(days):
        return (
            starting_balance
            - discretionary_burn_daily * days
            - _recurring_cost_through_day(recurring_bills, today, days)
        )

    if starting_balance < 0:
        runway_days = 0
        runout_date = today
    elif discretionary_burn_daily == 0 and not recurring_bills:
        runway_days = None
        runout_date = None
    else:
        lower_bound = 0
        upper_bound = 1
        while projected_balance_after(upper_bound) >= 0:
            upper_bound *= 2
        while lower_bound + 1 < upper_bound:
            midpoint = (lower_bound + upper_bound) // 2
            if projected_balance_after(midpoint) < 0:
                upper_bound = midpoint
            else:
                lower_bound = midpoint
        runway_days = upper_bound
        runout_date = today + timedelta(days=runway_days)

    forecast_end = today + timedelta(days=forecast_days)
    scheduled_bills = {}
    for bill in recurring_bills:
        payment_offset = bill["first_month_offset"]
        payment_date = _monthly_payment_date(
            bill["last_payment_date"],
            payment_offset,
        )
        while payment_date <= forecast_end:
            scheduled_bills[payment_date] = (
                scheduled_bills.get(payment_date, 0.0)
                + bill["monthly_cost"]
            )
            payment_offset += 1
            payment_date = _monthly_payment_date(
                bill["last_payment_date"],
                payment_offset,
            )

    projected_rows = []
    balance = starting_balance
    for day_offset in range(1, forecast_days + 1):
        forecast_date = today + timedelta(days=day_offset)
        balance -= discretionary_burn_daily
        balance -= scheduled_bills.get(forecast_date, 0.0)
        projected_rows.append(
            {
                "date": forecast_date,
                "projected_balance": round(balance, 2),
            }
        )

    return {
        "projected_df": pd.DataFrame(
            projected_rows,
            columns=["date", "projected_balance"],
        ),
        "burn_rate_daily": burn_rate_daily,
        "runway_days": runway_days,
        "runout_date": runout_date,
    }


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def monthly_trend(df, user_id=None, selected_month=None):
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def compare_months(
    df,
    current_month,
    previous_month,
    user_id=None,
    selected_month=None,
):
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


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def calculate_budget_status(
    month_df,
    budgets,
    user_id=None,
    selected_month=None,
):
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