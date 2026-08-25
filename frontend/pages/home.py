"""ETF奈米戶初學者首頁。"""

from typing import Any

import streamlit as st

from frontend.api_client import APIClientError, fetch_system_overview
from frontend.config import get_api_base_url
from frontend.navigation import (
    DIVIDEND_DATA_QUALITY_ROUTE,
    ETF_COMPARISON_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    PUBLIC_PLANNER_ROUTE,
    create_streamlit_page,
)
from frontend.ui.formatters import format_iso_date, format_percentage
from frontend.ui.states import loading_state, render_api_error


@st.cache_data(ttl=30, show_spinner=False)
def load_system_overview(api_base_url: str) -> dict[str, Any]:
    """取得並短暫快取首頁公開資料摘要。"""

    return fetch_system_overview(api_base_url)


def format_overview_percentage(value: Any) -> str:
    """格式化覆蓋率並保留缺資料語意。"""

    return format_percentage(
        value,
        missing_text="尚無資料",
        invalid_text="資料格式異常",
    )


def build_home_data_dates(overview: dict[str, Any]) -> list[str]:
    """建立首頁需要的簡短資料日期，不顯示內部 Pipeline 欄位。"""

    performance_date = format_iso_date(
        overview["performance"].get("latest_as_of_date"),
        missing_text="尚未取得",
    )
    dividend_date = format_iso_date(
        overview["dividends"].get("latest_event_date"),
        missing_text="尚未取得",
    )
    return [
        f"績效資料至 {performance_date}",
        f"配息事件至 {dividend_date}",
    ]


def render_primary_action() -> None:
    """將核心配置流程放在首頁第一個可操作位置。"""

    with st.container(border=True):
        st.subheader("先算出適合你的 ETF 配置")
        st.write(
            "告訴我們每個目標月想領多少、想在哪些月份領息，以及目前持有的 "
            "0～N 檔 ETF；系統會試算應增加哪些 ETF、各買多少股與所需資金。"
        )
        st.page_link(
            create_streamlit_page(PUBLIC_PLANNER_ROUTE),
            label="開始配置",
            icon=":material/calculate:",
            width="stretch",
        )
        st.caption("不需登入，輸入與試算結果不會儲存，也不會送出交易。")


def render_exploration_links() -> None:
    """呈現核心配置以外的次要資料探索入口。"""

    st.subheader("也可以先了解 ETF")
    routes = (
        (ETF_SEARCH_ROUTE, "查 ETF 基本資料", ":material/search:"),
        (PERFORMANCE_RANKING_ROUTE, "看歷史績效", ":material/query_stats:"),
        (ETF_COMPARISON_ROUTE, "並排比較 ETF", ":material/compare_arrows:"),
        (DIVIDEND_DATA_QUALITY_ROUTE, "了解資料完整度", ":material/database:"),
    )
    columns = st.columns(4)
    for column, (route, label, icon) in zip(columns, routes, strict=True):
        with column:
            st.page_link(
                create_streamlit_page(route),
                label=label,
                icon=icon,
                width="stretch",
            )


def render_public_data_snapshot(overview: dict[str, Any]) -> None:
    """只顯示初學者能理解的公開資料可用量。"""

    st.subheader("目前可用資料")
    etfs = overview["etfs"]
    performance = overview["performance"]
    dividends = overview["dividends"]
    with st.container(horizontal=True):
        st.metric("可查詢 ETF", f"{etfs['total_count']:,} 檔", border=True)
        st.metric("有績效資料", f"{performance['etf_count']:,} 檔", border=True)
        st.metric("有配息歷史", f"{dividends['etf_count']:,} 檔", border=True)
        st.metric(
            "正式配息組成覆蓋",
            format_overview_percentage(dividends.get("actual_component_coverage_pct")),
            border=True,
        )
    st.caption("；".join(build_home_data_dates(overview)) + "。缺少資料時不會以 0 代替。")


def render_home() -> None:
    """顯示以初學者核心任務為主的首頁。"""

    st.title("ETF奈米戶")
    st.caption("從現金流目標與現有持股出發，透明規劃台灣 ETF 配置。")
    render_primary_action()
    render_exploration_links()

    try:
        api_base_url = get_api_base_url()
    except ValueError as error:
        render_api_error("目前無法讀取公開資料摘要。", error)
        return

    try:
        with loading_state("正在讀取資料摘要..."):
            overview = load_system_overview(api_base_url)
    except APIClientError as error:
        render_api_error(
            "目前無法取得資料摘要。",
            error,
            hint="核心試算暫時也可能無法使用，請稍後再試。",
        )
        return

    render_public_data_snapshot(overview)
    st.caption(
        "本站不下單、不提供即時交易訊號，也不保證未來配息、報酬或本金。"
    )
