"""Streamlit 導覽與頁面關係定義。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from frontend.query_state import (
    get_query_value,
    normalize_comparison_codes,
    parse_etf_search_query_state,
    parse_performance_query_state,
    query_params_to_dict,
)


NAVIGATION_GROUP = "TW ETF AI Analyzer"


@dataclass(frozen=True)
class PageRoute:
    """單一 Streamlit 頁面的穩定路由契約。"""

    key: str
    title: str
    icon: str
    url_path: str | None = None
    default: bool = False
    hidden: bool = False


HOME_ROUTE = PageRoute(
    key="home",
    title="首頁",
    icon="🏠",
    default=True,
)

ETF_SEARCH_ROUTE = PageRoute(
    key="etf-search",
    title="ETF 查詢",
    icon="🔍",
    url_path="etf-search",
)

PERFORMANCE_RANKING_ROUTE = PageRoute(
    key="performance-ranking",
    title="績效排行榜",
    icon="📈",
    url_path="performance-ranking",
)

ETF_COMPARISON_ROUTE = PageRoute(
    key="etf-comparison",
    title="ETF 比較",
    icon="⚖️",
    url_path="etf-comparison",
)

DIVIDEND_DATA_QUALITY_ROUTE = PageRoute(
    key="dividend-data-quality",
    title="配息資料品質",
    icon="🧪",
    url_path="dividend-data-quality",
)

ETF_DETAIL_ROUTE = PageRoute(
    key="etf-detail",
    title="ETF 詳細資料",
    icon="📄",
    url_path="etf-detail",
    hidden=True,
)

PUBLIC_ROUTES = (
    HOME_ROUTE,
    ETF_SEARCH_ROUTE,
    PERFORMANCE_RANKING_ROUTE,
    ETF_COMPARISON_ROUTE,
    DIVIDEND_DATA_QUALITY_ROUTE,
)

ALL_ROUTES = (
    *PUBLIC_ROUTES,
    ETF_DETAIL_ROUTE,
)

RETURN_ROUTES = {
    ETF_SEARCH_ROUTE.url_path: (
        ETF_SEARCH_ROUTE
    ),
    PERFORMANCE_RANKING_ROUTE.url_path: (
        PERFORMANCE_RANKING_ROUTE
    ),
}


def create_streamlit_page(
    route: PageRoute,
) -> Any:
    """依集中路由定義建立 Streamlit Page。"""

    if route == HOME_ROUTE:
        from frontend.pages.home import (
            render_home,
        )

        source: Any = render_home

    elif route == ETF_SEARCH_ROUTE:
        from frontend.pages.etf_search import (
            render_etf_search,
        )

        source = render_etf_search

    elif route == PERFORMANCE_RANKING_ROUTE:
        from frontend.pages.performance_ranking import (
            render_performance_ranking,
        )

        source = render_performance_ranking

    elif route == ETF_COMPARISON_ROUTE:
        from frontend.pages.etf_comparison import (
            render_etf_comparison,
        )

        source = render_etf_comparison

    elif route == DIVIDEND_DATA_QUALITY_ROUTE:
        from frontend.pages.dividend_data_quality import (
            render_dividend_data_quality,
        )

        source = render_dividend_data_quality

    elif route == ETF_DETAIL_ROUTE:
        source = (
            "page_scripts/"
            "etf_detail_page.py"
        )

    else:
        raise ValueError(
            f"未知頁面路由：{route.key}"
        )

    page_arguments: dict[str, Any] = {
        "title": route.title,
        "icon": route.icon,
    }

    if route.url_path is not None:
        page_arguments["url_path"] = (
            route.url_path
        )

    if route.default:
        page_arguments["default"] = True

    if route.hidden:
        page_arguments["visibility"] = (
            "hidden"
        )

    return st.Page(
        source,
        **page_arguments,
    )


def create_navigation() -> Any:
    """建立網站唯一的 Streamlit 導覽表。"""

    from frontend.ui.theme import (
        apply_global_styles,
    )

    apply_global_styles()

    pages = [
        create_streamlit_page(route)
        for route in ALL_ROUTES
    ]

    return st.navigation(
        {
            NAVIGATION_GROUP: pages,
        }
    )


def normalize_detail_source(
    value: str,
) -> str:
    """正規化 ETF 詳細頁來源；未知來源回 ETF 查詢。"""

    normalized = value.strip().lower()

    return (
        normalized
        if normalized in RETURN_ROUTES
        else str(
            ETF_SEARCH_ROUTE.url_path
        )
    )


def build_detail_query_params(
    *,
    code: str,
    source: str,
    source_query_params: dict[str, str],
) -> dict[str, str]:
    """建立詳細頁網址並保留來源頁查詢條件。"""

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    normalized_source = (
        normalize_detail_source(
            source
        )
    )

    return {
        "code": normalized_code,
        "from": normalized_source,
        **{
            str(key): str(value)
            for key, value in (
                source_query_params.items()
            )
        },
    }


def resolve_detail_return(
    query_params: Any,
) -> tuple[
    PageRoute,
    dict[str, str],
]:
    """解析 ETF 詳細頁應返回的頁面與 URL 狀態。"""

    source = normalize_detail_source(
        get_query_value(
            query_params,
            "from",
            str(
                ETF_SEARCH_ROUTE.url_path
            ),
        )
    )

    route = RETURN_ROUTES[source]

    if route == PERFORMANCE_RANKING_ROUTE:
        return (
            route,
            parse_performance_query_state(
                query_params
            ).to_query_params(),
        )

    return (
        route,
        parse_etf_search_query_state(
            query_params
        ).to_query_params(),
    )

COMPARISON_RETURN_ROUTES = {
    str(ETF_SEARCH_ROUTE.url_path): (
        ETF_SEARCH_ROUTE
    ),
    str(PERFORMANCE_RANKING_ROUTE.url_path): (
        PERFORMANCE_RANKING_ROUTE
    ),
    str(ETF_DETAIL_ROUTE.url_path): (
        ETF_DETAIL_ROUTE
    ),
}


def normalize_comparison_source(
    value: str,
) -> str:
    """正規化 ETF 比較頁來源。"""

    normalized = value.strip().lower()

    return (
        normalized
        if normalized in COMPARISON_RETURN_ROUTES
        else str(
            ETF_SEARCH_ROUTE.url_path
        )
    )


def build_comparison_query_params(
    *,
    codes: list[str] | tuple[str, ...],
    source: str,
    source_query_params: dict[str, str],
) -> dict[str, str]:
    """建立比較頁網址並保存來源頁狀態。"""

    normalized_codes = (
        normalize_comparison_codes(codes)
    )
    normalized_source = (
        normalize_comparison_source(
            source
        )
    )

    params: dict[str, str] = {
        "from": normalized_source,
    }

    if normalized_codes:
        params["codes"] = ",".join(
            normalized_codes
        )

    for key, value in (
        source_query_params.items()
    ):
        normalized_key = str(key).strip()

        if (
            not normalized_key
            or normalized_key.startswith(
                "embed"
            )
        ):
            continue

        params[
            f"return_{normalized_key}"
        ] = str(value)

    return params


def resolve_comparison_return(
    query_params: Any,
) -> tuple[
    PageRoute,
    dict[str, str],
]:
    """解析 ETF 比較頁返回目標與狀態。"""

    source = normalize_comparison_source(
        get_query_value(
            query_params,
            "from",
            str(
                ETF_SEARCH_ROUTE.url_path
            ),
        )
    )

    route = COMPARISON_RETURN_ROUTES[
        source
    ]

    raw_values = query_params_to_dict(
        query_params
    )

    return_params = {
        key.removeprefix(
            "return_"
        ): value
        for key, value in (
            raw_values.items()
        )
        if key.startswith(
            "return_"
        )
    }

    if route == PERFORMANCE_RANKING_ROUTE:
        return (
            route,
            parse_performance_query_state(
                return_params
            ).to_query_params(),
        )

    if route == ETF_DETAIL_ROUTE:
        detail_code = get_query_value(
            return_params,
            "code",
        ).upper()

        if not detail_code:
            return (
                ETF_SEARCH_ROUTE,
                parse_etf_search_query_state(
                    return_params
                ).to_query_params(),
            )

        return (
            route,
            return_params,
        )

    return (
        route,
        parse_etf_search_query_state(
            return_params
        ).to_query_params(),
    )
