"""Shared theme tokens, widget styling, chart layout, and contrast checks."""

import streamlit as st

from utils.formatting import tint


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
    "glass_bg": tint("#FFFFFF", 10),
    "glass_bg_strong": tint("#FFFFFF", 14),
    "glass_border": tint("#FFFFFF", 18),
    "glass_highlight": tint("#FFFFFF", 24),
    "glass_shadow": tint("#020617", 48),
    "glass_blur": "18px",
    "radius_card": "22px",
    "radius_pill": "999px",
    "mesh_emerald": tint("#10B981", 18),
    "mesh_indigo": tint("#6366F1", 16),
    "mesh_warm": tint("#F59E0B", 12),
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
    "glass_bg": tint("#FFFFFF", 64),
    "glass_bg_strong": tint("#FFFFFF", 78),
    "glass_border": tint("#FFFFFF", 82),
    "glass_highlight": tint("#FFFFFF", 95),
    "glass_shadow": tint("#64748B", 18),
    "glass_blur": "18px",
    "radius_card": "22px",
    "radius_pill": "999px",
    "mesh_emerald": tint("#10B981", 12),
    "mesh_indigo": tint("#6366F1", 14),
    "mesh_warm": tint("#F59E0B", 10),
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
        radial-gradient(780px 520px at 96% -6%, var(--mesh-emerald), transparent 72%),
        radial-gradient(760px 560px at 4% 18%, var(--mesh-indigo), transparent 70%),
        radial-gradient(640px 440px at 78% 92%, var(--mesh-warm), transparent 72%),
        var(--bg) !important;
    background-attachment: fixed;
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
    background: var(--glass-bg) !important;
    border-color: var(--glass-border) !important;
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 1px 2px var(--shadow-soft),
        0 14px 34px var(--glass-shadow) !important;
    border-radius: var(--radius-card) !important;
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
    transition: transform 180ms ease, box-shadow 180ms ease,
        border-color 180ms ease !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:hover,
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    border-color: var(--accent) !important;
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 18px 38px var(--glass-shadow) !important;
}}

.ss-hero-card {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 24px 28px;
    margin-bottom: 16px;
    background: var(--glass-bg-strong);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-card);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 1px 2px var(--shadow-soft),
        0 14px 34px var(--glass-shadow);
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
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

.ss-glass-card {{
    position: relative;
    overflow: hidden;
    padding: 18px;
    color: var(--text);
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-card);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 10px 24px var(--glass-shadow);
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
    transition: transform 180ms ease, box-shadow 180ms ease,
        border-color 180ms ease;
}}

.ss-glass-card::before {{
    position: absolute;
    inset: 0 12% auto;
    height: 1px;
    content: "";
    background: var(--glass-highlight);
    pointer-events: none;
}}

.ss-glass-card:hover {{
    border-color: var(--accent);
    transform: translateY(-4px);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 18px 38px var(--glass-shadow);
}}

.ss-glass-kpi {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
}}

.ss-glass-kpi-copy {{ min-width: 0; }}
.ss-glass-kpi-label {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-muted);
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}}
.ss-glass-kpi-icon {{ color: var(--accent); }}
.ss-glass-kpi-value {{
    margin-top: 10px;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: clamp(1.45rem, 2.4vw, 2.15rem);
    font-variant-numeric: tabular-nums;
    font-weight: 800;
    letter-spacing: -0.05em;
    overflow-wrap: anywhere;
}}
.ss-glass-kpi-delta {{
    margin-top: 7px;
    color: var(--text-muted);
    font-size: 0.78rem;
}}
.ss-glass-sparkline {{ width: 120px; height: 58px; flex: 0 0 120px; }}

.ss-glass-progress {{
    display: grid;
    place-items: center;
    gap: 12px;
    text-align: center;
}}
.ss-glass-ring {{
    display: grid;
    place-items: center;
    width: 96px;
    height: 96px;
    border-radius: 50%;
    background: conic-gradient(
        var(--accent) var(--ring-progress),
        var(--surface-2) 0
    );
    position: relative;
}}
.ss-glass-ring::after {{
    position: absolute;
    inset: 8px;
    content: "";
    border-radius: 50%;
    background: var(--glass-bg-strong);
}}
.ss-glass-ring span {{
    position: relative;
    z-index: 1;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 1rem;
    font-variant-numeric: tabular-nums;
    font-weight: 800;
}}
.ss-glass-progress-label,
.ss-glass-section-subtitle,
.ss-glass-empty-message {{
    color: var(--text-muted);
    font-size: 0.8rem;
}}
.ss-glass-legend-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}}
.ss-glass-legend-label {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text);
}}
.ss-glass-legend-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
}}
.ss-glass-legend-value {{
    color: var(--text);
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
}}
.ss-glass-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 11px;
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-pill);
    color: var(--text);
    background: var(--glass-bg);
    font-size: 0.76rem;
    font-weight: 700;
}}
.ss-glass-pill-icon {{ color: var(--accent); }}
.ss-glass-chip-default {{ color: var(--text); }}
.ss-glass-chip-success {{ color: var(--success); background: var(--accent-soft); }}
.ss-glass-chip-danger {{ color: var(--danger); background: color-mix(in srgb, var(--danger) 12%, transparent); }}
.ss-glass-chip-warning {{ color: var(--warning); background: color-mix(in srgb, var(--warning) 12%, transparent); }}
.ss-glass-chip-info {{ color: var(--info); background: color-mix(in srgb, var(--info) 12%, transparent); }}
.ss-glass-section-header {{ margin-bottom: 14px; }}
.ss-glass-section-title {{
    color: var(--text);
    font-family: var(--font-heading);
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}}
.ss-glass-empty-state {{
    display: grid;
    place-items: center;
    gap: 7px;
    min-height: 132px;
    text-align: center;
}}
.ss-glass-empty-icon {{ color: var(--accent); font-size: 1.6rem; }}
.ss-glass-empty-title {{ color: var(--text); font-weight: 800; }}

.st-key-topbar {{
    position: sticky;
    z-index: 20;
    top: 12px;
    display: flex;
    align-items: center;
    min-height: 54px;
    margin-bottom: 18px;
    padding: 8px 14px;
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-pill);
    background: var(--glass-bg);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 10px 24px var(--glass-shadow);
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
}}

.ss-topbar-greeting {{
    color: var(--text-muted);
    font-size: 0.88rem;
}}
.ss-topbar-greeting strong {{ color: var(--text); }}
.st-key-topbar [data-testid="stHorizontalBlock"] {{
    align-items: center;
}}
.st-key-topbar .stButton > button {{
    min-height: 34px;
    border-radius: var(--radius-pill) !important;
}}
.st-key-topbar [data-testid="stPopover"] > button {{
    min-width: 38px;
    min-height: 34px;
    padding: 0;
    border-radius: 50%;
}}
.st-key-topbar [data-testid="stToggle"] {{
    justify-content: flex-end;
}}

[data-testid="stSidebar"] {{
    width: 78px !important;
    min-width: 78px !important;
    background: var(--glass-bg) !important;
    border-right: 1px solid var(--glass-border) !important;
    box-shadow: inset -1px 0 0 var(--glass-highlight);
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
}}
[data-testid="stSidebar"] > div:first-child {{
    width: 78px !important;
    padding: 14px 10px 96px !important;
}}
.ss-rail-brand {{
    display: grid;
    place-items: center;
    margin-bottom: 14px;
}}
.ss-rail-logo {{
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border: 1px solid var(--glass-highlight);
    border-radius: 14px;
    color: var(--on-accent);
    background: var(--accent);
    box-shadow: 0 8px 22px var(--accent-glow);
    font-family: var(--font-heading);
    font-weight: 800;
}}
.st-key-rail_quick_add,
[class*="st-key-rail_"][class*="_active"],
[class*="st-key-rail_"][class*="_item"] {{
    display: grid;
    place-items: center;
    margin: 4px 0;
}}
.st-key-rail_quick_add .stButton > button,
[class*="st-key-rail_"][class*="_active"] .stButton > button,
[class*="st-key-rail_"][class*="_item"] .stButton > button {{
    width: 44px;
    min-width: 44px;
    height: 44px;
    min-height: 44px;
    padding: 0;
    border: 1px solid transparent !important;
    border-radius: 14px !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    font-size: 1.15rem;
}}
.st-key-rail_quick_add .stButton > button {{
    border-color: var(--accent) !important;
    color: var(--on-accent) !important;
    background: var(--accent) !important;
    border-radius: 50% !important;
    box-shadow: 0 8px 22px var(--accent-glow);
}}
[class*="st-key-rail_"][class*="_item"] .stButton > button:hover {{
    border-color: var(--glass-border) !important;
    color: var(--text) !important;
    background: var(--glass-bg-strong) !important;
}}
[class*="st-key-rail_"][class*="_active"] .stButton > button {{
    border-color: var(--accent) !important;
    color: var(--text) !important;
    background: var(--accent-soft) !important;
    box-shadow: 0 0 18px var(--accent-glow);
}}
.st-key-rail_period {{
    display: grid;
    place-items: center;
    margin-top: 12px;
}}
.st-key-rail_period [data-testid="stPopover"] > button {{
    width: 44px;
    min-width: 44px;
    height: 44px;
    padding: 0;
    border-radius: 14px;
}}
.st-key-rail_period [data-testid="stPopover"] > button p {{
    color: var(--text-muted) !important;
}}

.st-key-bottom_dock {{
    position: fixed;
    z-index: 50;
    right: max(16px, env(safe-area-inset-right));
    bottom: max(16px, env(safe-area-inset-bottom));
    left: max(16px, env(safe-area-inset-left));
    width: min(720px, calc(100vw - 32px));
    margin: 0 auto;
    padding: 7px;
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-pill);
    background: var(--glass-bg-strong);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 16px 38px var(--glass-shadow);
    -webkit-backdrop-filter: blur(var(--glass-blur));
    backdrop-filter: blur(var(--glass-blur));
}}
.st-key-bottom_dock [data-testid="column"] {{
    padding: 0 3px;
}}
.st-key-bottom_dock [class*="st-key-dock_"] {{
    display: grid;
}}
.st-key-bottom_dock .stButton > button {{
    min-height: 38px;
    padding: 6px 9px;
    border: 1px solid transparent !important;
    border-radius: var(--radius-pill) !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    font-size: 0.74rem;
    font-weight: 700 !important;
    white-space: nowrap;
}}
.st-key-bottom_dock [class*="st-key-dock_"][class*="_active"] .stButton > button,
.st-key-bottom_dock .stButton > button:hover {{
    border-color: var(--accent) !important;
    color: var(--text) !important;
    background: var(--accent-soft) !important;
}}
.st-key-bottom_dock .stButton > button p {{
    color: inherit !important;
}}
.block-container {{
    padding-bottom: 7rem !important;
}}

.ss-delta-chip {{
    display: inline-flex;
    align-items: center;
    border-radius: var(--radius-pill);
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
        animation: none !important;
    }}
}}

@supports not ((backdrop-filter: blur(1px))) {{
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stForm"],
    [data-testid="stExpander"] details,
    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .ss-hero-card,
    .ss-glass-card {{
        background: var(--glass-bg-strong) !important;
        -webkit-backdrop-filter: none;
        backdrop-filter: none;
    }}
}}

@media (prefers-reduced-transparency: reduce) {{
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stForm"],
    [data-testid="stExpander"] details,
    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .ss-hero-card,
    .ss-glass-card {{
        background: var(--glass-bg-strong) !important;
        -webkit-backdrop-filter: none;
        backdrop-filter: none;
    }}
}}

@media (max-width: 700px) {{
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {{
        width: 68px !important;
        min-width: 68px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-left: 5px !important;
        padding-right: 5px !important;
    }}
    .st-key-bottom_dock {{
        right: max(8px, env(safe-area-inset-right));
        bottom: max(8px, env(safe-area-inset-bottom));
        left: max(8px, env(safe-area-inset-left));
        width: calc(100vw - 16px);
    }}
    .st-key-bottom_dock .stButton > button {{
        padding: 6px 4px;
        font-size: 0;
    }}
    .st-key-bottom_dock .stButton > button p {{
        font-size: 0;
    }}
    .st-key-bottom_dock .stButton > button p::first-letter {{
        font-size: 1.1rem;
    }}
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
