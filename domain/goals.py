"""Savings goal progress, timelines, and status."""

import math
from datetime import date, datetime


def calculate_goal_metrics(goal, today, monthly_savings_avg=0.0):
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


def is_goal_completed(goal):
    return float(goal.get("current_amount") or 0.0) >= float(
        goal["target_amount"]
    )


def split_goals(goals):
    """(active, completed) goals, preserving order."""

    active = [goal for goal in goals if not is_goal_completed(goal)]
    completed = [goal for goal in goals if is_goal_completed(goal)]
    return active, completed


def goal_status_label(metrics):
    """Badge text for a goal card."""

    if metrics["status"] != "COMPLETED" and metrics["months_remaining"] > 0:
        return "On track"
    return metrics["status"].title()
