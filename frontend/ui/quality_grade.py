"""公開探索頁共用的 ETF 喵喵評等呈現。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import (
    fetch_historical_quality_grades,
    quality_grade_lookup,
)
from frontend.ui.assessment import historical_quality_presentation


@st.cache_data(ttl=300, max_entries=64, show_spinner=False)
def load_historical_quality_grade_lookup(
    api_base_url: str,
    codes: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """批次取得公開安全評等並短暫快取。"""

    response = fetch_historical_quality_grades(
        api_base_url=api_base_url,
        codes=codes,
    )
    return quality_grade_lookup(response)


def quality_grade_short_label(payload: object) -> str:
    """回傳列表使用的簡短字母評等。"""

    presentation = historical_quality_presentation(payload)
    return presentation.label.removeprefix("喵喵評等：").strip()


def render_historical_quality_evidence(
    payload: object,
    *,
    compact: bool = False,
    show_owner_details: bool = False,
) -> None:
    """呈現字母評等與公開理由，不洩漏內部分數。"""

    grade = historical_quality_presentation(payload)
    source = payload if isinstance(payload, dict) else {}

    st.badge(grade.label, color=grade.color)
    if grade.label != "喵喵評等：暫無" or show_owner_details:
        st.caption(grade.explanation)

    if compact:
        return

    strengths = source.get("strengths")
    risks = source.get("risks")
    unavailable = source.get("unavailable_evidence")

    if isinstance(strengths, list) and strengths:
        st.write("**歷史優點：** " + "；".join(str(item) for item in strengths))
    if isinstance(risks, list) and risks:
        st.write("**需要留意：** " + "；".join(str(item) for item in risks))
    if (
        show_owner_details
        and isinstance(unavailable, list)
        and unavailable
    ):
        lines = "  \n".join(
            f"{item}；" for item in unavailable
        )
        st.markdown(f"**原因：**  \n{lines}")
