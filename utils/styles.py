import streamlit as st


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

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

def apply_styles():
    """Apply SpendSense AI's design system."""

    # Remove blank lines and indentation so Markdown never
    # misreads the stylesheet as code.
    css = "\n".join(
        line.strip() for line in _CSS.splitlines() if line.strip()
    )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
