"""正式配息資料品質 Streamlit 頁面。"""

import math
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    APIResourceNotFoundError,
    fetch_actual_dividend_coverage,
    fetch_dividend_review_queue,
    fetch_dividend_review_queue_item,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.ui.components import (
    render_pagination_controls,
)
from frontend.ui.formatters import (
    format_amount,
    format_optional_text,
    format_percentage,
)
from frontend.ui.states import (
    render_api_error,
    render_empty_state,
    render_not_found_state,
)


STATUS_FILTER_OPTIONS: dict[
    str,
    str | None,
] = {
    "待處理": "PENDING",
    "審核中": "IN_REVIEW",
    "已解決": "RESOLVED",
    "已略過": "SKIPPED",
    "全部": None,
}

ISSUE_FILTER_OPTIONS: dict[
    str,
    str | None,
] = {
    "全部": None,
    "缺少正式組成": (
        "MISSING_ACTUAL_COMPONENTS"
    ),
    "缺少正式來源文件": (
        "MISSING_SOURCE_DOCUMENT"
    ),
}

STATUS_LABELS = {
    "PENDING": "待處理",
    "IN_REVIEW": "審核中",
    "RESOLVED": "已解決",
    "SKIPPED": "已略過",
}

ISSUE_LABELS = {
    "MISSING_ACTUAL_COMPONENTS": (
        "缺少正式 ACTUAL 組成"
    ),
    "MISSING_SOURCE_DOCUMENT": (
        "缺少正式來源文件"
    ),
}

PAGE_SIZE_OPTIONS = (
    10,
    20,
    50,
    100,
)

QUALITY_STATE_DEFAULTS: dict[
    str,
    object,
] = {
    "quality_coverage_etf_code": "",
    "quality_queue_status_label": "待處理",
    "quality_queue_issue_label": "全部",
    "quality_queue_etf_code": "",
    "quality_queue_page_size": 20,
    "quality_queue_page_number": 1,
}


def initialize_quality_state() -> None:
    """初始化資料品質頁 Session State。"""

    for key, value in (
        QUALITY_STATE_DEFAULTS.items()
    ):
        if key not in st.session_state:
            st.session_state[key] = value


def reset_quality_queue_state() -> None:
    """重設待處理佇列篩選條件。"""

    for key in (
        "quality_queue_status_label",
        "quality_queue_issue_label",
        "quality_queue_etf_code",
        "quality_queue_page_size",
        "quality_queue_page_number",
    ):
        st.session_state[key] = (
            QUALITY_STATE_DEFAULTS[key]
        )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_actual_dividend_coverage(
    api_base_url: str,
    etf_code: str | None = None,
) -> dict[str, Any]:
    """取得並短暫快取正式配息覆蓋率。"""

    return fetch_actual_dividend_coverage(
        api_base_url=api_base_url,
        etf_code=etf_code,
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_dividend_review_queue(
    api_base_url: str,
    status: str | None,
    etf_code: str | None,
    issue_type: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """取得並短暫快取正式配息待處理佇列。"""

    return fetch_dividend_review_queue(
        api_base_url=api_base_url,
        status=status,
        etf_code=etf_code,
        issue_type=issue_type,
        limit=limit,
        offset=offset,
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_dividend_review_queue_item(
    api_base_url: str,
    queue_id: int,
) -> dict[str, Any]:
    """取得並短暫快取單一佇列項目。"""

    return fetch_dividend_review_queue_item(
        api_base_url=api_base_url,
        queue_id=queue_id,
    )


def format_coverage_percentage(
    value: Any,
) -> str:
    """格式化覆蓋率並保留缺資料語意。"""

    return format_percentage(
        value,
        missing_text="尚無事件",
        invalid_text="資料格式異常",
    )


def format_quality_amount(
    value: Any,
    currency: Any,
) -> str:
    """格式化待處理事件配息金額。"""

    return format_amount(
        value,
        currency,
        missing_text="資料格式異常",
        invalid_text="資料格式異常",
    )


def format_quality_optional(
    value: Any,
) -> str:
    """格式化可能缺少的品質欄位。"""

    return format_optional_text(
        value,
        missing_text="—",
    )


def get_review_issue_label(
    issue_type: Any,
) -> str:
    """取得待處理問題的中文名稱。"""

    normalized = str(
        issue_type
    ).strip().upper()

    return ISSUE_LABELS.get(
        normalized,
        normalized or "未知問題",
    )


def get_review_status_label(
    status: Any,
) -> str:
    """取得待處理狀態的中文名稱。"""

    normalized = str(
        status
    ).strip().upper()

    return STATUS_LABELS.get(
        normalized,
        normalized or "未知狀態",
    )


def render_coverage_summary(
    summary: dict[str, Any],
    *,
    title: str,
) -> None:
    """顯示全站或單一 ETF 覆蓋率摘要。"""

    st.subheader(title)

    total_count = int(
        summary["total_dividend_count"]
    )

    if total_count == 0:
        st.info(
            "尚無配息事件可計算覆蓋率。"
        )

    total_column, estimated_column, actual_column, actual_76w_column = (
        st.columns(4)
    )

    with total_column:
        st.metric(
            "配息事件",
            f"{total_count:,} 次",
        )

    with estimated_column:
        st.metric(
            "已有預估組成",
            (
                f"{summary['estimated_component_event_count']:,} "
                "次"
            ),
        )

    with actual_column:
        st.metric(
            "已有正式組成",
            (
                f"{summary['actual_component_event_count']:,} "
                "次"
            ),
        )

    with actual_76w_column:
        st.metric(
            "已有正式 76W",
            (
                f"{summary['actual_76w_event_count']:,} "
                "次"
            ),
        )

    document_column, missing_actual_column, missing_document_column = (
        st.columns(3)
    )

    with document_column:
        st.metric(
            "已有正式來源文件",
            (
                f"{summary['source_document_event_count']:,} "
                "次"
            ),
        )

    with missing_actual_column:
        st.metric(
            "缺少正式組成",
            (
                f"{summary['missing_actual_component_event_count']:,} "
                "次"
            ),
        )

    with missing_document_column:
        st.metric(
            "缺少正式來源文件",
            (
                f"{summary['missing_source_document_event_count']:,} "
                "次"
            ),
        )

    actual_rate_column, actual_76w_rate_column, document_rate_column = (
        st.columns(3)
    )

    with actual_rate_column:
        st.metric(
            "ACTUAL 覆蓋率",
            format_coverage_percentage(
                summary[
                    "actual_component_coverage_pct"
                ]
            ),
        )

    with actual_76w_rate_column:
        st.metric(
            "76W 覆蓋率",
            format_coverage_percentage(
                summary[
                    "actual_76w_coverage_pct"
                ]
            ),
        )

    with document_rate_column:
        st.metric(
            "來源文件覆蓋率",
            format_coverage_percentage(
                summary[
                    "source_document_coverage_pct"
                ]
            ),
        )


def render_etf_coverage_form(
    api_base_url: str,
) -> None:
    """顯示單一 ETF 覆蓋率查詢。"""

    st.divider()
    st.subheader("ETF 個別覆蓋率")

    with st.form(
        "quality_etf_coverage_form"
    ):
        etf_code = st.text_input(
            "ETF 代號",
            value=str(
                st.session_state[
                    "quality_coverage_etf_code"
                ]
            ),
            placeholder="例如 00878 或 00900",
        )

        submitted = (
            st.form_submit_button(
                "查詢 ETF 覆蓋率",
                type="primary",
            )
        )

    if submitted:
        st.session_state[
            "quality_coverage_etf_code"
        ] = etf_code.strip().upper()

        load_actual_dividend_coverage.clear()
        st.rerun()

    requested_code = str(
        st.session_state[
            "quality_coverage_etf_code"
        ]
    ).strip().upper()

    if not requested_code:
        st.caption(
            "輸入 ETF 代號後，可查看該 ETF "
            "的正式組成、76W 與來源文件覆蓋率。"
        )
        return

    try:
        summary = (
            load_actual_dividend_coverage(
                api_base_url=api_base_url,
                etf_code=requested_code,
            )
        )

    except APIResourceNotFoundError:
        render_not_found_state(
            f"找不到 ETF：{requested_code}"
        )
        return

    except APIClientError as error:
        render_api_error(
            "無法取得 ETF 個別覆蓋率。",
            error,
        )
        return

    render_coverage_summary(
        summary,
        title=(
            f"{requested_code} 覆蓋率"
        ),
    )


def render_queue_filter_form() -> None:
    """顯示待處理佇列篩選表單。"""

    status_labels = list(
        STATUS_FILTER_OPTIONS
    )
    issue_labels = list(
        ISSUE_FILTER_OPTIONS
    )

    with st.form(
        "quality_review_queue_form"
    ):
        status_column, issue_column = (
            st.columns(2)
        )

        with status_column:
            current_status_label = str(
                st.session_state[
                    "quality_queue_status_label"
                ]
            )

            status_label = st.selectbox(
                "狀態",
                options=status_labels,
                index=status_labels.index(
                    current_status_label
                ),
            )

        with issue_column:
            current_issue_label = str(
                st.session_state[
                    "quality_queue_issue_label"
                ]
            )

            issue_label = st.selectbox(
                "問題類型",
                options=issue_labels,
                index=issue_labels.index(
                    current_issue_label
                ),
            )

        etf_column, size_column = (
            st.columns(2)
        )

        with etf_column:
            etf_code = st.text_input(
                "篩選 ETF 代號",
                value=str(
                    st.session_state[
                        "quality_queue_etf_code"
                    ]
                ),
                placeholder="留空代表全部 ETF",
            )

        with size_column:
            current_page_size = int(
                st.session_state[
                    "quality_queue_page_size"
                ]
            )

            page_size = st.selectbox(
                "每頁筆數",
                options=PAGE_SIZE_OPTIONS,
                index=PAGE_SIZE_OPTIONS.index(
                    current_page_size
                ),
            )

        submitted = (
            st.form_submit_button(
                "套用佇列篩選",
                type="primary",
            )
        )

    if submitted:
        st.session_state[
            "quality_queue_status_label"
        ] = status_label

        st.session_state[
            "quality_queue_issue_label"
        ] = issue_label

        st.session_state[
            "quality_queue_etf_code"
        ] = etf_code.strip().upper()

        st.session_state[
            "quality_queue_page_size"
        ] = page_size

        st.session_state[
            "quality_queue_page_number"
        ] = 1

        load_dividend_review_queue.clear()
        load_dividend_review_queue_item.clear()
        st.rerun()


def render_queue_action_buttons() -> None:
    """顯示佇列重設與重新載入按鈕。"""

    reset_column, refresh_column, _ = (
        st.columns(
            [
                1,
                1,
                4,
            ]
        )
    )

    with reset_column:
        reset_clicked = st.button(
            "清除佇列條件",
            key="reset_quality_queue",
        )

    with refresh_column:
        refresh_clicked = st.button(
            "重新載入品質資料",
            key="refresh_quality_data",
        )

    if reset_clicked:
        reset_quality_queue_state()
        load_dividend_review_queue.clear()
        load_dividend_review_queue_item.clear()
        st.rerun()

    if refresh_clicked:
        load_actual_dividend_coverage.clear()
        load_dividend_review_queue.clear()
        load_dividend_review_queue_item.clear()
        st.rerun()


def build_review_queue_rows(
    items: list[dict[str, Any]],
) -> list[dict[str, str | int]]:
    """建立待處理佇列顯示資料。"""

    return [
        {
            "優先級": int(
                item["priority"]
            ),
            "ETF": str(
                item["etf_code"]
            ),
            "除息日": (
                format_quality_optional(
                    item["ex_dividend_date"]
                )
            ),
            "問題": (
                get_review_issue_label(
                    item["issue_type"]
                )
            ),
            "狀態": (
                get_review_status_label(
                    item["status"]
                )
            ),
            "每單位配息": (
                format_quality_amount(
                    item["amount_per_unit"],
                    item["currency"],
                )
            ),
            "建議來源": (
                format_quality_optional(
                    item["suggested_source_id"]
                )
            ),
            "最後檢查": (
                format_quality_optional(
                    item["last_evaluated_at"]
                )
            ),
        }
        for item in items
    ]


def render_queue_detail(
    detail: dict[str, Any],
) -> None:
    """顯示單一佇列項目明細。"""

    st.subheader("佇列項目明細")

    rows = [
        {
            "項目": "Queue ID",
            "內容": detail["queue_id"],
        },
        {
            "項目": "Dividend ID",
            "內容": detail["dividend_id"],
        },
        {
            "項目": "ETF 代號",
            "內容": detail["etf_code"],
        },
        {
            "項目": "來源事件 ID",
            "內容": detail["source_event_id"],
        },
        {
            "項目": "除息日",
            "內容": format_quality_optional(
                detail["ex_dividend_date"]
            ),
        },
        {
            "項目": "每單位配息",
            "內容": format_quality_amount(
                detail["amount_per_unit"],
                detail["currency"],
            ),
        },
        {
            "項目": "問題類型",
            "內容": get_review_issue_label(
                detail["issue_type"]
            ),
        },
        {
            "項目": "建議來源",
            "內容": format_quality_optional(
                detail["suggested_source_id"]
            ),
        },
        {
            "項目": "狀態",
            "內容": get_review_status_label(
                detail["status"]
            ),
        },
        {
            "項目": "備註",
            "內容": format_quality_optional(
                detail["notes"]
            ),
        },
        {
            "項目": "正式來源文件 ID",
            "內容": format_quality_optional(
                detail[
                    "resolution_document_id"
                ]
            ),
        },
        {
            "項目": "建立時間",
            "內容": detail["created_at"],
        },
        {
            "項目": "更新時間",
            "內容": detail["updated_at"],
        },
    ]

    st.table(rows)


def render_quality_pagination(
    current_page: int,
    total_pages: int,
) -> None:
    """顯示待處理佇列分頁控制。"""

    action = render_pagination_controls(
        current_page=current_page,
        total_pages=total_pages,
        previous_key=(
            "previous_quality_page"
        ),
        next_key="next_quality_page",
    )

    if action == "previous":
        st.session_state[
            "quality_queue_page_number"
        ] = current_page - 1
        st.rerun()

    if action == "next":
        st.session_state[
            "quality_queue_page_number"
        ] = current_page + 1
        st.rerun()


def render_review_queue(
    api_base_url: str,
) -> None:
    """顯示正式配息待處理佇列。"""

    st.divider()
    st.subheader("待處理來源佇列")

    st.caption(
        "此頁目前僅供查詢；"
        "狀態更新仍由後端管理流程處理。"
    )

    render_queue_filter_form()
    render_queue_action_buttons()

    status_label = str(
        st.session_state[
            "quality_queue_status_label"
        ]
    )
    issue_label = str(
        st.session_state[
            "quality_queue_issue_label"
        ]
    )
    etf_code = str(
        st.session_state[
            "quality_queue_etf_code"
        ]
    ).strip().upper()
    page_size = int(
        st.session_state[
            "quality_queue_page_size"
        ]
    )
    current_page = int(
        st.session_state[
            "quality_queue_page_number"
        ]
    )

    status_value = (
        STATUS_FILTER_OPTIONS[
            status_label
        ]
    )
    issue_value = (
        ISSUE_FILTER_OPTIONS[
            issue_label
        ]
    )

    offset = (
        current_page - 1
    ) * page_size

    try:
        result = load_dividend_review_queue(
            api_base_url=api_base_url,
            status=status_value,
            etf_code=(
                etf_code
                if etf_code
                else None
            ),
            issue_type=issue_value,
            limit=page_size,
            offset=offset,
        )

    except APIResourceNotFoundError:
        render_not_found_state(
            f"找不到 ETF：{etf_code}"
        )
        return

    except APIClientError as error:
        render_api_error(
            "無法取得正式配息待處理佇列。",
            error,
        )
        return

    total = int(
        result["total"]
    )
    items = result["items"]

    total_pages = max(
        1,
        math.ceil(
            total / page_size
        ),
    )

    if current_page > total_pages:
        st.session_state[
            "quality_queue_page_number"
        ] = total_pages
        st.rerun()

    total_column, page_column, count_column = (
        st.columns(3)
    )

    with total_column:
        st.metric(
            "符合條件",
            f"{total:,} 項",
        )

    with page_column:
        st.metric(
            "目前頁次",
            (
                f"{current_page}"
                f" / {total_pages}"
            ),
        )

    with count_column:
        st.metric(
            "本頁項目",
            f"{len(items):,} 項",
        )

    if not items:
        render_empty_state(
            "目前沒有符合條件的待處理項目。",
            hint=(
                "可清除條件或改用其他狀態、"
                "問題類型與 ETF 代號。"
            ),
        )
        return

    st.table(
        build_review_queue_rows(
            items
        )
    )

    st.caption(
        f"目前顯示第 "
        f"{offset + 1:,} 至 "
        f"{offset + len(items):,} 項，"
        f"共 {total:,} 項"
    )

    queue_ids = [
        int(item["queue_id"])
        for item in items
    ]

    selected_queue_id = st.selectbox(
        "查看佇列項目",
        options=queue_ids,
        format_func=lambda value: (
            f"Queue #{value}"
        ),
    )

    try:
        detail = (
            load_dividend_review_queue_item(
                api_base_url=api_base_url,
                queue_id=int(
                    selected_queue_id
                ),
            )
        )

    except APIClientError as error:
        render_api_error(
            "無法取得佇列項目明細。",
            error,
        )

    else:
        render_queue_detail(
            detail
        )

    render_quality_pagination(
        current_page=current_page,
        total_pages=total_pages,
    )


def render_dividend_data_quality() -> None:
    """顯示正式配息資料品質總覽。"""

    initialize_quality_state()

    st.title("配息資料品質")

    st.caption(
        "檢視正式 ACTUAL、76W 與"
        "來源文件覆蓋率"
    )

    st.info(
        "缺少正式資料不代表 76W 為 0%。"
        "只有 ACTUAL + 76W 的正式紀錄"
        "才計入 76W 覆蓋率。"
    )

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    try:
        overall_summary = (
            load_actual_dividend_coverage(
                api_base_url=api_base_url,
                etf_code=None,
            )
        )

    except APIClientError as error:
        render_api_error(
            "無法取得全站正式配息覆蓋率。",
            error,
        )

    else:
        render_coverage_summary(
            overall_summary,
            title="全站覆蓋率摘要",
        )

    render_etf_coverage_form(
        api_base_url
    )

    render_review_queue(
        api_base_url
    )
