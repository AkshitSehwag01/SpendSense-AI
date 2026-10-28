"""Shared theme tokens, widget styling, chart layout, and contrast checks."""

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
    "radius": "14px",
    "grid": "#2A3B52",
    "hover": "#1D2B42",
    "input": "#0F1829",
    "on_accent": "#052E22",
}

LIGHT = {
    "bg": "#F6F8FB",
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
    return "\n".join(
        f"    --{key.replace('_', '-')}: {value};"
        for key, value in palette.items()
    )


def theme_css(palette=None):
    """Build the final token-driven application stylesheet."""

    palette = palette or current_palette()
    return f"""
:root {{
{_css_vars(palette)}
    --font-body: 'Plus Jakarta Sans', Inter, sans-serif;
    --font-heading: 'Space Grotesk', Inter, sans-serif;
    --font-mono: 'JetBrains Mono', Consolas, monospace;
}}

html, body, .stApp {{
    color: var(--text) !important;
    background: var(--bg) !important;
    font-family: var(--font-body);
}}

.stApp, [data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(800px 360px at 100% 0%, var(--accent-soft), transparent 70%),
        var(--bg) !important;
}}

h1, h2, h3, h4, .ss-page-title, .ss-section-title {{
    color: var(--text) !important;
    font-family: var(--font-heading) !important;
}}

p, label, li, [data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"] p, [data-testid="stMetricLabel"] p {{
    color: var(--text-muted) !important;
}}

a {{ color: var(--accent) !important; }}
hr {{ border-color: var(--border) !important; }}

div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stForm"],
[data-testid="stExpander"] details,
[data-testid="stMetric"],
[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"],
[data-testid="stTable"] {{
    color: var(--text) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
    box-shadow: 0 10px 28px var(--shadow) !important;
    border-radius: var(--radius) !important;
}}

[data-testid="stMetricValue"] {{
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
}}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div,
input, textarea {{
    color: var(--text) !important;
    background: var(--input) !important;
    border-color: var(--border) !important;
}}

input::placeholder, textarea::placeholder {{
    color: var(--text-muted) !important;
}}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent) !important;
}}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {{
    color: var(--text) !important;
    background: var(--surface) !important;
    border: 1px solid var(--border);
}}

li[role="option"] {{ color: var(--text) !important; }}
li[role="option"]:hover {{ background: var(--hover) !important; }}
span[data-baseweb="tag"] {{
    color: var(--accent) !important;
    background: var(--accent-soft) !important;
}}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {{
    color: var(--on-accent) !important;
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}}

.stButton > button p,
.stDownloadButton > button p,
.stFormSubmitButton > button p {{
    color: var(--on-accent) !important;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    background: var(--success) !important;
    filter: brightness(1.05);
    transform: translateY(-1px);
}}

[data-testid="stSidebar"] {{
    color: var(--text) !important;
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}}

[data-testid="stSidebar"] [role="radiogroup"] label {{
    border: 1px solid transparent;
    border-radius: 10px;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: var(--hover) !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-of-type {{
    display: flex !important;
    width: 14px;
    height: 14px;
    border: 1px solid var(--text-muted);
    border-radius: 50%;
    background: transparent !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: var(--accent-soft) !important;
    border-color: var(--accent) !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)
[data-baseweb="radio"] > div:first-of-type {{
    border: 4px solid var(--accent);
    background: var(--surface) !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label p {{
    color: var(--text-muted) !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{
    color: var(--text) !important;
    font-weight: 700 !important;
}}

[data-testid="stToast"], [data-testid="stAlert"] {{
    color: var(--text) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
}}

@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }}
}}
"""


def apply_theme():
    """Inject token variables and widget rules on every Streamlit rerun."""

    st.markdown(f"<style>{theme_css()}</style>", unsafe_allow_html=True)


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
