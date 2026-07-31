"""Streamlit 前端使用的 FastAPI Client。"""

from datetime import date, datetime
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

SUPPORTED_DIVIDEND_COMPONENT_BASES = (
    "ESTIMATED",
    "ACTUAL",
)


def validate_non_negative_integer(
    value: object,
    field_name: str,
) -> int:
    """驗證非負整數。"""

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise APIResponseError(
            f"{field_name} 必須是非負整數"
        )

    return value


def validate_positive_integer(
    value: object,
    field_name: str,
) -> int:
    """驗證正整數。"""

    normalized_value = (
        validate_non_negative_integer(
            value,
            field_name,
        )
    )

    if normalized_value < 1:
        raise APIResponseError(
            f"{field_name} 必須大於 0"
        )

    return normalized_value


def validate_optional_iso_date(
    value: object,
    field_name: str,
) -> str | None:
    """驗證可能為空值的 ISO 日期。"""

    if value is None:
        return None

    return validate_performance_date(
        value,
        field_name,
    )


def validate_optional_number(
    value: object,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    """驗證可能為空值的數值。"""

    if value is None:
        return None

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

    if (
        minimum is not None
        and normalized_value < minimum
    ):
        raise APIResponseError(
            f"{field_name} 不得小於 "
            f"{minimum}"
        )

    if (
        maximum is not None
        and normalized_value > maximum
    ):
        raise APIResponseError(
            f"{field_name} 不得大於 "
            f"{maximum}"
        )

    return normalized_value


def validate_required_text(
    value: object,
    field_name: str,
) -> str:
    """驗證必要文字欄位。"""

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise APIResponseError(
            f"{field_name} 必須是非空白文字"
        )

    return value.strip()


def validate_dividend_event_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單筆 ETF 配息事件。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"配息歷史第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "dividend_id",
        "source_event_id",
        "announcement_date",
        "ex_dividend_date",
        "record_date",
        "payment_date",
        "amount_per_unit",
        "currency",
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
            f"配息歷史第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    currency = validate_required_text(
        item["currency"],
        (
            f"配息歷史第 {index} 筆 "
            "currency"
        ),
    ).upper()

    if len(currency) != 3:
        raise APIResponseError(
            f"配息歷史第 {index} 筆 "
            "currency 必須是 3 個字元"
        )

    amount_per_unit = (
        validate_optional_number(
            item["amount_per_unit"],
            (
                f"配息歷史第 {index} 筆 "
                "amount_per_unit"
            ),
            minimum=0,
        )
    )

    if amount_per_unit is None:
        raise APIResponseError(
            f"配息歷史第 {index} 筆 "
            "amount_per_unit 不可為空值"
        )

    return {
        "dividend_id": (
            validate_positive_integer(
                item["dividend_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "dividend_id"
                ),
            )
        ),
        "source_event_id": (
            validate_required_text(
                item["source_event_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "source_event_id"
                ),
            )
        ),
        "announcement_date": (
            validate_optional_iso_date(
                item["announcement_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "announcement_date"
                ),
            )
        ),
        "ex_dividend_date": (
            validate_optional_iso_date(
                item["ex_dividend_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "ex_dividend_date"
                ),
            )
        ),
        "record_date": (
            validate_optional_iso_date(
                item["record_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "record_date"
                ),
            )
        ),
        "payment_date": (
            validate_optional_iso_date(
                item["payment_date"],
                (
                    f"配息歷史第 {index} 筆 "
                    "payment_date"
                ),
            )
        ),
        "amount_per_unit": amount_per_unit,
        "currency": currency,
        "source_id": (
            validate_required_text(
                item["source_id"],
                (
                    f"配息歷史第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        ),
    }


def fetch_etf_dividends(
    api_base_url: str,
    code: str,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的配息歷史。"""

    normalized_code = (
        code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "ETF 代號不可為空白"
        )

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    encoded_code = quote(
        normalized_code,
        safe="",
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/etfs/"
            f"{encoded_code}/dividends"
        ),
        operation_name=(
            f"ETF {normalized_code} "
            "配息歷史查詢"
        ),
        params={
            "limit": limit,
            "offset": offset,
        },
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 配息歷史回應必須是 JSON 物件"
        )

    response_code = validate_required_text(
        payload.get("etf_code"),
        "ETF 配息歷史 etf_code",
    ).upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "ETF 配息歷史代號與查詢代號不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "ETF 配息歷史 items 格式不正確"
        )

    total = validate_non_negative_integer(
        payload.get("total"),
        "ETF 配息歷史 total",
    )

    response_limit = (
        validate_positive_integer(
            payload.get("limit"),
            "ETF 配息歷史 limit",
        )
    )

    response_offset = (
        validate_non_negative_integer(
            payload.get("offset"),
            "ETF 配息歷史 offset",
        )
    )

    if response_limit != limit:
        raise APIResponseError(
            "ETF 配息歷史回傳 limit "
            "與查詢條件不一致"
        )

    if response_offset != offset:
        raise APIResponseError(
            "ETF 配息歷史回傳 offset "
            "與查詢條件不一致"
        )

    validated_items = [
        validate_dividend_event_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    return {
        "etf_code": response_code,
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
        "items": validated_items,
    }


def validate_dividend_component_item(
    item: object,
    index: int,
    expected_dividend_id: int,
) -> dict[str, Any]:
    """驗證單筆配息組成。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"配息組成第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "component_id",
        "dividend_id",
        "component_code",
        "component_basis",
        "component_name",
        "amount_per_unit",
        "ratio_pct",
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
            f"配息組成第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    dividend_id = validate_positive_integer(
        item["dividend_id"],
        (
            f"配息組成第 {index} 筆 "
            "dividend_id"
        ),
    )

    if dividend_id != expected_dividend_id:
        raise APIResponseError(
            "配息組成包含其他配息事件資料"
        )

    component_basis = (
        validate_required_text(
            item["component_basis"],
            (
                f"配息組成第 {index} 筆 "
                "component_basis"
            ),
        ).upper()
    )

    if (
        component_basis
        not in SUPPORTED_DIVIDEND_COMPONENT_BASES
    ):
        raise APIResponseError(
            f"配息組成第 {index} 筆 "
            "component_basis 格式不正確"
        )

    component_name = (
        item["component_name"]
    )

    if component_name is not None:
        component_name = (
            validate_required_text(
                component_name,
                (
                    f"配息組成第 {index} 筆 "
                    "component_name"
                ),
            )
        )

    return {
        "component_id": (
            validate_positive_integer(
                item["component_id"],
                (
                    f"配息組成第 {index} 筆 "
                    "component_id"
                ),
            )
        ),
        "dividend_id": dividend_id,
        "component_code": (
            validate_required_text(
                item["component_code"],
                (
                    f"配息組成第 {index} 筆 "
                    "component_code"
                ),
            ).upper()
        ),
        "component_basis": (
            component_basis
        ),
        "component_name": (
            component_name
        ),
        "amount_per_unit": (
            validate_optional_number(
                item["amount_per_unit"],
                (
                    f"配息組成第 {index} 筆 "
                    "amount_per_unit"
                ),
                minimum=0,
            )
        ),
        "ratio_pct": (
            validate_optional_number(
                item["ratio_pct"],
                (
                    f"配息組成第 {index} 筆 "
                    "ratio_pct"
                ),
                minimum=0,
                maximum=100,
            )
        ),
        "source_id": (
            validate_required_text(
                item["source_id"],
                (
                    f"配息組成第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        ),
    }


def fetch_dividend_detail(
    api_base_url: str,
    dividend_id: int,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單次配息事件及全部組成。"""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/dividends/"
            f"{dividend_id}"
        ),
        operation_name=(
            f"配息事件 {dividend_id} 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    event = validate_dividend_event_item(
        payload,
        index=1,
    )

    if (
        event["dividend_id"]
        != dividend_id
    ):
        raise APIResponseError(
            "配息事件 ID 與查詢 ID 不一致"
        )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "配息事件回應必須是 JSON 物件"
        )

    etf_code = validate_required_text(
        payload.get("etf_code"),
        "配息事件 etf_code",
    ).upper()

    components = payload.get(
        "components"
    )

    if not isinstance(components, list):
        raise APIResponseError(
            "配息事件 components 格式不正確"
        )

    validated_components = [
        validate_dividend_component_item(
            item=item,
            index=index,
            expected_dividend_id=(
                dividend_id
            ),
        )
        for index, item in enumerate(
            components,
            start=1,
        )
    ]

    return {
        **event,
        "etf_code": etf_code,
        "components": validated_components,
    }


def normalize_component_basis(
    value: str | None,
) -> str | None:
    """正規化配息組成資訊基礎。"""

    if value is None:
        return None

    normalized_value = (
        value.strip().upper()
    )

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_COMPONENT_BASES
    ):
        raise ValueError(
            "component_basis 必須是 "
            "ESTIMATED 或 ACTUAL"
        )

    return normalized_value


def fetch_dividend_components(
    api_base_url: str,
    dividend_id: int,
    component_basis: str | None = None,
    component_code: str | None = None,
    source_id: str | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單次配息的篩選後組成。"""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    normalized_basis = (
        normalize_component_basis(
            component_basis
        )
    )

    params: dict[str, str | int] = {}

    if normalized_basis is not None:
        params["component_basis"] = (
            normalized_basis
        )

    if component_code is not None:
        normalized_component_code = (
            component_code.strip().upper()
        )

        if not normalized_component_code:
            raise ValueError(
                "component_code 不可為空白"
            )

        params["component_code"] = (
            normalized_component_code
        )

    if source_id is not None:
        normalized_source_id = (
            source_id.strip().lower()
        )

        if not normalized_source_id:
            raise ValueError(
                "source_id 不可為空白"
            )

        params["source_id"] = (
            normalized_source_id
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            f"/api/v1/dividends/"
            f"{dividend_id}/components"
        ),
        operation_name=(
            f"配息事件 {dividend_id} "
            "組成查詢"
        ),
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "配息組成回應必須是 JSON 物件"
        )

    response_dividend_id = (
        validate_positive_integer(
            payload.get("dividend_id"),
            "配息組成 dividend_id",
        )
    )

    if response_dividend_id != dividend_id:
        raise APIResponseError(
            "配息組成回傳事件 ID "
            "與查詢 ID 不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "配息組成 items 格式不正確"
        )

    total = validate_non_negative_integer(
        payload.get("total"),
        "配息組成 total",
    )

    validated_items = [
        validate_dividend_component_item(
            item=item,
            index=index,
            expected_dividend_id=(
                dividend_id
            ),
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    if total != len(
        validated_items
    ):
        raise APIResponseError(
            "配息組成 total 與 items "
            "筆數不一致"
        )

    return {
        "dividend_id": (
            response_dividend_id
        ),
        "total": total,
        "items": validated_items,
    }


def validate_actual_76w_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單筆實際 76W 歷史。"""

    event = validate_dividend_event_item(
        item,
        index,
    )

    if not isinstance(item, dict):
        raise APIResponseError(
            f"實際 76W 第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "component_amount_per_unit",
        "ratio_pct",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"實際 76W 第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    return {
        **event,
        "component_amount_per_unit": (
            validate_optional_number(
                item[
                    "component_amount_per_unit"
                ],
                (
                    f"實際 76W 第 {index} 筆 "
                    "component_amount_per_unit"
                ),
                minimum=0,
            )
        ),
        "ratio_pct": (
            validate_optional_number(
                item["ratio_pct"],
                (
                    f"實際 76W 第 {index} 筆 "
                    "ratio_pct"
                ),
                minimum=0,
                maximum=100,
            )
        ),
    }


def fetch_etf_actual_76w(
    api_base_url: str,
    code: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得 ETF 的正式 ACTUAL 76W 歷史摘要。"""

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
            f"{encoded_code}/dividends/76w"
        ),
        operation_name=(
            f"ETF {normalized_code} "
            "實際 76W 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "實際 76W 回應必須是 JSON 物件"
        )

    response_code = validate_required_text(
        payload.get("etf_code"),
        "實際 76W etf_code",
    ).upper()

    if response_code != normalized_code:
        raise APIResponseError(
            "實際 76W 代號與查詢代號不一致"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "實際 76W items 格式不正確"
        )

    validated_items = [
        validate_actual_76w_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    total_dividend_count = (
        validate_non_negative_integer(
            payload.get(
                "total_dividend_count"
            ),
            (
                "實際 76W "
                "total_dividend_count"
            ),
        )
    )

    actual_record_count = (
        validate_non_negative_integer(
            payload.get(
                "actual_76w_record_count"
            ),
            (
                "實際 76W "
                "actual_76w_record_count"
            ),
        )
    )

    full_76w_count = (
        validate_non_negative_integer(
            payload.get(
                "full_76w_count"
            ),
            (
                "實際 76W "
                "full_76w_count"
            ),
        )
    )

    if actual_record_count != len(
        validated_items
    ):
        raise APIResponseError(
            "實際 76W 紀錄數與 items "
            "筆數不一致"
        )

    if full_76w_count > actual_record_count:
        raise APIResponseError(
            "100% 76W 次數不可大於 "
            "實際 76W 紀錄數"
        )

    latest_ratio = (
        validate_optional_number(
            payload.get(
                "latest_76w_ratio_pct"
            ),
            (
                "實際 76W "
                "latest_76w_ratio_pct"
            ),
            minimum=0,
            maximum=100,
        )
    )

    average_ratio = (
        validate_optional_number(
            payload.get(
                "average_76w_ratio_pct"
            ),
            (
                "實際 76W "
                "average_76w_ratio_pct"
            ),
            minimum=0,
            maximum=100,
        )
    )

    return {
        "etf_code": response_code,
        "total_dividend_count": (
            total_dividend_count
        ),
        "actual_76w_record_count": (
            actual_record_count
        ),
        "full_76w_count": (
            full_76w_count
        ),
        "latest_76w_ratio_pct": (
            latest_ratio
        ),
        "average_76w_ratio_pct": (
            average_ratio
        ),
        "items": validated_items,
    }

SUPPORTED_DIVIDEND_REVIEW_STATUSES = (
    "PENDING",
    "IN_REVIEW",
    "RESOLVED",
    "SKIPPED",
)

SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES = (
    "MISSING_ACTUAL_COMPONENTS",
    "MISSING_SOURCE_DOCUMENT",
)


def normalize_dividend_review_status(
    value: str | None,
) -> str | None:
    """正規化正式配息審核狀態。"""

    if value is None:
        return None

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_REVIEW_STATUSES
    ):
        raise ValueError(
            "status 必須是 PENDING、IN_REVIEW、"
            "RESOLVED 或 SKIPPED"
        )

    return normalized_value


def normalize_dividend_review_issue_type(
    value: str | None,
) -> str | None:
    """正規化正式配息缺失類型。"""

    if value is None:
        return None

    normalized_value = value.strip().upper()

    if (
        normalized_value
        not in SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES
    ):
        raise ValueError(
            "issue_type 必須是 "
            "MISSING_ACTUAL_COMPONENTS 或 "
            "MISSING_SOURCE_DOCUMENT"
        )

    return normalized_value


def validate_optional_iso_datetime(
    value: object,
    field_name: str,
) -> str | None:
    """驗證可能為空值的 ISO 日期時間。"""

    if value is None:
        return None

    if not isinstance(value, str):
        raise APIResponseError(
            f"{field_name} 必須是日期時間文字"
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise APIResponseError(
            f"{field_name} 不可為空白"
        )

    try:
        datetime.fromisoformat(
            normalized_value.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError as error:
        raise APIResponseError(
            f"{field_name} 不是有效 ISO 日期時間"
        ) from error

    return normalized_value


def validate_required_iso_datetime(
    value: object,
    field_name: str,
) -> str:
    """驗證必要 ISO 日期時間。"""

    normalized_value = (
        validate_optional_iso_datetime(
            value,
            field_name,
        )
    )

    if normalized_value is None:
        raise APIResponseError(
            f"{field_name} 不可為空值"
        )

    return normalized_value


def validate_actual_dividend_coverage(
    payload: object,
    expected_etf_code: str | None = None,
) -> dict[str, Any]:
    """驗證正式配息覆蓋率回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "正式配息覆蓋率回應必須是 JSON 物件"
        )

    required_fields = {
        "etf_code",
        "total_dividend_count",
        "estimated_component_event_count",
        "actual_component_event_count",
        "actual_76w_event_count",
        "source_document_event_count",
        "missing_actual_component_event_count",
        "missing_source_document_event_count",
        "actual_component_coverage_pct",
        "actual_76w_coverage_pct",
        "source_document_coverage_pct",
    }

    missing_fields = (
        required_fields - payload.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            "正式配息覆蓋率缺少欄位："
            f"{missing_text}"
        )

    response_etf_code = payload["etf_code"]

    if response_etf_code is not None:
        response_etf_code = (
            validate_required_text(
                response_etf_code,
                "正式配息覆蓋率 etf_code",
            ).upper()
        )

    if (
        response_etf_code
        != expected_etf_code
    ):
        raise APIResponseError(
            "正式配息覆蓋率 ETF 代號"
            "與查詢條件不一致"
        )

    count_fields = (
        "total_dividend_count",
        "estimated_component_event_count",
        "actual_component_event_count",
        "actual_76w_event_count",
        "source_document_event_count",
        "missing_actual_component_event_count",
        "missing_source_document_event_count",
    )

    counts = {
        field_name: (
            validate_non_negative_integer(
                payload[field_name],
                (
                    "正式配息覆蓋率 "
                    f"{field_name}"
                ),
            )
        )
        for field_name in count_fields
    }

    total_count = counts[
        "total_dividend_count"
    ]

    for field_name in (
        "estimated_component_event_count",
        "actual_component_event_count",
        "actual_76w_event_count",
        "source_document_event_count",
    ):
        if counts[field_name] > total_count:
            raise APIResponseError(
                "正式配息覆蓋率事件數"
                "不可大於配息事件總數"
            )

    if (
        counts[
            "missing_actual_component_event_count"
        ]
        != (
            total_count
            - counts[
                "actual_component_event_count"
            ]
        )
    ):
        raise APIResponseError(
            "缺少 ACTUAL 事件數與覆蓋數不一致"
        )

    if (
        counts[
            "missing_source_document_event_count"
        ]
        != (
            total_count
            - counts[
                "source_document_event_count"
            ]
        )
    ):
        raise APIResponseError(
            "缺少來源文件事件數與覆蓋數不一致"
        )

    rate_fields = (
        "actual_component_coverage_pct",
        "actual_76w_coverage_pct",
        "source_document_coverage_pct",
    )

    rates = {
        field_name: (
            validate_optional_number(
                payload[field_name],
                (
                    "正式配息覆蓋率 "
                    f"{field_name}"
                ),
                minimum=0,
                maximum=100,
            )
        )
        for field_name in rate_fields
    }

    if total_count == 0:
        if any(
            value is not None
            for value in rates.values()
        ):
            raise APIResponseError(
                "沒有配息事件時覆蓋率必須為空值"
            )

    elif any(
        value is None
        for value in rates.values()
    ):
        raise APIResponseError(
            "有配息事件時覆蓋率不可為空值"
        )

    return {
        "etf_code": response_etf_code,
        **counts,
        **rates,
    }


def fetch_actual_dividend_coverage(
    api_base_url: str,
    etf_code: str | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得全站或單一 ETF 的正式配息覆蓋率。"""

    normalized_code: str | None = None
    params: dict[str, str | int] = {}

    if etf_code is not None:
        normalized_code = (
            etf_code.strip().upper()
        )

        if not normalized_code:
            raise ValueError(
                "etf_code 不可為空白"
            )

        params["etf_code"] = (
            normalized_code
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/data-quality/dividends/"
            "actual-coverage"
        ),
        operation_name="正式配息覆蓋率查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    return validate_actual_dividend_coverage(
        payload,
        expected_etf_code=normalized_code,
    )


def validate_dividend_review_queue_item(
    item: object,
    index: int,
    expected_queue_id: int | None = None,
) -> dict[str, Any]:
    """驗證單筆正式配息待處理項目。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"待處理佇列第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "queue_id",
        "dividend_id",
        "etf_code",
        "source_event_id",
        "ex_dividend_date",
        "amount_per_unit",
        "currency",
        "issue_type",
        "suggested_source_id",
        "priority",
        "status",
        "notes",
        "resolution_document_id",
        "last_evaluated_at",
        "resolved_at",
        "created_at",
        "updated_at",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"待處理佇列第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    queue_id = validate_positive_integer(
        item["queue_id"],
        (
            f"待處理佇列第 {index} 筆 "
            "queue_id"
        ),
    )

    if (
        expected_queue_id is not None
        and queue_id != expected_queue_id
    ):
        raise APIResponseError(
            "待處理佇列項目 ID 與查詢 ID 不一致"
        )

    issue_type = (
        normalize_dividend_review_issue_type(
            validate_required_text(
                item["issue_type"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "issue_type"
                ),
            )
        )
    )

    status_value = (
        normalize_dividend_review_status(
            validate_required_text(
                item["status"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "status"
                ),
            )
        )
    )

    priority = validate_positive_integer(
        item["priority"],
        (
            f"待處理佇列第 {index} 筆 "
            "priority"
        ),
    )

    if priority > 100:
        raise APIResponseError(
            f"待處理佇列第 {index} 筆 "
            "priority 不得大於 100"
        )

    currency = validate_required_text(
        item["currency"],
        (
            f"待處理佇列第 {index} 筆 "
            "currency"
        ),
    ).upper()

    if len(currency) != 3:
        raise APIResponseError(
            f"待處理佇列第 {index} 筆 "
            "currency 必須是 3 個字元"
        )

    amount_per_unit = (
        validate_optional_number(
            item["amount_per_unit"],
            (
                f"待處理佇列第 {index} 筆 "
                "amount_per_unit"
            ),
            minimum=0,
        )
    )

    if amount_per_unit is None:
        raise APIResponseError(
            f"待處理佇列第 {index} 筆 "
            "amount_per_unit 不可為空值"
        )

    suggested_source_id = (
        item["suggested_source_id"]
    )

    if suggested_source_id is not None:
        suggested_source_id = (
            validate_required_text(
                suggested_source_id,
                (
                    f"待處理佇列第 {index} 筆 "
                    "suggested_source_id"
                ),
            ).lower()
        )

    notes = item["notes"]

    if notes is not None:
        notes = validate_required_text(
            notes,
            (
                f"待處理佇列第 {index} 筆 "
                "notes"
            ),
        )

    resolution_document_id = item[
        "resolution_document_id"
    ]

    if resolution_document_id is not None:
        resolution_document_id = (
            validate_positive_integer(
                resolution_document_id,
                (
                    f"待處理佇列第 {index} 筆 "
                    "resolution_document_id"
                ),
            )
        )

    return {
        "queue_id": queue_id,
        "dividend_id": (
            validate_positive_integer(
                item["dividend_id"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "dividend_id"
                ),
            )
        ),
        "etf_code": (
            validate_required_text(
                item["etf_code"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "etf_code"
                ),
            ).upper()
        ),
        "source_event_id": (
            validate_required_text(
                item["source_event_id"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "source_event_id"
                ),
            )
        ),
        "ex_dividend_date": (
            validate_optional_iso_date(
                item["ex_dividend_date"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "ex_dividend_date"
                ),
            )
        ),
        "amount_per_unit": amount_per_unit,
        "currency": currency,
        "issue_type": issue_type,
        "suggested_source_id": (
            suggested_source_id
        ),
        "priority": priority,
        "status": status_value,
        "notes": notes,
        "resolution_document_id": (
            resolution_document_id
        ),
        "last_evaluated_at": (
            validate_required_iso_datetime(
                item["last_evaluated_at"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "last_evaluated_at"
                ),
            )
        ),
        "resolved_at": (
            validate_optional_iso_datetime(
                item["resolved_at"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "resolved_at"
                ),
            )
        ),
        "created_at": (
            validate_required_iso_datetime(
                item["created_at"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "created_at"
                ),
            )
        ),
        "updated_at": (
            validate_required_iso_datetime(
                item["updated_at"],
                (
                    f"待處理佇列第 {index} 筆 "
                    "updated_at"
                ),
            )
        ),
    }


def fetch_dividend_review_queue(
    api_base_url: str,
    status: str | None = "PENDING",
    etf_code: str | None = None,
    issue_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得正式配息待處理佇列。"""

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit 必須介於 1 到 100"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    normalized_status = (
        normalize_dividend_review_status(
            status
        )
    )

    normalized_issue_type = (
        normalize_dividend_review_issue_type(
            issue_type
        )
    )

    normalized_code: str | None = None

    params: dict[str, str | int] = {
        "limit": limit,
        "offset": offset,
    }

    if normalized_status is not None:
        params["status"] = normalized_status

    if etf_code is not None:
        normalized_code = (
            etf_code.strip().upper()
        )

        if not normalized_code:
            raise ValueError(
                "etf_code 不可為空白"
            )

        params["etf_code"] = (
            normalized_code
        )

    if normalized_issue_type is not None:
        params["issue_type"] = (
            normalized_issue_type
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/data-quality/dividends/"
            "review-queue"
        ),
        operation_name="正式配息待處理佇列查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "正式配息待處理佇列回應"
            "必須是 JSON 物件"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "正式配息待處理佇列 items "
            "格式不正確"
        )

    total = validate_non_negative_integer(
        payload.get("total"),
        "正式配息待處理佇列 total",
    )

    response_limit = validate_positive_integer(
        payload.get("limit"),
        "正式配息待處理佇列 limit",
    )

    response_offset = (
        validate_non_negative_integer(
            payload.get("offset"),
            "正式配息待處理佇列 offset",
        )
    )

    if response_limit != limit:
        raise APIResponseError(
            "正式配息待處理佇列回傳 limit "
            "與查詢條件不一致"
        )

    if response_offset != offset:
        raise APIResponseError(
            "正式配息待處理佇列回傳 offset "
            "與查詢條件不一致"
        )

    validated_items = [
        validate_dividend_review_queue_item(
            item,
            index,
        )
        for index, item in enumerate(
            items,
            start=1,
        )
    ]

    if len(validated_items) > total:
        raise APIResponseError(
            "正式配息待處理佇列 items "
            "筆數不可大於 total"
        )

    if normalized_code is not None:
        if any(
            item["etf_code"]
            != normalized_code
            for item in validated_items
        ):
            raise APIResponseError(
                "正式配息待處理佇列包含"
                "其他 ETF 資料"
            )

    if normalized_status is not None:
        if any(
            item["status"]
            != normalized_status
            for item in validated_items
        ):
            raise APIResponseError(
                "正式配息待處理佇列包含"
                "其他狀態資料"
            )

    if normalized_issue_type is not None:
        if any(
            item["issue_type"]
            != normalized_issue_type
            for item in validated_items
        ):
            raise APIResponseError(
                "正式配息待處理佇列包含"
                "其他缺失類型資料"
            )

    return {
        "total": total,
        "limit": response_limit,
        "offset": response_offset,
        "items": validated_items,
    }


def fetch_dividend_review_queue_item(
    api_base_url: str,
    queue_id: int,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一正式配息待處理項目。"""

    if queue_id < 1:
        raise ValueError(
            "queue_id 必須大於 0"
        )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/data-quality/dividends/"
            f"review-queue/{queue_id}"
        ),
        operation_name=(
            f"正式配息待處理項目 {queue_id} 查詢"
        ),
        timeout_seconds=timeout_seconds,
    )

    return validate_dividend_review_queue_item(
        payload,
        index=1,
        expected_queue_id=queue_id,
    )

SYSTEM_OVERVIEW_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)

SYSTEM_OVERVIEW_BATCH_STATUSES = (
    "running",
    "success",
    "failed",
)


def validate_overview_coverage_pct(
    value: object,
    *,
    covered_count: int,
    total_count: int,
    field_name: str,
) -> float | None:
    """驗證首頁覆蓋率與計數一致。"""

    normalized_value = (
        validate_optional_number(
            value,
            field_name,
            minimum=0,
            maximum=100,
        )
    )

    if total_count == 0:
        if normalized_value is not None:
            raise APIResponseError(
                f"{field_name} 在零分母時"
                "必須為空值"
            )

        return None

    if normalized_value is None:
        raise APIResponseError(
            f"{field_name} 在有資料時"
            "不可為空值"
        )

    expected_value = round(
        covered_count
        / total_count
        * 100,
        6,
    )

    if abs(
        normalized_value
        - expected_value
    ) > 0.000001:
        raise APIResponseError(
            f"{field_name} 與事件數不一致"
        )

    return normalized_value


def validate_system_overview_etfs(
    payload: object,
) -> dict[str, Any]:
    """驗證首頁 ETF 主資料摘要。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "系統總覽 etfs 必須是 JSON 物件"
        )

    total_count = (
        validate_non_negative_integer(
            payload.get(
                "total_count"
            ),
            (
                "系統總覽 etfs "
                "total_count"
            ),
        )
    )

    active_count = (
        validate_non_negative_integer(
            payload.get(
                "active_count"
            ),
            (
                "系統總覽 etfs "
                "active_count"
            ),
        )
    )

    passive_count = (
        validate_non_negative_integer(
            payload.get(
                "passive_count"
            ),
            (
                "系統總覽 etfs "
                "passive_count"
            ),
        )
    )

    bond_count = (
        validate_non_negative_integer(
            payload.get(
                "bond_count"
            ),
            (
                "系統總覽 etfs "
                "bond_count"
            ),
        )
    )

    non_bond_count = (
        validate_non_negative_integer(
            payload.get(
                "non_bond_count"
            ),
            (
                "系統總覽 etfs "
                "non_bond_count"
            ),
        )
    )

    if (
        active_count
        + passive_count
        != total_count
    ):
        raise APIResponseError(
            "系統總覽主動式與被動式"
            "數量不等於 ETF 總數"
        )

    if (
        bond_count
        + non_bond_count
        != total_count
    ):
        raise APIResponseError(
            "系統總覽債券與非債券"
            "數量不等於 ETF 總數"
        )

    return {
        "total_count": total_count,
        "active_count": active_count,
        "passive_count": passive_count,
        "bond_count": bond_count,
        "non_bond_count": (
            non_bond_count
        ),
        "latest_master_import_at": (
            validate_optional_iso_datetime(
                payload.get(
                    "latest_master_import_at"
                ),
                (
                    "系統總覽 etfs "
                    "latest_master_import_at"
                ),
            )
        ),
    }


def validate_system_overview_performance(
    payload: object,
    *,
    expected_total_etf_count: int,
) -> dict[str, Any]:
    """驗證首頁績效覆蓋摘要。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "系統總覽 performance "
            "必須是 JSON 物件"
        )

    metric_code = (
        validate_required_text(
            payload.get(
                "metric_code"
            ),
            (
                "系統總覽 performance "
                "metric_code"
            ),
        ).upper()
    )

    if metric_code != "PRICE_RETURN":
        raise APIResponseError(
            "系統總覽目前只支援 "
            "PRICE_RETURN"
        )

    source_id = (
        validate_required_text(
            payload.get(
                "source_id"
            ),
            (
                "系統總覽 performance "
                "source_id"
            ),
        ).lower()
    )

    if source_id != "twse_stock_day":
        raise APIResponseError(
            "系統總覽績效來源必須是 "
            "twse_stock_day"
        )

    etf_count = (
        validate_non_negative_integer(
            payload.get(
                "etf_count"
            ),
            (
                "系統總覽 performance "
                "etf_count"
            ),
        )
    )

    total_etf_count = (
        validate_non_negative_integer(
            payload.get(
                "total_etf_count"
            ),
            (
                "系統總覽 performance "
                "total_etf_count"
            ),
        )
    )

    if (
        total_etf_count
        != expected_total_etf_count
    ):
        raise APIResponseError(
            "系統總覽績效分母"
            "與 ETF 總數不一致"
        )

    if etf_count > total_etf_count:
        raise APIResponseError(
            "系統總覽績效 ETF 數量"
            "不可大於 ETF 總數"
        )

    coverage_pct = (
        validate_overview_coverage_pct(
            payload.get(
                "coverage_pct"
            ),
            covered_count=etf_count,
            total_count=(
                total_etf_count
            ),
            field_name=(
                "系統總覽 performance "
                "coverage_pct"
            ),
        )
    )

    latest_as_of_date = (
        validate_optional_iso_date(
            payload.get(
                "latest_as_of_date"
            ),
            (
                "系統總覽 performance "
                "latest_as_of_date"
            ),
        )
    )

    if (
        etf_count == 0
        and latest_as_of_date is not None
    ):
        raise APIResponseError(
            "系統總覽沒有績效資料時"
            "不得提供最新基準日"
        )

    raw_periods = payload.get(
        "periods"
    )

    if not isinstance(
        raw_periods,
        list,
    ):
        raise APIResponseError(
            "系統總覽 performance "
            "periods 必須是陣列"
        )

    periods: list[
        dict[str, Any]
    ] = []

    seen_periods: set[str] = set()

    for index, item in enumerate(
        raw_periods,
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(
                "系統總覽績效期間第 "
                f"{index} 筆不是 JSON 物件"
            )

        period_code = (
            validate_required_text(
                item.get(
                    "period_code"
                ),
                (
                    "系統總覽績效期間第 "
                    f"{index} 筆 "
                    "period_code"
                ),
            ).upper()
        )

        if (
            period_code
            not in SYSTEM_OVERVIEW_PERIODS
        ):
            raise APIResponseError(
                "系統總覽包含不支援的"
                "績效期間"
            )

        if period_code in seen_periods:
            raise APIResponseError(
                "系統總覽包含重複"
                "績效期間"
            )

        seen_periods.add(
            period_code
        )

        period_etf_count = (
            validate_non_negative_integer(
                item.get(
                    "etf_count"
                ),
                (
                    "系統總覽績效期間 "
                    f"{period_code} "
                    "etf_count"
                ),
            )
        )

        if (
            period_etf_count
            > total_etf_count
        ):
            raise APIResponseError(
                "系統總覽期間績效 ETF "
                "數量不可大於 ETF 總數"
            )

        period_coverage = (
            validate_overview_coverage_pct(
                item.get(
                    "coverage_pct"
                ),
                covered_count=(
                    period_etf_count
                ),
                total_count=(
                    total_etf_count
                ),
                field_name=(
                    "系統總覽績效期間 "
                    f"{period_code} "
                    "coverage_pct"
                ),
            )
        )

        period_latest_date = (
            validate_optional_iso_date(
                item.get(
                    "latest_as_of_date"
                ),
                (
                    "系統總覽績效期間 "
                    f"{period_code} "
                    "latest_as_of_date"
                ),
            )
        )

        if (
            period_etf_count == 0
            and period_latest_date
            is not None
        ):
            raise APIResponseError(
                "系統總覽期間沒有績效"
                "資料時不得提供日期"
            )

        periods.append(
            {
                "period_code": (
                    period_code
                ),
                "etf_count": (
                    period_etf_count
                ),
                "coverage_pct": (
                    period_coverage
                ),
                "latest_as_of_date": (
                    period_latest_date
                ),
            }
        )

    if seen_periods != set(
        SYSTEM_OVERVIEW_PERIODS
    ):
        raise APIResponseError(
            "系統總覽績效期間必須完整包含"
            " 1M、3M、6M、1Y"
        )

    period_order = {
        period_code: index
        for index, period_code in enumerate(
            SYSTEM_OVERVIEW_PERIODS
        )
    }

    periods.sort(
        key=lambda item: (
            period_order[
                item["period_code"]
            ]
        )
    )

    return {
        "metric_code": metric_code,
        "source_id": source_id,
        "etf_count": etf_count,
        "total_etf_count": (
            total_etf_count
        ),
        "coverage_pct": coverage_pct,
        "latest_as_of_date": (
            latest_as_of_date
        ),
        "periods": periods,
    }


def validate_system_overview_dividends(
    payload: object,
    *,
    total_etf_count: int,
) -> dict[str, Any]:
    """驗證首頁配息與正式資料覆蓋摘要。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "系統總覽 dividends "
            "必須是 JSON 物件"
        )

    event_count = (
        validate_non_negative_integer(
            payload.get(
                "event_count"
            ),
            (
                "系統總覽 dividends "
                "event_count"
            ),
        )
    )

    etf_count = (
        validate_non_negative_integer(
            payload.get(
                "etf_count"
            ),
            (
                "系統總覽 dividends "
                "etf_count"
            ),
        )
    )

    if etf_count > total_etf_count:
        raise APIResponseError(
            "系統總覽配息 ETF 數量"
            "不可大於 ETF 總數"
        )

    latest_event_date = (
        validate_optional_iso_date(
            payload.get(
                "latest_event_date"
            ),
            (
                "系統總覽 dividends "
                "latest_event_date"
            ),
        )
    )

    if (
        event_count == 0
        and latest_event_date is not None
    ):
        raise APIResponseError(
            "系統總覽沒有配息事件時"
            "不得提供最新事件日期"
        )

    count_fields = (
        "actual_component_event_count",
        "actual_76w_event_count",
        "source_document_event_count",
    )

    counts = {
        field_name: (
            validate_non_negative_integer(
                payload.get(
                    field_name
                ),
                (
                    "系統總覽 dividends "
                    f"{field_name}"
                ),
            )
        )
        for field_name in count_fields
    }

    if any(
        value > event_count
        for value in counts.values()
    ):
        raise APIResponseError(
            "系統總覽正式資料事件數"
            "不可大於配息事件總數"
        )

    actual_coverage = (
        validate_overview_coverage_pct(
            payload.get(
                (
                    "actual_component_"
                    "coverage_pct"
                )
            ),
            covered_count=counts[
                (
                    "actual_component_"
                    "event_count"
                )
            ],
            total_count=event_count,
            field_name=(
                "系統總覽 dividends "
                "actual_component_coverage_pct"
            ),
        )
    )

    actual_76w_coverage = (
        validate_overview_coverage_pct(
            payload.get(
                "actual_76w_coverage_pct"
            ),
            covered_count=counts[
                "actual_76w_event_count"
            ],
            total_count=event_count,
            field_name=(
                "系統總覽 dividends "
                "actual_76w_coverage_pct"
            ),
        )
    )

    source_coverage = (
        validate_overview_coverage_pct(
            payload.get(
                (
                    "source_document_"
                    "coverage_pct"
                )
            ),
            covered_count=counts[
                (
                    "source_document_"
                    "event_count"
                )
            ],
            total_count=event_count,
            field_name=(
                "系統總覽 dividends "
                "source_document_coverage_pct"
            ),
        )
    )

    return {
        "event_count": event_count,
        "etf_count": etf_count,
        "latest_event_date": (
            latest_event_date
        ),
        **counts,
        "actual_component_coverage_pct": (
            actual_coverage
        ),
        "actual_76w_coverage_pct": (
            actual_76w_coverage
        ),
        "source_document_coverage_pct": (
            source_coverage
        ),
        (
            "latest_actual_"
            "source_document_date"
        ): (
            validate_optional_iso_date(
                payload.get(
                    (
                        "latest_actual_"
                        "source_document_date"
                    )
                ),
                (
                    "系統總覽 dividends "
                    "latest_actual_"
                    "source_document_date"
                ),
            )
        ),
    }


def validate_system_overview_batch(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證首頁最近匯入批次摘要。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"系統總覽匯入批次第 {index} 筆"
            "不是 JSON 物件"
        )

    status_value = (
        validate_required_text(
            item.get(
                "status"
            ),
            (
                "系統總覽匯入批次第 "
                f"{index} 筆 status"
            ),
        ).lower()
    )

    if (
        status_value
        not in SYSTEM_OVERVIEW_BATCH_STATUSES
    ):
        raise APIResponseError(
            "系統總覽包含不支援的"
            "匯入批次狀態"
        )

    error_message = item.get(
        "error_message"
    )

    if error_message is not None:
        error_message = (
            validate_required_text(
                error_message,
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "error_message"
                ),
            )
        )

    return {
        "batch_id": (
            validate_positive_integer(
                item.get(
                    "batch_id"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 batch_id"
                ),
            )
        ),
        "pipeline_name": (
            validate_required_text(
                item.get(
                    "pipeline_name"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "pipeline_name"
                ),
            )
        ),
        "source_id": (
            validate_required_text(
                item.get(
                    "source_id"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 source_id"
                ),
            ).lower()
        ),
        "endpoint_id": (
            validate_required_text(
                item.get(
                    "endpoint_id"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 endpoint_id"
                ),
            )
        ),
        "started_at": (
            validate_required_iso_datetime(
                item.get(
                    "started_at"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 started_at"
                ),
            )
        ),
        "completed_at": (
            validate_optional_iso_datetime(
                item.get(
                    "completed_at"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 completed_at"
                ),
            )
        ),
        "status": status_value,
        "raw_record_count": (
            validate_non_negative_integer(
                item.get(
                    "raw_record_count"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "raw_record_count"
                ),
            )
        ),
        "accepted_record_count": (
            validate_non_negative_integer(
                item.get(
                    "accepted_record_count"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "accepted_record_count"
                ),
            )
        ),
        "rejected_record_count": (
            validate_non_negative_integer(
                item.get(
                    "rejected_record_count"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "rejected_record_count"
                ),
            )
        ),
        "inserted_record_count": (
            validate_non_negative_integer(
                item.get(
                    "inserted_record_count"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "inserted_record_count"
                ),
            )
        ),
        "updated_record_count": (
            validate_non_negative_integer(
                item.get(
                    "updated_record_count"
                ),
                (
                    "系統總覽匯入批次第 "
                    f"{index} 筆 "
                    "updated_record_count"
                ),
            )
        ),
        "error_message": error_message,
    }


def validate_system_overview(
    payload: object,
) -> dict[str, Any]:
    """驗證首頁系統資料總覽完整回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "系統總覽回應必須是 JSON 物件"
        )

    api_status = (
        validate_required_text(
            payload.get(
                "api_status"
            ),
            "系統總覽 api_status",
        ).lower()
    )

    if api_status != "healthy":
        raise APIResponseError(
            "系統總覽 API 狀態不是 healthy"
        )

    database_type = (
        validate_required_text(
            payload.get(
                "database_type"
            ),
            "系統總覽 database_type",
        )
    )

    if database_type != "SQLite":
        raise APIResponseError(
            "系統總覽資料庫類型不是 SQLite"
        )

    etfs = validate_system_overview_etfs(
        payload.get(
            "etfs"
        )
    )

    performance = (
        validate_system_overview_performance(
            payload.get(
                "performance"
            ),
            expected_total_etf_count=(
                etfs["total_count"]
            ),
        )
    )

    dividends = (
        validate_system_overview_dividends(
            payload.get(
                "dividends"
            ),
            total_etf_count=(
                etfs["total_count"]
            ),
        )
    )

    raw_batches = payload.get(
        "recent_import_batches"
    )

    if not isinstance(
        raw_batches,
        list,
    ):
        raise APIResponseError(
            "系統總覽 recent_import_batches "
            "必須是陣列"
        )

    if len(raw_batches) > 5:
        raise APIResponseError(
            "系統總覽最近匯入批次"
            "不可超過 5 筆"
        )

    recent_batches = [
        validate_system_overview_batch(
            item,
            index,
        )
        for index, item in enumerate(
            raw_batches,
            start=1,
        )
    ]

    batch_ids = [
        item["batch_id"]
        for item in recent_batches
    ]

    if batch_ids != sorted(
        batch_ids,
        reverse=True,
    ):
        raise APIResponseError(
            "系統總覽最近匯入批次"
            "必須依 ID 由新到舊排列"
        )

    return {
        "api_status": api_status,
        "database_type": database_type,
        "etfs": etfs,
        "performance": performance,
        "dividends": dividends,
        "recent_import_batches": (
            recent_batches
        ),
    }


def fetch_system_overview(
    api_base_url: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得首頁系統資料總覽。"""

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/system/overview"
        ),
        operation_name="系統資料總覽查詢",
        timeout_seconds=timeout_seconds,
    )

    return validate_system_overview(
        payload
    )
