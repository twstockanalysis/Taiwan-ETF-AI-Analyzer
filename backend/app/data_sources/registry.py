"""ETF 官方資料來源 Registry。"""

from dataclasses import dataclass
from enum import StrEnum


class Market(StrEnum):
    """ETF 掛牌市場。"""

    TWSE = "TWSE"
    TPEX = "TPEX"


class SourceType(StrEnum):
    """資料來源型態。"""

    OPEN_API = "open_api"
    OFFICIAL_WEB_PAGE = "official_web_page"


@dataclass(
    frozen=True,
    slots=True,
)
class DataSource:
    """ETF 資料來源設定。"""

    source_id: str
    display_name: str
    market: Market
    source_type: SourceType
    documentation_url: str
    priority: int
    base_url: str | None = None
    specification_url: str | None = None
    enabled: bool = True
    # 僅供不相容於 Python 3.13 嚴格 X.509
    # 驗證官方來源使用
    allow_legacy_x509: bool = False


DATA_SOURCES: dict[str, DataSource] = {
    "twse_openapi": DataSource(
        source_id="twse_openapi",
        display_name="臺灣證券交易所 OpenAPI",
        market=Market.TWSE,
        source_type=SourceType.OPEN_API,
        documentation_url=(
            "https://openapi.twse.com.tw/"
        ),
        base_url=(
            "https://openapi.twse.com.tw/v1"
        ),
        specification_url=(
            "https://openapi.twse.com.tw/v1/"
            "swagger.json"
        ),
        priority=1,
    ),
    "tpex_openapi": DataSource(
        source_id="tpex_openapi",
        display_name="證券櫃檯買賣中心 OpenAPI",
        market=Market.TPEX,
        source_type=SourceType.OPEN_API,
        documentation_url=(
            "https://www.tpex.org.tw/openapi/"
        ),
        specification_url=(
            "https://www.tpex.org.tw/openapi/"
            "swagger.json"
        ),
        priority=1,
        allow_legacy_x509=True,
    ),
    "twse_etf_products": DataSource(
        source_id="twse_etf_products",
        display_name="證交所 ETF 商品清單",
        market=Market.TWSE,
        source_type=SourceType.OFFICIAL_WEB_PAGE,
        documentation_url=(
            "https://www.twse.com.tw/zh/products/"
            "securities/etf/products/list.html"
        ),
        base_url=(
            "https://www.twse.com.tw/zh/products/"
            "securities/etf/products/list.html"
        ),
        priority=2,
        enabled=False,
    ),
    "tpex_etf_products": DataSource(
        source_id="tpex_etf_products",
        display_name="櫃買中心 ETF 商品資訊",
        market=Market.TPEX,
        source_type=SourceType.OFFICIAL_WEB_PAGE,
        documentation_url=(
            "https://www.tpex.org.tw/zh-tw/"
            "product/etf/overview/categories.html"
        ),
        base_url=(
            "https://www.tpex.org.tw/zh-tw/"
            "product/etf/overview/categories.html"
        ),
        priority=2,
        enabled=False,
    ),
}


def get_data_source(
    source_id: str,
) -> DataSource:
    """依識別碼取得資料來源。

    Args:
        source_id: 資料來源識別碼。

    Returns:
        DataSource: 資料來源設定。

    Raises:
        KeyError: 找不到來源時拋出。
    """

    normalized_source_id = (
        source_id.strip().lower()
    )

    try:
        return DATA_SOURCES[
            normalized_source_id
        ]

    except KeyError as error:
        raise KeyError(
            f"找不到資料來源："
            f"{normalized_source_id}"
        ) from error


def list_enabled_sources() -> list[DataSource]:
    """取得目前啟用的資料來源。

    Returns:
        list[DataSource]: 依優先順序排列的來源。
    """

    enabled_sources = [
        source
        for source in DATA_SOURCES.values()
        if source.enabled
    ]

    return sorted(
        enabled_sources,
        key=lambda source: (
            source.priority,
            source.source_id,
        ),
    )


def list_enabled_openapi_sources(
) -> list[DataSource]:
    """取得目前啟用的 OpenAPI 資料來源。

    Returns:
        list[DataSource]:
            已啟用且具有規格網址的來源。
    """

    return [
        source
        for source in list_enabled_sources()
        if (
            source.source_type
            == SourceType.OPEN_API
            and source.specification_url
        )
    ]