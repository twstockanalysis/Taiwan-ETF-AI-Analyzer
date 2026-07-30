"""Streamlit 前端使用的 FastAPI Client。"""

from datetime import date
from typing import Any
from urllib.parse import quote

import httpx


class APIClientError(RuntimeError):
    """FastAPI Client 的共用錯誤。"""


class APIConnectionError(APIClientError):
    """無法連接 FastAPI 時的錯誤。"""


class APIResponseError(APIClientError):
    """FastAPI 回應內容不正確時的錯誤。"""


class APIResourceNotFoundError(
    APIResponseError
):
    """FastAPI 找不到指定資源。"""


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


def fetch_etf_by_code(
    api_base_url: str,
    code: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """依代號取得單筆 ETF 資料。

    Args:
        api_base_url:
            FastAPI Base URL。
        code:
            ETF 證券代號。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        dict[str, Any]:
            ETF 主資料。

    Raises:
        ValueError:
            ETF 代號為空白。
        APIClientError:
            FastAPI 連線或回應錯誤。
    """

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/"
            f"{encoded_code}"
        ),
        operation_name=(
            f"ETF {normalized_code} 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    item = validate_etf_item(
        payload,
        index=1,
    )

    response_code = str(
        item["code"]
    ).strip().upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "ETF 詳細資料代號與查詢代號不一致"
        )

    return item

SUPPORTED_PERFORMANCE_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)

SUPPORTED_PERFORMANCE_METRICS = (
    "PRICE_RETURN",
    "TOTAL_RETURN",
    "NAV_RETURN",
)


def normalize_performance_period(
    value: str,
) -> str:
    """正規化前端使用的績效期間。"""

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_PERFORMANCE_PERIODS
    ):
        raise ValueError(
            "period 必須是 "
            "1M、3M、6M 或 1Y"
        )

    return normalized_value


def normalize_performance_metric(
    value: str,
) -> str:
    """正規化前端使用的績效類型。"""

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_PERFORMANCE_METRICS
    ):
        raise ValueError(
            "metric 必須是 "
            "PRICE_RETURN、TOTAL_RETURN "
            "或 NAV_RETURN"
        )

    return normalized_value


def validate_performance_date(
    value: object,
    field_name: str,
) -> str:
    """驗證 API 回傳的 ISO 日期文字。"""

    if not isinstance(value, str):
        raise APIResponseError(
            f"{field_name} 必須是日期文字"
        )

    try:
        date.fromisoformat(value)

    except ValueError as error:
        raise APIResponseError(
            f"{field_name} 不是有效西元日期"
        ) from error

    return value


def validate_return_pct(
    value: object,
    field_name: str,
) -> float:
    """驗證績效百分比數值。"""

    if (
        not isinstance(
            value,
            (
                int,
                float,
            ),
        )
        or isinstance(value, bool)
    ):
        raise APIResponseError(
            f"{field_name} 必須是數值"
        )

    normalized_value = float(value)

    if normalized_value < -100:
        raise APIResponseError(
            f"{field_name} 不得小於 -100"
        )

    return normalized_value


def validate_performance_ranking_item(
    item: object,
    index: int,
    expected_period: str,
    expected_metric: str,
) -> dict[str, Any]:
    """驗證單筆績效排行榜資料。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"績效排行榜第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "rank",
        "etf_code",
        "name",
        "is_active",
        "is_bond",
        "as_of_date",
        "period_code",
        "metric_code",
        "return_pct",
        "source_id",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"績效排行榜第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    rank = item["rank"]

    if (
        not isinstance(rank, int)
        or isinstance(rank, bool)
        or rank < 1
    ):
        raise APIResponseError(
            f"績效排行榜第 {index} 筆 "
            "rank 格式不正確"
        )

    for field_name in (
        "etf_code",
        "name",
        "source_id",
    ):
        value = item[field_name]

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise APIResponseError(
                f"績效排行榜第 {index} 筆 "
                f"{field_name} 格式不正確"
            )

    for field_name in (
        "is_active",
        "is_bond",
    ):
        if not isinstance(
            item[field_name],
            bool,
        ):
            raise APIResponseError(
                f"績效排行榜第 {index} 筆 "
                f"{field_name} 必須是布林值"
            )

    period_code = str(
        item["period_code"]
    ).strip().upper()

    metric_code = str(
        item["metric_code"]
    ).strip().upper()

    if period_code != expected_period:
        raise APIResponseError(
            "績效排行榜包含非指定期間資料"
        )

    if metric_code != expected_metric:
        raise APIResponseError(
            "績效排行榜包含非指定類型資料"
        )

    validated_item = dict(item)
    validated_item["etf_code"] = str(
        item["etf_code"]
    ).strip().upper()
    validated_item["name"] = str(
        item["name"]
    ).strip()
    validated_item["source_id"] = str(
        item["source_id"]
    ).strip().lower()
    validated_item["period_code"] = (
        period_code
    )
    validated_item["metric_code"] = (
        metric_code
    )
    validated_item["as_of_date"] = (
        validate_performance_date(
            item["as_of_date"],
            (
                f"績效排行榜第 {index} 筆 "
                "as_of_date"
            ),
        )
    )
    validated_item["return_pct"] = (
        validate_return_pct(
            item["return_pct"],
            (
                f"績效排行榜第 {index} 筆 "
                "return_pct"
            ),
        )
    )

    return validated_item


def fetch_performance_ranking(
    api_base_url: str,
    period: str = "6M",
    metric: str = "PRICE_RETURN",
    is_active: bool | None = None,
    is_bond: bool | None = False,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得 ETF 績效排行榜。"""

    normalized_period = (
        normalize_performance_period(
            period
        )
    )

    normalized_metric = (
        normalize_performance_metric(
            metric
        )
    )

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    params: dict[str, str | int] = {
        "period": normalized_period,
        "metric": normalized_metric,
        "limit": limit,
        "offset": offset,
    }

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
        endpoint_path=(
            "/api/v1/performance/ranking"
        ),
        operation_name="ETF 績效排行榜查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "績效排行榜回應必須是 JSON 物件"
        )

    response_period = str(
        payload.get("period_code", "")
    ).strip().upper()

    response_metric = str(
        payload.get("metric_code", "")
    ).strip().upper()

    if response_period != normalized_period:
        raise APIResponseError(
            "績效排行榜回傳期間與查詢期間不一致"
        )

    if response_metric != normalized_metric:
        raise APIResponseError(
            "績效排行榜回傳類型與查詢類型不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "績效排行榜 items 格式不正確"
        )

    integer_values = {
        "total": payload.get("total"),
        "limit": payload.get("limit"),
        "offset": payload.get("offset"),
    }

    for field_name, value in (
        integer_values.items()
    ):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise APIResponseError(
                f"績效排行榜 {field_name} "
                "必須是非負整數"
            )

    if integer_values["limit"] < 1:
        raise APIResponseError(
            "績效排行榜 limit 必須大於 0"
        )

    validated_items = [
        validate_performance_ranking_item(
            item=item,
            index=index,
            expected_period=(
                normalized_period
            ),
            expected_metric=(
                normalized_metric
            ),
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    return {
        "period_code": response_period,
        "metric_code": response_metric,
        "items": validated_items,
        "total": integer_values["total"],
        "limit": integer_values["limit"],
        "offset": integer_values["offset"],
    }


def validate_etf_performance_item(
    item: object,
    index: int,
    expected_metric: str,
) -> dict[str, Any]:
    """驗證單一 ETF 的單一期間績效。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"ETF 績效第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "as_of_date",
        "period_code",
        "metric_code",
        "return_pct",
        "source_id",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"ETF 績效第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    try:
        period_code = (
            normalize_performance_period(
                str(item["period_code"])
            )
        )

    except ValueError as error:
        raise APIResponseError(
            f"ETF 績效第 {index} 筆 "
            "period_code 格式不正確"
        ) from error

    metric_code = str(
        item["metric_code"]
    ).strip().upper()

    if metric_code != expected_metric:
        raise APIResponseError(
            "ETF 績效包含非指定類型資料"
        )

    source_id = item["source_id"]

    if (
        not isinstance(source_id, str)
        or not source_id.strip()
    ):
        raise APIResponseError(
            f"ETF 績效第 {index} 筆 "
            "source_id 格式不正確"
        )

    return {
        "as_of_date": (
            validate_performance_date(
                item["as_of_date"],
                (
                    f"ETF 績效第 {index} 筆 "
                    "as_of_date"
                ),
            )
        ),
        "period_code": period_code,
        "metric_code": metric_code,
        "return_pct": validate_return_pct(
            item["return_pct"],
            (
                f"ETF 績效第 {index} 筆 "
                "return_pct"
            ),
        ),
        "source_id": (
            source_id.strip().lower()
        ),
    }


def fetch_etf_performance(
    api_base_url: str,
    code: str,
    metric: str = "PRICE_RETURN",
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的多期間績效。"""

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    normalized_metric = (
        normalize_performance_metric(
            metric
        )
    )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/"
            f"{encoded_code}/performance"
        ),
        operation_name=(
            f"ETF {normalized_code} 績效查詢"
        ),
        params={
            "metric": normalized_metric,
        },
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 績效回應必須是 JSON 物件"
        )

    response_code = str(
        payload.get("etf_code", "")
    ).strip().upper()

    response_metric = str(
        payload.get("metric_code", "")
    ).strip().upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "ETF 績效代號與查詢代號不一致"
        )

    if response_metric != normalized_metric:
        raise APIResponseError(
            "ETF 績效類型與查詢類型不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "ETF 績效 items 格式不正確"
        )

    validated_items = [
        validate_etf_performance_item(
            item=item,
            index=index,
            expected_metric=(
                normalized_metric
            ),
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    period_order = {
        period_code: index
        for index, period_code in enumerate(
            SUPPORTED_PERFORMANCE_PERIODS
        )
    }

    period_codes = [
        item["period_code"]
        for item in validated_items
    ]

    if len(period_codes) != len(
        set(period_codes)
    ):
        raise APIResponseError(
            "ETF 績效包含重複期間"
        )

    validated_items.sort(
        key=lambda item: (
            period_order[
                item["period_code"]
            ]
        )
    )

    return {
        "etf_code": response_code,
        "metric_code": response_metric,
        "items": validated_items,
    }
