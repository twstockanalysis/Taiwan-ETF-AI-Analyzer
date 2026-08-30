"""ETF 績效排行榜頁面。"""

from html import escape, unescape
from typing import Any
from urllib.parse import urlencode

import streamlit as st

from frontend.ui.components import render_page_title

from frontend.api_client import (
    APIClientError,
    fetch_multi_period_performance_ranking,
)
from frontend.config import (
    get_api_base_url,
)
from frontend.navigation import (
    ETF_DETAIL_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    build_detail_query_params,
)
from frontend.query_state import (
    PERFORMANCE_PERIODS,
    PerformanceQueryState,
    parse_performance_query_state,
    sync_query_params,
)
from frontend.ui.formatters import (
    format_etf_display_name,
    format_percentage,
    management_type_label,
)
from frontend.ui.states import (
    loading_state,
    render_api_error,
    render_empty_state,
)
from frontend.ui.quality_grade import (
    load_historical_quality_grade_lookup,
    quality_grade_short_label,
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

NON_BOND_LABEL = "非債券"
RANKING_LIMIT = 20
RANKING_ACTION_KEY = (
    "performance_ranking_detail_action"
)

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

    return (
        f"**#{rank}　{code}**",
        name,
        selected_period_segment,
        f"截至 {sort_as_of_date}",
        management_type,
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
    grade_lookup: dict[str, dict[str, Any]] | None = None,
) -> None:
    """以整列可點擊的固定欄位表格顯示績效排行榜。"""

    source_state = (
        query_state
        if query_state is not None
        else PerformanceQueryState(
            bond_label=NON_BOND_LABEL,
            page=1,
            page_size=RANKING_LIMIT,
        )
    )

    st.html(
        build_performance_table_html(
            items,
            source_state,
            grade_lookup=grade_lookup,
        ),
        width="stretch",
    )


def html_text(value: object) -> str:
    """將外部文字正規化後安全放入 HTML。"""

    return escape(
        unescape(str(value)),
        quote=True,
    )


def build_performance_table_html(
    items: list[dict[str, Any]],
    source_state: PerformanceQueryState,
    *,
    grade_lookup: dict[str, dict[str, Any]] | None = None,
) -> str:
    """建立無選取欄、整列可開啟詳細資料的排行榜。"""

    header_values = (
        "排名",
        "代號",
        "名稱",
        f"{source_state.period} 報酬率",
        "喵喵評等",
        "資料日期",
        "管理方式",
    )
    header_cells = "".join(
        (
            '<span class="performance-ranking-cell" '
            f'role="columnheader">{html_text(label)}</span>'
        )
        for label in header_values
    )

    row_html: list[str] = []
    for item in items:
        code = str(item["etf_code"]).strip().upper()
        row = build_performance_table_row(
            item,
            (grade_lookup or {}).get(code),
        )
        query = urlencode(
            build_detail_query_params(
                code=code,
                source=str(PERFORMANCE_RANKING_ROUTE.url_path),
                source_query_params=source_state.to_query_params(),
            )
        )
        href = f"/{ETF_DETAIL_ROUTE.url_path}?{query}"
        cell_values = (
            row["rank"],
            row["code"],
            row["name"],
            row["period_return"],
            row["historical_quality"],
            row["as_of_date"],
            row["management_type"],
        )
        cells = "".join(
            (
                '<span class="performance-ranking-cell" '
                f'role="cell">{html_text(value)}</span>'
            )
            for value in cell_values
        )
        row_html.append(
            (
                '<a class="performance-ranking-row" '
                f'href="{html_text(href)}" role="row" '
                f'aria-label="查看 {html_text(code)} '
                f'{html_text(row["name"])} 詳細資料">'
                f"{cells}</a>"
            )
        )

    return (
        '<div class="performance-ranking-scroll">'
        '<div class="performance-ranking-grid" role="table" '
        'aria-label="ETF 績效排行榜">'
        '<div class="performance-ranking-header" role="row">'
        f"{header_cells}</div>"
        f"{''.join(row_html)}"
        "</div></div>"
    )


def build_performance_table_row(
    item: dict[str, Any],
    grade_payload: object = None,
) -> dict[str, str]:
    """建立單一排行榜資料表列。"""

    rank = int(item["rank"])
    code = str(item["etf_code"]).strip().upper()
    name = format_etf_display_name(item["name"])
    sort_period = str(
        item.get(
            "sort_period",
            item.get("period_code", "6M"),
        )
    ).strip().upper()
    performance_item = (
        build_period_performance_lookup(item).get(
            sort_period
        )
    )
    period_return = (
        format_performance_return(
            performance_item["return_pct"]
        )
        if performance_item is not None
        else "歷史資料不足"
    )
    as_of_date = str(
        item.get(
            "sort_as_of_date",
            item.get("as_of_date", ""),
        )
    ).strip()

    return {
        "rank": f"#{rank}",
        "code": code,
        "name": name,
        "period_return": period_return,
        "historical_quality": quality_grade_short_label(
            grade_payload
        ),
        "as_of_date": as_of_date or "—",
        "management_type": management_type_label(
            item["is_active"]
        ),
    }


def open_performance_detail(
    items: list[dict[str, Any]],
    source_state: PerformanceQueryState,
    *,
    row_index: int | None = None,
) -> None:
    """由排行榜資料表開啟所選 ETF 詳細資料。"""

    if row_index is None:
        action = st.session_state.get(
            RANKING_ACTION_KEY
        )

        if action is None:
            return

        selected_rows = action.get(
            "selection",
            {},
        ).get("rows", [])
        if selected_rows:
            row_index = int(selected_rows[0])
        elif "row" in action:
            row_index = int(action["row"])
        else:
            return

    if not 0 <= row_index < len(items):
        return

    code = str(
        items[row_index]["etf_code"]
    ).strip().upper()

    st.switch_page(
        "page_scripts/etf_detail_page.py",
        query_params=build_detail_query_params(
            code=code,
            source=str(
                PERFORMANCE_RANKING_ROUTE.url_path
            ),
            source_query_params=(
                source_state.to_query_params()
            ),
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

    state = replace_performance_defaults(
        parse_performance_query_state(
            st.query_params
        )
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
        replace_performance_defaults(
            PerformanceQueryState()
        )
    )


def replace_performance_defaults(
    state: PerformanceQueryState,
) -> PerformanceQueryState:
    """固定排行榜為非債券前 20 名且不分頁。"""

    return PerformanceQueryState(
        period=state.period,
        active_label=state.active_label,
        bond_label=NON_BOND_LABEL,
        page=1,
        page_size=RANKING_LIMIT,
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

        submitted = st.form_submit_button(
            "篩選",
            type="primary",
        )

        with st.container(
            key="performance-ranking-secondary-actions",
            horizontal=True,
            gap="small",
        ):
            clear_clicked = st.form_submit_button(
                "清除條件"
            )
            refresh_clicked = st.form_submit_button(
                "重新載入"
            )

    if clear_clicked:
        reset_performance_state()
        load_performance_ranking.clear()
        st.rerun()

    if refresh_clicked:
        load_performance_ranking.clear()
        load_historical_quality_grade_lookup.clear()
        st.rerun()

    if submitted:
        update_performance_state(
            PerformanceQueryState(
                period=period,
                active_label=active_label,
                bond_label=NON_BOND_LABEL,
                page=1,
                page_size=RANKING_LIMIT,
            )
        )

        load_performance_ranking.clear()
        st.rerun()
def render_performance_ranking() -> None:
    """顯示 ETF 績效排行榜。"""

    initialize_performance_state()

    render_page_title("績效排行榜")

    st.caption("預設為6M")

    render_performance_filter_form()

    try:
        api_base_url = get_api_base_url()

    except ValueError as error:
        render_api_error(
            "前端 API 網址設定不正確。",
            error,
        )
        return

    state = get_performance_state()

    is_active = ACTIVE_FILTER_OPTIONS[
        state.active_label
    ]

    is_bond = False

    try:
        with loading_state(
            "正在讀取績效排行榜..."
        ):
            result = load_performance_ranking(
                api_base_url=api_base_url,
                period=state.period,
                is_active=is_active,
                is_bond=is_bond,
                limit=RANKING_LIMIT,
                offset=0,
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

    items = result["items"]

    with st.container(gap=None, key="performance-ranking-period-summary"):
        st.metric(
            "排序期間",
            state.period,
        )
        with st.container(key="performance-ranking-limit"):
            st.markdown("前20名")
        st.divider()

    if not items:
        render_empty_state(
            "目前沒有符合條件的績效資料。",
            hint=(
                "可清除條件或改用其他績效期間與"
                "管理方式。"
            ),
        )
        return

    grade_lookup: dict[str, dict[str, Any]] = {}
    grade_error = False
    try:
        grade_lookup = load_historical_quality_grade_lookup(
            api_base_url,
            tuple(str(item["etf_code"]) for item in items),
        )
    except (APIClientError, ValueError):
        grade_error = True

    render_clickable_performance_rows(
        items,
        query_state=state,
        grade_lookup=grade_lookup,
    )

    if grade_error:
        st.caption(
            "喵喵評等暫時無法取得；"
            "排行榜仍依所選期間正常排序。"
        )

    st.caption(
        f"名次與每列報酬率均依 "
        f"{state.period}；"
        "其他期間可從排序期間切換查看。"
    )
