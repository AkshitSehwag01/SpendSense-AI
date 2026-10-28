import html
import math
import re

import streamlit as st

from utils.constants import EXPENSE_CATEGORIES


SUPPORTED_CURRENCIES = {
    "INR": {"symbol": "₹", "rate": 1.0, "name": "INR (₹)"},
    "USD": {"symbol": "$", "rate": 0.012, "name": "USD ($)"},
    "EUR": {"symbol": "€", "rate": 0.011, "name": "EUR (€)"},
    "AED": {"symbol": "د.إ", "rate": 0.044, "name": "AED (د.إ)"},
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_conversion_rates():
    """Return approximate display rates, with INR as the base currency."""

    return {
        code: details["rate"]
        for code, details in SUPPORTED_CURRENCIES.items()
    }


def get_currency_symbol():
    """Return the active display symbol, defaulting to Indian rupees."""

    return st.session_state.get(
        "currency_symbol",
        SUPPORTED_CURRENCIES["INR"]["symbol"],
    )


def convert_currency(amount, currency_symbol=None):
    """Convert an INR amount to one of the supported display currencies."""

    currency_symbol = currency_symbol or get_currency_symbol()
    try:
        currency_code = next(
            code
            for code, details in SUPPORTED_CURRENCIES.items()
            if details["symbol"] == currency_symbol
        )
    except StopIteration as error:
        raise ValueError(
            f"Unsupported currency symbol: {currency_symbol}"
        ) from error

    return float(amount) * get_conversion_rates()[currency_code]


_CSS_COLOR_PATTERN = re.compile(
    r"(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{4}"
    r"|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8}"
    r"|transparent)\Z",
    re.IGNORECASE,
)

_MERCHANT_CATEGORY_KEYWORDS = (
    (("zomato", "swiggy"), "Food"),
    (("uber", "ola"), "Travel"),
    (("d-mart", "dmart", "amazon"), "Shopping"),
    (("netflix",), "Entertainment"),
    (("sip", "mutual fund"), "Investment"),
    (("rent",), "Rent"),
)


def suggest_category(description):
    """Suggest a canonical expense category from common merchant text."""

    if not isinstance(description, str) or not description.strip():
        return None

    normalized = re.sub(r"[^a-z0-9]+", " ", description.casefold()).strip()

    for keywords, category in _MERCHANT_CATEGORY_KEYWORDS:
        if category not in EXPENSE_CATEGORIES:
            continue
        padded_description = f" {normalized} "
        normalized_keywords = (
            re.sub(r"[^a-z0-9]+", " ", keyword.casefold()).strip()
            for keyword in keywords
        )
        if any(
            f" {keyword} " in padded_description
            for keyword in normalized_keywords
        ):
            return category

    return None


def render_badge(text, bg_color="#1E293B", text_color="#94A3B8"):
    """Return a compact badge span with escaped text and validated colors."""

    if not isinstance(bg_color, str) or not _CSS_COLOR_PATTERN.fullmatch(
        bg_color
    ):
        raise ValueError(
            "Badge background color must be a hex color or transparent."
        )
    if not isinstance(text_color, str) or not _CSS_COLOR_PATTERN.fullmatch(
        text_color
    ):
        raise ValueError(
            "Badge text color must be a hex color or transparent."
        )

    return (
        '<span style="display:inline-block;padding:3px 9px;'
        'border-radius:999px;font-size:0.68rem;font-weight:800;'
        f'letter-spacing:0.05em;background-color:{bg_color};'
        f'color:{text_color};">{html.escape(str(text), quote=True)}</span>'
    )


def money(value, currency_symbol=None):
    """
    Convert and format an INR amount in the selected display currency.

    INR uses lakh/crore grouping; other currencies use standard grouping.
    Invalid amounts display as zero in the selected currency.
    """

    currency_symbol = currency_symbol or get_currency_symbol()
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0

    if not math.isfinite(value):
        value = 0.0

    value = convert_currency(value, currency_symbol)
    text = f"{abs(value):.2f}"
    whole, fraction = text.split(".")

    if currency_symbol == SUPPORTED_CURRENCIES["INR"]["symbol"] and len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []

        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]

        if head:
            groups.insert(0, head)

        whole = ",".join(groups + [tail])
    elif currency_symbol != SUPPORTED_CURRENCIES["INR"]["symbol"]:
        whole = f"{int(whole):,}"

    sign = "-" if value < 0 and round(value, 2) != 0 else ""

    return f"{sign}{currency_symbol}{whole}.{fraction}"


def signed_money(transaction_type, amount, currency_symbol=None):
    """Format a transaction amount with its income/expense sign."""

    sign = "+" if transaction_type == "Income" else "−"
    return f"{sign}{money(amount, currency_symbol=currency_symbol)}"