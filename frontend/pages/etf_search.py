"""ETF 搜尋、篩選及分頁頁面。"""

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


PAGE_SIZE_OPTIONS = (
    10,
    20,
    50,
    100,
)


SEARCH_STATE_DEFAULTS: dict[
    str,
    object,
] = {
    "etf_search_keyword": "",
    "etf_search_active_label": "全部",
    "etf_search_bond_label": "全部",
    "etf_search_page_size": 20,
    "etf_search_page_number": 1,
}


def initialize_search_state() -> None:
    """初始化 ETF 搜尋頁 Session State。"""

    for key, value in (
        SEARCH_STATE_DEFAULTS.items()
    ):
        if key not in st.session_state:
            st.session_state[key] = value


def reset_search_state() -> None:
    """清除所有 ETF 搜尋條件。"""

    for key, value in (
        SEARCH_STATE_DEFAULTS.items()
    ):
        st.session_state[key] = value


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


def open_etf_detail(
    code: str,
) -> None:
    """前往 ETF 詳細資料頁。

    Args:
        code:
            ETF 證券代號。
    """

    detail_page = st.Page(
        "page_scripts/etf_detail_page.py",
        title="ETF 詳細資料",
        icon="📄",
        url_path="etf-detail",
        visibility="hidden",
    )

    st.switch_page(
        detail_page,
        query_params={
            "code": code,
        },
    )


def format_etf_rows(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """將 ETF API 資料轉成畫面欄位。

    Args:
        items:
            ETF API 資料。

    Returns:
        list[dict[str, Any]]:
            適合表格顯示的 ETF 資料。
    """

    display_rows: list[
        dict[str, Any]
    ] = []

    for item in items:
        display_rows.append(
            {
                "代號": item["code"],
                "ETF 名稱": item["name"],
                "管理方式": (
                    "主動式"
                    if item["is_active"]
                    else "被動式"
                ),
                "資產類型": (
                    "債券"
                    if item["is_bond"]
                    else "非債券"
                ),
                "上市日期": (
                    item["listing_date"]
                    or "—"
                ),
                "基金規模（億元）": (
                    item["fund_size"]
                ),
                "費用率（%）": (
                    item["expense_ratio"]
                ),
            }
        )

    return display_rows


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
        st.session_state[
            "etf_search_keyword"
        ] = keyword.strip()

        st.session_state[
            "etf_search_active_label"
        ] = active_label

        st.session_state[
            "etf_search_bond_label"
        ] = bond_label

        st.session_state[
            "etf_search_page_size"
        ] = page_size

        st.session_state[
            "etf_search_page_number"
        ] = 1

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
    current_page: int,
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
                current_page <= 1
            ),
            key="previous_etf_page",
        )

    with page_column:
        st.write(
            f"第 {current_page} 頁，"
            f"共 {total_pages} 頁"
        )

    with next_column:
        next_clicked = st.button(
            "下一頁 →",
            disabled=(
                current_page
                >= total_pages
            ),
            key="next_etf_page",
        )

    if previous_clicked:
        st.session_state[
            "etf_search_page_number"
        ] = current_page - 1

        st.rerun()

    if next_clicked:
        st.session_state[
            "etf_search_page_number"
        ] = current_page + 1

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
        st.error(str(error))
        return

    keyword = str(
        st.session_state[
            "etf_search_keyword"
        ]
    )

    active_label = str(
        st.session_state[
            "etf_search_active_label"
        ]
    )

    bond_label = str(
        st.session_state[
            "etf_search_bond_label"
        ]
    )

    page_size = int(
        st.session_state[
            "etf_search_page_size"
        ]
    )

    current_page = int(
        st.session_state[
            "etf_search_page_number"
        ]
    )

    is_active = ACTIVE_FILTER_OPTIONS[
        active_label
    ]

    is_bond = BOND_FILTER_OPTIONS[
        bond_label
    ]

    offset = (
        current_page - 1
    ) * page_size

    try:
        with st.spinner(
            "正在讀取 ETF 資料..."
        ):
            result = load_etf_page(
                api_base_url=api_base_url,
                keyword=(
                    keyword
                    if keyword
                    else None
                ),
                is_active=is_active,
                is_bond=is_bond,
                limit=page_size,
                offset=offset,
            )

    except APIClientError as error:
        st.error(
            "無法取得 ETF 資料。"
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

    total = int(result["total"])
    items = result["items"]

    total_pages = max(
        1,
        math.ceil(
            total / page_size
        ),
    )

    if current_page > total_pages:
        st.session_state[
            "etf_search_page_number"
        ] = total_pages

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
                f"{current_page}"
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
        st.info(
            "目前沒有符合條件的 ETF。"
        )
        return

    display_rows = format_etf_rows(
        items
    )

    table_key = (
        "etf_search_results::"
        f"{keyword}::"
        f"{active_label}::"
        f"{bond_label}::"
        f"{page_size}::"
        f"{current_page}"
    )

    selection_event = st.dataframe(
        display_rows,
        hide_index=True,
        width="stretch",
        key=table_key,
        on_select="rerun",
        selection_mode="single-row",
    )

    st.caption(
        f"目前顯示第 "
        f"{offset + 1:,} 至 "
        f"{offset + len(items):,} 筆，"
        f"共 {total:,} 筆"
    )

    selected_rows = list(
        selection_event.selection.rows
    )

    if selected_rows:
        selected_index = (
            selected_rows[0]
        )

        if selected_index < len(items):
            selected_item = items[
                selected_index
            ]

            selected_code = str(
                selected_item["code"]
            )

            selected_name = str(
                selected_item["name"]
            )

            st.info(
                f"已選擇："
                f"{selected_code} "
                f"{selected_name}"
            )

            if st.button(
                "查看 ETF 詳細資料",
                type="primary",
                key=(
                    "open_etf_detail_"
                    f"{selected_code}"
                ),
            ):
                open_etf_detail(
                    selected_code
                )

    else:
        st.caption(
            "選取表格中的一列，"
            "即可查看 ETF 詳細資料。"
        )

    render_pagination(
        current_page=current_page,
        total_pages=total_pages,
    )