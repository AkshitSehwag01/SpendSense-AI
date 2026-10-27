from calendar import monthrange
from datetime import date

from utils.dates import today_local


_MONTHLY_BUDGETS = {
    "Food": 18000.0,
    "Shopping": 10000.0,
    "Travel": 8000.0,
    "Rent": 25000.0,
    "Utilities": 6000.0,
    "Healthcare": 5000.0,
    "Education": 4000.0,
    "Entertainment": 5000.0,
    "EMI / Loans": 12000.0,
    "Investment": 15000.0,
    "Other": 4000.0,
}


def _month_offset(year, month, offset):
    month_index = year * 12 + month - 1 + offset
    return month_index // 12, month_index % 12 + 1


def _day_in_month(year, month, day):
    return date(year, month, min(day, monthrange(year, month)[1]))


def get_demo_transactions():
    """Return realistic, synthetic transactions spanning six months."""

    today = today_local()
    transactions = []
    transaction_id = 1
    monthly_examples = (
        ("Income", 125000.0, "Salary", "Monthly salary", 1),
        ("Expense", 25000.0, "Rent", "Apartment rent", 3),
        ("Expense", 4200.0, "Food", "Groceries at D-Mart", 6),
        ("Expense", 1850.0, "Food", "Dinner at Swiggy", 12),
        ("Expense", 2400.0, "Utilities", "Electricity and internet", 15),
        ("Expense", 3200.0, "Entertainment", "Streaming and cinema", 19),
        ("Expense", 6000.0, "Investment", "Monthly SIP investment", 24),
    )

    for offset in range(-5, 1):
        year, month = _month_offset(today.year, today.month, offset)
        for kind, amount, category, description, day in monthly_examples:
            transactions.append(
                {
                    "id": transaction_id,
                    "transaction_type": kind,
                    "amount": amount,
                    "category": category,
                    "description": description,
                    "transaction_date": _day_in_month(
                        year, month, day
                    ).isoformat(),
                }
            )
            transaction_id += 1

    return transactions


def get_demo_budgets():
    """Return sample monthly category budget limits."""

    return dict(_MONTHLY_BUDGETS)


def get_demo_budget_records(month=None):
    """Return sample budgets in the same row shape as database reports."""

    if month is None:
        today = today_local()
        month = f"{today.year:04d}-{today.month:02d}"
    return [
        {"month": month, "category": category, "amount": amount}
        for category, amount in _MONTHLY_BUDGETS.items()
    ]


def get_demo_transaction_months():
    """Return months represented by the synthetic transaction history."""

    return {
        transaction["transaction_date"][:7]
        for transaction in get_demo_transactions()
    }
