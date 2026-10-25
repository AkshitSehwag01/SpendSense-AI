import html

import streamlit as st

from auth import (
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
        '<div class="ss-eyebrow">SPENDSENSE AI</div>'
        '<div class="ss-page-title">Welcome back.</div>'
        '<div class="ss-subtitle">'
        "Sign in to see your own money, budgets and insights. "
        "Your data stays private to your account."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='height:14px'></div>",
        unsafe_allow_html=True,
    )


def _render_sign_in_tab():
    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        remember = st.checkbox(
            "Keep me signed in on this device",
            value=True,
            key="login_remember",
        )

        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True,
        )

    if not submitted:
        return

    user, error = authenticate(email, password)

    if error:
        st.error(error)
        return

    sign_in(user, remember=remember)
    st.rerun()


def _render_sign_up_tab():
    needs_invite = invite_code_required()

    with st.form("signup_form"):
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

        password = st.text_input(
            "Password",
            type="password",
            help=f"At least {MIN_PASSWORD_LENGTH} characters.",
            key="signup_password",
        )

        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm",
        )

        invite_code = ""

        if needs_invite:
            invite_code = st.text_input(
                "Invite code",
                type="password",
                help="Ask the person who shared SpendSense AI with you.",
                key="signup_invite",
            )

        agreed = st.checkbox(
            "I have read and agree to the Terms of Service and "
            "Privacy Policy.",
            key="signup_agreed",
        )

        submitted = st.form_submit_button(
            "Create account",
            use_container_width=True,
        )

    render_legal_button("signup_legal_button", "Read the Privacy Policy & Terms")

    if not submitted:
        return

    if password != confirm:
        st.error("The two passwords do not match.")
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
        st.error(str(error))
        return
    except Exception:
        st.error(
            "Your account could not be created. "
            "Please try again in a moment."
        )
        return

    sign_in(user, remember=True)
    st.rerun()


def render_login():
    """Full-page sign-in / create-account screen."""

    _hide_sidebar()

    _, center, _ = st.columns([1, 1.5, 1])

    with center:
        _render_brand()

        flash = st.session_state.pop("auth_flash", None)

        if flash:
            st.success(flash)

        with st.container(border=True):
            sign_in_tab, sign_up_tab = st.tabs(
                ["Sign in", "Create account"]
            )

            with sign_in_tab:
                _render_sign_in_tab()

            with sign_up_tab:
                _render_sign_up_tab()

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