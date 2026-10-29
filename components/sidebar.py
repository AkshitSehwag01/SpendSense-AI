from datetime import datetime
import html

import streamlit as st

from auth import current_user, get_user_context, sign_out

PAGES = [
    "Dashboard",
    "Add Transaction",
    "Transactions",
    "Budget Planner",
    "Goals",
    "Financial Insights",
    "Reports",
    "Settings",
]

PAGE_ICONS = {
    "Dashboard": ":material/dashboard:",
    "Add Transaction": ":material/add_circle:",
    "Transactions": ":material/receipt_long:",
    "Budget Planner": ":material/pie_chart:",
    "Goals": ":material/flag:",
    "Financial Insights": ":material/lightbulb:",
    "Reports": ":material/assessment:",
    "Settings": ":material/settings:",
}

DOCK_PAGES = {
    "Overview": "Dashboard",
    "Transactions": "Transactions",
    "Budgets": "Budget Planner",
    "Goals": "Goals",
    "Insights": "Financial Insights",
    "Reports": "Reports",
}

DOCK_ICONS = {
    "Overview": ":material/dashboard:",
    "Transactions": ":material/receipt_long:",
    "Budgets": ":material/pie_chart:",
    "Goals": ":material/flag:",
    "Insights": ":material/lightbulb:",
    "Reports": ":material/assessment:",
}


def _go_to(page):
    """Button callback: switch to another page."""
    st.session_state["nav_page"] = page


def _sync_sidebar_theme():
    st.session_state["app_theme"] = (
        "light" if st.session_state["sidebar_theme_toggle"] else "dark"
    )


def _sync_topbar_theme():
    mode = "light" if st.session_state["topbar_theme_toggle"] else "dark"
    st.session_state["app_theme"] = mode
    st.session_state["sidebar_theme_toggle"] = mode == "light"


def _month_label(month):
    """Show 2026-10 as October 2026."""
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    except (TypeError, ValueError):
        return str(month)


def render_sidebar(available_months):
    """Render SpendSense AI's sidebar navigation and month selector."""

    with st.sidebar:
        page = st.session_state.get("nav_page", "Dashboard")
        st.markdown(
            '<div class="ss-rail-brand" title="SpendSense AI">'
            '<span class="ss-rail-logo">₹</span></div>',
            unsafe_allow_html=True,
        )

        with st.container(key="rail_quick_add"):
            st.button(
                ":material/add_circle:",
                key="sidebar_quick_add",
                on_click=_go_to,
                args=("Add Transaction",),
                help="Quick add transaction",
            )

        for nav_page in PAGES:
            slug = nav_page.casefold().replace(" ", "_")
            active = st.session_state.get("nav_page", "Dashboard") == nav_page
            key = f"rail_{slug}_{'active' if active else 'item'}"
            with st.container(key=key):
                st.button(
                    PAGE_ICONS[nav_page],
                    key=f"rail_button_{slug}",
                    on_click=_go_to,
                    args=(nav_page,),
                    help=nav_page,
                )

        with st.popover(":material/calendar_month:", key="rail_period", help="Analysis period"):
            selected_month = st.selectbox(
                "Analysis period",
                available_months,
                format_func=_month_label,
                label_visibility="collapsed",
                key="analysis_month",
            )

        if "analysis_month" not in st.session_state:
            st.session_state["analysis_month"] = available_months[0]
        selected_month = st.session_state["analysis_month"]

    return page, selected_month


def render_topbar():
    """Render the glass header with greeting, theme, and account menu."""

    context = get_user_context()
    user = current_user() or {}
    name = str(user.get("name") or context.get("user_name") or "there")
    first_name = name.split()[0] if name.split() else "there"
    greeting = "Good morning" if datetime.now().hour < 12 else (
        "Good afternoon" if datetime.now().hour < 18 else "Good evening"
    )

    with st.container(key="topbar"):
        left, right = st.columns([4, 1], vertical_alignment="center")
        with left:
            st.markdown(
                f'<div class="ss-topbar-greeting">{greeting}, '
                f'<strong>{html.escape(first_name)}</strong></div>',
                unsafe_allow_html=True,
            )
        with right:
            theme_col, account_col = st.columns(
                [3, 1], gap="small", vertical_alignment="center"
            )
            with theme_col:
                theme_value = (
                    st.session_state.get("app_theme", "dark") == "light"
                )
                st.toggle(
                    "☀ Light" if not theme_value else "🌙 Dark",
                    value=theme_value,
                    key="topbar_theme_toggle",
                    on_change=_sync_topbar_theme,
                    help="Switch between Glassmorphic Dark and Enterprise Light",
                )
            with account_col:
                with st.popover(
                    ":material/account_circle:",
                    key="topbar_account",
                    help="Account menu",
                ):
                    st.markdown(f"**{name}**")
                    st.caption(str(user.get("email", "")))
                    if st.button("Log out", key="topbar_logout"):
                        sign_out()
                        st.rerun()


def render_bottom_dock(page):
    """Render fixed primary navigation at the bottom of the viewport."""

    with st.container(key="bottom_dock"):
        columns = st.columns(len(DOCK_PAGES), gap="small")
        for column, (label, target) in zip(columns, DOCK_PAGES.items()):
            active = page == target
            slug = label.casefold()
            with column:
                with st.container(
                    key=f"dock_{slug}_{'active' if active else 'item'}"
                ):
                    st.button(
                        f"{DOCK_ICONS[label]} {label}",
                        key=f"dock_button_{slug}",
                        on_click=_go_to,
                        args=(target,),
                        help=label,
                    )