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
        radial-gradient(800px 360px at 100% 0%, var(--accent-glow), transparent 70%),
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
    box-shadow: 0 1px 2px var(--shadow-soft), 0 10px 28px var(--shadow) !important;
    border-radius: var(--radius) !important;
    transition: transform 180ms ease, box-shadow 180ms ease,
        border-color 180ms ease !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:hover,
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    border-color: var(--accent) !important;
    box-shadow: 0 12px 30px var(--shadow) !important;
}}

.ss-hero-card {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 24px 28px;
    margin-bottom: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: 0 1px 2px var(--shadow-soft), 0 14px 34px var(--shadow);
    animation: ssFadeIn 240ms ease both;
}}

.ss-hero-value {{
    color: var(--text);
    font-family: var(--font-mono);
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 800;
    letter-spacing: -0.06em;
}}

.ss-hero-helper {{
    margin-top: 8px;
}}

.ss-delta-chip {{
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 0.75rem;
    font-weight: 700;
}}

.ss-delta-chip.success {{
    color: var(--success);
    background: var(--accent-soft);
}}

.ss-delta-chip.danger {{
    color: var(--danger);
    background: color-mix(in srgb, var(--danger) 12%, transparent);
}}

.ss-delta-chip.neutral {{
    color: var(--text-muted);
    background: var(--surface-2);
}}

.ss-sparkline {{
    width: 150px;
    height: 72px;
}}

.ss-sparkline-base {{
    fill: none;
    stroke: var(--border);
    stroke-width: 1;
}}

.ss-sparkline-line {{
    fill: none;
    stroke: var(--accent);
    stroke-width: 3;
    stroke-linecap: round;
    stroke-linejoin: round;
}}

@keyframes ssFadeIn {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.ss-transaction-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid var(--border);
}}

.ss-transaction-row:last-child {{
    border-bottom: 0;
}}

.ss-category-icon {{
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    border-radius: 50%;
    background: var(--accent-soft);
}}

.ss-transaction-main {{
    display: grid;
    flex: 1;
    min-width: 0;
    gap: 2px;
}}

.ss-transaction-main strong {{
    overflow: hidden;
    color: var(--text);
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.ss-transaction-main span {{
    color: var(--text-muted);
    font-size: 0.76rem;
}}

.ss-income {{ color: var(--success) !important; }}
.ss-expense {{ color: var(--danger) !important; }}

.ss-recurring-card {{
    display: flex;
    justify-content: space-between;
    gap: 18px;
    padding: 14px 16px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--surface-2);
}}

.ss-recurring-card strong,
.ss-recurring-card span {{
    display: block;
}}

.ss-recurring-card strong {{
    color: var(--text);
    font-family: var(--font-mono);
}}

.ss-recurring-card span {{
    color: var(--text-muted);
    font-size: 0.78rem;
    margin-top: 4px;
}}

[data-testid="stProgressBar"] > div {{
    height: 7px;
    border-radius: 999px;
    background: var(--surface-2);
}}

[data-testid="stProgressBar"] > div > div {{
    border-radius: 999px;
    background: var(--accent);
}}

.ss-budget-track {{
    height: 7px;
    margin: 8px 0 2px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--surface-2);
}}

.ss-budget-fill {{
    height: 100%;
    border-radius: 999px;
    transition: width 180ms ease;
}}

[data-testid="stSegmentedControl"] button {{
    min-height: 36px;
    border-radius: 999px !important;
    color: var(--text-muted) !important;
}}

[data-testid="stSegmentedControl"] button[aria-checked="true"] {{
    color: var(--text) !important;
    background: var(--accent-soft) !important;
    border-color: var(--accent) !important;
}}

.ss-goal-summary {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0;
}}

.ss-goal-summary strong,
.ss-goal-summary span {{
    display: block;
}}

.ss-goal-summary strong {{
    color: var(--text);
}}

.ss-goal-summary span {{
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 3px;
}}

.ss-goal-ring {{
    display: grid;
    place-items: center;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: conic-gradient(
        var(--accent) var(--goal-progress),
        var(--surface-2) 0
    );
    position: relative;
}}

.ss-goal-ring::after {{
    content: "";
    position: absolute;
    inset: 5px;
    border-radius: 50%;
    background: var(--surface);
}}

.ss-goal-ring span {{
    position: relative;
    z-index: 1;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
}}

[data-testid="stMetricValue"] {{
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.035em;
}}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div,
input, textarea {{
    color: var(--text) !important;
    background: var(--input) !important;
    border-color: var(--border) !important;
}}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input {{
    color: var(--text) !important;
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

[data-testid="stDataFrame"] *,
[data-testid="stTable"] * {{
    color: var(--text) !important;
    border-color: var(--border) !important;
}}

[data-testid="stDataFrame"] [role="columnheader"] {{
    background: var(--surface-2) !important;
    color: var(--text-muted) !important;
    font-weight: 700 !important;
}}

[data-testid="stTabs"] [role="tab"] {{
    color: var(--text-muted) !important;
}}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    border-bottom-color: var(--accent) !important;
}}

[data-testid="stExpander"] summary {{
    color: var(--text) !important;
}}

[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b {{
    color: var(--text) !important;
}}

.ss-money,
[data-testid="stMetricDelta"] {{
    font-variant-numeric: tabular-nums;
}}

@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }}
}}

@media (max-width: 700px) {{
    .ss-hero-card {{
        padding: 20px;
    }}
    .ss-sparkline {{
        width: 96px;
    }}
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap;
    }}
}}

/* Final navigation and budget overrides: emitted after all other app CSS. */
[data-testid="stSidebar"] [data-testid="stRadioGroup"] label
    > div:first-child:not([data-testid="stMarkdownContainer"]),
section[data-testid="stSidebar"] [data-testid="stRadioGroup"] label
    > div:first-child:not([data-testid="stMarkdownContainer"]) {{
    display: none !important;
}}

[data-testid="stSidebar"] [data-testid="stRadioGroup"]
    label input[type="radio"],
section[data-testid="stSidebar"] [data-testid="stRadioGroup"]
    label input[type="radio"] {{
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label > div:not(:has([data-testid="stMarkdownContainer"])),
section[data-testid="stSidebar"] div[role="radiogroup"]
    label > div:not(:has([data-testid="stMarkdownContainer"])),
[data-testid="stSidebar"] div[role="radiogroup"]
    label > div:not(:has([data-testid="stMarkdownContainer"])),
section[data-testid="stSidebar"] label[data-baseweb="radio"]
    > div:first-child,
[data-testid="stSidebar"] label[data-baseweb="radio"]
    > div:first-child {{
    display: none !important;
}}

section[data-testid="stSidebar"] [data-testid="stRadioGroup"],
section[data-testid="stSidebar"] div[role="radiogroup"],
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"],
[data-testid="stSidebar"] div[role="radiogroup"] {{
    display: grid;
    gap: 4px;
}}

section[data-testid="stSidebar"] div[role="radiogroup"]
    label input[type="radio"],
[data-testid="stSidebar"] div[role="radiogroup"]
    label input[type="radio"] {{
    display: none !important;
}}

section[data-testid="stSidebar"] [data-testid="stRadioGroup"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] label,
[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label,
[data-testid="stSidebar"] div[role="radiogroup"] label {{
    display: flex;
    align-items: center;
    gap: 4px;
    width: 100%;
    min-width: 0;
    padding: 10px 14px;
    border: 1px solid transparent;
    border-radius: 10px;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.2s ease;
}}

section[data-testid="stSidebar"] [data-testid="stRadioGroup"] label:hover,
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover,
section[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label:hover,
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: rgba(16, 185, 129, 0.12) !important;
}}

section[data-testid="stSidebar"] [data-testid="stRadioGroup"]
    label:has(input:checked),
section[data-testid="stSidebar"] div[role="radiogroup"]
    label:has(input:checked),
section[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label:has(input:checked),
[data-testid="stSidebar"] div[role="radiogroup"]
    label:has(input:checked) {{
    border: 1px solid #10b981 !important;
    background: rgba(16, 185, 129, 0.18) !important;
    box-shadow: inset 3px 0 0 var(--primary);
    font-weight: 600 !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label p,
[data-testid="stSidebar"] div[role="radiogroup"] label p {{
    min-width: 0;
    overflow: hidden;
    color: var(--text-muted) !important;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

[data-testid="stSidebar"] [data-testid="stRadio"]
    div[role="radiogroup"] label:has(input:checked) p,
[data-testid="stSidebar"] div[role="radiogroup"]
    label:has(input:checked) p {{
    color: var(--primary) !important;
    font-weight: 700 !important;
}}

.ss-budget-track {{
    height: 8px !important;
    margin: 8px 0 6px !important;
    overflow: hidden !important;
    border-radius: var(--radius-pill) !important;
    background: color-mix(in srgb, var(--text) 8%, transparent) !important;
}}

.ss-budget-fill {{
    height: 100% !important;
    border-radius: inherit !important;
}}

.ss-budget-fill--ok {{
    background: var(--success) !important;
}}

.ss-budget-fill--warning {{
    background: var(--warning) !important;
}}

.ss-budget-fill--danger {{
    background: var(--danger) !important;
}}

.ss-budget-caption {{
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    min-width: 0;
    margin: 0 !important;
    opacity: 0.85;
    font-size: 0.8rem;
}}

.ss-budget-caption--ok {{
    color: var(--success) !important;
}}

.ss-budget-caption--warning {{
    color: var(--warning) !important;
}}

.ss-budget-caption--danger {{
    color: var(--danger) !important;
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
