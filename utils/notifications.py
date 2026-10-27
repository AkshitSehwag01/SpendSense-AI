import html
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from utils.formatting import money


def format_weekly_digest(user_id, summary, top_categories, budget_alerts):
    """Build an HTML-formatted finance digest suitable for Telegram."""

    account_reference = html.escape(str(user_id))
    income = money(summary.get("income", 0))
    expenses = money(summary.get("expenses", 0))
    savings = money(summary.get("savings", 0))
    transaction_count = int(summary.get("transaction_count", 0) or 0)

    lines = [
        "<b>SpendSense AI · Weekly digest</b>",
        (
            f"<b>Period:</b> {html.escape(str(summary['period']))}"
            if summary.get("period")
            else ""
        ),
        f"Account reference: <code>{account_reference}</code>",
        "",
        f"<b>Income:</b> {html.escape(income)}",
        f"<b>Expenses:</b> {html.escape(expenses)}",
        f"<b>Net savings:</b> {html.escape(savings)}",
        f"<b>Transactions:</b> {transaction_count:,}",
        "",
        "<b>Top spending categories</b>",
    ]

    category_items = (
        top_categories.items()
        if isinstance(top_categories, dict)
        else top_categories or []
    )
    category_lines = []
    for item in category_items:
        if isinstance(top_categories, dict):
            category, amount = item
        elif isinstance(item, dict):
            category = item.get("category", "Other")
            amount = item.get("amount", 0)
        else:
            try:
                category, amount = item
            except (TypeError, ValueError):
                continue
        category_lines.append(
            f"• {html.escape(str(category))}: {html.escape(money(amount))}"
        )

    lines.extend(category_lines or ["No spending categories recorded."])
    lines.extend(["", "<b>Budget alerts</b>"])

    alert_lines = []
    for alert in budget_alerts or []:
        if isinstance(alert, dict):
            category = alert.get("category", "Category")
            spent = alert.get("spent", 0)
            budget = alert.get("budget", 0)
            alert_lines.append(
                f"• {html.escape(str(category))}: "
                f"{html.escape(money(spent))} spent of "
                f"{html.escape(money(budget))} budget"
            )
        else:
            alert_lines.append(f"• {html.escape(str(alert))}")
    lines.extend(alert_lines or ["No budget alerts."])

    return "\n".join(lines)


def send_telegram_message(message):
    """Send an HTML message to the Telegram chat configured in Streamlit secrets."""

    try:
        token = str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip()
        chat_id = str(st.secrets["TELEGRAM_CHAT_ID"]).strip()
    except (KeyError, TypeError, StreamlitSecretNotFoundError):
        return False, (
            "Telegram secrets are unavailable. Configure them in Streamlit "
            "secrets and try again."
        )

    if not token or not chat_id:
        return False, (
            "Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in "
            "Streamlit secrets to enable Telegram notifications."
        )

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError:
        return False, "Telegram rejected the message. Check the bot settings."
    except (URLError, TimeoutError):
        return False, "Could not reach Telegram. Check the connection and retry."
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, "Telegram returned an unreadable response."

    if not isinstance(result, dict) or result.get("ok") is not True:
        return False, "Telegram could not deliver the message."

    return True, "Summary sent to Telegram."
