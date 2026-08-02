"""Streamlit 前端使用的 FastAPI Client。"""

from typing import Any
from urllib.parse import quote

import httpx

from frontend.api.errors import (
    APIClientError,
    APIConnectionError,
    APIResourceNotFoundError,
    APIResponseError,
)
from frontend.api.etfs import (
    fetch_etf_by_code,
    fetch_etfs,
    validate_etf_item,
)
from frontend.api.normalizers import (
    COMPARISON_PERIODS,
    SUPPORTED_DIVIDEND_COMPONENT_BASES,
    SUPPORTED_DIVIDEND_REVIEW_ISSUE_TYPES,
    SUPPORTED_DIVIDEND_REVIEW_STATUSES,
    SUPPORTED_PERFORMANCE_METRICS,
    SUPPORTED_PERFORMANCE_PERIODS,
    normalize_component_basis,
    normalize_dividend_review_issue_type,
    normalize_dividend_review_status,
    normalize_etf_comparison_codes,
    normalize_performance_metric,
    normalize_performance_period,
)
from frontend.api.dividends import (
    SUPPORTED_DIVIDEND_YIELD_BASES,
    fetch_dividend_components,
    fetch_dividend_detail,
    fetch_etf_dividends,
    fetch_etf_monthly_income,
    validate_dividend_component_item,
    validate_dividend_event_item,
    validate_monthly_income_distribution,
    validate_monthly_income_month_item,
)
from frontend.api.performance import (
    fetch_etf_performance,
    fetch_multi_period_performance_ranking,
    fetch_performance_ranking,
    validate_etf_performance_item,
    validate_multi_period_ranking_item,
    validate_performance_ranking_item,
    validate_return_pct,
)
from frontend.api.transport import (
    extract_response_detail,
    get_json,
)

from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_dividend_period,
    validate_optional_iso_date,
    validate_optional_iso_datetime,
    validate_optional_number,
    validate_performance_date,
    validate_positive_integer,
    validate_required_iso_datetime,
    validate_required_text,
)


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


def validate_actual_76w_item(
    item: object,
    index: int,
) -> dict[str, Any]:
    """驗證單筆實際 76W 歷史。"""

    event = validate_dividend_event_item(
        item,
        index,
        require_summary_fields=False,
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

def validate_etf_data_profile_sources(
    payload: object,
    field_name: str,
) -> list[dict[str, str]]:
    """驗證 ETF 資料概況來源清單。"""

    if not isinstance(payload, list):
        raise APIResponseError(
            f"{field_name} 必須是陣列"
        )

    sources: list[
        dict[str, str]
    ] = []

    seen_source_ids: set[str] = set()

    for index, item in enumerate(
        payload,
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(
                f"{field_name} 第 {index} 筆"
                "必須是 JSON 物件"
            )

        source_id = (
            validate_required_text(
                item.get("source_id"),
                (
                    f"{field_name} 第 {index} 筆 "
                    "source_id"
                ),
            ).lower()
        )

        display_name = (
            validate_required_text(
                item.get("display_name"),
                (
                    f"{field_name} 第 {index} 筆 "
                    "display_name"
                ),
            )
        )

        if source_id in seen_source_ids:
            raise APIResponseError(
                f"{field_name} 包含重複來源："
                f"{source_id}"
            )

        seen_source_ids.add(
            source_id
        )

        sources.append(
            {
                "source_id": source_id,
                "display_name": (
                    display_name
                ),
            }
        )

    return sources


def validate_etf_data_profile(
    payload: object,
) -> dict[str, Any]:
    """驗證 ETF 詳細頁資料來源與新鮮度回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 資料概況回應必須是 JSON 物件"
        )

    etf_code = (
        validate_required_text(
            payload.get("etf_code"),
            "ETF 資料概況 etf_code",
        ).upper()
    )

    master = payload.get("master")
    performance = payload.get(
        "performance"
    )
    dividends = payload.get(
        "dividends"
    )
    actual_dividend = payload.get(
        "actual_dividend"
    )

    sections = {
        "master": master,
        "performance": performance,
        "dividends": dividends,
        "actual_dividend": (
            actual_dividend
        ),
    }

    for section_name, section in (
        sections.items()
    ):
        if not isinstance(section, dict):
            raise APIResponseError(
                "ETF 資料概況 "
                f"{section_name} "
                "必須是 JSON 物件"
            )

    validated_master = {
        "sources": (
            validate_etf_data_profile_sources(
                master.get("sources"),
                "ETF 資料概況 master sources",
            )
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                master.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 master "
                    "latest_import_at"
                ),
            )
        ),
    }

    metric_code = (
        validate_required_text(
            performance.get(
                "metric_code"
            ),
            (
                "ETF 資料概況 performance "
                "metric_code"
            ),
        ).upper()
    )

    if metric_code != "PRICE_RETURN":
        raise APIResponseError(
            "ETF 資料概況目前只支援 "
            "PRICE_RETURN"
        )

    raw_periods = performance.get(
        "available_periods"
    )

    if not isinstance(raw_periods, list):
        raise APIResponseError(
            "ETF 資料概況 performance "
            "available_periods 必須是陣列"
        )

    available_periods: list[str] = []
    seen_periods: set[str] = set()

    for index, value in enumerate(
        raw_periods,
        start=1,
    ):
        period_code = (
            validate_required_text(
                value,
                (
                    "ETF 資料概況 performance "
                    "available_periods 第 "
                    f"{index} 筆"
                ),
            ).upper()
        )

        if (
            period_code
            not in SUPPORTED_PERFORMANCE_PERIODS
        ):
            raise APIResponseError(
                "ETF 資料概況包含不支援"
                f"的績效期間：{period_code}"
            )

        if period_code in seen_periods:
            raise APIResponseError(
                "ETF 資料概況包含重複"
                f"績效期間：{period_code}"
            )

        seen_periods.add(
            period_code
        )
        available_periods.append(
            period_code
        )

    performance_record_count = (
        validate_non_negative_integer(
            performance.get(
                "record_count"
            ),
            (
                "ETF 資料概況 performance "
                "record_count"
            ),
        )
    )

    latest_as_of_date = (
        validate_optional_iso_date(
            performance.get(
                "latest_as_of_date"
            ),
            (
                "ETF 資料概況 performance "
                "latest_as_of_date"
            ),
        )
    )

    if (
        performance_record_count == 0
        and (
            available_periods
            or latest_as_of_date is not None
        )
    ):
        raise APIResponseError(
            "ETF 資料概況沒有績效紀錄時"
            "不得提供期間或最新日期"
        )

    validated_performance = {
        "metric_code": metric_code,
        "sources": (
            validate_etf_data_profile_sources(
                performance.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "performance sources"
                ),
            )
        ),
        "record_count": (
            performance_record_count
        ),
        "available_periods": (
            available_periods
        ),
        "latest_as_of_date": (
            latest_as_of_date
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                performance.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "performance "
                    "latest_import_at"
                ),
            )
        ),
    }

    dividend_event_count = (
        validate_non_negative_integer(
            dividends.get(
                "event_count"
            ),
            (
                "ETF 資料概況 dividends "
                "event_count"
            ),
        )
    )

    latest_event_date = (
        validate_optional_iso_date(
            dividends.get(
                "latest_event_date"
            ),
            (
                "ETF 資料概況 dividends "
                "latest_event_date"
            ),
        )
    )

    if (
        dividend_event_count == 0
        and latest_event_date is not None
    ):
        raise APIResponseError(
            "ETF 資料概況沒有配息事件時"
            "不得提供最新事件日期"
        )

    validated_dividends = {
        "sources": (
            validate_etf_data_profile_sources(
                dividends.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "dividends sources"
                ),
            )
        ),
        "event_count": (
            dividend_event_count
        ),
        "latest_event_date": (
            latest_event_date
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                dividends.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "dividends "
                    "latest_import_at"
                ),
            )
        ),
    }

    actual_component_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "actual_component_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "actual_component_event_count"
            ),
        )
    )

    actual_76w_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "actual_76w_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "actual_76w_event_count"
            ),
        )
    )

    source_document_count = (
        validate_non_negative_integer(
            actual_dividend.get(
                "source_document_event_count"
            ),
            (
                "ETF 資料概況 actual_dividend "
                "source_document_event_count"
            ),
        )
    )

    if actual_76w_count > actual_component_count:
        raise APIResponseError(
            "ETF 資料概況正式 76W 事件數"
            "不可大於 ACTUAL 事件數"
        )

    if source_document_count > actual_component_count:
        raise APIResponseError(
            "ETF 資料概況正式來源文件事件數"
            "不可大於 ACTUAL 事件數"
        )

    validated_actual_dividend = {
        "sources": (
            validate_etf_data_profile_sources(
                actual_dividend.get(
                    "sources"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend sources"
                ),
            )
        ),
        "actual_component_event_count": (
            actual_component_count
        ),
        "actual_76w_event_count": (
            actual_76w_count
        ),
        "source_document_event_count": (
            source_document_count
        ),
        "latest_source_document_date": (
            validate_optional_iso_date(
                actual_dividend.get(
                    "latest_source_document_date"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend "
                    "latest_source_document_date"
                ),
            )
        ),
        "latest_import_at": (
            validate_optional_iso_datetime(
                actual_dividend.get(
                    "latest_import_at"
                ),
                (
                    "ETF 資料概況 "
                    "actual_dividend "
                    "latest_import_at"
                ),
            )
        ),
    }

    return {
        "etf_code": etf_code,
        "master": validated_master,
        "performance": (
            validated_performance
        ),
        "dividends": (
            validated_dividends
        ),
        "actual_dividend": (
            validated_actual_dividend
        ),
    }


def fetch_etf_data_profile(
    api_base_url: str,
    code: str,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """取得單一 ETF 的資料來源與新鮮度。"""

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
            "/api/v1/etfs/"
            f"{encoded_code}/data-profile"
        ),
        operation_name="ETF 資料概況查詢",
        timeout_seconds=timeout_seconds,
    )

    profile = validate_etf_data_profile(
        payload
    )

    if (
        profile["etf_code"]
        != normalized_code
    ):
        raise APIResponseError(
            "ETF 資料概況回傳代號"
            "與查詢條件不一致"
        )

    return profile


def validate_etf_comparison(
    payload: object,
) -> dict[str, Any]:
    """驗證 ETF 比較 API 回應。"""

    if not isinstance(payload, dict):
        raise APIResponseError(
            "ETF 比較回應必須是 JSON 物件"
        )

    raw_codes = payload.get("codes")
    periods = payload.get("periods")
    items = payload.get("items")

    if not isinstance(raw_codes, list):
        raise APIResponseError(
            "ETF 比較 codes 格式不正確"
        )

    try:
        codes = normalize_etf_comparison_codes(
            [str(value) for value in raw_codes]
        )

    except ValueError as error:
        raise APIResponseError(
            str(error)
        ) from error

    metric_code = str(
        payload.get("metric_code", "")
    ).strip().upper()

    if metric_code != "PRICE_RETURN":
        raise APIResponseError(
            "ETF 比較目前只接受 PRICE_RETURN"
        )

    if (
        not isinstance(periods, list)
        or [
            str(value).strip().upper()
            for value in periods
        ]
        != list(COMPARISON_PERIODS)
    ):
        raise APIResponseError(
            "ETF 比較期間必須依序為 1M、3M、6M、1Y"
        )

    if (
        not isinstance(items, list)
        or len(items) != len(codes)
    ):
        raise APIResponseError(
            "ETF 比較 items 數量與 codes 不一致"
        )

    validated_items: list[
        dict[str, Any]
    ] = []

    for index, item in enumerate(
        items,
        start=1,
    ):
        if not isinstance(item, dict):
            raise APIResponseError(
                f"ETF 比較第 {index} 筆格式不正確"
            )

        etf = validate_etf_item(
            item.get("etf"),
            index,
        )

        expected_code = codes[index - 1]

        if etf["code"] != expected_code:
            raise APIResponseError(
                "ETF 比較項目順序與 codes 不一致"
            )

        performance_items = item.get(
            "performance_items"
        )

        if not isinstance(
            performance_items,
            list,
        ):
            raise APIResponseError(
                "ETF 比較 performance_items 格式不正確"
            )

        validated_performance = [
            validate_etf_performance_item(
                performance_item,
                performance_index,
                metric_code,
            )
            for performance_index, performance_item in enumerate(
                performance_items,
                start=1,
            )
        ]

        period_codes = [
            performance_item[
                "period_code"
            ]
            for performance_item in (
                validated_performance
            )
        ]

        if len(period_codes) != len(
            set(period_codes)
        ):
            raise APIResponseError(
                "ETF 比較績效包含重複期間"
            )

        validated_performance.sort(
            key=lambda value: (
                COMPARISON_PERIODS.index(
                    value["period_code"]
                )
            )
        )

        dividend = item.get("dividend")
        actual_76w = item.get(
            "actual_76w"
        )
        completeness = item.get(
            "completeness"
        )

        if not isinstance(dividend, dict):
            raise APIResponseError(
                "ETF 比較 dividend 格式不正確"
            )

        event_count = (
            validate_non_negative_integer(
                dividend.get("event_count"),
                "ETF 比較 event_count",
            )
        )

        latest_event_date = (
            validate_optional_iso_date(
                dividend.get(
                    "latest_event_date"
                ),
                "ETF 比較 latest_event_date",
            )
        )

        latest_amount = (
            validate_optional_number(
                dividend.get(
                    "latest_amount_per_unit"
                ),
                "ETF 比較 latest_amount_per_unit",
                minimum=0,
            )
        )

        currency = dividend.get(
            "currency"
        )

        if currency is not None:
            currency = validate_required_text(
                currency,
                "ETF 比較 currency",
            ).upper()

            if len(currency) != 3:
                raise APIResponseError(
                    "ETF 比較 currency 必須是 3 個字元"
                )

        if event_count == 0 and any(
            value is not None
            for value in (
                latest_event_date,
                latest_amount,
                currency,
            )
        ):
            raise APIResponseError(
                "沒有配息事件時不得提供最新配息資料"
            )

        if not isinstance(actual_76w, dict):
            raise APIResponseError(
                "ETF 比較 actual_76w 格式不正確"
            )

        record_count = (
            validate_non_negative_integer(
                actual_76w.get(
                    "record_count"
                ),
                "ETF 比較 76W record_count",
            )
        )
        full_count = (
            validate_non_negative_integer(
                actual_76w.get(
                    "full_76w_count"
                ),
                "ETF 比較 76W full_76w_count",
            )
        )

        if full_count > record_count:
            raise APIResponseError(
                "100% 76W 次數不可大於 76W 紀錄數"
            )

        latest_ratio = validate_optional_number(
            actual_76w.get(
                "latest_ratio_pct"
            ),
            "ETF 比較 latest_ratio_pct",
            minimum=0,
            maximum=100,
        )
        average_ratio = validate_optional_number(
            actual_76w.get(
                "average_ratio_pct"
            ),
            "ETF 比較 average_ratio_pct",
            minimum=0,
            maximum=100,
        )

        if record_count == 0 and any(
            value is not None
            for value in (
                latest_ratio,
                average_ratio,
            )
        ):
            raise APIResponseError(
                "沒有 76W 紀錄時比例必須為空值"
            )

        profile = validate_etf_data_profile(
            item.get("data_profile")
        )

        if profile["etf_code"] != expected_code:
            raise APIResponseError(
                "ETF 比較資料概況代號不一致"
            )

        if not isinstance(
            completeness,
            dict,
        ):
            raise APIResponseError(
                "ETF 比較 completeness 格式不正確"
            )

        available_count = (
            validate_non_negative_integer(
                completeness.get(
                    "available_section_count"
                ),
                "ETF 比較 available_section_count",
            )
        )
        total_count = validate_positive_integer(
            completeness.get(
                "total_section_count"
            ),
            "ETF 比較 total_section_count",
        )
        score_pct = validate_optional_number(
            completeness.get("score_pct"),
            "ETF 比較 score_pct",
            minimum=0,
            maximum=100,
        )

        available_sections = completeness.get(
            "available_sections"
        )
        missing_sections = completeness.get(
            "missing_sections"
        )

        if (
            not isinstance(
                available_sections,
                list,
            )
            or not isinstance(
                missing_sections,
                list,
            )
        ):
            raise APIResponseError(
                "ETF 比較完整度區塊格式不正確"
            )

        available_sections = [
            validate_required_text(
                value,
                "ETF 比較 available_sections",
            )
            for value in available_sections
        ]
        missing_sections = [
            validate_required_text(
                value,
                "ETF 比較 missing_sections",
            )
            for value in missing_sections
        ]

        if (
            available_count
            != len(available_sections)
            or total_count
            != (
                len(available_sections)
                + len(missing_sections)
            )
        ):
            raise APIResponseError(
                "ETF 比較完整度計數不一致"
            )

        expected_score = round(
            available_count
            / total_count
            * 100,
            6,
        )

        if (
            score_pct is None
            or abs(
                score_pct - expected_score
            )
            > 0.000001
        ):
            raise APIResponseError(
                "ETF 比較完整度百分比不一致"
            )

        validated_items.append(
            {
                "etf": etf,
                "performance_items": (
                    validated_performance
                ),
                "dividend": {
                    "event_count": event_count,
                    "latest_event_date": (
                        latest_event_date
                    ),
                    "latest_amount_per_unit": (
                        latest_amount
                    ),
                    "currency": currency,
                },
                "actual_76w": {
                    "record_count": record_count,
                    "full_76w_count": (
                        full_count
                    ),
                    "latest_ratio_pct": (
                        latest_ratio
                    ),
                    "average_ratio_pct": (
                        average_ratio
                    ),
                },
                "data_profile": profile,
                "completeness": {
                    "available_section_count": (
                        available_count
                    ),
                    "total_section_count": (
                        total_count
                    ),
                    "score_pct": score_pct,
                    "available_sections": (
                        available_sections
                    ),
                    "missing_sections": (
                        missing_sections
                    ),
                },
            }
        )

    return {
        "codes": list(codes),
        "metric_code": metric_code,
        "periods": list(
            COMPARISON_PERIODS
        ),
        "items": validated_items,
    }


def fetch_etf_comparison(
    api_base_url: str,
    codes: list[str] | tuple[str, ...],
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    """取得 2 至 4 檔 ETF 的聚合比較資料。"""

    normalized_codes = (
        normalize_etf_comparison_codes(
            codes
        )
    )

    payload = get_json(
        api_base_url=api_base_url,
        endpoint_path=(
            "/api/v1/etfs/comparison"
        ),
        operation_name="ETF 比較查詢",
        params={
            "codes": ",".join(
                normalized_codes
            ),
        },
        timeout_seconds=timeout_seconds,
    )

    result = validate_etf_comparison(
        payload
    )

    if tuple(result["codes"]) != (
        normalized_codes
    ):
        raise APIResponseError(
            "ETF 比較回傳代號與查詢條件不一致"
        )

    return result
