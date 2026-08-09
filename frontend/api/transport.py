"""前端 API 共用 HTTP 傳輸與 JSON 解析。"""

from typing import Any

import httpx

from frontend.api.errors import (
    APIConnectionError,
    APIResourceNotFoundError,
    APIResponseError,
)


def extract_response_detail(
    response: httpx.Response,
) -> str:
    """從 HTTP 錯誤回應取得可讀訊息。

    Args:
        response:
            HTTPX 回應物件。

    Returns:
        str:
            FastAPI 錯誤內容。
    """

    try:
        payload: Any = response.json()

    except ValueError:
        response_text = response.text.strip()

        return (
            response_text
            if response_text
            else "沒有錯誤內容"
        )

    if isinstance(payload, dict):
        detail = payload.get("detail")

        if detail is not None:
            return str(detail)

    return str(payload)


def get_json(
    api_base_url: str,
    endpoint_path: str,
    operation_name: str,
    params: dict[str, str | int] | None = None,
    timeout_seconds: float = 5.0,
) -> Any:
    """呼叫 FastAPI 並解析 JSON。

    Args:
        api_base_url:
            FastAPI Base URL。
        endpoint_path:
            API 路徑。
        operation_name:
            顯示於錯誤訊息的作業名稱。
        params:
            Query Parameters。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        Any:
            FastAPI JSON 回應。

    Raises:
        APIConnectionError:
            無法連接 FastAPI。
        APIResponseError:
            HTTP 或 JSON 回應不正確。
    """

    endpoint_url = (
        f"{api_base_url.rstrip('/')}/"
        f"{endpoint_path.lstrip('/')}"
    )

    try:
        response = httpx.get(
            endpoint_url,
            params=params,
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
            f"無法連接 FastAPI 後端："
            f"{endpoint_url}"
        ) from error

    except httpx.HTTPStatusError as error:
        detail = extract_response_detail(
            error.response
        )

        status_code = (
            error.response.status_code
        )

        if status_code == 404:
            raise APIResourceNotFoundError(
                f"{operation_name}找不到資料："
                f"{detail}"
            ) from error

        raise APIResponseError(
            f"{operation_name}失敗："
            f"HTTP {status_code}；"
            f"{detail}"
        ) from error

    try:
        return response.json()

    except ValueError as error:
        raise APIResponseError(
            f"{operation_name}回傳內容不是有效 JSON"
        ) from error


def post_json(
    api_base_url: str,
    endpoint_path: str,
    operation_name: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> Any:
    """以 POST 呼叫 FastAPI 並解析 JSON。"""

    endpoint_url = (
        f"{api_base_url.rstrip('/')}/"
        f"{endpoint_path.lstrip('/')}"
    )
    try:
        response = httpx.post(
            endpoint_url,
            json=payload,
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "TW-ETF-AI-Analyzer-Frontend/0.1",
            },
        )
        response.raise_for_status()
    except httpx.RequestError as error:
        raise APIConnectionError(
            f"無法連接 FastAPI 後端：{endpoint_url}"
        ) from error
    except httpx.HTTPStatusError as error:
        detail = extract_response_detail(error.response)
        status_code = error.response.status_code
        if status_code == 404:
            raise APIResourceNotFoundError(
                f"{operation_name}找不到資料：{detail}"
            ) from error
        raise APIResponseError(
            f"{operation_name}失敗：HTTP {status_code}；{detail}"
        ) from error

    try:
        return response.json()
    except ValueError as error:
        raise APIResponseError(
            f"{operation_name}回傳內容不是有效 JSON"
        ) from error
