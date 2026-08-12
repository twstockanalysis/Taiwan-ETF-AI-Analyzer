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
    fetch_etf_latest_close,
    fetch_etf_target_analysis,
    fetch_tax_reinvestment_scenarios,
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


@st.cache_data(ttl=60, show_spinner=False)
def load_etf_latest_close(
    api_base_url: str,
    code: str,
) -> dict[str, Any]:
    """取得並短暫快取官方最新收盤價。"""

    return fetch_etf_latest_close(api_base_url=api_base_url, code=code)


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


def format_dividend_summary_date(
    value: Any,
) -> str:
    """格式化配息摘要日期，缺少時顯示破折號。"""

    return format_iso_date(
        value,
        missing_text="—",
    )


def format_dividend_yield(
    value: Any,
) -> str:
    """格式化單次殖利率並保留缺資料語意。"""

    return format_shared_percentage(
        value,
        missing_text="—",
        invalid_text="資料格式異常",
    )


def build_dividend_summary_chart_rows(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """建立依除息日排序的股利與殖利率趨勢資料。"""

    rows = [
        {
            "除息日": item["ex_dividend_date"],
            "現金股利": float(
                item["amount_per_unit"]
            ),
            "殖利率": (
                float(item["yield_pct"])
                if item.get("yield_pct")
                is not None
                else None
            ),
        }
        for item in items
        if item.get("ex_dividend_date")
        is not None
        and item.get("amount_per_unit")
        is not None
    ]

    return sorted(
        rows,
        key=lambda row: str(row["除息日"]),
    )


def format_dividend_yield_basis(
    item: dict[str, Any],
) -> str:
    """顯示官方或回退殖利率的可追溯依據。"""

    basis = item.get("yield_basis")

    if basis == "OFFICIAL":
        source_id = item.get(
            "yield_source_id"
        )

        return (
            f"官方（{source_id}）"
            if source_id
            else "官方"
        )

    if basis == "CALCULATED":
        reference_date = (
            format_dividend_summary_date(
                item.get(
                    "reference_trade_date"
                )
            )
        )

        reference_price = item.get(
            "reference_close_price"
        )

        price_text = (
            format_dividend_amount(
                reference_price,
                "TWD",
            )
            if reference_price is not None
            else "—"
        )

        return (
            "回退計算（"
            f"{reference_date} 收盤 {price_text}）"
        )

    return "—"


def build_dividend_summary_rows(
    items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """建立較完整的歷次配息摘要明細。"""

    return [
        {
            "年季": (
                str(item["distribution_period"])
                if item.get(
                    "distribution_period"
                ) is not None
                else "—"
            ),
            "現金股利": format_dividend_amount(
                item.get("amount_per_unit"),
                item.get("currency"),
            ),
            "殖利率": format_dividend_yield(
                item.get("yield_pct")
            ),
            "殖利率依據": (
                format_dividend_yield_basis(
                    item
                )
            ),
            "除息日": (
                format_dividend_summary_date(
                    item.get(
                        "ex_dividend_date"
                    )
                )
            ),
            "股利發放日": (
                format_dividend_summary_date(
                    item.get(
                        "payment_date"
                    )
                )
            ),
        }
        for item in items
    ]


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

    st.markdown(
        "**歷次現金股利與殖利率趨勢**"
    )

    chart_rows = (
        build_dividend_summary_chart_rows(
            items
        )
    )

    if chart_rows:
        st.vega_lite_chart(
            chart_rows,
            {
                "layer": [
                    {
                        "mark": {
                            "type": "line",
                            "point": True,
                            "color": "#4C78A8",
                        },
                        "encoding": {
                            "x": {
                                "field": "除息日",
                                "type": "temporal",
                                "axis": {
                                    "title": "除息日"
                                },
                            },
                            "y": {
                                "field": "現金股利",
                                "type": "quantitative",
                                "axis": {
                                    "title": (
                                        "現金股利／單位"
                                    ),
                                    "titleColor": (
                                        "#4C78A8"
                                    ),
                                },
                            },
                            "tooltip": [
                                {
                                    "field": "除息日",
                                    "type": "temporal",
                                },
                                {
                                    "field": "現金股利",
                                    "type": "quantitative",
                                },
                            ],
                        },
                    },
                    {
                        "mark": {
                            "type": "line",
                            "point": True,
                            "color": "#F58518",
                        },
                        "encoding": {
                            "x": {
                                "field": "除息日",
                                "type": "temporal",
                            },
                            "y": {
                                "field": "殖利率",
                                "type": "quantitative",
                                "axis": {
                                    "title": "單次殖利率（%）",
                                    "orient": "right",
                                    "titleColor": (
                                        "#F58518"
                                    ),
                                },
                            },
                            "tooltip": [
                                {
                                    "field": "除息日",
                                    "type": "temporal",
                                },
                                {
                                    "field": "殖利率",
                                    "type": "quantitative",
                                    "format": ".2f",
                                },
                            ],
                        },
                    },
                ],
                "resolve": {
                    "scale": {
                        "y": "independent"
                    }
                },
            },
            width="stretch",
        )

    else:
        st.info(
            "目前沒有可繪製趨勢的除息資料。"
        )

    st.caption(
        "年季只採官方收益所屬年季；"
        "殖利率優先採官方值，缺少時才以"
        "每單位現金股利 ÷ 除息前一交易日收盤價 × 100 計算。"
    )

    st.table(
        build_dividend_summary_rows(
            items
        )
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


_REINVESTMENT_POLICY_LABELS = {
    "NO_REINVESTMENT": "不再投入",
    "EXCESS_ONLY": "僅投入超過目標的現金",
    "CUSTOM_PERCENTAGE": "自訂比例再投入",
    "FULL_REINVESTMENT": "全部再投入",
}


def _build_tax_rule_payload(
    *,
    income_tax_rate_54c: float,
    tax_credit_rate_54c: float,
    other_income_tax_rate: float,
    allow_credit_offset: bool,
) -> dict[str, Any]:
    """建立畫面明示的版本化稅務假設。"""

    common_other_codes = (
        "5A",
        "5B",
        "61D",
        "71",
        "76",
        "OTHER",
    )
    assumptions = [
        {
            "component_code": "54C",
            "income_tax_rate_pct": income_tax_rate_54c,
            "tax_credit_rate_pct": tax_credit_rate_54c,
            "supplementary_premium_applicable": True,
        },
        {
            "component_code": "76W",
            "income_tax_rate_pct": 0,
            "tax_credit_rate_pct": 0,
            "supplementary_premium_applicable": False,
        },
    ]
    assumptions.extend(
        {
            "component_code": code,
            "income_tax_rate_pct": other_income_tax_rate,
            "tax_credit_rate_pct": 0,
            "supplementary_premium_applicable": code in {"5A", "5B"},
        }
        for code in common_other_codes
    )
    return {
        "rule_version": "TW-INDIVIDUAL-2026.1",
        "effective_date": "2021-01-01",
        "supplementary_premium_rate_pct": 2.11,
        "supplementary_premium_payment_threshold": 20000,
        "supplementary_premium_payment_cap": 10000000,
        "annual_tax_credit_cap": 80000,
        "allow_credit_offset_other_tax": allow_credit_offset,
        "component_assumptions": assumptions,
    }


def _render_tax_reinvestment_result(result: dict[str, Any]) -> None:
    """顯示歷史事實與四種前瞻假設，不產生推薦。"""

    facts = result["historical_facts"]
    calculation = result["calculation"]
    if result["status"] == "PARTIAL":
        issue_text = "、".join(
            (
                f"{item['field']} ({item['reason']})"
                + (
                    f"：{item['component_code']}"
                    if item.get("component_code")
                    else ""
                )
            )
            for item in calculation.get("issues", [])
        )
        st.warning(
            "部分結果無法計算；缺少的資料不會被當成 0。"
            + (f" {issue_text}" if issue_text else "")
        )

    with st.container(border=True):
        st.markdown("**歷史資料事實**")
        st.caption(
            "正式組成與歷史報酬只用來建立情境起點，"
            "不代表未來仍會持續。"
        )
        st.table(
            [
                {
                    "正式組成事件": facts.get("component_source_event_id")
                    or "尚未取得",
                    "正式組成日期": facts.get("component_source_date")
                    or "尚未取得",
                    "歷史年化配息率": format_shared_percentage(
                        facts.get("annual_gross_distribution_rate_pct")
                    ),
                    "價格報酬期間": facts.get("price_return_period_code")
                    or "尚未取得",
                    "年化價格報酬假設": format_shared_percentage(
                        facts.get("annual_price_return_pct")
                    ),
                }
            ]
        )
        component_mix = facts.get("actual_component_mix")
        if component_mix:
            st.table(
                [
                    {
                        "正式所得代碼": item["component_code"],
                        "名稱": item.get("component_name") or "—",
                        "ACTUAL 比例": format_shared_percentage(
                            item.get("ratio_pct")
                        ),
                    }
                    for item in component_mix
                ]
            )

    st.markdown("**情境估算結果**")
    st.caption(
        f"規則版本 {calculation['rule_version']}；"
        f"生效日 {calculation['rule_effective_date']}。"
        "以下為估算，不是稅務建議，也不標示最佳方案。"
    )
    rows = []
    failed_total_return = False
    for item in calculation["scenarios"]:
        failed_total_return = failed_total_return or (
            item.get("total_return_check_passed") is False
        )
        rows.append(
            {
                "配息使用方式": _REINVESTMENT_POLICY_LABELS.get(
                    item["policy"], item["policy"]
                ),
                "可使用現金": format_shared_amount(
                    item.get("usable_cash"), calculation["currency"],
                    decimal_places=2,
                ),
                "再投入現金": format_shared_amount(
                    item.get("reinvested_cash"), calculation["currency"],
                    decimal_places=2,
                ),
                "期末單位數": format_number(
                    item.get("ending_units"), decimal_places=4
                ),
                "期末價值": format_shared_amount(
                    item.get("ending_value"), calculation["currency"],
                    decimal_places=2,
                ),
                "估算稅與補充保費": format_shared_amount(
                    item.get("modeled_tax_cost"), calculation["currency"],
                    decimal_places=2,
                ),
                "稅後總報酬": format_shared_percentage(
                    item.get("after_tax_total_return_pct"), signed=True
                ),
            }
        )
    st.table(rows)
    if failed_total_return:
        st.error(
            "至少一個情境未通過總報酬檢查；"
            "稅務差異不能覆蓋資產價值惡化。"
        )


def build_target_monthly_cash_rows(
    monthly_cash_flow: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """建立 1 至 12 月現金流表格並清楚區分缺值與零。"""

    rows: list[dict[str, Any]] = []
    for item in monthly_cash_flow:
        rows.append(
            {
                "月份": f"{item['month']} 月",
                "歷史入帳次數": item["event_count"],
                "涵蓋年數": item["observed_year_count"],
                "年化稅前現金": format_shared_amount(
                    item.get("annualized_gross_cash"),
                    missing_text="無法計算",
                    decimal_places=2,
                ),
                "年化稅後現金": format_shared_amount(
                    item.get("annualized_after_tax_cash"),
                    missing_text="無法計算",
                    decimal_places=2,
                ),
                "最近入帳日": format_iso_date(
                    item.get("latest_payment_date")
                ),
            }
        )
    return rows


def _render_target_analysis_result(result: dict[str, Any]) -> None:
    """呈現固定現金流目標與歷史逐月估算。"""

    cash_flow = result["cash_flow"]
    scenario = result["scenario_estimate"]
    with st.container(horizontal=True, border=True):
        st.metric(
            "所需本金",
            format_shared_amount(
                cash_flow.get("required_capital"), decimal_places=0
            ),
        )
        st.metric(
            "資金缺口",
            format_shared_amount(
                cash_flow.get("funding_shortfall"), decimal_places=0
            ),
        )
        st.metric(
            "年度稅後目標",
            format_shared_amount(
                cash_flow.get("annual_after_tax_target"), decimal_places=0
            ),
        )
        st.metric(
            "目前目標覆蓋率",
            format_shared_percentage(cash_flow.get("target_coverage_pct")),
        )

    st.caption(
        "下表以歷史付款月份按涵蓋年數年化；無入帳資料顯示為無法計算，"
        "不代表該月現金流為 0。"
    )
    st.table(build_target_monthly_cash_rows(result["monthly_cash_flow"]))
    st.caption(
        "不再投入配息情境的估算稅後總報酬："
        + format_shared_percentage(
            scenario.get("after_tax_total_return_pct"), signed=True
        )
    )
    for warning in result.get("warnings", []):
        st.warning(warning.get("message", "歷史結果不保證未來表現。"))
        if warning.get("as_of_date") or warning.get("source_id"):
            basis = "；".join(
                item
                for item in (
                    (
                        f"資料基準日 {warning['as_of_date']}"
                        if warning.get("as_of_date")
                        else ""
                    ),
                    (
                        f"來源 {warning['source_id']}"
                        if warning.get("source_id")
                        else ""
                    ),
                )
                if item
            )
            st.caption(basis)
        if warning.get("evidence"):
            evidence_text = "、".join(
                f"{key}={value}"
                for key, value in warning["evidence"].items()
                if value is not None and value != ""
            )
            st.caption(f"判定證據：{evidence_text}")
    if result.get("unavailable_fields"):
        fields = "、".join(
            str(item.get("field", "未知欄位"))
            for item in result["unavailable_fields"]
        )
        st.info(f"目前無法計算：{fields}")


def render_base_target_analysis(
    *,
    api_base_url: str,
    etf: dict[str, Any],
    latest_close: dict[str, Any] | None,
    latest_close_error: APIClientError | None = None,
) -> None:
    """呈現基準 ETF 的固定現金流目標分析。"""

    st.divider()
    st.subheader("目標現金流分析")
    st.caption("依歷史配息與市價績效估算；不是報酬承諾或投資建議。")
    if latest_close_error is not None:
        render_warning_state("無法取得官方最新收盤價。", detail=latest_close_error)
        return
    if latest_close is None or latest_close.get("close_price") is None:
        st.warning("目前沒有可追溯的官方收盤價，因此暫不提供本金需求估算。")
        return

    st.info(
        "計算採用官方收盤價 "
        f"{latest_close['close_price']:.2f} TWD（{latest_close['trade_date']}；"
        f"來源 {latest_close['source_id']}），價格不可手動覆寫。"
    )
    with st.form(f"target_analysis_{etf['code']}"):
        columns = st.columns(3)
        with columns[0]:
            held_units = st.number_input(
                "目前持有單位數", min_value=0, value=0, step=100
            )
            monthly_target = st.number_input(
                "每月稅後現金目標（TWD）",
                min_value=0.0,
                value=3000.0,
                step=500.0,
            )
        with columns[1]:
            analysis_years = st.number_input(
                "估算年數", min_value=1, max_value=50, value=10
            )
            history_years = st.number_input(
                "歷史資料年數", min_value=1, max_value=10, value=3
            )
        with columns[2]:
            has_deduction = st.checkbox("提供現金扣除率假設", value=False)
            deduction_rate = st.number_input(
                "現金扣除率（%）",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                disabled=not has_deduction,
            )
        submitted = st.form_submit_button(
            "計算現金流目標", type="primary", icon=":material/calculate:"
        )

    state_key = f"target_analysis_result_{etf['code']}"
    if submitted:
        payload = {
            "held_units": int(held_units),
            "unit_price": latest_close["close_price"],
            "monthly_after_tax_target": monthly_target,
            "analysis_years": int(analysis_years),
            "history_years": int(history_years),
            "cash_deduction_rate_pct": (
                deduction_rate if has_deduction else None
            ),
        }
        try:
            with loading_state("正在計算目標現金流..."):
                st.session_state[state_key] = fetch_etf_target_analysis(
                    api_base_url=api_base_url,
                    code=str(etf["code"]),
                    payload=payload,
                )
        except APIClientError as error:
            render_warning_state("無法完成目標現金流分析。", detail=error)
    if state_key in st.session_state:
        _render_target_analysis_result(st.session_state[state_key])


def render_tax_reinvestment_analysis(
    *,
    api_base_url: str,
    etf: dict[str, Any],
) -> None:
    """顯示 M10-4 稅務與再投資估算表單。"""

    st.divider()
    st.subheader("稅務與再投入情境")
    st.caption(
        "適用範圍：持有台灣上市 ETF 的台灣稅務居民個人。"
        "請依自身申報情況調整有效稅率；結果僅供估算。"
    )

    with st.form(f"tax_reinvestment_{etf['code']}"):
        input_columns = st.columns(3)
        with input_columns[0]:
            held_units = st.number_input(
                "持有單位數", min_value=0.0, value=1000.0, step=100.0
            )
            unit_price = st.number_input(
                "目前每單位價格（TWD）",
                min_value=0.01,
                value=30.0,
                step=0.1,
            )
            monthly_target = st.number_input(
                "每月希望保留的現金（TWD）",
                min_value=0.0,
                value=3000.0,
                step=500.0,
            )
        with input_columns[1]:
            analysis_years = st.number_input(
                "估算年數", min_value=1, max_value=50, value=10
            )
            history_years = st.number_input(
                "歷史資料年數", min_value=1, max_value=10, value=3
            )
            payments_per_year = st.number_input(
                "假設每年配息次數", min_value=1, max_value=365, value=4
            )
            custom_pct = st.number_input(
                "自訂再投入比例（%）",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
            )
        with input_columns[2]:
            rate_54c = st.number_input(
                "54C 有效所得稅率（%）",
                min_value=0.0,
                max_value=100.0,
                value=12.0,
            )
            credit_54c = st.number_input(
                "54C 可用抵減率（%）",
                min_value=0.0,
                max_value=100.0,
                value=8.5,
            )
            other_rate = st.number_input(
                "其他所得有效稅率（%）",
                min_value=0.0,
                max_value=100.0,
                value=12.0,
            )
            allow_credit_offset = st.checkbox(
                "允許股利抵減影響其他所得稅額",
                value=False,
            )
        submitted = st.form_submit_button(
            "比較四種情境",
            type="primary",
            icon=":material/calculate:",
        )

    state_key = f"tax_reinvestment_result_{etf['code']}"
    if submitted:
        request_payload = {
            "held_units": held_units,
            "unit_price": unit_price,
            "monthly_cash_target": monthly_target,
            "analysis_years": int(analysis_years),
            "history_years": int(history_years),
            "payments_per_year": int(payments_per_year),
            "custom_reinvestment_pct": custom_pct,
            "tax_rule": _build_tax_rule_payload(
                income_tax_rate_54c=rate_54c,
                tax_credit_rate_54c=credit_54c,
                other_income_tax_rate=other_rate,
                allow_credit_offset=allow_credit_offset,
            ),
        }
        try:
            with loading_state("正在計算稅務與再投入情境..."):
                st.session_state[state_key] = (
                    fetch_tax_reinvestment_scenarios(
                        api_base_url=api_base_url,
                        code=str(etf["code"]),
                        payload=request_payload,
                    )
                )
        except APIClientError as error:
            render_warning_state("無法完成稅務情境估算。", detail=error)

    if state_key in st.session_state:
        _render_tax_reinvestment_result(st.session_state[state_key])


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

    latest_close: dict[str, Any] | None = None
    latest_close_error: APIClientError | None = None
    try:
        latest_close = load_etf_latest_close(
            api_base_url=api_base_url,
            code=requested_code,
        )
    except APIClientError as error:
        latest_close_error = error

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
            load_etf_latest_close.clear()
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

    render_base_target_analysis(
        api_base_url=api_base_url,
        etf=etf,
        latest_close=latest_close,
        latest_close_error=latest_close_error,
    )

    render_tax_reinvestment_analysis(
        api_base_url=api_base_url,
        etf=etf,
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
