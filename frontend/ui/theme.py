"""Streamlit 全站響應式字體與可讀性設定。"""

from __future__ import annotations

import streamlit as st


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

[data-testid="stPageLink"] p {{
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.4 !important;
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
}}
</style>
"""


def apply_global_styles() -> None:
    """注入全站共用響應式 CSS。"""

    st.markdown(
        GLOBAL_STYLES,
        unsafe_allow_html=True,
    )
