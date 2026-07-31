"""TW ETF AI Analyzer 首頁與系統資料總覽。"""

from datetime import datetime
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_system_overview,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    DIVIDEND_DATA_QUALITY_ROUTE,
    ETF_COMPARISON_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    create_streamlit_page,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
    render_empty_state,
)


IMPORT_STATUS_LABELS = {
    "running": "執行中",
    "success": "成功",
    "failed": "失敗",
}


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_system_overview(
    api_base_url: str,
) -> dict[str, Any]:
    """取得並短暫快取首頁系統總覽。"""

    return fetch_system_overview(
        api_base_url
    )


def format_overview_percentage(
    value: Any,
) -> str:
    """格式化覆蓋率並保留缺資料語意。"""

    if value is None:
        return "尚無資料"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"

    return f"{number:.2f}%"


def format_overview_date(
    value: Any,
) -> str:
    """格式化首頁日期欄位。"""

    if value is None:
        return "尚未取得"

    text = str(value).strip()

    return (
        text
        if text
        else "尚未取得"
    )


def format_overview_datetime(
    value: Any,
) -> str:
    """格式化首頁 ISO 日期時間。"""

    if value is None:
        return "尚未取得"

    text = str(value).strip()

    if not text:
        return "尚未取得"

    try:
        parsed = datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError:
        return text

    return parsed.isoformat(
        sep=" ",
        timespec="minutes",
    )


def format_import_error(
    value: Any,
) -> str:
    """格式化匯入批次錯誤摘要。"""

    if value is None:
        return "—"

    text = str(value).strip()

    if not text:
        return "—"

    maximum_length = 100

    if len(text) <= maximum_length:
        return text

    return (
        text[:maximum_length]
        + "…"
    )


def render_feature_entry_points() -> None:
    """顯示首頁四個主要公開功能入口。"""

    st.subheader("開始使用")

    (
        search_column,
        ranking_column,
        comparison_column,
        quality_column,
    ) = st.columns(4)

    with search_column:
        st.page_link(
            create_streamlit_page(
                ETF_SEARCH_ROUTE
            ),
            label="ETF 查詢",
            icon="🔍",
            width="stretch",
        )

        st.caption(
            "依代號、名稱、管理方式與"
            "資產類型篩選 ETF。"
        )

    with ranking_column:
        st.page_link(
            create_streamlit_page(
                PERFORMANCE_RANKING_ROUTE
            ),
            label="績效排行榜",
            icon="📈",
            width="stretch",
        )

        st.caption(
            "比較 1M、3M、6M、1Y "
            "市價報酬率。"
        )

    with comparison_column:
        st.page_link(
            create_streamlit_page(
                ETF_COMPARISON_ROUTE
            ),
            label="ETF 比較",
            icon="⚖️",
            width="stretch",
        )

        st.caption(
            "並列比較 2 至 4 檔 ETF 的"
            "績效、配息、76W 與資料完整度。"
        )

    with quality_column:
        st.page_link(
            create_streamlit_page(
                DIVIDEND_DATA_QUALITY_ROUTE
            ),
            label="配息資料品質",
            icon="🧪",
            width="stretch",
        )

        st.caption(
            "檢視 ACTUAL、76W 與"
            "正式來源文件覆蓋。"
        )


def render_system_status(
    overview: dict[str, Any],
    api_base_url: str,
) -> None:
    """顯示後端與資料庫狀態。"""

    st.subheader("系統狀態")

    api_column, database_column, endpoint_column = (
        st.columns(3)
    )

    with api_column:
        st.metric(
            "後端 API",
            "正常",
        )

    with database_column:
        st.metric(
            "資料庫",
            str(
                overview[
                    "database_type"
                ]
            ),
        )

    with endpoint_column:
        st.metric(
            "API 狀態",
            str(
                overview[
                    "api_status"
                ]
            ),
        )

    st.caption(
        f"FastAPI：`{api_base_url}`"
    )

    st.success(
        "FastAPI 連線成功："
        f"{overview['api_status']}"
    )


def render_core_metrics(
    overview: dict[str, Any],
) -> None:
    """顯示 ETF、績效與配息核心摘要。"""

    st.divider()
    st.subheader("資料總覽")

    etfs = overview["etfs"]
    performance = overview[
        "performance"
    ]
    dividends = overview[
        "dividends"
    ]

    (
        etf_column,
        non_bond_column,
        performance_column,
        dividend_column,
    ) = st.columns(4)

    with etf_column:
        st.metric(
            "ETF 總數",
            f"{etfs['total_count']:,} 檔",
        )

    with non_bond_column:
        st.metric(
            "非債券 ETF",
            (
                f"{etfs['non_bond_count']:,} "
                "檔"
            ),
        )

    with performance_column:
        st.metric(
            "有市價績效",
            (
                f"{performance['etf_count']:,} "
                "檔"
            ),
        )

        st.caption(
            "占全部 ETF "
            + format_overview_percentage(
                performance[
                    "coverage_pct"
                ]
            )
        )

    with dividend_column:
        st.metric(
            "有配息歷史",
            (
                f"{dividends['etf_count']:,} "
                "檔"
            ),
        )

        st.caption(
            (
                f"{dividends['event_count']:,} "
                "筆配息事件"
            )
        )

    (
        active_column,
        bond_column,
        actual_column,
        actual_76w_column,
    ) = st.columns(4)

    with active_column:
        st.metric(
            "主動式 ETF",
            (
                f"{etfs['active_count']:,} "
                "檔"
            ),
        )

    with bond_column:
        st.metric(
            "債券 ETF",
            (
                f"{etfs['bond_count']:,} "
                "檔"
            ),
        )

    with actual_column:
        st.metric(
            "ACTUAL 覆蓋率",
            format_overview_percentage(
                dividends[
                    (
                        "actual_component_"
                        "coverage_pct"
                    )
                ]
            ),
        )

        st.caption(
            (
                f"{dividends['actual_component_event_count']:,}"
                f" / {dividends['event_count']:,} "
                "筆事件"
            )
        )

    with actual_76w_column:
        st.metric(
            "正式 76W 覆蓋率",
            format_overview_percentage(
                dividends[
                    "actual_76w_coverage_pct"
                ]
            ),
        )

        st.caption(
            (
                f"{dividends['actual_76w_event_count']:,}"
                f" / {dividends['event_count']:,} "
                "筆事件"
            )
        )


def render_performance_coverage(
    overview: dict[str, Any],
) -> None:
    """顯示各市價績效期間的 ETF 覆蓋。"""

    st.divider()
    st.subheader("市價績效覆蓋")

    performance = overview[
        "performance"
    ]

    st.caption(
        "目前統計 PRICE_RETURN／"
        "twse_stock_day；"
        "各期間獨立計算。"
    )

    columns = st.columns(
        len(
            performance["periods"]
        )
    )

    for column, item in zip(
        columns,
        performance["periods"],
        strict=True,
    ):
        with column:
            st.metric(
                str(
                    item[
                        "period_code"
                    ]
                ),
                (
                    f"{item['etf_count']:,}"
                    f" / "
                    f"{performance['total_etf_count']:,}"
                    " 檔"
                ),
            )

            st.caption(
                "覆蓋率 "
                + format_overview_percentage(
                    item[
                        "coverage_pct"
                    ]
                )
            )

            st.caption(
                "最新基準日："
                + format_overview_date(
                    item[
                        "latest_as_of_date"
                    ]
                )
            )


def build_freshness_rows(
    overview: dict[str, Any],
) -> list[dict[str, str]]:
    """建立首頁資料新鮮度表格。"""

    etfs = overview["etfs"]
    performance = overview[
        "performance"
    ]
    dividends = overview[
        "dividends"
    ]

    return [
        {
            "資料集": "ETF 主資料",
            "最新資料時間": (
                format_overview_datetime(
                    etfs[
                        (
                            "latest_master_"
                            "import_at"
                        )
                    ]
                )
            ),
            "判定方式": (
                "最近成功的 "
                "etf_master_pipeline"
            ),
        },
        {
            "資料集": "市價績效",
            "最新資料時間": (
                format_overview_date(
                    performance[
                        "latest_as_of_date"
                    ]
                )
            ),
            "判定方式": (
                "PRICE_RETURN 最新基準日"
            ),
        },
        {
            "資料集": "配息事件",
            "最新資料時間": (
                format_overview_date(
                    dividends[
                        "latest_event_date"
                    ]
                )
            ),
            "判定方式": (
                "公告、除息、基準或發放日"
            ),
        },
        {
            "資料集": "正式來源文件",
            "最新資料時間": (
                format_overview_date(
                    dividends[
                        (
                            "latest_actual_"
                            "source_document_date"
                        )
                    ]
                )
            ),
            "判定方式": (
                "已解析 ACTUAL 文件日期"
            ),
        },
    ]


def render_data_freshness(
    overview: dict[str, Any],
) -> None:
    """顯示資料集最新日期與判定方式。"""

    st.divider()
    st.subheader("資料新鮮度")

    st.table(
        build_freshness_rows(
            overview
        )
    )


def build_import_batch_rows(
    batches: list[
        dict[str, Any]
    ],
) -> list[dict[str, str]]:
    """建立型別一致的匯入批次表格。"""

    rows: list[
        dict[str, str]
    ] = []

    for batch in batches:
        status_value = str(
            batch["status"]
        ).strip().lower()

        rows.append(
            {
                "批次": (
                    f"#{batch['batch_id']}"
                ),
                "Pipeline": str(
                    batch[
                        "pipeline_name"
                    ]
                ),
                "來源": str(
                    batch["source_id"]
                ),
                "狀態": (
                    IMPORT_STATUS_LABELS.get(
                        status_value,
                        status_value,
                    )
                ),
                "開始": (
                    format_overview_datetime(
                        batch[
                            "started_at"
                        ]
                    )
                ),
                "完成": (
                    format_overview_datetime(
                        batch[
                            "completed_at"
                        ]
                    )
                ),
                "原始": str(
                    batch[
                        "raw_record_count"
                    ]
                ),
                "接受": str(
                    batch[
                        "accepted_record_count"
                    ]
                ),
                "拒絕": str(
                    batch[
                        "rejected_record_count"
                    ]
                ),
                "新增": str(
                    batch[
                        "inserted_record_count"
                    ]
                ),
                "更新": str(
                    batch[
                        "updated_record_count"
                    ]
                ),
                "錯誤": (
                    format_import_error(
                        batch[
                            "error_message"
                        ]
                    )
                ),
            }
        )

    return rows


def render_recent_import_batches(
    overview: dict[str, Any],
) -> None:
    """顯示最近五筆匯入批次摘要。"""

    st.divider()
    st.subheader("最近匯入批次")

    batches = overview[
        "recent_import_batches"
    ]

    if not batches:
        render_empty_state(
            "尚無匯入批次紀錄。",
            hint=(
                "執行資料 Pipeline 後，"
                "首頁會顯示最近結果。"
            ),
        )
        return

    st.table(
        build_import_batch_rows(
            batches
        )
    )

    if any(
        batch["status"] == "failed"
        for batch in batches
    ):
        st.warning(
            "最近批次包含失敗紀錄；"
            "請查看錯誤欄位與 Pipeline "
            "輸出後再重新執行。"
        )


def render_home() -> None:
    """顯示首頁與 FastAPI 系統資料總覽。"""

    st.title("TW ETF AI Analyzer")

    st.caption(
        "台灣 ETF 資料查詢、"
        "績效與配息品質分析網站"
    )

    render_feature_entry_points()

    st.divider()

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    refresh_clicked = st.button(
        "重新載入系統總覽",
        type="secondary",
    )

    if refresh_clicked:
        load_system_overview.clear()

    try:
        with loading_state(
            "正在讀取系統資料總覽..."
        ):
            overview = (
                load_system_overview(
                    api_base_url
                )
            )

    except APIClientError as error:
        render_api_error(
            "目前無法取得系統資料總覽。",
            error,
            hint=(
                "請確認 FastAPI 已在"
                "另一個終端機啟動，"
                "且資料庫已完成初始化。"
            ),
        )
        return

    render_system_status(
        overview,
        api_base_url,
    )

    render_core_metrics(
        overview
    )

    render_performance_coverage(
        overview
    )

    render_data_freshness(
        overview
    )

    render_recent_import_batches(
        overview
    )
