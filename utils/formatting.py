import math


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