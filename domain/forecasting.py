"""Cash-flow projections, rolling daily spend, and runway assessment."""

import math
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

from domain.insights import detect_recurring_subscriptions
from domain.transactions import normalize_descriptions, prepare_transactions, to_datetime


ROLLING_SPEND_WINDOW_DAYS = 30
RUNWAY_WARNING_DAYS = 30
FORECAST_HORIZONS = (30, 60, 90)


def calculate_rolling_daily_spend(
    df,
    as_of,
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

    dates = to_datetime(df["transaction_date"]).dt.date
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
            # This cycle's charge missed the amount filter; keep the cadence.
            anchor = earliest + (latest - earliest) / 2
        else:
            anchor = in_cycle.max()
            indices.append(in_cycle.index[in_cycle.eq(anchor)][0])
        earliest = anchor - timedelta(days=35)
        latest = anchor - timedelta(days=25)
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


def calculate_cash_flow_forecast(
    transactions,
    current_balance,
    today,
    forecast_days=30,
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

    if not isinstance(transactions, pd.DataFrame):
        transactions = prepare_transactions(transactions)
    else:
        transactions = prepare_transactions(transactions.to_dict("records"))

    burn_rate_daily = calculate_rolling_daily_spend(transactions, as_of=today)

    subscriptions = detect_recurring_subscriptions(transactions, today)
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
        descriptions = normalize_descriptions(transactions["description"])
        amounts = pd.to_numeric(transactions["amount"], errors="coerce")
        payment_dates = to_datetime(transactions["transaction_date"]).dt.date
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


def estimate_balance_history(transactions, today):
    """
    Signed balance changes for dated transactions up to ``today``.
    Returns the current balance and the per-transaction history frame.
    """

    transaction_dates = pd.to_datetime(
        transactions["transaction_date"],
        errors="coerce",
        format="ISO8601",
    )
    historical = transactions.loc[
        transaction_dates.notna()
        & transaction_dates.dt.date.le(today)
    ].copy()
    historical["transaction_date"] = transaction_dates.loc[
        historical.index
    ]
    historical["balance_change"] = historical["amount"].where(
        historical["transaction_type"].eq("Income"),
        -historical["amount"],
    )
    historical["balance_date"] = historical["transaction_date"].dt.date
    return float(historical["balance_change"].sum()), historical


def daily_balance_series(historical, today, days=30):
    """End-of-day recorded balances for the ``days`` ending ``today``."""

    history_start = today - timedelta(days=days - 1)
    daily_changes = historical.groupby("balance_date")[
        "balance_change"
    ].sum()
    history_dates = pd.date_range(
        start=history_start,
        end=today,
        freq="D",
    )
    balance = float(
        historical.loc[
            historical["balance_date"] < history_start,
            "balance_change",
        ].sum()
    )
    balances = []
    for history_date in history_dates:
        balance += float(daily_changes.get(history_date.date(), 0.0))
        balances.append(balance)
    return history_dates, balances


def projected_balances_at(projected_df, today, horizons=FORECAST_HORIZONS):
    """Projected balance at each horizon in days (None past the forecast)."""

    by_day = projected_df.set_index("date")["projected_balance"]
    return {
        horizon: by_day.get(today + timedelta(days=horizon))
        for horizon in horizons
    }


def forecast_series(projected_df, today, current_balance, days=30):
    """Dates and balances from today through ``days`` of the projection."""

    end = today + timedelta(days=days)
    window = projected_df.loc[projected_df["date"] <= end]
    return (
        [today] + window["date"].tolist(),
        [current_balance] + window["projected_balance"].tolist(),
    )


@dataclass(frozen=True)
class RunwayAssessment:
    runway_days: int | None
    runout_date: date | None
    below_warning_threshold: bool
    no_runout: bool
    negative_at_horizon: bool
    horizon_balance: float | None


def assess_runway(
    runway_days,
    runout_date,
    horizon_balance,
    warning_days=RUNWAY_WARNING_DAYS,
):
    """
    Classify runway risk. ``negative_at_horizon`` is only set when the
    shorter-runway warning does not already apply.
    """

    below = runway_days is not None and runway_days < warning_days
    return RunwayAssessment(
        runway_days=runway_days,
        runout_date=runout_date,
        below_warning_threshold=below,
        no_runout=runway_days is None,
        negative_at_horizon=(
            horizon_balance is not None
            and horizon_balance < 0
            and not below
        ),
        horizon_balance=horizon_balance,
    )
