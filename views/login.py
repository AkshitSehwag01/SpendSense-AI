import html

import streamlit as st

from auth import (
    MIN_PASSWORD_LENGTH,
    authenticate,
    current_user,
    login_required,
    register_user,
    sign_in,
    sign_out,
)


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

    sign_in(user)
    st.rerun()


def _render_sign_up_tab():
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

        submitted = st.form_submit_button(
            "Create account",
            use_container_width=True,
        )

    if not submitted:
        return

    if password != confirm:
        st.error("The two passwords do not match.")
        return

    try:
        user = register_user(email, password, name)
    except ValueError as error:
        st.error(str(error))
        return
    except Exception:
        st.error(
            "Your account could not be created. "
            "Please try again in a moment."
        )
        return

    sign_in(user)
    st.rerun()


def render_login():
    """Full-page sign-in / create-account screen."""

    _hide_sidebar()

    _, center, _ = st.columns([1, 1.5, 1])

    with center:
        _render_brand()

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


def render_account_box():
    """Signed-in name and Log out button at the bottom of the sidebar."""

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

        if st.button(
            "Log out",
            key="logout_button",
            use_container_width=True,
        ):
            sign_out()
            st.rerun()