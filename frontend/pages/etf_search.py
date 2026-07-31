"""ETF 搜尋、篩選及分頁頁面。"""

from dataclasses import replace
import math
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_etfs,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    ETF_SEARCH_ROUTE,
    build_detail_query_params,
)
from frontend.query_state import (
    ETFSearchQueryState,
    PAGE_SIZE_OPTIONS,
    parse_etf_search_query_state,
    sync_query_params,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
    render_empty_state,
)


ACTIVE_FILTER_OPTIONS: dict[
    str,
    bool | None,
] = {
    "全部": None,
    "主動式": True,
    "被動式": False,
}

BOND_FILTER_OPTIONS: dict[
    str,
    bool | None,
] = {
    "全部": None,
    "非債券": False,
    "債券": True,
}

SEARCH_QUERY_SIGNATURE_KEY = (
    "_etf_search_query_signature"
)


def format_optional_number(
    value: Any,
    suffix: str,
    decimal_places: int = 2,
) -> str:
    """格式化可能為空白的數值。"""

    if value is None:
        return "—"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "格式異常"

    return (
        f"{number:,.{decimal_places}f}"
        f"{suffix}"
    )


def format_clickable_etf_row(
    item: dict[str, Any],
) -> str:
    """建立整列 ETF 顯示文字。"""

    code = str(
        item["code"]
    ).strip().upper()

    name = str(
        item["name"]
    ).strip()

    management_type = (
        "主動式"
        if item["is_active"]
        else "被動式"
    )

    asset_type = (
        "債券"
        if item["is_bond"]
        else "非債券"
    )

    listing_date = (
        str(item["listing_date"])
        if item["listing_date"]
        else "—"
    )

    fund_size = format_optional_number(
        item["fund_size"],
        " 億元",
    )

    expense_ratio = format_optional_number(
        item["expense_ratio"],
        "%",
    )

    return (
        f"**{code}**　"
        f"{name}"
        f"　│　{management_type}"
        f"　│　{asset_type}"
        f"　│　{listing_date}"
        f"　│　規模 {fund_size}"
        f"　│　費用率 {expense_ratio}"
    )


def render_clickable_etf_rows(
    items: list[dict[str, Any]],
    query_state: ETFSearchQueryState | None = None,
) -> None:
    """顯示整列可點擊的 ETF 搜尋結果。"""

    source_state = (
        query_state
        if query_state is not None
        else ETFSearchQueryState()
    )

    source_params = (
        source_state.to_query_params()
    )

    st.caption(
        "代號與名稱｜管理方式｜資產類型｜"
        "上市日期｜基金規模｜費用率"
    )

    for item in items:
        code = str(
            item["code"]
        ).strip().upper()

        name = str(
            item["name"]
        ).strip()

        st.page_link(
            "page_scripts/etf_detail_page.py",
            label=format_clickable_etf_row(
                item
            ),
            icon=":material/chevron_right:",
            icon_position="right",
            help=(
                f"查看 {code} {name} 詳細資料"
            ),
            width="stretch",
            query_params=(
                build_detail_query_params(
                    code=code,
                    source=str(
                        ETF_SEARCH_ROUTE.url_path
                    ),
                    source_query_params=(
                        source_params
                    ),
                )
            ),
        )


def apply_search_state(
    state: ETFSearchQueryState,
) -> None:
    """將 URL 狀態套用至 Session State。"""

    st.session_state[
        "etf_search_keyword"
    ] = state.keyword

    st.session_state[
        "etf_search_active_label"
    ] = state.active_label

    st.session_state[
        "etf_search_bond_label"
    ] = state.bond_label

    st.session_state[
        "etf_search_page_size"
    ] = state.page_size

    st.session_state[
        "etf_search_page_number"
    ] = state.page

    st.session_state[
        SEARCH_QUERY_SIGNATURE_KEY
    ] = tuple(
        sorted(
            state.to_query_params().items()
        )
    )


def get_search_state() -> ETFSearchQueryState:
    """由 Session State 建立目前 ETF 查詢狀態。"""

    return ETFSearchQueryState(
        keyword=str(
            st.session_state[
                "etf_search_keyword"
            ]
        ),
        active_label=str(
            st.session_state[
                "etf_search_active_label"
            ]
        ),
        bond_label=str(
            st.session_state[
                "etf_search_bond_label"
            ]
        ),
        page=int(
            st.session_state[
                "etf_search_page_number"
            ]
        ),
        page_size=int(
            st.session_state[
                "etf_search_page_size"
            ]
        ),
    )


def initialize_search_state() -> None:
    """由 URL 初始化或更新 ETF 搜尋狀態。"""

    state = parse_etf_search_query_state(
        st.query_params
    )

    canonical = state.to_query_params()

    sync_query_params(
        st.query_params,
        canonical,
    )

    signature = tuple(
        sorted(canonical.items())
    )

    if (
        st.session_state.get(
            SEARCH_QUERY_SIGNATURE_KEY
        )
        != signature
    ):
        apply_search_state(state)


def update_search_state(
    state: ETFSearchQueryState,
) -> None:
    """同步 ETF 查詢 Session State 與網址。"""

    apply_search_state(state)

    sync_query_params(
        st.query_params,
        state.to_query_params(),
    )


def reset_search_state() -> None:
    """清除所有 ETF 搜尋條件。"""

    update_search_state(
        ETFSearchQueryState()
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_etf_page(
    api_base_url: str,
    keyword: str | None,
    is_active: bool | None,
    is_bond: bool | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """取得並短暫快取 ETF 列表。"""

    return fetch_etfs(
        api_base_url=api_base_url,
        keyword=keyword,
        is_active=is_active,
        is_bond=is_bond,
        limit=limit,
        offset=offset,
    )


def render_search_form() -> None:
    """顯示 ETF 搜尋條件表單。"""

    active_labels = list(
        ACTIVE_FILTER_OPTIONS
    )

    bond_labels = list(
        BOND_FILTER_OPTIONS
    )

    with st.form(
        "etf_search_form"
    ):
        keyword_column, active_column = (
            st.columns(2)
        )

        with keyword_column:
            keyword = st.text_input(
                "關鍵字",
                value=str(
                    st.session_state[
                        "etf_search_keyword"
                    ]
                ),
                placeholder=(
                    "輸入 ETF 代號或名稱，"
                    "例如 00918"
                ),
            )

        with active_column:
            current_active_label = str(
                st.session_state[
                    "etf_search_active_label"
                ]
            )

            active_label = st.selectbox(
                "管理方式",
                options=active_labels,
                index=active_labels.index(
                    current_active_label
                ),
            )

        bond_column, size_column = (
            st.columns(2)
        )

        with bond_column:
            current_bond_label = str(
                st.session_state[
                    "etf_search_bond_label"
                ]
            )

            bond_label = st.selectbox(
                "資產類型",
                options=bond_labels,
                index=bond_labels.index(
                    current_bond_label
                ),
            )

        with size_column:
            current_page_size = int(
                st.session_state[
                    "etf_search_page_size"
                ]
            )

            page_size = st.selectbox(
                "每頁筆數",
                options=PAGE_SIZE_OPTIONS,
                index=(
                    PAGE_SIZE_OPTIONS.index(
                        current_page_size
                    )
                ),
            )

        submitted = (
            st.form_submit_button(
                "套用篩選",
                type="primary",
            )
        )

    if submitted:
        update_search_state(
            ETFSearchQueryState(
                keyword=keyword.strip(),
                active_label=active_label,
                bond_label=bond_label,
                page=1,
                page_size=page_size,
            )
        )

        load_etf_page.clear()
        st.rerun()


def render_action_buttons() -> None:
    """顯示清除及重新載入按鈕。"""

    clear_column, refresh_column, _ = (
        st.columns(
            [
                1,
                1,
                4,
            ]
        )
    )

    with clear_column:
        clear_clicked = st.button(
            "清除條件",
            key="clear_etf_filters",
        )

    with refresh_column:
        refresh_clicked = st.button(
            "重新載入",
            key="refresh_etf_data",
        )

    if clear_clicked:
        reset_search_state()
        load_etf_page.clear()
        st.rerun()

    if refresh_clicked:
        load_etf_page.clear()
        st.rerun()


def render_pagination(
    state: ETFSearchQueryState,
    total_pages: int,
) -> None:
    """顯示上一頁與下一頁控制項。"""

    previous_column, page_column, next_column = (
        st.columns(
            [
                1,
                2,
                1,
            ]
        )
    )

    with previous_column:
        previous_clicked = st.button(
            "← 上一頁",
            disabled=(
                state.page <= 1
            ),
            key="previous_etf_page",
        )

    with page_column:
        st.write(
            f"第 {state.page} 頁，"
            f"共 {total_pages} 頁"
        )

    with next_column:
        next_clicked = st.button(
            "下一頁 →",
            disabled=(
                state.page >= total_pages
            ),
            key="next_etf_page",
        )

    if previous_clicked:
        update_search_state(
            replace(
                state,
                page=state.page - 1,
            )
        )
        st.rerun()

    if next_clicked:
        update_search_state(
            replace(
                state,
                page=state.page + 1,
            )
        )
        st.rerun()


def render_etf_search() -> None:
    """顯示 ETF 搜尋頁面。"""

    initialize_search_state()

    st.title("ETF 查詢")

    st.caption(
        "搜尋及篩選臺灣 ETF 官方主資料"
    )

    render_search_form()
    render_action_buttons()

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    state = get_search_state()

    is_active = ACTIVE_FILTER_OPTIONS[
        state.active_label
    ]

    is_bond = BOND_FILTER_OPTIONS[
        state.bond_label
    ]

    offset = (
        state.page - 1
    ) * state.page_size

    try:
        with loading_state(
            "正在讀取 ETF 資料..."
        ):
            result = load_etf_page(
                api_base_url=api_base_url,
                keyword=(
                    state.keyword
                    if state.keyword
                    else None
                ),
                is_active=is_active,
                is_bond=is_bond,
                limit=state.page_size,
                offset=offset,
            )

    except APIClientError as error:
        render_api_error(
            "無法取得 ETF 資料。",
            error,
            hint=(
                "請確認 FastAPI 已在 "
                "127.0.0.1:8000 啟動。"
            ),
        )
        return

    total = int(result["total"])
    items = result["items"]

    total_pages = max(
        1,
        math.ceil(
            total / state.page_size
        ),
    )

    if state.page > total_pages:
        update_search_state(
            replace(
                state,
                page=total_pages,
            )
        )
        st.rerun()

    total_column, page_column, count_column = (
        st.columns(3)
    )

    with total_column:
        st.metric(
            "符合條件",
            f"{total:,} 檔",
        )

    with page_column:
        st.metric(
            "目前頁次",
            (
                f"{state.page}"
                f" / {total_pages}"
            ),
        )

    with count_column:
        st.metric(
            "本頁筆數",
            f"{len(items)}",
        )

    st.divider()

    if not items:
        render_empty_state(
            "目前沒有符合條件的 ETF。",
            hint=(
                "可清除條件或調整關鍵字、"
                "管理方式與資產類型。"
            ),
        )
        return

    render_clickable_etf_rows(
        items,
        query_state=state,
    )

    st.caption(
        f"目前顯示第 "
        f"{offset + 1:,} 至 "
        f"{offset + len(items):,} 筆，"
        f"共 {total:,} 筆"
    )

    st.caption(
        "滑鼠移到 ETF 資料列時，"
        "整列會顯示可點擊效果；"
        "單擊即可進入詳細資料頁。"
    )

    render_pagination(
        state=state,
        total_pages=total_pages,
    )
