"""官方 JSON API 下載工具。"""

from typing import Any

import httpx

from backend.app.data_sources.endpoints import (
    ApiEndpoint,
    build_endpoint_url,
)
from backend.app.data_sources.openapi import (
    create_ssl_context,
)
from backend.app.data_sources.registry import (
    get_data_source,
)


def validate_json_records(
    payload: object,
) -> list[dict[str, Any]]:
    """驗證 API 回傳的是 JSON 物件陣列。

    Args:
        payload:
            HTTP 回傳並解析後的 JSON。

    Returns:
        list[dict[str, Any]]:
            驗證完成的資料紀錄。

    Raises:
        ValueError:
            回傳格式不是物件陣列時拋出。
    """

    if not isinstance(payload, list):
        raise ValueError(
            "官方 API 回傳內容必須是 JSON 陣列"
        )

    records: list[dict[str, Any]] = []

    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(
                "官方 API 第 "
                f"{index + 1} 筆資料不是 JSON 物件"
            )

        records.append(item)

    return records


def fetch_json_records(
    endpoint: ApiEndpoint,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    """從官方 API 下載 JSON 紀錄。

    Args:
        endpoint:
            API Endpoint 設定。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        list[dict[str, Any]]:
            官方 API 資料。

    Raises:
        httpx.HTTPError:
            HTTP 請求失敗時拋出。
        ValueError:
            JSON 格式不正確時拋出。
    """

    source = get_data_source(
        endpoint.source_id
    )

    endpoint_url = build_endpoint_url(
        endpoint
    )

    ssl_context = create_ssl_context(
        allow_legacy_x509=(
            source.allow_legacy_x509
        ),
    )

    response = httpx.get(
        endpoint_url,
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=ssl_context,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "TW-ETF-AI-Analyzer/0.1 "
                "(official-data-downloader)"
            ),
        },
    )

    response.raise_for_status()

    return validate_json_records(
        response.json()
    )