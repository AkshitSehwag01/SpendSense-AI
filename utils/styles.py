"""Small, token-based styles for the Streamlit application."""

import streamlit as st


_CSS = """
:root {
    --primary: #10B981;
    --accent: #10B981;
    --surface: #111B2D;
    --surface-muted: #172235;
    --border: #2A3B52;
    --text: #F8FAFC;
    --text-muted: #AAB8CA;
    --success: #34D399;
    --danger: #FB7185;
    --warning: #FBBF24;
    --radius: 14px;
}

html, body, .stApp {
    color: var(--text);
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
}

.stApp {
    background: var(--surface);
}

.block-container {
    max-width: 1680px;
    padding: 2rem 2.2rem 80px;
}

h1, h2, h3, h4, .ss-page-title, .ss-section-title {
    color: var(--text);
    font-weight: 700;
    letter-spacing: -0.03em;
}

p, label, li, .ss-subtitle, .ss-muted {
    color: var(--text-muted);
}

a {
    color: var(--accent);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border-color: var(--border);
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    min-height: 42px;
    border-radius: 10px;
    border: 1px solid var(--primary);
    color: #FFFFFF;
    background: var(--primary);
    font-weight: 700;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: var(--accent);
    background: var(--accent);
    filter: brightness(1.05);
}

.ss-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 4px 12px;
}

.ss-brand-logo {
    display: grid;
    width: 44px;
    height: 44px;
    place-items: center;
    border-radius: 13px;
    background: var(--primary);
}

.ss-brand-name {
    color: var(--text);
    font-size: 1.15rem;
    font-weight: 800;
}

.ss-brand-tag, .ss-side-label {
    color: var(--text-muted);
}

.ss-side-label {
    margin: 16px 0 8px 4px;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.ss-eyebrow {
    color: var(--accent);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.16em;
}

.ss-page-title {
    margin: 0;
    font-size: clamp(1.8rem, 2.6vw, 2.3rem);
}

.ss-subtitle {
    max-width: 62ch;
    margin: 0.5rem 0 1.2rem;
    font-size: 0.92rem;
}

.ss-section-title {
    font-size: 1.05rem;
}

.ss-muted {
    font-size: 0.8rem;
}

.ss-pill,
.ss-delta-chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    color: var(--accent);
    font-size: 0.75rem;
    font-weight: 700;
}

.ss-pill {
    padding: 4px 10px;
}

.ss-delta-chip {
    padding: 5px 10px;
}

.ss-delta-chip.danger, .ss-expense {
    color: var(--danger);
}

.ss-delta-chip.success, .ss-income {
    color: var(--success);
}

.ss-hero-card,
.ss-recurring-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface-muted);
}

.ss-hero-value {
    color: var(--text);
    font-family: "JetBrains Mono", Consolas, monospace;
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 800;
}

.ss-sparkline {
    width: 150px;
    height: 72px;
}

.ss-sparkline-base {
    fill: none;
    stroke: var(--border);
}

.ss-sparkline-line {
    fill: none;
    stroke: var(--accent);
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 3;
}

.ss-transaction-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid var(--border);
}

.ss-category-icon {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    place-items: center;
    border-radius: 50%;
    background: color-mix(in srgb, var(--accent) 12%, transparent);
}

.ss-transaction-main {
    display: grid;
    flex: 1;
    min-width: 0;
    gap: 2px;
}

.ss-transaction-main strong {
    overflow: hidden;
    color: var(--text);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.ss-transaction-main span {
    color: var(--text-muted);
    font-size: 0.76rem;
}

.ss-budget-row {
    display: grid;
    gap: 6px;
    margin: 16px 0 18px;
}

.ss-budget-row-header,
.ss-budget-caption {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.ss-budget-category {
    overflow: hidden;
    color: var(--text);
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.ss-budget-amount {
    color: var(--text-muted);
    font-size: 0.8rem;
    white-space: nowrap;
}

.ss-budget-track {
    height: 8px;
    overflow: hidden;
    border-radius: 999px;
    background: var(--surface-muted);
}

.ss-budget-fill {
    height: 100%;
    border-radius: inherit;
}

.ss-budget-fill--ok { background: var(--success); }
.ss-budget-fill--warning { background: var(--warning); }
.ss-budget-fill--danger { background: var(--danger); }
.ss-budget-caption--ok { color: var(--success); }
.ss-budget-caption--warning { color: var(--warning); }
.ss-budget-caption--danger { color: var(--danger); }

.ss-goal-summary {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0;
}

.ss-goal-ring {
    display: grid;
    width: 52px;
    height: 52px;
    place-items: center;
    border-radius: 50%;
    background: conic-gradient(
        var(--accent) var(--goal-progress),
        var(--surface-muted) 0
    );
}

.ss-goal-ring span {
    color: var(--text);
    font-family: "JetBrains Mono", Consolas, monospace;
    font-size: 0.72rem;
    font-weight: 700;
}

.ss-money {
    font-variant-numeric: tabular-nums;
}

.ss-auth-header {
    margin-bottom: 1.5rem;
    text-align: center;
}

.ss-auth-brand {
    color: var(--accent);
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.ss-auth-title {
    color: var(--text);
}

.ss-auth-subtitle,
.ss-auth-form-heading span,
.ss-auth-footer-copy {
    color: var(--text-muted);
}

.ss-auth-form-heading {
    display: grid;
    gap: 0.3rem;
    margin-bottom: 1.1rem;
}

.ss-auth-or {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    color: var(--text-muted);
    font-size: 0.7rem;
}

@media (max-width: 900px) {
    .block-container {
        padding: 1.4rem 1rem 80px;
    }
}

@media (max-width: 700px) {
    .block-container {
        padding: 1rem 0.65rem 80px;
    }

    .ss-hero-card {
        flex-wrap: wrap;
    }

    .ss-sparkline {
        width: 96px;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }
}
"""


def get_theme_css(theme_mode="dark"):
    """Return the safe, token-based stylesheet for the selected mode."""

    if theme_mode not in ("dark", "light"):
        raise ValueError("theme_mode must be 'dark' or 'light'.")

    if theme_mode == "light":
        return _CSS.replace(
            "--surface: #111B2D;",
            "--surface: #FFFFFF;",
        ).replace(
            "--surface-muted: #172235;",
            "--surface-muted: #F1F5F9;",
        ).replace(
            "--border: #2A3B52;",
            "--border: #D7E0EA;",
        ).replace(
            "--text: #F8FAFC;",
            "--text: #0F172A;",
        ).replace(
            "--text-muted: #AAB8CA;",
            "--text-muted: #475569;",
        )

    return _CSS


def apply_styles(theme_mode=None):
    """Inject the selected safe stylesheet."""

    theme_mode = theme_mode or st.session_state.get("app_theme", "dark")
    st.markdown(
        f"<style>{get_theme_css(theme_mode)}</style>",
        unsafe_allow_html=True,
    )
