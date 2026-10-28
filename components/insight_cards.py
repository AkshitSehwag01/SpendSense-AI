import re
from html import escape

import streamlit as st


# level -> (icon, accent colour, background tint)
LEVEL_STYLES = {
    "danger": ("🚨", "var(--danger)", "color-mix(in srgb, var(--danger) 10%, transparent)"),
    "warning": ("⚠️", "var(--warning)", "color-mix(in srgb, var(--warning) 10%, transparent)"),
    "success": ("✅", "var(--success)", "color-mix(in srgb, var(--success) 10%, transparent)"),
    "info": ("💡", "var(--info)", "color-mix(in srgb, var(--info) 10%, transparent)"),
}

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _format_text(text):
    """Escape HTML, then keep **bold** and line breaks."""
    safe = escape(str(text or ""))
    safe = _BOLD.sub(r"<strong>\1</strong>", safe)
    return safe.replace("\n", "<br>")


def show_insights(insights):
    """Display financial insights as premium cards."""

    if not insights:
        st.info("No insights yet. Add a few transactions to get started.")
        return

    for item in insights:
        level = item.get("level", "info")
        icon, accent, tint = LEVEL_STYLES.get(level, LEVEL_STYLES["info"])

        title = _format_text(item.get("title", ""))
        message = _format_text(item.get("message", ""))

        st.markdown(
            "".join([
                f'<div style="display:flex;gap:14px;align-items:flex-start;'
                f"padding:14px 16px;margin-bottom:10px;border-radius:14px;"
                f"border:1px solid var(--border);"
                f"border-left:4px solid {accent};background:{tint};\">",
                f'<div style="font-size:1.25rem;line-height:1.4;">{icon}</div>',
                "<div>",
                f'<div style="font-weight:700;color:var(--text);">{title}</div>',
                f'<div style="font-size:0.88rem;color:var(--text-muted);'
                f'margin-top:3px;line-height:1.5;">{message}</div>',
                "</div>",
                "</div>",
            ]),
            unsafe_allow_html=True,
        )