"""Streamlit 前端使用的 FastAPI Client。"""

from typing import Any

import httpx


class APIClientError(RuntimeError):
    """FastAPI Client 的共用錯誤。"""


class APIConnectionError(APIClientError):
    """無法連接 FastAPI 時的錯誤。"""


class APIResponseError(APIClientError):
    """FastAPI 回應內容不正確時的錯誤。"""


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

        raise APIResponseError(
            f"{operation_name}失敗："
            f"HTTP {error.response.status_code}；"
            f"{detail}"
        ) from error

    try:
        return response.json()

    except ValueError as error:
        raise APIResponseError(
            f"{operation_name}回傳內容不是有效 JSON"
        ) from error


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
            FastAPI 回應格式不正確。
    """

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/health",
        operation_name="FastAPI 健康檢查",
        timeout_seconds=timeout_seconds,
    )

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


def validate_etf_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單筆 ETF API 回應。

    Args:
        item:
            ETF API 回應項目。
        index:
            項目所在位置。

    Returns:
        dict[str, Any]:
            驗證後的 ETF 資料。

    Raises:
        APIResponseError:
            ETF 項目格式不正確。
    """

    if not isinstance(item, dict):
        raise APIResponseError(
            f"ETF 列表第 {index} 筆不是 JSON 物件"
        )

    required_fields = {
        "code",
        "name",
        "is_active",
        "is_bond",
        "listing_date",
        "fund_size",
        "expense_ratio",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"ETF 列表第 {index} 筆缺少欄位："
            f"{missing_text}"
        )

    return item


def fetch_etfs(
    api_base_url: str,
    keyword: str | None = None,
    is_active: bool | None = None,
    is_bond: bool | None = None,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """讀取 ETF 篩選及分頁列表。

    Args:
        api_base_url:
            FastAPI Base URL。
        keyword:
            ETF 代號或名稱關鍵字。
        is_active:
            主動式或被動式篩選。
        is_bond:
            債券或非債券篩選。
        limit:
            每頁筆數，範圍為 1 到 100。
        offset:
            略過筆數。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        dict[str, Any]:
            ETF 列表、總筆數與分頁資訊。

    Raises:
        ValueError:
            分頁參數超出允許範圍。
        APIClientError:
            FastAPI 連線或回應錯誤。
    """

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    params: dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
    }

    if keyword is not None:
        normalized_keyword = keyword.strip()

        if normalized_keyword:
            params["keyword"] = normalized_keyword

    if is_active is not None:
        params["is_active"] = (
            "true"
            if is_active
            else "false"
        )

    if is_bond is not None:
        params["is_bond"] = (
            "true"
            if is_bond
            else "false"
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path="/api/v1/etfs",
        operation_name="ETF 列表查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 列表回應必須是 JSON 物件"
        )

    items = payload.get("items")
    total = payload.get("total")
    response_limit = payload.get("limit")
    response_offset = payload.get("offset")

    if not isinstance(items, list):
        raise APIResponseError(
            "ETF 列表 items 格式不正確"
        )

    integer_values = {
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
    }

    for field_name, value in integer_values.items():
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
        ):
            raise APIResponseError(
                f"ETF 列表 {field_name} "
                "必須是整數"
            )

    validated_items = [
        validate_etf_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    return {
        "items": validated_items,
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
    }