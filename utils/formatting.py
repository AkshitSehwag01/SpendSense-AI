import html
import math
import re


_CSS_COLOR_PATTERN = re.compile(
    r"(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{4}"
    r"|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8}"
    r"|transparent)\Z",
    re.IGNORECASE,
)


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