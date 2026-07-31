"""ETF 詳細資料頁面。"""

from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    APIResourceNotFoundError,
    SUPPORTED_PERFORMANCE_PERIODS,
    fetch_dividend_detail,
    fetch_etf_actual_76w,
    fetch_etf_by_code,
    fetch_etf_data_profile,
    fetch_etf_dividends,
    fetch_etf_performance,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    ETF_COMPARISON_ROUTE,
    ETF_DETAIL_ROUTE,
    build_comparison_query_params,
    build_detail_query_params,
    create_streamlit_page,
    resolve_detail_return,
)
from frontend.query_state import (
    get_query_value,
    query_params_to_dict,
    sync_query_params,
)
from frontend.ui.formatters import (
    asset_type_label,
    format_amount as format_shared_amount,
    format_iso_date,
    format_iso_datetime,
    format_number,
    format_percentage as format_shared_percentage,
    format_source_references as format_shared_source_references,
    management_type_label,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
    render_not_found_state,
    render_warning_state,
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
def load_etf_data_profile(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 資料來源概況。"""

    return fetch_etf_data_profile(
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


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_etf_dividends(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 配息歷史。"""

    return fetch_etf_dividends(
        api_base_url=api_base_url,
        code=code,
        limit=20,
        offset=0,
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_etf_actual_76w(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 實際 76W 摘要。"""

    return fetch_etf_actual_76w(
        api_base_url=api_base_url,
        code=code,
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_dividend_detail(
    api_base_url: str,
    dividend_id: int,
) -> dict[str, Any]:
    """取得並短暫快取單次配息及其組成。"""

    return fetch_dividend_detail(
        api_base_url=api_base_url,
        dividend_id=dividend_id,
    )


def get_requested_code() -> str:
    """從網址取得 ETF 代號。"""

    return get_query_value(
        st.query_params,
        "code",
    ).upper()


def format_fund_size(
    value: Any,
) -> str:
    """格式化基金規模。"""

    return format_number(
        value,
        suffix=" 億元",
        missing_text="尚無資料",
        invalid_text="資料格式異常",
    )


def format_expense_ratio(
    value: Any,
) -> str:
    """格式化費用率。"""

    return format_shared_percentage(
        value,
        missing_text="尚無資料",
        invalid_text="資料格式異常",
    )


def format_performance_return(
    value: Any,
) -> str:
    """格式化績效報酬率。"""

    return format_shared_percentage(
        value,
        signed=True,
        missing_text="資料格式異常",
        invalid_text="資料格式異常",
    )


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
    """依來源頁顯示返回按鈕並保留 URL 狀態。"""

    route, return_query_params = (
        resolve_detail_return(
            st.query_params
        )
    )

    return_page = create_streamlit_page(
        route
    )

    if st.button(
        f"← 返回 {route.title}",
        type="secondary",
    ):
        st.switch_page(
            return_page,
            query_params=(
                return_query_params
            ),
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

    route, return_query_params = (
        resolve_detail_return(
            st.query_params
        )
    )

    sync_query_params(
        st.query_params,
        build_detail_query_params(
            code=normalized_code,
            source=str(
                route.url_path
            ),
            source_query_params=(
                return_query_params
            ),
        ),
    )

    load_etf_detail.clear()
    load_etf_data_profile.clear()
    load_etf_performance.clear()
    load_etf_dividends.clear()
    load_etf_actual_76w.clear()
    load_dividend_detail.clear()

    st.rerun()


def render_etf_information(
    etf: dict[str, Any],
) -> None:
    """顯示 ETF 身分、分類與核心資料。"""

    code = str(etf["code"])
    name = str(etf["name"])

    management_type = (
        management_type_label(
            etf["is_active"]
        )
    )

    asset_type = asset_type_label(
        etf["is_bond"]
    )

    listing_date = (
        etf["listing_date"]
        or "尚無資料"
    )

    st.header(
        f"{code}　{name}"
    )

    st.caption(
        f"{management_type}　｜　"
        f"{asset_type}"
    )

    st.subheader("核心資料概覽")

    date_column, size_column, fee_column = (
        st.columns(3)
    )

    with date_column:
        st.metric(
            "上市日期",
            listing_date,
        )

    with size_column:
        st.metric(
            "基金規模",
            format_fund_size(
                etf["fund_size"]
            ),
        )

    with fee_column:
        st.metric(
            "費用率",
            format_expense_ratio(
                etf["expense_ratio"]
            ),
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



DIVIDEND_COMPONENT_LABELS = {
    "EST_DIVIDEND": "預估股利所得",
    "EST_INTEREST": "預估利息所得",
    "EST_EQUALIZATION": "預估收益平準金",
    "EST_REALIZED_CAPITAL_GAIN": (
        "預估已實現資本利得"
    ),
    "EST_OTHER": "預估其他所得",
    "76W": "實際所得類別 76W",
}


def format_dividend_amount(
    value: Any,
    currency: Any = "TWD",
) -> str:
    """格式化每單位配息金額。"""

    return format_shared_amount(
        value,
        currency,
        missing_text="尚無資料",
        invalid_text="資料格式異常",
    )


def format_dividend_percentage(
    value: Any,
) -> str:
    """格式化配息組成比例並保留缺資料語意。"""

    return format_shared_percentage(
        value,
        missing_text="尚未取得",
        invalid_text="資料格式異常",
    )


def format_optional_date(
    value: Any,
) -> str:
    """格式化可能缺少的日期。"""

    return format_iso_date(
        value,
        missing_text="尚無資料",
    )


def get_component_display_name(
    component: dict[str, Any],
) -> str:
    """取得不混淆預估與實際所得的顯示名稱。"""

    code = str(
        component.get(
            "component_code",
            "",
        )
    ).strip().upper()

    configured_label = (
        DIVIDEND_COMPONENT_LABELS.get(
            code
        )
    )

    if configured_label is not None:
        return configured_label

    component_name = component.get(
        "component_name"
    )

    if component_name is not None:
        normalized_name = str(
            component_name
        ).strip()

        if normalized_name:
            return normalized_name

    return code or "未命名組成"


def build_component_display_rows(
    components: list[dict[str, Any]],
    component_basis: str,
) -> list[dict[str, str]]:
    """建立指定資訊基礎的配息組成顯示資料。"""

    normalized_basis = (
        component_basis.strip().upper()
    )

    rows: list[
        dict[str, str]
    ] = []

    for component in components:
        current_basis = str(
            component.get(
                "component_basis",
                "",
            )
        ).strip().upper()

        if current_basis != normalized_basis:
            continue

        rows.append(
            {
                "組成": (
                    get_component_display_name(
                        component
                    )
                ),
                "代碼": str(
                    component.get(
                        "component_code",
                        "",
                    )
                ).strip().upper(),
                "比例": (
                    format_dividend_percentage(
                        component.get(
                            "ratio_pct"
                        )
                    )
                ),
                "每單位金額": (
                    format_dividend_amount(
                        component.get(
                            "amount_per_unit"
                        )
                    )
                    if component.get(
                        "amount_per_unit"
                    ) is not None
                    else "尚未取得"
                ),
                "來源": str(
                    component.get(
                        "source_id",
                        "",
                    )
                ),
            }
        )

    return rows


def render_component_group(
    title: str,
    components: list[dict[str, Any]],
    component_basis: str,
) -> None:
    """顯示預估或實際配息組成。"""

    st.markdown(
        f"**{title}**"
    )

    rows = build_component_display_rows(
        components=components,
        component_basis=component_basis,
    )

    if not rows:
        st.caption(
            "目前沒有此類組成資料。"
        )
        return

    st.table(rows)


def render_dividend_summary(
    history: dict[str, Any],
) -> None:
    """顯示 ETF 配息摘要。"""

    st.divider()
    st.subheader("配息摘要")

    items = history.get(
        "items",
        [],
    )

    if not items:
        st.info(
            "目前沒有配息歷史資料。"
        )
        return

    latest = items[0]

    count_column, date_column, amount_column, payment_column = (
        st.columns(4)
    )

    with count_column:
        st.metric(
            "配息事件",
            f"{history['total']:,} 次",
        )

    with date_column:
        st.metric(
            "最新除息日",
            format_optional_date(
                latest.get(
                    "ex_dividend_date"
                )
            ),
        )

    with amount_column:
        st.metric(
            "最新每單位配息",
            format_dividend_amount(
                latest.get(
                    "amount_per_unit"
                ),
                latest.get(
                    "currency"
                ),
            ),
        )

    with payment_column:
        st.metric(
            "最新發放日",
            format_optional_date(
                latest.get(
                    "payment_date"
                )
            ),
        )


def render_actual_76w_summary(
    summary: dict[str, Any],
) -> None:
    """顯示正式 ACTUAL 76W 分析。"""

    st.divider()
    st.subheader("實際 76W 分析")

    st.caption(
        "僅統計正式 ACTUAL + 76W；"
        "預估已實現資本利得不列入。"
    )

    record_count = int(
        summary[
            "actual_76w_record_count"
        ]
    )

    if record_count == 0:
        st.info(
            "尚未取得正式 76W 收益分配資料。"
        )
        return

    record_column, full_column, latest_column, average_column = (
        st.columns(4)
    )

    with record_column:
        st.metric(
            "正式 76W 配息",
            f"{record_count:,} 次",
        )

    with full_column:
        st.metric(
            "100% 76W",
            (
                f"{summary['full_76w_count']:,} "
                "次"
            ),
        )

    with latest_column:
        st.metric(
            "最新 76W 比例",
            format_dividend_percentage(
                summary[
                    "latest_76w_ratio_pct"
                ]
            ),
        )

    with average_column:
        st.metric(
            "平均 76W 比例",
            format_dividend_percentage(
                summary[
                    "average_76w_ratio_pct"
                ]
            ),
        )


def render_dividend_history(
    api_base_url: str,
    history: dict[str, Any],
) -> None:
    """顯示配息歷史及每次事件的組成。"""

    st.divider()
    st.subheader("配息歷史與組成")

    items = history.get(
        "items",
        [],
    )

    if not items:
        st.info(
            "目前沒有可顯示的配息事件。"
        )
        return

    st.caption(
        "下列為目前頁面載入的最新 "
        f"{len(items)} 筆配息事件；"
        f"資料庫共 {history['total']:,} 筆。"
    )

    for item in items:
        dividend_id = int(
            item["dividend_id"]
        )

        ex_date = format_optional_date(
            item.get(
                "ex_dividend_date"
            )
        )

        amount = format_dividend_amount(
            item.get(
                "amount_per_unit"
            ),
            item.get(
                "currency"
            ),
        )

        label = (
            f"{ex_date}　每單位 {amount}"
        )

        with st.expander(
            label,
            expanded=False,
        ):
            event_rows = [
                {
                    "項目": "除息日",
                    "內容": ex_date,
                },
                {
                    "項目": "發放日",
                    "內容": (
                        format_optional_date(
                            item.get(
                                "payment_date"
                            )
                        )
                    ),
                },
                {
                    "項目": "每單位配息",
                    "內容": amount,
                },
                {
                    "項目": "事件來源",
                    "內容": str(
                        item.get(
                            "source_id",
                            "",
                        )
                    ),
                },
            ]

            st.table(event_rows)

            try:
                detail = load_dividend_detail(
                    api_base_url=api_base_url,
                    dividend_id=dividend_id,
                )

            except APIClientError as error:
                st.warning(
                    "無法取得此配息事件的組成資料。"
                )

                st.code(
                    str(error),
                    language=None,
                )

                continue

            components = detail.get(
                "components",
                [],
            )

            render_component_group(
                title="預估配息組成",
                components=components,
                component_basis="ESTIMATED",
            )

            render_component_group(
                title="實際所得組成",
                components=components,
                component_basis="ACTUAL",
            )





def format_optional_datetime(
    value: Any,
) -> str:
    """格式化可能缺少的 ISO 日期時間。"""

    return format_iso_datetime(
        value,
        missing_text="尚未取得",
        timespec=None,
        utc_label=True,
    )


def format_freshness_date(
    value: Any,
) -> str:
    """格式化新鮮度日期並保留缺資料語意。"""

    return format_iso_date(
        value,
        missing_text="尚未取得",
    )


def format_source_references(
    sources: list[dict[str, Any]],
) -> str:
    """將資料來源清單格式化為可讀文字。"""

    return format_shared_source_references(
        sources,
        missing_text="尚未取得",
    )


def build_data_profile_rows(
    profile: dict[str, Any],
) -> list[dict[str, str]]:
    """建立資料來源與新鮮度顯示列。"""

    master = profile["master"]
    performance = profile[
        "performance"
    ]
    dividends = profile["dividends"]
    actual = profile[
        "actual_dividend"
    ]

    available_periods = (
        performance[
            "available_periods"
        ]
    )

    period_text = (
        "、".join(
            available_periods
        )
        if available_periods
        else "尚無期間"
    )

    return [
        {
            "資料區塊": "ETF 主資料",
            "官方來源": (
                format_source_references(
                    master["sources"]
                )
            ),
            "最新資料日期": "—",
            "最近匯入": (
                format_optional_datetime(
                    master[
                        "latest_import_at"
                    ]
                )
            ),
            "資料量": "1 檔 ETF",
            "說明": (
                "最近匯入時間為 ETF "
                "主資料集層級"
            ),
        },
        {
            "資料區塊": "市價績效",
            "官方來源": (
                format_source_references(
                    performance["sources"]
                )
            ),
            "最新資料日期": (
                format_freshness_date(
                    performance[
                        "latest_as_of_date"
                    ]
                )
            ),
            "最近匯入": (
                format_optional_datetime(
                    performance[
                        "latest_import_at"
                    ]
                )
            ),
            "資料量": (
                f"{performance['record_count']:,} 筆"
            ),
            "說明": (
                "可用期間："
                f"{period_text}；"
                "目前為 PRICE_RETURN"
            ),
        },
        {
            "資料區塊": "配息事件",
            "官方來源": (
                format_source_references(
                    dividends["sources"]
                )
            ),
            "最新資料日期": (
                format_freshness_date(
                    dividends[
                        "latest_event_date"
                    ]
                )
            ),
            "最近匯入": (
                format_optional_datetime(
                    dividends[
                        "latest_import_at"
                    ]
                )
            ),
            "資料量": (
                f"{dividends['event_count']:,} 次"
            ),
            "說明": (
                "事件日期依除息、"
                "基準、發放或公告日判定"
            ),
        },
        {
            "資料區塊": "正式配息組成",
            "官方來源": (
                format_source_references(
                    actual["sources"]
                )
            ),
            "最新資料日期": (
                format_freshness_date(
                    actual[
                        "latest_source_document_date"
                    ]
                )
            ),
            "最近匯入": (
                format_optional_datetime(
                    actual[
                        "latest_import_at"
                    ]
                )
            ),
            "資料量": (
                "ACTUAL "
                f"{actual['actual_component_event_count']:,} 次；"
                "76W "
                f"{actual['actual_76w_event_count']:,} 次；"
                "來源文件 "
                f"{actual['source_document_event_count']:,} 次"
            ),
            "說明": (
                "僅統計正式 ACTUAL；"
                "預估資本利得不算 76W"
            ),
        },
    ]


def render_data_profile(
    profile: dict[str, Any],
) -> None:
    """顯示 ETF 資料來源與新鮮度。"""

    st.divider()
    st.subheader("資料來源與新鮮度")

    st.caption(
        "所有資訊均由 FastAPI 提供；"
        "日期缺少時顯示尚未取得，"
        "不以今天日期代替。"
    )

    st.table(
        build_data_profile_rows(
            profile
        )
    )


def render_comparison_entry_point(
    etf: dict[str, Any],
) -> None:
    """將目前 ETF 帶入公開比較頁。"""

    st.divider()
    st.subheader("ETF 比較")

    st.caption(
        f"將 {etf['code']} 加入比較清單，"
        "再選擇其他 ETF 進行 2 至 4 檔並列比較。"
    )

    st.page_link(
        create_streamlit_page(
            ETF_COMPARISON_ROUTE
        ),
        label="加入 ETF 比較",
        icon="⚖️",
        width="stretch",
        query_params=(
            build_comparison_query_params(
                codes=(
                    str(etf["code"]),
                ),
                source=str(
                    ETF_DETAIL_ROUTE.url_path
                ),
                source_query_params=(
                    query_params_to_dict(
                        st.query_params
                    )
                ),
            )
        ),
    )


def render_detail_section_error(
    title: str,
    message: str,
    error: APIClientError,
) -> None:
    """顯示不影響其他區塊的載入錯誤。"""

    st.divider()
    st.subheader(title)

    render_warning_state(
        message,
        detail=error,
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
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    try:
        with loading_state(
            f"正在讀取 {requested_code}..."
        ):
            etf = load_etf_detail(
                api_base_url=api_base_url,
                code=requested_code,
            )

    except APIResourceNotFoundError as error:
        render_not_found_state(
            f"找不到 ETF：{requested_code}",
            hint=str(error),
        )

        render_code_form(
            default_code=requested_code
        )

        return

    except APIClientError as error:
        render_api_error(
            "無法取得 ETF 詳細資料。",
            error,
            hint=(
                "請確認 FastAPI 已在 "
                "127.0.0.1:8000 啟動。"
            ),
        )
        return

    profile: dict[str, Any] | None = None
    profile_error: APIClientError | None = None

    try:
        profile = load_etf_data_profile(
            api_base_url=api_base_url,
            code=requested_code,
        )

    except APIClientError as error:
        profile_error = error

    performance: dict[str, Any] | None = None
    performance_error: APIClientError | None = None

    try:
        performance = load_etf_performance(
            api_base_url=api_base_url,
            code=requested_code,
        )

    except APIClientError as error:
        performance_error = error

    dividend_history: dict[
        str,
        Any,
    ] | None = None

    dividend_history_error: (
        APIClientError | None
    ) = None

    try:
        dividend_history = (
            load_etf_dividends(
                api_base_url=api_base_url,
                code=requested_code,
            )
        )

    except APIClientError as error:
        dividend_history_error = error

    actual_76w: dict[
        str,
        Any,
    ] | None = None

    actual_76w_error: (
        APIClientError | None
    ) = None

    try:
        actual_76w = (
            load_etf_actual_76w(
                api_base_url=api_base_url,
                code=requested_code,
            )
        )

    except APIClientError as error:
        actual_76w_error = error

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
            load_etf_data_profile.clear()
            load_etf_performance.clear()
            load_etf_dividends.clear()
            load_etf_actual_76w.clear()
            load_dividend_detail.clear()
            st.rerun()

    render_etf_information(
        etf
    )

    if performance_error is not None:
        render_detail_section_error(
            "市價績效",
            "無法取得 ETF 績效資料。",
            performance_error,
        )

    elif performance is not None:
        render_etf_performance(
            performance
        )

    if dividend_history_error is not None:
        render_detail_section_error(
            "配息摘要",
            "無法取得 ETF 配息歷史。",
            dividend_history_error,
        )

    elif dividend_history is not None:
        render_dividend_summary(
            dividend_history
        )

    if actual_76w_error is not None:
        render_detail_section_error(
            "實際 76W 分析",
            "無法取得實際 76W 資料。",
            actual_76w_error,
        )

    elif actual_76w is not None:
        render_actual_76w_summary(
            actual_76w
        )

    if dividend_history is not None:
        render_dividend_history(
            api_base_url=api_base_url,
            history=dividend_history,
        )

    if profile_error is not None:
        render_detail_section_error(
            "資料來源與新鮮度",
            "無法取得 ETF 資料概況。",
            profile_error,
        )

    elif profile is not None:
        render_data_profile(
            profile
        )

    render_comparison_entry_point(
        etf
    )
