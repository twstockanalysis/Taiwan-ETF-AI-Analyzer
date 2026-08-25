"""網站管理者使用的資料與匯入狀態總覽。"""

from typing import Any

import streamlit as st

from frontend.api_client import APIClientError, fetch_system_overview
from frontend.config import get_api_base_url
from frontend.ui.formatters import (
    format_iso_date,
    format_iso_datetime,
    format_percentage,
    truncate_text,
)
from frontend.ui.states import loading_state, render_api_error, render_empty_state


IMPORT_STATUS_LABELS = {
    "running": "執行中",
    "success": "成功",
    "failed": "失敗",
}


@st.cache_data(ttl=30, show_spinner=False)
def load_admin_overview(api_base_url: str) -> dict[str, Any]:
    """取得並短暫快取管理者系統總覽。"""

    return fetch_system_overview(api_base_url)


def format_admin_percentage(value: Any) -> str:
    """格式化管理頁覆蓋率並保留缺資料語意。"""

    return format_percentage(
        value,
        missing_text="尚無資料",
        invalid_text="資料格式異常",
    )


def build_freshness_rows(overview: dict[str, Any]) -> list[dict[str, str]]:
    """建立各資料集最新日期表格。"""

    return [
        {
            "資料集": "ETF 主資料",
            "最新資料時間": format_iso_datetime(
                overview["etfs"].get("latest_master_import_at"),
                missing_text="尚未取得",
                timespec="minutes",
            ),
        },
        {
            "資料集": "市價績效",
            "最新資料時間": format_iso_date(
                overview["performance"].get("latest_as_of_date"),
                missing_text="尚未取得",
            ),
        },
        {
            "資料集": "配息事件",
            "最新資料時間": format_iso_date(
                overview["dividends"].get("latest_event_date"),
                missing_text="尚未取得",
            ),
        },
        {
            "資料集": "正式來源文件",
            "最新資料時間": format_iso_date(
                overview["dividends"].get("latest_actual_source_document_date"),
                missing_text="尚未取得",
            ),
        },
    ]


def build_import_batch_rows(batches: list[dict[str, Any]]) -> list[dict[str, str]]:
    """建立最近匯入批次表格。"""

    rows: list[dict[str, str]] = []
    for batch in batches:
        status = str(batch.get("status", "")).strip().lower()
        rows.append(
            {
                "批次": f"#{batch['batch_id']}",
                "Pipeline": str(batch["pipeline_name"]),
                "來源": str(batch["source_id"]),
                "狀態": IMPORT_STATUS_LABELS.get(status, status),
                "開始": format_iso_datetime(
                    batch.get("started_at"),
                    missing_text="尚未取得",
                    timespec="minutes",
                ),
                "完成": format_iso_datetime(
                    batch.get("completed_at"),
                    missing_text="尚未取得",
                    timespec="minutes",
                ),
                "接受／拒絕": (
                    f"{batch['accepted_record_count']}／{batch['rejected_record_count']}"
                ),
                "錯誤": truncate_text(
                    batch.get("error_message"),
                    maximum_length=100,
                    missing_text="—",
                ),
            }
        )
    return rows


def render_admin_metrics(overview: dict[str, Any]) -> None:
    """顯示原首頁資料量與覆蓋狀態。"""

    etfs = overview["etfs"]
    performance = overview["performance"]
    dividends = overview["dividends"]

    st.subheader("目前可用資料")
    with st.container(horizontal=True):
        st.metric("可查詢 ETF", f"{etfs['total_count']:,} 檔", border=True)
        st.metric("有績效資料", f"{performance['etf_count']:,} 檔", border=True)
        st.metric("有配息歷史", f"{dividends['etf_count']:,} 檔", border=True)
        st.metric(
            "正式配息組成覆蓋",
            format_admin_percentage(dividends.get("actual_component_coverage_pct")),
            border=True,
        )

    st.subheader("資料分類與覆蓋")
    with st.container(horizontal=True):
        st.metric("主動式 ETF", f"{etfs['active_count']:,} 檔", border=True)
        st.metric("債券 ETF", f"{etfs['bond_count']:,} 檔", border=True)
        st.metric(
            "正式 76W 覆蓋",
            format_admin_percentage(dividends.get("actual_76w_coverage_pct")),
            border=True,
        )
        st.metric(
            "來源文件覆蓋",
            format_admin_percentage(dividends.get("source_document_coverage_pct")),
            border=True,
        )


def render_admin_overview() -> None:
    """顯示僅管理者導覽可進入的網站資料總覽。"""

    st.title("網站管理")
    st.caption("資料覆蓋、更新日期與最近匯入批次，僅供網站管理者檢查。")

    try:
        api_base_url = get_api_base_url()
    except ValueError as error:
        render_api_error("前端 API 網址設定不正確。", error)
        return

    if st.button("重新載入管理資料", type="secondary"):
        load_admin_overview.clear()

    try:
        with loading_state("正在讀取網站管理資料..."):
            overview = load_admin_overview(api_base_url)
    except APIClientError as error:
        render_api_error(
            "目前無法取得網站管理資料。",
            error,
            hint="請確認後端服務與資料庫狀態。",
        )
        return

    st.caption(
        f"API 狀態：{overview['api_status']}｜資料庫：{overview['database_type']}"
    )
    render_admin_metrics(overview)

    st.subheader("資料更新日期")
    st.table(build_freshness_rows(overview))

    st.subheader("最近匯入批次")
    batches = overview["recent_import_batches"]
    if not batches:
        render_empty_state("尚無匯入批次紀錄。")
        return

    st.table(build_import_batch_rows(batches))
    if any(batch.get("status") == "failed" for batch in batches):
        st.warning("最近批次包含失敗紀錄，請檢查錯誤欄位與 Pipeline 輸出。")
