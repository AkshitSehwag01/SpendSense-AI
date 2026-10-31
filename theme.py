"""Theme tokens and chart styling shared by the Streamlit application."""

import streamlit as st


DARK = {
    "bg": "#0B1120",
    "surface": "#111B2D",
    "surface_2": "#172235",
    "border": "#2A3B52",
    "text": "#F8FAFC",
    "text_muted": "#AAB8CA",
    "accent": "#10B981",
    "accent_soft": "#163D3A",
    "success": "#34D399",
    "danger": "#FB7185",
    "warning": "#FBBF24",
    "info": "#38BDF8",
    "shadow": "rgba(2, 6, 23, 0.18)",
    "shadow_soft": "rgba(2, 6, 23, 0.28)",
    "accent_glow": "rgba(16, 185, 129, 0.10)",
    "radius": "14px",
    "grid": "#2A3B52",
    "hover": "#1D2B42",
    "input": "#0F1829",
    "on_accent": "#052E22",
}

LIGHT = {
    "bg": "#F7F8FA",
    "surface": "#FFFFFF",
    "surface_2": "#F1F5F9",
    "border": "#D7E0EA",
    "text": "#0F172A",
    "text_muted": "#475569",
    "accent": "#047857",
    "accent_soft": "#D1FAE5",
    "success": "#047857",
    "danger": "#BE123C",
    "warning": "#A16207",
    "info": "#0369A1",
    "shadow": "rgba(15, 23, 42, 0.08)",
    "shadow_soft": "rgba(15, 23, 42, 0.04)",
    "accent_glow": "rgba(4, 120, 87, 0.06)",
    "radius": "14px",
    "grid": "#D7E0EA",
    "hover": "#ECFDF5",
    "input": "#FFFFFF",
    "on_accent": "#FFFFFF",
}


def current_palette():
    """Return the palette selected in session state."""

    return LIGHT if st.session_state.get("app_theme", "dark") == "light" else DARK


def _css_vars(palette):
    variables = {
        **palette,
        "primary": palette["accent"],
    }
    return "\n".join(
        f"    --{key.replace('_', '-')}: {value};"
        for key, value in variables.items()
    )


def theme_css(palette=None):
    """Build a token-based stylesheet without Streamlit DOM selectors."""

    palette = palette or current_palette()
    return f"""
:root {{
{_css_vars(palette)}
    --font-body: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
    --font-heading: "Space Grotesk", Inter, sans-serif;
    --font-mono: "JetBrains Mono", Consolas, monospace;
}}

html, body, .stApp {{
    color: var(--text);
    background: var(--bg);
    font-family: var(--font-body);
}}

.stApp {{
    background:
        radial-gradient(800px 360px at 100% 0%, var(--accent-glow), transparent 70%),
        var(--bg);
}}

.block-container {{
    padding-bottom: 80px;
}}

h1, h2, h3, h4, .ss-page-title, .ss-section-title {{
    color: var(--text);
    font-family: var(--font-heading);
}}

p, label, li {{
    color: var(--text-muted);
}}

a {{
    color: var(--accent);
}}

hr {{
    border-color: var(--border);
}}

.ss-hero-card,
.ss-recurring-card {{
    border-color: var(--border);
    background: var(--surface);
    box-shadow: 0 10px 28px var(--shadow);
}}

.ss-hero-value,
.ss-money,
.ss-goal-ring span {{
    color: var(--text);
    font-family: var(--font-mono);
}}

.ss-eyebrow,
.ss-income,
.ss-delta-chip.success,
.ss-budget-caption--ok {{
    color: var(--success);
}}

.ss-expense,
.ss-delta-chip.danger,
.ss-budget-caption--danger {{
    color: var(--danger);
}}

.ss-delta-chip,
.ss-pill,
.ss-category-icon {{
    background: var(--accent-soft);
    color: var(--accent);
}}

.ss-sparkline-line {{
    stroke: var(--accent);
}}

.ss-sparkline-base {{
    stroke: var(--border);
}}

.ss-budget-track {{
    background: var(--surface-2);
}}

.ss-budget-fill--ok {{
    background: var(--success);
}}

.ss-budget-fill--warning,
.ss-budget-caption--warning {{
    background: var(--warning);
    color: var(--warning);
}}

.ss-budget-fill--danger {{
    background: var(--danger);
}}

.ss-goal-ring {{
    background: conic-gradient(
        var(--accent) var(--goal-progress),
        var(--surface-2) 0
    );
}}

@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }}
}}
"""


def apply_theme():
    """Inject token variables and component rules on every rerun."""

    st.markdown(
        f"<style>{theme_css()}</style>",
        unsafe_allow_html=True,
    )


def chart_layout(theme=None):
    """Return Plotly layout tokens shared by every chart."""

    palette = theme or current_palette()
    return {
        "paper_bgcolor": palette["surface"],
        "plot_bgcolor": palette["surface"],
        "font": {
            "family": "Plus Jakarta Sans, sans-serif",
            "color": palette["text"],
            "size": 12,
        },
        "legend": {"font": {"color": palette["text"]}},
        "hoverlabel": {
            "bgcolor": palette["surface"],
            "bordercolor": palette["border"],
            "font": {"color": palette["text"]},
        },
        "xaxis": {
            "color": palette["text_muted"],
            "gridcolor": palette["grid"],
            "linecolor": palette["border"],
            "tickfont": {"color": palette["text_muted"]},
        },
        "yaxis": {
            "color": palette["text_muted"],
            "gridcolor": palette["grid"],
            "linecolor": palette["border"],
            "tickfont": {"color": palette["text_muted"]},
        },
    }


def contrast_ratio(foreground, background):
    """Calculate WCAG contrast ratio for #RRGGBB colors."""

    def luminance(value):
        channels = [
            int(value[index : index + 2], 16) / 255
            for index in (1, 3, 5)
        ]
        channels = [
            channel / 12.92
            if channel <= 0.03928
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return (
            0.2126 * channels[0]
            + 0.7152 * channels[1]
            + 0.0722 * channels[2]
        )

    high = max(luminance(foreground), luminance(background))
    low = min(luminance(foreground), luminance(background))
    return (high + 0.05) / (low + 0.05)


def check_contrast():
    """Print any body/heading token pairs below WCAG AA."""

    for name, palette in (("dark", DARK), ("light", LIGHT)):
        for foreground in ("text", "text_muted"):
            ratio = contrast_ratio(palette[foreground], palette["bg"])
            if ratio < 4.5:
                print(
                    f"WCAG AA failure: {name} {foreground} "
                    f"against bg = {ratio:.2f}:1"
                )


if __name__ == "__main__":
    check_contrast()
