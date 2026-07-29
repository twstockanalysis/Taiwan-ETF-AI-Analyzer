"""Streamlit 前端使用的 FastAPI Client。"""

from typing import Any

import httpx


class APIClientError(RuntimeError):
    """FastAPI Client 的共用錯誤。"""


class APIConnectionError(APIClientError):
    """無法連接 FastAPI 時的錯誤。"""


class APIResponseError(APIClientError):
    """FastAPI 回應內容不正確時的錯誤。"""


def fetch_api_health(
    api_base_url: str,
    timeout_seconds: float = 5.0,
) -> dict[str, str]:
    """讀取 FastAPI 健康狀態。

    Args:
        api_base_url:
            FastAPI Base URL。
        timeout_seconds:
            HTTP 請求逾時秒數。

    Returns:
        dict[str, str]:
            FastAPI 健康狀態。

    Raises:
        APIConnectionError:
            無法連接 FastAPI。
        APIResponseError:
            FastAPI 回應錯誤或格式不正確。
    """

    endpoint_url = (
        f"{api_base_url.rstrip('/')}/health"
    )

    try:
        response = httpx.get(
            endpoint_url,
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "TW-ETF-AI-Analyzer-Frontend/0.1"
                ),
            },
        )

        response.raise_for_status()

    except httpx.RequestError as error:
        raise APIConnectionError(
            "無法連接 FastAPI 後端："
            f"{endpoint_url}"
        ) from error

    except httpx.HTTPStatusError as error:
        raise APIResponseError(
            "FastAPI 健康檢查回傳錯誤："
            f"HTTP {error.response.status_code}"
        ) from error

    try:
        payload: Any = response.json()

    except ValueError as error:
        raise APIResponseError(
            "FastAPI 回傳內容不是有效 JSON"
        ) from error

    if not isinstance(payload, dict):
        raise APIResponseError(
            "FastAPI 健康檢查格式不正確"
        )

    status_value = payload.get("status")

    if status_value != "healthy":
        raise APIResponseError(
            "FastAPI 狀態不是 healthy"
        )

    return {
        "status": str(status_value),
    }