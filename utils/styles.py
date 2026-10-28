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
            rgba(16, 185, 129, 0.10), transparent 60%),
        radial-gradient(900px 480px at -8% 0%,
            rgba(14, 165, 233, 0.08), transparent 55%),
        #0B1120;
    background-attachment: fixed;
    color: #F1F5F9;
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

::selection {
    background: rgba(16, 185, 129, 0.35);
}

::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #26364B;
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: #34D399;
}

/* =====================================================
   TYPOGRAPHY
   ===================================================== */

h1, h2, h3, h4 {
    color: #F8FAFC !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em;
}

p, label, li {
    color: #CBD5E1;
}

a {
    color: #34D399 !important;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border-color: #26364B;
}

.ss-eyebrow {
    color: #34D399;
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
    background: linear-gradient(90deg, #F8FAFC 0%, #BFD3EA 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.ss-subtitle {
    color: #93A4BA;
    font-size: 0.92rem;
    margin-top: 0.5rem;
    margin-bottom: 1.2rem;
    max-width: 62ch;
}

.ss-section-title {
    color: #F1F5F9;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem;
}

.ss-muted {
    color: #91A0B5;
    font-size: 0.8rem;
}

.ss-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    background: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

/* =====================================================
   CARDS AND CONTAINERS
   ===================================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #26364B;
    border-radius: 18px;
    background: linear-gradient(
        150deg,
        rgba(19, 29, 45, 0.97),
        rgba(13, 21, 34, 0.97)
    );
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.14);
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #172235 0%, #111A29 100%);
    border: 1px solid #2A3B52;
    border-radius: 17px;
    padding: 20px 22px;
    min-height: 116px;
    box-shadow: 0 10px 26px rgba(0, 0, 0, 0.13);
    transition: border-color 0.18s ease, transform 0.18s ease;
}

[data-testid="stMetric"]:hover {
    border-color: #10B981;
    transform: translateY(-2px);
}

[data-testid="stMetricLabel"] p {
    color: #9EAFC5 !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-size: clamp(1.35rem, 2vw, 2rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.035em;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

div[data-testid="stForm"] {
    background: rgba(15, 24, 41, 0.6);
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #26364B;
}

[data-testid="stExpander"] details {
    border: 1px solid #26364B;
    border-radius: 14px;
    background: rgba(15, 24, 41, 0.6);
}

[data-testid="stExpander"] summary:hover {
    color: #34D399;
}

[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.15);
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border: 1px solid #26354A;
    border-radius: 14px;
    overflow: hidden;
}

/* =====================================================
   FORM CONTROLS
   ===================================================== */

[data-testid="stWidgetLabel"] p {
    color: #E2E8F0 !important;
    font-weight: 600;
    font-size: 0.86rem;
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: #0F1829 !important;
    border: 1px solid #2A3B52 !important;
    border-radius: 10px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: #10B981 !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.16) !important;
}

input, textarea {
    background: transparent !important;
    color: #F1F5F9 !important;
}

input::placeholder,
textarea::placeholder {
    color: #64748B !important;
}

span[data-baseweb="tag"] {
    background: rgba(16, 185, 129, 0.18) !important;
    border-radius: 8px !important;
}

span[data-baseweb="tag"] span {
    color: #A7F3D0 !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: #111B2D !important;
}

li[role="option"]:hover {
    background: rgba(16, 185, 129, 0.12) !important;
}

[data-baseweb="tab-highlight"] {
    background: #10B981 !important;
}

div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #0EA5E9, #10D6A0);
    border-radius: 999px;
}

/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #FFFFFF !important;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 42px;
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.18);
    transition: transform 0.15s ease, filter 0.15s ease,
        box-shadow 0.15s ease;
}

.stButton > button p,
.stDownloadButton > button p,
.stFormSubmitButton > button p {
    color: #FFFFFF !important;
    font-weight: 700;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    color: #FFFFFF !important;
    filter: brightness(1.08);
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(16, 185, 129, 0.28);
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
    background: linear-gradient(180deg, #0D1524 0%, #101B2D 100%);
    border-right: 1px solid #233249;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #CBD5E1;
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
    background: linear-gradient(135deg, #10B981, #0EA5E9);
    box-shadow: 0 8px 22px rgba(16, 185, 129, 0.3);
}

.ss-brand-name {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: -0.035em;
    line-height: 1.1;
    color: #F8FAFC;
}

.ss-brand-tag {
    font-size: 0.72rem;
    color: #7F90A8;
    margin-top: 3px;
}

.ss-side-label {
    color: #64748B;
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
    background: rgba(148, 163, 184, 0.08);
}

[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-of-type {
    display: none;
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: #AAB8CA;
    font-size: 0.92rem;
    font-weight: 500;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(
        90deg,
        rgba(16, 185, 129, 0.2),
        rgba(16, 185, 129, 0.04)
    );
    border-color: rgba(16, 185, 129, 0.35);
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #F8FAFC !important;
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
            rgba(16, 185, 129, 0.12), transparent 60%),
        radial-gradient(900px 480px at -8% 0%,
            rgba(14, 165, 233, 0.10), transparent 55%),
        #070B14;
    color: #F1F5F9;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(148, 163, 184, 0.18);
    background: linear-gradient(
        150deg,
        rgba(19, 29, 45, 0.72),
        rgba(13, 21, 34, 0.68)
    );
    backdrop-filter: blur(18px);
}

[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        rgba(23, 34, 53, 0.82),
        rgba(17, 26, 41, 0.78)
    );
    backdrop-filter: blur(16px);
}
"""

_LIGHT_THEME_CSS = """
.stApp {
    background: #F8FAFC;
    color: #0F172A;
}

[data-testid="stHeader"] {
    background: rgba(248, 250, 252, 0.9);
}

html, body, .stApp,
p, label, li, [data-testid="stWidgetLabel"] p,
[data-testid="stMarkdownContainer"] {
    color: #334155;
}

h1, h2, h3, h4,
.ss-section-title,
[data-testid="stMetricValue"] {
    color: #0F172A !important;
}

.ss-page-title {
    background: linear-gradient(90deg, #0F172A 0%, #475569 100%);
    -webkit-background-clip: text;
    background-clip: text;
}

.ss-subtitle, .ss-muted {
    color: #64748B;
}

a {
    color: #047857 !important;
}

hr {
    border-color: #E2E8F0;
}

div[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMetric"],
div[data-testid="stForm"],
[data-testid="stExpander"] details,
[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border-color: #E2E8F0;
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    backdrop-filter: blur(12px);
}

[data-testid="stMetricLabel"] p,
[data-testid="stWidgetLabel"] p {
    color: #475569 !important;
}

[data-testid="stMetricValue"] {
    color: #0F172A !important;
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}

input, textarea {
    color: #0F172A !important;
}

input::placeholder, textarea::placeholder {
    color: #94A3B8 !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: #FFFFFF !important;
}

li[role="option"] {
    color: #0F172A !important;
}

li[role="option"]:hover {
    background: #ECFDF5 !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #F1F5F9 100%);
    border-right-color: #E2E8F0;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #475569;
}

.ss-brand-name {
    color: #0F172A;
}

.ss-brand-tag, .ss-side-label {
    color: #64748B;
}

.ss-auth-brand,
.ss-auth-form-heading strong {
    color: #0F172A;
}

.ss-auth-title {
    color: #0F172A !important;
}

.ss-auth-subtitle,
.ss-auth-form-heading span {
    color: #64748B;
}

.ss-auth-logo {
    color: #047857;
    border-color: rgba(5, 150, 105, 0.28);
    background: linear-gradient(
        145deg,
        rgba(16, 185, 129, 0.12),
        rgba(6, 182, 212, 0.08)
    );
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: #475569;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #0F172A !important;
}

::-webkit-scrollbar-thumb {
    background: #CBD5E1;
}

::-webkit-scrollbar-thumb:hover {
    background: #10B981;
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    border-color: #E2E8F0;
}
"""

_FINTECH_THEME_CSS = """
/* =====================================================
   SPENDSENSE AI · FINTECH DESIGN SYSTEM
   ===================================================== */

:root {
    --ss-obsidian: #070A12;
    --ss-surface: rgba(15, 23, 42, 0.55);
    --ss-border: rgba(255, 255, 255, 0.08);
    --ss-emerald: #10B981;
    --ss-cyan: #06B6D4;
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
            rgba(16, 185, 129, 0.05),
            transparent 64%
        ),
        radial-gradient(
            850px 650px at 108% 112%,
            rgba(6, 182, 212, 0.04),
            transparent 62%
        ),
        #070A12;
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
    background: linear-gradient(110deg, #10B981 0%, #06B6D4 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 14px rgba(16, 185, 129, 0.24));
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
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
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
        rgba(16, 185, 129, 0.10),
        transparent 70%
    );
    transition: opacity 180ms ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover,
[data-testid="stMetric"]:hover,
div[data-testid="stForm"]:hover {
    transform: translateY(-2px);
    border-color: rgba(16, 185, 129, 0.3);
    box-shadow:
        0 14px 34px -12px rgba(0, 0, 0, 0.6),
        inset 0 0 24px rgba(16, 185, 129, 0.06);
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
    border: 1px solid rgba(16, 185, 129, 0.62);
    border-radius: 999px;
    background: linear-gradient(
        135deg,
        rgba(16, 185, 129, 0.96),
        rgba(5, 150, 105, 0.96)
    );
    box-shadow:
        0 8px 22px rgba(16, 185, 129, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transition:
        transform 160ms ease,
        box-shadow 160ms ease,
        filter 160ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    border-color: rgba(110, 231, 183, 0.9);
    box-shadow:
        0 12px 30px rgba(16, 185, 129, 0.28),
        0 0 20px rgba(16, 185, 129, 0.14);
}

div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.03) !important;
    border-color: rgba(148, 163, 184, 0.22) !important;
    border-radius: 12px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.025);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within,
input:focus, textarea:focus {
    border-color: rgba(16, 185, 129, 0.5) !important;
    box-shadow:
        0 0 0 3px rgba(16, 185, 129, 0.1),
        0 0 18px rgba(16, 185, 129, 0.18) !important;
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
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 14px;
    color: #6EE7B7;
    background: linear-gradient(
        145deg,
        rgba(16, 185, 129, 0.2),
        rgba(6, 182, 212, 0.12)
    );
    box-shadow:
        0 0 28px rgba(16, 185, 129, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.16);
    font-size: 1.5rem;
}

.ss-auth-brand {
    color: #E2E8F0;
    font-family: var(--ss-heading);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.ss-auth-brand span {
    color: #10B981;
}

.ss-auth-title {
    margin: 1rem 0 0.45rem;
    color: #F8FAFC !important;
    font-size: clamp(2rem, 5vw, 2.65rem) !important;
}

.ss-auth-subtitle,
.ss-auth-form-heading span {
    color: #94A3B8;
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
    color: #F1F5F9;
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
    color: #6EE7B7;
    border-color: rgba(16, 185, 129, 0.30);
    background: rgba(16, 185, 129, 0.10);
}

.pulse-badge-success::before {
    background: #10B981;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.65);
}

.pulse-badge-warning {
    color: #FCD34D;
    border-color: rgba(245, 158, 11, 0.30);
    background: rgba(245, 158, 11, 0.10);
}

.pulse-badge-warning::before {
    background: #F59E0B;
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.65);
}

.pulse-badge-danger {
    color: #FDA4AF;
    border-color: rgba(244, 63, 94, 0.30);
    background: rgba(244, 63, 94, 0.10);
}

.pulse-badge-danger::before {
    background: #F43F5E;
    box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.65);
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
    background: #070A12;
}

::-webkit-scrollbar-thumb {
    border: 2px solid #070A12;
    border-radius: 999px;
    background: #26364B;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(#10B981, #06B6D4);
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
    return f"{base_css}\n{_FINTECH_THEME_CSS}\n{theme_css}"


def apply_styles(theme_mode=None):
    """Inject the selected theme stylesheet across the current app view."""

    theme_mode = theme_mode or st.session_state.get("app_theme", "dark")
    css = get_theme_css(theme_mode)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
