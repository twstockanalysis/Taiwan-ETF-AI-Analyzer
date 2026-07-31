"""Streamlit URL Query State 正規化工具。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PAGE_SIZE_OPTIONS = (
    10,
    20,
    50,
    100,
)

ACTIVE_TOKEN_TO_LABEL = {
    "all": "全部",
    "active": "主動式",
    "passive": "被動式",
}

ACTIVE_LABEL_TO_TOKEN = {
    label: token
    for token, label in ACTIVE_TOKEN_TO_LABEL.items()
}

BOND_TOKEN_TO_LABEL = {
    "all": "全部",
    "non-bond": "非債券",
    "bond": "債券",
}

BOND_LABEL_TO_TOKEN = {
    label: token
    for token, label in BOND_TOKEN_TO_LABEL.items()
}

PERFORMANCE_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)


def get_query_value(
    query_params: Any,
    key: str,
    default: str = "",
) -> str:
    """取得單一 Query Parameter；重複鍵採最後一值。"""

    raw_value = query_params.get(
        key,
        default,
    )

    if isinstance(raw_value, list):
        raw_value = (
            raw_value[-1]
            if raw_value
            else default
        )

    return str(raw_value).strip()


def _normalize_positive_integer(
    value: str,
    *,
    default: int,
) -> int:
    """將文字正規化為正整數。"""

    try:
        normalized = int(value)

    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        normalized
        if normalized >= 1
        else default
    )


def _normalize_page_size(
    value: str,
    *,
    default: int,
) -> int:
    """只接受前端支援的每頁筆數。"""

    normalized = _normalize_positive_integer(
        value,
        default=default,
    )

    return (
        normalized
        if normalized in PAGE_SIZE_OPTIONS
        else default
    )


def _normalize_label(
    value: str,
    *,
    mapping: dict[str, str],
    default_token: str,
) -> str:
    """將 URL Token 轉成合法顯示標籤。"""

    normalized_token = value.strip().lower()

    return mapping.get(
        normalized_token,
        mapping[default_token],
    )


@dataclass(frozen=True)
class ETFSearchQueryState:
    """ETF 查詢頁可分享的 URL 狀態。"""

    keyword: str = ""
    active_label: str = "全部"
    bond_label: str = "全部"
    page: int = 1
    page_size: int = 20

    def to_query_params(
        self,
    ) -> dict[str, str]:
        """轉成標準 Query Parameters。"""

        params = {
            "active": ACTIVE_LABEL_TO_TOKEN.get(
                self.active_label,
                "all",
            ),
            "bond": BOND_LABEL_TO_TOKEN.get(
                self.bond_label,
                "all",
            ),
            "page": str(
                max(1, int(self.page))
            ),
            "page_size": str(
                self.page_size
                if self.page_size in PAGE_SIZE_OPTIONS
                else 20
            ),
        }

        normalized_keyword = (
            self.keyword.strip()
        )

        if normalized_keyword:
            params["keyword"] = (
                normalized_keyword
            )

        return params


@dataclass(frozen=True)
class PerformanceQueryState:
    """績效排行榜可分享的 URL 狀態。"""

    period: str = "6M"
    active_label: str = "全部"
    bond_label: str = "非債券"
    page: int = 1
    page_size: int = 20

    def to_query_params(
        self,
    ) -> dict[str, str]:
        """轉成標準 Query Parameters。"""

        normalized_period = (
            self.period.strip().upper()
        )

        if normalized_period not in PERFORMANCE_PERIODS:
            normalized_period = "6M"

        return {
            "period": normalized_period,
            "active": ACTIVE_LABEL_TO_TOKEN.get(
                self.active_label,
                "all",
            ),
            "bond": BOND_LABEL_TO_TOKEN.get(
                self.bond_label,
                "non-bond",
            ),
            "page": str(
                max(1, int(self.page))
            ),
            "page_size": str(
                self.page_size
                if self.page_size in PAGE_SIZE_OPTIONS
                else 20
            ),
        }


def parse_etf_search_query_state(
    query_params: Any,
) -> ETFSearchQueryState:
    """由網址建立 ETF 查詢頁狀態。"""

    return ETFSearchQueryState(
        keyword=get_query_value(
            query_params,
            "keyword",
        ),
        active_label=_normalize_label(
            get_query_value(
                query_params,
                "active",
                "all",
            ),
            mapping=ACTIVE_TOKEN_TO_LABEL,
            default_token="all",
        ),
        bond_label=_normalize_label(
            get_query_value(
                query_params,
                "bond",
                "all",
            ),
            mapping=BOND_TOKEN_TO_LABEL,
            default_token="all",
        ),
        page=_normalize_positive_integer(
            get_query_value(
                query_params,
                "page",
                "1",
            ),
            default=1,
        ),
        page_size=_normalize_page_size(
            get_query_value(
                query_params,
                "page_size",
                "20",
            ),
            default=20,
        ),
    )


def parse_performance_query_state(
    query_params: Any,
) -> PerformanceQueryState:
    """由網址建立績效排行榜狀態。"""

    period = get_query_value(
        query_params,
        "period",
        "6M",
    ).upper()

    if period not in PERFORMANCE_PERIODS:
        period = "6M"

    return PerformanceQueryState(
        period=period,
        active_label=_normalize_label(
            get_query_value(
                query_params,
                "active",
                "all",
            ),
            mapping=ACTIVE_TOKEN_TO_LABEL,
            default_token="all",
        ),
        bond_label=_normalize_label(
            get_query_value(
                query_params,
                "bond",
                "non-bond",
            ),
            mapping=BOND_TOKEN_TO_LABEL,
            default_token="non-bond",
        ),
        page=_normalize_positive_integer(
            get_query_value(
                query_params,
                "page",
                "1",
            ),
            default=1,
        ),
        page_size=_normalize_page_size(
            get_query_value(
                query_params,
                "page_size",
                "20",
            ),
            default=20,
        ),
    )


def query_params_to_dict(
    query_params: Any,
) -> dict[str, str]:
    """將 Query Parameters 轉成一般字典。"""

    if hasattr(
        query_params,
        "to_dict",
    ):
        raw_values = (
            query_params.to_dict()
        )

        return {
            str(key): str(value)
            for key, value in raw_values.items()
            if not str(key).startswith(
                "embed"
            )
        }

    try:
        keys = list(
            query_params.keys()
        )

    except AttributeError:
        keys = list(query_params)

    return {
        str(key): get_query_value(
            query_params,
            str(key),
        )
        for key in keys
        if not str(key).startswith(
            "embed"
        )
    }


def sync_query_params(
    query_params: Any,
    expected: dict[str, str],
) -> bool:
    """以標準狀態取代網址參數；相同時不重寫。"""

    normalized_expected = {
        str(key): str(value)
        for key, value in expected.items()
    }

    current = query_params_to_dict(
        query_params
    )

    if current == normalized_expected:
        return False

    if hasattr(
        query_params,
        "from_dict",
    ):
        query_params.from_dict(
            normalized_expected
        )

    else:
        query_params.clear()

        for key, value in (
            normalized_expected.items()
        ):
            query_params[key] = value

    return True
