"""Reusable glassmorphic presentation components."""

import html
import math
import re

import streamlit as st


_TOKEN_COLOR = re.compile(r"var\(--[A-Za-z][A-Za-z0-9_-]*\)\Z")
_TONE_CLASSES = {
    "default": "ss-glass-chip-default",
    "success": "ss-glass-chip-success",
    "danger": "ss-glass-chip-danger",
    "warning": "ss-glass-chip-warning",
    "info": "ss-glass-chip-info",
}


def _escape(value):
    return html.escape(str(value), quote=True)


def _compact_html(value):
    return " ".join(line.strip() for line in value.splitlines())


def _token_color(value):
    color = str(value)
    if not _TOKEN_COLOR.fullmatch(color):
        raise ValueError("Glass component colors must use a theme token.")
    return color


def _safe_percent(value):
    try:
        percent = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Progress percent must be numeric.") from error
    if not math.isfinite(percent):
        raise ValueError("Progress percent must be finite.")
    return min(max(percent, 0.0), 100.0)


def glass_card(content, class_name=""):
    """Render an escaped-class, token-driven glass card."""

    classes = "ss-glass-card"
    if class_name:
        classes += f" {_escape(class_name)}"
    st.markdown(
        _compact_html(
            f"""
            <div class="{classes}">
                {content}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def kpi_card(title, value, delta="", icon="", sparkline=None):
    """Render a large KPI card with an optional sparkline."""

    sparkline_html = ""
    if sparkline:
        values = [float(point) for point in sparkline]
        if not all(math.isfinite(point) for point in values):
            raise ValueError("Sparkline values must be finite numbers.")
        if len(values) > 1:
            low, high = min(values), max(values)
            span = high - low or 1.0
            points = " ".join(
                f"{index * 100 / (len(values) - 1):.1f},"
                f"{42 - ((point - low) / span) * 32:.1f}"
                for index, point in enumerate(values)
            )
            sparkline_html = (
                '<svg class="ss-glass-sparkline" viewBox="0 0 100 48" '
                'role="img" aria-label="KPI trend">'
                '<polyline points="0,44 100,44" '
                'class="ss-sparkline-base"></polyline>'
                f'<polyline points="{points}" '
                'class="ss-sparkline-line"></polyline></svg>'
            )

    delta_html = (
        f'<div class="ss-glass-kpi-delta">{_escape(delta)}</div>'
        if delta
        else ""
    )
    glass_card(
        _compact_html(
            f"""
            <div class="ss-glass-kpi">
                <div class="ss-glass-kpi-copy">
                    <div class="ss-glass-kpi-label">
                        <span class="ss-glass-kpi-icon">{_escape(icon)}</span>
                        {_escape(title)}
                    </div>
                    <div class="ss-glass-kpi-value">{_escape(value)}</div>
                    {delta_html}
                </div>
                {sparkline_html}
            </div>
            """
        )
    )


def progress_ring(percent, label):
    """Render a token-colored circular progress indicator."""

    value = _safe_percent(percent)
    glass_card(
        _compact_html(
            f"""
            <div class="ss-glass-progress">
                <div class="ss-glass-ring"
                    style="--ring-progress:{value:.1f}%;"
                    role="img"
                    aria-label="{_escape(value):}% complete">
                    <span>{value:.0f}%</span>
                </div>
                <div class="ss-glass-progress-label">{_escape(label)}</div>
            </div>
            """
        )
    )


def donut_legend_row(label, value, color="var(--accent)"):
    """Render one accessible legend row for a donut chart."""

    safe_color = _token_color(color)
    glass_card(
        _compact_html(
            f"""
            <div class="ss-glass-legend-row">
                <span class="ss-glass-legend-label">
                    <span class="ss-glass-legend-dot"
                        style="background:{safe_color};"></span>
                    {_escape(label)}
                </span>
                <strong class="ss-glass-legend-value">{_escape(value)}</strong>
            </div>
            """
        )
    )


def pill_button(label, icon="", tone="default"):
    """Render a compact, non-interactive pill action or status control."""

    try:
        tone_class = _TONE_CLASSES[tone]
    except KeyError as error:
        raise ValueError(f"Unknown pill tone: {tone}") from error
    st.markdown(
        _compact_html(
            f"""
            <span class="ss-glass-pill {tone_class}">
                <span class="ss-glass-pill-icon">{_escape(icon)}</span>
                {_escape(label)}
            </span>
            """
        ),
        unsafe_allow_html=True,
    )


def chip(label, tone="default"):
    """Render a compact status chip."""

    pill_button(label, tone=tone)


def section_header(title, subtitle=""):
    """Render a token-driven section heading."""

    subtitle_html = (
        f'<div class="ss-glass-section-subtitle">{_escape(subtitle)}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        _compact_html(
            f"""
            <div class="ss-glass-section-header">
                <div class="ss-glass-section-title">{_escape(title)}</div>
                {subtitle_html}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def empty_state(title, message, icon="○"):
    """Render a calm empty state for cards and dashboard sections."""

    glass_card(
        _compact_html(
            f"""
            <div class="ss-glass-empty-state">
                <div class="ss-glass-empty-icon">{_escape(icon)}</div>
                <div class="ss-glass-empty-title">{_escape(title)}</div>
                <div class="ss-glass-empty-message">{_escape(message)}</div>
            </div>
            """
        )
    )
