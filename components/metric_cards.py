import html

import pandas as pd
import streamlit as st

from utils.formatting import render_badge


# -----------------------------
# Design tokens (shared by all components)
# -----------------------------

GREEN = "#34D399"
RED = "#FB7185"
AMBER = "#FBBF24"
BLUE = "#60A5FA"
MUTED = "#94A3B8"


# -----------------------------
# Small UI helpers
# -----------------------------

def collapse_html(text):
    """Collapse indentation so Markdown never treats HTML as code."""
    return " ".join(line.strip() for line in text.splitlines())


def go_to(page):
    """Button callback: switch the sidebar to another page."""
    st.session_state["nav_page"] = page


def spacer(height=16):
    st.markdown(
        f"<div style='height:{height}px'></div>",
        unsafe_allow_html=True,
    )


def pretty_month(month):
    """'2026-10' -> 'October 2026'. Falls back to the original text."""
    try:
        return pd.Period(month, "M").strftime("%B %Y")
    except Exception:
        return str(month)


def section_header(title, subtitle):
    st.markdown(
        collapse_html(
            f"""
            <div class="ss-section-title">{title}</div>
            <div class="ss-muted" style="margin-bottom:12px;">
                {subtitle}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def safe_float(value, default=0.0):
    """Convert to a float (handles None / NaN / bad values)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return default if number != number else number  # NaN check


def progress_bar_html(percent, color):
    """A slim rounded progress bar in any colour (returns HTML)."""
    width = min(max(percent, 0.0), 100.0)
    return collapse_html(
        f"""
        <div style="height:8px;border-radius:999px;margin-top:10px;
            background:rgba(148,163,184,0.15);overflow:hidden;">
            <div style="width:{width:.1f}%;height:100%;
                border-radius:999px;background:{color};"></div>
        </div>
        """
    )


def page_header(
    eyebrow,
    title,
    subtitle,
    period_label,
    period_value,
    period_note,
):
    """Page title on the left, period card on the right."""

    left, right = st.columns([3, 1], gap="large")

    with left:
        st.markdown(
            f'<div class="ss-eyebrow">{eyebrow}</div>'
            f'<div class="ss-page-title">{title}</div>'
            f'<div class="ss-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )

    with right:
        with st.container(border=True):
            st.caption(f"📅 {period_label}")
            st.markdown(
                collapse_html(
                    f"""
                    <div style="font-size:1.5rem;font-weight:800;
                        color:#F8FAFC;letter-spacing:-0.03em;">
                        {html.escape(period_value)}
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            st.caption(period_note)


# -----------------------------
# Cards
# -----------------------------

def delta_html(kind, current, previous, higher_is_good, money):
    """
    Small 'vs last month' line.
    kind: "percent", "amount" or "points".
    """

    placeholder = (
        '<div style="font-size:0.78rem;margin-top:6px;">&nbsp;</div>'
    )

    if previous is None:
        return placeholder

    if kind == "percent":
        if previous <= 0:
            return placeholder
        change = (current - previous) / previous * 100
        text = f"{abs(change):.1f}%"
    elif kind == "points":
        change = current - previous
        text = f"{abs(change):.1f} pts"
    else:
        change = current - previous
        text = money(abs(change))

    if abs(change) < 0.005:
        badge = render_badge(
            "• No change vs last month",
            bg_color="transparent",
            text_color=MUTED,
        )
        return (
            '<div style="font-size:0.78rem;margin-top:6px;">'
            f"{badge}</div>"
        )

    arrow = "▲" if change > 0 else "▼"
    is_good = (change > 0) == higher_is_good
    color = GREEN if is_good else RED
    badge = render_badge(
        f"{arrow} {text} vs last month",
        bg_color="transparent",
        text_color=color,
    )

    return (
        '<div style="margin-top:6px;">'
        f"{badge}</div>"
    )


def stat_card(
    icon,
    label,
    value,
    color,
    note,
    delta="",
    size="clamp(1.35rem, 2vw, 1.9rem)",
):
    """A bordered metric card with an icon, label, big value and note."""

    with st.container(border=True):
        st.caption(f"{icon} {label}")
        st.markdown(
            collapse_html(
                f"""
                <div style="font-size:{size};font-weight:800;
                    color:{color};letter-spacing:-0.04em;
                    overflow-wrap:anywhere;">{value}</div>
                <div style="color:{MUTED};font-size:0.78rem;
                    margin-top:8px;">{note}</div>
                {delta}
                """
            ),
            unsafe_allow_html=True,
        )