import streamlit as st


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* =====================================================
   BASE
   ===================================================== */

html, body, .stApp {
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto,
        'Helvetica Neue', Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(1100px 480px at 88% -8%,
            var(--mesh-emerald), transparent 60%),
        radial-gradient(900px 480px at -8% 0%,
            var(--mesh-cyan), transparent 55%),
        var(--bg);
    background-attachment: fixed;
    color: var(--text);
}

[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu,
footer,
[data-testid="stDeployButton"] {
    visibility: hidden;
}

.block-container {
    max-width: 1680px;
    padding-top: 2rem;
    padding-bottom: 3rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
}

.main .block-container {
    padding-bottom: 120px !important;
}

::selection {
    background: color-mix(in srgb, var(--accent) 1%, transparent);
}

::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--success);
}

/* =====================================================
   TYPOGRAPHY
   ===================================================== */

h1, h2, h3, h4 {
    color: var(--text) !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em;
}

p, label, li {
    color: var(--text-muted);
}

a {
    color: var(--success) !important;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border-color: var(--border);
}

.ss-eyebrow {
    color: var(--success);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

.ss-page-title {
    font-size: clamp(1.8rem, 2.6vw, 2.3rem);
    font-weight: 800;
    letter-spacing: -0.05em;
    line-height: 1.12;
    background: linear-gradient(90deg, var(--text) 0%, var(--text-muted) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.ss-subtitle {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin-top: 0.5rem;
    margin-bottom: 1.2rem;
    max-width: 62ch;
}

.ss-section-title {
    color: var(--text);
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem;
}

.ss-muted {
    color: var(--text-muted);
    font-size: 0.8rem;
}

.ss-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: color-mix(in srgb, var(--accent) 1%, transparent);
    color: var(--success);
    border: 1px solid color-mix(in srgb, var(--accent) 1%, transparent);
}

/* =====================================================
   CARDS AND CONTAINERS
   ===================================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-card);
    background: var(--glass-bg);
    box-shadow:
        inset 0 1px 0 var(--glass-highlight),
        0 14px 34px var(--glass-shadow);
    -webkit-backdrop-filter: blur(18px) saturate(140%);
    backdrop-filter: blur(18px) saturate(140%);
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, var(--surface-2) 0%, var(--surface) 100%);
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 20px 22px;
    min-height: 116px;
    box-shadow: 0 10px 26px color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    transition: border-color 0.18s ease, transform 0.18s ease;
}

[data-testid="stMetric"]:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
}

[data-testid="stMetricLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-size: clamp(1.35rem, 2vw, 2rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.035em;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

div[data-testid="stForm"] {
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    padding: 22px;
    border-radius: 14px;
    border: 1px solid var(--border);
}

[data-testid="stExpander"] details {
    border: 1px solid var(--border);
    border-radius: 14px;
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent);
}

[data-testid="stExpander"] summary:hover {
    color: var(--success);
}

[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid color-mix(in srgb, var(--info) 1%, transparent);
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
}

/* =====================================================
   FORM CONTROLS
   ===================================================== */

[data-testid="stWidgetLabel"] p {
    color: var(--text) !important;
    font-weight: 600;
    font-size: 0.86rem;
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: var(--input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 1%, transparent) !important;
}

input, textarea {
    background: transparent !important;
    color: var(--text) !important;
}

input::placeholder,
textarea::placeholder {
    color: var(--text-muted) !important;
}

span[data-baseweb="tag"] {
    background: color-mix(in srgb, var(--accent) 1%, transparent) !important;
    border-radius: 8px !important;
}

span[data-baseweb="tag"] span {
    color: var(--accent-soft) !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: var(--surface) !important;
}

li[role="option"]:hover {
    background: color-mix(in srgb, var(--accent) 1%, transparent) !important;
}

[data-baseweb="tab-highlight"] {
    background: var(--accent) !important;
}

div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--info), var(--success));
    border-radius: 999px;
}

/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent) 100%);
    color: var(--text) !important;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 42px;
    box-shadow: 0 6px 18px color-mix(in srgb, var(--accent) 1%, transparent);
    transition: transform 0.15s ease, filter 0.15s ease,
        box-shadow 0.15s ease;
}

.stButton > button p,
.stDownloadButton > button p,
.stFormSubmitButton > button p {
    color: var(--text) !important;
    font-weight: 700;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    color: var(--text) !important;
    filter: brightness(1.08);
    transform: translateY(-1px);
    box-shadow: 0 10px 24px color-mix(in srgb, var(--accent) 1%, transparent);
}

.stButton > button:active,
.stDownloadButton > button:active,
.stFormSubmitButton > button:active {
    transform: translateY(0);
}

.stButton > button:disabled,
.stFormSubmitButton > button:disabled {
    opacity: 0.45;
    box-shadow: none;
}

/* =====================================================
   SIDEBAR
   ===================================================== */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg) 0%, var(--surface) 100%);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: var(--text-muted);
}

.ss-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 4px 12px 4px;
}

.ss-brand-logo {
    width: 44px;
    height: 44px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    background: linear-gradient(135deg, var(--accent), var(--info));
    box-shadow: 0 8px 22px color-mix(in srgb, var(--accent) 1%, transparent);
}

.ss-brand-name {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.035em;
    line-height: 1.1;
    color: var(--text);
}

.ss-brand-tag {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 3px;
}

.ss-side-label {
    color: var(--text-muted);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 16px 0 8px 4px;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 4px;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    width: 100%;
    margin: 0;
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid transparent;
    transition: background 0.15s ease, border-color 0.15s ease;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: color-mix(in srgb, var(--info) 1%, transparent);
}

[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-of-type {
    display: none;
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: var(--text-muted);
    font-size: 0.92rem;
    font-weight: 500;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(
        90deg,
        color-mix(in srgb, var(--accent) 1%, transparent),
        color-mix(in srgb, var(--accent) 1%, transparent)
    );
    border-color: color-mix(in srgb, var(--accent) 1%, transparent);
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: var(--text) !important;
    font-weight: 700;
}

/* Hide Streamlit's automatic page navigation */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* =====================================================
   RESPONSIVE
   ===================================================== */

@media (max-width: 900px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1.4rem;
    }
}
@media (max-width: 767px) {
    .block-container {
        padding-left: 0.65rem;
        padding-right: 0.65rem;
        padding-top: 1rem;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0.55rem !important;
    }
    [data-testid="column"] {
        padding-left: 0.15rem;
        padding-right: 0.15rem;
    }
    .ss-page-title {
        font-size: 1.65rem;
        line-height: 1.15;
    }
    .ss-subtitle {
        font-size: 0.82rem;
        line-height: 1.45;
    }
    .ss-section-title,
    h2 {
        font-size: 1rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"] {
        font-size: 0.72rem !important;
    }
}
"""

_DARK_THEME_CSS = """
.stApp {
    background:
        radial-gradient(1100px 480px at 88% -8%,
            color-mix(in srgb, var(--accent) 1%, transparent), transparent 60%),
        radial-gradient(900px 480px at -8% 0%,
            color-mix(in srgb, var(--info) 1%, transparent), transparent 55%),
        var(--bg);
    color: var(--text);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: color-mix(in srgb, var(--info) 1%, transparent);
    background: linear-gradient(
        150deg,
        color-mix(in srgb, var(--glass-shadow) 1%, transparent),
        color-mix(in srgb, var(--glass-shadow) 1%, transparent)
    );
}

[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        color-mix(in srgb, var(--glass-shadow) 1%, transparent),
        color-mix(in srgb, var(--glass-shadow) 1%, transparent)
    );
}
"""

_LIGHT_THEME_CSS = """
.stApp {
    background: var(--text);
    color: var(--bg);
}

[data-testid="stHeader"] {
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent);
}

html, body, .stApp,
p, label, li, [data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] {
    color: var(--text-muted);
}

h1, h2, h3, h4,
.ss-section-title,
[data-testid="stMetricValue"] {
    color: var(--bg) !important;
}

.ss-page-title {
    background: linear-gradient(90deg, var(--bg) 0%, var(--text-muted) 100%);
    -webkit-background-clip: text;
    background-clip: text;
}

.ss-subtitle, .ss-muted {
    color: var(--text-muted);
}

a {
    color: var(--accent) !important;
}

hr {
    border-color: var(--text);
}

div[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMetric"],
div[data-testid="stForm"],
[data-testid="stExpander"] details,
[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border-color: var(--text);
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    box-shadow: 0 8px 24px color-mix(in srgb, var(--glass-shadow) 1%, transparent);
}

[data-testid="stMetricLabel"] p,
[data-testid="stWidgetLabel"] p {
    color: var(--text-muted) !important;
}

[data-testid="stMetricValue"] {
    color: var(--bg) !important;
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: var(--text) !important;
    border-color: var(--text-muted) !important;
}

input, textarea {
    color: var(--bg) !important;
}

input::placeholder, textarea::placeholder {
    color: var(--text-muted) !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: var(--text) !important;
}

li[role="option"] {
    color: var(--bg) !important;
}

li[role="option"]:hover {
    background: var(--hover) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--text) 0%, var(--text) 100%);
    border-right-color: var(--text);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: var(--text-muted);
}

.ss-brand-name {
    color: var(--bg);
}

.ss-brand-tag, .ss-side-label {
    color: var(--text-muted);
}

.ss-auth-brand,
.ss-auth-form-heading strong {
    color: var(--bg);
}

.ss-auth-title {
    color: var(--bg) !important;
}

.ss-auth-subtitle,
.ss-auth-form-heading span {
    color: var(--text-muted);
}

.ss-auth-logo {
    color: var(--accent);
    border-color: color-mix(in srgb, var(--accent) 1%, transparent);
    background: linear-gradient(
        145deg,
        color-mix(in srgb, var(--accent) 1%, transparent),
        color-mix(in srgb, var(--info) 1%, transparent)
    );
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: var(--text-muted);
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: var(--bg) !important;
}

::-webkit-scrollbar-thumb {
    background: var(--text-muted);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border-color: var(--text);
}
"""

_FINTECH_THEME_CSS = """
/* =====================================================
   SPENDSENSE AI · FINTECH DESIGN SYSTEM
   ===================================================== */

:root {
    --ss-obsidian: var(--bg);
    --ss-surface: color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    --ss-border: color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    --ss-emerald: var(--accent);
    --ss-cyan: var(--info);
    --ss-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
    --ss-heading: 'Space Grotesk', Inter, sans-serif;
    --ss-body: 'Plus Jakarta Sans', Inter, sans-serif;
}

html, body, .stApp,
button, input, textarea, select, [data-testid="stMarkdownContainer"] {
    font-family: var(--ss-body);
}

.stApp {
    position: relative;
    min-height: 100vh;
    overflow-x: hidden;
    background:
        radial-gradient(
            900px 700px at -8% -12%,
            color-mix(in srgb, var(--accent) 1%, transparent),
            transparent 64%
        ),
        radial-gradient(
            850px 650px at 108% 112%,
            color-mix(in srgb, var(--info) 1%, transparent),
            transparent 62%
        ),
        var(--bg);
    background-attachment: fixed;
}

.stApp::before {
    position: fixed;
    z-index: 0;
    inset: 0;
    pointer-events: none;
    content: "";
    opacity: 0.035;
    background-image:
        url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.32'/%3E%3C/svg%3E");
    mix-blend-mode: soft-light;
}

.stApp > * {
    position: relative;
    z-index: 1;
}

h1, h2, h3 {
    font-family: var(--ss-heading) !important;
    letter-spacing: -0.03em !important;
}

h4, h5, h6 {
    font-family: var(--ss-heading) !important;
}

.gradient-text-emerald {
    background: linear-gradient(110deg, var(--accent) 0%, var(--info) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 14px color-mix(in srgb, var(--accent) 1%, transparent));
}

[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th,
.transaction-amount,
.balance-total,
.monetary-value,
code, pre {
    font-family: var(--ss-mono) !important;
    font-variant-numeric: tabular-nums;
}

[data-testid="stMetricValue"] {
    letter-spacing: -0.04em;
}

div[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMetric"],
div[data-testid="stForm"],
[data-testid="stExpander"] details,
[data-testid="stPopover"],
[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    position: relative;
    overflow: hidden;
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    border-radius: 20px;
    box-shadow: 0 10px 30px -10px color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    transition:
        transform 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]::after,
[data-testid="stMetric"]::after {
    position: absolute;
    inset: 0;
    pointer-events: none;
    content: "";
    opacity: 0;
    background: radial-gradient(
        500px 180px at 50% 0%,
        color-mix(in srgb, var(--accent) 1%, transparent),
        transparent 70%
    );
    transition: opacity 180ms ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover,
[data-testid="stMetric"]:hover,
div[data-testid="stForm"]:hover {
    transform: translateY(-2px);
    border-color: color-mix(in srgb, var(--accent) 1%, transparent);
    box-shadow:
        0 14px 34px -12px color-mix(in srgb, var(--glass-shadow) 1%, transparent),
        inset 0 0 24px color-mix(in srgb, var(--accent) 1%, transparent);
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover::after,
[data-testid="stMetric"]:hover::after {
    opacity: 1;
}

[data-testid="stMetric"] {
    min-height: 116px;
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border: 1px solid color-mix(in srgb, var(--accent) 1%, transparent);
    border-radius: 999px;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--accent) 1%, transparent),
        color-mix(in srgb, var(--accent) 1%, transparent)
    );
    box-shadow:
        0 8px 22px color-mix(in srgb, var(--accent) 1%, transparent),
        inset 0 1px 0 color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    transition:
        transform 160ms ease,
        box-shadow 160ms ease,
        filter 160ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    border-color: color-mix(in srgb, var(--accent) 1%, transparent);
    box-shadow:
        0 12px 30px color-mix(in srgb, var(--accent) 1%, transparent),
        0 0 20px color-mix(in srgb, var(--accent) 1%, transparent);
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-color: color-mix(in srgb, var(--info) 1%, transparent) !important;
    border-radius: 12px !important;
    box-shadow: inset 0 1px 0 color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within,
input:focus, textarea:focus {
    border-color: color-mix(in srgb, var(--accent) 1%, transparent) !important;
    box-shadow:
        0 0 0 3px color-mix(in srgb, var(--accent) 1%, transparent),
        0 0 18px color-mix(in srgb, var(--accent) 1%, transparent) !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background: transparent !important;
}

.stButton > button,
.stFormSubmitButton > button {
    border: none !important;
    font-family: var(--ss-body) !important;
    font-weight: 600 !important;
}

.ss-auth-header {
    margin: 0 auto 1.75rem;
    text-align: center;
}

.ss-auth-logo {
    display: inline-grid;
    width: 3rem;
    height: 3rem;
    margin-bottom: 0.75rem;
    place-items: center;
    border: 1px solid color-mix(in srgb, var(--accent) 1%, transparent);
    border-radius: 14px;
    color: var(--success);
    background: linear-gradient(
        145deg,
        color-mix(in srgb, var(--accent) 1%, transparent),
        color-mix(in srgb, var(--info) 1%, transparent)
    );
    box-shadow:
        0 0 28px color-mix(in srgb, var(--accent) 1%, transparent),
        inset 0 1px 0 color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    font-size: 1.5rem;
}

.ss-auth-brand {
    color: var(--text);
    font-family: var(--ss-heading);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.ss-auth-brand span {
    color: var(--accent);
}

.ss-auth-title {
    margin: 1rem 0 0.45rem;
    color: var(--text) !important;
    font-size: clamp(2rem, 5vw, 2.65rem) !important;
}

.ss-auth-subtitle,
.ss-auth-form-heading span {
    color: var(--text-muted);
}

.ss-auth-subtitle {
    margin: 0;
    font-size: 0.88rem;
}

.ss-auth-form-heading {
    display: grid;
    gap: 0.3rem;
    margin-bottom: 1.1rem;
}

.ss-auth-form-heading strong {
    color: var(--text);
    font-family: var(--ss-heading);
    font-size: 1.15rem;
    letter-spacing: -0.02em;
}

.ss-auth-form-heading span {
    font-size: 0.82rem;
}

.pulse-badge-success,
.pulse-badge-warning,
.pulse-badge-danger {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 10px;
    border: 1px solid;
    border-radius: 999px;
    font-family: var(--ss-body);
    font-size: 0.72rem;
    font-weight: 700;
    line-height: 1;
}

.pulse-badge-success::before,
.pulse-badge-warning::before,
.pulse-badge-danger::before {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    content: "";
    animation: pulseGlow 1.8s ease-in-out infinite;
}

.pulse-badge-success {
    color: var(--success);
    border-color: color-mix(in srgb, var(--accent) 1%, transparent);
    background: color-mix(in srgb, var(--accent) 1%, transparent);
}

.pulse-badge-success::before {
    background: var(--accent);
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 1%, transparent);
}

.pulse-badge-warning {
    color: var(--warning);
    border-color: color-mix(in srgb, var(--danger) 1%, transparent);
    background: color-mix(in srgb, var(--danger) 1%, transparent);
}

.pulse-badge-warning::before {
    background: var(--warning);
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--danger) 1%, transparent);
}

.pulse-badge-danger {
    color: var(--danger);
    border-color: color-mix(in srgb, var(--danger) 1%, transparent);
    background: color-mix(in srgb, var(--danger) 1%, transparent);
}

.pulse-badge-danger::before {
    background: var(--danger);
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--danger) 1%, transparent);
}

@keyframes pulseGlow {
    0%, 100% {
        opacity: 0.75;
        transform: scale(0.9);
        box-shadow: 0 0 0 0 currentColor;
    }
    50% {
        opacity: 1;
        transform: scale(1.15);
        box-shadow: 0 0 0 5px transparent;
    }
}

::-webkit-scrollbar {
    width: 9px;
    height: 9px;
}

::-webkit-scrollbar-track {
    background: var(--bg);
}

::-webkit-scrollbar-thumb {
    border: 2px solid var(--bg);
    border-radius: 999px;
    background: var(--border);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(var(--accent), var(--info));
}
"""

_CINEMATIC_AUTH_CSS = """
/* Scoped cinematic luxury authentication surface. */
.stApp:has(.auth-page-marker) {
    background:
        radial-gradient(
            78% 16% at 7% 24%,
            color-mix(in srgb, var(--danger) 1%, transparent) 0%,
            color-mix(in srgb, var(--danger) 1%, transparent) 34%,
            transparent 72%
        ),
        radial-gradient(
            74% 14% at 94% 33%,
            color-mix(in srgb, var(--danger) 1%, transparent) 0%,
            color-mix(in srgb, var(--danger) 1%, transparent) 38%,
            transparent 74%
        ),
        radial-gradient(
            88% 18% at 15% 78%,
            color-mix(in srgb, var(--danger) 1%, transparent) 0%,
            color-mix(in srgb, var(--danger) 1%, transparent) 38%,
            transparent 72%
        ),
        radial-gradient(
            76% 13% at 96% 88%,
            color-mix(in srgb, var(--danger) 1%, transparent) 0%,
            color-mix(in srgb, var(--danger) 1%, transparent) 42%,
            transparent 74%
        ),
        radial-gradient(
            120% 90% at 50% 50%,
            transparent 45%,
            color-mix(in srgb, var(--glass-shadow) 1%, transparent) 100%
        ),
        var(--bg) !important;
    background-attachment: fixed !important;
}

.stApp:has(.auth-page-marker)::after {
    position: fixed;
    z-index: 0;
    inset: -28%;
    pointer-events: none;
    content: "";
    opacity: 0.9;
    background:
        radial-gradient(
            42% 5% at 12% 25%,
            color-mix(in srgb, var(--danger) 1%, transparent),
            color-mix(in srgb, var(--danger) 1%, transparent) 42%,
            transparent 76%
        ),
        radial-gradient(
            46% 5% at 84% 38%,
            color-mix(in srgb, var(--danger) 1%, transparent),
            color-mix(in srgb, var(--danger) 1%, transparent) 44%,
            transparent 76%
        ),
        radial-gradient(
            48% 5% at 18% 76%,
            color-mix(in srgb, var(--danger) 1%, transparent),
            color-mix(in srgb, var(--danger) 1%, transparent) 45%,
            transparent 78%
        );
    filter: blur(26px);
    transform: rotate(-25deg);
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2) {
    position: relative;
    overflow: hidden;
    max-width: 460px !important;
    margin: 0 auto !important;
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent) !important;
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-top: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-radius: 20px !important;
    padding: 32px !important;
    clip-path: polygon(0 4%, 4% 0, 100% 0, 100% 96%, 96% 100%, 0 100%);
    box-shadow:
        0 20px 60px color-mix(in srgb, var(--glass-shadow) 1%, transparent),
        inset 0 1px 0 color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    animation: authCardIn 500ms ease both;
    transition: min-height 300ms ease;
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::before,
.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::after {
    position: absolute;
    z-index: 4;
    inset: 0;
    pointer-events: none;
    content: "";
    border-radius: 20px;
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    opacity: 1;
    clip-path: polygon(0 4%, 4% 0, 100% 0, 100% 96%, 96% 100%, 0 100%);
    animation: authCardReveal 900ms ease 500ms forwards;
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::before {
    inset: 0;
    z-index: 3;
    width: auto;
    height: auto;
    border: 1px solid transparent;
    border-radius: 20px;
    background: conic-gradient(
        from 0deg,
        transparent 0deg,
        transparent 240deg,
        color-mix(in srgb, var(--warning) 1%, transparent) 280deg,
        transparent 320deg,
        transparent 360deg
    ) border-box;
    -webkit-mask:
        linear-gradient(var(--bg) 0 0) padding-box,
        linear-gradient(var(--bg) 0 0);
    -webkit-mask-composite: xor;
    mask:
        linear-gradient(var(--bg) 0 0) padding-box,
        linear-gradient(var(--bg) 0 0);
    mask-composite: exclude;
    animation: authEdgeSpin 8s linear infinite;
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::after {
    display: block;
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)
> [data-testid="stVerticalBlock"] {
    position: relative;
    z-index: 5;
    animation: authContentIn 700ms ease 500ms both;
}

.stApp:has(.auth-page-marker) .auth-page-marker {
    display: block;
    position: absolute;
    z-index: 6;
    top: 0;
    left: 0;
    width: 34px;
    height: 34px;
    pointer-events: none;
}

.stApp:has(.auth-page-marker) .auth-page-marker::before,
.stApp:has(.auth-page-marker) .auth-page-marker::after {
    position: absolute;
    width: 28px;
    height: 28px;
    content: "";
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent);
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent);
}

.stApp:has(.auth-page-marker) .auth-page-marker::before {
    top: 0;
    left: 0;
    clip-path: polygon(0 0, 100% 0, 0 100%);
}

.stApp:has(.auth-page-marker) .auth-page-marker::after {
    right: -418px;
    bottom: -590px;
    clip-path: polygon(100% 0, 100% 100%, 0 100%);
}

.stApp:has(.auth-page-marker) [data-testid="stSegmentedControl"] {
    display: none !important;
}

.stApp:has(.auth-page-marker) [data-testid="stTextInput"] {
    position: relative;
}

.stApp:has(.auth-page-marker) [data-testid="stTextInput"] input {
    background-color: color-mix(in srgb, var(--glass-shadow) 1%, transparent) !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
    background-size: 18px 18px !important;
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    padding: 14px 14px 14px 40px !important;
    transition: all 0.3s ease !important;
}

.stApp:has(.auth-page-marker)
[data-testid="stTextInput"] input[type="text"] {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 6H4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2Z'/%3E%3Cpath d='m2 8 10 6 10-6'/%3E%3C/svg%3E") !important;
}

.stApp:has(.auth-page-marker)
[data-testid="stTextInput"] input[placeholder="you@example.com"] {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='14' rx='2'/%3E%3Cpath d='m3 7 9 6 9-6'/%3E%3C/svg%3E") !important;
}

.stApp:has(.auth-page-marker)
[data-testid="stTextInput"] input[type="password"] {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='10' width='16' height='10' rx='2'/%3E%3Cpath d='M8 10V7a4 4 0 0 1 8 0v3'/%3E%3C/svg%3E") !important;
}

.stApp:has(.auth-page-marker) [data-testid="stTextInput"] input:focus {
    border-color: color-mix(in srgb, var(--warning) 1%, transparent) !important;
    box-shadow: 0 0 15px color-mix(in srgb, var(--warning) 1%, transparent) !important;
}

.stApp:has(.auth-page-marker) [data-testid="stTextInput"] label p {
    color: var(--text-muted) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.04em;
}

.stApp:has(.auth-page-marker) .ss-forgot-password {
    margin-top: 0.55rem;
    color: var(--text-muted);
    font-size: 0.7rem;
    text-align: right;
}

.stApp:has(.auth-page-marker) .ss-auth-footer-copy {
    color: var(--text-muted);
    font-size: 0.78rem;
    line-height: 2rem;
    text-align: right;
}

.stApp:has(.auth-page-marker) .stButton > button[kind="tertiary"] {
    min-height: 2rem;
    padding: 0 !important;
    color: var(--warning) !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 800 !important;
}

.stApp:has(.auth-page-marker) .stButton > button[kind="tertiary"]:hover {
    color: var(--warning) !important;
    text-decoration: underline;
}

.stApp:has(.auth-page-marker) .ss-auth-title {
    color: var(--text) !important;
}

.stApp:has(.auth-page-marker) .ss-auth-heading-accent,
.stApp:has(.auth-page-marker) .ss-auth-brand span {
    color: var(--warning) !important;
}

.stApp:has(.auth-page-marker) .ss-auth-subtitle,
.stApp:has(.auth-page-marker) .ss-auth-footer {
    color: var(--text-muted) !important;
}

.stApp:has(.auth-page-marker) .stButton > button[kind="primary"] {
    width: 100%;
    background: var(--warning) !important;
    color: var(--bg) !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 20px -5px color-mix(in srgb, var(--warning) 1%, transparent) !important;
}

.stApp:has(.auth-page-marker) .stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 15px 25px -5px color-mix(in srgb, var(--warning) 1%, transparent) !important;
}

.stApp:has(.auth-page-marker) .stButton > button[kind="secondary"] {
    color: var(--text) !important;
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-radius: 12px !important;
}

.stApp:has(.auth-page-marker) .ss-auth-or {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 1.15rem 0 0.75rem;
    color: var(--text-muted);
    font-size: 0.62rem;
    letter-spacing: 0.14em;
}

.stApp:has(.auth-page-marker) .ss-auth-or::before,
.stApp:has(.auth-page-marker) .ss-auth-or::after {
    height: 1px;
    flex: 1;
    content: "";
    background: color-mix(in srgb, var(--glass-highlight) 1%, transparent);
}

@keyframes authCardReveal {
    from { opacity: 1; }
    to { opacity: 0; }
}

@keyframes authContentIn {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes authCardIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes authEdgeSpin {
    to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
    .stApp:has(.auth-page-marker)::after,
    .stApp:has(.auth-page-marker)
    [data-testid="stMainBlockContainer"]
    > [data-testid="stVerticalBlock"]
    > [data-testid="stLayoutWrapper"]
    > [data-testid="stHorizontalBlock"]
    > div[data-testid="stColumn"]:nth-child(2)::before,
    .stApp:has(.auth-page-marker)
    [data-testid="stMainBlockContainer"]
    > [data-testid="stVerticalBlock"]
    > [data-testid="stLayoutWrapper"]
    > [data-testid="stHorizontalBlock"]
    > div[data-testid="stColumn"]:nth-child(2)::after,
    .stApp:has(.auth-page-marker)
    [data-testid="stMainBlockContainer"]
    > [data-testid="stVerticalBlock"]
    > [data-testid="stLayoutWrapper"]
    > [data-testid="stHorizontalBlock"]
    > div[data-testid="stColumn"]:nth-child(2)
    > [data-testid="stVerticalBlock"] {
        animation: none !important;
    }
}

/* Stable keyed auth surface: animation names are swapped by the page render. */
.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2) {
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    clip-path: none !important;
    overflow: visible !important;
    animation: none !important;
}

.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::before,
.stApp:has(.auth-page-marker)
[data-testid="stMainBlockContainer"]
> [data-testid="stVerticalBlock"]
> [data-testid="stLayoutWrapper"]
> [data-testid="stHorizontalBlock"]
> div[data-testid="stColumn"]:nth-child(2)::after {
    display: none !important;
}

.stApp:has(.auth-page-marker) .st-key-auth_card {
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 460px;
    min-height: 420px;
    margin: 0 auto;
    padding: 32px !important;
    overflow: hidden;
    background: color-mix(in srgb, var(--glass-shadow) 1%, transparent) !important;
    border: 1px solid color-mix(in srgb, var(--glass-highlight) 1%, transparent) !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 60px color-mix(in srgb, var(--glass-shadow) 1%, transparent) !important;
    clip-path: polygon(0 4%, 4% 0, 100% 0, 100% 96%, 96% 100%, 0 100%);
}

.stApp:has(.auth-page-marker) .st-key-auth_card::before {
    position: absolute;
    z-index: 1;
    inset: 0;
    pointer-events: none;
    content: "";
    border: 1px solid transparent;
    border-radius: 20px;
    background: conic-gradient(
        from 0deg,
        transparent 0deg,
        transparent 240deg,
        color-mix(in srgb, var(--warning) 1%, transparent) 280deg,
        transparent 320deg,
        transparent 360deg
    ) border-box;
    -webkit-mask:
        linear-gradient(var(--bg) 0 0) padding-box,
        linear-gradient(var(--bg) 0 0);
    -webkit-mask-composite: xor;
    mask:
        linear-gradient(var(--bg) 0 0) padding-box,
        linear-gradient(var(--bg) 0 0);
    mask-composite: exclude;
    animation: authEdgeSpin 8s linear infinite;
}

.stApp:has(.auth-page-marker) .st-key-auth_card::after {
    position: absolute;
    z-index: 10;
    inset: 0;
    pointer-events: none;
    content: "";
    background-image:
        linear-gradient(
            135deg,
            transparent 0 43%,
            color-mix(in srgb, var(--glass-highlight) 1%, transparent) 48%,
            transparent 55%
        ),
        color-mix(in srgb, var(--glass-shadow) 1%, transparent);
    background-position: center, center, center;
    background-repeat: no-repeat;
    border-radius: 20px;
    clip-path: polygon(0 4%, 4% 0, 100% 0, 100% 96%, 96% 100%, 0 100%);
    opacity: 1;
    animation: swapA 1s ease forwards;
}

.stApp:has(.auth-page-marker) .st-key-auth_card::after {
    box-shadow:
        0 0 0 1px var(--warning),
        0 0 30px color-mix(in srgb, var(--warning) 1%, transparent);
}

.stApp:has(.auth-page-marker) .st-key-auth_card
> * {
    position: relative;
    z-index: 5;
    animation: formA 1s ease forwards;
}

@keyframes swapA {
    0%, 45% {
        opacity: 1;
        box-shadow:
            0 0 0 1px var(--warning),
            0 0 30px color-mix(in srgb, var(--warning) 1%, transparent);
    }
    100% {
        opacity: 0;
        box-shadow: none;
    }
}

@keyframes swapB {
    0%, 45% {
        opacity: 1;
        box-shadow:
            0 0 0 1px var(--warning),
            0 0 30px color-mix(in srgb, var(--warning) 1%, transparent);
    }
    100% {
        opacity: 0;
        box-shadow: none;
    }
}

@keyframes formA {
    0%, 40% {
        opacity: 0;
        transform: translateY(14px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes formB {
    0%, 40% {
        opacity: 0;
        transform: translateY(14px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {
    .stApp:has(.auth-page-marker) .st-key-auth_card::before,
    .stApp:has(.auth-page-marker) .st-key-auth_card::after,
    .stApp:has(.auth-page-marker) .st-key-auth_card > * {
        animation: none !important;
        box-shadow: none !important;
        opacity: 1 !important;
        transform: none !important;
    }
}
"""


def get_theme_css(theme_mode="dark"):
    """Return the complete design system stylesheet for the selected mode."""

    if theme_mode not in ("dark", "light"):
        raise ValueError("theme_mode must be 'dark' or 'light'.")

    base_css = "\n".join(
        line.strip() for line in _CSS.splitlines() if line.strip()
    )
    theme_css = _DARK_THEME_CSS if theme_mode == "dark" else _LIGHT_THEME_CSS
    return (
        f"{base_css}\n{_FINTECH_THEME_CSS}\n{theme_css}\n"
        f"{_CINEMATIC_AUTH_CSS}"
    )


def apply_styles(theme_mode=None):
    """Inject the selected theme stylesheet across the current app view."""

    theme_mode = theme_mode or st.session_state.get("app_theme", "dark")
    css = get_theme_css(theme_mode)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
