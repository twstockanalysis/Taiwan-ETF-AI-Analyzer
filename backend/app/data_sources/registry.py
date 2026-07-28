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
    base_url: str
    documentation_url: str
    priority: int
    enabled: bool = True


DATA_SOURCES: dict[str, DataSource] = {
    "twse_openapi": DataSource(
        source_id="twse_openapi",
        display_name="臺灣證券交易所 OpenAPI",
        market=Market.TWSE,
        source_type=SourceType.OPEN_API,
        base_url="https://openapi.twse.com.tw/v1",
        documentation_url="https://openapi.twse.com.tw/",
        priority=1,
    ),
    "tpex_openapi": DataSource(
        source_id="tpex_openapi",
        display_name="證券櫃檯買賣中心 OpenAPI",
        market=Market.TPEX,
        source_type=SourceType.OPEN_API,
        base_url="https://www.tpex.org.tw/openapi",
        documentation_url=(
            "https://www.tpex.org.tw/openapi/"
        ),
        priority=1,
    ),
    "twse_etf_products": DataSource(
        source_id="twse_etf_products",
        display_name="證交所 ETF 商品清單",
        market=Market.TWSE,
        source_type=SourceType.OFFICIAL_WEB_PAGE,
        base_url=(
            "https://www.twse.com.tw/zh/products/"
            "securities/etf/products/list.html"
        ),
        documentation_url=(
            "https://www.twse.com.tw/zh/products/"
            "securities/etf/products/list.html"
        ),
        priority=2,
        enabled=False,
    ),
    "twse_etf_dividends": DataSource(
        source_id="twse_etf_dividends",
        display_name="證交所 ETF e添富配息資料",
        market=Market.TWSE,
        source_type=SourceType.OFFICIAL_WEB_PAGE,
        base_url=(
            "https://www.twse.com.tw/zh/"
            "ETFortune-institute/dividendList"
        ),
        documentation_url=(
            "https://www.twse.com.tw/zh/"
            "ETFortune-institute/dividendList"
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

    normalized_source_id = source_id.strip().lower()

    try:
        return DATA_SOURCES[normalized_source_id]

    except KeyError as error:
        raise KeyError(
            f"找不到資料來源：{normalized_source_id}"
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