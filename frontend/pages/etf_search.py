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
from frontend.ui.components import (
    render_page_title,
    render_pagination_controls,
)
from frontend.ui.formatters import (
    format_number,
    management_type_label,
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

NON_BOND_LABEL = "非債券"

RESULT_ACTION_KEY = "etf_search_detail_action"

SEARCH_QUERY_SIGNATURE_KEY = (
    "_etf_search_query_signature"
)


def format_optional_number(
    value: Any,
    suffix: str,
    decimal_places: int = 2,
) -> str:
    """格式化可能為空白的數值。"""

    return format_number(
        value,
        decimal_places=decimal_places,
        suffix=suffix,
        missing_text="—",
        invalid_text="格式異常",
    )


def format_etf_result_row(
    item: dict[str, Any],
) -> dict[str, str]:
    """建立欄位固定的 ETF 搜尋結果。"""

    code = str(
        item["code"]
    ).strip().upper()

    name = str(
        item["name"]
    ).strip()

    management_type = (
        management_type_label(
            item["is_active"]
        )
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

    return {
        "code": code,
        "name": name,
        "management_type": management_type,
        "listing_date": listing_date,
        "fund_size": fund_size,
        "expense_ratio": expense_ratio,
    }


def render_clickable_etf_rows(
    items: list[dict[str, Any]],
    query_state: ETFSearchQueryState | None = None,
) -> None:
    """以固定欄位資料表顯示 ETF 清單。"""

    source_state = (
        query_state
        if query_state is not None
        else ETFSearchQueryState(
            bond_label=NON_BOND_LABEL
        )
    )

    rows = [
        format_etf_result_row(item)
        for item in items
    ]

    selection = st.dataframe(
        rows,
        column_order=(
            "code",
            "name",
            "management_type",
            "listing_date",
            "fund_size",
            "expense_ratio",
        ),
        column_config={
            "code": st.column_config.TextColumn(
                "代號",
                width="small",
                pinned=True,
            ),
            "name": st.column_config.TextColumn(
                "名稱",
                width="large",
                pinned=True,
            ),
            "management_type": (
                st.column_config.TextColumn(
                    "管理方式",
                    width="small",
                )
            ),
            "listing_date": (
                st.column_config.TextColumn(
                    "上市日期",
                    width="medium",
                )
            ),
            "fund_size": st.column_config.TextColumn(
                "基金規模",
                width="medium",
            ),
            "expense_ratio": (
                st.column_config.TextColumn(
                    "費用率",
                    width="small",
                )
            ),
        },
        hide_index=True,
        width="stretch",
        height="content",
        key=RESULT_ACTION_KEY,
        on_select="rerun",
        selection_mode="single-row",
    )

    selected_rows = selection.selection.rows
    if selected_rows:
        open_etf_detail(
            items,
            source_state,
            row_index=int(selected_rows[0]),
        )


def open_etf_detail(
    items: list[dict[str, Any]],
    source_state: ETFSearchQueryState,
    *,
    row_index: int | None = None,
) -> None:
    """由資料表選取列開啟 ETF 詳細資料。"""

    if row_index is None:
        selection = st.session_state.get(
            RESULT_ACTION_KEY,
            {},
        ).get("selection", {})
        selected_rows = selection.get(
            "rows",
            [],
        )
        if not selected_rows:
            return
        row_index = int(selected_rows[0])

    if not 0 <= row_index < len(items):
        return

    item = items[row_index]
    code = str(item["code"]).strip().upper()

    st.switch_page(
        "page_scripts/etf_detail_page.py",
        query_params=build_detail_query_params(
            code=code,
            source=str(
                ETF_SEARCH_ROUTE.url_path
            ),
            source_query_params=(
                source_state.to_query_params()
            ),
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

    state = replace(
        parse_etf_search_query_state(
            st.query_params
        ),
        bond_label=NON_BOND_LABEL,
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
        ETFSearchQueryState(
            bond_label=NON_BOND_LABEL
        )
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

    with st.form(
        "etf_search_form",
        enter_to_submit=False,
    ):
        (
            keyword_column,
            active_column,
            size_column,
        ) = st.columns([2, 1, 1])

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
                bond_label=NON_BOND_LABEL,
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

    action = render_pagination_controls(
        current_page=state.page,
        total_pages=total_pages,
        previous_key="previous_etf_page",
        next_key="next_etf_page",
    )

    if action == "previous":
        update_search_state(
            replace(
                state,
                page=state.page - 1,
            )
        )
        st.rerun()

    if action == "next":
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

    render_page_title("搜尋&詳細資料")

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

    is_bond = False

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
                "可清除條件或調整關鍵字與"
                "管理方式。"
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
        "點選即可查看詳細資料。"
    )

    render_pagination(
        state=state,
        total_pages=total_pages,
    )
