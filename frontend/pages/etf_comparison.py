"""ETF 多檔比較頁面。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_etf_comparison,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    build_comparison_query_params,
    create_streamlit_page,
    resolve_comparison_return,
)
from frontend.query_state import (
    ETFComparisonQueryState,
    normalize_comparison_codes,
    parse_etf_comparison_query_state,
    query_params_to_dict,
    sync_query_params,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
)


COMPARISON_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)


def format_optional_date(
    value: Any,
) -> str:
    """格式化可缺少日期。"""

    if value is None:
        return "尚無資料"

    text = str(value).strip()

    return text or "尚無資料"


def format_optional_number(
    value: Any,
    *,
    suffix: str = "",
    decimal_places: int = 2,
) -> str:
    """格式化可缺少數值。"""

    if value is None:
        return "尚無資料"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"

    return (
        f"{number:,.{decimal_places}f}"
        f"{suffix}"
    )


def format_return(
    value: Any,
) -> str:
    """格式化市價報酬率。"""

    if value is None:
        return "歷史資料不足"

    try:
        return f"{float(value):+.2f}%"

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"


def format_percentage(
    value: Any,
) -> str:
    """格式化正式百分比並區分缺資料與零。"""

    if value is None:
        return "尚未取得"

    try:
        return f"{float(value):.2f}%"

    except (
        TypeError,
        ValueError,
    ):
        return "資料格式異常"


def build_identity_rows(
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    """建立基本資料並列表。"""

    rows: list[dict[str, str]] = []

    for item in comparison["items"]:
        etf = item["etf"]

        rows.append(
            {
                "ETF": (
                    f"{etf['code']} {etf['name']}"
                ),
                "管理方式": (
                    "主動式"
                    if etf["is_active"]
                    else "被動式"
                ),
                "資產類型": (
                    "債券"
                    if etf["is_bond"]
                    else "非債券"
                ),
                "上市日期": (
                    format_optional_date(
                        etf["listing_date"]
                    )
                ),
                "基金規模": (
                    format_optional_number(
                        etf["fund_size"],
                        suffix=" 億元",
                    )
                ),
                "費用率": (
                    format_optional_number(
                        etf["expense_ratio"],
                        suffix="%",
                    )
                ),
            }
        )

    return rows


def build_performance_rows(
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    """建立 1M、3M、6M、1Y 績效比較列。"""

    lookup_by_code: dict[
        str,
        dict[str, dict[str, Any]],
    ] = {}

    for item in comparison["items"]:
        code = item["etf"]["code"]

        lookup_by_code[code] = {
            performance_item[
                "period_code"
            ]: performance_item
            for performance_item in (
                item["performance_items"]
            )
        }

    rows: list[dict[str, str]] = []

    for period in comparison["periods"]:
        row: dict[str, str] = {
            "期間": period,
        }

        for item in comparison["items"]:
            code = item["etf"]["code"]
            performance_item = (
                lookup_by_code[code].get(
                    period
                )
            )

            if performance_item is None:
                row[code] = "歷史資料不足"

            else:
                row[code] = (
                    format_return(
                        performance_item[
                            "return_pct"
                        ]
                    )
                    + "\n截至 "
                    + performance_item[
                        "as_of_date"
                    ]
                )

        rows.append(row)

    return rows


def build_dividend_rows(
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    """建立配息與正式 76W 比較列。"""

    rows: list[dict[str, str]] = []

    for item in comparison["items"]:
        etf = item["etf"]
        dividend = item["dividend"]
        actual = item["actual_76w"]

        latest_amount = (
            "尚無資料"
            if dividend[
                "latest_amount_per_unit"
            ] is None
            else (
                format_optional_number(
                    dividend[
                        "latest_amount_per_unit"
                    ],
                    decimal_places=4,
                )
                + " "
                + str(
                    dividend["currency"]
                    or "TWD"
                )
            )
        )

        rows.append(
            {
                "ETF": (
                    f"{etf['code']} {etf['name']}"
                ),
                "配息事件": (
                    f"{dividend['event_count']:,} 次"
                ),
                "最新事件日": (
                    format_optional_date(
                        dividend[
                            "latest_event_date"
                        ]
                    )
                ),
                "最新每單位配息": (
                    latest_amount
                ),
                "正式 76W 紀錄": (
                    f"{actual['record_count']:,} 次"
                ),
                "最新 76W 比例": (
                    format_percentage(
                        actual[
                            "latest_ratio_pct"
                        ]
                    )
                ),
                "平均 76W 比例": (
                    format_percentage(
                        actual[
                            "average_ratio_pct"
                        ]
                    )
                ),
            }
        )

    return rows


def build_completeness_rows(
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    """建立資料完整度比較列。"""

    rows: list[dict[str, str]] = []

    for item in comparison["items"]:
        etf = item["etf"]
        completeness = item[
            "completeness"
        ]

        missing_sections = (
            completeness[
                "missing_sections"
            ]
        )

        rows.append(
            {
                "ETF": (
                    f"{etf['code']} {etf['name']}"
                ),
                "完整度": (
                    format_percentage(
                        completeness[
                            "score_pct"
                        ]
                    )
                ),
                "可用區塊": (
                    f"{completeness['available_section_count']}"
                    f"/{completeness['total_section_count']}"
                ),
                "缺少區塊": (
                    "、".join(
                        missing_sections
                    )
                    if missing_sections
                    else "無"
                ),
            }
        )

    return rows


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_etf_comparison(
    api_base_url: str,
    codes: tuple[str, ...],
) -> dict[str, Any]:
    """取得並短暫快取 ETF 比較資料。"""

    return fetch_etf_comparison(
        api_base_url=api_base_url,
        codes=codes,
    )


def _return_state_params() -> dict[str, str]:
    """保留比較頁來源參數。"""

    current = query_params_to_dict(
        st.query_params
    )

    return {
        key: value
        for key, value in current.items()
        if (
            key == "from"
            or key.startswith("return_")
        )
    }


def update_comparison_codes(
    codes: tuple[str, ...],
) -> None:
    """更新網址中的比較清單並保留返回狀態。"""

    comparison_params = (
        ETFComparisonQueryState(
            codes=codes
        ).to_query_params()
    )

    sync_query_params(
        st.query_params,
        {
            **comparison_params,
            **_return_state_params(),
        },
    )


def render_return_button() -> None:
    """返回原始頁面並保留其 URL 狀態。"""

    route, params = (
        resolve_comparison_return(
            st.query_params
        )
    )

    if st.button(
        f"← 返回 {route.title}",
        type="secondary",
    ):
        st.switch_page(
            create_streamlit_page(route),
            query_params=params,
        )


def render_code_form(
    codes: tuple[str, ...],
) -> None:
    """顯示比較代號輸入與清單操作。"""

    with st.form(
        "etf_comparison_form"
    ):
        code_text = st.text_input(
            "ETF 代號",
            value=",".join(codes),
            placeholder=(
                "輸入 2 至 4 個代號，"
                "例如 0050,0056,00878"
            ),
            help=(
                "使用半形逗號分隔；"
                "重複代號會自動移除。"
            ),
        )

        submitted = (
            st.form_submit_button(
                "更新比較",
                type="primary",
            )
        )

    if submitted:
        raw_codes = [
            value.strip()
            for value in code_text.split(",")
            if value.strip()
        ]

        normalized = (
            normalize_comparison_codes(
                raw_codes
            )
        )

        if len(raw_codes) > 4:
            st.warning(
                "ETF 比較最多支援 4 檔。"
            )
            return

        if not normalized:
            st.warning(
                "請輸入至少一個合法 ETF 代號。"
            )
            return

        update_comparison_codes(
            normalized
        )
        load_etf_comparison.clear()
        st.rerun()

    if not codes:
        return

    columns = st.columns(
        len(codes) + 1
    )

    for column, code in zip(
        columns,
        codes,
        strict=False,
    ):
        with column:
            if st.button(
                f"移除 {code}",
                key=f"remove_compare_{code}",
                width="stretch",
            ):
                update_comparison_codes(
                    tuple(
                        current_code
                        for current_code in codes
                        if current_code != code
                    )
                )
                load_etf_comparison.clear()
                st.rerun()

    with columns[-1]:
        if st.button(
            "清空比較",
            key="clear_comparison",
            width="stretch",
        ):
            update_comparison_codes(())
            load_etf_comparison.clear()
            st.rerun()


def render_etf_comparison() -> None:
    """顯示 ETF 比較頁。"""

    st.title("ETF 比較")
    st.caption(
        "並列比較 2 至 4 檔 ETF；"
        "目前績效為 PRICE_RETURN，"
        "不包含配息再投資。"
    )

    render_return_button()

    state = parse_etf_comparison_query_state(
        st.query_params
    )

    sync_query_params(
        st.query_params,
        {
            **state.to_query_params(),
            **_return_state_params(),
        },
    )

    render_code_form(
        state.codes
    )

    if len(state.codes) < 2:
        st.info(
            "請選擇至少 2 檔 ETF 才能開始比較。"
        )
        return

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
            "正在整理 ETF 比較資料..."
        ):
            comparison = (
                load_etf_comparison(
                    api_base_url,
                    state.codes,
                )
            )

    except APIClientError as error:
        render_api_error(
            "無法取得 ETF 比較資料。",
            error,
            hint=(
                "請確認代號存在且 FastAPI "
                "已正常啟動。"
            ),
        )
        return

    refresh_column, _ = st.columns(
        [1, 4]
    )

    with refresh_column:
        if st.button(
            "重新載入比較",
            key="refresh_etf_comparison",
        ):
            load_etf_comparison.clear()
            st.rerun()

    st.subheader("基本資料")
    st.table(
        build_identity_rows(
            comparison
        )
    )

    st.divider()
    st.subheader("市價績效")
    st.caption(
        "每個期間獨立比較；"
        "缺少歷史資料不轉換為 0%。"
    )
    st.table(
        build_performance_rows(
            comparison
        )
    )

    st.divider()
    st.subheader("配息與正式 76W")
    st.caption(
        "只有 ACTUAL + 76W 才列為正式 76W；"
        "預估已實現資本利得不列入。"
    )
    st.table(
        build_dividend_rows(
            comparison
        )
    )

    st.divider()
    st.subheader("資料完整度")
    st.caption(
        "完整度只代表目前五個比較資料區塊的"
        "可用情況，不是投資評分。"
    )
    st.table(
        build_completeness_rows(
            comparison
        )
    )
