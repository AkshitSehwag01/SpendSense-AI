import html
import math
import re

from utils.constants import EXPENSE_CATEGORIES


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


def money(value):
    """
    Format an amount in Indian Rupees with lakh/crore grouping.
    Examples: ₹1,500.00   ₹12,34,567.00   -₹9,99,99,999.00
    Bad values (None, text, NaN, infinity) show as ₹0.00.
    """

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "₹0.00"

    if not math.isfinite(value):
        return "₹0.00"

    text = f"{abs(value):.2f}"
    whole, fraction = text.split(".")

    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []

        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]

        if head:
            groups.insert(0, head)

        whole = ",".join(groups + [tail])

    # Avoid showing "-₹0.00" for tiny negative values.
    sign = "-" if value < 0 and float(text) != 0 else ""

    return f"{sign}₹{whole}.{fraction}"


def signed_money(transaction_type, amount):
    """Format a transaction amount with its income/expense sign."""

    sign = "+" if transaction_type == "Income" else "−"
    return f"{sign}{money(amount)}"