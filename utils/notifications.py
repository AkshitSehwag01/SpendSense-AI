import html
import json
import logging
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from streamlit.errors import StreamlitSecretNotFoundError

from auth import get_secret
from database import get_transactions, get_user_preferences
from domain.insights import detect_upcoming_bills
from utils.dates import today_local
from utils.formatting import money


logger = logging.getLogger(__name__)

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


def _post_telegram_message(message, token, chat_id):
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

    return _post_telegram_message(message, token, chat_id)


@st.cache_data(ttl=300, show_spinner=False, max_entries=256)
def get_upcoming_bill_due_dates(user_id, today=None):
    """Infer recurring utility bills due within three days from transaction history."""

    if user_id is None:
        raise ValueError("user_id is required to find upcoming bills.")

    return detect_upcoming_bills(
        get_transactions(user_id=user_id),
        today or today_local(),
    )


def _saved_telegram_credentials(user_id):
    preferences = get_user_preferences(user_id=user_id)
    encrypted_token = preferences.get("telegram_bot_token", "")
    chat_id = str(preferences.get("telegram_chat_id", "")).strip()
    if not encrypted_token or not chat_id:
        return None, None, (
            "Save your Telegram bot token and chat ID in Notification "
            "Settings first."
        )

    encryption_key = get_secret("NOTIFICATIONS_ENCRYPTION_KEY")
    if not encryption_key:
        return None, None, (
            "Telegram token decryption is unavailable. Check the "
            "notification encryption key in app secrets."
        )
    try:
        token = (
            Fernet(encryption_key.encode("ascii"))
            .decrypt(encrypted_token.encode("ascii"))
            .decode("utf-8")
        )
    except (ValueError, UnicodeEncodeError, InvalidToken, UnicodeDecodeError):
        logger.exception("Could not decrypt Telegram token for user %s", user_id)
        return None, None, (
            "The saved Telegram token could not be decrypted. Verify the "
            "notification encryption key."
        )

    return token, chat_id, None


def send_bill_due_reminders(user_id, bills=None, today=None, test=False):
    """Send upcoming bill reminders to the Telegram account saved by this user."""

    if user_id is None:
        raise ValueError("user_id is required to send bill reminders.")

    today = today or today_local()
    if test:
        reminder_date = today + timedelta(days=3)
        message = (
            "⏰ <b>Test bill reminder</b>\n"
            "Your Electricity Bill of approx "
            f"{html.escape(money(1250))} is due in 3 days on "
            f"{reminder_date:%d %b %Y}. Avoid late payment fees!"
        )
    else:
        bills = (
            get_upcoming_bill_due_dates(user_id, today=today)
            if bills is None
            else bills
        )
        if not bills:
            return True, "No recurring bills are due within the next 3 days."

        reminder_lines = ["<b>⏰ Upcoming bill reminders</b>"]
        for bill in bills:
            days_until_due = bill["days_until_due"]
            due_label = (
                "today"
                if days_until_due == 0
                else f"in {days_until_due} day"
                + ("s" if days_until_due != 1 else "")
            )
            reminder_lines.append(
                "⏰ Reminder: Your "
                f"{html.escape(str(bill['bill_type']))} Bill of approx "
                f"{html.escape(money(bill['amount']))} is due {due_label} "
                f"on {bill['due_date']:%d %b %Y}. "
                "Avoid late payment fees!"
            )
        message = "\n".join(reminder_lines)

    try:
        token, chat_id, credential_error = _saved_telegram_credentials(user_id)
    except Exception:
        logger.exception("Could not load Telegram settings for user %s", user_id)
        return False, "Could not load Telegram notification settings."
    if credential_error:
        return False, credential_error

    sent, detail = _post_telegram_message(message, token, chat_id)
    if sent:
        return True, (
            "Test bill reminder sent to Telegram."
            if test
            else "Bill due reminders sent to Telegram."
        )
    return sent, detail
