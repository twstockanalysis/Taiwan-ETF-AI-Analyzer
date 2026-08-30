"""Streamlit 全站響應式字體與可讀性設定。"""

from __future__ import annotations

import streamlit as st


GOODCAT_PALETTE = {
    "canvas": "#F7F7F4",
    "surface": "#FFFFFF",
    "primary_text": "#343740",
    "secondary_text": "#6F737C",
    "cat_gray": "#5B5E69",
    "soft_pink": "#DFA5B4",
    "border": "#D9DADF",
}


GOODCAT_DARK_PALETTE = {
    "canvas": "#1E1B18",
    "surface": "#2A2724",
    "primary_text": "#FDFBF7",
    "secondary_text": "#A8A29E",
    "cat_orange": "#F59E0B",
    "border": "#3D3732",
}


GLOBAL_STYLE_MARKER = (
    "tw-etf-responsive-typography"
)


GLOBAL_STYLES = f"""
<style id="{GLOBAL_STYLE_MARKER}">
:root {{
    --tw-etf-metric-size:
        clamp(1.15rem, 2.1vw, 1.9rem);
    --tw-etf-metric-size-narrow:
        clamp(1.05rem, 3.2vw, 1.45rem);
}}

[data-testid="stMainBlockContainer"] h1 {{
    font-size:
        clamp(1.75rem, 3vw, 2.25rem);
    line-height: 1.2;
}}

[data-testid="stMainBlockContainer"] h2 {{
    font-size:
        clamp(1.35rem, 2.3vw, 1.75rem);
    line-height: 1.25;
}}

[data-testid="stMainBlockContainer"] h3 {{
    font-size:
        clamp(1.1rem, 1.9vw, 1.35rem);
    line-height: 1.3;
}}

[data-testid="stSidebar"] {{
    font-size: 0.9rem;
}}

[data-testid="stSidebar"]
[data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"]
[data-testid="stPageLink"] p,
[data-testid="stSidebarNav"] span {{
    font-size: 0.9rem !important;
    line-height: 1.35 !important;
}}

[data-testid="stMetric"] {{
    min-width: 0;
}}

[data-testid="stMetricLabel"] p {{
    font-size: 0.8rem !important;
    line-height: 1.25 !important;
    white-space: normal !important;
}}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] > div {{
    font-size:
        var(--tw-etf-metric-size) !important;
    line-height: 1.15 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: anywhere !important;
}}

[data-testid="stMetricDelta"] {{
    font-size: 0.78rem !important;
}}

.st-key-performance-ranking-limit
[data-testid="stMarkdownContainer"] p {{
    font-size:
        var(--tw-etf-metric-size) !important;
    line-height: 1.15 !important;
    margin: 0 !important;
}}

.st-key-etf-search-summary hr {{
    margin-top: 0 !important;
}}

[data-testid="stVerticalBlock"][class*="-card"],
.st-key-etf-detail-summary,
.st-key-etf-detail-performance,
.st-key-etf-detail-dividend-summary,
.st-key-home-primary-action {{
    padding-top: 10px !important;
}}

.st-key-etf-detail-dividend-summary
[data-testid="stCaptionContainer"] p {{
    font-size: 0.75rem !important;
}}

.st-key-etf-detail-dividend-summary
[data-testid="stElementToolbar"] {{
    display: none !important;
}}

.st-key-etf-detail-performance
[data-testid="stElementToolbar"] {{
    display: none !important;
}}

.st-key-dividend-event-header {{
    padding-left: 2.3rem;
    padding-right: 1rem;
    padding-top: 0.4rem;
    padding-bottom: 0.4rem;
    overflow: hidden;
    border-radius: 0.45rem;
    background: var(--secondary-background-color);
}}

.st-key-dividend-event-header p,
.st-key-etf-detail-dividend-summary details summary p {{
    font-family:
        "Cascadia Mono", "Noto Sans Mono CJK TC", monospace !important;
    white-space: pre !important;
    width: 100%;
    min-width: 0;
    font-size:
        clamp(0.72rem, 1.35vw, 0.875rem)
        !important;
    line-height: 1.6 !important;
    font-weight: 400 !important;
}}

.st-key-dividend-event-header
.dividend-event-grid-header {{
    display: inline-grid;
    font-family:
        "Cascadia Mono", "Noto Sans Mono CJK TC", monospace !important;
    font-size:
        clamp(0.72rem, 1.35vw, 0.875rem)
        !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
    white-space: pre !important;
    grid-template-columns:
        8ch max-content
        11ch max-content
        8ch max-content
        12ch max-content
        auto;
    align-items: center;
}}

.st-key-etf-detail-dividend-summary details {{
    overflow: hidden;
}}

@media (min-width: 769px) {{
    [data-testid="stSidebarNav"] {{
        margin-top: 3.75rem;
    }}
}}

[data-testid="stPageLink"] p {{
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.4 !important;
}}

.st-key-home-primary-action [data-testid="stPageLink"] a {{
    min-height: 3.75rem !important;
    padding: 0.8rem 1.25rem !important;
}}

.st-key-home-primary-action [data-testid="stPageLink"] p {{
    font-size: clamp(1.35rem, 2.4vw, 1.7rem) !important;
    font-weight: 700 !important;
}}

.st-key-home-primary-action [data-testid="stPageLink"] svg {{
    width: 1.5rem !important;
    height: 1.5rem !important;
}}

.st-key-home-slogan h4 {{
    margin-bottom: 0 !important;
    font-size: clamp(1rem, 1.5vw, 1.15rem) !important;
    line-height: 1.25 !important;
}}

.performance-ranking-scroll {{
    width: 100%;
    overflow-x: auto;
    border-radius: 12px;
}}

.performance-ranking-grid {{
    min-width: 920px;
}}

.performance-ranking-grid.etf-search-grid {{
    min-width: 0;
}}

.performance-ranking-header,
.performance-ranking-row {{
    display: grid;
    grid-template-columns:
        minmax(4.5rem, 0.55fr)
        minmax(5.5rem, 0.7fr)
        minmax(13rem, 2.35fr)
        minmax(7.5rem, 0.95fr)
        minmax(8.5rem, 1.05fr)
        minmax(7.5rem, 0.95fr)
        minmax(6rem, 0.75fr);
    column-gap: 1rem;
    align-items: center;
    padding: 0 1rem;
}}

.etf-search-grid .performance-ranking-header,
.etf-search-grid .performance-ranking-row {{
    box-sizing: border-box;
    grid-template-columns: var(--etf-search-columns);
}}

.performance-ranking-header {{
    min-height: 2.6rem;
    position: sticky;
    top: 0;
    z-index: 1;
    color: color-mix(
        in srgb,
        var(--text-color) 68%,
        transparent
    );
    background: var(--secondary-background-color);
    font-size: 0.875rem;
}}

.performance-ranking-row {{
    min-height: 3.65rem;
    color: var(--text-color);
    background: var(--background-color);
    text-decoration: none !important;
    transition: background-color 120ms ease;
}}

.performance-ranking-row:hover,
.performance-ranking-row:focus-visible {{
    color: var(--text-color);
    background: var(--secondary-background-color);
    text-decoration: none !important;
    outline: none;
}}

.performance-ranking-cell {{
    min-width: 0;
    overflow-wrap: anywhere;
}}

.st-key-public-planner-holdings [data-testid="stElementToolbar"],
.st-key-performance_ranking_detail_action
[data-testid="stElementToolbar"] {{
    display: none !important;
}}

.st-key-etf_search_detail_action [data-testid="stElementToolbar"] {{
    display: none !important;
}}

.st-key-public-planner-holdings
.stDataFrameGlideDataEditor {{
    --gdg-bg-cell: var(--secondary-background-color) !important;
    --gdg-bg-cell-medium: var(--secondary-background-color) !important;
}}

.st-key-public-planner-holdings
.stDataFrameGlideDataEditor,
.st-key-performance_ranking_detail_action
.stDataFrameGlideDataEditor {{
    --gdg-bg-icon-header: transparent !important;
    --gdg-fg-icon-header: transparent !important;
}}

.st-key-public-planner-holdings
[data-testid="stDataFrameResizable"]::after,
.st-key-performance_ranking_detail_action
[data-testid="stDataFrameResizable"]::after {{
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 36px;
    z-index: 3;
    cursor: default;
}}

@media (max-width: 1100px) {{
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div {{
        font-size:
            var(--tw-etf-metric-size-narrow)
            !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    [data-testid="stPageLink"] p {{
        font-size: 0.9rem !important;
    }}

    .st-key-home-primary-action [data-testid="stPageLink"] p {{
        font-size: 1.3rem !important;
    }}

    .st-key-home-primary-action [data-testid="stPageLink"] a {{
        min-height: 3.5rem !important;
    }}
}}

@media (max-width: 768px) {{
    [class*="st-key-public-planner-month-row-"]
    [data-testid="stHorizontalBlock"] {{
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 0.75rem !important;
    }}

    [class*="st-key-public-planner-month-row-"]
    [data-testid="stColumn"] {{
        width: auto !important;
        min-width: 0 !important;
        flex: unset !important;
    }}
}}
</style>
"""


def apply_global_styles() -> None:
    """注入全站共用響應式 CSS。"""

    st.markdown(
        GLOBAL_STYLES,
        unsafe_allow_html=True,
    )
