"""Compatibility shim: insight rules now live in ``domain.insights``."""

from domain.insights import (
    BUDGET_WARNING_PERCENT,
    CONCENTRATION_THRESHOLD,
    HEALTHY_SAVINGS_RATE,
    LOW_SAVINGS_RATE,
    MIN_EXPENSES_FOR_OUTLIER,
    OUTLIER_MULTIPLIER,
    generate_insights,
)

__all__ = [
    "BUDGET_WARNING_PERCENT",
    "CONCENTRATION_THRESHOLD",
    "HEALTHY_SAVINGS_RATE",
    "LOW_SAVINGS_RATE",
    "MIN_EXPENSES_FOR_OUTLIER",
    "OUTLIER_MULTIPLIER",
    "generate_insights",
]
