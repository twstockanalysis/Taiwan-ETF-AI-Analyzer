"""TW ETF AI Analyzer 首頁。"""

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_api_health,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.ui.states import (
    render_api_error,
)


@st.cache_data(
    ttl=15,
    show_spinner=False,
)
def load_api_health(
    api_base_url: str,
) -> dict[str, str]:
    """取得並暫存 FastAPI 健康狀態。

    Args:
        api_base_url:
            FastAPI Base URL。

    Returns:
        dict[str, str]:
            FastAPI 健康狀態。
    """

    return fetch_api_health(
        api_base_url
    )


def render_home() -> None:
    """顯示網站首頁。"""

    st.title("TW ETF AI Analyzer")

    st.caption(
        "台灣 ETF 資料查詢與分析網站"
    )

    st.markdown(
        """
        第一版網站將提供：

        - ETF 基本資料查詢
        - 主動式與被動式 ETF 篩選
        - 債券 ETF 排除
        - ETF 關鍵字搜尋
        - 1M／3M／6M／1Y 績效排行榜
        - ETF 多期間市價績效
        - ETF 配息歷史與實際 76W 分析
        - 正式配息資料品質與來源覆蓋率
        - 正式官方資料更新
        """
    )

    st.divider()

    st.subheader("系統狀態")

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    st.caption(
        f"FastAPI：`{api_base_url}`"
    )

    if st.button(
        "重新檢查後端",
        type="secondary",
    ):
        load_api_health.clear()

    try:
        health = load_api_health(
            api_base_url
        )

    except APIClientError as error:
        render_api_error(
            "目前無法連接 FastAPI 後端。",
            error,
            hint=(
                "請確認 FastAPI 已在"
                "另一個終端機啟動。"
            ),
        )
        return

    status_column, database_column = (
        st.columns(2)
    )

    with status_column:
        st.metric(
            label="後端 API",
            value="正常",
        )

    with database_column:
        st.metric(
            label="資料庫",
            value="SQLite",
        )

    st.success(
        "FastAPI 連線成功："
        f"{health['status']}"
    )
