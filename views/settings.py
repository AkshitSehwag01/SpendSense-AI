import csv
import io
import logging
import zipfile

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken

from auth import (
    change_password,
    delete_account,
    get_secret,
    get_user_context,
    sign_out,
)
from database import (
    get_all_budgets,
    get_transactions,
    get_user_preferences,
    save_user_preferences,
)
from utils.notifications import send_bill_due_reminders
from utils.formatting import SUPPORTED_CURRENCIES


logger = logging.getLogger(__name__)

_TRANSACTION_FIELDS = (
    "id",
    "transaction_type",
    "amount",
    "category",
    "description",
    "transaction_date",
    "created_at",
)
_BUDGET_FIELDS = ("month", "category", "amount")


def _fernet():
    key = get_secret("NOTIFICATIONS_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "Configure NOTIFICATIONS_ENCRYPTION_KEY in the app secrets "
            "before saving a Telegram bot token."
        )

    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise RuntimeError(
            "NOTIFICATIONS_ENCRYPTION_KEY must be a valid Fernet key. "
            "Generate one with Fernet.generate_key()."
        ) from error


def _encrypt_token(token):
    if not token:
        return ""
    return _fernet().encrypt(token.encode("utf-8")).decode("ascii")


def _decrypt_token(encrypted_token):
    if not encrypted_token:
        return ""

    try:
        return (
            _fernet()
            .decrypt(encrypted_token.encode("ascii"))
            .decode("utf-8")
        )
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as error:
        raise RuntimeError(
            "The saved Telegram token could not be decrypted. Verify that "
            "NOTIFICATIONS_ENCRYPTION_KEY has not changed."
        ) from error


def _csv_text(rows, fields):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _build_backup_zip(user_id):
    transactions = get_transactions(user_id=user_id)
    budgets = get_all_budgets(user_id=user_id)

    archive = io.BytesIO()
    with zipfile.ZipFile(
        archive,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        zip_file.writestr(
            "transactions.csv",
            _csv_text(transactions, _TRANSACTION_FIELDS),
        )
        zip_file.writestr(
            "budgets.csv",
            _csv_text(budgets, _BUDGET_FIELDS),
        )
    return archive.getvalue()


def render_settings(user_id):
    st.title("Settings")
    st.caption("Manage account security, notifications, and your data.")

    try:
        preferences = get_user_preferences(user_id=user_id)
        saved_token = _decrypt_token(preferences["telegram_bot_token"])
    except Exception:
        logger.exception("Could not load preferences for user %s", user_id)
        st.error("Could not load notification preferences. Please try again.")
        preferences = {
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "currency_symbol": "₹",
        }
        saved_token = ""

    available_symbols = tuple(SUPPORTED_CURRENCIES.values())
    saved_currency_symbol = preferences.get("currency_symbol", "₹")
    if saved_currency_symbol not in available_symbols:
        saved_currency_symbol = SUPPORTED_CURRENCIES["INR"]
    st.session_state.setdefault("currency_selector", saved_currency_symbol)
    if st.session_state.get("currency_selector") not in available_symbols:
        st.session_state["currency_selector"] = saved_currency_symbol

    st.session_state.setdefault("settings_telegram_bot_token", saved_token)
    st.session_state.setdefault(
        "settings_telegram_chat_id",
        preferences["telegram_chat_id"],
    )

    account_tab, security_tab, notification_tab, data_tab = st.tabs(
        [
            "Account Settings",
            "Security & Password",
            "Notification Settings",
            "Data Export & Account Deletion",
        ]
    )

    with account_tab:
        st.subheader("Appearance")
        theme_mode = st.radio(
            "App Theme",
            options=("dark", "light"),
            format_func=lambda mode: (
                "🌙 Glassmorphic Dark"
                if mode == "dark"
                else "☀️ Enterprise Light"
            ),
            key="app_theme",
        )
        st.caption(
            "The selected theme is applied across the app and stays active "
            "for this browser session."
        )

        st.subheader("Display preferences")
        st.caption(
            "Amounts remain stored in INR. Display conversions use "
            "approximate fixed rates and are not live exchange quotes."
        )
        currency_symbol = st.selectbox(
            "Default Display Currency",
            options=available_symbols,
            format_func=lambda symbol: (
                f"{next(code for code, value in SUPPORTED_CURRENCIES.items() if value == symbol)} "
                f"({symbol})"
            ),
            key="currency_selector",
        )
        if currency_symbol != saved_currency_symbol:
            try:
                save_user_preferences(
                    preferences["telegram_bot_token"],
                    preferences["telegram_chat_id"],
                    user_id=user_id,
                    currency_symbol=currency_symbol,
                )
            except Exception:
                logger.exception(
                    "Could not save display currency for user %s",
                    user_id,
                )
                st.error(
                    "Could not save your display currency. Please try again."
                )
            else:
                saved_currency_symbol = currency_symbol
                context = get_user_context()
                context["currency_symbol"] = currency_symbol
                st.session_state["currency_symbol"] = currency_symbol
                preferences["currency_symbol"] = currency_symbol
                st.toast("Default display currency updated.", icon="💱")

    with security_tab:
        st.subheader("Change password")
        with st.form("settings_password_form", clear_on_submit=True):
            current_password = st.text_input(
                "Current password",
                type="password",
                key="settings_current_password",
            )
            new_password = st.text_input(
                "New password",
                type="password",
                key="settings_new_password",
            )
            confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="settings_confirm_password",
            )
            password_submitted = st.form_submit_button(
                "Update password",
                type="primary",
            )

        if password_submitted:
            if new_password != confirm_password:
                st.error("The new password and confirmation do not match.")
            else:
                try:
                    updated, message = change_password(
                        user_id,
                        current_password,
                        new_password,
                    )
                except Exception:
                    logger.exception(
                        "Could not change password for user %s", user_id
                    )
                    st.error("Could not update your password. Please try again.")
                else:
                    if updated:
                        st.toast("Password updated successfully.", icon="🔒")
                    else:
                        st.error(message or "Could not update your password.")

    with notification_tab:
        st.subheader("Telegram notifications")
        st.caption(
            "Your bot token is encrypted before it is stored. The encryption "
            "key must remain unchanged to keep saved credentials readable."
        )
        with st.form("settings_notification_form"):
            telegram_token = st.text_input(
                "Telegram bot token",
                type="password",
                key="settings_telegram_bot_token",
            )
            telegram_chat_id = st.text_input(
                "Telegram chat ID",
                key="settings_telegram_chat_id",
            )
            notification_submitted = st.form_submit_button(
                "Save notification settings",
                type="primary",
            )

        if notification_submitted:
            try:
                encrypted_token = _encrypt_token(telegram_token.strip())
                save_user_preferences(
                    encrypted_token,
                    telegram_chat_id.strip(),
                    user_id=user_id,
                )
            except Exception:
                logger.exception(
                    "Could not save notification preferences for user %s",
                    user_id,
                )
                st.error(
                    "Could not save notification settings. Please try again."
                )
            else:
                st.toast("Notification settings saved.", icon="🔔")

        if st.button(
            "Test Bill Reminder",
            key="settings_test_bill_reminder",
            help="Send a sample bill reminder to the saved Telegram chat.",
        ):
            try:
                sent, detail = send_bill_due_reminders(
                    user_id,
                    test=True,
                )
            except Exception:
                logger.exception(
                    "Could not send test bill reminder for user %s",
                    user_id,
                )
                st.error("Could not send the test reminder. Please try again.")
            else:
                if sent:
                    st.success(detail)
                else:
                    st.error(detail)

    with data_tab:
        st.subheader("Data export")
        st.download_button(
            "Download Full Backup (ZIP)",
            data=lambda: _build_backup_zip(user_id),
            file_name="spendsense-backup.zip",
            mime="application/zip",
            width="stretch",
            key="settings_download_backup",
        )

        st.divider()
        with st.expander("Danger Zone"):
            st.warning(
                "Deleting your account permanently removes your account, "
                "transactions, budgets, goals, and saved preferences."
            )
            with st.form(
                "settings_delete_account_form",
                clear_on_submit=True,
            ):
                confirmation = st.text_input(
                    'Type "DELETE" to confirm',
                    key="settings_delete_confirmation",
                )
                delete_password = st.text_input(
                    "Current password",
                    type="password",
                    key="settings_delete_password",
                )
                delete_submitted = st.form_submit_button(
                    "Delete account and data",
                    type="primary",
                )

            if delete_submitted:
                if confirmation != "DELETE":
                    st.error(
                        'Type "DELETE" exactly to confirm account deletion.'
                    )
                else:
                    try:
                        deleted, message = delete_account(
                            user_id,
                            delete_password,
                        )
                    except Exception:
                        logger.exception(
                            "Could not delete account for user %s", user_id
                        )
                        st.error(
                            "Could not delete your account. Please try again."
                        )
                    else:
                        if deleted:
                            sign_out()
                            st.session_state["auth_flash"] = (
                                "Your account and data were deleted."
                            )
                            st.rerun()
                        else:
                            st.error(message or "Could not delete your account.")
