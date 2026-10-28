import hashlib
import hmac
import math
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import streamlit as st

from database import (
    LOCAL_USER_ID,
    create_user,
    create_session,
    delete_session,
    delete_user_account,
    get_session,
    get_user,
    get_user_by_email,
    set_login_state,
    update_user_password,
)


# -----------------------------
# Settings
# -----------------------------

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 10

# scrypt cost settings (about 16 MB of memory per check)
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LENGTH = 32
_SCRYPT_MAX_MEMORY = 64 * 1024 * 1024

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

USER_CONTEXT_KEY = "user_context"

GENERIC_LOGIN_ERROR = "Incorrect email or password."

# "Keep me signed in" cookie
COOKIE_NAME = "spendsense_session"
SESSION_DAYS = 30


class NotAuthenticatedError(PermissionError):
    """Raised when data is requested without a signed-in user."""


def get_user_context():
    """Return the session's user-scoped state dictionary."""

    context = st.session_state.setdefault(USER_CONTEXT_KEY, {})
    if not isinstance(context, dict):
        raise RuntimeError("The session user context is invalid.")
    context.setdefault("currency_symbol", "₹")
    return context


# -----------------------------
# Secrets (environment first, then Streamlit secrets)
# -----------------------------

def get_secret(name):
    """A configured secret value, or an empty string."""

    value = os.environ.get(name, "").strip()

    if value:
        return value

    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def invite_code_required():
    """True when an INVITE_CODE secret is set (sign-up is invite-only)."""
    return bool(get_secret("INVITE_CODE"))


def _invite_code_is_valid(code):
    expected = get_secret("INVITE_CODE")

    if not expected:
        return True

    return hmac.compare_digest(
        str(code or "").strip().encode("utf-8"),
        expected.encode("utf-8"),
    )


# -----------------------------
# Login on / off
# -----------------------------

def login_required():
    """
    Login is ON by default (hosted mode).
    For local testing, set the environment variable
    SPENDSENSE_REQUIRE_LOGIN=0 to skip login and use the local account.
    """
    value = os.environ.get("SPENDSENSE_REQUIRE_LOGIN", "1")
    return value.strip().lower() not in ("0", "false", "no", "off")


# -----------------------------
# Password hashing (scrypt, built into Python)
# -----------------------------

def hash_password(password):
    salt = secrets.token_bytes(16)

    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_LENGTH,
        maxmem=_SCRYPT_MAX_MEMORY,
    )

    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}"
        f"${salt.hex()}${digest.hex()}"
    )


def verify_password(password, stored_hash):
    """True only if the password matches. Never raises."""

    try:
        scheme, n, r, p, salt_hex, hash_hex = stored_hash.split("$")

        if scheme != "scrypt":
            return False

        expected = bytes.fromhex(hash_hex)

        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=_SCRYPT_MAX_MEMORY,
        )

        return hmac.compare_digest(digest, expected)

    except Exception:
        return False


_dummy_hash_cache = []


def _dummy_hash():
    """Used so unknown emails take as long to check as real ones."""
    if not _dummy_hash_cache:
        _dummy_hash_cache.append(hash_password("not-a-real-password"))
    return _dummy_hash_cache[0]


# -----------------------------
# Validation
# -----------------------------

def clean_email(email):
    """Return a normalized email, or raise ValueError."""

    if not isinstance(email, str):
        raise ValueError("Please enter a valid email address.")

    email = email.strip().lower()

    if len(email) > 254 or not _EMAIL_PATTERN.match(email):
        raise ValueError("Please enter a valid email address.")

    return email


def check_password_rules(password):
    if not isinstance(password, str) or not password.strip():
        raise ValueError("Please enter a password.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer."
        )


# -----------------------------
# Sign up and sign in
# -----------------------------

def register_user(
    email,
    password,
    display_name="",
    accepted_terms=False,
    invite_code="",
):
    """Create an account and return the user. Raises ValueError."""

    if not _invite_code_is_valid(invite_code):
        raise ValueError("That invite code is not valid.")

    if not accepted_terms:
        raise ValueError(
            "Please accept the Terms of Service and Privacy Policy."
        )

    email = clean_email(email)
    check_password_rules(password)

    display_name = " ".join((display_name or "").split())[:50]

    user_id = create_user(
        email,
        hash_password(password),
        display_name,
        datetime.now(timezone.utc).isoformat(),
    )

    return get_user(user_id)


def delete_account(user_id, password):
    """
    Delete the signed-in user's account and all their data after
    checking their password. Returns (True, None) or (False, message).
    """

    user = get_user(user_id)

    if user is None:
        return False, "This account no longer exists."

    checked, error = authenticate(user["email"], password)

    if checked is None:
        return False, error or GENERIC_LOGIN_ERROR

    delete_user_account(user["id"])

    return True, None


def change_password(user_id, current_pw, new_pw):
    """Change a user's password after verifying the current password."""

    user = get_user(user_id)
    if user is None or user["id"] == LOCAL_USER_ID:
        return False, "This account no longer exists."

    checked, error = authenticate(user["email"], current_pw)
    if checked is None:
        return False, error or GENERIC_LOGIN_ERROR

    try:
        check_password_rules(new_pw)
    except ValueError as validation_error:
        return False, str(validation_error)

    if verify_password(new_pw, user["password_hash"]):
        return False, "Choose a password different from your current one."

    update_user_password(user["id"], hash_password(new_pw))
    return True, None


def _parse_time(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def authenticate(email, password):
    """
    Check an email and password.
    Returns (user, None) on success or (None, error message).
    The error never says whether the email exists.
    """

    try:
        email = clean_email(email)
    except ValueError:
        verify_password(str(password or ""), _dummy_hash())
        return None, GENERIC_LOGIN_ERROR

    if (
        not isinstance(password, str)
        or not password
        or len(password) > MAX_PASSWORD_LENGTH
    ):
        verify_password("x", _dummy_hash())
        return None, GENERIC_LOGIN_ERROR

    user = get_user_by_email(email)

    if user is None or user["id"] == LOCAL_USER_ID:
        verify_password(password, _dummy_hash())
        return None, GENERIC_LOGIN_ERROR

    now = datetime.now(timezone.utc)
    locked_until = _parse_time(user["locked_until"])

    if locked_until and locked_until > now:
        minutes = max(
            1, math.ceil((locked_until - now).total_seconds() / 60)
        )
        return None, (
            "Too many failed attempts. "
            f"Please try again in {minutes} minute(s)."
        )

    if verify_password(password, user["password_hash"]):
        if user["failed_attempts"] or user["locked_until"]:
            set_login_state(user["id"], 0, None)
        return user, None

    failed = int(user["failed_attempts"] or 0) + 1

    if failed >= MAX_FAILED_ATTEMPTS:
        lock_time = now + timedelta(minutes=LOCK_MINUTES)
        set_login_state(user["id"], 0, lock_time.isoformat())
    else:
        set_login_state(user["id"], failed, None)

    return None, GENERIC_LOGIN_ERROR


# -----------------------------
# Session
# -----------------------------

def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sign_in(user, remember=False):
    """
    Remember the user for this browser session.
    With remember=True, also create a long-lived session so a page
    refresh or a later visit does not ask for the password again.
    """

    name = user.get("display_name") or user["email"].split("@")[0]
    context = get_user_context()
    user_id = int(user["id"])
    if context.get("user_id") != user_id:
        context.clear()

    context.update(
        {
            "user_id": user_id,
            "user_email": user["email"],
            "user_name": name,
            "currency_symbol": context.get("currency_symbol", "₹"),
            "is_demo": False,
            "has_completed_onboarding": False,
            "onboarding_step": 1,
        }
    )

    if remember and login_required():
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)

        # Only a hash of the token is stored, like a password.
        create_session(user["id"], _hash_token(token), expires.isoformat())

        context["_session_token"] = token
        st.session_state["_cookie_action"] = (
            "set", token, SESSION_DAYS * 86400
        )


def restore_session():
    """
    If the browser has a valid 'stay signed in' cookie, sign the user in.
    Runs once per browser session and never raises.
    """

    context = get_user_context()
    if context.get("is_demo"):
        return

    if not login_required():
        return

    if context.get("user_id") is not None:
        return

    # A sign-out is waiting to clear the cookie: do not sign back in.
    pending = st.session_state.get("_cookie_action")

    if pending and pending[0] == "clear":
        return

    if st.session_state.get("_restore_tried"):
        return

    st.session_state["_restore_tried"] = True

    try:
        token = st.context.cookies.get(COOKIE_NAME, "")

        if not token or len(token) > 200:
            return

        record = get_session(_hash_token(token))

        if record is None:
            return

        expires = _parse_time(record["expires_at"])

        if expires is None or expires <= datetime.now(timezone.utc):
            delete_session(_hash_token(token))
            return

        user = get_user(record["user_id"])

        if user is None or user["id"] == LOCAL_USER_ID:
            return

        sign_in(user)
        get_user_context()["_session_token"] = token

    except Exception:
        # Never let a cookie problem stop the sign-in page from showing.
        return


def apply_cookie_actions():
    """
    Write or clear the browser cookie after a sign-in or sign-out.
    Call this at the end of a page run (it draws a hidden 0-height box).
    """

    action = st.session_state.pop("_cookie_action", None)

    if not action or not login_required():
        return

    if action[0] == "set":
        _, token, seconds = action
        value, max_age = token, int(seconds)
    else:
        value, max_age = "", 0

    script = f"""
    <script>
    (function () {{
        try {{
            var host = window.parent;
            var secure = host.location.protocol === "https:" ? "; Secure" : "";
            host.document.cookie = "{COOKIE_NAME}={value}; Max-Age={max_age}"
                + "; Path=/; SameSite=Lax" + secure;
        }} catch (error) {{}}
    }})();
    </script>
    """

    import streamlit.components.v1 as components

    components.html(script, height=0)


def sign_out():
    """
    Forget the user and every other saved page setting, and end the
    'stay signed in' session so the cookie stops working everywhere.
    """

    context = st.session_state.get(USER_CONTEXT_KEY)
    token = context.get("_session_token") if isinstance(context, dict) else None

    if token:
        try:
            delete_session(_hash_token(token))
        except Exception:
            pass

    st.session_state.clear()
    # This is the only retained key, needed to expire the browser cookie
    # on the following run; all user and widget state has been removed.
    st.session_state["_cookie_action"] = ("clear",)


def is_authenticated():
    context = get_user_context()
    if context.get("is_demo"):
        return True

    if not login_required():
        return True

    return context.get("user_id") is not None


def current_user_id():
    """The signed-in user's ID. Raises if nobody is signed in."""

    context = get_user_context()
    if context.get("is_demo"):
        return 0

    if not login_required():
        return LOCAL_USER_ID

    user_id = context.get("user_id")

    if user_id is None:
        raise NotAuthenticatedError("Please sign in to continue.")

    return int(user_id)


def current_user():
    """Name and email of the signed-in user, or None."""

    context = get_user_context()
    if context.get("is_demo"):
        user = context.get("user")
        if not isinstance(user, dict):
            return None
        return {
            "id": 0,
            "email": str(user.get("email", "guest@demo.spendsense.ai")),
            "name": str(user.get("name", "Demo User")),
        }

    if not login_required():
        return None

    if context.get("user_id") is None:
        return None

    return {
        "id": int(context["user_id"]),
        "email": context.get("user_email", ""),
        "name": context.get("user_name", ""),
    }