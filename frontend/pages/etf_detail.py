"""ETF 詳細資料頁面。"""

from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    APIResourceNotFoundError,
    SUPPORTED_PERFORMANCE_PERIODS,
    fetch_etf_by_code,
    fetch_etf_performance,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.pages.etf_search import (
    render_etf_search,
)


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_etf_detail(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 詳細資料。"""

    return fetch_etf_by_code(
        api_base_url=api_base_url,
        code=code,
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_etf_performance(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 多期間績效。"""

    return fetch_etf_performance(
        api_base_url=api_base_url,
        code=code,
        metric="PRICE_RETURN",
    )


def get_requested_code() -> str:
    """從網址取得 ETF 代號。"""

    raw_code = st.query_params.get(
        "code",
        "",
    )

    if isinstance(raw_code, list):
        raw_code = (
            raw_code[-1]
            if raw_code
            else ""
        )

    return str(
        raw_code
    ).strip().upper()


def format_fund_size(
    value: Any,
) -> str:
    """格式化基金規模。"""

    if value is None:
        return "尚無資料"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"

    return f"{number:,.2f} 億元"


def format_expense_ratio(
    value: Any,
) -> str:
    """格式化費用率。"""

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


def format_performance_return(
    value: Any,
) -> str:
    """格式化績效報酬率。"""

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"

    return f"{number:+.2f}%"


def build_performance_lookup(
    items: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """依績效期間建立快速查詢表。"""

    lookup: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in items:
        period_code = str(
            item["period_code"]
        ).strip().upper()

        if (
            period_code
            not in SUPPORTED_PERFORMANCE_PERIODS
        ):
            continue

        lookup[period_code] = item

    return lookup


def render_back_button() -> None:
    """顯示返回 ETF 查詢按鈕。"""

    search_page = st.Page(
        render_etf_search,
        title="ETF 查詢",
        icon="🔍",
        url_path="etf-search",
    )

    if st.button(
        "← 返回 ETF 查詢",
        type="secondary",
    ):
        st.switch_page(
            search_page
        )


def render_code_form(
    default_code: str = "",
) -> None:
    """顯示 ETF 代號查詢表單。"""

    with st.form(
        "etf_detail_code_form"
    ):
        code = st.text_input(
            "ETF 代號",
            value=default_code,
            placeholder="例如 0050 或 00980A",
        )

        submitted = (
            st.form_submit_button(
                "查詢 ETF",
                type="primary",
            )
        )

    if not submitted:
        return

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        st.warning(
            "請輸入 ETF 代號。"
        )
        return

    st.query_params["code"] = (
        normalized_code
    )

    load_etf_detail.clear()
    load_etf_performance.clear()

    st.rerun()


def render_etf_information(
    etf: dict[str, Any],
) -> None:
    """顯示 ETF 詳細資料。"""

    code = str(etf["code"])
    name = str(etf["name"])

    st.header(
        f"{code}　{name}"
    )

    st.caption(
        "資料來源：TW ETF AI Analyzer FastAPI"
    )

    management_type = (
        "主動式"
        if etf["is_active"]
        else "被動式"
    )

    asset_type = (
        "債券"
        if etf["is_bond"]
        else "非債券"
    )

    listing_date = (
        etf["listing_date"]
        or "尚無資料"
    )

    management_column, asset_column, date_column = (
        st.columns(3)
    )

    with management_column:
        st.metric(
            "管理方式",
            management_type,
        )

    with asset_column:
        st.metric(
            "資產類型",
            asset_type,
        )

    with date_column:
        st.metric(
            "上市日期",
            listing_date,
        )

    st.divider()

    st.subheader("基本資料")

    basic_information = [
        {
            "項目": "ETF 代號",
            "內容": code,
        },
        {
            "項目": "ETF 名稱",
            "內容": name,
        },
        {
            "項目": "管理方式",
            "內容": management_type,
        },
        {
            "項目": "資產類型",
            "內容": asset_type,
        },
        {
            "項目": "上市日期",
            "內容": listing_date,
        },
        {
            "項目": "基金規模",
            "內容": format_fund_size(
                etf["fund_size"]
            ),
        },
        {
            "項目": "費用率",
            "內容": format_expense_ratio(
                etf["expense_ratio"]
            ),
        },
    ]

    st.table(
        basic_information
    )

    if (
        etf["fund_size"] is None
        or etf["expense_ratio"] is None
    ):
        st.info(
            "基金規模或費用率顯示「尚無資料」，"
            "代表目前 ETF 主資料來源尚未提供或"
            "尚未匯入該項指標。"
        )


def render_etf_performance(
    performance: dict[str, Any],
) -> None:
    """顯示 ETF 的 1M、3M、6M、1Y 績效。"""

    st.divider()

    st.subheader("市價績效")

    st.caption(
        "目前為市價報酬率，"
        "不包含配息再投資。"
    )

    items = performance.get(
        "items",
        [],
    )

    lookup = build_performance_lookup(
        items
    )

    columns = st.columns(
        len(SUPPORTED_PERFORMANCE_PERIODS)
    )

    for column, period_code in zip(
        columns,
        SUPPORTED_PERFORMANCE_PERIODS,
        strict=True,
    ):
        item = lookup.get(
            period_code
        )

        with column:
            if item is None:
                st.metric(
                    period_code,
                    "歷史資料不足",
                )

                st.caption(
                    "尚無足夠價格歷史"
                )

                continue

            st.metric(
                period_code,
                format_performance_return(
                    item["return_pct"]
                ),
            )

            st.caption(
                f"截至 {item['as_of_date']}"
            )

    if not items:
        st.info(
            "目前尚無可顯示的績效資料。"
        )


def render_etf_detail() -> None:
    """顯示 ETF 詳細資料頁。"""

    st.title("ETF 詳細資料")

    render_back_button()

    requested_code = (
        get_requested_code()
    )

    if not requested_code:
        st.warning(
            "目前網址沒有指定 ETF 代號。"
        )

        render_code_form()
        return

    st.caption(
        f"查詢代號：`{requested_code}`"
    )

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        st.error(str(error))
        return

    try:
        with st.spinner(
            f"正在讀取 {requested_code}..."
        ):
            etf = load_etf_detail(
                api_base_url=api_base_url,
                code=requested_code,
            )

    except APIResourceNotFoundError as error:
        st.warning(
            f"找不到 ETF：{requested_code}"
        )

        st.code(
            str(error),
            language=None,
        )

        render_code_form(
            default_code=requested_code
        )

        return

    except APIClientError as error:
        st.error(
            "無法取得 ETF 詳細資料。"
        )

        st.code(
            str(error),
            language=None,
        )

        st.info(
            "請確認 FastAPI 已在 "
            "127.0.0.1:8000 啟動。"
        )

        return

    performance: dict[str, Any] | None = None
    performance_error: APIClientError | None = None

    try:
        performance = load_etf_performance(
            api_base_url=api_base_url,
            code=requested_code,
        )

    except APIClientError as error:
        performance_error = error

    refresh_column, _ = st.columns(
        [
            1,
            4,
        ]
    )

    with refresh_column:
        if st.button(
            "重新載入資料",
            key="refresh_etf_detail",
        ):
            load_etf_detail.clear()
            load_etf_performance.clear()
            st.rerun()

    render_etf_information(
        etf
    )

    if performance_error is not None:
        st.divider()
        st.subheader("市價績效")

        st.warning(
            "無法取得 ETF 績效資料。"
        )

        st.code(
            str(performance_error),
            language=None,
        )

        return

    if performance is not None:
        render_etf_performance(
            performance
        )
