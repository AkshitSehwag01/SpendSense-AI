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
    get_user,
    get_user_by_email,
    set_login_state,
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

_SESSION_KEYS = ("user_id", "user_email", "user_name")

GENERIC_LOGIN_ERROR = "Incorrect email or password."


class NotAuthenticatedError(PermissionError):
    """Raised when data is requested without a signed-in user."""


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

def register_user(email, password, display_name=""):
    """Create an account and return the user. Raises ValueError."""

    email = clean_email(email)
    check_password_rules(password)

    display_name = " ".join((display_name or "").split())[:50]

    user_id = create_user(email, hash_password(password), display_name)

    return get_user(user_id)


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

def sign_in(user):
    """Remember the user for this browser session."""

    name = user.get("display_name") or user["email"].split("@")[0]

    st.session_state["user_id"] = int(user["id"])
    st.session_state["user_email"] = user["email"]
    st.session_state["user_name"] = name


def sign_out():
    """Forget the user and every other saved page setting."""
    st.session_state.clear()


def is_authenticated():
    if not login_required():
        return True

    return st.session_state.get("user_id") is not None


def current_user_id():
    """The signed-in user's ID. Raises if nobody is signed in."""

    if not login_required():
        return LOCAL_USER_ID

    user_id = st.session_state.get("user_id")

    if user_id is None:
        raise NotAuthenticatedError("Please sign in to continue.")

    return int(user_id)


def current_user():
    """Name and email of the signed-in user, or None."""

    if not login_required():
        return None

    if st.session_state.get("user_id") is None:
        return None

    return {
        "id": int(st.session_state["user_id"]),
        "email": st.session_state.get("user_email", ""),
        "name": st.session_state.get("user_name", ""),
    }