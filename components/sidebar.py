from datetime import datetime

import streamlit as st

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
    "Dashboard": ":material/home:",
    "Add Transaction": ":material/add_circle:",
    "Transactions": ":material/list:",
    "Budget Planner": ":material/pie_chart:",
    "Goals": ":material/flag:",
    "Financial Insights": ":material/lightbulb:",
    "Reports": ":material/bar_chart:",
    "Settings": ":material/settings:",
}


def _go_to(page):
    """Button callback: switch to another page."""
    st.session_state["nav_page"] = page


def _sync_sidebar_theme():
    st.session_state["app_theme"] = (
        "light" if st.session_state["sidebar_theme_toggle"] else "dark"
    )


def _page_label(page):
    return f"{PAGE_ICONS[page]}  {page}"


def _month_label(month):
    """Show 2026-10 as October 2026."""
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    except (TypeError, ValueError):
        return str(month)


def render_sidebar(available_months):
    """Render SpendSense AI's sidebar navigation and month selector."""

    st.sidebar.markdown(
        '<div class="ss-brand">'
        '<div class="ss-brand-logo">💸</div>'
        "<div>"
        '<div class="ss-brand-name">SpendSense AI</div>'
        '<div class="ss-brand-tag">Personal Finance Intelligence</div>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.sidebar.button(
        ":material/add_circle:  Quick add",
        key="sidebar_quick_add",
        on_click=_go_to,
        args=("Add Transaction",),
        use_container_width=True,
    )

    st.sidebar.toggle(
        "☀️ Light mode",
        value=st.session_state.get("app_theme", "dark") == "light",
        key="sidebar_theme_toggle",
        on_change=_sync_sidebar_theme,
        help="Switch between Enterprise Light and Glassmorphic Dark.",
    )

    st.sidebar.markdown(
        '<div class="ss-side-label">Menu</div>',
        unsafe_allow_html=True,
    )

    page = st.sidebar.radio(
        "Navigation",
        PAGES,
        key="nav_page",
        format_func=_page_label,
        label_visibility="collapsed",
    )

    st.sidebar.markdown(
        '<div class="ss-side-label">Analysis period</div>',
        unsafe_allow_html=True,
    )

    selected_month = st.sidebar.selectbox(
        "Select month",
        available_months,
        format_func=_month_label,
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.caption("Track smarter. Save better.")

    return page, selected_month