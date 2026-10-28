import logging
import html
import re

import streamlit as st

from auth import (
    get_user_context,
    MIN_PASSWORD_LENGTH,
    authenticate,
    current_user,
    delete_account,
    invite_code_required,
    login_required,
    register_user,
    sign_in,
    sign_out,
)
from views.legal import render_legal_button


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
logger = logging.getLogger(__name__)

_LOGIN_CSS = """
.stApp {
    background: radial-gradient(
            ellipse at top right,
            #1A202C 0%,
            #000000 100%
        ),
        radial-gradient(
            ellipse at bottom left,
            rgba(217, 119, 6, 0.15) 0%,
            transparent 50%
        ) !important;
    background-attachment: fixed !important;
}

.block-container {
    max-width: 1120px;
    padding-top: clamp(2rem, 8vh, 6rem);
    padding-bottom: 3rem;
}

.stApp [data-testid="column"]:nth-of-type(2) {
    animation: fadeIn 500ms ease both;
}

.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="textarea"],
.stApp div[data-baseweb="select"] > div {
    background: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.stApp div[data-baseweb="input"]:focus-within,
.stApp div[data-baseweb="textarea"]:focus-within,
.stApp div[data-baseweb="select"] > div:focus-within {
    border-color: rgba(245, 158, 11, 0.5) !important;
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.2) !important;
}

.stApp input,
.stApp textarea {
    background: transparent !important;
    color: #F1F5F9 !important;
}

.stApp input::placeholder,
.stApp textarea::placeholder {
    color: rgba(203, 213, 225, 0.55) !important;
}

.stApp [data-testid="stButton"] > button,
.stApp [data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(90deg, #F59E0B, #D97706) !important;
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
    color: #000000 !important;
    font-weight: 800 !important;
    border: none !important;
    transition:
        transform 0.3s ease,
        box-shadow 0.3s ease,
        background-color 0.3s ease !important;
}

.stApp [data-testid="stButton"] > button:hover,
.stApp [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 25px -5px rgba(217, 119, 6, 0.6) !important;
}

.stApp [data-testid="stSegmentedControl"] [role="radiogroup"] {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 4px;
}

.stApp [data-testid="stSegmentedControl"] [role="radio"] {
    border-radius: 9px;
    color: #AAB8CA;
}

.stApp [data-testid="stSegmentedControl"]
[role="radio"][aria-checked="true"] {
    background: rgba(16, 185, 129, 0.18);
    color: #F1F5F9;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 767px) {
    .block-container {
        padding-top: 1.5rem;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }
}
"""


def _hide_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_brand():
    st.markdown(
        '<div class="ss-auth-header">'
        '<div class="ss-auth-logo" aria-hidden="true">✦</div>'
        '<div class="ss-auth-brand">SpendSense <span>AI</span></div>'
        '<h2 class="ss-auth-title">Welcome Back</h2>'
        '<p class="ss-auth-subtitle">'
        "Your private, intelligent financial workspace."
        "</p></div>",
        unsafe_allow_html=True,
    )


def _email_is_valid(email):
    return bool(_EMAIL_PATTERN.fullmatch(email.strip()))


def _render_email_feedback(email, creating_account=False):
    if not email:
        prompt = (
            "Enter an email address you can access."
            if creating_account
            else "Use the email address associated with your account."
        )
        st.caption(prompt)
    elif _email_is_valid(email):
        st.caption("Email address looks good.")
    else:
        st.caption("Enter a valid email address, such as you@example.com.")


def _login_error_message(error):
    message = str(error or "").casefold()

    if "too many failed attempts" in message or "locked" in message:
        return (
            "Sign-in is temporarily locked after several unsuccessful "
            "attempts. Please wait a few minutes before trying again."
        )

    if "rate limit" in message or "too many requests" in message:
        return "There have been too many attempts. Please wait and try again."

    if "incorrect email or password" in message:
        return (
            "We couldn't sign you in with those details. Check your email "
            "and password, then try again."
        )

    return "Sign-in is temporarily unavailable. Please try again shortly."


def _render_sign_in_tab():
    st.markdown(
        '<div class="ss-auth-form-heading">'
        "<strong>Sign in to your account</strong>"
        "<span>Continue to your private financial overview.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    email = st.text_input(
        "Email",
        placeholder="you@example.com",
        key="login_email",
    )
    _render_email_feedback(email)

    password = st.text_input(
        "Password",
        type="password",
        key="login_password",
    )

    remember = st.checkbox(
        "Keep me signed in on this device",
        value=False,
        key="login_remember_v2",
        help=(
            "When selected, a secure browser cookie keeps you signed in "
            "for up to 30 days."
        ),
    )

    if not st.button(
        "Sign in",
        key="login_submit",
        type="primary",
        width="stretch",
    ):
        return

    if not _email_is_valid(email):
        st.error("Enter a valid email address to sign in.")
        return

    try:
        user, error = authenticate(email, password)
    except Exception:
        logger.exception("Sign-in authentication failed")
        st.error(
            "Sign-in is temporarily unavailable. Please try again shortly."
        )
        return

    if error:
        st.error(_login_error_message(error))
        return

    sign_in(user, remember=remember)
    st.rerun()


def _render_sign_up_tab():
    needs_invite = invite_code_required()

    st.markdown(
        '<div class="ss-auth-form-heading">'
        "<strong>Create your account</strong>"
        "<span>Start building a clearer picture of your finances.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    name = st.text_input(
        "Your name (optional)",
        max_chars=50,
        key="signup_name",
    )

    email = st.text_input(
        "Email",
        placeholder="you@example.com",
        key="signup_email",
    )
    _render_email_feedback(email, creating_account=True)

    password = st.text_input(
        "Password",
        type="password",
        help=f"At least {MIN_PASSWORD_LENGTH} characters.",
        key="signup_password",
    )
    st.caption(
        f"Use at least {MIN_PASSWORD_LENGTH} characters."
        if len(password) < MIN_PASSWORD_LENGTH
        else "Minimum password length met."
    )

    confirm = st.text_input(
        "Confirm password",
        type="password",
        key="signup_confirm",
    )
    if confirm:
        st.caption(
            "Passwords match."
            if password == confirm
            else "Passwords do not match yet."
        )

    invite_code = ""

    if needs_invite:
        st.caption("Invite-only access is enabled. Ask your inviter for a code.")
        invite_code = st.text_input(
            "Invite code",
            type="password",
            key="signup_invite",
        )

    agreed = st.checkbox(
        "I have read and agree to the Terms of Service and "
        "Privacy Policy.",
        key="signup_agreed",
    )

    if not st.button(
        "Create account",
        key="signup_submit",
        type="primary",
        width="stretch",
    ):
        return

    if not _email_is_valid(email):
        st.error("Enter a valid email address to create your account.")
        return

    if len(password) < MIN_PASSWORD_LENGTH:
        st.error(
            f"Choose a password with at least {MIN_PASSWORD_LENGTH} "
            "characters."
        )
        return

    if password != confirm:
        st.error("The password and confirmation do not match.")
        return

    try:
        user = register_user(
            email,
            password,
            name,
            accepted_terms=agreed,
            invite_code=invite_code,
        )
    except ValueError as error:
        message = str(error)
        if "invite code" in message.casefold():
            message = (
                "That invite code could not be verified. Check it with "
                "the person who invited you."
            )
        elif "already exists" in message.casefold():
            message = (
                "An account with this email already exists. Sign in or use "
                "a different email address."
            )
        elif "terms" in message.casefold():
            message = "Please accept the Terms of Service and Privacy Policy."
        elif "email" in message.casefold():
            message = "Enter a valid email address to create your account."
        elif "password" in message.casefold():
            message = (
                f"Choose a password with at least {MIN_PASSWORD_LENGTH} "
                "characters."
            )
        st.error(message)
        return
    except Exception:
        st.error(
            "We couldn't create your account right now. Please try again "
            "shortly."
        )
        return

    sign_in(user)
    st.rerun()


def render_login():
    """Full-page sign-in / create-account screen."""

    _hide_sidebar()
    st.markdown(
        f"<style>{_LOGIN_CSS}</style>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        _render_brand()

        flash = st.session_state.pop("auth_flash", None)

        if flash:
            st.success(flash)

        auth_mode = st.segmented_control(
            "Account access",
            ["Sign In", "Create Account"],
            default="Sign In",
            label_visibility="collapsed",
            key="login_mode",
        )

        if auth_mode == "Create Account":
            _render_sign_up_tab()
        else:
            _render_sign_in_tab()

        st.divider()
        render_legal_button(
            "auth_legal_button",
            "Privacy Policy · Terms of Service",
        )
        if st.button(
            "🚀 Explore Demo Mode (No Sign-Up Required)",
            key="explore_demo_mode",
            width="stretch",
        ):
            context = get_user_context()
            context.update(
                {
                    "user_id": 0,
                    "user_name": "Demo User",
                    "user_email": "guest@demo.spendsense.ai",
                    "currency_symbol": "₹",
                    "is_demo": True,
                    "user": {
                        "id": 0,
                        "name": "Demo User",
                        "email": "guest@demo.spendsense.ai",
                    },
                }
            )
            st.rerun()

        st.caption(
            "Passwords are stored as secure one-way hashes. "
            "SpendSense AI staff cannot see them."
        )


def _render_delete_account(user):
    with st.expander("Delete my account"):
        st.caption(
            "This permanently deletes your account, transactions and "
            "budgets. It cannot be undone. Download your data from the "
            "Reports page first if you want a copy."
        )

        password = st.text_input(
            "Confirm with your password",
            type="password",
            key="delete_account_password",
        )

        if st.button(
            "Delete everything",
            key="delete_account_button",
            use_container_width=True,
        ):
            ok, message = delete_account(user["id"], password)

            if not ok:
                st.error(message)
                return

            sign_out()
            st.session_state["auth_flash"] = (
                "Your account and all its data have been deleted."
            )
            st.rerun()


def render_account_box():
    """Signed-in name, legal link, account deletion and Log out."""

    context = get_user_context()
    if context.get("is_demo"):
        user = context.get("user", {})
        with st.sidebar:
            st.divider()
            st.caption("EXPLORING DEMO MODE")
            st.markdown(
                f'<div style="font-weight:700;color:#F1F5F9;">'
                f'{html.escape(str(user.get("name", "Demo User")))}</div>'
            )
            if st.button(
                "Exit demo",
                key="exit_demo_button",
                width="stretch",
            ):
                sign_out()
                st.rerun()
        return

    if not login_required():
        return

    user = current_user()

    if not user:
        return

    with st.sidebar:
        st.divider()

        st.caption("SIGNED IN AS")

        st.markdown(
            f'<div style="font-weight:700;color:#F1F5F9;">'
            f'{html.escape(user["name"])}</div>'
            f'<div style="font-size:0.8rem;color:#94A3B8;'
            f'overflow-wrap:anywhere;">{html.escape(user["email"])}</div>',
            unsafe_allow_html=True,
        )

        render_legal_button("sidebar_legal_button")

        _render_delete_account(user)

        if st.button(
            "Log out",
            key="logout_button",
            use_container_width=True,
        ):
            sign_out()
            st.rerun()