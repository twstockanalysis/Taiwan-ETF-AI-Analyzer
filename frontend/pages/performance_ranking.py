"""ETF 績效排行榜頁面。"""

from dataclasses import replace
import math
from typing import Any

import streamlit as st

from frontend.api_client import (
    APIClientError,
    fetch_multi_period_performance_ranking,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    ETF_COMPARISON_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    build_comparison_query_params,
    build_detail_query_params,
    create_streamlit_page,
)
from frontend.query_state import (
    PAGE_SIZE_OPTIONS,
    PERFORMANCE_PERIODS,
    PerformanceQueryState,
    parse_performance_query_state,
    sync_query_params,
)
from frontend.ui.components import (
    render_etf_detail_links,
    render_pagination_controls,
)
from frontend.ui.formatters import (
    asset_type_label,
    format_etf_display_name,
    format_percentage,
    management_type_label,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
    render_empty_state,
)


PERFORMANCE_PERIOD_OPTIONS = (
    PERFORMANCE_PERIODS
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

PERFORMANCE_QUERY_SIGNATURE_KEY = (
    "_performance_query_signature"
)


def format_performance_return(
    value: Any,
) -> str:
    """格式化績效百分比。"""

    return format_percentage(
        value,
        signed=True,
        missing_text="格式異常",
        invalid_text="格式異常",
    )


def build_period_performance_lookup(
    item: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """建立排行榜項目的期間績效查找表。"""

    performance_items = item.get(
        "performance_items"
    )

    if isinstance(
        performance_items,
        list,
    ):
        return {
            str(
                performance_item[
                    "period_code"
                ]
            ).strip().upper(): (
                performance_item
            )
            for performance_item in (
                performance_items
            )
        }

    period_code = str(
        item.get(
            "period_code",
            item.get(
                "sort_period",
                "",
            ),
        )
    ).strip().upper()

    if not period_code:
        return {}

    return {
        period_code: {
            "period_code": period_code,
            "as_of_date": item.get(
                "as_of_date",
                item.get(
                    "sort_as_of_date"
                ),
            ),
            "return_pct": item.get(
                "return_pct",
                item.get(
                    "sort_return_pct"
                ),
            ),
            "source_id": item.get(
                "source_id"
            ),
        }
    }


def format_ranking_period(
    *,
    period_code: str,
    performance_item: (
        dict[str, Any] | None
    ),
    is_sort_period: bool,
) -> str:
    """格式化排行榜單一期間並強調排序期間。"""

    if performance_item is None:
        text = (
            f"{period_code} "
            "歷史資料不足"
        )

    else:
        text = (
            f"{period_code} "
            + format_performance_return(
                performance_item[
                    "return_pct"
                ]
            )
        )

    return (
        f"**{text}**"
        if is_sort_period
        else text
    )


def build_performance_ranking_segments(
    item: dict[str, Any],
) -> tuple[str, ...]:
    """建立只顯示目前排序期間的排行榜欄位。"""

    rank = int(item["rank"])

    code = str(
        item["etf_code"]
    ).strip().upper()

    name = format_etf_display_name(
        item["name"]
    )

    sort_period = str(
        item.get(
            "sort_period",
            item.get(
                "period_code",
                "6M",
            ),
        )
    ).strip().upper()

    sort_as_of_date = str(
        item.get(
            "sort_as_of_date",
            item.get(
                "as_of_date",
                "",
            ),
        )
    ).strip()

    performance_lookup = (
        build_period_performance_lookup(
            item
        )
    )

    selected_period_segment = (
        format_ranking_period(
            period_code=sort_period,
            performance_item=(
                performance_lookup.get(
                    sort_period
                )
            ),
            is_sort_period=True,
        )
    )

    management_type = (
        management_type_label(
            item["is_active"]
        )
    )

    asset_type = asset_type_label(
        item["is_bond"]
    )

    return (
        f"**#{rank}　{code}**",
        name,
        selected_period_segment,
        f"截至 {sort_as_of_date}",
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
    query_state: PerformanceQueryState | None = None,
) -> None:
    """顯示整列可點擊的績效排行榜。"""

    source_state = (
        query_state
        if query_state is not None
        else PerformanceQueryState()
    )

    render_etf_detail_links(
        items,
        caption=(
            "排名與代號｜ETF 名稱｜"
            f"{source_state.period} 報酬率｜"
            "排序基準日｜管理方式｜資產類型"
        ),
        label_builder=(
            format_performance_ranking_row
        ),
        code_field="etf_code",
        name_field="name",
        source=str(
            PERFORMANCE_RANKING_ROUTE.url_path
        ),
        source_query_params=(
            source_state.to_query_params()
        ),
    )


def apply_performance_state(
    state: PerformanceQueryState,
) -> None:
    """將 URL 狀態套用至 Session State。"""

    st.session_state[
        "performance_period"
    ] = state.period

    st.session_state[
        "performance_active_label"
    ] = state.active_label

    st.session_state[
        "performance_bond_label"
    ] = state.bond_label

    st.session_state[
        "performance_page_size"
    ] = state.page_size

    st.session_state[
        "performance_page_number"
    ] = state.page

    st.session_state[
        PERFORMANCE_QUERY_SIGNATURE_KEY
    ] = tuple(
        sorted(
            state.to_query_params().items()
        )
    )


def get_performance_state() -> PerformanceQueryState:
    """由 Session State 建立目前排行榜狀態。"""

    return PerformanceQueryState(
        period=str(
            st.session_state[
                "performance_period"
            ]
        ),
        active_label=str(
            st.session_state[
                "performance_active_label"
            ]
        ),
        bond_label=str(
            st.session_state[
                "performance_bond_label"
            ]
        ),
        page=int(
            st.session_state[
                "performance_page_number"
            ]
        ),
        page_size=int(
            st.session_state[
                "performance_page_size"
            ]
        ),
    )


def initialize_performance_state() -> None:
    """由 URL 初始化或更新績效排行榜狀態。"""

    state = parse_performance_query_state(
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
            PERFORMANCE_QUERY_SIGNATURE_KEY
        )
        != signature
    ):
        apply_performance_state(state)


def update_performance_state(
    state: PerformanceQueryState,
) -> None:
    """同步排行榜 Session State 與網址。"""

    apply_performance_state(state)

    sync_query_params(
        st.query_params,
        state.to_query_params(),
    )


def reset_performance_state() -> None:
    """重設績效排行榜查詢條件。"""

    update_performance_state(
        PerformanceQueryState()
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

    return (
        fetch_multi_period_performance_ranking(
            api_base_url=api_base_url,
            sort_period=period,
            metric="PRICE_RETURN",
            is_active=is_active,
            is_bond=is_bond,
            limit=limit,
            offset=offset,
        )
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
        "performance_ranking_form",
        enter_to_submit=False,
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
                "排序期間",
                options=(
                    PERFORMANCE_PERIOD_OPTIONS
                ),
                index=(
                    PERFORMANCE_PERIOD_OPTIONS
                    .index(current_period)
                ),
                help=(
                    "預設以 6M 排名；"
                    "排行榜每列只顯示"
                    "目前選取期間。"
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
        update_performance_state(
            PerformanceQueryState(
                period=period,
                active_label=active_label,
                bond_label=bond_label,
                page=1,
                page_size=page_size,
            )
        )

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
    state: PerformanceQueryState,
    total_pages: int,
) -> None:
    """顯示績效排行榜分頁控制項。"""

    action = render_pagination_controls(
        current_page=state.page,
        total_pages=total_pages,
        previous_key=(
            "previous_performance_page"
        ),
        next_key=(
            "next_performance_page"
        ),
    )

    if action == "previous":
        update_performance_state(
            replace(
                state,
                page=state.page - 1,
            )
        )
        st.rerun()

    if action == "next":
        update_performance_state(
            replace(
                state,
                page=state.page + 1,
            )
        )
        st.rerun()


def render_performance_ranking() -> None:
    """顯示 ETF 績效排行榜。"""

    initialize_performance_state()

    st.title("ETF 績效排行榜")

    st.caption(
        "依指定期間排序並只顯示該期間；"
        "預設為 6M。"
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
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    state = get_performance_state()

    st.page_link(
        create_streamlit_page(
            ETF_COMPARISON_ROUTE
        ),
        label="開啟 ETF 比較",
        icon="⚖️",
        query_params=(
            build_comparison_query_params(
                codes=(),
                source=str(
                    PERFORMANCE_RANKING_ROUTE.url_path
                ),
                source_query_params=(
                    state.to_query_params()
                ),
            )
        ),
    )

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
            "正在讀取績效排行榜..."
        ):
            result = load_performance_ranking(
                api_base_url=api_base_url,
                period=state.period,
                is_active=is_active,
                is_bond=is_bond,
                limit=state.page_size,
                offset=offset,
            )

    except APIClientError as error:
        render_api_error(
            "無法取得 ETF 績效排行榜。",
            error,
            hint=(
                "請確認 FastAPI 已啟動，"
                "且已匯入績效資料。"
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
        update_performance_state(
            replace(
                state,
                page=total_pages,
            )
        )
        st.rerun()

    period_column, total_column, page_column = (
        st.columns(3)
    )

    with period_column:
        st.metric(
            "排序期間",
            state.period,
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
                f"{state.page}"
                f" / {total_pages}"
            ),
        )

    st.divider()

    if not items:
        render_empty_state(
            "目前沒有符合條件的績效資料。",
            hint=(
                "可清除條件或改用其他績效期間、"
                "管理方式與資產類型。"
            ),
        )
        return

    render_clickable_performance_rows(
        items,
        query_state=state,
    )

    st.caption(
        f"目前顯示第 "
        f"{offset + 1:,} 至 "
        f"{offset + len(items):,} 名，"
        f"共 {total:,} 檔"
    )

    st.caption(
        f"名次與每列報酬率均依 "
        f"{state.period}；"
        "其他期間可從排序期間切換查看。"
    )

    render_performance_pagination(
        state=state,
        total_pages=total_pages,
    )
