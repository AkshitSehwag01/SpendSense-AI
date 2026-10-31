"""Domain services run as plain Python, without Streamlit or a database."""

import sys
from datetime import date, timedelta

import pytest

sys.modules["streamlit"] = None  # any Streamlit import in domain/ fails

from domain import budgets, forecasting, goals, insights, tax  # noqa: E402
from domain.transactions import (  # noqa: E402
    calculate_summary,
    month_window,
    monthly_trend,
    prepare_transactions,
)

TODAY = date(2027, 3, 1)


def _rows(*items):
    return [
        {
            "id": index,
            "transaction_type": kind,
            "amount": amount,
            "category": category,
            "description": description,
            "transaction_date": day.isoformat(),
        }
        for index, (kind, amount, category, description, day) in enumerate(
            items, start=1
        )
    ]


def test_prepare_and_summarize():
    df = prepare_transactions(
        _rows(
            ("Income", 1000, "salary", "Pay", TODAY),
            ("Expense", 250, "food", "Lunch", TODAY),
            ("Expense", -1, "food", "Invalid", TODAY),
        )
    )
    assert df.attrs["invalid_rows"] == 1
    assert calculate_summary(df) == {
        "income": 1000.0,
        "expenses": 250.0,
        "savings": 750.0,
        "savings_rate": 75.0,
        "transaction_count": 2,
    }


def test_month_window_fills_missing_months():
    df = prepare_transactions(
        _rows(("Expense", 100, "Food", "x", date(2027, 1, 5)))
    )
    window = month_window(monthly_trend(df), "2027-03", 3)
    assert window["month"].tolist() == ["2027-01", "2027-02", "2027-03"]
    assert window["expenses"].tolist() == [100.0, 0.0, 0.0]


def test_rolling_daily_spend_uses_trailing_30_days():
    df = prepare_transactions(
        _rows(
            ("Expense", 300, "Food", "in window", TODAY - timedelta(days=29)),
            ("Expense", 900, "Food", "outside", TODAY - timedelta(days=30)),
        )
    )
    assert forecasting.calculate_rolling_daily_spend(df, TODAY) == 10.0


def test_forecast_excludes_recurring_bill_from_discretionary_burn():
    df = prepare_transactions(
        _rows(
            ("Expense", 1000, "Rent", "Rent", date(2027, 1, 1)),
            ("Expense", 1000, "Rent", "Rent", date(2027, 2, 1)),
            ("Expense", 1000, "Rent", "Rent", date(2027, 3, 1)),
            ("Expense", 300, "Food", "groceries", date(2027, 2, 20)),
        )
    )
    forecast = forecasting.calculate_cash_flow_forecast(
        df, 5000.0, TODAY, forecast_days=90
    )
    assert round(forecast["burn_rate_daily"], 2) == 76.67
    assert forecast["projected_df"].iloc[-1]["projected_balance"] == 2100.0


@pytest.mark.parametrize(
    ("runway", "horizon_balance", "below", "negative"),
    [(10, -500.0, True, False), (61, -3000.0, False, True), (None, 100.0, False, False)],
)
def test_assess_runway(runway, horizon_balance, below, negative):
    result = forecasting.assess_runway(runway, None, horizon_balance)
    assert result.below_warning_threshold is below
    assert result.negative_at_horizon is negative
    assert result.no_runout is (runway is None)


def test_budget_status_and_totals():
    month_df = prepare_transactions(
        _rows(
            ("Expense", 900, "Food", "x", TODAY),
            ("Expense", 50, "Travel", "x", TODAY),
            ("Expense", 400, "Shopping", "x", TODAY),
        )
    )
    status = budgets.calculate_budget_status(month_df, {"Food": 1000, "travel": 40})
    assert status["Used (%)"].tolist() == [90.0, 125.0]
    totals = budgets.summarize_budgets(status, month_df)
    assert (totals.total_limit, totals.spent, totals.unbudgeted) == (1040.0, 950.0, 400.0)
    assert budgets.count_status_levels(status) == {"over": 1, "near": 1, "ok": 0}
    assert budgets.budget_status_level(76, near_percent=75) == "near"


def test_goal_metrics_and_split():
    goal = {"target_amount": 12000, "current_amount": 0, "target_date": "2028-03-01"}
    metrics = goals.calculate_goal_metrics(goal, TODAY, monthly_savings_avg=500)
    assert metrics["months_remaining"] == 12
    assert metrics["required_monthly_savings"] == 1000.0
    assert metrics["status"] == "BEHIND"
    done = {"target_amount": 10, "current_amount": 10, "target_date": "2027-01-01"}
    assert goals.split_goals([goal, done]) == ([goal], [done])


def test_tax_statement_old_vs_new_regime():
    df = prepare_transactions(
        _rows(
            ("Expense", 200000, "Investment", "PPF deposit", date(2026, 6, 1)),
            ("Expense", 30000, "Healthcare", "Health insurance premium", date(2026, 7, 1)),
        )
    )
    start, end = tax.financial_year(TODAY)
    assert (start, end) == (date(2026, 4, 1), date(2027, 3, 31))
    transactions = tax.financial_year_transactions(df, start, end)
    prefill = tax.tax_prefill(transactions)
    args = dict(
        transactions=transactions, basic_salary=0, hra_received=0, rent_paid=0,
        metro_city=False, self_health_premium=prefill["self_health_premium"],
        parent_health_premium=0, parent_is_senior=False, savings_interest=0,
        taxpayer_is_senior=False, other_80c=0,
    )
    _, old_total = tax.build_deduction_statement(old_regime=True, **args)
    _, new_total = tax.build_deduction_statement(old_regime=False, **args)
    assert old_total == 150000 + 25000
    assert new_total == 0.0


def test_subscriptions_and_bills():
    df = prepare_transactions(
        _rows(
            ("Expense", 649, "Entertainment", "Netflix", date(2027, 1, 2)),
            ("Expense", 649, "Entertainment", "Netflix", date(2027, 2, 2)),
        )
    )
    subscriptions = insights.detect_recurring_subscriptions(df, TODAY)
    summary = insights.summarize_subscriptions(subscriptions, monthly_income=1000)
    assert summary.count == 1 and summary.exceeds_income_share_limit
    bills = insights.detect_upcoming_bills(
        _rows(
            ("Expense", 1500, "Utilities", "Electricity bill", date(2027, 1, 3)),
            ("Expense", 1500, "Utilities", "Electricity bill", date(2027, 2, 3)),
        ),
        date(2027, 3, 4),
    )
    assert [bill["bill_type"] for bill in bills] == ["Electricity"]
    assert bills[0]["days_until_due"] == 2
