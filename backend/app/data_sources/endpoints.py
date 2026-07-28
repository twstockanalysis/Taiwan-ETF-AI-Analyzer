"""官方資料 API Endpoint Registry。"""

from dataclasses import dataclass
from enum import StrEnum

from backend.app.data_sources.registry import (
    get_data_source,
)


class DatasetKind(StrEnum):
    """官方資料集用途。"""

    ETF_MASTER = "etf_master"
    MARKET_QUOTES = "market_quotes"
    DIVIDENDS = "dividends"


@dataclass(
    frozen=True,
    slots=True,
)
class ApiEndpoint:
    """官方 API Endpoint 設定。"""

    endpoint_id: str
    display_name: str
    source_id: str
    dataset_kind: DatasetKind
    path: str
    enabled: bool = True


API_ENDPOINTS: dict[str, ApiEndpoint] = {
    "twse_fund_master": ApiEndpoint(
        endpoint_id="twse_fund_master",
        display_name="TWSE 基金基本資料彙總表",
        source_id="twse_openapi",
        dataset_kind=DatasetKind.ETF_MASTER,
        path="/opendata/t187ap47_L",
    ),
}


def get_api_endpoint(
    endpoint_id: str,
) -> ApiEndpoint:
    """依識別碼取得 API Endpoint。

    Args:
        endpoint_id:
            API Endpoint 識別碼。

    Returns:
        ApiEndpoint:
            API Endpoint 設定。

    Raises:
        KeyError:
            找不到指定 Endpoint 時拋出。
    """

    normalized_endpoint_id = (
        endpoint_id.strip().lower()
    )

    try:
        return API_ENDPOINTS[
            normalized_endpoint_id
        ]

    except KeyError as error:
        raise KeyError(
            f"找不到 API Endpoint："
            f"{normalized_endpoint_id}"
        ) from error


def build_endpoint_url(
    endpoint: ApiEndpoint,
) -> str:
    """組合正式 API URL。

    Args:
        endpoint:
            API Endpoint 設定。

    Returns:
        str:
            完整 API URL。

    Raises:
        ValueError:
            資料來源缺少 Base URL 時拋出。
    """

    source = get_data_source(
        endpoint.source_id
    )

    if not source.base_url:
        raise ValueError(
            f"資料來源缺少 Base URL："
            f"{source.source_id}"
        )

    return (
        f"{source.base_url.rstrip('/')}/"
        f"{endpoint.path.lstrip('/')}"
    )