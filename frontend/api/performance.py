"""前端 ETF 績效查詢與回應驗證。"""

from typing import Any
from urllib.parse import quote

from frontend.api.errors import APIResponseError
from frontend.api.normalizers import (
    SUPPORTED_PERFORMANCE_PERIODS,
    normalize_performance_metric,
    normalize_performance_period,
)
from frontend.api.transport import get_json
from frontend.api.validators import (
    validate_performance_date,
    validate_required_text,
)


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


def validate_multi_period_ranking_item(
    item: object,
    index: int,
    expected_sort_period: str,
    expected_metric: str,
) -> dict[str, Any]:
    """驗證單筆多期間績效排行榜資料。"""

    if not isinstance(item, dict):
        raise APIResponseError(
            f"多期間績效排行榜第 {index} 筆"
            "不是 JSON 物件"
        )

    required_fields = {
        "rank",
        "etf_code",
        "name",
        "is_active",
        "is_bond",
        "sort_period",
        "sort_as_of_date",
        "sort_return_pct",
        "source_id",
        "performance_items",
    }

    missing_fields = (
        required_fields - item.keys()
    )

    if missing_fields:
        missing_text = ", ".join(
            sorted(missing_fields)
        )

        raise APIResponseError(
            f"多期間績效排行榜第 {index} 筆"
            f"缺少欄位：{missing_text}"
        )

    rank = item["rank"]

    if (
        not isinstance(rank, int)
        or isinstance(rank, bool)
        or rank < 1
    ):
        raise APIResponseError(
            f"多期間績效排行榜第 {index} 筆 "
            "rank 格式不正確"
        )

    etf_code = validate_required_text(
        item["etf_code"],
        (
            f"多期間績效排行榜第 {index} 筆 "
            "etf_code"
        ),
    ).upper()

    name = validate_required_text(
        item["name"],
        (
            f"多期間績效排行榜第 {index} 筆 "
            "name"
        ),
    )

    source_id = validate_required_text(
        item["source_id"],
        (
            f"多期間績效排行榜第 {index} 筆 "
            "source_id"
        ),
    ).lower()

    for field_name in (
        "is_active",
        "is_bond",
    ):
        if not isinstance(
            item[field_name],
            bool,
        ):
            raise APIResponseError(
                f"多期間績效排行榜第 {index} 筆 "
                f"{field_name} 必須是布林值"
            )

    sort_period = str(
        item["sort_period"]
    ).strip().upper()

    if sort_period != expected_sort_period:
        raise APIResponseError(
            "多期間績效排行榜排序期間"
            "與查詢條件不一致"
        )

    sort_as_of_date = (
        validate_performance_date(
            item["sort_as_of_date"],
            (
                f"多期間績效排行榜第 {index} 筆 "
                "sort_as_of_date"
            ),
        )
    )

    sort_return_pct = validate_return_pct(
        item["sort_return_pct"],
        (
            f"多期間績效排行榜第 {index} 筆 "
            "sort_return_pct"
        ),
    )

    performance_items = item[
        "performance_items"
    ]

    if not isinstance(
        performance_items,
        list,
    ):
        raise APIResponseError(
            f"多期間績效排行榜第 {index} 筆 "
            "performance_items 格式不正確"
        )

    validated_performance = [
        validate_etf_performance_item(
            performance_item,
            performance_index,
            expected_metric,
        )
        for performance_index, performance_item in enumerate(
            performance_items,
            start=1,
        )
    ]

    period_codes = [
        performance_item["period_code"]
        for performance_item in (
            validated_performance
        )
    ]

    if len(period_codes) != len(
        set(period_codes)
    ):
        raise APIResponseError(
            "多期間績效排行榜包含重複期間"
        )

    sort_item = next(
        (
            performance_item
            for performance_item in (
                validated_performance
            )
            if performance_item[
                "period_code"
            ] == sort_period
        ),
        None,
    )

    if sort_item is None:
        raise APIResponseError(
            "多期間績效排行榜缺少排序期間資料"
        )

    if (
        sort_item["as_of_date"]
        != sort_as_of_date
        or abs(
            sort_item["return_pct"]
            - sort_return_pct
        )
        > 0.000001
        or sort_item["source_id"]
        != source_id
    ):
        raise APIResponseError(
            "多期間績效排行榜排序摘要"
            "與期間明細不一致"
        )

    period_order = {
        period_code: order
        for order, period_code in enumerate(
            SUPPORTED_PERFORMANCE_PERIODS
        )
    }

    validated_performance.sort(
        key=lambda performance_item: (
            period_order[
                performance_item[
                    "period_code"
                ]
            ]
        )
    )

    return {
        "rank": rank,
        "etf_code": etf_code,
        "name": name,
        "is_active": item["is_active"],
        "is_bond": item["is_bond"],
        "sort_period": sort_period,
        "sort_as_of_date": (
            sort_as_of_date
        ),
        "sort_return_pct": (
            sort_return_pct
        ),
        "source_id": source_id,
        "performance_items": (
            validated_performance
        ),
    }


def fetch_multi_period_performance_ranking(
    api_base_url: str,
    sort_period: str = "6M",
    metric: str = "PRICE_RETURN",
    is_active: bool | None = None,
    is_bond: bool | None = False,
    limit: int = 20,
    offset: int = 0,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得以一個期間排序的多期間績效排行榜。"""

    normalized_sort_period = (
        normalize_performance_period(
            sort_period
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
        "sort_period": (
            normalized_sort_period
        ),
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
            "/api/v1/performance/"
            "multi-period-ranking"
        ),
        operation_name="ETF 多期間績效排行榜查詢",
        params=params,
        timeout_seconds=timeout_seconds,
    )

    if not isinstance(payload, dict):
        raise APIResponseError(
            "多期間績效排行榜回應"
            "必須是 JSON 物件"
        )

    response_sort_period = str(
        payload.get("sort_period", "")
    ).strip().upper()

    response_metric = str(
        payload.get("metric_code", "")
    ).strip().upper()

    if (
        response_sort_period
        != normalized_sort_period
    ):
        raise APIResponseError(
            "多期間績效排行榜回傳排序期間"
            "與查詢條件不一致"
        )

    if response_metric != normalized_metric:
        raise APIResponseError(
            "多期間績效排行榜回傳類型"
            "與查詢條件不一致"
        )

    raw_periods = payload.get(
        "periods"
    )

    if (
        not isinstance(raw_periods, list)
        or [
            str(value).strip().upper()
            for value in raw_periods
        ]
        != list(
            SUPPORTED_PERFORMANCE_PERIODS
        )
    ):
        raise APIResponseError(
            "多期間績效排行榜 periods "
            "必須依序為 1M、3M、6M、1Y"
        )

    items = payload.get("items")

    if not isinstance(items, list):
        raise APIResponseError(
            "多期間績效排行榜 items "
            "格式不正確"
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
                "多期間績效排行榜 "
                f"{field_name} 必須是非負整數"
            )

    if integer_values["limit"] < 1:
        raise APIResponseError(
            "多期間績效排行榜 limit "
            "必須大於 0"
        )

    validated_items = [
        validate_multi_period_ranking_item(
            item=item,
            index=index,
            expected_sort_period=(
                normalized_sort_period
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
        "sort_period": (
            response_sort_period
        ),
        "metric_code": response_metric,
        "periods": list(
            SUPPORTED_PERFORMANCE_PERIODS
        ),
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
