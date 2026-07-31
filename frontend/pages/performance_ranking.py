"""ETF 績效排行榜頁面。"""

import math
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_performance_ranking,
)
from frontend.config import (
    get_api_base_url,
)


PERFORMANCE_PERIOD_OPTIONS = (
    "1M",
    "3M",
    "6M",
    "1Y",
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
    "非債券": False,
    "債券": True,
    "全部": None,
}

PAGE_SIZE_OPTIONS = (
    10,
    20,
    50,
    100,
)

PERFORMANCE_STATE_DEFAULTS: dict[
    str,
    object,
] = {
    "performance_period": "6M",
    "performance_active_label": "全部",
    "performance_bond_label": "非債券",
    "performance_page_size": 20,
    "performance_page_number": 1,
}


def initialize_performance_state() -> None:
    """初始化績效排行榜 Session State。"""

    for key, value in (
        PERFORMANCE_STATE_DEFAULTS.items()
    ):
        if key not in st.session_state:
            st.session_state[key] = value


def reset_performance_state() -> None:
    """重設績效排行榜查詢條件。"""

    for key, value in (
        PERFORMANCE_STATE_DEFAULTS.items()
    ):
        st.session_state[key] = value


def format_performance_return(
    value: Any,
) -> str:
    """格式化績效百分比。"""

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "格式異常"

    return f"{number:+.2f}%"


def build_performance_ranking_segments(
    item: dict[str, Any],
) -> tuple[str, ...]:
    """依固定 UX 契約建立排行榜欄位。"""

    rank = int(item["rank"])

    code = str(
        item["etf_code"]
    ).strip().upper()

    period_code = str(
        item["period_code"]
    ).strip().upper()

    return_text = format_performance_return(
        item["return_pct"]
    )

    name = str(
        item["name"]
    ).strip()

    as_of_date = str(
        item["as_of_date"]
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

    return (
        f"**#{rank}　{code}**",
        f"**{period_code} {return_text}**",
        name,
        f"截至 {as_of_date}",
        management_type,
        asset_type,
    )


def format_performance_ranking_row(
    item: dict[str, Any],
) -> str:
    """建立固定欄位順序的可點擊排行榜資料列。"""

    return "　│　".join(
        build_performance_ranking_segments(
            item
        )
    )


def render_clickable_performance_rows(
    items: list[dict[str, Any]],
) -> None:
    """顯示整列可點擊的績效排行榜。"""

    st.caption(
        "排名與代號｜期間報酬率｜ETF 名稱｜"
        "基準日｜管理方式｜資產類型"
    )

    for item in items:
        code = str(
            item["etf_code"]
        ).strip().upper()

        name = str(
            item["name"]
        ).strip()

        st.page_link(
            "page_scripts/etf_detail_page.py",
            label=(
                format_performance_ranking_row(
                    item
                )
            ),
            icon=":material/chevron_right:",
            icon_position="right",
            help=(
                f"查看 {code} {name} 詳細資料"
            ),
            width="stretch",
            query_params={
                "code": code,
            },
        )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_performance_ranking(
    api_base_url: str,
    period: str,
    is_active: bool | None,
    is_bond: bool | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """取得並短暫快取績效排行榜。"""

    return fetch_performance_ranking(
        api_base_url=api_base_url,
        period=period,
        metric="PRICE_RETURN",
        is_active=is_active,
        is_bond=is_bond,
        limit=limit,
        offset=offset,
    )


def render_performance_filter_form() -> None:
    """顯示績效排行榜篩選表單。"""

    active_labels = list(
        ACTIVE_FILTER_OPTIONS
    )

    bond_labels = list(
        BOND_FILTER_OPTIONS
    )

    with st.form(
        "performance_ranking_form"
    ):
        period_column, active_column = (
            st.columns(2)
        )

        with period_column:
            current_period = str(
                st.session_state[
                    "performance_period"
                ]
            )

            period = st.selectbox(
                "績效期間",
                options=(
                    PERFORMANCE_PERIOD_OPTIONS
                ),
                index=(
                    PERFORMANCE_PERIOD_OPTIONS
                    .index(current_period)
                ),
            )

        with active_column:
            current_active_label = str(
                st.session_state[
                    "performance_active_label"
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
                    "performance_bond_label"
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
                    "performance_page_size"
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

        submitted = st.form_submit_button(
            "套用篩選",
            type="primary",
        )

    if submitted:
        st.session_state[
            "performance_period"
        ] = period

        st.session_state[
            "performance_active_label"
        ] = active_label

        st.session_state[
            "performance_bond_label"
        ] = bond_label

        st.session_state[
            "performance_page_size"
        ] = page_size

        st.session_state[
            "performance_page_number"
        ] = 1

        load_performance_ranking.clear()

        st.rerun()


def render_performance_action_buttons() -> None:
    """顯示重設與重新載入按鈕。"""

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
            key="clear_performance_filters",
        )

    with refresh_column:
        refresh_clicked = st.button(
            "重新載入",
            key="refresh_performance_data",
        )

    if clear_clicked:
        reset_performance_state()
        load_performance_ranking.clear()
        st.rerun()

    if refresh_clicked:
        load_performance_ranking.clear()
        st.rerun()


def render_performance_pagination(
    current_page: int,
    total_pages: int,
) -> None:
    """顯示績效排行榜分頁控制項。"""

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
            key="previous_performance_page",
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
            key="next_performance_page",
        )

    if previous_clicked:
        st.session_state[
            "performance_page_number"
        ] = current_page - 1

        st.rerun()

    if next_clicked:
        st.session_state[
            "performance_page_number"
        ] = current_page + 1

        st.rerun()


def render_performance_ranking() -> None:
    """顯示 ETF 績效排行榜。"""

    initialize_performance_state()

    st.title("ETF 績效排行榜")

    st.caption(
        "依指定期間比較 ETF 市價報酬率"
    )

    st.info(
        "目前為市價報酬率，"
        "不包含配息再投資。"
    )

    render_performance_filter_form()
    render_performance_action_buttons()

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        st.error(str(error))
        return

    period = str(
        st.session_state[
            "performance_period"
        ]
    )

    active_label = str(
        st.session_state[
            "performance_active_label"
        ]
    )

    bond_label = str(
        st.session_state[
            "performance_bond_label"
        ]
    )

    page_size = int(
        st.session_state[
            "performance_page_size"
        ]
    )

    current_page = int(
        st.session_state[
            "performance_page_number"
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
            "正在讀取績效排行榜..."
        ):
            result = load_performance_ranking(
                api_base_url=api_base_url,
                period=period,
                is_active=is_active,
                is_bond=is_bond,
                limit=page_size,
                offset=offset,
            )

    except APIClientError as error:
        st.error(
            "無法取得 ETF 績效排行榜。"
        )

        st.code(
            str(error),
            language=None,
        )

        st.info(
            "請確認 FastAPI 已在 "
            "127.0.0.1:8000 啟動，"
            "且已匯入績效資料。"
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
            "performance_page_number"
        ] = total_pages

        st.rerun()

    period_column, total_column, page_column = (
        st.columns(3)
    )

    with period_column:
        st.metric(
            "績效期間",
            period,
        )

    with total_column:
        st.metric(
            "排行榜 ETF",
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

    st.divider()

    if not items:
        st.info(
            "目前沒有符合條件的績效資料。"
        )
        return

    render_clickable_performance_rows(
        items
    )

    st.caption(
        f"目前顯示第 "
        f"{offset + 1:,} 至 "
        f"{offset + len(items):,} 名，"
        f"共 {total:,} 檔"
    )

    st.caption(
        "排行榜只比較相同期間，"
        "不會混合不同期間的報酬率。"
    )

    render_performance_pagination(
        current_page=current_page,
        total_pages=total_pages,
    )
