"""前端系統總覽查詢與回應驗證。"""

from typing import Any

from frontend.api.errors import APIResponseError
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
