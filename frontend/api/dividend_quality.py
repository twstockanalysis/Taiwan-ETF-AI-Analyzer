"""前端配息品質查詢與回應驗證。"""

from typing import Any
from urllib.parse import quote

from frontend.api.dividends import validate_dividend_event_item
from frontend.api.errors import APIResponseError
from frontend.api.normalizers import (
    normalize_dividend_review_issue_type,
    normalize_dividend_review_status,
)
from frontend.api.transport import get_json
from frontend.api.validators import (
    validate_non_negative_integer,
    validate_optional_iso_date,
    validate_optional_iso_datetime,
    validate_optional_number,
    validate_positive_integer,
    validate_required_iso_datetime,
    validate_required_text,
)


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
